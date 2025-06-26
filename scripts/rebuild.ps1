# Rebuild script for multimodal RAG system (PowerShell)
# This script performs a complete rebuild of the Docker containers

Write-Host "🔄 Starting complete rebuild process..." -ForegroundColor Blue

# Stop and remove all containers, networks, and volumes
Write-Host "📦 Stopping and removing existing containers..." -ForegroundColor Yellow
docker-compose down -v --remove-orphans

# Remove existing images
Write-Host "🗑️ Removing existing Docker images..." -ForegroundColor Yellow
docker rmi multimodal_rag_openui_v2-multimodal-rag 2>$null

# Prune Docker system to free up space
Write-Host "🧹 Cleaning up Docker system..." -ForegroundColor Yellow
docker system prune -f

# Build and start containers with no cache
Write-Host "🏗️ Building containers from scratch..." -ForegroundColor Green
docker-compose build --no-cache

Write-Host "🚀 Starting containers..." -ForegroundColor Green
docker-compose up -d

# Wait a moment for containers to start
Start-Sleep -Seconds 5

# Show container status
Write-Host "📊 Container status:" -ForegroundColor Cyan
docker-compose ps

# Show logs for debugging
Write-Host "📝 Recent logs:" -ForegroundColor Cyan
docker-compose logs --tail=20

Write-Host "✅ Rebuild complete!" -ForegroundColor Green
Write-Host "🌐 Streamlit app: http://localhost:8501" -ForegroundColor Magenta
Write-Host "🔗 FastAPI docs: http://localhost:8000/docs" -ForegroundColor Magenta
