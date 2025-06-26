#!/bin/bash

# 🔄 Complete Deployment Script for Multimodal RAG System
# This script handles all aspects of deployment including cleanup, rebuild, and verification

set -e  # Exit on any error

echo "🚀 Multimodal RAG System - Complete Deployment Script"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${BLUE}📍 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Step 1: Environment Check
print_step "Checking environment..."

if [ ! -f ".env" ]; then
    print_error ".env file not found!"
    echo "Please create a .env file with your API keys. Example:"
    echo "COHERE_API_KEY=co_your_actual_key_here"
    echo "GEMINI_API_KEY=AIza_your_actual_key_here"
    exit 1
fi

if [ -x "check-env.sh" ]; then
    ./check-env.sh
else
    print_warning "check-env.sh not found or not executable"
fi

# Step 2: Docker Cleanup
print_step "Cleaning up previous deployment..."

docker-compose down -v --remove-orphans 2>/dev/null || true
docker rmi multimodal_rag_openui_v2-multimodal-rag 2>/dev/null || true

print_success "Cleanup completed"

# Step 3: Verify Requirements Files
print_step "Verifying requirements files..."

if ! grep -q "faiss-cpu" requirements.txt; then
    print_error "faiss-cpu not found in requirements.txt"
    exit 1
fi

if ! grep -q "faiss-cpu" api_requirements.txt; then
    print_error "faiss-cpu not found in api_requirements.txt"
    exit 1
fi

# Check for invalid package versions
if grep -q "cohere==4.21.1" requirements.txt || grep -q "cohere==4.21.1" api_requirements.txt; then
    print_error "Invalid cohere version 4.21.1 found. Please use 4.57 or later."
    exit 1
fi

print_success "Requirements files verified"

# Step 4: Build Containers
print_step "Building containers from scratch..."

docker-compose build --no-cache

if [ $? -ne 0 ]; then
    print_error "Container build failed"
    exit 1
fi

print_success "Containers built successfully"

# Step 5: Start Services
print_step "Starting services..."

docker-compose up -d

if [ $? -ne 0 ]; then
    print_error "Failed to start services"
    exit 1
fi

print_success "Services started"

# Step 6: Wait for services to be ready
print_step "Waiting for services to start..."

sleep 15

# Step 7: Health Checks
print_step "Running health checks..."

echo "Container status:"
docker-compose ps

echo -e "\nTesting imports inside container..."
docker-compose exec -T multimodal-rag python debug_imports.py

echo -e "\nTesting API endpoints..."
for i in {1..5}; do
    if curl -s http://localhost:8000/health > /dev/null; then
        print_success "API is responding"
        break
    else
        if [ $i -eq 5 ]; then
            print_error "API not responding after 5 attempts"
            print_warning "Check logs with: docker-compose logs multimodal-rag"
            exit 1
        else
            print_warning "API not ready yet, waiting... (attempt $i/5)"
            sleep 5
        fi
    fi
done

# Step 8: Display Results
print_step "Deployment Summary"

echo -e "\n${GREEN}🎉 Deployment Successful!${NC}"
echo -e "\n📊 Service URLs:"
echo -e "   • Streamlit UI:     ${BLUE}http://localhost:8501${NC}"
echo -e "   • API Documentation: ${BLUE}http://localhost:8000/docs${NC}"
echo -e "   • API Health Check:  ${BLUE}http://localhost:8000/health${NC}"
echo -e "   • N8N Interface:     ${BLUE}http://localhost:5678${NC}"

echo -e "\n🔍 Quick Tests:"
echo -e "   • API Health:  curl http://localhost:8000/health"
echo -e "   • API Status:  curl http://localhost:8000/status"
echo -e "   • View Logs:   docker-compose logs -f"

echo -e "\n🛠️ Useful Commands:"
echo -e "   • Stop services:     docker-compose down"
echo -e "   • View logs:         docker-compose logs -f multimodal-rag"
echo -e "   • Restart:           docker-compose restart"
echo -e "   • Debug container:   docker-compose exec multimodal-rag /bin/bash"

print_success "All systems operational!"
