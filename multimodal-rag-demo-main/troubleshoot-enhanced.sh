#!/bin/bash
# Enhanced troubleshooting script for RAG deployment issues

echo "=================================================="
echo "🛠️  RAG System Troubleshooting & Diagnostics"
echo "=================================================="

# Check Docker system
echo "🐳 Docker System Check..."
if systemctl is-active --quiet docker; then
    echo "✅ Docker is running"
    docker --version
else
    echo "❌ Docker is not running!"
    echo "Run: sudo systemctl start docker"
    exit 1
fi

# Check current containers
echo ""
echo "📦 Current Container Status..."
docker-compose -f docker-compose.dev.yml ps

# Detailed container health
echo ""
echo "🏥 Container Health Analysis..."
CONTAINER_NAME=$(docker ps --filter "name=multimodal-rag-app" --format "{{.Names}}" | head -1)
if [ ! -z "$CONTAINER_NAME" ]; then
    echo "Found container: $CONTAINER_NAME"
    
    # Check container state
    CONTAINER_STATE=$(docker inspect "$CONTAINER_NAME" --format "{{.State.Status}}")
    CONTAINER_HEALTH=$(docker inspect "$CONTAINER_NAME" --format "{{.State.Health.Status}}" 2>/dev/null || echo "no-healthcheck")
    
    echo "  Status: $CONTAINER_STATE"
    echo "  Health: $CONTAINER_HEALTH"
    
    # Test internal connectivity
    echo ""
    echo "🔗 Internal Connectivity Test..."
    docker exec "$CONTAINER_NAME" bash -c "
        echo '🔍 Checking internal ports:'
        echo -n '  Port 8501 (Streamlit): '
        nc -z localhost 8501 && echo 'OPEN ✅' || echo 'CLOSED ❌'
        echo -n '  Port 8000 (FastAPI): '
        nc -z localhost 8000 && echo 'OPEN ✅' || echo 'CLOSED ❌'
        
        echo ''
        echo '🏃 Running processes:'
        ps aux | grep -E '(streamlit|uvicorn|python)' | grep -v grep | head -5
        
        echo ''
        echo '🌐 Network interfaces:'
        ip addr show | grep -E 'inet.*eth0'
    " 2>/dev/null || echo "❌ Cannot access container"
else
    echo "❌ No RAG container found!"
fi

# Check host port bindings
echo ""
echo "🌐 Host Port Analysis..."
echo "Ports bound on host:"
netstat -tuln | grep -E ":8501|:8000|:6379" || echo "❌ No relevant ports found on host"

echo ""
echo "Docker port mappings:"
docker ps --format "table {{.Names}}\t{{.Ports}}" | grep -E "(8501|8000)"

# Check logs for errors
echo ""
echo "📝 Container Logs Analysis..."
if [ ! -z "$CONTAINER_NAME" ]; then
    echo "Last 20 lines from $CONTAINER_NAME:"
    docker logs --tail 20 "$CONTAINER_NAME" 2>&1 | tail -20
    
    echo ""
    echo "Searching for errors in logs:"
    docker logs "$CONTAINER_NAME" 2>&1 | grep -i -E "(error|exception|failed|denied)" | tail -5 || echo "No obvious errors found"
fi

# Test connectivity
echo ""
echo "🚀 Connectivity Tests..."
echo "Testing localhost access:"
timeout 5 curl -s http://localhost:8501 >/dev/null 2>&1 && echo "✅ Streamlit responding on localhost:8501" || echo "❌ Streamlit not responding on localhost:8501"
timeout 5 curl -s http://localhost:8000/health >/dev/null 2>&1 && echo "✅ FastAPI responding on localhost:8000" || echo "❌ FastAPI not responding on localhost:8000"

# Check environment
echo ""
echo "🔑 Environment Configuration..."
if [ -f .env ]; then
    echo "✅ .env file found"
    echo "Environment variables configured:"
    grep -E "^[A-Z_]+=" .env | sed 's/=.*/=***/' | head -5
else
    echo "❌ .env file not found!"
    echo "Create .env with: COHERE_API_KEY=your_key and GEMINI_API_KEY=your_key"
fi

# Firewall check
echo ""
echo "🔥 Firewall Status..."
if command -v ufw &> /dev/null; then
    echo "UFW firewall status:"
    ufw status | head -10
    if ! ufw status | grep -q "8501"; then
        echo "⚠️  Port 8501 not explicitly allowed"
        echo "To fix: sudo ufw allow 8501"
    fi
    if ! ufw status | grep -q "8000"; then
        echo "⚠️  Port 8000 not explicitly allowed"  
        echo "To fix: sudo ufw allow 8000"
    fi
else
    echo "UFW not found, checking iptables..."
    iptables -L INPUT -n | grep -E "(ACCEPT|DROP).*dpt:(8501|8000)" || echo "No specific rules for ports 8501/8000"
fi

# External access information
echo ""
echo "🌍 External Access Information..."
echo "Server IP addresses:"
hostname -I | tr ' ' '\n' | grep -v '^$' | head -3

echo ""
echo "External access URLs:"
for ip in $(hostname -I | tr ' ' '\n' | head -2); do
    [ ! -z "$ip" ] && echo "  🌐 http://$ip:8501 (Streamlit UI)"
    [ ! -z "$ip" ] && echo "  🌐 http://$ip:8000/docs (FastAPI docs)"
done

# Cloud provider notes
echo ""
echo "☁️  Cloud Provider Security Groups:"
echo "If using GCP/AWS/Azure, ensure security groups allow:"
echo "  - Inbound TCP 8501 from 0.0.0.0/0"
echo "  - Inbound TCP 8000 from 0.0.0.0/0"

# Action recommendations
echo ""
echo "🎯 Recommended Actions:"

if docker ps --filter "name=multimodal-rag-app" --filter "health=unhealthy" | grep -q "unhealthy"; then
    echo "❌ UNHEALTHY CONTAINER - Priority actions:"
    echo "  1. Check health script: docker exec $CONTAINER_NAME /app/healthcheck-simple.sh"
    echo "  2. Use debug mode: docker-compose -f docker-compose.debug.yml up"
    echo "  3. Rebuild: docker-compose -f docker-compose.dev.yml up --build"
fi

if ! netstat -tuln | grep -q ":8501"; then
    echo "❌ PORT 8501 NOT ACCESSIBLE - Check:"
    echo "  1. Container port mapping in docker-compose.yml"
    echo "  2. Firewall rules: sudo ufw allow 8501"
    echo "  3. Cloud security groups"
fi

if [ -z "$CONTAINER_NAME" ]; then
    echo "❌ NO CONTAINER RUNNING - Start services:"
    echo "  1. Check .env file exists with API keys"
    echo "  2. Run: docker-compose -f docker-compose.dev.yml up -d"
fi

echo ""
echo "🛠️  Quick Fix Commands:"
echo "  Restart: docker-compose -f docker-compose.dev.yml restart"
echo "  Debug mode: docker-compose -f docker-compose.debug.yml up"
echo "  View logs: docker-compose -f docker-compose.dev.yml logs -f rag-app"
echo "  Shell access: docker-compose -f docker-compose.dev.yml exec rag-app bash"
echo "  Full restart: docker-compose -f docker-compose.dev.yml down && docker-compose -f docker-compose.dev.yml up -d"

echo ""
echo "📞 For external access troubleshooting: ./diagnose-connectivity.sh"
