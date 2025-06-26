"""
FastAPI main application for Multimodal RAG System
Production-ready API with N8N integration capabilities
"""

import os
import logging
import asyncio
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import structlog
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import httpx

from .models import *
from .services.auth import AuthService
from .services.rate_limiter import RateLimiter
from .services.document_service import DocumentService
from .services.search_service import SearchService
from .services.task_manager import TaskManager
from .database import get_db_session
from .config import get_settings

# Load OpenAPI specification
import yaml
try:
    with open(os.path.join(os.path.dirname(__file__), "openapi.yaml"), "r") as f:
        openapi_spec = yaml.safe_load(f)
except FileNotFoundError:
    openapi_spec = None

# Initialize structured logger
logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter('multimodal_rag_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('multimodal_rag_request_duration_seconds', 'Request duration')
DOCUMENT_PROCESSING_DURATION = Histogram('multimodal_rag_document_processing_duration_seconds', 'Document processing duration')
SEARCH_DURATION = Histogram('multimodal_rag_search_duration_seconds', 'Search operation duration')

# Settings
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    logger.info("Starting Multimodal RAG API")
    
    # Initialize services
    await DocumentService.initialize()
    await SearchService.initialize()
    await TaskManager.initialize()
    
    logger.info("API startup complete")
    yield
    
    # Cleanup
    logger.info("Shutting down API")
    await DocumentService.cleanup()
    await SearchService.cleanup()
    await TaskManager.cleanup()

# Create FastAPI app
app = FastAPI(
    title="Multimodal RAG API",
    description="Production-ready Multimodal Retrieval-Augmented Generation API with N8N integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Security
security = HTTPBearer()
auth_service = AuthService()
rate_limiter = RateLimiter()

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Dependencies
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate API key and get current user"""
    try:
        user = await auth_service.validate_api_key(credentials.credentials)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid API key")
        return user
    except Exception as e:
        logger.error("Authentication error", error=str(e))
        raise HTTPException(status_code=401, detail="Authentication failed")

async def check_rate_limit(user=Depends(get_current_user)):
    """Check rate limiting for user"""
    if not await rate_limiter.check_limit(user.id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return user

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for load balancers"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

# Metrics endpoint
@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()

# Document management endpoints
@app.post("/documents/upload", response_model=DocumentUploadResponse, tags=["Documents"])
async def upload_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    user=Depends(check_rate_limit),
    db=Depends(get_db_session)
):
    """
    Upload and process documents for indexing
    
    - **files**: List of PDF files to upload and process
    - Returns task ID for tracking processing status
    """
    try:
        REQUEST_COUNT.labels(method="POST", endpoint="/documents/upload", status="success").inc()
        
        # Validate files
        for file in files:
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(status_code=400, detail=f"Only PDF files are supported. Got: {file.filename}")
            
            if file.size > settings.MAX_FILE_SIZE_BYTES:
                raise HTTPException(
                    status_code=400, 
                    detail=f"File {file.filename} exceeds maximum size of {settings.MAX_FILE_SIZE_MB}MB"
                )
        
        # Create processing task
        task = await TaskManager.create_document_processing_task(files, user.id)
        
        # Start background processing
        background_tasks.add_task(DocumentService.process_documents_async, task.id, files, user.id)
        
        logger.info("Document upload initiated", task_id=task.id, user_id=user.id, file_count=len(files))
        
        return DocumentUploadResponse(
            task_id=task.id,
            status="processing",
            message=f"Processing {len(files)} documents",
            estimated_completion=datetime.utcnow() + timedelta(minutes=len(files) * 2)
        )
        
    except HTTPException:
        REQUEST_COUNT.labels(method="POST", endpoint="/documents/upload", status="error").inc()
        raise
    except Exception as e:
        REQUEST_COUNT.labels(method="POST", endpoint="/documents/upload", status="error").inc()
        logger.error("Document upload error", error=str(e), user_id=user.id)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/documents", response_model=List[DocumentInfo], tags=["Documents"])
async def list_documents(
    user=Depends(check_rate_limit),
    db=Depends(get_db_session)
):
    """List all documents for the authenticated user"""
    try:
        documents = await DocumentService.get_user_documents(user.id)
        return documents
    except Exception as e:
        logger.error("Error listing documents", error=str(e), user_id=user.id)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/documents/{document_id}", tags=["Documents"])
async def delete_document(
    document_id: str,
    user=Depends(check_rate_limit),
    db=Depends(get_db_session)
):
    """Delete a specific document and its embeddings"""
    try:
        success = await DocumentService.delete_document(document_id, user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"message": "Document deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting document", error=str(e), document_id=document_id, user_id=user.id)
        raise HTTPException(status_code=500, detail="Internal server error")

# Search endpoints
@app.post("/search", response_model=SearchResponse, tags=["Search"])
async def search_documents(
    request: SearchRequest,
    user=Depends(check_rate_limit),
    db=Depends(get_db_session)
):
    """
    Search through indexed documents using natural language queries
    
    - **query**: Natural language search query
    - **top_k**: Number of results to return (default: 5)
    - **include_answer**: Whether to generate an AI answer (default: true)
    - **filters**: Optional filters for search results
    """
    try:
        with SEARCH_DURATION.time():
            REQUEST_COUNT.labels(method="POST", endpoint="/search", status="success").inc()
            
            results = await SearchService.search(
                query=request.query,
                user_id=user.id,
                top_k=request.top_k,
                include_answer=request.include_answer,
                filters=request.filters
            )
            
            logger.info("Search completed", user_id=user.id, query=request.query, results_count=len(results.results))
            
            return results
            
    except HTTPException:
        REQUEST_COUNT.labels(method="POST", endpoint="/search", status="error").inc()
        raise
    except Exception as e:
        REQUEST_COUNT.labels(method="POST", endpoint="/search", status="error").inc()
        logger.error("Search error", error=str(e), user_id=user.id, query=request.query)
        raise HTTPException(status_code=500, detail="Internal server error")

# N8N Integration endpoints
@app.post("/n8n/webhook/search", response_model=N8NSearchResponse, tags=["N8N Integration"])
async def n8n_webhook_search(
    request: N8NSearchRequest,
    webhook_secret: str = Query(..., description="N8N webhook secret for authentication")
):
    """
    N8N webhook endpoint for search operations
    
    - **query**: Search query from N8N workflow
    - **user_id**: User ID for document access
    - **options**: Search options and parameters
    """
    try:
        # Validate webhook secret
        if webhook_secret != settings.N8N_WEBHOOK_SECRET:
            raise HTTPException(status_code=401, detail="Invalid webhook secret")
        
        # Perform search
        search_request = SearchRequest(
            query=request.query,
            top_k=request.options.get("top_k", 5),
            include_answer=request.options.get("include_answer", True),
            filters=request.options.get("filters", {})
        )
        
        results = await SearchService.search(
            query=search_request.query,
            user_id=request.user_id,
            top_k=search_request.top_k,
            include_answer=search_request.include_answer,
            filters=search_request.filters
        )
        
        # Format response for N8N
        n8n_response = N8NSearchResponse(
            success=True,
            data={
                "answer": results.answer,
                "results": [
                    {
                        "content": r.content,
                        "source": r.source,
                        "score": r.similarity_score,
                        "type": r.content_type,
                        "metadata": r.metadata
                    }
                    for r in results.results
                ],
                "query": request.query,
                "timestamp": datetime.utcnow().isoformat()
            },
            message="Search completed successfully"
        )
        
        logger.info("N8N search completed", user_id=request.user_id, query=request.query)
        return n8n_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("N8N search error", error=str(e), query=request.query)
        return N8NSearchResponse(
            success=False,
            data={},
            message=f"Search failed: {str(e)}"
        )

@app.post("/n8n/webhook/upload", response_model=N8NUploadResponse, tags=["N8N Integration"])
async def n8n_webhook_upload(
    files: List[UploadFile] = File(...),
    user_id: str = Form(...),
    webhook_secret: str = Form(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    N8N webhook endpoint for document upload
    """
    try:
        # Validate webhook secret
        if webhook_secret != settings.N8N_WEBHOOK_SECRET:
            raise HTTPException(status_code=401, detail="Invalid webhook secret")
        
        # Create processing task
        task = await TaskManager.create_document_processing_task(files, user_id)
        
        # Start background processing
        background_tasks.add_task(DocumentService.process_documents_async, task.id, files, user_id)
        
        return N8NUploadResponse(
            success=True,
            data={
                "task_id": task.id,
                "status": "processing",
                "files_count": len(files),
                "estimated_completion": (datetime.utcnow() + timedelta(minutes=len(files) * 2)).isoformat()
            },
            message="Document processing started"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("N8N upload error", error=str(e), user_id=user_id)
        return N8NUploadResponse(
            success=False,
            data={},
            message=f"Upload failed: {str(e)}"
        )

# Task management endpoints
@app.get("/tasks/{task_id}", response_model=TaskStatus, tags=["Tasks"])
async def get_task_status(
    task_id: str,
    user=Depends(check_rate_limit)
):
    """Get the status of a background task"""
    try:
        task = await TaskManager.get_task_status(task_id, user.id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return task
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting task status", error=str(e), task_id=task_id, user_id=user.id)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/tasks", response_model=List[TaskStatus], tags=["Tasks"])
async def list_user_tasks(
    user=Depends(check_rate_limit),
    limit: int = Query(default=10, le=100)
):
    """List recent tasks for the authenticated user"""
    try:
        tasks = await TaskManager.get_user_tasks(user.id, limit)
        return tasks
    except Exception as e:
        logger.error("Error listing tasks", error=str(e), user_id=user.id)
        raise HTTPException(status_code=500, detail="Internal server error")

# Admin endpoints
@app.get("/admin/stats", tags=["Admin"])
async def get_system_stats(user=Depends(get_current_user)):
    """Get system statistics (admin only)"""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        stats = await DocumentService.get_system_stats()
        return stats
    except Exception as e:
        logger.error("Error getting system stats", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,
        log_level="info"
    )
