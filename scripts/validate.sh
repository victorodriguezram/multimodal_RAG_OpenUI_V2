#!/bin/bash

# Multimodal RAG System - Deployment Validation Script
# This script tests all the key functionalities

echo "🧪 Multimodal RAG System - Deployment Validation"
echo "==============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test functions
test_api_health() {
    echo -e "${BLUE}Testing API health...${NC}"
    response=$(curl -s -w "%{http_code}" http://localhost:8000/health)
    http_code="${response: -3}"
    if [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✅ API health check passed${NC}"
        return 0
    else
        echo -e "${RED}❌ API health check failed (HTTP $http_code)${NC}"
        return 1
    fi
}

test_api_status() {
    echo -e "${BLUE}Testing API status endpoint...${NC}"
    response=$(curl -s -w "%{http_code}" http://localhost:8000/status)
    http_code="${response: -3}"
    if [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✅ API status check passed${NC}"
        body="${response%???}"
        echo "   Status: $body"
        return 0
    else
        echo -e "${RED}❌ API status check failed (HTTP $http_code)${NC}"
        return 1
    fi
}

test_streamlit_ui() {
    echo -e "${BLUE}Testing Streamlit UI...${NC}"
    response=$(curl -s -w "%{http_code}" http://localhost:8501)
    http_code="${response: -3}"
    if [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✅ Streamlit UI is accessible${NC}"
        return 0
    else
        echo -e "${RED}❌ Streamlit UI is not accessible (HTTP $http_code)${NC}"
        return 1
    fi
}

test_n8n_ui() {
    echo -e "${BLUE}Testing N8N UI...${NC}"
    response=$(curl -s -w "%{http_code}" http://localhost:5678)
    http_code="${response: -3}"
    if [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✅ N8N UI is accessible${NC}"
        return 0
    else
        echo -e "${RED}❌ N8N UI is not accessible (HTTP $http_code)${NC}"
        return 1
    fi
}

test_api_docs() {
    echo -e "${BLUE}Testing API documentation...${NC}"
    response=$(curl -s -w "%{http_code}" http://localhost:8000/docs)
    http_code="${response: -3}"
    if [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✅ API documentation is accessible${NC}"
        return 0
    else
        echo -e "${RED}❌ API documentation is not accessible (HTTP $http_code)${NC}"
        return 1
    fi
}

test_docker_services() {
    echo -e "${BLUE}Testing Docker services...${NC}"
    
    # Check if containers are running
    rag_status=$(docker-compose ps -q multimodal-rag)
    n8n_status=$(docker-compose ps -q n8n)
    
    if [ -n "$rag_status" ]; then
        echo -e "${GREEN}✅ Multimodal RAG container is running${NC}"
    else
        echo -e "${RED}❌ Multimodal RAG container is not running${NC}"
        return 1
    fi
    
    if [ -n "$n8n_status" ]; then
        echo -e "${GREEN}✅ N8N container is running${NC}"
    else
        echo -e "${RED}❌ N8N container is not running${NC}"
        return 1
    fi
    
    return 0
}

test_volumes() {
    echo -e "${BLUE}Testing Docker volumes...${NC}"
    
    # Check if volumes exist
    rag_volume=$(docker volume ls -q | grep rag_data)
    n8n_volume=$(docker volume ls -q | grep n8n_data)
    
    if [ -n "$rag_volume" ]; then
        echo -e "${GREEN}✅ RAG data volume exists${NC}"
    else
        echo -e "${YELLOW}⚠️  RAG data volume not found${NC}"
    fi
    
    if [ -n "$n8n_volume" ]; then
        echo -e "${GREEN}✅ N8N data volume exists${NC}"
    else
        echo -e "${YELLOW}⚠️  N8N data volume not found${NC}"
    fi
    
    return 0
}

# Run all tests
echo -e "${BLUE}Starting validation tests...${NC}"
echo ""

passed=0
total=0

tests=(
    "test_docker_services"
    "test_volumes"
    "test_api_health"
    "test_api_status"
    "test_api_docs"
    "test_streamlit_ui"
    "test_n8n_ui"
)

for test in "${tests[@]}"; do
    total=$((total + 1))
    if $test; then
        passed=$((passed + 1))
    fi
    echo ""
done

# Summary
echo "==============================================="
echo -e "${BLUE}Validation Summary${NC}"
echo "==============================================="
echo -e "Tests passed: ${GREEN}$passed${NC}/$total"

if [ $passed -eq $total ]; then
    echo -e "${GREEN}🎉 All tests passed! Your deployment is ready.${NC}"
    echo ""
    echo -e "${BLUE}Quick Access Links:${NC}"
    echo "📊 Streamlit UI:      http://localhost:8501"
    echo "🔗 API Docs:          http://localhost:8000/docs"
    echo "🤖 N8N Automation:    http://localhost:5678"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo "1. Upload a PDF document via the Streamlit UI"
    echo "2. Test querying through the web interface"
    echo "3. Try the API endpoints using the documentation"
    echo "4. Create your first N8N workflow"
else
    echo -e "${RED}❌ Some tests failed. Please check the logs:${NC}"
    echo "   docker-compose logs -f"
    echo ""
    echo -e "${YELLOW}Common issues:${NC}"
    echo "• Check if API keys are properly set in .env file"
    echo "• Ensure sufficient memory is available (4GB+ recommended)"
    echo "• Verify no other services are using ports 8000, 8501, or 5678"
    echo "• Wait a bit longer for services to fully start up"
fi

echo ""
