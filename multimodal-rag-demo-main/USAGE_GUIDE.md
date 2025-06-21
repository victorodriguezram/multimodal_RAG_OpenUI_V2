# 🚀 Complete Usage Guide: API & UI

## 📡 n8n API Integration Guide

### **API Base URLs:**
- **Development**: `http://your-server-ip:8000`
- **Production (with nginx)**: `http://your-server-ip/api`

### **1. Document Upload API**

#### **Endpoint:**
```http
POST /api/documents/upload
```

#### **n8n HTTP Request Node Configuration:**
```json
{
  "method": "POST",
  "url": "http://your-server-ip:8000/api/documents/upload",
  "headers": {
    "Content-Type": "multipart/form-data"
  },
  "body": {
    "file": "{{ $binary.data }}"
  }
}
```

#### **Example Response:**
```json
{
  "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "filename": "financial_report.pdf",
  "status": "processing",
  "message": "Document upload successful, processing started"
}
```

#### **n8n Workflow Example:**
```
1. Trigger (Webhook/Email/File Upload)
2. HTTP Request (Upload PDF)
3. Wait (30 seconds for processing)
4. HTTP Request (Check status)
5. Conditional (If completed, proceed)
```

### **2. Document Query API**

#### **Endpoint:**
```http
POST /api/query
```

#### **n8n HTTP Request Node Configuration:**
```json
{
  "method": "POST",
  "url": "http://your-server-ip:8000/api/query",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "query": "{{ $json.question }}",
    "top_k": 3
  }
}
```

#### **Example Request Body:**
```json
{
  "query": "What was the revenue in Q4?",
  "top_k": 3
}
```

#### **Example Response:**
```json
{
  "answer": "Based on the financial report, the revenue in Q4 was $2.5 million, representing a 15% increase from the previous quarter.",
  "sources": [
    {
      "source": "financial_report.pdf",
      "content_type": "text",
      "similarity": 0.8945,
      "preview": "Q4 revenue reached $2.5M..."
    },
    {
      "source": "financial_report.pdf", 
      "content_type": "image",
      "similarity": 0.8234,
      "page": 3
    }
  ],
  "processing_time": 2.341
}
```

### **3. n8n-Optimized Webhook**

#### **Endpoint:**
```http
POST /webhook/n8n/query
```

#### **n8n Webhook Node Configuration:**
```json
{
  "method": "POST",
  "url": "http://your-server-ip:8000/webhook/n8n/query",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "query": "{{ $json.question }}"
  }
}
```

#### **Simplified Response for n8n:**
```json
{
  "answer": "The revenue in Q4 was $2.5 million...",
  "query": "What was the revenue in Q4?",
  "sources_count": 2,
  "processing_time": 2.341,
  "timestamp": "2025-06-20T15:30:45",
  "sources": [...]
}
```

### **4. Document Status Check**

#### **Endpoint:**
```http
GET /api/documents/{document_id}/status
```

#### **n8n Configuration:**
```json
{
  "method": "GET",
  "url": "http://your-server-ip:8000/api/documents/{{ $json.document_id }}/status"
}
```

#### **Response:**
```json
{
  "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "filename": "financial_report.pdf",
  "status": "completed",
  "embeddings_count": 15,
  "upload_time": "2025-06-20T15:25:30"
}
```

### **5. List All Documents**

#### **Endpoint:**
```http
GET /api/documents
```

#### **Response:**
```json
{
  "documents": [
    {
      "filename": "financial_report.pdf",
      "text_content": true,
      "image_pages": [1, 2, 3, 4, 5],
      "total_embeddings": 15
    }
  ],
  "total_count": 1
}
```

## 🎨 Built-in Streamlit UI Guide

### **Access URLs:**
- **Development**: `http://your-server-ip:8501`
- **Production (with nginx)**: `http://your-server-ip`

### **Tab 1: Index Documents**

#### **Document Upload Process:**
1. **Click "Browse files"** or drag & drop PDFs
2. **Select multiple PDFs** (supports batch processing)
3. **Click "Process Documents"**
4. **Monitor progress bar** and status messages
5. **View completion summary** with embedding counts

