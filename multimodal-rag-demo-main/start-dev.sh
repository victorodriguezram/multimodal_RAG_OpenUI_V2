#!/bin/bash
# Development startup script with debugging

set -e  # Exit on any error

echo "=================================================="
echo "🚀 Starting Multimodal RAG Development Environment"
echo "=================================================="

# Environment validation
echo "🔍 Checking environment variables..."
if [ -z "$COHERE_API_KEY" ]; then
    echo "❌ ERROR: COHERE_API_KEY is not set!"
    exit 1
fi

if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ ERROR: GEMINI_API_KEY is not set!"
    exit 1
fi

echo "✅ COHERE_API_KEY: ${COHERE_API_KEY:0:10}..."
echo "✅ GEMINI_API_KEY: ${GEMINI_API_KEY:0:10}..."
echo "✅ DATA_DIR: $DATA_DIR"

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p $DATA_DIR/uploads
chmod 755 $DATA_DIR
chmod 755 $DATA_DIR/uploads

# Check dependencies
echo "🔍 Checking Python dependencies..."
python -c "import streamlit; print('✅ Streamlit:', streamlit.__version__)"
python -c "import fastapi; print('✅ FastAPI:', fastapi.__version__)"
python -c "import uvicorn; print('✅ Uvicorn:', uvicorn.__version__)"
python -c "import cohere; print('✅ Cohere: installed')"
python -c "import google.generativeai; print('✅ Google AI: installed')"

# Test API connections
echo "🌐 Testing API connections..."
python -c "
import cohere
try:
    client = cohere.ClientV2(api_key='$COHERE_API_KEY')
    print('✅ Cohere API: Connection successful')
except Exception as e:
    print('❌ Cohere API error:', str(e))
"

# Start services with proper error handling
echo "🎬 Starting services..."

# Start Streamlit
echo "▶️  Starting Streamlit on port 8501..."
streamlit run app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.enableCORS true \
    --server.enableXsrfProtection false \
    --server.fileWatcherType auto \
    --server.allowRunOnSave true \
    --browser.gatherUsageStats false \
    --logger.level debug &

STREAMLIT_PID=$!
echo "✅ Streamlit started with PID: $STREAMLIT_PID"

# Wait a moment for Streamlit to start
sleep 5

# Start FastAPI
echo "▶️  Starting FastAPI on port 8000..."
python -m uvicorn api:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info &

FASTAPI_PID=$!
echo "✅ FastAPI started with PID: $FASTAPI_PID"

# Monitor services
echo "👀 Monitoring services..."
echo "📍 Streamlit UI: http://0.0.0.0:8501"
echo "📍 FastAPI docs: http://0.0.0.0:8000/docs"
echo "📍 Health check: http://0.0.0.0:8000/health"

# Keep the script running and monitor processes
while true; do
    if ! kill -0 $STREAMLIT_PID 2>/dev/null; then
        echo "❌ Streamlit process died!"
        exit 1
    fi
    
    if ! kill -0 $FASTAPI_PID 2>/dev/null; then
        echo "❌ FastAPI process died!"
        exit 1
    fi
    
    sleep 30
    echo "💓 Services are running... ($(date))"
done
