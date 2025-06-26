from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid
import os
import json
from datetime import datetime

# Import core modules
from core.embeddings import get_document_embedding, get_query_embedding
from core.document_utils import (
    pdf_to_images,
    extract_text_from_pdf,
    save_image_preview,
    load_embeddings_and_info,
    save_embeddings_and_info,
)
from core.search import search_documents, answer_with_gemini
from PIL import Image

app = FastAPI(title="Multimodal RAG API", version="1.0.0")

# Enable CORS for N8N integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state for embeddings
faiss_index = None
docs_info = []

# Initialize embeddings on startup
@app.on_event("startup")
async def startup_event():
    global faiss_index, docs_info
    faiss_index, docs_info = load_embeddings_and_info()

# Pydantic models
class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 3

class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]
    query: str
    timestamp: str

class DocumentInfo(BaseModel):
    doc_id: str
    source: str
    content_type: str
    page: Optional[int] = None
    preview: Optional[str] = None

class SystemStatus(BaseModel):
    status: str
    total_documents: int
    text_documents: int
    image_documents: int
    faiss_index_size: Optional[int] = None

# API Endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "multimodal-rag-api"}

@app.get("/status", response_model=SystemStatus)
async def get_system_status():
    """Get system status and statistics"""
    global faiss_index, docs_info
    
    text_count = sum(1 for doc in docs_info if doc["content_type"] == "text")
    image_count = sum(1 for doc in docs_info if doc["content_type"] == "image")
    
    return SystemStatus(
        status="active" if faiss_index is not None else "empty",
        total_documents=len(docs_info),
        text_documents=text_count,
        image_documents=image_count,
        faiss_index_size=faiss_index.ntotal if faiss_index else 0
    )

@app.post("/documents/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload and process PDF documents"""
    global faiss_index, docs_info
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    processed_files = []
    new_embeddings = []
    
    for uploaded_file in files:
        if not uploaded_file.filename.endswith('.pdf'):
            continue
            
        try:
            # Read file content
            content = await uploaded_file.read()
            await uploaded_file.seek(0)
            
            doc_id = str(uuid.uuid4())
            
            # Convert to images
            class FileWrapper:
                def __init__(self, content):
                    self.content = content
                def getvalue(self):
                    return self.content
            
            file_wrapper = FileWrapper(content)
            images = pdf_to_images(file_wrapper)
            text = extract_text_from_pdf(file_wrapper)
            
            # Process text
            if text.strip():
                emb = get_document_embedding(text, "text")
                if emb is not None:
                    new_embeddings.append({"embedding": emb, "doc_id": doc_id, "content_type": "text"})
                    docs_info.append({
                        "doc_id": doc_id,
                        "source": uploaded_file.filename,
                        "content_type": "text",
                        "content": text,
                        "preview": text[:200] + "..." if len(text) > 200 else text,
                    })
            
            # Process images
            for page_num, img in enumerate(images, 1):
                page_id = f"{doc_id}_page_{page_num}"
                emb = get_document_embedding(img, "image")
                if emb is not None:
                    new_embeddings.append({"embedding": emb, "doc_id": page_id, "content_type": "image"})
                    path = save_image_preview(img, f"{page_id}.png")
                    docs_info.append({
                        "doc_id": page_id,
                        "source": uploaded_file.filename,
                        "content_type": "image",
                        "page": page_num,
                        "preview": path,
                    })
            
            processed_files.append({
                "filename": uploaded_file.filename,
                "doc_id": doc_id,
                "text_pages": 1 if text.strip() else 0,
                "image_pages": len(images)
            })
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing {uploaded_file.filename}: {str(e)}")
    
    # Save embeddings
    if new_embeddings:
        save_embeddings_and_info(new_embeddings, docs_info)
        faiss_index, _ = load_embeddings_and_info()  # Reload
    
    return {
        "message": f"Successfully processed {len(processed_files)} documents",
        "processed_files": processed_files,
        "total_indexed_items": len(docs_info)
    }

@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query the document collection"""
    global faiss_index, docs_info
    
    if faiss_index is None:
        raise HTTPException(status_code=400, detail="No documents indexed yet")
    
    # Search documents
    results = search_documents(
        request.query, 
        faiss_index, 
        docs_info, 
        get_query_embedding, 
        top_k=request.top_k
    )
    
    if not results:
        return QueryResponse(
            answer="No relevant results found.",
            sources=[],
            query=request.query,
            timestamp=datetime.now().isoformat()
        )
    
    # Get best result for LLM
    text_result = next((r for r in results if r['content_type'] == 'text'), None)
    image_result = next((r for r in results if r['content_type'] == 'image'), None)
    
    # Generate answer
    if image_result:
        content = Image.open(image_result['preview'])
    elif text_result:
        content = text_result['content']
    else:
        content = ""
    
    answer = answer_with_gemini(request.query, content)
    
    # Format sources
    sources = []
    for result in results:
        source = {
            "doc_id": result["doc_id"],
            "source": result["source"],
            "content_type": result["content_type"],
            "similarity": result["similarity"],
        }
        if result["content_type"] == "image":
            source["page"] = result.get("page", 1)
        else:
            source["preview"] = result.get("preview", "")
        sources.append(source)
    
    return QueryResponse(
        answer=answer,
        sources=sources,
        query=request.query,
        timestamp=datetime.now().isoformat()
    )

@app.get("/documents", response_model=List[DocumentInfo])
async def list_documents():
    """List all indexed documents"""
    global docs_info
    
    return [
        DocumentInfo(
            doc_id=doc["doc_id"],
            source=doc["source"],
            content_type=doc["content_type"],
            page=doc.get("page"),
            preview=doc.get("preview")
        )
        for doc in docs_info
    ]

@app.delete("/documents/clear")
async def clear_all_documents():
    """Clear all indexed documents"""
    global faiss_index, docs_info
    
    try:
        # Clear in-memory data
        docs_info = []
        faiss_index = None
        
        # Remove files
        for file in ["data/faiss.index", "data/docs_info.pkl"]:
            if os.path.exists(file):
                os.remove(file)
        
        # Clear image previews
        data_dir = "data"
        if os.path.exists(data_dir):
            for file in os.listdir(data_dir):
                if file.endswith('.png'):
                    os.remove(os.path.join(data_dir, file))
        
        return {"message": "All documents cleared successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing documents: {str(e)}")

@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a specific document"""
    global docs_info
    
    # Find and remove document
    original_count = len(docs_info)
    docs_info = [doc for doc in docs_info if not doc["doc_id"].startswith(doc_id)]
    
    if len(docs_info) == original_count:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Note: For simplicity, we're not rebuilding the FAISS index here
    # In production, you might want to rebuild the index after deletions
    
    return {"message": f"Document {doc_id} deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
