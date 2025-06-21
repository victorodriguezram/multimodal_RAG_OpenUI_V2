"""
FastAPI service for n8n integration with the RAG system
This provides REST API endpoints for document processing and querying
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid
import asyncio
import aiofiles
import os
from datetime import datetime

# Import our RAG components
from core.embeddings import get_document_embedding, get_query_embedding
from core.document_utils import (
    pdf_to_images,
    extract_text_from_pdf,
    save_image_preview,
    load_embeddings_and_info,
    save_embeddings_and_info,
)
from core.search import search_documents, answer_with_gemini
from config import DATA_DIR

app = FastAPI(
    title="Multimodal RAG API",
    description="REST API for document processing and querying with multimodal RAG",
    version="1.0.0"
)

# Enable CORS for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class QueryRequest(BaseModel):
    query: str
    top_k: int = 3

class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]
    processing_time: float

class DocumentStatus(BaseModel):
    document_id: str
    filename: str
    status: str
    embeddings_count: int
    upload_time: datetime

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    services: dict

# Global variables for in-memory storage (consider Redis for production)
processing_status = {}
faiss_index = None
docs_info = []

# Load existing data on startup
@app.on_event("startup")
async def startup_event():
    global faiss_index, docs_info
    faiss_index, docs_info = load_embeddings_and_info()

@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Multimodal RAG API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "upload": "/api/documents/upload",
            "query": "/api/query",
            "documents": "/api/documents",
            "status": "/api/documents/{document_id}/status"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring"""
    global faiss_index, docs_info
    
    services = {
        "faiss_index": "healthy" if faiss_index is not None else "not_initialized",
        "documents_count": len(docs_info) if docs_info else 0,
        "data_directory": "accessible" if os.path.exists(DATA_DIR) else "not_accessible"
    }
    
    overall_status = "healthy" if all(
        status != "not_accessible" for status in services.values()
    ) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(),
        services=services
    )

