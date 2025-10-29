"""
S3-Only Tools for Royal Enfield Chatbot
Tools that retrieve pre-processed data directly from S3
"""

import logging
from typing import Dict, List, Optional, Any
from strands import tool
from utils.s3_only_knowledge_base import S3OnlyKnowledgeBase

logger = logging.getLogger(__name__)

# Global S3-only knowledge base instance
s3_kb = S3OnlyKnowledgeBase()

@tool
def search_s3_knowledge_base(query: str, max_results: int = 5) -> str:
    """
    Search the S3 knowledge base for relevant information
    
    Args:
        query: Search query about Royal Enfield Meteor
        max_results: Maximum number of results to return
        
    Returns:
        str: Search results with relevance scores
    """
    try:
        logger.info(f"Searching S3 knowledge base for: '{query}'")
        
        # Check if knowledge base is ready
        if not s3_kb.is_knowledge_base_ready():
            return """❌ S3 Knowledge Base Not Available

The Royal Enfield manual data is not available in the S3 bucket.

Please ensure:
• The S3 bucket contains processed manual data
• Processed chunks are in 'processed/chunks/' folder
• Document metadata exists in 'processed/metadata/' folder
• You have proper S3 access permissions"""
        
        results = s3_kb.search_chunks(query, max_results)
        
        if not results:
            return f"""🔍 S3 Search Results for: "{query}"

❌ No relevant information found in the Royal Enfield Meteor manual stored in S3.

💡 Suggestions:
• Try rephrasing your question with different keywords
• Use more specific terms (e.g., "engine oil change" instead of "maintenance")
• Check if your question relates to motorcycle maintenance, specifications, or troubleshooting"""
        
        # Format results
        result_text = f"🔍 S3 Search Results for: \"{query}\"\n\n"
        result_text += f"☁️ Retrieved from AWS S3 storage\n"
        result_text += f"📊 Found {len(results)} relevant results:\n\n"
        
        for i, result in enumerate(results, 1):
            content = result.get('content', '')
            # Truncate long content
            if len(content) > 300:
                content = content[:300] + "..."
            
            score = result.get('relevance_score', 0)
            metadata = result.get('metadata', {})
            
            result_text += f"**Result {i}** (Relevance: {score:.2f})\n"
            result_text += f"📍 Section: {metadata.get('section', 'Unknown')}\n"
            
            pages = metadata.get('page_numbers', [])
            if pages:
                result_text += f"📄 Pages: {', '.join(map(str, pages))}\n"
            
            result_text += f"🏷️ Type: {metadata.get('chunk_type', 'general')}\n"
            result_text += f"📝 Content: {content}\n\n"
        
        return result_text
        
    except Exception as e:
        error_msg = f"❌ S3 search failed: {str(e)}"
        logger.error(error_msg)
        return error_msg

