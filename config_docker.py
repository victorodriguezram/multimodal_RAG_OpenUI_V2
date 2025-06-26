# Enhanced config.py for Docker deployment
import os

# API Keys from environment variables
COHERE_API_KEY = os.getenv('COHERE_API_KEY', 'your_COHERE_API_KEY_here')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'your_GEMINI_API_KEY_here')

# Model configuration
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash-preview-04-17')

# Data directory
DATA_DIR = os.getenv('DATA_DIR', 'data')

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)
