"""
Celery tasks for background processing
"""

import os
import uuid
import tempfile
from typing import List, Dict, Any
from celery import current_task
import structlog

from worker.main import app
from api.services.document_service import DocumentService
from api.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

@app.task(bind=True, name='process_documents')
def process_documents_task(self, files_data: List[Dict], user_id: str):
    """
    Process uploaded documents asynchronously
    
    Args:
        files_data: List of file data dictionaries
        user_id: User ID who uploaded the documents
    """
    try:
        task_id = self.request.id
        total_files = len(files_data)
        
        logger.info("Starting document processing task", task_id=task_id, file_count=total_files)
        
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': total_files, 'status': 'Starting processing...'}
        )
        
        processed_documents = []
        
        for i, file_data in enumerate(files_data):
            try:
                filename = file_data['filename']
                content = file_data['content']
                
                logger.info("Processing document", filename=filename, task_id=task_id)
                
                # Update progress
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i,
                        'total': total_files,
                        'status': f'Processing {filename}...'
                    }
                )
                
                # Process the document
                doc_info = process_single_document(content, filename, user_id)
                processed_documents.append(doc_info)
                
                # Update progress
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i + 1,
                        'total': total_files,
                        'status': f'Completed {filename}'
                    }
                )
                
            except Exception as e:
                logger.error(
                    "Error processing document",
                    error=str(e),
                    filename=filename,
                    task_id=task_id
                )
                continue
        
        logger.info("Document processing completed", task_id=task_id, processed_count=len(processed_documents))
        
        return {
            'status': 'completed',
            'processed_documents': len(processed_documents),
            'total_files': total_files,
            'documents': [doc.__dict__ for doc in processed_documents]
        }
        
    except Exception as e:
        logger.error("Document processing task failed", error=str(e), task_id=self.request.id)
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'status': 'Processing failed'}
        )
        raise

def process_single_document(content: bytes, filename: str, user_id: str):
    """Process a single document synchronously"""
    from core.embeddings import get_document_embedding
    from core.document_utils import pdf_to_images, extract_text_from_pdf
    
    doc_id = str(uuid.uuid4())
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(content)
        tmp_path = tmp_file.name
    
    try:
        # Create a mock file object for the existing functions
        class MockFile:
            def __init__(self, path, filename):
                self.filename = filename
                self.size = os.path.getsize(path)
                with open(path, 'rb') as f:
                    self._content = f.read()
            
            def getvalue(self):
                return self._content
            
            def read(self):
                return self._content
        
        mock_file = MockFile(tmp_path, filename)
        
        # Extract images and text
        images = pdf_to_images(mock_file)
        text = extract_text_from_pdf(mock_file)
        
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
                from api.services.document_service import DocumentService
                preview_path = DocumentService._save_image_preview(img, f"{page_id}.png")
                
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
            DocumentService._save_embeddings(doc_id, embeddings_data, user_id)
        
        # Create document info
        from api.models import DocumentInfo
        from datetime import datetime
        
        doc_info = DocumentInfo(
            id=doc_id,
            filename=filename,
            size=mock_file.size,
            content_type="application/pdf",
            upload_date=datetime.utcnow(),
            status="processed",
            page_count=len(images),
            text_chunks=text_chunks,
            image_chunks=image_chunks,
            user_id=user_id
        )
        
        # Save to database
        DocumentService._save_document_info(doc_info)
        
        return doc_info
        
    finally:
        # Clean up temporary file
        os.unlink(tmp_path)

@app.task(bind=True, name='cleanup_old_data')
def cleanup_old_data_task(self, days: int = 30):
    """Clean up old data and temporary files"""
    try:
        logger.info("Starting cleanup task", days=days)
        
        # Clean up old tasks
        from api.services.task_manager import TaskManager
        deleted_tasks = TaskManager.cleanup_old_tasks(days)
        
        # Clean up temporary files
        temp_dir = tempfile.gettempdir()
        cleaned_files = 0
        
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.startswith('tmp') and file.endswith('.pdf'):
                    file_path = os.path.join(root, file)
                    try:
                        # Check if file is older than specified days
                        file_age = time.time() - os.path.getctime(file_path)
                        if file_age > (days * 24 * 3600):
                            os.remove(file_path)
                            cleaned_files += 1
                    except Exception as e:
                        logger.warning("Error cleaning temp file", file=file_path, error=str(e))
        
        logger.info("Cleanup completed", deleted_tasks=deleted_tasks, cleaned_files=cleaned_files)
        
        return {
            'status': 'completed',
            'deleted_tasks': deleted_tasks,
            'cleaned_files': cleaned_files
        }
        
    except Exception as e:
        logger.error("Cleanup task failed", error=str(e))
        raise

@app.task(bind=True, name='health_check')
def health_check_task(self):
    """Health check task for monitoring"""
    try:
        # Check database connectivity
        from api.database import check_database_health
        db_healthy = check_database_health()
        
        # Check Redis connectivity
        import redis
        redis_client = redis.from_url(settings.REDIS_URL)
        redis_healthy = redis_client.ping()
        
        # Check file system
        fs_healthy = os.path.exists(settings.DATA_VOLUME_PATH) and os.access(settings.DATA_VOLUME_PATH, os.W_OK)
        
        health_status = {
            'database': db_healthy,
            'redis': redis_healthy,
            'filesystem': fs_healthy,
            'overall': db_healthy and redis_healthy and fs_healthy
        }
        
        logger.info("Health check completed", status=health_status)
        return health_status
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            'database': False,
            'redis': False,
            'filesystem': False,
            'overall': False,
            'error': str(e)
        }
