#!/bin/bash

# Docker Targeted Cleanup Script
# This script removes only multimodal RAG related Docker resources

set -e

echo "🎯 Docker Targeted Cleanup Script"
echo "================================="
echo "This will remove only multimodal RAG and N8N related Docker resources."
echo ""

echo "🔍 Step 1: Checking current state..."
echo "Containers:"
docker ps -a --filter "name=multimodal" --filter "name=n8n" --format "table {{.Names}}\t{{.Status}}" || echo "No related containers found"
echo ""
echo "Images:"
docker images --filter "reference=*multimodal*" --filter "reference=*n8n*" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" || echo "No related images found"
echo ""
echo "Volumes:"
docker volume ls --filter "name=multimodal" --format "table {{.Name}}\t{{.Driver}}" || echo "No related volumes found"

echo ""
echo "🛑 Step 2: Stopping project containers..."
docker-compose down --remove-orphans 2>/dev/null || echo "No compose file or containers to stop"

echo ""
echo "🗑️  Step 3: Removing project containers..."
docker rm $(docker ps -aq --filter "name=multimodal") 2>/dev/null || echo "No multimodal containers to remove"
docker rm $(docker ps -aq --filter "name=n8n") 2>/dev/null || echo "No n8n containers to remove"

echo ""
echo "🖼️  Step 4: Removing project images..."
docker rmi $(docker images --filter "reference=*multimodal*" -q) -f 2>/dev/null || echo "No multimodal images to remove"
docker rmi $(docker images --filter "reference=*n8n*" -q) -f 2>/dev/null || echo "No n8n images to remove"
docker rmi $(docker images --filter "reference=multimodal_rag_openui_v2*" -q) -f 2>/dev/null || echo "No project images to remove"

echo ""
echo "💾 Step 5: Removing project volumes..."
docker volume rm $(docker volume ls --filter "name=multimodal" -q) 2>/dev/null || echo "No multimodal volumes to remove"

echo ""
echo "🧹 Step 6: Cleaning up unused resources..."
docker system prune -f

echo ""
echo "🔍 Step 7: Checking port availability..."
check_port() {
    local port=$1
    if sudo lsof -i :$port 2>/dev/null; then
        echo "⚠️  Port $port is still in use:"
        sudo lsof -i :$port
        echo "To free it, run: sudo fuser -k $port/tcp"
    else
        echo "✅ Port $port is free"
    fi
}

check_port 8000
check_port 8501
check_port 5678

echo ""
echo "📊 Final verification:"
echo "====================="
echo "Related containers remaining:"
docker ps -a --filter "name=multimodal" --filter "name=n8n" --format "table {{.Names}}\t{{.Status}}" 2>/dev/null || echo "None"
echo ""
echo "Related images remaining:"
docker images --filter "reference=*multimodal*" --filter "reference=*n8n*" --format "table {{.Repository}}\t{{.Tag}}" 2>/dev/null || echo "None"
echo ""
echo "Related volumes remaining:"
docker volume ls --filter "name=multimodal" --format "table {{.Name}}" 2>/dev/null || echo "None"

echo ""
echo "✅ Targeted cleanup completed!"
echo ""
echo "🚀 Next steps:"
echo "1. Run: docker-compose up -d"
echo "2. Monitor: docker-compose logs -f"
echo "3. Verify: curl http://localhost:8000/health"
