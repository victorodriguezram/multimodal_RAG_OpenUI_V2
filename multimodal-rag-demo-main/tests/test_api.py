import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
import tempfile
import os
from unittest.mock import patch, MagicMock
import json

# Import your FastAPI app
import sys
sys.path.append('../api')
from main import app
from models import SearchRequest, SearchResponse
from database import get_db_session
from services.auth import get_api_key_auth

# Test configuration
TEST_API_KEY = "test-api-key-12345"
TEST_ADMIN_KEY = "test-admin-key-12345"

class TestMultimodalRAGAPI:
    """Test suite for the Multimodal RAG API"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def headers(self):
        """Standard headers for API requests"""
        return {"X-API-Key": TEST_API_KEY}
    
    @pytest.fixture
    def admin_headers(self):
        """Admin headers for admin API requests"""
        return {"X-Admin-Key": TEST_ADMIN_KEY}
    
    @pytest.fixture
    def sample_pdf(self):
        """Create a sample PDF file for testing"""
        content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(content)
            f.flush()
            yield f.name
        os.unlink(f.name)
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
    
    def test_upload_document_success(self, client, headers, sample_pdf):
        """Test successful document upload"""
        with patch('api.services.document_service.DocumentService.process_document_async') as mock_process:
            mock_process.return_value = {"task_id": "test-task-123", "status": "pending"}
            
            with open(sample_pdf, 'rb') as f:
                files = {"file": ("test.pdf", f, "application/pdf")}
                response = client.post("/documents/upload", files=files, headers=headers)
            
            assert response.status_code == 202
            data = response.json()
            assert "task_id" in data
            assert data["status"] in ["pending", "processing"]
    
    def test_upload_document_unauthorized(self, client, sample_pdf):
        """Test document upload without API key"""
        with open(sample_pdf, 'rb') as f:
            files = {"file": ("test.pdf", f, "application/pdf")}
            response = client.post("/documents/upload", files=files)
        
        assert response.status_code == 401
    
    def test_upload_document_invalid_file(self, client, headers):
        """Test upload with invalid file"""
        files = {"file": ("test.txt", b"invalid content", "text/plain")}
        response = client.post("/documents/upload", files=files, headers=headers)
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    def test_search_success(self, client, headers):
        """Test successful search"""
        with patch('api.services.search_service.SearchService.search') as mock_search:
            mock_search.return_value = {
                "results": [
                    {
                        "document_id": "doc-1",
                        "chunk_id": "chunk-1",
                        "content": "Sample content about ETFs",
                        "score": 0.95,
                        "metadata": {"page": 1}
                    }
                ],
                "total_results": 1,
                "query_time_ms": 45.2
            }
            
            search_data = {"query": "What are ETFs?", "top_k": 5}
            response = client.post("/search", json=search_data, headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            assert len(data["results"]) == 1
            assert data["results"][0]["score"] == 0.95
    
    def test_search_unauthorized(self, client):
        """Test search without API key"""
        search_data = {"query": "What are ETFs?"}
        response = client.post("/search", json=search_data)
        
        assert response.status_code == 401
    
    def test_search_invalid_query(self, client, headers):
        """Test search with invalid query"""
        search_data = {"query": "", "top_k": 0}
        response = client.post("/search", json=search_data, headers=headers)
        
        assert response.status_code == 400
    
    def test_multimodal_search(self, client, headers):
        """Test multimodal search with text and image"""
        with patch('api.services.search_service.SearchService.multimodal_search') as mock_search:
            mock_search.return_value = {
                "results": [
                    {
                        "document_id": "doc-2",
                        "chunk_id": "chunk-2",
                        "content": "Image showing financial charts",
                        "score": 0.88,
                        "metadata": {"type": "image"}
                    }
                ],
                "total_results": 1,
                "query_time_ms": 67.8
            }
            
            # Create a simple image file
            image_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
            files = {
                "image": ("test.png", image_content, "image/png")
            }
            data = {"text_query": "financial charts", "top_k": 3}
            
            response = client.post("/search/multimodal", files=files, data=data, headers=headers)
            
            assert response.status_code == 200
            result = response.json()
            assert "results" in result
            assert len(result["results"]) == 1
    
    def test_task_status(self, client, headers):
        """Test task status retrieval"""
        with patch('api.services.task_manager.TaskManager.get_task_status') as mock_status:
            mock_status.return_value = {
                "task_id": "test-task-123",
                "status": "completed",
                "progress": 100,
                "result": {"document_id": "doc-123", "chunks_created": 25},
                "error": None,
                "created_at": "2025-06-26T12:00:00Z",
                "updated_at": "2025-06-26T12:05:00Z"
            }
            
            response = client.get("/tasks/test-task-123", headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "test-task-123"
            assert data["status"] == "completed"
            assert data["progress"] == 100
    
    def test_task_status_not_found(self, client, headers):
        """Test task status for non-existent task"""
        with patch('api.services.task_manager.TaskManager.get_task_status') as mock_status:
            mock_status.return_value = None
            
            response = client.get("/tasks/non-existent-task", headers=headers)
            
            assert response.status_code == 404
    
    def test_n8n_webhook(self, client, headers):
        """Test N8N webhook endpoint"""
        webhook_data = {
            "workflow_id": "test-workflow",
            "execution_id": "exec-123",
            "action": "document_processed",
            "data": {
                "document_id": "doc-456",
                "processing_time": 120
            }
        }
        
        response = client.post("/webhooks/n8n", json=webhook_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "received"
        assert "processed_at" in data
    
    def test_admin_stats_success(self, client, admin_headers):
        """Test admin statistics endpoint"""
        with patch('api.services.admin_service.AdminService.get_system_stats') as mock_stats:
            mock_stats.return_value = {
                "total_documents": 150,
                "total_chunks": 3750,
                "index_size_mb": 45.2,
                "active_tasks": 3,
                "api_calls_today": 1250,
                "uptime_seconds": 86400,
                "memory_usage": {
                    "used_mb": 512.5,
                    "available_mb": 1536.0
                }
            }
            
            response = client.get("/admin/stats", headers=admin_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_documents"] == 150
            assert data["total_chunks"] == 3750
            assert "memory_usage" in data
    
    def test_admin_stats_unauthorized(self, client, headers):
        """Test admin stats with regular API key"""
        response = client.get("/admin/stats", headers=headers)
        
        assert response.status_code == 403
    
    def test_rate_limiting(self, client, headers):
        """Test rate limiting functionality"""
        with patch('api.services.rate_limiter.RateLimiter.is_allowed') as mock_limiter:
            mock_limiter.return_value = False
            
            search_data = {"query": "test query"}
            response = client.post("/search", json=search_data, headers=headers)
            
            assert response.status_code == 429
            data = response.json()
            assert "rate limit" in data["error"].lower()

class TestCoreServices:
    """Test core service functionality"""
    
    def test_document_processing(self):
        """Test document processing logic"""
        from api.services.document_service import DocumentService
        
        service = DocumentService()
        
        # Mock the dependencies
        with patch.object(service, '_extract_text') as mock_extract, \
             patch.object(service, '_generate_embeddings') as mock_embed, \
             patch.object(service, '_store_document') as mock_store:
            
            mock_extract.return_value = "Sample document text"
            mock_embed.return_value = [0.1, 0.2, 0.3] * 256  # 768-dim vector
            mock_store.return_value = "doc-123"
            
            # Test processing
            result = service.process_document(b"sample pdf content", "test.pdf")
            
            assert result["document_id"] == "doc-123"
            mock_extract.assert_called_once()
            mock_embed.assert_called_once()
            mock_store.assert_called_once()
    
    def test_search_service(self):
        """Test search service functionality"""
        from api.services.search_service import SearchService
        
        service = SearchService()
        
        with patch.object(service, '_get_query_embedding') as mock_embed, \
             patch.object(service, '_vector_search') as mock_search:
            
            mock_embed.return_value = [0.1, 0.2, 0.3] * 256
            mock_search.return_value = [
                {
                    "document_id": "doc-1",
                    "chunk_id": "chunk-1",
                    "content": "Sample content",
                    "score": 0.95,
                    "metadata": {}
                }
            ]
            
            results = service.search("test query", top_k=5)
            
            assert len(results["results"]) == 1
            assert results["results"][0]["score"] == 0.95
            mock_embed.assert_called_once_with("test query")
            mock_search.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
