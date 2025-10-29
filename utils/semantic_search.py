"""
Semantic Search Engine for Royal Enfield Knowledge Base
Implements intelligent search and ranking for document chunks
"""

import re
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from collections import Counter
import math
from utils.content_retriever import ContentRetriever

logger = logging.getLogger(__name__)

class SemanticSearchEngine:
    """
    Advanced search engine for finding relevant content chunks
    """
    
    def __init__(self):
        """Initialize semantic search engine"""
        self.content_retriever = ContentRetriever()
        self.stopwords = self._get_stopwords()
        
    def search(self, query: str, document_name: Optional[str] = None, 
              max_results: int = 5, min_score: float = 0.1) -> List[Dict[str, Any]]:
        """
        Perform semantic search across document chunks
        
        Args:
            query: Search query
            document_name: Optional specific document to search
            max_results: Maximum number of results to return
            min_score: Minimum relevance score threshold
            
        Returns:
            List[Dict[str, Any]]: Ranked search results with scores
        """
        try:
            logger.info(f"Performing search for query: '{query}'")
            
            # Get all relevant chunks
            if document_name:
                chunks = self.content_retriever.get_document_chunks(document_name)
            else:
                chunks = self.content_retriever._get_all_chunks()
            
            if not chunks:
                logger.warning("No chunks available for search")
                return []
            
            # Preprocess query
            processed_query = self._preprocess_text(query)
            query_terms = self._extract_terms(processed_query)
            
            if not query_terms:
                logger.warning("No valid search terms extracted from query")
                return []
            
            # Score all chunks
            scored_results = []
            for chunk in chunks:
                score = self._calculate_comprehensive_score(chunk, query, query_terms)
                
                if score >= min_score:
                    result = chunk.copy()
                    result['search_score'] = score
                    result['search_explanation'] = self._generate_score_explanation(chunk, query, query_terms, score)
                    scored_results.append(result)
            
            # Sort by score (descending) and return top results
            scored_results.sort(key=lambda x: x['search_score'], reverse=True)
            results = scored_results[:max_results]
            
            logger.info(f"Found {len(results)} relevant results for query")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def _calculate_comprehensive_score(self, chunk: Dict[str, Any], 
                                     original_query: str, query_terms: List[str]) -> float:
        """
        Calculate comprehensive relevance score using multiple factors
        
        Args:
            chunk: Document chunk to score
            original_query: Original search query
            query_terms: Processed query terms
            
        Returns:
            float: Comprehensive relevance score (0.0 to 1.0)
        """
        content = chunk.get('content', '').lower()
        metadata = chunk.get('metadata', {})
        
        # Component scores
        term_frequency_score = self._calculate_term_frequency_score(content, query_terms)
        phrase_match_score = self._calculate_phrase_match_score(content, original_query)
        position_score = self._calculate_position_score(content, query_terms)
        metadata_score = self._calculate_metadata_score(metadata, query_terms)
        content_type_score = self._calculate_content_type_score(metadata, original_query)
        
        # Weighted combination
        weights = {
            'term_frequency': 0.3,
            'phrase_match': 0.25,
            'position': 0.15,
            'metadata': 0.15,
            'content_type': 0.15
        }
        
        total_score = (
            weights['term_frequency'] * term_frequency_score +
            weights['phrase_match'] * phrase_match_score +
            weights['position'] * position_score +
            weights['metadata'] * metadata_score +
            weights['content_type'] * content_type_score
        )
        
        return min(total_score, 1.0)
    
    def _calculate_term_frequency_score(self, content: str, query_terms: List[str]) -> float:
        """Calculate TF-IDF style score for query terms"""
        if not query_terms:
            return 0.0
        
        content_terms = self._extract_terms(content)
        content_term_count = Counter(content_terms)
        total_terms = len(content_terms)
        
        if total_terms == 0:
            return 0.0
        
        score = 0.0
        for term in query_terms:
            if term in content_term_count:
                # Term frequency
                tf = content_term_count[term] / total_terms
                # Simple IDF approximation (can be enhanced with corpus statistics)
                idf = math.log(1 + (1 / max(tf, 0.001)))
                score += tf * idf
        
        # Normalize by query length
        return min(score / len(query_terms), 1.0)
    
    def _calculate_phrase_match_score(self, content: str, query: str) -> float:
        """Calculate score for exact phrase matches"""
        query_lower = query.lower().strip()
        content_lower = content.lower()
        
        if not query_lower:
            return 0.0
        
        # Exact phrase match
        if query_lower in content_lower:
            # Bonus for exact match
            base_score = 0.8
            
            # Additional bonus for multiple occurrences
            occurrences = content_lower.count(query_lower)
            occurrence_bonus = min(occurrences * 0.1, 0.2)
            
            return min(base_score + occurrence_bonus, 1.0)
        
        # Partial phrase matching
        query_words = query_lower.split()
        if len(query_words) > 1:
            # Check for consecutive word matches
            consecutive_matches = 0
            max_consecutive = 0
            
            content_words = content_lower.split()
            for i in range(len(content_words) - len(query_words) + 1):
                matches = 0
                for j, query_word in enumerate(query_words):
                    if i + j < len(content_words) and content_words[i + j] == query_word:
                        matches += 1
                    else:
                        break
                
                if matches > max_consecutive:
                    max_consecutive = matches
            
            if max_consecutive > 1:
                return (max_consecutive / len(query_words)) * 0.6
        
        return 0.0
    
    def _calculate_position_score(self, content: str, query_terms: List[str]) -> float:
        """Calculate score based on term positions (earlier = better)"""
        if not query_terms:
            return 0.0
        
        content_lower = content.lower()
        content_length = len(content_lower)
        
        if content_length == 0:
            return 0.0
        
        position_scores = []
        for term in query_terms:
            position = content_lower.find(term)
            if position != -1:
                # Earlier positions get higher scores
                position_score = 1.0 - (position / content_length)
                position_scores.append(position_score)
        
        if position_scores:
            return sum(position_scores) / len(position_scores)
        
        return 0.0
    
    def _calculate_metadata_score(self, metadata: Dict[str, Any], query_terms: List[str]) -> float:
        """Calculate score based on metadata matches"""
        if not query_terms:
            return 0.0
        
        score = 0.0
        
        # Check section title
        section = metadata.get('section', '').lower()
        for term in query_terms:
            if term in section:
                score += 0.3
        
        # Check topics
        topics = metadata.get('topics', [])
        for topic in topics:
            topic_lower = str(topic).lower()
            for term in query_terms:
                if term in topic_lower:
                    score += 0.2
        
        # Check chunk type relevance
        chunk_type = metadata.get('chunk_type', '')
        type_relevance = self._get_type_relevance(chunk_type, query_terms)
        score += type_relevance * 0.1
        
        return min(score, 1.0)
    
    def _calculate_content_type_score(self, metadata: Dict[str, Any], query: str) -> float:
        """Calculate score based on content type relevance to query"""
        chunk_type = metadata.get('chunk_type', 'general')
        query_lower = query.lower()
        
        # Define query type patterns
        type_patterns = {
            'maintenance': ['maintain', 'service', 'repair', 'replace', 'check', 'inspect', 'oil', 'filter'],
            'troubleshooting': ['problem', 'issue', 'trouble', 'fix', 'solve', 'error', 'fault', 'diagnose'],
            'specifications': ['spec', 'dimension', 'weight', 'capacity', 'size', 'measurement', 'technical'],
            'safety': ['safety', 'warning', 'caution', 'danger', 'risk', 'hazard', 'protect'],
            'procedures': ['how', 'step', 'procedure', 'process', 'method', 'instruction', 'guide']
        }
        
        # Calculate query type scores
        query_type_scores = {}
        for content_type, patterns in type_patterns.items():
            score = sum(1 for pattern in patterns if pattern in query_lower)
            query_type_scores[content_type] = score / len(patterns)
        
        # Get the most likely query type
        best_query_type = max(query_type_scores, key=query_type_scores.get)
        best_score = query_type_scores[best_query_type]
        
        # Bonus if chunk type matches query type
        if chunk_type == best_query_type and best_score > 0.1:
            return 0.8
        elif chunk_type in query_type_scores and query_type_scores[chunk_type] > 0.05:
            return 0.4
        
        return 0.0
    
    def _get_type_relevance(self, chunk_type: str, query_terms: List[str]) -> float:
        """Get relevance score for chunk type"""
        type_keywords = {
            'maintenance': ['maintenance', 'service', 'oil', 'filter', 'replace'],
            'troubleshooting': ['problem', 'trouble', 'issue', 'fix', 'repair'],
            'specifications': ['spec', 'specification', 'dimension', 'weight'],
            'safety': ['safety', 'warning', 'caution', 'danger'],
            'procedures': ['procedure', 'step', 'instruction', 'guide']
        }
        
        if chunk_type in type_keywords:
            keywords = type_keywords[chunk_type]
            matches = sum(1 for term in query_terms if term in keywords)
            return matches / len(keywords) if keywords else 0.0
        
        return 0.0
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for search"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep spaces and hyphens
        text = re.sub(r'[^\w\s\-]', ' ', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _extract_terms(self, text: str) -> List[str]:
        """Extract search terms from text"""
        if not text:
            return []
        
        # Split into words
        words = text.split()
        
        # Filter out stopwords and short words
        terms = [
            word for word in words 
            if len(word) > 2 and word not in self.stopwords
        ]
        
        return terms
    
    def _get_stopwords(self) -> set:
        """Get common English stopwords"""
        return {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'you', 'your', 'this', 'these',
            'they', 'them', 'their', 'have', 'had', 'can', 'could', 'should',
            'would', 'may', 'might', 'must', 'shall', 'do', 'does', 'did'
        }
    
    def _generate_score_explanation(self, chunk: Dict[str, Any], query: str, 
                                  query_terms: List[str], total_score: float) -> Dict[str, Any]:
        """Generate explanation for the search score"""
        content = chunk.get('content', '').lower()
        metadata = chunk.get('metadata', {})
        
        explanation = {
            'total_score': round(total_score, 3),
            'factors': {
                'term_matches': [],
                'phrase_matches': [],
                'section_relevance': metadata.get('section', ''),
                'content_type': metadata.get('chunk_type', 'general'),
                'page_numbers': metadata.get('page_numbers', [])
            }
        }
        
        # Find term matches
        for term in query_terms:
            if term in content:
                count = content.count(term)
                explanation['factors']['term_matches'].append({
                    'term': term,
                    'occurrences': count
                })
        
        # Check for phrase matches
        if query.lower() in content:
            explanation['factors']['phrase_matches'].append({
                'phrase': query,
                'exact_match': True
            })
        
        return explanation
    
    def get_search_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        """
        Get search suggestions based on partial query
        
        Args:
            partial_query: Partial search query
            limit: Maximum number of suggestions
            
        Returns:
            List[str]: Search suggestions
        """
        try:
            # Get common terms from all chunks
            all_chunks = self.content_retriever._get_all_chunks()
            
            # Extract common terms and topics
            all_terms = set()
            for chunk in all_chunks:
                content = chunk.get('content', '')
                terms = self._extract_terms(self._preprocess_text(content))
                all_terms.update(terms)
                
                # Add topics
                topics = chunk.get('metadata', {}).get('topics', [])
                all_terms.update([str(topic).lower() for topic in topics])
            
            # Filter suggestions based on partial query
            partial_lower = partial_query.lower()
            suggestions = [
                term for term in all_terms 
                if term.startswith(partial_lower) and len(term) > len(partial_lower)
            ]
            
            # Sort by length (shorter suggestions first)
            suggestions.sort(key=len)
            
            return suggestions[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get search suggestions: {e}")
            return []