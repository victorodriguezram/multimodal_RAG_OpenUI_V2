"""
Document processing and management service
"""

import os
import uuid
import asyncio
import tempfile
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog
from PIL import Image
import numpy as np
import faiss

from ..models import DocumentInfo, ContentType
from ..config import get_settings
from ...core.embeddings import get_document_embedding
from ...core.document_utils import pdf_to_images, extract_text_from_pdf, save_image_preview
from ..database import get_db_session

logger = structlog.get_logger()
settings = get_settings()

class DocumentService:
    """Handle document processing and storage"""
    
    @staticmethod
    async def initialize():
        """Initialize document service"""
        try:
            # Create necessary directories
            os.makedirs(settings.UPLOAD_FULL_PATH, exist_ok=True)
            os.makedirs(settings.FAISS_FULL_PATH, exist_ok=True)
            os.makedirs(settings.PREVIEW_FULL_PATH, exist_ok=True)
            
            logger.info("Document service initialized")
        except Exception as e:
            logger.error("Failed to initialize document service", error=str(e))
            raise
    
    @staticmethod
    async def process_documents_async(task_id: str, files: List, user_id: str):
        """Process documents asynchronously"""
        try:
            logger.info("Starting document processing", task_id=task_id, file_count=len(files))
            
            # Update task status
            await DocumentService._update_task_progress(task_id, 0, "Starting processing")
            
            processed_documents = []
            total_files = len(files)
            
            for i, file in enumerate(files):
                try:
                    # Process individual document
                    doc_info = await DocumentService._process_single_document(file, user_id)
                    processed_documents.append(doc_info)
                    
                    # Update progress
                    progress = ((i + 1) / total_files) * 100
                    await DocumentService._update_task_progress(
                        task_id, 
                        progress, 
                        f"Processed {i + 1}/{total_files} documents"
                    )
                    
                except Exception as e:
                    logger.error(
                        "Error processing document", 
                        error=str(e), 
                        filename=file.filename,
                        task_id=task_id
                    )
                    continue
            
            # Mark task as completed
            await DocumentService._update_task_progress(
                task_id, 
                100, 
                f"Completed processing {len(processed_documents)} documents"
            )
            
            logger.info(
                "Document processing completed", 
                task_id=task_id, 
                processed_count=len(processed_documents)
            )
            
        except Exception as e:
            logger.error("Document processing failed", error=str(e), task_id=task_id)
            await DocumentService._update_task_progress(task_id, 0, f"Processing failed: {str(e)}")
    
    @staticmethod
    async def _process_single_document(file, user_id: str) -> DocumentInfo:
        """Process a single document"""
        doc_id = str(uuid.uuid4())
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(await file.read())
            tmp_path = tmp_file.name
        
        try:
            # Extract images and text
            images = pdf_to_images(file)
            text = extract_text_from_pdf(file)
            
            embeddings_data = []
            text_chunks = 0
            image_chunks = 0
            
            # Process text if available
            if text.strip():
                text_embedding = get_document_embedding(text, "text")
                if text_embedding is not None:
                    embeddings_data.append({
                        "embedding": text_embedding,
                        "doc_id": doc_id,
                        "content_type": "text",
                        "content": text
                    })
                    text_chunks = 1
            
            # Process images
            for page_num, img in enumerate(images, 1):
                page_id = f"{doc_id}_page_{page_num}"
                img_embedding = get_document_embedding(img, "image")
                
                if img_embedding is not None:
                    # Save image preview
                    preview_path = await DocumentService._save_image_preview(img, f"{page_id}.png")
                    
                    embeddings_data.append({
                        "embedding": img_embedding,
                        "doc_id": page_id,
                        "content_type": "image",
                        "page": page_num,
                        "preview_path": preview_path
                    })
                    image_chunks += 1
            
            # Save embeddings to FAISS index
            if embeddings_data:
                await DocumentService._save_embeddings(doc_id, embeddings_data, user_id)
            
            # Create document info
            doc_info = DocumentInfo(
                id=doc_id,
                filename=file.filename,
                size=file.size,
                content_type="application/pdf",
                upload_date=datetime.utcnow(),
                status="processed",
                page_count=len(images),
                text_chunks=text_chunks,
                image_chunks=image_chunks,
                user_id=user_id
            )
            
            # Save to database
            await DocumentService._save_document_info(doc_info)
            
            return doc_info
            
        finally:
            # Clean up temporary file
            os.unlink(tmp_path)
    
    @staticmethod
    async def _save_embeddings(doc_id: str, embeddings_data: List[Dict], user_id: str):
        """Save embeddings to FAISS index"""
        try:
            # Create user-specific index file
            index_path = os.path.join(settings.FAISS_FULL_PATH, f"user_{user_id}.index")
            metadata_path = os.path.join(settings.FAISS_FULL_PATH, f"user_{user_id}_metadata.json")
            
            # Load existing index or create new one
            if os.path.exists(index_path):
                index = faiss.read_index(index_path)
                # Load existing metadata
                import json
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            else:
                # Create new index
                dimension = len(embeddings_data[0]["embedding"])
                index = faiss.IndexFlatL2(dimension)
                metadata = []
            
            # Add new embeddings
            vectors = np.array([item["embedding"] for item in embeddings_data]).astype("float32")
            index.add(vectors)
            
            # Add metadata
            for item in embeddings_data:
                metadata.append({
                    "doc_id": item["doc_id"],
                    "content_type": item["content_type"],
                    "content": item.get("content", ""),
                    "page": item.get("page"),
                    "preview_path": item.get("preview_path"),
                    "parent_doc_id": doc_id
                })
            
            # Save updated index and metadata
            faiss.write_index(index, index_path)
            
            import json
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
            
            logger.info("Embeddings saved", doc_id=doc_id, user_id=user_id, count=len(embeddings_data))
            
        except Exception as e:
            logger.error("Error saving embeddings", error=str(e), doc_id=doc_id)
            raise
    
    @staticmethod
    async def _save_image_preview(image: Image.Image, filename: str) -> str:
        """Save image preview and return path"""
        try:
            preview_path = os.path.join(settings.PREVIEW_FULL_PATH, filename)
            image.save(preview_path)
            return preview_path
        except Exception as e:
            logger.error("Error saving image preview", error=str(e), filename=filename)
            raise
    
    @staticmethod
    async def _save_document_info(doc_info: DocumentInfo):
        """Save document info to database"""
        try:
            async with get_db_session() as session:
                session.add(doc_info)
                await session.commit()
        except Exception as e:
            logger.error("Error saving document info", error=str(e), doc_id=doc_info.id)
            raise
    
    @staticmethod
    async def _update_task_progress(task_id: str, progress: float, message: str):
        """Update task progress in database"""
        try:
            async with get_db_session() as session:
                # Implementation depends on your task model
                # This is a placeholder
                pass
        except Exception as e:
            logger.error("Error updating task progress", error=str(e), task_id=task_id)
    
    @staticmethod
    async def get_user_documents(user_id: str) -> List[DocumentInfo]:
        """Get all documents for a user"""
        try:
            async with get_db_session() as session:
                documents = await session.query(DocumentInfo).filter(
                    DocumentInfo.user_id == user_id
                ).order_by(DocumentInfo.upload_date.desc()).all()
                
                return documents
        except Exception as e:
            logger.error("Error getting user documents", error=str(e), user_id=user_id)
            return []
    
    @staticmethod
    async def delete_document(doc_id: str, user_id: str) -> bool:
        """Delete a document and its embeddings"""
        try:
            async with get_db_session() as session:
                # Get document info
                doc = await session.query(DocumentInfo).filter(
                    DocumentInfo.id == doc_id,
                    DocumentInfo.user_id == user_id
                ).first()
                
                if not doc:
                    return False
                
                # Delete from FAISS index (implementation needed)
                # Delete preview images
                # Delete from database
                await session.delete(doc)
                await session.commit()
                
                logger.info("Document deleted", doc_id=doc_id, user_id=user_id)
                return True
                
        except Exception as e:
            logger.error("Error deleting document", error=str(e), doc_id=doc_id)
            return False
    
    @staticmethod
    async def get_system_stats() -> Dict[str, Any]:
        """Get system statistics"""
        try:
            async with get_db_session() as session:
                # Calculate various statistics
                total_documents = await session.query(DocumentInfo).count()
                
                # Calculate storage usage
                storage_used = 0
                for root, dirs, files in os.walk(settings.DATA_VOLUME_PATH):
                    for file in files:
                        filepath = os.path.join(root, file)
                        if os.path.exists(filepath):
                            storage_used += os.path.getsize(filepath)
                
                return {
                    "total_documents": total_documents,
                    "storage_used_mb": storage_used / (1024 * 1024),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error("Error getting system stats", error=str(e))
            return {}
    
    @staticmethod
    async def cleanup():
        """Cleanup document service"""
        logger.info("Document service cleanup completed")
