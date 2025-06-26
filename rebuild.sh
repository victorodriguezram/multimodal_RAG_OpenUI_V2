#!/bin/bash

# Rebuild script for multimodal RAG system
# This script performs a complete rebuild of the Docker containers

echo "🔄 Starting complete rebuild process..."

# Stop and remove all containers, networks, and volumes
echo "📦 Stopping and removing existing containers..."
docker-compose down -v --remove-orphans

# Remove existing images
echo "🗑️ Removing existing Docker images..."
docker rmi multimodal_rag_openui_v2-multimodal-rag 2>/dev/null || true

# Prune Docker system to free up space
echo "🧹 Cleaning up Docker system..."
docker system prune -f

# Build and start containers with no cache
echo "🏗️ Building containers from scratch..."
docker-compose build --no-cache

echo "🚀 Starting containers..."
docker-compose up -d

# Wait a moment for containers to start
sleep 5

# Show container status
echo "📊 Container status:"
docker-compose ps

# Show logs for debugging
echo "📝 Recent logs:"
docker-compose logs --tail=20

echo "✅ Rebuild complete!"
echo "🌐 Streamlit app: http://localhost:8501"
echo "🔗 FastAPI docs: http://localhost:8000/docs"
