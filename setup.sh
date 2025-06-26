#!/bin/bash

# Multimodal RAG System - Quick Setup Script
# This script automates the deployment process

set -e

echo "🔍 Multimodal RAG System - Docker Deployment Setup"
echo "=================================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first:"
    echo "   curl -fsSL https://get.docker.com -o get-docker.sh"
    echo "   sudo sh get-docker.sh"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first:"
    echo "   sudo apt install docker-compose-plugin -y"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Please create it with your API keys:"
    echo ""
    echo "COHERE_API_KEY=your_actual_cohere_api_key_here"
    echo "GEMINI_API_KEY=your_actual_gemini_api_key_here"
    echo "GEMINI_MODEL=gemini-2.5-flash-preview-04-17"
    echo "N8N_USER=admin"
    echo "N8N_PASSWORD=your_secure_password_here"
    echo "N8N_ENCRYPTION_KEY=your_secure_encryption_key_here"
    echo "N8N_HOST=localhost"
    echo ""
    echo "Please create .env file and run this script again."
    exit 1
fi

echo "✅ .env file found"

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p data uploads

# Build and start services
echo "🚀 Building and starting services..."
docker-compose down --remove-orphans
docker-compose pull
docker-compose build --no-cache
docker-compose up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 30

# Check service health
echo "🔍 Checking service health..."

# Check multimodal-rag service
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Multimodal RAG API is healthy"
else
    echo "❌ Multimodal RAG API is not responding"
fi

# Check Streamlit
if curl -s http://localhost:8501/_stcore/health > /dev/null; then
    echo "✅ Streamlit UI is healthy"
else
    echo "❌ Streamlit UI is not responding"
fi

# Check N8N
if curl -s http://localhost:5678 > /dev/null; then
    echo "✅ N8N is healthy"
else
    echo "❌ N8N is not responding"
fi

echo ""
echo "🎉 Deployment completed!"
echo ""
echo "Access your applications:"
echo "========================"
echo "📊 Streamlit UI:        http://localhost:8501"
echo "🔗 API Documentation:   http://localhost:8000/docs"
echo "🤖 N8N Automation:      http://localhost:5678"
echo ""
echo "N8N Login Credentials:"
echo "Username: $(grep N8N_USER .env | cut -d'=' -f2)"
echo "Password: $(grep N8N_PASSWORD .env | cut -d'=' -f2)"
echo ""
echo "🔧 Useful Commands:"
echo "==================="
echo "View logs:           docker-compose logs -f"
echo "Stop services:       docker-compose down"
echo "Restart services:    docker-compose restart"
echo "Check status:        docker-compose ps"
echo ""
echo "📖 For detailed documentation, see README_DOCKER.md"
