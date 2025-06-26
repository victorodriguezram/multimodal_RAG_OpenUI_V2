"""
Pydantic models for API request/response schemas
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator

# Enums
class ContentType(str, Enum):
    TEXT = "text"
    IMAGE = "image"

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class SearchResultType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    MULTIMODAL = "multimodal"

# Base models
class BaseResponse(BaseModel):
    success: bool = True
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Authentication models
class User(BaseModel):
    id: str
    email: str
    is_admin: bool = False
    api_key: str
    rate_limit_per_minute: int = 60
    created_at: datetime
    updated_at: datetime

class APIKeyRequest(BaseModel):
    email: str
    description: Optional[str] = None

class APIKeyResponse(BaseResponse):
    api_key: str
    user_id: str
    expires_at: Optional[datetime] = None

# Document models
class DocumentInfo(BaseModel):
    id: str
    filename: str
    size: int
    content_type: str
    upload_date: datetime
    status: str
    page_count: Optional[int] = None
    text_chunks: int = 0
    image_chunks: int = 0
    user_id: str

class DocumentUploadResponse(BaseResponse):
    task_id: str
    status: str
    estimated_completion: datetime

# Search models
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results to return")
    include_answer: bool = Field(default=True, description="Generate AI answer")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Search filters")
    
    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()

class SearchResult(BaseModel):
    content: str
    source: str
    content_type: ContentType
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    page: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    preview_url: Optional[str] = None

class SearchResponse(BaseResponse):
    query: str
    results: List[SearchResult]
    answer: Optional[str] = None
    total_results: int
    processing_time: float

# Task models
class TaskInfo(BaseModel):
    id: str
    type: str
    status: TaskStatus
    progress: float = Field(..., ge=0.0, le=100.0)
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    user_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TaskStatusResponse(BaseResponse):
    task: TaskInfo

# N8N Integration models
class N8NSearchRequest(BaseModel):
    query: str
    user_id: str
    options: Dict[str, Any] = Field(default_factory=dict)

class N8NSearchResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class N8NUploadResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class N8NWebhookConfig(BaseModel):
    url: str
    secret: str
    events: List[str] = Field(default_factory=lambda: ["document.processed", "search.completed"])

# Admin models
class SystemStats(BaseModel):
    total_documents: int
    total_embeddings: int
    total_users: int
    total_searches_today: int
    storage_used_mb: float
    average_response_time: float
    uptime_seconds: int

class AdminStatsResponse(BaseResponse):
    stats: SystemStats

# Error models
class ErrorResponse(BaseModel):
    success: bool = False
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Batch operation models
class BatchSearchRequest(BaseModel):
    queries: List[str] = Field(..., min_items=1, max_items=10)
    user_id: str
    options: Dict[str, Any] = Field(default_factory=dict)

class BatchSearchResponse(BaseModel):
    success: bool
    results: List[SearchResponse]
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# File upload models
class FileValidationResponse(BaseModel):
    filename: str
    valid: bool
    size: int
    error_message: Optional[str] = None

class BulkUploadRequest(BaseModel):
    user_id: str
    files: List[str]  # File paths or URLs
    options: Dict[str, Any] = Field(default_factory=dict)

# Monitoring models
class HealthCheckResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    dependencies: Dict[str, str] = Field(default_factory=dict)

class MetricsResponse(BaseModel):
    requests_total: int
    requests_per_minute: float
    average_response_time: float
    error_rate: float
    active_users: int
    storage_usage: Dict[str, float]

# Configuration models
class APIConfig(BaseModel):
    max_file_size_mb: int
    supported_file_types: List[str]
    rate_limit_per_minute: int
    max_concurrent_uploads: int
    embedding_model: str
    llm_model: str
