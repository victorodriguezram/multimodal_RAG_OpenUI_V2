#!/bin/bash
# Debug startup script with enhanced logging

set -e  # Exit on any error

echo "=================================================="
echo "🚀 DEBUG MODE: Multimodal RAG Development Environment"
echo "=================================================="

# Show system info
echo "🖥️  System Information:"
echo "User: $(whoami)"
echo "Working Dir: $(pwd)"
echo "IP Address: $(hostname -I || echo 'unknown')"
echo "Date: $(date)"

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

# Show network configuration
echo "🌐 Network Configuration:"
echo "Listening interfaces:"
netstat -tuln | head -10

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p $DATA_DIR/uploads
chmod 755 $DATA_DIR
chmod 755 $DATA_DIR/uploads

# Check dependencies
echo "🔍 Checking Python dependencies..."
python3 -c "import streamlit; print('✅ Streamlit:', streamlit.__version__)"
python3 -c "import fastapi; print('✅ FastAPI:', fastapi.__version__)"
python3 -c "import uvicorn; print('✅ Uvicorn:', uvicorn.__version__)"
python3 -c "import cohere; print('✅ Cohere: installed')"
python3 -c "import google.generativeai; print('✅ Google AI: installed')"

# Test API connections
echo "🌐 Testing API connections..."
python3 -c "
import cohere
try:
    client = cohere.ClientV2(api_key='$COHERE_API_KEY')
    print('✅ Cohere API: Connection successful')
except Exception as e:
    print('❌ Cohere API error:', str(e))
"

echo "▶️  Starting services with enhanced logging..."

# Start Streamlit with debug logging
echo "🎬 Starting Streamlit on 0.0.0.0:8501..."
STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
STREAMLIT_SERVER_PORT=8501 \
STREAMLIT_SERVER_HEADLESS=true \
STREAMLIT_SERVER_ENABLE_CORS=true \
STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false \
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
streamlit run app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.enableCORS true \
    --server.enableXsrfProtection false \
    --server.allowRunOnSave true \
    --logger.level debug &

STREAMLIT_PID=$!
echo "✅ Streamlit started with PID: $STREAMLIT_PID"

# Wait a moment for Streamlit to start
echo "⏱️  Waiting for Streamlit to initialize..."
sleep 10

# Check if Streamlit is actually running
if ps -p $STREAMLIT_PID > /dev/null; then
    echo "✅ Streamlit process is running"
else
    echo "❌ Streamlit process died!"
    exit 1
fi

# Start FastAPI with debug logging
echo "🎬 Starting FastAPI on 0.0.0.0:8000..."
python3 -m uvicorn api:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level debug &

FASTAPI_PID=$!
echo "✅ FastAPI started with PID: $FASTAPI_PID"

# Wait a moment for FastAPI to start
echo "⏱️  Waiting for FastAPI to initialize..."
sleep 5

# Check if FastAPI is actually running
if ps -p $FASTAPI_PID > /dev/null; then
    echo "✅ FastAPI process is running"
else
    echo "❌ FastAPI process died!"
    exit 1
fi

# Show listening ports
echo "🔍 Checking listening ports..."
netstat -tuln | grep -E ":(8501|8000|6379) "

# Test internal connectivity
echo "🔗 Testing internal connectivity..."
if nc -z localhost 8501; then
    echo "✅ Streamlit port 8501 is accessible internally"
else
    echo "❌ Streamlit port 8501 is NOT accessible internally"
fi

if nc -z localhost 8000; then
    echo "✅ FastAPI port 8000 is accessible internally"
else
    echo "❌ FastAPI port 8000 is NOT accessible internally"
fi

# Show service URLs
echo "=================================================="
echo "🌟 SERVICES READY:"
echo "📍 Streamlit UI: http://0.0.0.0:8501"
echo "📍 FastAPI API: http://0.0.0.0:8000"
echo "📍 FastAPI docs: http://0.0.0.0:8000/docs"
echo "📍 Health check: http://0.0.0.0:8000/health"
echo ""
echo "🌐 For external access, replace 0.0.0.0 with your server's IP"
echo "=================================================="

# Monitor services with detailed logging
echo "👀 Monitoring services (detailed mode)..."
while true; do
    if ! kill -0 $STREAMLIT_PID 2>/dev/null; then
        echo "❌ Streamlit process died at $(date)!"
        echo "Checking logs..."
        exit 1
    fi
    
    if ! kill -0 $FASTAPI_PID 2>/dev/null; then
        echo "❌ FastAPI process died at $(date)!"
        exit 1
    fi
    
    # Show resource usage
    echo "💓 Services running at $(date)"
    echo "   Streamlit PID $STREAMLIT_PID - CPU: $(ps -o %cpu -p $STREAMLIT_PID --no-headers 2>/dev/null || echo 'N/A')%"
    echo "   FastAPI PID $FASTAPI_PID - CPU: $(ps -o %cpu -p $FASTAPI_PID --no-headers 2>/dev/null || echo 'N/A')%"
    
    # Check ports every cycle
    if ! nc -z localhost 8501; then
        echo "⚠️  WARNING: Streamlit port 8501 not responding"
    fi
    if ! nc -z localhost 8000; then
        echo "⚠️  WARNING: FastAPI port 8000 not responding"
    fi
    
    sleep 30
done
