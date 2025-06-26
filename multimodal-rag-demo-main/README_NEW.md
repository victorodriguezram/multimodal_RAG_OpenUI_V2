# 🔍 Multimodal RAG System - Production Ready

A **production-ready** Multimodal Retrieval-Augmented Generation (RAG) system with full containerization, N8N integration, monitoring, and comprehensive API capabilities. This system enables intelligent document processing and search across both text and visual content.

## 🚀 Quick Start

### For Demo/Development:
```bash
git clone <repository-url>
cd multimodal-rag-demo-main
cp .env.example .env
# Update .env with your API keys
docker-compose up -d
```

### For Production Deployment:
See the comprehensive [**Production Deployment Guide**](PRODUCTION_README.md) for detailed setup instructions.

---

## 📄 What's New in Production Version

This is a **complete transformation** of the original demo into a production-ready system:

### 🏗️ **Architecture Transformation**
- **Microservices Architecture** - Separate API, UI, and Worker services
- **Container-First Design** - Docker Compose with all services
- **API-First Approach** - Complete REST API with OpenAPI documentation
- **Async Processing** - Background tasks with Celery workers

### 🔌 **Integration & Automation**
- **N8N Integration** - Pre-built workflow examples for automation
- **Webhook Support** - Real-time notifications and integrations
- **External APIs** - RESTful endpoints for third-party systems

### 📊 **Production Operations**
- **Monitoring & Metrics** - Prometheus, Grafana dashboards
- **Centralized Logging** - Structured logging with correlation IDs
- **Health Checks** - Comprehensive service monitoring
- **Backup/Restore** - Automated data protection

### 🔒 **Security & Performance**
- **Authentication** - API key-based access control
- **Rate Limiting** - Protection against abuse
- **Input Validation** - Comprehensive request validation
- **Performance Optimization** - Caching and efficient processing

### 🧪 **Quality Assurance**
- **Test Suite** - Unit, integration, and end-to-end tests
- **CI/CD Pipeline** - GitHub Actions for automated deployment
- **Code Quality** - Linting, formatting, and type checking

---

## ✨ Features

### Core Capabilities
- **Multimodal RAG** - Process both text and images from documents
- **Vector Search** - FAISS-powered similarity search with 768-dim embeddings
- **Smart Chunking** - Intelligent document segmentation
- **Real-time Processing** - Live progress tracking and updates

### API Features
- **Document Upload** - Multi-format support (PDF, images, text)
- **Search Endpoints** - Text and multimodal search capabilities
- **Task Management** - Async job monitoring and results
- **Admin Interface** - System statistics and management

### UI Enhancements
- **Modern Interface** - Enhanced Streamlit UI with real-time updates
- **Progress Tracking** - Live processing status and results
- **Error Handling** - User-friendly error messages and recovery
- **Multi-session Support** - Concurrent user sessions

---

## 📂 System Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    Nginx    │    │  Streamlit  │    │   FastAPI   │
│   (Proxy)   │◄──►│     UI      │◄──►│     API     │
└─────────────┘    └─────────────┘    └─────────────┘
                                              │
                   ┌─────────────┐    ┌─────────────┐
                   │   Celery    │◄──►│ PostgreSQL  │
                   │   Worker    │    │  Database   │
                   └─────────────┘    └─────────────┘
                          │
        ┌─────────────┐   │   ┌─────────────┐   ┌─────────────┐
        │ Prometheus  │   │   │    Redis    │   │    FAISS    │
        │ Monitoring  │   │   │   Broker    │   │   Vector    │
        └─────────────┘   │   └─────────────┘   │   Store     │
                          │                     └─────────────┘
                   ┌─────────────┐    ┌─────────────┐
                   │   Grafana   │    │     N8N     │
                   │ Dashboards  │    │ Workflows   │
                   └─────────────┘    └─────────────┘
```

### Service Details

| Service | Purpose | Port | Health Check |
|---------|---------|------|--------------|
| **API** | FastAPI backend | 8000 | `/health` |
| **UI** | Streamlit interface | 8501 | Direct access |
| **Worker** | Celery task processor | - | Celery status |
| **PostgreSQL** | Primary database | 5432 | Connection test |
| **Redis** | Task broker & cache | 6379 | PING command |
| **Nginx** | Reverse proxy | 80/443 | Status page |
| **Prometheus** | Metrics collection | 9090 | `/metrics` |
| **Grafana** | Monitoring dashboard | 3000 | Login page |

---

## 🛠️ Development Setup

### Prerequisites
- Docker & Docker Compose
- Python 3.9+
- Git
- API Keys (Cohere, Gemini)

### Local Development
```bash
# Clone repository
git clone <repository-url>
cd multimodal-rag-demo-main

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Start development environment
docker-compose up -d

# Run update script
chmod +x scripts/update.sh
./scripts/update.sh
```

### Manual Setup (without Docker)
```bash
# Install dependencies
pip install -r requirements.api.txt
pip install -r requirements.ui.txt
pip install -r requirements.worker.txt

