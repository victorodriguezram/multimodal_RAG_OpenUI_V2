#!/bin/bash

# Nuclear Docker Cleanup - One Command
# Removes EVERYTHING Docker related

echo "💥 NUCLEAR DOCKER CLEANUP"
echo "========================"
echo "This will remove ALL Docker resources on this system!"
echo ""
read -p "Type 'NUCLEAR' to confirm: " confirm

if [ "$confirm" != "NUCLEAR" ]; then
    echo "Cleanup cancelled."
    exit 1
fi

echo ""
echo "🚨 Executing nuclear cleanup..."

# The nuclear option - removes everything
docker stop $(docker ps -aq) 2>/dev/null; \
docker rm $(docker ps -aq) 2>/dev/null; \
docker rmi $(docker images -q) -f 2>/dev/null; \
docker volume rm $(docker volume ls -q) 2>/dev/null; \
docker network rm $(docker network ls --filter type=custom -q) 2>/dev/null; \
docker system prune -a --volumes -f; \
docker builder prune -a -f

# Kill processes on our ports
sudo fuser -k 8000/tcp 2>/dev/null || true
sudo fuser -k 8501/tcp 2>/dev/null || true
sudo fuser -k 5678/tcp 2>/dev/null || true

echo ""
echo "💥 Nuclear cleanup completed!"
echo "Docker state should be completely clean."
echo ""
echo "Verification:"
docker ps -a 2>/dev/null || echo "No containers"
docker images 2>/dev/null || echo "No images"  
docker volume ls 2>/dev/null || echo "No volumes"
echo ""
echo "🚀 Ready for fresh deployment: docker-compose up -d"