@tool
def get_contextual_information_s3(query: str) -> str:
    """
    Get aggregated contextual information for a query from S3 knowledge base
    
    Args:
        query: Query to get context for
        
    Returns:
        str: Aggregated context with source information
    """
    try:
        logger.info(f"Getting contextual information from S3 for: '{query}'")
        
        # Check if knowledge base is ready
        if not s3_kb.is_knowledge_base_ready():
            return """❌ S3 Knowledge Base Not Available

The Royal Enfield manual data is not available in the S3 bucket.
Please ensure the processed data exists in S3."""
        
        # Search for relevant information
        search_results = s3_kb.search_chunks(query, max_results=8)
        
        if not search_results:
            return f"""📋 S3 Context for: "{query}"

❌ No relevant information found in the Royal Enfield Meteor manual stored in S3.

The manual may not contain information about this specific topic. Consider:
• Consulting a Royal Enfield dealer or service center
• Checking the complete owner's manual
• Rephrasing your question with different terms"""
        
        # Aggregate context
        context_parts = []
        sections_covered = set()
        pages_referenced = set()
        
        for result in search_results[:5]:  # Use top 5 results
            content = result.get('content', '')
            metadata = result.get('metadata', {})
            
            sections_covered.add(metadata.get('section', 'Unknown'))
            pages_referenced.update(metadata.get('page_numbers', []))
            
            context_parts.append({
                'content': content,
                'section': metadata.get('section', 'Unknown'),
                'pages': metadata.get('page_numbers', []),
                'score': result.get('relevance_score', 0)
            })
        
        # Calculate confidence level
        avg_score = sum(part['score'] for part in context_parts) / len(context_parts)
        if avg_score >= 0.7:
            confidence = 'high'
        elif avg_score >= 0.4:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        # Format context
        context_text = f"📋 S3 Contextual Information for: \"{query}\"\n\n"
        context_text += f"☁️ Retrieved from AWS S3 storage\n"
        context_text += f"🎯 Confidence Level: {confidence.title()}\n"
        context_text += f"📚 Sources: {len(context_parts)} sections\n"
        context_text += f"📄 Pages: {', '.join(map(str, sorted(pages_referenced)))}\n\n"
        
        context_text += "📖 **Relevant Information:**\n\n"
        
        for i, part in enumerate(context_parts, 1):
            context_text += f"**From {part['section']}** (Score: {part['score']:.2f})\n"
            context_text += f"{part['content']}\n\n"
        
        context_text += f"📚 **S3 Sources Referenced:**\n"
        for section in sorted(sections_covered):
            context_text += f"• {section}\n"
        
        return context_text
        
    except Exception as e:
        error_msg = f"❌ Failed to get S3 contextual information: {str(e)}"
        logger.error(error_msg)
        return error_msg

@tool
def get_s3_knowledge_base_status() -> str:
    """
    Get the status and statistics of the S3 knowledge base
    
    Returns:
        str: S3 knowledge base status and statistics
    """
    try:
        stats = s3_kb.get_knowledge_base_stats()
        health = s3_kb.get_s3_health_status()
        
        if not stats['ready']:
            return """📊 S3 Knowledge Base Status

❌ Knowledge base not ready

The Royal Enfield manual data is not available in the S3 bucket.

Required S3 structure:
• processed/chunks/ - Text chunks in JSON format
• processed/metadata/ - Document metadata
• documents/ - Original PDF files (optional)

Please ensure the processed data exists in your S3 bucket."""
        
        doc_metadata = stats.get('document_metadata', {})
        storage_stats = stats.get('storage_stats', {})
        
        result = f"""📊 S3 Knowledge Base Status

✅ Status: Ready and operational
☁️ Storage: AWS S3

📄 **Document Information:**
• Name: {doc_metadata.get('document_name', 'Royal Enfield Meteor Manual')}
• Processed: {doc_metadata.get('processed_at', 'Unknown')}

📈 **Content Statistics:**
• Total chunks: {stats['total_chunks']}
• Total words: {stats['total_words']:,}
• Sections: {len(stats['sections'])}
• Pages covered: {len(stats['pages'])}

☁️ **S3 Storage Statistics:**
• Total objects: {storage_stats.get('total_objects', 0)}
• Documents: {storage_stats.get('documents_count', 0)}
• Chunks: {storage_stats.get('chunks_count', 0)}
• Total size: {storage_stats.get('total_size_mb', 0)} MB

🔗 **S3 Connection:**
• Status: {'✅ Connected' if health['healthy'] else '❌ Issues detected'}
• Region: {health.get('s3_connection', {}).get('region', 'Unknown')}
• Bucket: {health.get('s3_connection', {}).get('bucket', {}).get('name', 'Unknown')}

📂 **Available Sections:**"""
        
        for section in stats['sections'][:10]:  # Show first 10 sections
            result += f"\n• {section}"
        
        if len(stats['sections']) > 10:
            result += f"\n... and {len(stats['sections']) - 10} more sections"
        
        if stats['pages']:
            result += f"\n\n📄 **Page Range:** {min(stats['pages'])} - {max(stats['pages'])}"
        
        result += f"\n\n🔍 **Ready for queries about:**"
        result += f"\n• Maintenance procedures"
        result += f"\n• Engine specifications"
        result += f"\n• Troubleshooting guides"
        result += f"\n• Safety information"
        result += f"\n• Operating procedures"
        
        return result
        
    except Exception as e:
        return f"❌ Failed to get S3 knowledge base status: {str(e)}"

