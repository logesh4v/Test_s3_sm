"""
S3-Only Knowledge Base for Royal Enfield Chatbot
Retrieves pre-processed knowledge base data directly from S3
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from utils.s3_manager import S3StorageManager

logger = logging.getLogger(__name__)

class S3OnlyKnowledgeBase:
    """
    Knowledge base that retrieves pre-processed data directly from S3
    Assumes all data is already processed and stored in S3
    """
    
    def __init__(self):
        """Initialize S3-only knowledge base"""
        self.storage_manager = S3StorageManager()
        
        # Cache for loaded chunks
        self._chunks_cache = None
        self._cache_timestamp = None
    
    def is_knowledge_base_ready(self) -> bool:
        """
        Check if knowledge base data exists in S3
        
        Returns:
            bool: True if knowledge base data is available in S3
        """
        try:
            # Check if metadata exists in S3
            metadata_key = "processed/metadata/document_metadata.json"
            if not self.storage_manager.object_exists(metadata_key):
                return False
            
            # Check if chunks exist
            chunk_objects = self.storage_manager.list_processed_chunks()
            
            return len(chunk_objects) > 0
            
        except Exception as e:
            logger.error(f"Error checking S3 knowledge base status: {e}")
            return False
    
    def get_all_chunks(self) -> List[Dict[str, Any]]:
        """
        Get all chunks from S3
        
        Returns:
            List[Dict[str, Any]]: All chunks from S3
        """
        try:
            # Use cache if available and recent
            if (self._chunks_cache is not None and 
                self._cache_timestamp is not None and 
                (datetime.now() - self._cache_timestamp).seconds < 300):  # 5 minute cache
                return self._chunks_cache
            
            chunks = []
            chunk_objects = self.storage_manager.list_processed_chunks()
            
            logger.info(f"Loading {len(chunk_objects)} chunks from S3...")
            
            for chunk_obj in chunk_objects:
                if chunk_obj['key'].endswith('.json'):
                    try:
                        chunk_content = self.storage_manager.get_object_content(chunk_obj['key'])
                        chunk_data = json.loads(chunk_content)
                        chunks.append(chunk_data)
                    except Exception as e:
                        logger.warning(f"Could not load chunk {chunk_obj['key']}: {e}")
                        continue
            
            # Sort chunks by chunk_index
            chunks.sort(key=lambda x: x.get('metadata', {}).get('chunk_index', 0))
            
            # Update cache
            self._chunks_cache = chunks
            self._cache_timestamp = datetime.now()
            
            logger.info(f"Successfully loaded {len(chunks)} chunks from S3")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to get chunks from S3: {e}")
            return []
    
    def search_chunks(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search chunks for relevant content
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List[Dict[str, Any]]: Relevant chunks with scores
        """
        try:
            all_chunks = self.get_all_chunks()
            if not all_chunks:
                logger.warning("No chunks available for search")
                return []
            
            query_lower = query.lower()
            scored_chunks = []
            
            for chunk in all_chunks:
                content = chunk.get('content', '').lower()
                score = self._calculate_relevance_score(query_lower, content)
                
                if score > 0:
                    chunk_with_score = chunk.copy()
                    chunk_with_score['relevance_score'] = score
                    scored_chunks.append(chunk_with_score)
            
            # Sort by relevance score
            scored_chunks.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            logger.info(f"Found {len(scored_chunks)} relevant chunks for query: {query}")
            return scored_chunks[:max_results]
            
        except Exception as e:
            logger.error(f"S3 search failed: {e}")
            return []
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the S3 knowledge base
        
        Returns:
            Dict[str, Any]: Knowledge base statistics
        """
        try:
            # Get document metadata from S3
            metadata_key = "processed/metadata/document_metadata.json"
            
            if not self.storage_manager.object_exists(metadata_key):
                return {
                    'ready': False,
                    'total_chunks': 0,
                    'total_words': 0,
                    'sections': [],
                    'pages': []
                }
            
            metadata_content = self.storage_manager.get_object_content(metadata_key)
            doc_metadata = json.loads(metadata_content)
            
            # Get current chunks
            chunks = self.get_all_chunks()
            
            if not chunks:
                return {
                    'ready': False,
                    'total_chunks': 0,
                    'total_words': 0,
                    'sections': [],
                    'pages': [],
                    'document_metadata': doc_metadata
                }
            
            # Calculate current statistics
            total_words = sum(chunk.get('metadata', {}).get('word_count', 0) for chunk in chunks)
            sections = set()
            pages = set()
            
            for chunk in chunks:
                metadata = chunk.get('metadata', {})
                if metadata.get('section'):
                    sections.add(metadata['section'])
                if metadata.get('page_numbers'):
                    pages.update(metadata['page_numbers'])
            
            # Get S3 storage stats
            storage_stats = self.storage_manager.get_storage_stats()
            
            return {
                'ready': True,
                'total_chunks': len(chunks),
                'total_words': total_words,
                'sections': sorted(list(sections)),
                'pages': sorted(list(pages)),
                'document_metadata': doc_metadata,
                'storage_stats': storage_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get S3 stats: {e}")
            return {
                'ready': False,
                'error': str(e)
            }
    
    def get_chunks_by_section(self, section_name: str) -> List[Dict[str, Any]]:
        """
        Get chunks from a specific section
        
        Args:
            section_name: Name of the section
            
        Returns:
            List[Dict[str, Any]]: Chunks from the section
        """
        try:
            all_chunks = self.get_all_chunks()
            section_chunks = [
                chunk for chunk in all_chunks
                if section_name.lower() in chunk.get('metadata', {}).get('section', '').lower()
            ]
            
            return section_chunks
            
        except Exception as e:
            logger.error(f"Failed to get chunks by section: {e}")
            return []
    
    def get_chunks_by_page(self, page_number: int) -> List[Dict[str, Any]]:
        """
        Get chunks from a specific page
        
        Args:
            page_number: Page number
            
        Returns:
            List[Dict[str, Any]]: Chunks from the page
        """
        try:
            all_chunks = self.get_all_chunks()
            page_chunks = [
                chunk for chunk in all_chunks
                if page_number in chunk.get('metadata', {}).get('page_numbers', [])
            ]
            
            return page_chunks
            
        except Exception as e:
            logger.error(f"Failed to get chunks by page: {e}")
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
        
        query_terms = query.split()
        score = 0.0
        
        for term in query_terms:
            if term in content:
                # Count occurrences
                occurrences = content.count(term)
                score += occurrences * 0.1
                
                # Bonus for exact phrase match
                if len(query_terms) > 1 and query in content:
                    score += 0.5
                
                # Position bonus (earlier = better)
                position = content.find(term)
                if position != -1:
                    position_bonus = max(0, 0.2 - (position / len(content)) * 0.2)
                    score += position_bonus
        
        # Normalize by query length
        return min(score / len(query_terms) if query_terms else 0, 1.0)
    
    def get_s3_health_status(self) -> Dict[str, Any]:
        """
        Get S3 connection and health status
        
        Returns:
            Dict[str, Any]: Health status
        """
        try:
            health_status = self.storage_manager.get_health_status()
            kb_stats = self.get_knowledge_base_stats()
            
            return {
                'healthy': health_status['healthy'] and kb_stats['ready'],
                's3_connection': health_status['connection'],
                's3_storage': health_status['storage'],
                'knowledge_base': kb_stats,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get S3 health status: {e}")
            return {
                'healthy': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def clear_cache(self) -> None:
        """Clear the chunks cache"""
        self._chunks_cache = None
        self._cache_timestamp = None
        logger.info("S3 knowledge base cache cleared")