#!/bin/bash
# Debugging script for external access issues

echo "🔍 Docker RAG System - Connectivity Diagnostics"
echo "==============================================="

# Check if containers are running
echo ""
echo "📦 Container Status:"
sudo docker-compose -f docker-compose.dev.yml ps

# Check container health
echo ""
echo "🏥 Health Status:"
CONTAINER_ID=$(sudo docker-compose -f docker-compose.dev.yml ps -q rag-app)
if [ ! -z "$CONTAINER_ID" ]; then
    echo "Container ID: $CONTAINER_ID"
    sudo docker inspect $CONTAINER_ID --format='{{.State.Health.Status}}'
else
    echo "❌ Container not found"
fi

# Check logs
echo ""
echo "📋 Recent Container Logs:"
sudo docker-compose -f docker-compose.dev.yml logs --tail=20 rag-app

# Check port bindings
echo ""
echo "🌐 Port Bindings:"
sudo docker port $CONTAINER_ID 2>/dev/null || echo "❌ Container not running"

# Check if ports are listening on host
echo ""
echo "🔌 Host Port Status:"
sudo netstat -tuln | grep -E ":(8501|8000)" || echo "❌ Ports not listening"

# Test internal container connectivity
echo ""
echo "🔗 Internal Container Tests:"
if [ ! -z "$CONTAINER_ID" ]; then
    echo "Testing Streamlit (8501):"
    sudo docker exec $CONTAINER_ID curl -f http://localhost:8501 >/dev/null 2>&1 && echo "✅ Streamlit OK" || echo "❌ Streamlit failed"
    
    echo "Testing FastAPI (8000):"
    sudo docker exec $CONTAINER_ID curl -f http://localhost:8000/health >/dev/null 2>&1 && echo "✅ FastAPI OK" || echo "❌ FastAPI failed"
else
    echo "❌ Cannot test - container not running"
fi

# Test host connectivity
echo ""
echo "🏠 Host Connectivity Tests:"
echo "Testing localhost:8501:"
curl -f http://localhost:8501 >/dev/null 2>&1 && echo "✅ Host->8501 OK" || echo "❌ Host->8501 failed"

echo "Testing localhost:8000:"
curl -f http://localhost:8000/health >/dev/null 2>&1 && echo "✅ Host->8000 OK" || echo "❌ Host->8000 failed"

# Check firewall
echo ""
echo "🔥 Firewall Status:"
if command -v ufw &> /dev/null; then
    echo "UFW Status:"
    sudo ufw status | grep -E "(8501|8000)" || echo "No rules for ports 8501/8000"
    echo ""
    echo "To allow ports: sudo ufw allow 8501 && sudo ufw allow 8000"
elif command -v firewall-cmd &> /dev/null; then
    echo "Firewalld Status:"
    sudo firewall-cmd --list-ports | grep -E "(8501|8000)" || echo "No rules for ports 8501/8000"
    echo ""
    echo "To allow ports: sudo firewall-cmd --permanent --add-port=8501/tcp --add-port=8000/tcp && sudo firewall-cmd --reload"
else
    echo "No recognized firewall found"
fi

# Check environment variables in container
echo ""
echo "🌍 Environment Variables in Container:"
if [ ! -z "$CONTAINER_ID" ]; then
    echo "COHERE_API_KEY: $(sudo docker exec $CONTAINER_ID printenv COHERE_API_KEY | cut -c1-10)..."
    echo "GEMINI_API_KEY: $(sudo docker exec $CONTAINER_ID printenv GEMINI_API_KEY | cut -c1-10)..."
    echo "DATA_DIR: $(sudo docker exec $CONTAINER_ID printenv DATA_DIR)"
else
    echo "❌ Container not running"
fi

# Check server IP
echo ""
echo "🌍 Server IP Information:"
echo "Internal IP addresses:"
ip addr show | grep -E "inet.*global" | awk '{print "  " $2}' | cut -d'/' -f1

echo ""
echo "External IP (if available):"
curl -s ifconfig.me 2>/dev/null && echo "" || echo "Unable to determine external IP"

echo ""
echo "📝 Summary:"
echo "1. Check container health above"
echo "2. Ensure firewall allows ports 8501 and 8000"
echo "3. For Google Cloud, check security groups allow these ports"
echo "4. Access via: http://YOUR_EXTERNAL_IP:8501"
echo "5. If still failing, check cloud provider firewall rules"

echo ""
echo "🛠️  Quick Fixes:"
echo "Restart containers: sudo docker-compose -f docker-compose.dev.yml restart"
echo "Rebuild containers: sudo docker-compose -f docker-compose.dev.yml up --build -d"
echo "View live logs: sudo docker-compose -f docker-compose.dev.yml logs -f rag-app"
