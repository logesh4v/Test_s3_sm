"""
Retrieval Tools for Royal Enfield Chatbot
Custom tools for the Retrieval Agent
"""

import json
import logging
from typing import Dict, List, Optional, Any
from strands import tool
from utils.semantic_search import SemanticSearchEngine
from utils.context_aggregator import ContextAggregator
from utils.content_retriever import ContentRetriever

logger = logging.getLogger(__name__)

@tool
def search_knowledge_base(query: str, max_results: int = 5, document_name: Optional[str] = None) -> str:
    """
    Search the Royal Enfield knowledge base for relevant information
    
    Args:
        query: Search query about Royal Enfield Meteor
        max_results: Maximum number of results to return (default: 5)
        document_name: Optional specific document to search in
        
    Returns:
        str: Search results with relevance scores and source information
    """
    try:
        logger.info(f"Searching knowledge base for: '{query}'")
        
        search_engine = SemanticSearchEngine()
        results = search_engine.search(
            query=query,
            document_name=document_name,
            max_results=max_results
        )
        
        if not results:
            return f"""🔍 Search Results for: "{query}"

❌ No relevant information found in the Royal Enfield Meteor manual.

💡 Suggestions:
• Try rephrasing your question with different keywords
• Use more specific terms (e.g., "engine oil change" instead of "maintenance")
• Check if your question relates to motorcycle maintenance, specifications, or troubleshooting"""
        
        # Format results
        result_text = f"🔍 Search Results for: \"{query}\"\n\n"
        result_text += f"📊 Found {len(results)} relevant results:\n\n"
        
        for i, result in enumerate(results, 1):
            content = result.get('content', '')[:300] + "..." if len(result.get('content', '')) > 300 else result.get('content', '')
            score = result.get('search_score', 0)
            metadata = result.get('metadata', {})
            
            result_text += f"**Result {i}** (Relevance: {score:.2f})\n"
            result_text += f"📍 Section: {metadata.get('section', 'Unknown')}\n"
            result_text += f"📄 Pages: {', '.join(map(str, metadata.get('page_numbers', [])))}\n"
            result_text += f"🏷️ Type: {metadata.get('chunk_type', 'general')}\n"
            result_text += f"📝 Content: {content}\n\n"
        
        return result_text
        
    except Exception as e:
        error_msg = f"❌ Search failed: {str(e)}"
        logger.error(error_msg)
        return error_msg

@tool
def get_contextual_information(query: str, max_context_length: int = 4000) -> str:
    """
    Get aggregated contextual information for a query, optimized for response generation
    
    Args:
        query: Query to get context for
        max_context_length: Maximum length of aggregated context
        
    Returns:
        str: Aggregated context with source citations
    """
    try:
        logger.info(f"Getting contextual information for: '{query}'")
        
        # Search for relevant information
        search_engine = SemanticSearchEngine()
        search_results = search_engine.search(query=query, max_results=10)
        
        if not search_results:
            return f"""📋 Context for: "{query}"

❌ No relevant information found in the Royal Enfield Meteor manual.

The manual may not contain information about this specific topic. Consider:
• Consulting a Royal Enfield dealer or service center
• Checking the complete owner's manual
• Rephrasing your question with different terms"""
        
        # Aggregate context
        aggregator = ContextAggregator(max_context_length=max_context_length)
        aggregated_context = aggregator.aggregate_search_results(search_results, query)
        
        # Prepare response context
        response_context = aggregator.prepare_response_context(aggregated_context, include_citations=True)
        
        # Format the context
        context_text = f"📋 Contextual Information for: \"{query}\"\n\n"
        
        if response_context['has_content']:
            context_text += f"🎯 Confidence Level: {response_context['confidence_level'].title()}\n"
            context_text += f"📚 Sources: {response_context['source_count']} sections\n"
            context_text += f"📄 Pages: {', '.join(map(str, response_context['coverage_info']['pages']))}\n\n"
            
            context_text += "📖 **Relevant Information:**\n"
            context_text += response_context['formatted_context']
            
            context_text += f"\n\n💡 **Response Instructions:**\n{response_context['instructions']}"
        else:
            context_text += "❌ No contextual information available.\n"
            context_text += response_context['instructions']
        
        return context_text
        
    except Exception as e:
        error_msg = f"❌ Failed to get contextual information: {str(e)}"
        logger.error(error_msg)
        return error_msg

