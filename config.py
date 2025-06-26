# config.py
import os
import sys

# API Keys from environment variables with validation
COHERE_API_KEY = os.getenv('COHERE_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Check if API keys are properly set
if not COHERE_API_KEY or COHERE_API_KEY == 'your_COHERE_API_KEY_here':
    print("ERROR: COHERE_API_KEY environment variable not set or contains placeholder value")
    print("Please set your actual Cohere API key in the .env file")
    sys.exit(1)

if not GEMINI_API_KEY or GEMINI_API_KEY == 'your_GEMINI_API_KEY_here':
    print("ERROR: GEMINI_API_KEY environment variable not set or contains placeholder value")
    print("Please set your actual Gemini API key in the .env file")
    sys.exit(1)

# Model configuration
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash-preview-04-17')

# Data directory
DATA_DIR = os.getenv('DATA_DIR', 'data')

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

print(f"✅ Configuration loaded successfully")
print(f"   - Cohere API Key: {'*' * (len(COHERE_API_KEY) - 4) + COHERE_API_KEY[-4:]}")
print(f"   - Gemini API Key: {'*' * (len(GEMINI_API_KEY) - 4) + GEMINI_API_KEY[-4:]}")
print(f"   - Gemini Model: {GEMINI_MODEL}")
print(f"   - Data Directory: {DATA_DIR}")
