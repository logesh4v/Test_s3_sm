"""
Content Retrieval Manager for Royal Enfield Knowledge Base
Handles content retrieval, caching, and search operations
"""

import json
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from .s3_manager import S3StorageManager

logger = logging.getLogger(__name__)

class ContentRetriever:
    """
    Manages content retrieval and caching for the knowledge base
    """
    
    def __init__(self, cache_ttl: int = 3600):
        """
        Initialize content retriever
        
        Args:
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
        """
        self.storage_manager = S3StorageManager()
        self.cache = {}
        self.cache_ttl = cache_ttl
    
    def get_document_content(self, document_key: str, use_cache: bool = True) -> Optional[bytes]:
        """
        Retrieve document content from S3
        
        Args:
            document_key: S3 key of the document
            use_cache: Whether to use caching
            
        Returns:
            Optional[bytes]: Document content as bytes
        """
        try:
            cache_key = f"doc_content_{document_key}"
            
            # Check cache first
            if use_cache and self._is_cached(cache_key):
                logger.info(f"Retrieved document from cache: {document_key}")
                return self.cache[cache_key]['data']
            
            # Download from S3
            response = self.storage_manager.s3_client.s3_client.get_object(
                Bucket=self.storage_manager.s3_client.bucket_name,
                Key=document_key
            )
            content = response['Body'].read()
            
            # Cache the content
            if use_cache:
                self._cache_data(cache_key, content)
            
            logger.info(f"Retrieved document from S3: {document_key}")
            return content
            
        except Exception as e:
            logger.error(f"Failed to retrieve document content: {e}")
            return None
    
    def get_document_chunks(self, document_name: str, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Retrieve all processed chunks for a document
        
        Args:
            document_name: Name of the document
            use_cache: Whether to use caching
            
        Returns:
            List[Dict[str, Any]]: List of document chunks
        """
        try:
            cache_key = f"chunks_{document_name}"
            
            # Check cache first
            if use_cache and self._is_cached(cache_key):
                logger.info(f"Retrieved chunks from cache: {document_name}")
                return self.cache[cache_key]['data']
            
            # Get chunks from S3
            chunks = []
            chunk_objects = self.storage_manager.list_processed_chunks()
            
            for chunk_obj in chunk_objects:
                if document_name in chunk_obj['key'] and chunk_obj['key'].endswith('.json'):
                    try:
                        chunk_content = self.storage_manager.get_object_content(chunk_obj['key'])
                        chunk_data = json.loads(chunk_content)
                        chunks.append(chunk_data)
                    except Exception as e:
                        logger.warning(f"Could not load chunk {chunk_obj['key']}: {e}")
                        continue
            
            # Sort chunks by chunk_id or page_number
            chunks.sort(key=lambda x: (
                x.get('metadata', {}).get('page_number', 0),
                x.get('chunk_id', '')
            ))
            
            # Cache the chunks
            if use_cache:
                self._cache_data(cache_key, chunks)
            
            logger.info(f"Retrieved {len(chunks)} chunks for document: {document_name}")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to retrieve document chunks: {e}")
            return []
    
    def search_chunks(self, query: str, document_name: Optional[str] = None, 
                     max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search through document chunks for relevant content
        
        Args:
            query: Search query
            document_name: Optional specific document to search
            max_results: Maximum number of results to return
            
        Returns:
            List[Dict[str, Any]]: Relevant chunks with relevance scores
        """
        try:
            # Get all chunks or chunks for specific document
            if document_name:
                all_chunks = self.get_document_chunks(document_name)
            else:
                all_chunks = self._get_all_chunks()
            
            if not all_chunks:
                return []
            
            # Simple text-based search (can be enhanced with embeddings later)
            query_lower = query.lower()
            scored_chunks = []
            
            for chunk in all_chunks:
                content = chunk.get('content', '').lower()
                relevance_score = self._calculate_relevance_score(query_lower, content)
                
                if relevance_score > 0:
                    chunk_with_score = chunk.copy()
                    chunk_with_score['relevance_score'] = relevance_score
                    scored_chunks.append(chunk_with_score)
            
            # Sort by relevance score (descending)
            scored_chunks.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # Return top results
            results = scored_chunks[:max_results]
            logger.info(f"Found {len(results)} relevant chunks for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search chunks: {e}")
            return []
    
    def _calculate_relevance_score(self, query: str, content: str) -> float:
        """
        Calculate relevance score between query and content
        
        Args:
            query: Search query (lowercase)
            content: Content to search (lowercase)
            
        Returns:
            float: Relevance score (0.0 to 1.0)
        """
        if not query or not content:
            return 0.0
        
        # Split query into terms
        query_terms = query.split()
        if not query_terms:
            return 0.0
        
        # Calculate term frequency and position bonuses
        score = 0.0
        content_words = content.split()
        
        for term in query_terms:
            # Exact phrase match gets highest score
            if term in content:
                score += 0.5
                
                # Bonus for multiple occurrences
                occurrences = content.count(term)
                score += min(occurrences * 0.1, 0.3)
                
                # Bonus for term appearing early in content
                try:
                    first_occurrence = content.index(term)
                    position_bonus = max(0, 0.2 - (first_occurrence / len(content)) * 0.2)
                    score += position_bonus
                except ValueError:
                    pass
        
        # Normalize score
        max_possible_score = len(query_terms) * 1.0
        normalized_score = min(score / max_possible_score, 1.0) if max_possible_score > 0 else 0.0
        
        return normalized_score
    
    def _get_all_chunks(self) -> List[Dict[str, Any]]:
        """
        Get all chunks from all documents
        
        Returns:
            List[Dict[str, Any]]: All available chunks
        """
        try:
            cache_key = "all_chunks"
            
            # Check cache first
            if self._is_cached(cache_key):
                return self.cache[cache_key]['data']
            
            # Get all chunk objects
            all_chunks = []
            chunk_objects = self.storage_manager.list_processed_chunks()
            
            for chunk_obj in chunk_objects:
                if chunk_obj['key'].endswith('.json'):
                    try:
                        chunk_content = self.storage_manager.get_object_content(chunk_obj['key'])
                        chunk_data = json.loads(chunk_content)
                        all_chunks.append(chunk_data)
                    except Exception as e:
                        logger.warning(f"Could not load chunk {chunk_obj['key']}: {e}")
                        continue
            
            # Cache all chunks
            self._cache_data(cache_key, all_chunks)
            
            return all_chunks
            
        except Exception as e:
            logger.error(f"Failed to get all chunks: {e}")
            return []
    
    def get_chunk_by_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific chunk by its ID
        
        Args:
            chunk_id: ID of the chunk to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Chunk data if found
        """
        try:
            # Search through all chunks for the specific ID
            all_chunks = self._get_all_chunks()
            
            for chunk in all_chunks:
                if chunk.get('chunk_id') == chunk_id:
                    return chunk
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get chunk by ID: {e}")
            return None
    
    def get_chunks_by_page(self, document_name: str, page_number: int) -> List[Dict[str, Any]]:
        """
        Get all chunks from a specific page of a document
        
        Args:
            document_name: Name of the document
            page_number: Page number to retrieve
            
        Returns:
            List[Dict[str, Any]]: Chunks from the specified page
        """
        try:
            document_chunks = self.get_document_chunks(document_name)
            
            page_chunks = [
                chunk for chunk in document_chunks
                if chunk.get('metadata', {}).get('page_number') == page_number
            ]
            
            return page_chunks
            
        except Exception as e:
            logger.error(f"Failed to get chunks by page: {e}")
            return []
    
    def get_chunks_by_section(self, document_name: str, section: str) -> List[Dict[str, Any]]:
        """
        Get all chunks from a specific section of a document
        
        Args:
            document_name: Name of the document
            section: Section name to retrieve
            
        Returns:
            List[Dict[str, Any]]: Chunks from the specified section
        """
        try:
            document_chunks = self.get_document_chunks(document_name)
            
            section_chunks = [
                chunk for chunk in document_chunks
                if section.lower() in chunk.get('metadata', {}).get('section', '').lower()
            ]
            
            return section_chunks
            
        except Exception as e:
            logger.error(f"Failed to get chunks by section: {e}")
            return []
    
    def _is_cached(self, cache_key: str) -> bool:
        """
        Check if data is cached and not expired
        
        Args:
            cache_key: Key to check in cache
            
        Returns:
            bool: True if cached and not expired
        """
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key]['timestamp']
        current_time = time.time()
        
        return (current_time - cached_time) < self.cache_ttl
    
    def _cache_data(self, cache_key: str, data: Any) -> None:
        """
        Cache data with timestamp
        
        Args:
            cache_key: Key for caching
            data: Data to cache
        """
        self.cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }
    
    def clear_cache(self) -> None:
        """Clear all cached data"""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dict[str, Any]: Cache statistics
        """
        current_time = time.time()
        valid_entries = 0
        expired_entries = 0
        
        for cache_key, cache_data in self.cache.items():
            if (current_time - cache_data['timestamp']) < self.cache_ttl:
                valid_entries += 1
            else:
                expired_entries += 1
        
        return {
            'total_entries': len(self.cache),
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'cache_ttl': self.cache_ttl
        }
    
    def cleanup_expired_cache(self) -> int:
        """
        Remove expired entries from cache
        
        Returns:
            int: Number of entries removed
        """
        current_time = time.time()
        expired_keys = []
        
        for cache_key, cache_data in self.cache.items():
            if (current_time - cache_data['timestamp']) >= self.cache_ttl:
                expired_keys.append(cache_key)
        
        for key in expired_keys:
            del self.cache[key]
        
        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        return len(expired_keys)