@tool
def search_by_section(section_name: str, query: Optional[str] = None) -> str:
    """
    Search within a specific section of the manual
    
    Args:
        section_name: Name of the section to search in
        query: Optional specific query within the section
        
    Returns:
        str: Section-specific search results
    """
    try:
        logger.info(f"Searching section '{section_name}' for: '{query or 'all content'}'")
        
        content_retriever = ContentRetriever()
        
        # Get all chunks and filter by section
        all_chunks = content_retriever._get_all_chunks()
        section_chunks = [
            chunk for chunk in all_chunks
            if section_name.lower() in chunk.get('metadata', {}).get('section', '').lower()
        ]
        
        if not section_chunks:
            return f"""📂 Section Search: "{section_name}"

❌ No content found in section matching: "{section_name}"

Available sections might include:
• Maintenance and Service
• Engine Specifications  
• Troubleshooting
• Safety Information
• Operating Procedures

Try searching with a different section name or use the general search."""
        
        result_text = f"📂 Section Search: \"{section_name}\"\n\n"
        result_text += f"📊 Found {len(section_chunks)} chunks in this section\n\n"
        
        # If specific query provided, search within section
        if query:
            search_engine = SemanticSearchEngine()
            # Filter search results to only include this section
            filtered_results = []
            for chunk in section_chunks:
                score = search_engine._calculate_comprehensive_score(chunk, query, search_engine._extract_terms(query.lower()))
                if score > 0.1:
                    chunk['search_score'] = score
                    filtered_results.append(chunk)
            
            filtered_results.sort(key=lambda x: x['search_score'], reverse=True)
            
            if filtered_results:
                result_text += f"🔍 Results for \"{query}\" in section \"{section_name}\":\n\n"
                for i, result in enumerate(filtered_results[:5], 1):
                    content = result.get('content', '')[:200] + "..." if len(result.get('content', '')) > 200 else result.get('content', '')
                    score = result.get('search_score', 0)
                    metadata = result.get('metadata', {})
                    
                    result_text += f"**Match {i}** (Score: {score:.2f})\n"
                    result_text += f"📄 Pages: {', '.join(map(str, metadata.get('page_numbers', [])))}\n"
                    result_text += f"📝 Content: {content}\n\n"
            else:
                result_text += f"❌ No matches for \"{query}\" in section \"{section_name}\"\n"
        else:
            # Show section overview
            result_text += f"📋 Section Overview:\n\n"
            for i, chunk in enumerate(section_chunks[:3], 1):
                content = chunk.get('content', '')[:150] + "..." if len(chunk.get('content', '')) > 150 else chunk.get('content', '')
                metadata = chunk.get('metadata', {})
                
                result_text += f"**Chunk {i}**\n"
                result_text += f"📄 Pages: {', '.join(map(str, metadata.get('page_numbers', [])))}\n"
                result_text += f"📝 Content: {content}\n\n"
            
            if len(section_chunks) > 3:
                result_text += f"... and {len(section_chunks) - 3} more chunks in this section\n"
        
        return result_text
        
    except Exception as e:
        error_msg = f"❌ Section search failed: {str(e)}"
        logger.error(error_msg)
        return error_msg

@tool
def search_by_page(page_number: int, document_name: Optional[str] = None) -> str:
    """
    Search content from a specific page number
    
    Args:
        page_number: Page number to search
        document_name: Optional specific document name
        
    Returns:
        str: Content from the specified page
    """
    try:
        logger.info(f"Searching page {page_number} in document: {document_name or 'all documents'}")
        
        content_retriever = ContentRetriever()
        
        if document_name:
            chunks = content_retriever.get_chunks_by_page(document_name, page_number)
        else:
            # Search all documents
            all_chunks = content_retriever._get_all_chunks()
            chunks = [
                chunk for chunk in all_chunks
                if page_number in chunk.get('metadata', {}).get('page_numbers', [])
            ]
        
        if not chunks:
            return f"""📄 Page Search: Page {page_number}

❌ No content found on page {page_number}.

This could mean:
• The page number doesn't exist in the manual
• The page contains only images or diagrams
• The page wasn't processed correctly

Try searching by topic or section instead."""
        
        result_text = f"📄 Content from Page {page_number}\n\n"
        result_text += f"📊 Found {len(chunks)} content sections on this page\n\n"
        
        for i, chunk in enumerate(chunks, 1):
            content = chunk.get('content', '')
            metadata = chunk.get('metadata', {})
            
            result_text += f"**Section {i}**\n"
            result_text += f"📂 From: {metadata.get('section', 'Unknown Section')}\n"
            result_text += f"🏷️ Type: {metadata.get('chunk_type', 'general')}\n"
            result_text += f"📝 Content:\n{content}\n\n"
        
        return result_text
        
    except Exception as e:
        error_msg = f"❌ Page search failed: {str(e)}"
        logger.error(error_msg)
        return error_msg

