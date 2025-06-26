FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
COPY api_requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r api_requirements.txt

# Copy application code
COPY multimodal-rag-demo-main/ .
# Override with updated files
COPY config.py .
COPY api_server.py .
COPY start.sh .
COPY debug_imports.py .

# Create necessary directories
RUN mkdir -p data uploads

# Make start script executable
RUN chmod +x start.sh

# Expose ports
EXPOSE 8501 8000

# Start both Streamlit and FastAPI
CMD ["./start.sh"]
