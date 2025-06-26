#!/bin/bash

# Update script for Multimodal RAG System
# Run this after pulling updates to ensure everything is properly configured

set -e

echo "🚀 Updating Multimodal RAG System..."

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found. Please run this script from the project root."
    exit 1
fi

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update .env with your configuration before running the system!"
fi

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x scripts/*.sh

# Pull latest images
echo "📦 Pulling latest Docker images..."
docker-compose pull

# Build custom images
echo "🏗️  Building custom images..."
docker-compose build

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p data/uploads
mkdir -p data/faiss

# Initialize database if needed
echo "🗄️  Checking database..."
if [ "$(docker-compose ps -q postgres)" = "" ]; then
    echo "Starting database..."
    docker-compose up -d postgres
    sleep 10
    echo "Initializing database..."
    docker-compose exec postgres psql -U rag_user -d rag_db -f /docker-entrypoint-initdb.d/init.sql || true
fi

# Health check function
check_service() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $service to be ready..."
    while [ $attempt -le $max_attempts ]; do
        if curl -f "$url" > /dev/null 2>&1; then
            echo "✅ $service is ready!"
            return 0
        fi
        echo "Attempt $attempt/$max_attempts - waiting for $service..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service failed to start after $max_attempts attempts"
    return 1
}

# Start all services
echo "🚀 Starting all services..."
docker-compose up -d

# Wait for services to be ready
check_service "API" "http://localhost:8000/health"
check_service "UI" "http://localhost:8501"

# Run any pending migrations
echo "🔄 Running database migrations..."
docker-compose exec api alembic upgrade head || echo "No migrations to run"

# Show service status
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "🎉 Update completed successfully!"
echo ""
echo "🌐 Services are available at:"
echo "   • API: http://localhost:8000"
echo "   • API Docs: http://localhost:8000/docs"
echo "   • UI: http://localhost:8501"
echo "   • Grafana: http://localhost:3000 (admin/admin)"
echo ""
echo "📝 Next steps:"
echo "   1. Update your .env file with proper configuration"
echo "   2. Upload your first document via the UI"
echo "   3. Test the search functionality"
echo "   4. Set up N8N workflows for automation"
echo ""
echo "📚 Documentation:"
echo "   • Production Guide: PRODUCTION_README.md"
echo "   • Contributing: CONTRIBUTING.md"
echo "   • API Reference: http://localhost:8000/docs"
