"""Worker tests"""
import pytest
from unittest.mock import patch, MagicMock
import json
import os
import sys

# Add worker directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'worker'))

class TestWorkerTasks:
    """Test Celery worker tasks"""
    
    def test_document_processing_task(self):
        """Test document processing task"""
        with patch('worker.tasks.process_document_content') as mock_process:
            mock_process.return_value = {
                "document_id": "doc-123",
                "chunks_created": 15,
                "processing_time": 45.2
            }
            
            # Test the task logic
            from tasks import process_document_task
            
            result = process_document_task.apply(args=[
                b"sample document content",
                "test.pdf",
                {"user_id": "user-123"}
            ])
            
            assert result.successful()
            assert result.result["document_id"] == "doc-123"
    
    def test_embedding_generation_task(self):
        """Test embedding generation task"""
        with patch('worker.tasks.generate_embeddings') as mock_embed:
            mock_embed.return_value = [0.1, 0.2, 0.3] * 256
            
            from tasks import generate_embeddings_task
            
            result = generate_embeddings_task.apply(args=[
                "Sample text content"
            ])
            
            assert result.successful()
            assert len(result.result) == 768
    
    def test_task_failure_handling(self):
        """Test task failure handling"""
        with patch('worker.tasks.process_document_content') as mock_process:
            mock_process.side_effect = Exception("Processing failed")
            
            from tasks import process_document_task
            
            result = process_document_task.apply(args=[
                b"invalid content",
                "test.pdf",
                {}
            ])
            
            assert result.failed()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
