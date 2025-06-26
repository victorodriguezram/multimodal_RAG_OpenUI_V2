#!/bin/bash

# Docker Complete Cleanup Script
# This script removes ALL Docker resources for a clean redeployment

set -e

echo "🧹 Docker Complete Cleanup Script"
echo "================================="
echo ""
echo "⚠️  WARNING: This will remove ALL Docker images, containers, and volumes!"
echo "   If you have other Docker projects, use 'cleanup-targeted.sh' instead."
echo ""
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 1
fi

echo ""
echo "🛑 Step 1: Stopping all containers..."
docker stop $(docker ps -aq) 2>/dev/null || echo "No containers to stop"

echo ""
echo "🗑️  Step 2: Removing all containers..."
docker rm $(docker ps -aq) 2>/dev/null || echo "No containers to remove"

echo ""
echo "🖼️  Step 3: Removing all images..."
docker rmi $(docker images -q) -f 2>/dev/null || echo "No images to remove"

echo ""
echo "💾 Step 4: Removing all volumes..."
docker volume rm $(docker volume ls -q) 2>/dev/null || echo "No volumes to remove"

echo ""
echo "🌐 Step 5: Removing custom networks..."
docker network rm $(docker network ls --filter type=custom -q) 2>/dev/null || echo "No custom networks to remove"

echo ""
echo "🧹 Step 6: System cleanup..."
docker system prune -a --volumes -f

echo ""
echo "🏗️  Step 7: Builder cleanup..."
docker builder prune -a -f

echo ""
echo "🔍 Step 8: Checking port availability..."
echo "Checking port 8000..."
if sudo lsof -i :8000 2>/dev/null; then
    echo "Port 8000 is still in use. Attempting to free it..."
    sudo fuser -k 8000/tcp 2>/dev/null || true
else
    echo "✅ Port 8000 is free"
fi

echo "Checking port 8501..."
if sudo lsof -i :8501 2>/dev/null; then
    echo "Port 8501 is still in use. Attempting to free it..."
    sudo fuser -k 8501/tcp 2>/dev/null || true
else
    echo "✅ Port 8501 is free"
fi

echo "Checking port 5678..."
if sudo lsof -i :5678 2>/dev/null; then
    echo "Port 5678 is still in use. Attempting to free it..."
    sudo fuser -k 5678/tcp 2>/dev/null || true
else
    echo "✅ Port 5678 is free"
fi

echo ""
echo "📊 Final verification:"
echo "====================="
echo "Containers remaining: $(docker ps -aq | wc -l)"
echo "Images remaining: $(docker images -q | wc -l)"
echo "Volumes remaining: $(docker volume ls -q | wc -l)"
echo "Custom networks remaining: $(docker network ls --filter type=custom -q | wc -l)"

echo ""
echo "✅ Cleanup completed!"
echo ""
echo "🚀 Next steps:"
echo "1. Run: docker-compose up -d"
echo "2. Monitor: docker-compose logs -f"
echo "3. Verify: curl http://localhost:8000/health"
