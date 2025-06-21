# Migration Guide: From Streamlit App to Docker Compose

## Overview
This guide walks you through converting your existing Multimodal RAG system from a standalone Streamlit application to a containerized Docker Compose deployment.

## Phase 1: Pre-Migration Assessment

### 1. Backup Your Current System
```bash
# Backup your existing data
cp -r data/ data_backup_$(date +%Y%m%d_%H%M%S)/

# Backup your configuration
cp config.py config.py.backup

# Export current package versions
pip freeze > requirements_backup.txt
```

### 2. Environment Assessment
```bash
# Check current Python version
python --version

# Check system dependencies
which poppler-utils
dpkg -l | grep poppler

# Check current data size
du -sh data/
ls -la data/
```

## Phase 2: Migration Steps

### Step 1: Update Configuration
Replace hardcoded API keys with environment variables:

**Before** (config.py):
```python
COHERE_API_KEY = "your_hardcoded_key"
GEMINI_API_KEY = "your_hardcoded_key"
```

**After** (config.py):
```python
import os
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
```

### Step 2: Create Environment File
```bash
# Copy the template
cp .env.template .env

# Edit with your actual values
nano .env
```

Add your actual API keys:
```bash
COHERE_API_KEY=your_actual_cohere_key
GEMINI_API_KEY=your_actual_gemini_key
POSTGRES_PASSWORD=secure_password_123
```

### Step 3: Update Dependencies
The new `requirements.txt` includes additional packages for production:
- `redis`: For caching
- `psycopg2-binary`: For PostgreSQL connection
- `python-dotenv`: For environment variable loading

### Step 4: Data Migration

#### Option A: Keep Existing FAISS Data
```bash
# Create Docker volume and copy existing data
docker volume create multimodal-rag-demo-main_rag_data
docker run --rm -v $(pwd)/data:/source -v multimodal-rag-demo-main_rag_data:/dest ubuntu cp -r /source/. /dest/
```

#### Option B: Fresh Start (Re-index Documents)
```bash
# Simply start with clean containers
# Your existing PDFs in pdf/ folder can be re-uploaded
```

### Step 5: Deploy Development Environment
```bash
# Start development containers
docker-compose -f docker-compose.dev.yml up -d

# Check logs
docker-compose -f docker-compose.dev.yml logs -f rag-app
```

### Step 6: Validate Migration
```bash
# Test application health
curl http://localhost:8501/_stcore/health

# Test document upload (upload a sample PDF)
# Test search functionality
```

## Phase 3: Production Deployment

### Step 1: Production Environment Setup
```bash
# Start production environment
docker-compose up -d

# Verify all services
docker-compose ps
```

### Step 2: Configure Reverse Proxy
The nginx configuration provides:
- Load balancing
- SSL termination (when configured)
- Rate limiting
- Static file caching

### Step 3: Database Setup
PostgreSQL is now used for:
- Document metadata
- User sessions
- Search query analytics

The database is automatically initialized with the required schema.

## Phase 4: Feature Enhancements

### Enhanced Document Management
The Docker setup includes:
- Persistent storage for uploaded files
- Database tracking of document metadata
- Better error handling and logging

### Caching Layer
Redis provides:
- Embedding caching for frequently accessed documents
- Session management
- Performance optimization

### Monitoring and Observability
```bash
# View system resources
docker stats

# Check application logs
docker-compose logs rag-app

# Monitor database
docker-compose exec postgres psql -U raguser ragdb -c "SELECT COUNT(*) FROM documents;"
```

## Phase 5: Optimization and Scaling

### Performance Tuning
```bash
# Adjust memory limits in docker-compose.yml
services:
  rag-app:
    deploy:
      resources:
        limits:
          memory: 4G
```

### Horizontal Scaling
```bash
# Scale application instances
docker-compose up -d --scale rag-app=3
```

### Load Testing
```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test concurrent requests
ab -n 100 -c 10 http://localhost:8501/
```

## Troubleshooting Migration Issues

### Common Problems and Solutions

#### 1. API Key Issues
```bash
# Verify environment variables are loaded
docker-compose exec rag-app env | grep API_KEY

# Check configuration loading
docker-compose exec rag-app python -c "from config import COHERE_API_KEY; print('✓' if COHERE_API_KEY else '✗')"
```

#### 2. Data Access Issues
```bash
# Check volume mounts
docker-compose exec rag-app ls -la /app/data/

# Fix permissions if needed
docker-compose exec rag-app chown -R appuser:appuser /app/data/
```

#### 3. Port Conflicts
```bash
# Check if ports are in use
sudo netstat -tulpn | grep :8501

# Change ports in docker-compose.yml if needed
ports:
  - "8502:8501"  # Use different external port
```

#### 4. Memory Issues
```bash
# Monitor memory usage
docker stats --format "table {{.Container}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Increase container memory limits
deploy:
  resources:
    limits:
      memory: 6G
```

#### 5. Database Connection Issues
```bash
# Check database status
docker-compose exec postgres pg_isready

# Reset database if needed
docker-compose down
docker volume rm multimodal-rag-demo-main_postgres_data
docker-compose up -d
```

## Rollback Procedure

If you need to rollback to the original setup:

### Step 1: Stop Docker Containers
```bash
docker-compose down
```

### Step 2: Restore Original Files
```bash
# Restore original config
cp config.py.backup config.py

# Restore original requirements
cp requirements_backup.txt requirements.txt
```

### Step 3: Restore Data
```bash
# Copy data back from backup
rm -rf data/
cp -r data_backup_YYYYMMDD_HHMMSS/ data/
```

### Step 4: Restart Original Application
```bash
# Install original dependencies
pip install -r requirements.txt

# Start Streamlit
streamlit run app.py
```

## Next Steps After Migration

### 1. n8n Integration
With Docker Compose, you can easily add n8n:
```yaml
# Add to docker-compose.yml
n8n:
  image: n8nio/n8n
  ports:
    - "5678:5678"
  environment:
    - WEBHOOK_URL=http://localhost:5678/
  volumes:
    - n8n_data:/home/node/.n8n
```

### 2. API Development
Consider creating REST API endpoints for better integration:
```python
# api.py (future enhancement)
from fastapi import FastAPI
app = FastAPI()

@app.post("/api/documents/upload")
async def upload_document():
    # Document upload endpoint
    pass

@app.post("/api/search")
async def search_documents():
    # Search endpoint for n8n
    pass
```

### 3. Advanced Features
- User authentication
- Document versioning
- Advanced analytics
- Multi-language support
- Custom embedding models

### 4. Production Hardening
- SSL/TLS certificates
- Security scanning
- Automated backups
- Monitoring and alerting
- Log aggregation

## Validation Checklist

After migration, verify:
- [ ] Application loads at http://localhost:8501
- [ ] Document upload works
- [ ] Search functionality works
- [ ] Data persists after container restart
- [ ] All services are healthy
- [ ] Logs show no errors
- [ ] Environment variables are properly loaded
- [ ] Database connections work
- [ ] Redis caching is functional

## Support and Resources

- **Documentation**: README-Docker.md
- **Configuration**: .env.template
- **Logs**: `docker-compose logs`
- **Health Checks**: `docker-compose exec rag-app curl http://localhost:8501/_stcore/health`

For additional help, check the troubleshooting section in README-Docker.md or create an issue in the project repository.
