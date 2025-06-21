#!/bin/bash
# Docker health check - simplified version

# Check basic connectivity to both services
nc -z localhost 8501 && nc -z localhost 8000 && echo "healthy" && exit 0

# If above fails, try individual checks
if nc -z localhost 8501; then
    echo "streamlit_only"
    exit 0
fi

if nc -z localhost 8000; then
    echo "fastapi_only" 
    exit 0
fi

echo "unhealthy"
exit 1
