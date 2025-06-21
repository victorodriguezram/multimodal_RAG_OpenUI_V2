#!/bin/bash
# Troubleshooting script for Docker deployment issues

echo "🔍 Docker RAG System Troubleshooting"
echo "===================================="

# Check if Docker is running
echo -n "Checking Docker service... "
if systemctl is-active --quiet docker; then
    echo "✅ Running"
else
    echo "❌ Not running"
    echo "Run: sudo systemctl start docker"
    exit 1
fi

# Check containers
echo ""
echo "📦 Container Status:"
docker-compose -f docker-compose.dev.yml ps

# Check port binding
echo ""
echo "🌐 Port 8501 Status:"
if netstat -tuln | grep -q ":8501"; then
    echo "✅ Port 8501 is bound"
    netstat -tuln | grep ":8501"
else
    echo "❌ Port 8501 is not bound"
fi

# Check container logs
echo ""
echo "📋 Recent Application Logs (last 20 lines):"
docker-compose -f docker-compose.dev.yml logs --tail=20 rag-app

# Check if app is responding
echo ""
echo "🔗 Testing Local Connection:"
if curl -s --max-time 5 "http://localhost:8501" > /dev/null; then
    echo "✅ Application responding on localhost:8501"
else
    echo "❌ Application not responding on localhost:8501"
fi

# Check external IP access
echo ""
echo "🌍 External IP Information:"
echo "Your server IP addresses:"
ip addr show | grep -E "inet.*global" | awk '{print $2}' | cut -d'/' -f1

# Firewall check
echo ""
echo "🔥 Firewall Status:"
if command -v ufw &> /dev/null; then
    echo "UFW Status:"
    sudo ufw status
    echo ""
    echo "To allow port 8501: sudo ufw allow 8501"
elif command -v firewall-cmd &> /dev/null; then
    echo "Firewalld Status:"
    sudo firewall-cmd --list-ports
    echo ""
    echo "To allow port 8501: sudo firewall-cmd --permanent --add-port=8501/tcp && sudo firewall-cmd --reload"
else
    echo "No recognized firewall tool found"
fi

# Docker network check
echo ""
echo "🔗 Docker Network Information:"
docker network ls | grep rag
echo ""
echo "Container network details:"
docker-compose -f docker-compose.dev.yml exec rag-app ip addr show eth0 2>/dev/null || echo "Container not running"

echo ""
echo "🛠️  Quick Fix Commands:"
echo "1. Restart containers: docker-compose -f docker-compose.dev.yml restart"
echo "2. Rebuild and restart: docker-compose -f docker-compose.dev.yml up --build -d"
echo "3. View real-time logs: docker-compose -f docker-compose.dev.yml logs -f rag-app"
echo "4. Access container shell: docker-compose -f docker-compose.dev.yml exec rag-app bash"
echo "5. Stop all: docker-compose -f docker-compose.dev.yml down"

echo ""
echo "🌐 Access URLs to try:"
echo "- Local: http://localhost:8501"
echo "- Server IP: http://YOUR_SERVER_IP:8501"
echo "- If using cloud: check security groups/firewall rules"
