# 🔍 Multimodal RAG System with Docker Compose & N8N Integration

A production-ready containerized deployment of a **Multimodal Retrieval-Augmented Generation (RAG)** system that combines **Cohere's multimodal embeddings** with **Gemini 2.5 Flash** for answering questions from both text and images in PDF documents. This system includes a complete API layer for seamless N8N automation integration.

## 📋 Table of Contents

- [System Overview](#system-overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [API Documentation](#api-documentation)
- [N8N Integration](#n8n-integration)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)

## 🏗️ System Overview

This system transforms PDF documents into a searchable multimodal knowledge base by:
1. **Extracting** both text content and page images from PDFs
2. **Embedding** content using Cohere's Embed-v4.0 multimodal model
3. **Storing** embeddings in FAISS vector database for fast similarity search
4. **Retrieving** relevant context (text or images) based on user queries
5. **Generating** contextual answers using Google's Gemini 2.5 Flash model

### Key Features
- ✅ **Multimodal RAG** (text + visual embeddings)
- ✅ **Production-ready Docker deployment**
- ✅ **REST API for automation integration**
- ✅ **N8N workflow automation support**
- ✅ **Streamlit web interface**
- ✅ **Ubuntu Server optimized**
- ✅ **Persistent data storage**

## 📋 Prerequisites

### System Requirements
- **Operating System**: Ubuntu Server 20.04+ (recommended) or Ubuntu Desktop
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: 10GB free space minimum
- **CPU**: 2+ cores recommended

### Required Software
- Docker Engine 20.10+
- Docker Compose 2.0+
- Git

### API Keys Required
- **Cohere API Key**: Sign up at [Cohere Dashboard](https://dashboard.cohere.com/)
- **Gemini API Key**: Get access via [Google AI Studio](https://aistudio.google.com/)

### Ubuntu Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Install Git
sudo apt install git -y

# Logout and login again to apply Docker group membership
```

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd multimodal_RAG_OpenUI_V2
```

### 2. Configure Environment Variables
```bash
# Edit environment variables
nano .env
```

Update `.env` with your actual API keys:
```env
COHERE_API_KEY=your_actual_cohere_api_key_here
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash-preview-04-17
N8N_USER=admin
N8N_PASSWORD=your_secure_password_here
N8N_ENCRYPTION_KEY=your_secure_encryption_key_here
N8N_HOST=localhost
```

### 3. Deploy the System
```bash
# Build and start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. Access the Applications
- **Streamlit UI**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs
- **N8N Interface**: http://localhost:5678
  - Username: admin
  - Password: (as set in .env file)

### 5. Verify Deployment
```bash
# Check API health
curl http://localhost:8000/health

# Check system status
curl http://localhost:8000/status
```

## 🏛️ Architecture

### Container Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Compose Network                  │
│                                                             │
│  ┌──────────────────┐    ┌──────────────────┐              │
│  │  multimodal-rag  │    │       n8n        │              │
│  │                  │    │                  │              │
│  │  ┌─────────────┐ │    │  Workflow Engine │              │
│  │  │ Streamlit   │ │    │  - HTTP Requests │              │
│  │  │    :8501    │ │    │  - Webhooks      │              │
│  │  └─────────────┘ │    │  - Automation    │              │
│  │                  │    │      :5678       │              │
│  │  ┌─────────────┐ │    └──────────────────┘              │
│  │  │  FastAPI    │ │                                      │
│  │  │    :8000    │ │                                      │
│  │  └─────────────┘ │                                      │
│  └──────────────────┘                                      │
│                                                             │
│  ┌──────────────────┐    ┌──────────────────┐              │
│  │   Persistent     │    │    Persistent    │              │
│  │   RAG Data       │    │    N8N Data      │              │
│  │   - FAISS Index  │    │   - Workflows    │              │
│  │   - Documents    │    │   - Credentials  │              │
│  │   - Images       │    │   - Executions   │              │
│  └──────────────────┘    └──────────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow
1. **Document Ingestion**: PDFs → Text Extraction + Image Conversion
2. **Embedding Generation**: Cohere Embed-v4.0 → Vector Embeddings
3. **Storage**: FAISS Index + Metadata in Pickle files
4. **Query Processing**: User Query → Embedding → Similarity Search
5. **Answer Generation**: Retrieved Context + Gemini 2.5 Flash → Response

## 📖 API Documentation

### Base URL
- Local: `http://localhost:8000`
- Production: `http://your-server-ip:8000`

### Core Endpoints

#### 1. Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "multimodal-rag-api"
}
```

#### 2. System Status
```http
GET /status
```

**Response:**
```json
{
  "status": "active",
  "total_documents": 15,
  "text_documents": 5,
  "image_documents": 10,
  "faiss_index_size": 15
}
```

#### 3. Upload Documents
```http
POST /documents/upload
Content-Type: multipart/form-data
```

**Request:**
```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@document1.pdf" \
  -F "files=@document2.pdf"
```

#### 4. Query Documents
```http
POST /query
Content-Type: application/json
```

**Request:**
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the profit margin of Visa?",
    "top_k": 3
  }'
```

#### 5. List Documents
```http
GET /documents
```

#### 6. Clear All Documents
```http
DELETE /documents/clear
```

## 🔄 N8N Integration

### Accessing N8N
1. Navigate to `http://localhost:5678`
2. Login with credentials from `.env` file

### Setting Up RAG Workflows

#### Basic Query Workflow
1. **Webhook Trigger Node**:
   - Method: `POST`
   - Path: `/rag-query`

2. **HTTP Request Node**:
   - Method: `POST`
   - URL: `http://multimodal-rag:8000/query`
   - Headers: `Content-Type: application/json`
   - Body:
   ```json
   {
     "query": "{{ $json.query }}",
     "top_k": 3
   }
   ```

3. **Response Node**: Return the answer to the webhook caller

### N8N Best Practices
- **Error Handling**: Always add error handling nodes for API calls
- **Rate Limiting**: Implement delays between bulk operations
- **Logging**: Use function nodes to log important data
- **Validation**: Validate inputs before sending to RAG API

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `COHERE_API_KEY` | Cohere API key for embeddings | - | Yes |
| `GEMINI_API_KEY` | Google Gemini API key | - | Yes |
| `GEMINI_MODEL` | Gemini model version | `gemini-2.5-flash-preview-04-17` | No |
| `N8N_USER` | N8N admin username | `admin` | No |
| `N8N_PASSWORD` | N8N admin password | `admin123` | No |
| `N8N_ENCRYPTION_KEY` | N8N encryption key | - | Yes |

### Port Configuration

| Service | Internal Port | External Port | Purpose |
|---------|---------------|---------------|---------|
| Streamlit | 8501 | 8501 | Web UI |
| FastAPI | 8000 | 8000 | REST API |
| N8N | 5678 | 5678 | Automation Platform |

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. Container Startup Issues
```bash
# Check container status
docker-compose ps

# View detailed logs
docker-compose logs multimodal-rag
docker-compose logs n8n
```

**Solutions**:
- Ensure sufficient memory (4GB+ recommended)
- Verify API keys are correctly set in `.env`
- Check port availability

#### 2. API Key Issues
```bash
# Check logs for API errors
docker-compose logs multimodal-rag | grep -i "error"
```

**Solutions**:
- Verify Cohere API key at https://dashboard.cohere.com/
- Verify Gemini API key at https://aistudio.google.com/
- Check API quotas and billing status

### Health Check Commands
```bash
# Full system health check
docker-compose ps
curl -s http://localhost:8000/health
curl -s http://localhost:8000/status
```

## 🔒 Security Considerations

### Basic Security Hardening

1. **Change default N8N credentials**
2. **Generate strong encryption keys**
3. **Implement API authentication for production**
4. **Set up HTTPS/TLS**
5. **Configure firewall rules**
6. **Regular security updates**

### API Key Management
- Never commit API keys to version control
- Use environment variables for all sensitive data
- Rotate API keys regularly
- Monitor API usage for anomalies

---

**🎯 Success Criteria**: The deployment is successful when you can upload a PDF document via the web interface, query it through both the UI and API, and create N8N workflows that interact with the RAG system APIs.

**📊 System Ready**: Your multimodal RAG system is now ready for production use with full N8N integration capabilities!