@app.post("/api/documents/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload and process a PDF document"""
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Generate document ID
    doc_id = str(uuid.uuid4())
    
    # Save uploaded file temporarily
    upload_dir = os.path.join(DATA_DIR, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{doc_id}_{file.filename}")
    
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Initialize processing status
    processing_status[doc_id] = {
        "status": "processing",
        "filename": file.filename,
        "upload_time": datetime.now(),
        "embeddings_count": 0
    }
    
    # Start background processing
    background_tasks.add_task(process_document, doc_id, file_path, file.filename)
    
    return {
        "document_id": doc_id,
        "filename": file.filename,
        "status": "processing",
        "message": "Document upload successful, processing started"
    }

async def process_document(doc_id: str, file_path: str, filename: str):
    """Background task to process uploaded document"""
    global faiss_index, docs_info
    
    try:
        # Read file content
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # Create a file-like object for compatibility
        from io import BytesIO
        file_obj = BytesIO(file_content)
        file_obj.name = filename
        
        # Process document
        images = pdf_to_images(file_obj)
        text = extract_text_from_pdf(file_obj)
        
        new_embeddings = []
        
        # Process text content
        if text.strip():
            emb = get_document_embedding(text, "text")
            if emb is not None:
                new_embeddings.append({
                    "embedding": emb,
                    "doc_id": doc_id,
                    "content_type": "text"
                })
                docs_info.append({
                    "doc_id": doc_id,
                    "source": filename,
                    "content_type": "text",
                    "content": text,
                    "preview": text[:200] + "..." if len(text) > 200 else text,
                })
        
        # Process images
        for page_num, img in enumerate(images, 1):
            page_id = f"{doc_id}_page_{page_num}"
            emb = get_document_embedding(img, "image")
            if emb is not None:
                new_embeddings.append({
                    "embedding": emb,
                    "doc_id": page_id,
                    "content_type": "image"
                })
                path = save_image_preview(img, f"{page_id}.png")
                docs_info.append({
                    "doc_id": page_id,
                    "source": filename,
                    "content_type": "image",
                    "page": page_num,
                    "preview": path,
                })
        
        # Save embeddings
        if new_embeddings:
            save_embeddings_and_info(new_embeddings, docs_info)
            faiss_index, _ = load_embeddings_and_info()  # Reload
        
        # Update status
        processing_status[doc_id] = {
            "status": "completed",
            "filename": filename,
            "upload_time": processing_status[doc_id]["upload_time"],
            "embeddings_count": len(new_embeddings),
            "processing_completed": datetime.now()
        }
        
        # Clean up temporary file
        os.remove(file_path)
        
    except Exception as e:
        processing_status[doc_id] = {
            "status": "failed",
            "filename": filename,
            "upload_time": processing_status[doc_id]["upload_time"],
            "error": str(e),
            "processing_completed": datetime.now()
        }

@app.get("/api/documents/{document_id}/status", response_model=DocumentStatus)
async def get_document_status(document_id: str):
    """Get processing status of a document"""
    
    if document_id not in processing_status:
        raise HTTPException(status_code=404, detail="Document not found")
    
    status_info = processing_status[document_id]
    return DocumentStatus(
        document_id=document_id,
        filename=status_info["filename"],
        status=status_info["status"],
        embeddings_count=status_info.get("embeddings_count", 0),
        upload_time=status_info["upload_time"]
    )

@app.get("/api/documents")
async def list_documents():
    """List all processed documents"""
    global docs_info
    
    # Group documents by source file
    documents = {}
    for doc in docs_info:
        source = doc["source"]
        if source not in documents:
            documents[source] = {
                "filename": source,
                "text_content": False,
                "image_pages": [],
                "total_embeddings": 0
            }
        
        if doc["content_type"] == "text":
            documents[source]["text_content"] = True
        elif doc["content_type"] == "image":
            documents[source]["image_pages"].append(doc.get("page", 1))
        
        documents[source]["total_embeddings"] += 1
    
    return {"documents": list(documents.values()), "total_count": len(documents)}

@app.post("/api/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query documents and get AI-generated response"""
    global faiss_index, docs_info
    
    if faiss_index is None:
        raise HTTPException(status_code=400, detail="No documents indexed yet")
    
    start_time = asyncio.get_event_loop().time()
    
    try:
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
                answer="No relevant documents found for your query.",
                sources=[],
                processing_time=asyncio.get_event_loop().time() - start_time
            )
        
        # Get best result for AI response
        text_result = next((r for r in results if r['content_type'] == 'text'), None)
        image_result = next((r for r in results if r['content_type'] == 'image'), None)
        
        # Generate AI response
        if image_result:
            from PIL import Image
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
                "source": result["source"],
                "content_type": result["content_type"],
                "similarity": round(result["similarity"], 4)
            }
            if result["content_type"] == "image":
                source["page"] = result.get("page", 1)
            elif result["content_type"] == "text":
                source["preview"] = result.get("preview", "")
            
            sources.append(source)
        
        processing_time = asyncio.get_event_loop().time() - start_time
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            processing_time=round(processing_time, 3)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@app.delete("/api/documents/clear")
async def clear_all_documents():
    """Clear all indexed documents (use with caution)"""
    global faiss_index, docs_info, processing_status
    
    try:
        # Clear in-memory data
        docs_info = []
        processing_status = {}
        faiss_index = None
        
        # Remove files
        import shutil
        if os.path.exists(DATA_DIR):
            for file in os.listdir(DATA_DIR):
                file_path = os.path.join(DATA_DIR, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
        
        return {"message": "All documents cleared successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear documents: {str(e)}")

# Webhook endpoint for n8n integration
@app.post("/webhook/n8n/query")
async def n8n_query_webhook(request: dict):
    """Webhook endpoint specifically designed for n8n integration"""
    
    # Extract query from n8n payload
    query = request.get("query") or request.get("question") or request.get("text")
    if not query:
        raise HTTPException(status_code=400, detail="Query field is required")
    
    # Process query
    query_request = QueryRequest(query=query, top_k=3)
    result = await query_documents(query_request)
    
    # Format response for n8n
    return {
        "answer": result.answer,
        "query": query,
        "sources_count": len(result.sources),
        "processing_time": result.processing_time,
        "timestamp": datetime.now().isoformat(),
        "sources": result.sources
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
