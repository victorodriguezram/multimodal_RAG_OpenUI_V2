#!/bin/bash

# Production deployment script for Multimodal RAG System
# This script automates the deployment process on Ubuntu systems

set -e  # Exit on any error

echo "🚀 Starting Multimodal RAG System Deployment"
echo "=============================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Check Ubuntu version
if ! grep -q "Ubuntu" /etc/os-release; then
    print_warning "This script is optimized for Ubuntu. Proceed with caution."
fi

print_status "Checking system requirements..."

# Check Docker installation
if ! command -v docker &> /dev/null; then
    print_status "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    print_success "Docker installed successfully"
else
    print_success "Docker is already installed"
fi

# Check Docker Compose installation
if ! command -v docker-compose &> /dev/null; then
    print_status "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    print_success "Docker Compose installed successfully"
else
    print_success "Docker Compose is already installed"
fi

# Verify Docker service is running
if ! sudo systemctl is-active --quiet docker; then
    print_status "Starting Docker service..."
    sudo systemctl start docker
    sudo systemctl enable docker
fi

print_status "System requirements check completed"

# Check if .env file exists
if [ ! -f ".env" ]; then
    if [ -f ".env.template" ]; then
        print_status "Creating .env file from template..."
        cp .env.template .env
        print_warning "Please edit .env file with your actual API keys before continuing"
        print_warning "Required: COHERE_API_KEY and GEMINI_API_KEY"
        
        read -p "Have you configured your API keys in .env file? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_error "Please configure your API keys in .env file and run this script again"
            exit 1
        fi
    else
        print_error ".env file not found and no template available"
        exit 1
    fi
fi

# Validate required environment variables
print_status "Validating environment configuration..."
source .env

if [ -z "$COHERE_API_KEY" ] || [ "$COHERE_API_KEY" == "your_cohere_api_key_here" ]; then
    print_error "COHERE_API_KEY is not configured in .env file"
    exit 1
fi

if [ -z "$GEMINI_API_KEY" ] || [ "$GEMINI_API_KEY" == "your_gemini_api_key_here" ]; then
    print_error "GEMINI_API_KEY is not configured in .env file"
    exit 1
fi

print_success "Environment configuration validated"

# Choose deployment type
echo
echo "Select deployment type:"
echo "1) Development (with hot reload)"
echo "2) Production (with nginx, postgres, redis)"
read -p "Enter your choice (1-2): " -n 1 -r
echo

case $REPLY in
    1)
        COMPOSE_FILE="docker-compose.dev.yml"
        DEPLOYMENT_TYPE="development"
        ;;
    2)
        COMPOSE_FILE="docker-compose.yml"
        DEPLOYMENT_TYPE="production"
        ;;
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

print_status "Starting $DEPLOYMENT_TYPE deployment..."

# Pull latest images
print_status "Pulling Docker images..."
docker-compose -f $COMPOSE_FILE pull

# Build custom images
print_status "Building application images..."
docker-compose -f $COMPOSE_FILE build

# Start services
print_status "Starting services..."
docker-compose -f $COMPOSE_FILE up -d

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 30

# Health checks
print_status "Performing health checks..."

# Check if containers are running
if ! docker-compose -f $COMPOSE_FILE ps | grep -q "Up"; then
    print_error "Some containers failed to start"
    docker-compose -f $COMPOSE_FILE logs
    exit 1
fi

# Check application health
max_attempts=10
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -f http://localhost:8501/_stcore/health &> /dev/null; then
        print_success "Application is healthy and responding"
        break
    else
        print_status "Waiting for application to be ready... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    print_error "Application failed to become healthy"
    print_status "Checking logs..."
    docker-compose -f $COMPOSE_FILE logs rag-app
    exit 1
fi

# Additional health checks for production
if [ "$DEPLOYMENT_TYPE" == "production" ]; then
    # Check PostgreSQL
    if docker-compose exec -T postgres pg_isready -U raguser &> /dev/null; then
        print_success "PostgreSQL is ready"
    else
        print_warning "PostgreSQL health check failed"
    fi
    
    # Check Redis
    if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
        print_success "Redis is ready"
    else
        print_warning "Redis health check failed"
    fi
    
    # Check Nginx
    if curl -f http://localhost/health &> /dev/null; then
        print_success "Nginx is ready"
    else
        print_warning "Nginx health check failed"
    fi
fi

# Display deployment information
echo
echo "🎉 Deployment completed successfully!"
echo "======================================"
echo
echo "Application URL: http://localhost:8501"

if [ "$DEPLOYMENT_TYPE" == "production" ]; then
    echo "Reverse Proxy URL: http://localhost"
    echo
    echo "Service Endpoints:"
    echo "  - Application: http://localhost:8501"
    echo "  - PostgreSQL: localhost:5432"
    echo "  - Redis: localhost:6379"
    echo "  - Nginx: http://localhost"
fi

echo
echo "Management Commands:"
echo "  - View logs: docker-compose -f $COMPOSE_FILE logs -f"
echo "  - Stop services: docker-compose -f $COMPOSE_FILE down"
echo "  - Restart services: docker-compose -f $COMPOSE_FILE restart"
echo "  - View status: docker-compose -f $COMPOSE_FILE ps"

echo
echo "Data Locations:"
echo "  - FAISS indices: Docker volume 'rag_data'"
echo "  - Uploaded files: Docker volume 'rag_uploads'"
if [ "$DEPLOYMENT_TYPE" == "production" ]; then
    echo "  - Database: Docker volume 'postgres_data'"
    echo "  - Redis cache: Docker volume 'redis_data'"
fi

echo
echo "Next Steps:"
echo "1. Upload some PDF documents to test the system"
echo "2. Try searching for content in the uploaded documents"
echo "3. Monitor logs for any issues: docker-compose -f $COMPOSE_FILE logs -f"

if [ "$DEPLOYMENT_TYPE" == "production" ]; then
    echo "4. Configure SSL certificates for production use"
    echo "5. Set up monitoring and backup procedures"
fi

echo
print_success "Deployment script completed successfully!"

# Show running containers
echo
print_status "Currently running containers:"
docker-compose -f $COMPOSE_FILE ps
