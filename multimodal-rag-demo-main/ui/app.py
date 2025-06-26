"""
Enhanced Streamlit UI for Multimodal RAG System
Communicates with FastAPI backend for production deployment
"""

import streamlit as st
import requests
import httpx
import asyncio
import time
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import os

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
DEFAULT_API_KEY = os.getenv("DEFAULT_API_KEY", "")

# Page configuration
st.set_page_config(
    page_title="Multimodal RAG System",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

class APIClient:
    """Client for communicating with the FastAPI backend"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def upload_documents(self, files: List) -> Dict[str, Any]:
        """Upload documents to the API"""
        try:
            files_data = []
            for file in files:
                files_data.append(("files", (file.name, file.getvalue(), file.type)))
            
            response = requests.post(
                f"{self.base_url}/documents/upload",
                files=files_data,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Upload failed: {response.text}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def search_documents(self, query: str, top_k: int = 5, include_answer: bool = True) -> Dict[str, Any]:
        """Search documents via API"""
        try:
            payload = {
                "query": query,
                "top_k": top_k,
                "include_answer": include_answer,
                "filters": {}
            }
            
            response = requests.post(
                f"{self.base_url}/search",
                json=payload,
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Search failed: {response.text}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def get_documents(self) -> List[Dict[str, Any]]:
        """Get list of user documents"""
        try:
            response = requests.get(
                f"{self.base_url}/documents",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return []
                
        except Exception as e:
            st.error(f"Error fetching documents: {e}")
            return []
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status"""
        try:
            response = requests.get(
                f"{self.base_url}/tasks/{task_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Task status fetch failed: {response.text}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document"""
        try:
            response = requests.delete(
                f"{self.base_url}/documents/{doc_id}",
                headers=self.headers
            )
            
            return response.status_code == 200
            
        except Exception as e:
            st.error(f"Error deleting document: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check API health"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

# Initialize session state
def init_session_state():
    """Initialize Streamlit session state"""
    if 'api_client' not in st.session_state:
        st.session_state.api_client = None
    
    if 'documents' not in st.session_state:
        st.session_state.documents = []
    
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []
    
    if 'current_task' not in st.session_state:
        st.session_state.current_task = None

def setup_api_client():
    """Setup API client with authentication"""
    st.sidebar.header("🔐 API Configuration")
    
    # API URL configuration
    api_url = st.sidebar.text_input(
        "API Base URL",
        value=API_BASE_URL,
        help="URL of the FastAPI backend"
    )
    
    # API Key configuration
    api_key = st.sidebar.text_input(
        "API Key",
        value=DEFAULT_API_KEY,
        type="password",
        help="Your API key for authentication"
    )
    
    if st.sidebar.button("Connect to API"):
        if api_key:
            client = APIClient(api_url, api_key)
            if client.health_check():
                st.session_state.api_client = client
                st.sidebar.success("✅ Connected to API")
            else:
                st.sidebar.error("❌ Failed to connect to API")
        else:
            st.sidebar.error("Please enter an API key")
    
    # Show connection status
    if st.session_state.api_client:
        if st.session_state.api_client.health_check():
            st.sidebar.success("🟢 API Connected")
        else:
            st.sidebar.error("🔴 API Disconnected")
            st.session_state.api_client = None

def document_upload_tab():
    """Document upload and management tab"""
    st.header("📄 Document Management")
    
    if not st.session_state.api_client:
        st.warning("Please connect to the API first using the sidebar.")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Upload Documents")
        uploaded_files = st.file_uploader(
            "Choose PDF files",
            type=["pdf"],
            accept_multiple_files=True,
            help="Upload PDF documents to index for searching"
        )
        
        if uploaded_files and st.button("🚀 Process Documents", type="primary"):
            with st.spinner("Uploading documents..."):
                result = st.session_state.api_client.upload_documents(uploaded_files)
                
                if "error" in result:
                    st.error(f"Upload failed: {result['error']}")
                else:
                    st.success(f"✅ Upload started! Task ID: {result.get('task_id', 'Unknown')}")
                    st.session_state.current_task = result.get('task_id')
                    
                    # Show estimated completion time
                    if 'estimated_completion' in result:
                        st.info(f"⏱️ Estimated completion: {result['estimated_completion']}")
    
    with col2:
        st.subheader("Upload Status")
        
        # Show current task status
        if st.session_state.current_task:
            if st.button("🔄 Refresh Status"):
                task_status = st.session_state.api_client.get_task_status(st.session_state.current_task)
                
                if "error" not in task_status:
                    task_info = task_status.get('task', {})
                    progress = task_info.get('progress', 0)
                    status = task_info.get('status', 'unknown')
                    
                    st.progress(progress / 100.0)
                    st.write(f"Status: {status}")
                    st.write(f"Progress: {progress:.1f}%")
                    
                    if status == 'completed':
                        st.success("✅ Processing completed!")
                        st.session_state.current_task = None
                        # Refresh documents list
                        st.session_state.documents = st.session_state.api_client.get_documents()
                    elif status == 'failed':
                        st.error("❌ Processing failed!")
                        st.session_state.current_task = None
    
    # Document list
    st.subheader("📚 Your Documents")
    
    if st.button("🔄 Refresh Documents"):
        st.session_state.documents = st.session_state.api_client.get_documents()
    
    if st.session_state.documents:
        # Create documents dataframe
        docs_data = []
        for doc in st.session_state.documents:
            docs_data.append({
                "Filename": doc.get("filename", "Unknown"),
                "Size (MB)": f"{doc.get('size', 0) / (1024*1024):.2f}",
                "Upload Date": doc.get("upload_date", "Unknown"),
                "Status": doc.get("status", "Unknown"),
                "Pages": doc.get("page_count", 0),
                "Text Chunks": doc.get("text_chunks", 0),
                "Image Chunks": doc.get("image_chunks", 0),
                "ID": doc.get("id", "")
            })
        
        df = pd.DataFrame(docs_data)
        
        # Display documents table
        st.dataframe(df, use_container_width=True)
        
        # Document statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Documents", len(st.session_state.documents))
        
        with col2:
            total_size = sum(doc.get("size", 0) for doc in st.session_state.documents)
            st.metric("Total Size", f"{total_size / (1024*1024):.1f} MB")
        
        with col3:
            total_text = sum(doc.get("text_chunks", 0) for doc in st.session_state.documents)
            st.metric("Text Chunks", total_text)
        
        with col4:
            total_images = sum(doc.get("image_chunks", 0) for doc in st.session_state.documents)
            st.metric("Image Chunks", total_images)
        
        # Document type distribution chart
        if len(st.session_state.documents) > 0:
            st.subheader("📊 Content Distribution")
            
            content_data = []
            for doc in st.session_state.documents:
                content_data.extend([
                    {"Type": "Text", "Count": doc.get("text_chunks", 0)},
                    {"Type": "Images", "Count": doc.get("image_chunks", 0)}
                ])
            
            content_df = pd.DataFrame(content_data)
            content_summary = content_df.groupby("Type")["Count"].sum().reset_index()
            
            fig = px.pie(
                content_summary,
                values="Count",
                names="Type",
                title="Content Type Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("No documents uploaded yet. Upload some PDF files to get started!")

def search_tab():
    """Search and query tab"""
    st.header("🔍 Search Your Documents")
    
    if not st.session_state.api_client:
        st.warning("Please connect to the API first using the sidebar.")
        return
    
    # Search interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input(
            "Enter your search query",
            placeholder="e.g., What is the main topic of the documents?",
            help="Ask questions about your uploaded documents"
        )
    
    with col2:
        top_k = st.selectbox("Results to show", [3, 5, 10, 15], index=1)
        include_answer = st.checkbox("Generate AI Answer", value=True)
    
    if query and st.button("🔍 Search", type="primary"):
        with st.spinner("Searching your documents..."):
            start_time = time.time()
            
            search_result = st.session_state.api_client.search_documents(
                query, top_k, include_answer
            )
            
            search_time = time.time() - start_time
            
            if "error" in search_result:
                st.error(f"Search failed: {search_result['error']}")
            else:
                # Save to search history
                search_entry = {
                    "query": query,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "results_count": len(search_result.get("results", [])),
                    "processing_time": search_time
                }
                st.session_state.search_history.append(search_entry)
                
                # Display results
                display_search_results(search_result)

def display_search_results(search_result: Dict[str, Any]):
    """Display search results"""
    results = search_result.get("results", [])
    answer = search_result.get("answer")
    processing_time = search_result.get("processing_time", 0)
    
    # Performance metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Results Found", len(results))
    with col2:
        st.metric("Processing Time", f"{processing_time:.2f}s")
    with col3:
        relevance_score = max([r.get("similarity_score", 0) for r in results], default=0)
        st.metric("Best Match Score", f"{relevance_score:.2%}")
    
    # AI Answer
    if answer:
        st.subheader("🤖 AI Answer")
        st.markdown(f"**{answer}**")
        st.divider()
    
    # Search Results
    if results:
        st.subheader("📋 Search Results")
        
        for i, result in enumerate(results, 1):
            with st.expander(f"Result {i}: {result.get('source', 'Unknown')} (Score: {result.get('similarity_score', 0):.2%})"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    content_type = result.get("content_type", "text")
                    
                    if content_type == "text":
                        st.markdown("**📄 Text Content:**")
                        st.text_area("Content", result.get("content", ""), height=150, disabled=True)
                    else:
                        st.markdown("**🖼️ Image Content:**")
                        # Display image if preview URL is available
                        preview_url = result.get("preview_url")
                        if preview_url:
                            st.image(f"{st.session_state.api_client.base_url}{preview_url}")
                        else:
                            st.info("Image preview not available")
                
                with col2:
                    st.markdown("**📊 Metadata:**")
                    st.write(f"**Source:** {result.get('source', 'Unknown')}")
                    st.write(f"**Type:** {result.get('content_type', 'Unknown')}")
                    st.write(f"**Page:** {result.get('page', 'N/A')}")
                    st.write(f"**Similarity:** {result.get('similarity_score', 0):.2%}")
    else:
        st.info("No results found for your query. Try rephrasing or uploading more documents.")

def analytics_tab():
    """Analytics and insights tab"""
    st.header("📊 Analytics & Insights")
    
    if not st.session_state.search_history:
        st.info("No search history available. Perform some searches to see analytics.")
        return
    
    # Search history analysis
    df = pd.DataFrame(st.session_state.search_history)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Search Activity Over Time")
        daily_searches = df.groupby(df['timestamp'].dt.date).size().reset_index()
        daily_searches.columns = ['Date', 'Searches']
        
        fig = px.line(
            daily_searches,
            x='Date',
            y='Searches',
            title='Daily Search Activity'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Search Performance")
        avg_time = df['processing_time'].mean()
        avg_results = df['results_count'].mean()
        
        st.metric("Average Processing Time", f"{avg_time:.2f}s")
        st.metric("Average Results per Search", f"{avg_results:.1f}")
        
        # Processing time distribution
        fig = px.histogram(
            df,
            x='processing_time',
            title='Processing Time Distribution',
            nbins=20
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent searches
    st.subheader("🕒 Recent Searches")
    recent_searches = df.tail(10)[['timestamp', 'query', 'results_count', 'processing_time']]
    recent_searches = recent_searches.sort_values('timestamp', ascending=False)
    st.dataframe(recent_searches, use_container_width=True)

def settings_tab():
    """Settings and configuration tab"""
    st.header("⚙️ Settings & Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔧 Search Settings")
        
        default_top_k = st.slider("Default results count", 1, 20, 5)
        default_include_answer = st.checkbox("Generate AI answers by default", True)
        
        st.subheader("🎨 UI Settings")
        
        theme = st.selectbox("Theme", ["Light", "Dark", "Auto"])
        show_advanced = st.checkbox("Show advanced options", False)
        
    with col2:
        st.subheader("📊 Export Options")
        
        if st.button("📥 Export Search History"):
            if st.session_state.search_history:
                df = pd.DataFrame(st.session_state.search_history)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"search_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No search history to export")
        
        st.subheader("🗑️ Data Management")
        
        if st.button("Clear Search History", type="secondary"):
            st.session_state.search_history = []
            st.success("Search history cleared!")
        
        if st.button("Refresh All Data", type="secondary"):
            if st.session_state.api_client:
                st.session_state.documents = st.session_state.api_client.get_documents()
                st.success("Data refreshed!")

def main():
    """Main application"""
    st.title("🔍 Multimodal RAG System")
    st.markdown("*Search across text and images in your PDF documents with AI-powered answers*")
    
    # Initialize session state
    init_session_state()
    
    # Setup API client in sidebar
    setup_api_client()
    
    # Main navigation
    tab1, tab2, tab3, tab4 = st.tabs(["📄 Documents", "🔍 Search", "📊 Analytics", "⚙️ Settings"])
    
    with tab1:
        document_upload_tab()
    
    with tab2:
        search_tab()
    
    with tab3:
        analytics_tab()
    
    with tab4:
        settings_tab()
    
    # Footer
    st.divider()
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <p>Multimodal RAG System v1.0 | Built with Streamlit & FastAPI</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