@tool
def search_by_section_s3(section_name: str, query: Optional[str] = None) -> str:
    """
    Search within a specific section of the manual in S3
    
    Args:
        section_name: Name of the section to search in
        query: Optional specific query within the section
        
    Returns:
        str: Section-specific search results from S3
    """
    try:
        logger.info(f"Searching S3 section '{section_name}' for: '{query or 'all content'}'")
        
        if not s3_kb.is_knowledge_base_ready():
            return "❌ S3 knowledge base not available. Please ensure processed data exists in S3."
        
        # Get chunks from specific section
        section_chunks = s3_kb.get_chunks_by_section(section_name)
        
        if not section_chunks:
            return f"""📂 S3 Section Search: "{section_name}"

❌ No content found in S3 section matching: "{section_name}"

Available sections might include:
• Maintenance and Service
• Engine Specifications  
• Troubleshooting
• Safety Information
• Operating Procedures

Try searching with a different section name or use the general S3 search."""
        
        result_text = f"📂 S3 Section Search: \"{section_name}\"\n\n"
        result_text += f"☁️ Retrieved from AWS S3 storage\n"
        result_text += f"📊 Found {len(section_chunks)} chunks in this section\n\n"
        
        # If specific query provided, search within section
        if query:
            query_lower = query.lower()
            filtered_results = []
            
            for chunk in section_chunks:
                content = chunk.get('content', '').lower()
                score = s3_kb._calculate_relevance_score(query_lower, content)
                if score > 0.1:
                    chunk['relevance_score'] = score
                    filtered_results.append(chunk)
            
            filtered_results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            if filtered_results:
                result_text += f"🔍 Results for \"{query}\" in S3 section \"{section_name}\":\n\n"
                for i, result in enumerate(filtered_results[:5], 1):
                    content = result.get('content', '')
                    if len(content) > 200:
                        content = content[:200] + "..."
                    
                    score = result.get('relevance_score', 0)
                    metadata = result.get('metadata', {})
                    
                    result_text += f"**Match {i}** (Score: {score:.2f})\n"
                    pages = metadata.get('page_numbers', [])
                    if pages:
                        result_text += f"📄 Pages: {', '.join(map(str, pages))}\n"
                    result_text += f"📝 Content: {content}\n\n"
            else:
                result_text += f"❌ No matches for \"{query}\" in S3 section \"{section_name}\"\n"
        else:
            # Show section overview
            result_text += f"📋 Section Overview:\n\n"
            for i, chunk in enumerate(section_chunks[:3], 1):
                content = chunk.get('content', '')
                if len(content) > 150:
                    content = content[:150] + "..."
                
                metadata = chunk.get('metadata', {})
                
                result_text += f"**Chunk {i}**\n"
                pages = metadata.get('page_numbers', [])
                if pages:
                    result_text += f"📄 Pages: {', '.join(map(str, pages))}\n"
                result_text += f"📝 Content: {content}\n\n"
            
            if len(section_chunks) > 3:
                result_text += f"... and {len(section_chunks) - 3} more chunks in this section\n"
        
        return result_text
        
    except Exception as e:
        error_msg = f"❌ S3 section search failed: {str(e)}"
        logger.error(error_msg)
        return error_msg

