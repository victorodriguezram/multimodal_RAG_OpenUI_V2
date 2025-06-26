"""
Search service for multimodal RAG operations
"""

import os
import json
import time
from typing import List, Dict, Any, Optional
import structlog
import numpy as np
import faiss
from PIL import Image

from ..models import SearchRequest, SearchResponse, SearchResult, ContentType
from ..config import get_settings
from ...core.embeddings import get_query_embedding
from ...core.search import answer_with_gemini

logger = structlog.get_logger()
settings = get_settings()

class SearchService:
    """Handle search operations across multimodal content"""
    
    @staticmethod
    async def initialize():
        """Initialize search service"""
        try:
            logger.info("Search service initialized")
        except Exception as e:
            logger.error("Failed to initialize search service", error=str(e))
            raise
    
    @staticmethod
    async def search(
        query: str,
        user_id: str,
        top_k: int = 5,
        include_answer: bool = True,
        filters: Optional[Dict[str, Any]] = None
    ) -> SearchResponse:
        """
        Perform multimodal search across user's documents
        
        Args:
            query: Search query
            user_id: User ID for document access
            top_k: Number of results to return
            include_answer: Whether to generate AI answer
            filters: Optional search filters
            
        Returns:
            SearchResponse with results and optional AI answer
        """
        start_time = time.time()
        
        try:
            # Get query embedding
            query_vector = get_query_embedding(query)
            if query_vector is None:
                return SearchResponse(
                    query=query,
                    results=[],
                    answer=None,
                    total_results=0,
                    processing_time=time.time() - start_time
                )
            
            # Load user's FAISS index and metadata
            index, metadata = await SearchService._load_user_index(user_id)
            if index is None or not metadata:
                return SearchResponse(
                    query=query,
                    results=[],
                    answer="No documents found for this user.",
                    total_results=0,
                    processing_time=time.time() - start_time
                )
            
            # Perform vector search
            search_results = await SearchService._vector_search(
                query_vector, index, metadata, top_k, filters
            )
            
            # Generate AI answer if requested
            answer = None
            if include_answer and search_results:
                answer = await SearchService._generate_answer(query, search_results)
            
            processing_time = time.time() - start_time
            
            logger.info(
                "Search completed",
                user_id=user_id,
                query=query,
                results_count=len(search_results),
                processing_time=processing_time
            )
            
            return SearchResponse(
                query=query,
                results=search_results,
                answer=answer,
                total_results=len(search_results),
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error("Search error", error=str(e), user_id=user_id, query=query)
            return SearchResponse(
                query=query,
                results=[],
                answer=f"Search error: {str(e)}",
                total_results=0,
                processing_time=time.time() - start_time
            )
    
    @staticmethod
    async def _load_user_index(user_id: str) -> tuple[Optional[faiss.Index], List[Dict]]:
        """Load user's FAISS index and metadata"""
        try:
            index_path = os.path.join(settings.FAISS_FULL_PATH, f"user_{user_id}.index")
            metadata_path = os.path.join(settings.FAISS_FULL_PATH, f"user_{user_id}_metadata.json")
            
            if not os.path.exists(index_path) or not os.path.exists(metadata_path):
                return None, []
            
            # Load FAISS index
            index = faiss.read_index(index_path)
            
            # Load metadata
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            return index, metadata
            
        except Exception as e:
            logger.error("Error loading user index", error=str(e), user_id=user_id)
            return None, []
    
    @staticmethod
    async def _vector_search(
        query_vector: np.ndarray,
        index: faiss.Index,
        metadata: List[Dict],
        top_k: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Perform vector search using FAISS"""
        try:
            # Perform similarity search
            scores, indices = index.search(
                np.array([query_vector.astype("float32")]), top_k
            )
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= len(metadata) or idx < 0:
                    continue
                
                meta = metadata[idx]
                
                # Apply filters if provided
                if filters and not SearchService._apply_filters(meta, filters):
                    continue
                
                # Calculate similarity score (convert distance to similarity)
                similarity_score = 1 / (1 + score) if score >= 0 else 0
                
                # Create search result
                result = SearchResult(
                    content=meta.get("content", ""),
                    source=meta.get("parent_doc_id", "unknown"),
                    content_type=ContentType(meta.get("content_type", "text")),
                    similarity_score=float(similarity_score),
                    page=meta.get("page"),
                    metadata={
                        "doc_id": meta.get("doc_id"),
                        "preview_path": meta.get("preview_path")
                    },
                    preview_url=SearchService._get_preview_url(meta)
                )
                
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error("Vector search error", error=str(e))
            return []
    
    @staticmethod
    def _apply_filters(metadata: Dict, filters: Dict[str, Any]) -> bool:
        """Apply search filters to metadata"""
        try:
            for key, value in filters.items():
                if key in metadata:
                    if isinstance(value, list):
                        if metadata[key] not in value:
                            return False
                    else:
                        if metadata[key] != value:
                            return False
            return True
        except Exception:
            return True
    
    @staticmethod
    def _get_preview_url(metadata: Dict) -> Optional[str]:
        """Generate preview URL for content"""
        preview_path = metadata.get("preview_path")
        if preview_path and os.path.exists(preview_path):
            # Convert to relative URL for API access
            relative_path = os.path.relpath(preview_path, settings.DATA_VOLUME_PATH)
            return f"/api/previews/{relative_path}"
        return None
    
    @staticmethod
    async def _generate_answer(query: str, search_results: List[SearchResult]) -> Optional[str]:
        """Generate AI answer using the best search result"""
        try:
            if not search_results:
                return None
            
            # Use the best result for answer generation
            best_result = search_results[0]
            
            if best_result.content_type == ContentType.IMAGE:
                # Load image for multimodal answer
                preview_path = best_result.metadata.get("preview_path")
                if preview_path and os.path.exists(preview_path):
                    image = Image.open(preview_path)
                    answer = answer_with_gemini(query, image)
                else:
                    answer = "Unable to process image for answer generation."
            else:
                # Use text content
                answer = answer_with_gemini(query, best_result.content)
            
            return answer
            
        except Exception as e:
            logger.error("Error generating answer", error=str(e), query=query)
            return f"Error generating answer: {str(e)}"
    
    @staticmethod
    async def batch_search(
        queries: List[str],
        user_id: str,
        options: Dict[str, Any]
    ) -> List[SearchResponse]:
        """Perform batch search operations"""
        try:
            results = []
            for query in queries:
                result = await SearchService.search(
                    query=query,
                    user_id=user_id,
                    top_k=options.get("top_k", 5),
                    include_answer=options.get("include_answer", True),
                    filters=options.get("filters", {})
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error("Batch search error", error=str(e), user_id=user_id)
            return []
    
    @staticmethod
    async def cleanup():
        """Cleanup search service"""
        logger.info("Search service cleanup completed")
