# Multimodal RAG System - Docker Deployment Guide

## Overview
This guide provides comprehensive instructions for deploying the Multimodal RAG system using Docker Compose on Ubuntu Linux systems.

## Prerequisites

### System Requirements (Ubuntu 20.04+ recommended)
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version
```

### Required API Keys
- **Cohere API Key**: Get from [Cohere Dashboard](https://dashboard.cohere.com/)
- **Gemini API Key**: Get from [Google AI Studio](https://aistudio.google.com/)

## Quick Start

### 1. Environment Setup
```bash
# Clone or navigate to your project directory
cd multimodal-rag-demo-main

# Copy environment template
cp .env.template .env

# Edit environment file with your API keys
nano .env
```

### 2. Configure Environment Variables
Edit `.env` file with your actual values:
```bash
# Required API Keys
COHERE_API_KEY=your_actual_cohere_api_key
GEMINI_API_KEY=your_actual_gemini_api_key

# Database credentials
POSTGRES_PASSWORD=your_secure_db_password
REDIS_PASSWORD=your_redis_password

# Generate secure secrets
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)
```

### 3. Development Deployment
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f rag-app

# Access application
open http://localhost:8501
```

### 4. Production Deployment
```bash
# Start production environment
docker-compose up -d

# Check all services are running
docker-compose ps

# View logs
docker-compose logs -f
```

## Architecture Overview

### Services Deployed
- **rag-app**: Main Streamlit application (port 8501)
- **redis**: Caching layer for embeddings and sessions (port 6379)
- **postgres**: Document metadata and user sessions (port 5432)
- **nginx**: Reverse proxy and load balancer (ports 80/443)

### Data Persistence
- **rag_data**: FAISS indices and document metadata
- **rag_uploads**: Uploaded PDF files
- **postgres_data**: Database storage
- **redis_data**: Cache persistence

## Container Management

### View Container Status
```bash
# Check running containers
docker-compose ps

# View resource usage
docker stats

# Check container health
docker-compose exec rag-app curl -f http://localhost:8501/_stcore/health
```

### Logs and Debugging
```bash
# View all logs
docker-compose logs

# Follow specific service logs
docker-compose logs -f rag-app
docker-compose logs -f postgres
docker-compose logs -f redis

# Execute commands in containers
docker-compose exec rag-app bash
docker-compose exec postgres psql -U raguser -d ragdb
docker-compose exec redis redis-cli
```

### Scaling and Updates
```bash
# Scale specific services
docker-compose up -d --scale rag-app=2

# Update application code
docker-compose build rag-app
docker-compose up -d rag-app

# Restart all services
docker-compose restart

# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ DATA LOSS)
docker-compose down -v
```

## Maintenance Operations

### Backup Data
```bash
# Backup FAISS indices and metadata
docker run --rm -v multimodal-rag-demo-main_rag_data:/data -v $(pwd):/backup ubuntu tar czf /backup/rag_data_backup.tar.gz -C /data .

# Backup PostgreSQL database
docker-compose exec postgres pg_dump -U raguser ragdb > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup uploaded files
docker run --rm -v multimodal-rag-demo-main_rag_uploads:/data -v $(pwd):/backup ubuntu tar czf /backup/uploads_backup.tar.gz -C /data .
```

### Restore Data
```bash
# Restore FAISS data
docker run --rm -v multimodal-rag-demo-main_rag_data:/data -v $(pwd):/backup ubuntu tar xzf /backup/rag_data_backup.tar.gz -C /data

# Restore PostgreSQL database
cat backup_20240620_143000.sql | docker-compose exec -T postgres psql -U raguser ragdb

# Restore uploads
docker run --rm -v multimodal-rag-demo-main_rag_uploads:/data -v $(pwd):/backup ubuntu tar xzf /backup/uploads_backup.tar.gz -C /data
```

### Monitor Performance
```bash
# Resource usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# Database performance
docker-compose exec postgres psql -U raguser ragdb -c "SELECT * FROM pg_stat_activity;"

# Redis performance
docker-compose exec redis redis-cli info memory
docker-compose exec redis redis-cli info stats
```

## Security Considerations

### Production Security Checklist
- [ ] Change default passwords in `.env`
- [ ] Use strong, unique secrets
- [ ] Enable SSL/TLS with proper certificates
- [ ] Configure firewall rules
- [ ] Regular security updates
- [ ] Monitor access logs
- [ ] Implement rate limiting
- [ ] Use non-root users in containers

### SSL/TLS Setup
```bash
# Generate self-signed certificates (development only)
mkdir ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/key.pem \
    -out ssl/cert.pem

# For production, use Let's Encrypt or proper CA certificates
```

## Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check logs for errors
docker-compose logs rag-app

# Verify environment variables
docker-compose config

# Check port conflicts
sudo netstat -tulpn | grep :8501
```

#### Out of Memory
```bash
# Add memory limits to docker-compose.yml
services:
  rag-app:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

#### Permission Issues
```bash
# Fix volume permissions
sudo chown -R 1000:1000 data/
sudo chmod -R 755 data/
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
docker-compose exec postgres pg_isready

# Reset database
docker-compose down
docker volume rm multimodal-rag-demo-main_postgres_data
docker-compose up -d postgres
```

### Performance Optimization

#### Memory Usage
```bash
# Monitor FAISS memory usage
docker-compose exec rag-app python -c "
import psutil
print(f'Memory usage: {psutil.virtual_memory().percent}%')
"

# Optimize Redis memory
docker-compose exec redis redis-cli config set maxmemory-policy allkeys-lru
```

#### Disk Space
```bash
# Clean up Docker resources
docker system prune -a

# Monitor disk usage
df -h
du -sh data/
```

## API Integration for n8n

### REST API Endpoints
The application can be extended with FastAPI endpoints for n8n integration:

```python
# Add to future api.py file
from fastapi import FastAPI, UploadFile
from typing import List

app = FastAPI()

@app.post("/api/upload")
async def upload_document(file: UploadFile):
    # Process document upload
    pass

@app.post("/api/query")
async def query_documents(query: str):
    # Search and return results
    pass

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
```

### n8n Webhook Configuration
```json
{
  "httpMethod": "POST",
  "url": "http://rag-app:8501/api/query",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "query": "{{$json.question}}"
  }
}
```

## Development Workflow

### Local Development
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# Make code changes (hot reload enabled)
# Changes are automatically reflected in running container

# Run tests
docker-compose exec rag-app python -m pytest tests/

# Code formatting
docker-compose exec rag-app black .
docker-compose exec rag-app flake8 .
```

### CI/CD Integration
```yaml
# .github/workflows/deploy.yml example
name: Deploy RAG System
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to production
        run: |
          docker-compose build
          docker-compose up -d
```

## Support and Monitoring

### Health Checks
- Application: `http://localhost:8501/_stcore/health`
- Database: `docker-compose exec postgres pg_isready`
- Redis: `docker-compose exec redis redis-cli ping`
- Nginx: `http://localhost/health`

### Metrics and Alerting
Consider integrating with:
- **Prometheus + Grafana**: For metrics collection and visualization
- **ELK Stack**: For centralized logging
- **Uptime monitoring**: For external health checks

For additional support or customization, refer to the component documentation or create issues in the project repository.