@tool
def search_by_page_s3(page_number: int) -> str:
    """
    Search content from a specific page in S3
    
    Args:
        page_number: Page number to search
        
    Returns:
        str: Content from the specified page
    """
    try:
        logger.info(f"Searching S3 page {page_number}")
        
        if not s3_kb.is_knowledge_base_ready():
            return "❌ S3 knowledge base not available. Please ensure processed data exists in S3."
        
        # Get chunks from specific page
        page_chunks = s3_kb.get_chunks_by_page(page_number)
        
        if not page_chunks:
            return f"""📄 S3 Page Search: Page {page_number}

❌ No content found on page {page_number} in S3.

This could mean:
• The page number doesn't exist in the manual
• The page contains only images or diagrams
• The page wasn't processed correctly

Try searching by topic or section instead."""
        
        result_text = f"📄 S3 Content from Page {page_number}\n\n"
        result_text += f"☁️ Retrieved from AWS S3 storage\n"
        result_text += f"📊 Found {len(page_chunks)} content sections on this page\n\n"
        
        for i, chunk in enumerate(page_chunks, 1):
            content = chunk.get('content', '')
            metadata = chunk.get('metadata', {})
            
            result_text += f"**Section {i}**\n"
            result_text += f"📂 From: {metadata.get('section', 'Unknown Section')}\n"
            result_text += f"🏷️ Type: {metadata.get('chunk_type', 'general')}\n"
            result_text += f"📝 Content:\n{content}\n\n"
        
        return result_text
        
    except Exception as e:
        error_msg = f"❌ S3 page search failed: {str(e)}"
        logger.error(error_msg)
        return error_msg

@tool
def get_s3_health_status() -> str:
    """
    Get comprehensive S3 connection and knowledge base health status
    
    Returns:
        str: S3 health status information
    """
    try:
        health = s3_kb.get_s3_health_status()
        
        result = f"""🏥 S3 Knowledge Base Health Status

🔗 **Overall Health:** {'✅ Healthy' if health['healthy'] else '❌ Issues Detected'}

☁️ **S3 Connection:**
• Status: {'✅ Connected' if health.get('s3_connection', {}).get('connected') else '❌ Connection Issues'}
• Region: {health.get('s3_connection', {}).get('region', 'Unknown')}
• Bucket: {health.get('s3_connection', {}).get('bucket', {}).get('name', 'Unknown')}

📊 **S3 Storage:**
• Total Objects: {health.get('s3_storage', {}).get('total_objects', 0)}
• Documents: {health.get('s3_storage', {}).get('documents_count', 0)}
• Chunks: {health.get('s3_storage', {}).get('chunks_count', 0)}
• Total Size: {health.get('s3_storage', {}).get('total_size_mb', 0)} MB

📚 **Knowledge Base:**
• Status: {'✅ Ready' if health.get('knowledge_base', {}).get('ready') else '❌ Not Ready'}
• Total Chunks: {health.get('knowledge_base', {}).get('total_chunks', 0)}
• Total Words: {health.get('knowledge_base', {}).get('total_words', 0):,}

🔐 **S3 Permissions:**"""
        
        permissions = health.get('s3_connection', {}).get('permissions', {})
        result += f"\n• Read: {'✅' if permissions.get('read') else '❌'}"
        result += f"\n• Write: {'✅' if permissions.get('write') else '❌'}"
        result += f"\n• List: {'✅' if permissions.get('list') else '❌'}"
        
        if not health['healthy']:
            error = health.get('error')
            if error:
                result += f"\n\n⚠️ **Error:** {error}"
        
        result += f"\n\n🕐 **Last Checked:** {health.get('timestamp', 'Unknown')}"
        
        return result
        
    except Exception as e:
        return f"❌ Failed to get S3 health status: {str(e)}"

@tool
def clear_s3_cache() -> str:
    """
    Clear the S3 knowledge base cache
    
    Returns:
        str: Cache clear result
    """
    try:
        s3_kb.clear_cache()
        return "✅ S3 knowledge base cache cleared successfully. Fresh data will be loaded on next request."
        
    except Exception as e:
        return f"❌ Failed to clear S3 cache: {str(e)}"