@tool
def get_search_suggestions(partial_query: str) -> str:
    """
    Get search suggestions based on partial query
    
    Args:
        partial_query: Partial search query to get suggestions for
        
    Returns:
        str: List of search suggestions
    """
    try:
        search_engine = SemanticSearchEngine()
        suggestions = search_engine.get_search_suggestions(partial_query, limit=10)
        
        if not suggestions:
            return f"""💡 Search Suggestions for: "{partial_query}"

❌ No suggestions found.

Try common motorcycle terms like:
• maintenance, service, oil change
• engine, brake, clutch, transmission
• troubleshooting, problem, repair
• specifications, dimensions, capacity"""
        
        result_text = f"💡 Search Suggestions for: \"{partial_query}\"\n\n"
        result_text += "📝 Suggested search terms:\n\n"
        
        for i, suggestion in enumerate(suggestions, 1):
            result_text += f"{i}. {suggestion}\n"
        
        result_text += "\n🔍 Click or type any suggestion to search!"
        
        return result_text
        
    except Exception as e:
        error_msg = f"❌ Failed to get suggestions: {str(e)}"
        logger.error(error_msg)
        return error_msg

@tool
def get_knowledge_base_overview() -> str:
    """
    Get an overview of the knowledge base contents
    
    Returns:
        str: Overview of available content
    """
    try:
        content_retriever = ContentRetriever()
        all_chunks = content_retriever._get_all_chunks()
        
        if not all_chunks:
            return """📚 Knowledge Base Overview

❌ No content available in the knowledge base.

Please process a Royal Enfield Meteor manual first using the document processor."""
        
        # Analyze content
        sections = set()
        content_types = {}
        page_numbers = set()
        total_words = 0
        
        for chunk in all_chunks:
            metadata = chunk.get('metadata', {})
            sections.add(metadata.get('section', 'Unknown'))
            
            chunk_type = metadata.get('chunk_type', 'general')
            content_types[chunk_type] = content_types.get(chunk_type, 0) + 1
            
            page_numbers.update(metadata.get('page_numbers', []))
            total_words += metadata.get('word_count', 0)
        
        result_text = "📚 Knowledge Base Overview\n\n"
        result_text += f"📊 **Statistics:**\n"
        result_text += f"• Total chunks: {len(all_chunks)}\n"
        result_text += f"• Total words: {total_words:,}\n"
        result_text += f"• Pages covered: {len(page_numbers)} pages\n"
        result_text += f"• Sections: {len(sections)}\n\n"
        
        result_text += f"📂 **Available Sections:**\n"
        for section in sorted(sections):
            result_text += f"• {section}\n"
        
        result_text += f"\n🏷️ **Content Types:**\n"
        for content_type, count in sorted(content_types.items()):
            result_text += f"• {content_type.title()}: {count} chunks\n"
        
        result_text += f"\n📄 **Page Range:** {min(page_numbers)} - {max(page_numbers)}\n"
        
        result_text += f"\n🔍 **Search Tips:**\n"
        result_text += f"• Use specific terms like 'oil change', 'brake adjustment'\n"
        result_text += f"• Search by section for organized results\n"
        result_text += f"• Ask questions in natural language\n"
        
        return result_text
        
    except Exception as e:
        error_msg = f"❌ Failed to get overview: {str(e)}"
        logger.error(error_msg)
        return error_msg