#!/bin/bash
# Improved health check script for both Streamlit and FastAPI

# Function to check if a port is listening
check_port() {
    local port=$1
    local service=$2
    
    if netstat -tuln | grep -q ":$port "; then
        echo "✅ $service port $port is listening"
        return 0
    else
        echo "❌ $service port $port is not listening"
        return 1
    fi
}

# Function to check HTTP endpoint
check_endpoint() {
    local url=$1
    local service=$2
    
    if curl -s --max-time 5 "$url" > /dev/null 2>&1; then
        echo "✅ $service endpoint responding"
        return 0
    else
        echo "❌ $service endpoint not responding"
        return 1
    fi
}

echo "🏥 Health Check Starting..."

# Check if ports are listening
PORT_8501_OK=0
PORT_8000_OK=0

if check_port 8501 "Streamlit"; then
    PORT_8501_OK=1
fi

if check_port 8000 "FastAPI"; then
    PORT_8000_OK=1
fi

# Check HTTP endpoints
STREAMLIT_OK=0
FASTAPI_OK=0

# Try Streamlit health endpoint
if [ $PORT_8501_OK -eq 1 ]; then
    # Try the Streamlit health endpoint first
    if check_endpoint "http://localhost:8501/_stcore/health" "Streamlit Health"; then
        STREAMLIT_OK=1
    else
        # Fallback to basic connection test
        if nc -z localhost 8501; then
            echo "✅ Streamlit basic connection OK"
            STREAMLIT_OK=1
        fi
    fi
fi

# Try FastAPI health endpoint
if [ $PORT_8000_OK -eq 1 ]; then
    if check_endpoint "http://localhost:8000/health" "FastAPI Health"; then
        FASTAPI_OK=1
    else
        # Fallback to basic connection test
        if nc -z localhost 8000; then
            echo "✅ FastAPI basic connection OK"
            FASTAPI_OK=1
        fi
    fi
fi

# Overall health assessment
if [ $STREAMLIT_OK -eq 1 ] && [ $FASTAPI_OK -eq 1 ]; then
    echo "✅ All services healthy"
    exit 0
elif [ $STREAMLIT_OK -eq 1 ] || [ $FASTAPI_OK -eq 1 ]; then
    echo "⚠️  Partial health - some services responding"
    exit 0
else
    echo "❌ No services responding"
    exit 1
fi
