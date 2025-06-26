#!/bin/bash

# Debug imports first
echo "🔍 Testing imports..."
python debug_imports.py
if [ $? -ne 0 ]; then
    echo "❌ Import test failed! Check dependencies."
    exit 1
fi

echo "✅ All imports successful, starting services..."

# Start Streamlit in the background
streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true &

# Start FastAPI
uvicorn api_server:app --host 0.0.0.0 --port 8000