#### **What Happens During Processing:**
```
📄 PDF Upload → 🔄 Processing → ✅ Indexed

For each PDF:
├── Text Extraction (PyPDF2)
├── Image Conversion (pdf2image) 
├── Text Embedding (Cohere v4.0)
├── Image Embeddings (Cohere v4.0)
├── FAISS Index Storage
└── Metadata Persistence
```

#### **Processing Status Indicators:**
- **"Processing document.pdf... (1/3)"** - Current file being processed
- **Progress bar** - Overall completion percentage
- **"All documents processed and indexed!"** - Success message

### **Tab 2: Search & Query**

#### **Search Process:**
1. **Enter your question** in the text input
   - Example: "What is the profit of Visa?"
   - Example: "Show me the revenue chart"
   - Example: "What are the key risks mentioned?"

2. **Press Enter** or click outside the input

3. **View Results:**
   - **🤖 LLM Answer** - AI-generated response from Gemini
   - **🖼️ Image Match** - Relevant PDF page images (if found)
   - **📄 Text Match** - Relevant text excerpts (if found)

#### **Search Features:**
- **Multimodal Results**: Gets both text and image content
- **Source Attribution**: Shows which PDF and page
- **Similarity Scoring**: Most relevant results first
- **Context Preservation**: Maintains document context

### **Sidebar: Index Statistics**

#### **Information Displayed:**
- **Total indexed items** - Number of embeddings stored
- **Content Type Pie Chart** - Distribution of text vs. image embeddings
- **Clear All Data Button** - ⚠️ Removes all indexed documents

#### **Management Actions:**
- **"Clear All Indexed Data"** - Completely resets the system
- **Real-time updates** - Statistics update after each upload

## 🔧 **n8n Integration Workflows**

### **Workflow 1: Document Processing Pipeline**
```
Email with PDF → Extract Attachment → Upload to RAG → 
Check Status → Notify Completion → Store Document ID
```

### **Workflow 2: Automated Q&A System**
```
Webhook Question → Query RAG API → Format Response → 
Send to Slack/Email/Database
```

### **Workflow 3: Document Analysis**
```
Scheduled Trigger → List Documents → 
For Each Document → Generate Summary → 
Compile Report → Send Weekly Digest
```

### **Workflow 4: Customer Support Integration**
```
Support Ticket → Extract Question → Query RAG → 
Check Confidence → Auto-Reply or Flag for Human
```

## 🌐 **API Testing with curl**

### **Upload Document:**
```bash
curl -X POST "http://your-server-ip:8000/api/documents/upload" \
     -F "file=@financial_report.pdf"
```

### **Query Documents:**
```bash
curl -X POST "http://your-server-ip:8000/api/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "What was the revenue?", "top_k": 3}'
```

### **Check Document Status:**
```bash
curl "http://your-server-ip:8000/api/documents/a1b2c3d4-e5f6-7890/status"
```

### **n8n Webhook:**
```bash
curl -X POST "http://your-server-ip:8000/webhook/n8n/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "What are the key findings?"}'
```

## 🔍 **Advanced Features**

### **API Features:**
- ✅ **Asynchronous Processing** - Non-blocking document uploads
- ✅ **Status Tracking** - Real-time processing updates
- ✅ **Error Handling** - Comprehensive error responses
- ✅ **Rate Limiting** - Built-in request throttling
- ✅ **Health Checks** - System monitoring endpoints

### **UI Features:**
- ✅ **Drag & Drop Upload** - Easy file management
- ✅ **Progress Tracking** - Visual processing feedback
- ✅ **Multimodal Display** - Text and image results
- ✅ **Real-time Search** - Instant query processing
- ✅ **Statistics Dashboard** - System overview

### **Integration Benefits:**
- 🚀 **Dual Interface** - Both programmatic API and visual UI
- 🔄 **Shared Data** - API and UI use same backend
- 📊 **Real-time Sync** - Changes reflect immediately
- 🛡️ **Security** - Rate limiting and input validation
- 📈 **Scalable** - Handles multiple concurrent requests

The system provides both **human-friendly UI** for manual document management and **API endpoints** for automation with n8n! 🎯
