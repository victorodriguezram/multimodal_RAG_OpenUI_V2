"""
Configuration management for the API
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Configuration
    API_SECRET_KEY: str = Field(..., description="Secret key for JWT tokens")
    API_HOST: str = Field(default="0.0.0.0", description="API host")
    API_PORT: int = Field(default=8000, description="API port")
    DEBUG: bool = Field(default=False, description="Debug mode")
    
    # Security
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8501"],
        description="Allowed CORS origins"
    )
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1", "*"],
        description="Allowed hosts"
    )
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="Default rate limit per minute")
    RATE_LIMIT_BURST: int = Field(default=10, description="Rate limit burst allowance")
    
    # File Upload
    MAX_FILE_SIZE_MB: int = Field(default=50, description="Maximum file size in MB")
    SUPPORTED_FILE_TYPES: List[str] = Field(
        default=["pdf"],
        description="Supported file types"
    )
    MAX_CONCURRENT_UPLOADS: int = Field(default=5, description="Maximum concurrent uploads per user")
    
    # AI Model Configuration
    COHERE_API_KEY: str = Field(..., description="Cohere API key")
    GEMINI_API_KEY: str = Field(..., description="Gemini API key")
    GEMINI_MODEL: str = Field(
        default="gemini-2.5-flash-preview-04-17",
        description="Gemini model name"
    )
    EMBEDDING_MODEL: str = Field(
        default="embed-v4.0",
        description="Cohere embedding model"
    )
    
    # Database Configuration
    POSTGRES_URL: str = Field(..., description="PostgreSQL connection URL")
    DATABASE_ECHO: bool = Field(default=False, description="Echo SQL queries")
    DATABASE_POOL_SIZE: int = Field(default=10, description="Database connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, description="Database max overflow connections")
    
    # Redis Configuration
    REDIS_URL: str = Field(..., description="Redis connection URL")
    REDIS_MAX_CONNECTIONS: int = Field(default=10, description="Redis max connections")
    
    # Storage Configuration
    DATA_VOLUME_PATH: str = Field(default="/app/data", description="Data volume path")
    FAISS_INDEX_PATH: str = Field(default="faiss_indices", description="FAISS index directory")
    UPLOAD_PATH: str = Field(default="uploads", description="Upload directory")
    PREVIEW_PATH: str = Field(default="previews", description="Preview images directory")
    
    # N8N Integration
    N8N_WEBHOOK_SECRET: str = Field(default="", description="N8N webhook secret")
    N8N_API_KEY: str = Field(default="", description="N8N API key")
    N8N_BASE_URL: str = Field(default="", description="N8N base URL")
    
    # Celery Configuration
    CELERY_BROKER_URL: str = Field(default="", description="Celery broker URL")
    CELERY_RESULT_BACKEND: str = Field(default="", description="Celery result backend")
    CELERY_TASK_TIMEOUT: int = Field(default=3600, description="Celery task timeout")
    
    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )
    
    # Monitoring
    ENABLE_METRICS: bool = Field(default=True, description="Enable Prometheus metrics")
    METRICS_PATH: str = Field(default="/metrics", description="Metrics endpoint path")
    
    # Performance
    WORKER_PROCESSES: int = Field(default=4, description="Number of worker processes")
    WORKER_THREADS: int = Field(default=1, description="Number of threads per worker")
    KEEP_ALIVE: int = Field(default=2, description="Keep alive timeout")
    
    # Search Configuration
    DEFAULT_TOP_K: int = Field(default=5, description="Default number of search results")
    MAX_TOP_K: int = Field(default=20, description="Maximum number of search results")
    SEARCH_TIMEOUT: int = Field(default=30, description="Search timeout in seconds")
    
    # Document Processing
    MAX_TEXT_CHUNK_SIZE: int = Field(default=1000, description="Maximum text chunk size")
    TEXT_OVERLAP: int = Field(default=200, description="Text chunk overlap")
    IMAGE_DPI: int = Field(default=200, description="Image extraction DPI")
    MAX_IMAGE_SIZE: int = Field(default=1568*1568, description="Maximum image size for embedding")
    
    # SSL Configuration
    SSL_CERT_PATH: Optional[str] = Field(default=None, description="SSL certificate path")
    SSL_KEY_PATH: Optional[str] = Field(default=None, description="SSL private key path")
    
    @property
    def MAX_FILE_SIZE_BYTES(self) -> int:
        """Convert MB to bytes"""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024
    
    @property
    def UPLOAD_FULL_PATH(self) -> str:
        """Full upload directory path"""
        return os.path.join(self.DATA_VOLUME_PATH, self.UPLOAD_PATH)
    
    @property
    def FAISS_FULL_PATH(self) -> str:
        """Full FAISS index directory path"""
        return os.path.join(self.DATA_VOLUME_PATH, self.FAISS_INDEX_PATH)
    
    @property
    def PREVIEW_FULL_PATH(self) -> str:
        """Full preview directory path"""
        return os.path.join(self.DATA_VOLUME_PATH, self.PREVIEW_PATH)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Global settings instance
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """Get application settings singleton"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

def reload_settings() -> Settings:
    """Reload settings (useful for testing)"""
    global _settings
    _settings = Settings()
    return _settings
