# config.py
import os

# API Keys from environment variables
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Model configuration
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")

# Application settings
DATA_DIR = os.getenv("DATA_DIR", "data")
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", "50"))  # MB
MAX_CONCURRENT_DOCS = int(os.getenv("MAX_CONCURRENT_DOCS", "5"))

# Validate required environment variables
if not COHERE_API_KEY:
    raise ValueError("COHERE_API_KEY environment variable is required")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")
