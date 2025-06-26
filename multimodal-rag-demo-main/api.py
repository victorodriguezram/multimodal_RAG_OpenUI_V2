
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import os
import uuid
from PIL import Image

from core.embeddings import get_document_embedding, get_query_embedding
from core.document_utils import (
    pdf_to_images,
    extract_text_from_pdf,
    save_image_preview,
    load_embeddings_and_info,
    save_embeddings_and_info,
)
from core.search import search_documents, answer_with_gemini

app = FastAPI()

faiss_index, docs_info = load_embeddings_and_info()

@app.post("/upload/")
async def upload_document(file: UploadFile = File(...)):
    try:
        doc_id = str(uuid.uuid4())
        images = pdf_to_images(file.file)
        text = extract_text_from_pdf(file.file)

        new_embeddings = []
        global docs_info

        if text.strip():
            emb = get_document_embedding(text, "text")
            if emb is not None:
                new_embeddings.append({"embedding": emb, "doc_id": doc_id, "content_type": "text"})
                docs_info.append({
                    "doc_id": doc_id,
                    "source": file.filename,
                    "content_type": "text",
                    "content": text,
                    "preview": text[:200] + "..." if len(text) > 200 else text,
                })

        for page_num, img in enumerate(images, 1):
            page_id = f"{doc_id}_page_{page_num}"
            emb = get_document_embedding(img, "image")
            if emb is not None:
                new_embeddings.append({"embedding": emb, "doc_id": page_id, "content_type": "image"})
                path = save_image_preview(img, f"{page_id}.png")
                docs_info.append({
                    "doc_id": page_id,
                    "source": file.filename,
                    "content_type": "image",
                    "page": page_num,
                    "preview": path,
                })
        
        global faiss_index
        save_embeddings_and_info(new_embeddings, docs_info)
        faiss_index, _ = load_embeddings_and_info()

        return JSONResponse(content={"message": "Document processed and indexed successfully.", "doc_id": doc_id})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/query/")
async def query_document(query: str):
    try:
        if faiss_index is None:
            raise HTTPException(status_code=404, detail="No documents indexed yet.")

        results = search_documents(query, faiss_index, docs_info, get_query_embedding, top_k=3)
        if not results:
            raise HTTPException(status_code=404, detail="No relevant results found.")

        text_result = next((r for r in results if r['content_type'] == 'text'), None)
        image_result = next((r for r in results if r['content_type'] == 'image'), None)

        if image_result:
            content = Image.open(image_result['preview'])
        elif text_result:
            content = text_result['content']
        else:
            content = ""

        answer = answer_with_gemini(query, content)
        
        response_data = {"answer": answer, "results": results}

        return JSONResponse(content=response_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health/")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
