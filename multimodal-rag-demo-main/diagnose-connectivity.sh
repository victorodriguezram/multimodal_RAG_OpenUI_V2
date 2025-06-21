#!/bin/bash
# Debugging script for external connectivity issues

echo "=================================================="
echo "🔍 RAG System Connectivity Diagnostic"
echo "=================================================="

# Check if Docker is running
echo "🐳 Checking Docker status..."
if systemctl is-active --quiet docker; then
    echo "✅ Docker is running"
else
    echo "❌ Docker is not running!"
    echo "Run: sudo systemctl start docker"
    exit 1
fi

# Check Docker Compose
echo "🔧 Checking Docker Compose..."
if command -v docker-compose &> /dev/null; then
    echo "✅ Docker Compose found: $(docker-compose --version)"
else
    echo "❌ Docker Compose not found!"
    exit 1
fi

# Check containers
echo "🏃 Checking running containers..."
docker ps

# Check container logs for errors
echo "📝 Checking container logs (last 20 lines)..."
if docker ps --format "table {{.Names}}" | grep -q "multimodal-rag-app"; then
    CONTAINER_NAME=$(docker ps --format "table {{.Names}}" | grep "multimodal-rag-app" | head -1)
    echo "Container: $CONTAINER_NAME"
    docker logs --tail 20 "$CONTAINER_NAME"
fi

# Check port bindings
echo "🔌 Checking port bindings..."
docker ps --format "table {{.Names}}\t{{.Ports}}" | grep -E "(8501|8000)"

# Test internal connectivity
echo "🔗 Testing internal connectivity..."
if docker ps --format "table {{.Names}}" | grep -q "multimodal-rag-app"; then
    CONTAINER_NAME=$(docker ps --format "table {{.Names}}" | grep "multimodal-rag-app" | head -1)
    
    echo "Testing Streamlit (8501)..."
    docker exec "$CONTAINER_NAME" nc -z localhost 8501 && echo "✅ Streamlit OK" || echo "❌ Streamlit not responding"
    
    echo "Testing FastAPI (8000)..."
    docker exec "$CONTAINER_NAME" nc -z localhost 8000 && echo "✅ FastAPI OK" || echo "❌ FastAPI not responding"
fi

# Check host networking
echo "🌐 Checking host networking..."
echo "Server IP addresses:"
hostname -I

echo "Listening ports on host:"
netstat -tuln | grep -E ":(8501|8000|6379) " || echo "No relevant ports found"

# Test external connectivity
echo "🌍 Testing external connectivity..."
echo "Testing localhost access..."
curl -s --max-time 5 http://localhost:8501 >/dev/null && echo "✅ Localhost:8501 OK" || echo "❌ Localhost:8501 failed"
curl -s --max-time 5 http://localhost:8000/health >/dev/null && echo "✅ Localhost:8000 OK" || echo "❌ Localhost:8000 failed"

# Check firewall
echo "🔥 Checking firewall status..."
if command -v ufw &> /dev/null; then
    echo "UFW status:"
    ufw status
    echo ""
    echo "To open ports if needed:"
    echo "sudo ufw allow 8501"
    echo "sudo ufw allow 8000"
elif command -v iptables &> /dev/null; then
    echo "Checking iptables rules..."
    iptables -L INPUT | grep -E "(8501|8000|ACCEPT|DROP)"
fi

# Check cloud provider security groups
echo "☁️  Cloud Provider Notes:"
echo "If running on GCP/AWS/Azure, ensure security groups allow:"
echo "- Inbound TCP 8501 (Streamlit UI)"
echo "- Inbound TCP 8000 (FastAPI)"
echo "- Source: 0.0.0.0/0 (or your IP range)"

# Show external access URLs
echo "=================================================="
echo "🌟 External Access URLs:"
for ip in $(hostname -I); do
    echo "📍 Streamlit: http://$ip:8501"
    echo "📍 FastAPI: http://$ip:8000"
    echo "📍 FastAPI Docs: http://$ip:8000/docs"
done
echo "=================================================="

# Recommendations
echo "🎯 Troubleshooting Recommendations:"
echo "1. Check container logs: docker logs [container-name]"
echo "2. Verify .env file has correct API keys"
echo "3. Ensure firewall/security groups allow ports 8501, 8000"
echo "4. Try debug mode: docker-compose -f docker-compose.debug.yml up"
echo "5. Test internal connectivity: docker exec [container] nc -z localhost 8501"