# Start services individually
cd api && uvicorn main:app --reload --port 8000
cd ui && streamlit run app.py --server.port 8501
cd worker && celery -A main worker --loglevel=info
```

---

## 🔌 API Documentation

### Endpoints Overview
- **Document Management**: Upload and process documents
- **Search Operations**: Text and multimodal search
- **Task Monitoring**: Async job status and results
- **N8N Integration**: Webhook endpoints for automation
- **Admin Functions**: System statistics and management

### Quick API Examples

**Upload Document:**
```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -H "X-API-Key: your-api-key" \
  -F "file=@document.pdf"
```

**Search Documents:**
```bash
curl -X POST "http://localhost:8000/search" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the benefits of ETFs?", "top_k": 5}'
```

**Check Task Status:**
```bash
curl "http://localhost:8000/tasks/{task_id}" \
  -H "X-API-Key: your-api-key"
```

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Spec**: `api/openapi.yaml`

---

## 🤖 N8N Workflow Integration

Pre-built workflow examples in `n8n-workflows/`:

- **`email-document-processing.json`** - Automated email document processing
- **`document-classifier.json`** - Intelligent document classification
- **`qa-bot.json`** - Smart Q&A bot with RAG capabilities

### Setting up N8N
```bash
# N8N is included in docker-compose
docker-compose up -d n8n

# Access N8N interface
open http://localhost:5678

# Import workflows from n8n-workflows/ directory
```

---

## 📊 Monitoring & Operations

### Accessing Dashboards
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **API Metrics**: http://localhost:8000/metrics

### Backup Operations
```bash
# Create backup
./scripts/backup.sh my_backup_name

# Restore from backup
./scripts/restore.sh my_backup_name

# List available backups
ls /opt/rag-backups/
```

### Log Management
```bash
# View service logs
docker-compose logs -f api
docker-compose logs -f worker

# System logs location
tail -f logs/application.log
```

---

## 🧪 Testing

### Running Tests
```bash
# Install test dependencies
pip install -r requirements.test.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=api --cov-report=html

# Run specific test categories
pytest tests/test_api.py -v
pytest tests/integration/ -v
```

### CI/CD Pipeline
The project includes a comprehensive GitHub Actions pipeline:
- Code quality checks (linting, formatting, type checking)
- Security scanning
- Automated testing
- Docker image building
- Deployment automation

---

## 📚 Documentation

### Available Guides
- **[Production Deployment](PRODUCTION_README.md)** - Complete production setup
- **[Contributing Guide](CONTRIBUTING.md)** - Development guidelines
- **[API Reference](api/openapi.yaml)** - Complete API specification
- **License**: [MIT License](LICENSE)

### Project Structure
```
multimodal-rag-demo-main/
├── api/                    # FastAPI backend
│   ├── main.py            # Application entry
│   ├── models.py          # Pydantic models
│   ├── openapi.yaml       # API specification
│   └── services/          # Business logic
├── ui/                    # Streamlit frontend
├── worker/                # Celery workers
├── scripts/               # Deployment & maintenance
├── tests/                 # Test suite
├── monitoring/            # Prometheus & Grafana configs
├── n8n-workflows/         # Automation examples
├── docker-compose.yml     # Service orchestration
└── docs/                  # Additional documentation
```

---

## 🚦 Getting Started Checklist

- [ ] Clone repository and set up environment
- [ ] Configure API keys in `.env`
- [ ] Run `docker-compose up -d`
- [ ] Access UI at http://localhost:8501
- [ ] Upload your first document
- [ ] Test search functionality
- [ ] Explore API at http://localhost:8000/docs
- [ ] Set up monitoring dashboards
- [ ] Configure N8N workflows
- [ ] Set up backups and monitoring

---

## 🆘 Support & Troubleshooting

### Common Issues
1. **Services not starting**: Check Docker daemon and available ports
2. **API errors**: Verify API keys in `.env` file
3. **Memory issues**: Increase Docker memory allocation
4. **Permission errors**: Run `chmod +x scripts/*.sh`

### Getting Help
- Check [PRODUCTION_README.md](PRODUCTION_README.md) for detailed troubleshooting
- Review logs: `docker-compose logs -f`
- Create an issue on GitHub
- Consult the API documentation

---

## 🎯 Next Steps

1. **Production Deployment**: Follow the production guide for live deployment
2. **Custom Workflows**: Create N8N workflows for your specific use cases
3. **API Integration**: Integrate the API with your existing systems
4. **Monitoring Setup**: Configure alerts and monitoring for production
5. **Performance Tuning**: Optimize for your specific workload and scale

---

## 👨‍💻 Credits

Built upon the original multimodal RAG demo, transformed into a production-ready system with:
- Modern microservices architecture
- Comprehensive API and automation capabilities
- Production-grade monitoring and operations
- Full documentation and testing suite

**Original Demo**: Based on Cohere multimodal embeddings and Gemini 2.5 Flash
**Production Enhancement**: Complete system redesign for enterprise deployment

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
