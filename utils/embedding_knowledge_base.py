"""
Embedding-Enhanced Knowledge Base for Royal Enfield Chatbot
Uses Amazon Titan Text Embeddings V3 for semantic search
"""

import json
import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from utils.s3_manager import S3StorageManager
from config.settings import Config

logger = logging.getLogger(__name__)

class EmbeddingKnowledgeBase:
    """
    Knowledge base with embedding-based semantic search using Titan Text Embeddings V3
    """
    
    def __init__(self):
        """Initialize embedding-enhanced knowledge base"""
        self.storage_manager = S3StorageManager()
        
        # Initialize Bedrock client for embeddings
        self.bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=Config.AWS_REGION,
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY
        )
        
        # Titan Text Embeddings V3 model
        self.embedding_model_id = "amazon.titan-embed-text-v3:0"
        
        # Cache for loaded chunks and embeddings
        self._chunks_cache = None
        self._embeddings_cache = None
        self._cache_timestamp = None
        
        # Embedding configuration
        self.embedding_dimension = 1024  # Titan Text Embeddings V3 dimension
        self.similarity_threshold = 0.7
    
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
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for text using Titan Text Embeddings V3
        
        Args:
            text: Text to embed
            
        Returns:
            Optional[List[float]]: Embedding vector or None if failed
        """
        try:
            # Prepare the request body
            body = {
                "inputText": text,
                "dimensions": self.embedding_dimension,
                "normalize": True
            }
            
            # Call Bedrock to generate embedding
            response = self.bedrock_client.invoke_model(
                modelId=self.embedding_model_id,
                body=json.dumps(body),
                contentType='application/json'
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            embedding = response_body.get('embedding')
            
            if embedding and len(embedding) == self.embedding_dimension:
                return embedding
            else:
                logger.error(f"Invalid embedding response: expected {self.embedding_dimension} dimensions")
                return None
                
        except ClientError as e:
            logger.error(f"Bedrock embedding generation failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            return None
    
    def get_all_chunks_with_embeddings(self) -> Tuple[List[Dict[str, Any]], List[List[float]]]:
        """
        Get all chunks from S3 with their embeddings
        
        Returns:
            Tuple[List[Dict[str, Any]], List[List[float]]]: Chunks and their embeddings
        """
        try:
            # Use cache if available and recent
            if (self._chunks_cache is not None and 
                self._embeddings_cache is not None and
                self._cache_timestamp is not None and 
                (datetime.now() - self._cache_timestamp).seconds < 300):  # 5 minute cache
                return self._chunks_cache, self._embeddings_cache
            
            chunks = []
            embeddings = []
            chunk_objects = self.storage_manager.list_processed_chunks()
            
            logger.info(f"Loading {len(chunk_objects)} chunks with embeddings from S3...")
            
            for chunk_obj in chunk_objects:
                if chunk_obj['key'].endswith('.json'):
                    try:
                        chunk_content = self.storage_manager.get_object_content(chunk_obj['key'])
                        chunk_data = json.loads(chunk_content)
                        
                        # Check if embedding already exists
                        if 'embedding' in chunk_data:
                            embedding = chunk_data['embedding']
                        else:
                            # Generate embedding for chunk content
                            content = chunk_data.get('content', '')
                            embedding = self.generate_embedding(content)
                            
                            if embedding:
                                # Store embedding back to S3
                                chunk_data['embedding'] = embedding
                                updated_content = json.dumps(chunk_data, indent=2)
                                self.storage_manager.upload_content(
                                    content=updated_content,
                                    s3_key=chunk_obj['key'],
                                    content_type='application/json'
                                )
                                logger.info(f"Generated and stored embedding for chunk: {chunk_data.get('chunk_id')}")
                        
                        if embedding:
                            chunks.append(chunk_data)
                            embeddings.append(embedding)
                        else:
                            logger.warning(f"No embedding available for chunk: {chunk_obj['key']}")
                            
                    except Exception as e:
                        logger.warning(f"Could not load chunk {chunk_obj['key']}: {e}")
                        continue
            
            # Sort chunks by chunk_index
            sorted_data = sorted(zip(chunks, embeddings), 
                               key=lambda x: x[0].get('metadata', {}).get('chunk_index', 0))
            chunks, embeddings = zip(*sorted_data) if sorted_data else ([], [])
            
            chunks = list(chunks)
            embeddings = list(embeddings)
            
            # Update cache
            self._chunks_cache = chunks
            self._embeddings_cache = embeddings
            self._cache_timestamp = datetime.now()
            
            logger.info(f"Successfully loaded {len(chunks)} chunks with embeddings from S3")
            return chunks, embeddings
            
        except Exception as e:
            logger.error(f"Failed to get chunks with embeddings from S3: {e}")
            return [], []
    
    def semantic_search(self, query: str, max_results: int = 5, 
                       similarity_threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Perform semantic search using embeddings
        
        Args:
            query: Search query
            max_results: Maximum number of results
            similarity_threshold: Minimum similarity score (0.0 to 1.0)
            
        Returns:
            List[Dict[str, Any]]: Relevant chunks with similarity scores
        """
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return self._fallback_keyword_search(query, max_results)
            
            # Get all chunks and embeddings
            chunks, chunk_embeddings = self.get_all_chunks_with_embeddings()
            if not chunks or not chunk_embeddings:
                logger.warning("No chunks with embeddings available for search")
                return []
            
            # Calculate cosine similarities
            query_vector = np.array(query_embedding)
            similarities = []
            
            for i, chunk_embedding in enumerate(chunk_embeddings):
                chunk_vector = np.array(chunk_embedding)
                
                # Cosine similarity
                dot_product = np.dot(query_vector, chunk_vector)
                norm_query = np.linalg.norm(query_vector)
                norm_chunk = np.linalg.norm(chunk_vector)
                
                if norm_query > 0 and norm_chunk > 0:
                    similarity = dot_product / (norm_query * norm_chunk)
                else:
                    similarity = 0.0
                
                similarities.append((i, similarity))
            
            # Filter by threshold
            threshold = similarity_threshold or self.similarity_threshold
            filtered_similarities = [(i, sim) for i, sim in similarities if sim >= threshold]
            
            # Sort by similarity score
            filtered_similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Prepare results
            results = []
            for i, similarity in filtered_similarities[:max_results]:
                chunk = chunks[i].copy()
                chunk['similarity_score'] = float(similarity)
                chunk['search_method'] = 'semantic'
                results.append(chunk)
            
            logger.info(f"Semantic search found {len(results)} relevant chunks for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return self._fallback_keyword_search(query, max_results)
    
    def hybrid_search(self, query: str, max_results: int = 5, 
                     semantic_weight: float = 0.7) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining semantic and keyword search
        
        Args:
            query: Search query
            max_results: Maximum number of results
            semantic_weight: Weight for semantic search (0.0 to 1.0)
            
        Returns:
            List[Dict[str, Any]]: Relevant chunks with combined scores
        """
        try:
            # Get semantic search results
            semantic_results = self.semantic_search(query, max_results * 2, 0.5)
            
            # Get keyword search results
            keyword_results = self._fallback_keyword_search(query, max_results * 2)
            
            # Combine and re-rank results
            combined_results = {}
            
            # Add semantic results
            for result in semantic_results:
                chunk_id = result.get('chunk_id')
                if chunk_id:
                    combined_results[chunk_id] = result.copy()
                    combined_results[chunk_id]['semantic_score'] = result.get('similarity_score', 0.0)
                    combined_results[chunk_id]['keyword_score'] = 0.0
            
            # Add keyword results
            for result in keyword_results:
                chunk_id = result.get('chunk_id')
                if chunk_id:
                    if chunk_id in combined_results:
                        combined_results[chunk_id]['keyword_score'] = result.get('relevance_score', 0.0)
                    else:
                        combined_results[chunk_id] = result.copy()
                        combined_results[chunk_id]['semantic_score'] = 0.0
                        combined_results[chunk_id]['keyword_score'] = result.get('relevance_score', 0.0)
            
            # Calculate hybrid scores
            for chunk_id, result in combined_results.items():
                semantic_score = result.get('semantic_score', 0.0)
                keyword_score = result.get('keyword_score', 0.0)
                
                # Normalize keyword score to 0-1 range
                normalized_keyword_score = min(keyword_score, 1.0)
                
                # Calculate weighted hybrid score
                hybrid_score = (semantic_weight * semantic_score + 
                              (1 - semantic_weight) * normalized_keyword_score)
                
                result['hybrid_score'] = hybrid_score
                result['search_method'] = 'hybrid'
            
            # Sort by hybrid score and return top results
            sorted_results = sorted(combined_results.values(), 
                                  key=lambda x: x['hybrid_score'], reverse=True)
            
            logger.info(f"Hybrid search found {len(sorted_results)} relevant chunks for query: {query}")
            return sorted_results[:max_results]
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return self._fallback_keyword_search(query, max_results)
    
    def _fallback_keyword_search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Fallback keyword-based search when embeddings are not available
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List[Dict[str, Any]]: Relevant chunks with scores
        """
        try:
            chunks, _ = self.get_all_chunks_with_embeddings()
            if not chunks:
                logger.warning("No chunks available for fallback search")
                return []
            
            query_lower = query.lower()
            scored_chunks = []
            
            for chunk in chunks:
                content = chunk.get('content', '').lower()
                score = self._calculate_keyword_relevance_score(query_lower, content)
                
                if score > 0:
                    chunk_with_score = chunk.copy()
                    chunk_with_score['relevance_score'] = score
                    chunk_with_score['search_method'] = 'keyword'
                    scored_chunks.append(chunk_with_score)
            
            # Sort by relevance score
            scored_chunks.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            logger.info(f"Keyword search found {len(scored_chunks)} relevant chunks for query: {query}")
            return scored_chunks[:max_results]
            
        except Exception as e:
            logger.error(f"Fallback keyword search failed: {e}")
            return []
    
    def _calculate_keyword_relevance_score(self, query: str, content: str) -> float:
        """
        Calculate keyword-based relevance score between query and content
        
        Args:
            query: Search query (lowercase)
            content: Content to search (lowercase)
            
        Returns:
            float: Relevance score (0.0 to 1.0+)
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
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the embedding knowledge base
        
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
                    'pages': [],
                    'embeddings_available': False
                }
            
            metadata_content = self.storage_manager.get_object_content(metadata_key)
            doc_metadata = json.loads(metadata_content)
            
            # Get current chunks and embeddings
            chunks, embeddings = self.get_all_chunks_with_embeddings()
            
            if not chunks:
                return {
                    'ready': False,
                    'total_chunks': 0,
                    'total_words': 0,
                    'sections': [],
                    'pages': [],
                    'embeddings_available': False,
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
                'total_embeddings': len(embeddings),
                'total_words': total_words,
                'sections': sorted(list(sections)),
                'pages': sorted(list(pages)),
                'embeddings_available': len(embeddings) > 0,
                'embedding_model': self.embedding_model_id,
                'embedding_dimension': self.embedding_dimension,
                'document_metadata': doc_metadata,
                'storage_stats': storage_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get embedding KB stats: {e}")
            return {
                'ready': False,
                'error': str(e),
                'embeddings_available': False
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
            chunks, _ = self.get_all_chunks_with_embeddings()
            section_chunks = [
                chunk for chunk in chunks
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
            chunks, _ = self.get_all_chunks_with_embeddings()
            page_chunks = [
                chunk for chunk in chunks
                if page_number in chunk.get('metadata', {}).get('page_numbers', [])
            ]
            
            return page_chunks
            
        except Exception as e:
            logger.error(f"Failed to get chunks by page: {e}")
            return []
    
    def clear_cache(self) -> None:
        """Clear the chunks and embeddings cache"""
        self._chunks_cache = None
        self._embeddings_cache = None
        self._cache_timestamp = None
        logger.info("Embedding knowledge base cache cleared")
    
    def get_embedding_health_status(self) -> Dict[str, Any]:
        """
        Get embedding system health status
        
        Returns:
            Dict[str, Any]: Health status including embedding capabilities
        """
        try:
            # Test embedding generation
            test_embedding = self.generate_embedding("test text")
            embedding_healthy = test_embedding is not None
            
            # Get knowledge base stats
            kb_stats = self.get_knowledge_base_stats()
            
            # Get S3 health
            s3_health = self.storage_manager.get_health_status()
            
            return {
                'healthy': embedding_healthy and s3_health['healthy'] and kb_stats['ready'],
                'embedding_service': {
                    'available': embedding_healthy,
                    'model_id': self.embedding_model_id,
                    'dimension': self.embedding_dimension
                },
                's3_connection': s3_health['connection'],
                's3_storage': s3_health['storage'],
                'knowledge_base': kb_stats,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get embedding health status: {e}")
            return {
                'healthy': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }