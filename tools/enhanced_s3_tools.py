"""
Enhanced S3 Tools for Royal Enfield Chatbot
Pure S3-based tools for PDF upload and knowledge base management
"""

import logging
import json
from typing import Dict, List, Optional, Any
from strands import tool
from utils.s3_only_knowledge_base import S3OnlyKnowledgeBase
from utils.s3_manager import S3Manager

logger = logging.getLogger(__name__)

# Global instances
s3_kb = S3OnlyKnowledgeBase()
s3_manager = S3Manager()

@tool
def upload_pdf_to_s3(pdf_file_path: str, document_name: Optional[str] = None) -> str:
    """
    Upload a PDF file directly to S3 for processing
    
    Args:
        pdf_file_path: Local path to the PDF file
        document_name: Optional custom name for the document
        
    Returns:
        str: Upload result and next steps
    """
    try:
        logger.info(f"Uploading PDF to S3: {pdf_file_path}")
        
        # Upload PDF to S3 documents folder
        result = s3_manager.upload_pdf_document(pdf_file_path, document_name)
        
        if result['success']:
            return f"""✅ PDF Upload Successful

📄 **Document:** {result['document_name']}
☁️ **S3 Location:** {result['s3_key']}
📊 **File Size:** {result['file_size_mb']} MB
🕐 **Uploaded:** {result['upload_time']}

📋 **Next Steps:**
1. The PDF is now stored in S3
2. You can process it into searchable chunks
3. Use 'process_s3_pdf' to create the knowledge base
4. Once processed, it will be available for chat queries

💡 **Note:** This is a pure S3-based system. The PDF will remain in S3 and can be processed on-demand."""
        else:
            return f"❌ PDF upload failed: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        error_msg = f"❌ Failed to upload PDF to S3: {str(e)}"
        logger.error(error_msg)
        return error_msg

@tool
def process_s3_pdf(document_name: str) -> str:
    """
    Process a PDF stored in S3 into searchable chunks
    
    Args:
        document_name: Name of the document in S3 to process
        
    Returns:
        str: Processing result
    """
    try:
        logger.info(f"Processing S3 PDF: {document_name}")
        
        # This would trigger S3-based processing (Lambda function or similar)
        # For now, we'll simulate the process
        result = s3_manager.process_pdf_document(document_name)
        
        if result['success']:
            return f"""✅ PDF Processing Complete

📄 **Document:** {document_name}
📊 **Chunks Created:** {result['total_chunks']}
📝 **Total Words:** {result['total_words']:,}
📂 **Sections:** {result['sections_count']}
☁️ **S3 Storage:** {result['storage_size_mb']} MB

🎯 **Knowledge Base Ready!**
The document has been processed and is now available for:
• Intelligent search queries
• Section-specific searches  
• Conversational Q&A
• Contextual information retrieval

💬 You can now ask questions about the {document_name} manual!"""
        else:
            return f"❌ PDF processing failed: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        error_msg = f"❌ Failed to process S3 PDF: {str(e)}"
        logger.error(error_msg)
        return error_msg

@tool
def list_s3_documents() -> str:
    """
    List all documents stored in S3
    
    Returns:
        str: List of available documents
    """
    try:
        documents = s3_manager.list_documents()
        
        if not documents:
            return """📂 S3 Documents

❌ No documents found in S3 storage.

To get started:
1. Upload a PDF using 'upload_pdf_to_s3'
2. Process it with 'process_s3_pdf'
3. Start asking questions!"""
        
        result = "📂 S3 Documents\n\n"
        result += f"☁️ Found {len(documents)} documents in S3:\n\n"
        
        for doc in documents:
            result += f"**{doc['name']}**\n"
            result += f"📄 Type: {doc['type']}\n"
            result += f"📊 Size: {doc['size_mb']} MB\n"
            result += f"🕐 Modified: {doc['last_modified']}\n"
            result += f"📍 Status: {doc['status']}\n\n"
        
        return result
        
    except Exception as e:
        error_msg = f"❌ Failed to list S3 documents: {str(e)}"
        logger.error(error_msg)
        return error_msg

@tool
def delete_s3_document(document_name: str) -> str:
    """
    Delete a document and its processed data from S3
    
    Args:
        document_name: Name of the document to delete
        
    Returns:
        str: Deletion result
    """
    try:
        logger.info(f"Deleting S3 document: {document_name}")
        
        result = s3_manager.delete_document(document_name)
        
        if result['success']:
            return f"""✅ Document Deleted Successfully

📄 **Document:** {document_name}
🗑️ **Removed:**
• Original PDF file
• Processed chunks ({result['chunks_deleted']} files)
• Document metadata
• Search indexes

☁️ **S3 Storage Freed:** {result['storage_freed_mb']} MB

The document has been completely removed from the knowledge base."""
        else:
            return f"❌ Document deletion failed: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        error_msg = f"❌ Failed to delete S3 document: {str(e)}"
        logger.error(error_msg)
        return error_msg

@tool
def get_s3_storage_stats() -> str:
    """
    Get comprehensive S3 storage statistics
    
    Returns:
        str: Storage statistics and usage information
    """
    try:
        stats = s3_manager.get_storage_statistics()
        
        result = f"""📊 S3 Storage Statistics

☁️ **AWS S3 Bucket:** {stats['bucket_name']}
🌍 **Region:** {stats['region']}

📄 **Documents:**
• Total Documents: {stats['total_documents']}
• PDF Files: {stats['pdf_count']}
• Processed Documents: {stats['processed_count']}

📦 **Storage Usage:**
• Total Size: {stats['total_size_mb']} MB
• Documents: {stats['documents_size_mb']} MB  
• Processed Data: {stats['processed_size_mb']} MB
• Metadata: {stats['metadata_size_mb']} MB

🔍 **Knowledge Base:**
• Total Chunks: {stats['total_chunks']}
• Total Words: {stats['total_words']:,}
• Searchable Sections: {stats['sections_count']}

💰 **Estimated Monthly Cost:** ${stats['estimated_cost_usd']:.2f}

🕐 **Last Updated:** {stats['last_updated']}"""
        
        return result
        
    except Exception as e:
        error_msg = f"❌ Failed to get S3 storage stats: {str(e)}"
        logger.error(error_msg)
        return error_msg

@tool
def search_s3_advanced(query: str, filters: Optional[Dict[str, Any]] = None) -> str:
    """
    Advanced search with filters and options
    
    Args:
        query: Search query
        filters: Optional filters (section, page_range, document, etc.)
        
    Returns:
        str: Advanced search results
    """
    try:
        logger.info(f"Advanced S3 search: {query} with filters: {filters}")
        
        if not s3_kb.is_knowledge_base_ready():
            return "❌ S3 knowledge base not available. Please ensure processed data exists in S3."
        
        # Apply filters if provided
        search_options = {
            'max_results': filters.get('max_results', 5) if filters else 5,
            'min_score': filters.get('min_score', 0.1) if filters else 0.1,
            'section_filter': filters.get('section') if filters else None,
            'document_filter': filters.get('document') if filters else None
        }
        
        results = s3_kb.advanced_search(query, search_options)
        
        if not results:
            return f"""🔍 Advanced S3 Search: "{query}"

❌ No results found with the specified criteria.

Applied filters: {json.dumps(filters, indent=2) if filters else 'None'}

💡 Try:
• Reducing filter restrictions
• Using broader search terms
• Checking available sections and documents"""
        
        result_text = f"🔍 Advanced S3 Search: \"{query}\"\n\n"
        
        if filters:
            result_text += f"🎯 **Applied Filters:**\n"
            for key, value in filters.items():
                result_text += f"• {key}: {value}\n"
            result_text += "\n"
        
        result_text += f"📊 Found {len(results)} results:\n\n"
        
        for i, result in enumerate(results, 1):
            content = result.get('content', '')
            if len(content) > 250:
                content = content[:250] + "..."
            
            score = result.get('relevance_score', 0)
            metadata = result.get('metadata', {})
            
            result_text += f"**Result {i}** (Score: {score:.3f})\n"
            result_text += f"📂 Section: {metadata.get('section', 'Unknown')}\n"
            result_text += f"📄 Pages: {', '.join(map(str, metadata.get('page_numbers', [])))}\n"
            result_text += f"📝 Content: {content}\n\n"
        
        return result_text
        
    except Exception as e:
        error_msg = f"❌ Advanced S3 search failed: {str(e)}"
        logger.error(error_msg)
        return error_msg