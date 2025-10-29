"""
Context Aggregation and Response Preparation for Royal Enfield Knowledge Base
Combines multiple chunks into coherent context and prepares responses with citations
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class ContextAggregator:
    """
    Aggregates search results into coherent context for response generation
    """
    
    def __init__(self, max_context_length: int = 4000):
        """
        Initialize context aggregator
        
        Args:
            max_context_length: Maximum length of aggregated context
        """
        self.max_context_length = max_context_length
    
    def aggregate_search_results(self, search_results: List[Dict[str, Any]], 
                                query: str) -> Dict[str, Any]:
        """
        Aggregate search results into coherent context for response generation
        
        Args:
            search_results: List of search results with scores
            query: Original search query
            
        Returns:
            Dict[str, Any]: Aggregated context with metadata
        """
        try:
            if not search_results:
                return self._create_empty_context(query)
            
            # Sort results by relevance score
            sorted_results = sorted(search_results, key=lambda x: x.get('search_score', 0), reverse=True)
            
            # Group results by section and content type
            grouped_results = self._group_results(sorted_results)
            
            # Build context from grouped results
            context_parts = []
            used_chunks = []
            current_length = 0
            
            # Prioritize high-scoring results from different sections
            for group_key, group_results in grouped_results.items():
                if current_length >= self.max_context_length:
                    break
                
                # Take the best result from each group
                best_result = group_results[0]
                content = best_result.get('content', '')
                
                # Check if adding this content would exceed limit
                if current_length + len(content) > self.max_context_length:
                    # Truncate content to fit
                    remaining_space = self.max_context_length - current_length
                    content = self._truncate_content_smartly(content, remaining_space)
                
                if content:
                    context_parts.append({
                        'content': content,
                        'source': self._create_source_info(best_result),
                        'relevance_score': best_result.get('search_score', 0),
                        'section': best_result.get('metadata', {}).get('section', 'Unknown'),
                        'chunk_id': best_result.get('chunk_id', '')
                    })
                    used_chunks.append(best_result)
                    current_length += len(content)
            
            # Create aggregated context
            aggregated_context = self._create_aggregated_context(context_parts, query, sorted_results)
            
            logger.info(f"Aggregated context from {len(used_chunks)} chunks for query: {query}")
            return aggregated_context
            
        except Exception as e:
            logger.error(f"Failed to aggregate search results: {e}")
            return self._create_empty_context(query, error=str(e))
    
    def _group_results(self, results: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group search results by section and content type for better organization
        
        Args:
            results: Search results to group
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: Grouped results
        """
        groups = {}
        
        for result in results:
            metadata = result.get('metadata', {})
            section = metadata.get('section', 'Unknown')
            content_type = metadata.get('chunk_type', 'general')
            
            # Create group key
            group_key = f"{section}_{content_type}"
            
            if group_key not in groups:
                groups[group_key] = []
            
            groups[group_key].append(result)
        
        # Sort each group by relevance score
        for group_key in groups:
            groups[group_key].sort(key=lambda x: x.get('search_score', 0), reverse=True)
        
        # Sort groups by best score in each group
        sorted_groups = dict(sorted(
            groups.items(),
            key=lambda x: x[1][0].get('search_score', 0) if x[1] else 0,
            reverse=True
        ))
        
        return sorted_groups
    
    def _truncate_content_smartly(self, content: str, max_length: int) -> str:
        """
        Truncate content at sentence boundaries when possible
        
        Args:
            content: Content to truncate
            max_length: Maximum allowed length
            
        Returns:
            str: Truncated content
        """
        if len(content) <= max_length:
            return content
        
        # Try to truncate at sentence boundary
        truncated = content[:max_length]
        
        # Find the last sentence ending
        last_sentence_end = max(
            truncated.rfind('.'),
            truncated.rfind('!'),
            truncated.rfind('?')
        )
        
        if last_sentence_end > max_length * 0.7:  # If we can keep at least 70% of content
            return truncated[:last_sentence_end + 1]
        
        # Otherwise, truncate at word boundary
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.8:  # If we can keep at least 80% of content
            return truncated[:last_space] + "..."
        
        # Fallback to character truncation
        return truncated + "..."
    
    def _create_source_info(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create source information for a chunk
        
        Args:
            chunk: Document chunk
            
        Returns:
            Dict[str, Any]: Source information
        """
        metadata = chunk.get('metadata', {})
        
        return {
            'document_name': metadata.get('document_name', 'Unknown Document'),
            'section': metadata.get('section', 'Unknown Section'),
            'page_numbers': metadata.get('page_numbers', []),
            'chunk_type': metadata.get('chunk_type', 'general'),
            'chunk_id': chunk.get('chunk_id', ''),
            'relevance_score': chunk.get('search_score', 0)
        }
    
    def _create_aggregated_context(self, context_parts: List[Dict[str, Any]], 
                                  query: str, all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create the final aggregated context structure
        
        Args:
            context_parts: Individual context parts
            query: Original query
            all_results: All search results
            
        Returns:
            Dict[str, Any]: Aggregated context
        """
        # Combine all content
        combined_content = "\n\n".join([
            f"[From {part['section']}]\n{part['content']}"
            for part in context_parts
        ])
        
        # Create source summary
        sources = []
        sections_covered = set()
        page_numbers = set()
        
        for part in context_parts:
            source = part['source']
            sources.append(source)
            sections_covered.add(source['section'])
            page_numbers.update(source['page_numbers'])
        
        # Calculate context statistics
        total_chunks = len(context_parts)
        avg_relevance = sum(part['relevance_score'] for part in context_parts) / total_chunks if total_chunks > 0 else 0
        
        return {
            'query': query,
            'context': combined_content,
            'context_parts': context_parts,
            'sources': sources,
            'statistics': {
                'total_chunks_used': total_chunks,
                'total_results_found': len(all_results),
                'sections_covered': list(sections_covered),
                'pages_referenced': sorted(list(page_numbers)),
                'average_relevance_score': round(avg_relevance, 3),
                'context_length': len(combined_content)
            },
            'metadata': {
                'aggregated_at': datetime.now().isoformat(),
                'has_content': len(combined_content) > 0,
                'confidence_level': self._calculate_confidence_level(context_parts, all_results)
            }
        }
    
    def _calculate_confidence_level(self, context_parts: List[Dict[str, Any]], 
                                   all_results: List[Dict[str, Any]]) -> str:
        """
        Calculate confidence level for the aggregated context
        
        Args:
            context_parts: Context parts used
            all_results: All search results
            
        Returns:
            str: Confidence level (high, medium, low)
        """
        if not context_parts:
            return 'none'
        
        # Calculate average relevance score
        avg_score = sum(part['relevance_score'] for part in context_parts) / len(context_parts)
        
        # Check coverage
        sections_count = len(set(part['section'] for part in context_parts))
        
        # Determine confidence level
        if avg_score >= 0.7 and sections_count >= 2:
            return 'high'
        elif avg_score >= 0.4 and sections_count >= 1:
            return 'medium'
        elif avg_score >= 0.2:
            return 'low'
        else:
            return 'very_low'
    
    def _create_empty_context(self, query: str, error: Optional[str] = None) -> Dict[str, Any]:
        """
        Create empty context when no results are found
        
        Args:
            query: Original query
            error: Optional error message
            
        Returns:
            Dict[str, Any]: Empty context structure
        """
        return {
            'query': query,
            'context': '',
            'context_parts': [],
            'sources': [],
            'statistics': {
                'total_chunks_used': 0,
                'total_results_found': 0,
                'sections_covered': [],
                'pages_referenced': [],
                'average_relevance_score': 0.0,
                'context_length': 0
            },
            'metadata': {
                'aggregated_at': datetime.now().isoformat(),
                'has_content': False,
                'confidence_level': 'none',
                'error': error
            }
        }
    
    def prepare_response_context(self, aggregated_context: Dict[str, Any], 
                               include_citations: bool = True) -> Dict[str, Any]:
        """
        Prepare context for response generation with proper formatting
        
        Args:
            aggregated_context: Aggregated context from search results
            include_citations: Whether to include source citations
            
        Returns:
            Dict[str, Any]: Formatted context for response generation
        """
        try:
            context = aggregated_context.get('context', '')
            sources = aggregated_context.get('sources', [])
            statistics = aggregated_context.get('statistics', {})
            
            # Format context for LLM
            formatted_context = context
            
            if include_citations and sources:
                # Add source information
                citation_info = "\n\nSource Information:\n"
                for i, source in enumerate(sources, 1):
                    pages = ", ".join(map(str, source['page_numbers'])) if source['page_numbers'] else "Unknown"
                    citation_info += f"{i}. Section: {source['section']} (Pages: {pages})\n"
                
                formatted_context += citation_info
            
            # Prepare response instructions
            instructions = self._generate_response_instructions(aggregated_context)
            
            return {
                'formatted_context': formatted_context,
                'instructions': instructions,
                'confidence_level': aggregated_context.get('metadata', {}).get('confidence_level', 'medium'),
                'has_content': len(context) > 0,
                'source_count': len(sources),
                'coverage_info': {
                    'sections': statistics.get('sections_covered', []),
                    'pages': statistics.get('pages_referenced', []),
                    'chunks': statistics.get('total_chunks_used', 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to prepare response context: {e}")
            return {
                'formatted_context': '',
                'instructions': 'No relevant information found in the manual.',
                'confidence_level': 'none',
                'has_content': False,
                'source_count': 0,
                'coverage_info': {'sections': [], 'pages': [], 'chunks': 0}
            }
    
    def _generate_response_instructions(self, aggregated_context: Dict[str, Any]) -> str:
        """
        Generate instructions for the LLM based on context quality
        
        Args:
            aggregated_context: Aggregated context
            
        Returns:
            str: Instructions for response generation
        """
        confidence = aggregated_context.get('metadata', {}).get('confidence_level', 'medium')
        has_content = aggregated_context.get('metadata', {}).get('has_content', False)
        
        if not has_content:
            return """No relevant information was found in the Royal Enfield Meteor manual for this query. 
Please let the user know that the information is not available in the manual and suggest they:
1. Rephrase their question with different terms
2. Contact a Royal Enfield dealer or service center
3. Consult the complete manual directly"""
        
        base_instructions = """Based on the information from the Royal Enfield Meteor owner's manual, provide a helpful and accurate response. """
        
        if confidence == 'high':
            return base_instructions + """The information found is highly relevant and comprehensive. 
Provide a detailed response with confidence, and mention the specific sections/pages where the information was found."""
        
        elif confidence == 'medium':
            return base_instructions + """The information found is moderately relevant. 
Provide a helpful response but acknowledge if the information might be partial or if additional details might be needed."""
        
        elif confidence == 'low':
            return base_instructions + """The information found has limited relevance to the query. 
Provide what information is available but clearly indicate that the response might be incomplete and suggest alternative approaches."""
        
        else:  # very_low or none
            return base_instructions + """Very limited relevant information was found. 
Provide any available information but clearly state the limitations and suggest the user consult additional resources."""