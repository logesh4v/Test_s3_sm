"""
Document Processing Tools for Royal Enfield Chatbot
Custom tools for the Document Processor Agent
"""

import json
import logging
from typing import Dict, List, Optional, Any
from strands import tool
from utils.pdf_processor import PDFProcessor
from utils.text_chunker import TextChunker
from utils.document_uploader import DocumentUploader
from utils.s3_manager import S3StorageManager

logger = logging.getLogger(__name__)

@tool
def process_pdf_document(file_path: str, document_name: Optional[str] = None) -> str:
    """
    Process a PDF document by extracting text, chunking, and uploading to S3
    
    Args:
        file_path: Path to the PDF file to process
        document_name: Optional custom name for the document
        
    Returns:
        str: Processing result summary
    """
    try:
        logger.info(f"Starting PDF processing for: {file_path}")
        
        # Initialize processors
        pdf_processor = PDFProcessor()
        text_chunker = TextChunker()
        document_uploader = DocumentUploader()
        storage_manager = S3StorageManager()
        
        # Step 1: Validate PDF
        validation = pdf_processor.validate_pdf(file_path)
        if not validation['valid']:
            return f"❌ PDF validation failed: {', '.join(validation['errors'])}"
        
        # Step 2: Extract text from PDF
        extraction_result = pdf_processor.extract_text_from_pdf(file_path)
        if not extraction_result['success']:
            return f"❌ Text extraction failed: {extraction_result.get('error', 'Unknown error')}"
        
        # Step 3: Extract sections
        sections = pdf_processor.extract_sections(
            extraction_result['text'], 
            extraction_result['pages']
        )
        
        # Step 4: Upload original document
        upload_result = document_uploader.upload_pdf_document(file_path, document_name)
        if not upload_result['success']:
            return f"❌ Document upload failed: {upload_result.get('error', 'Unknown error')}"
        
        # Step 5: Create text chunks
        chunks = text_chunker.chunk_document(
            text=extraction_result['text'],
            pages_data=extraction_result['pages'],
            sections=sections,
            document_name=document_name or upload_result['metadata']['document_name']
        )
        
        # Step 6: Upload chunks to S3
        uploaded_chunks = 0
        for chunk in chunks:
            chunk_key = f"processed/chunks/{chunk['chunk_id']}.json"
            chunk_content = json.dumps(chunk, indent=2)
            
            success = storage_manager.upload_content(
                content=chunk_content,
                s3_key=chunk_key,
                content_type='application/json'
            )
            
            if success:
                uploaded_chunks += 1
        
        # Step 7: Create processing summary
        summary = {
            'document_name': upload_result['metadata']['document_name'],
            'pages_processed': len(extraction_result['pages']),
            'sections_found': len(sections),
            'chunks_created': len(chunks),
            'chunks_uploaded': uploaded_chunks,
            'word_count': extraction_result.get('word_count', 0),
            'document_key': upload_result['document_key']
        }
        
        result_message = f"""✅ Document processing completed successfully!

📄 Document: {summary['document_name']}
📊 Statistics:
  • Pages processed: {summary['pages_processed']}
  • Sections identified: {summary['sections_found']}
  • Text chunks created: {summary['chunks_created']}
  • Chunks uploaded: {summary['chunks_uploaded']}
  • Total words: {summary['word_count']:,}

🔗 Document stored at: {summary['document_key']}

The document is now ready for chat interactions!"""
        
        logger.info(f"PDF processing completed: {summary}")
        return result_message
        
    except Exception as e:
        error_msg = f"❌ Document processing failed: {str(e)}"
        logger.error(error_msg)
        return error_msg

@tool
def check_document_status(document_name: str) -> str:
    """
    Check the processing status of a document
    
    Args:
        document_name: Name of the document to check
        
    Returns:
        str: Status information
    """
    try:
        document_uploader = DocumentUploader()
        progress = document_uploader.get_upload_progress(document_name)
        
        status_message = f"📋 Status for document: {document_name}\n\n"
        
        if progress['document_uploaded']:
            status_message += "✅ Document uploaded to S3\n"
        else:
            status_message += "❌ Document not uploaded\n"
        
        if progress['metadata_created']:
            status_message += "✅ Metadata created\n"
        else:
            status_message += "❌ Metadata not created\n"
        
        if progress['chunks_processed']:
            chunk_count = progress.get('chunk_count', 0)
            status_message += f"✅ Text chunks processed ({chunk_count} chunks)\n"
        else:
            status_message += "❌ Text chunks not processed\n"
        
        if progress['ready_for_chat']:
            status_message += "\n🎉 Document is ready for chat interactions!"
        else:
            status_message += "\n⏳ Document processing is incomplete"
        
        return status_message
        
    except Exception as e:
        return f"❌ Failed to check document status: {str(e)}"

@tool
def list_processed_documents() -> str:
    """
    List all processed documents in the knowledge base
    
    Returns:
        str: List of documents with their status
    """
    try:
        document_uploader = DocumentUploader()
        documents = document_uploader.list_uploaded_documents()
        
        if not documents:
            return "📭 No documents found in the knowledge base."
        
        result = "📚 Documents in Knowledge Base:\n\n"
        
        for i, doc in enumerate(documents, 1):
            doc_name = doc['name']
            size_mb = round(doc['size'] / (1024 * 1024), 2)
            last_modified = doc['last_modified'].strftime('%Y-%m-%d %H:%M')
            
            # Check processing status
            progress = document_uploader.get_upload_progress(doc_name)
            status = "✅ Ready" if progress['ready_for_chat'] else "⏳ Processing"
            
            result += f"{i}. {doc_name}\n"
            result += f"   Size: {size_mb} MB\n"
            result += f"   Modified: {last_modified}\n"
            result += f"   Status: {status}\n"
            
            if progress.get('chunk_count'):
                result += f"   Chunks: {progress['chunk_count']}\n"
            
            result += "\n"
        
        return result
        
    except Exception as e:
        return f"❌ Failed to list documents: {str(e)}"

@tool
def delete_document(document_name: str) -> str:
    """
    Delete a document and all its associated data from the knowledge base
    
    Args:
        document_name: Name of the document to delete
        
    Returns:
        str: Deletion result
    """
    try:
        document_uploader = DocumentUploader()
        
        # Find the document key
        documents = document_uploader.list_uploaded_documents()
        document_key = None
        
        for doc in documents:
            if document_name in doc['name'] or doc['name'] in document_name:
                document_key = doc['key']
                break
        
        if not document_key:
            return f"❌ Document '{document_name}' not found in knowledge base."
        
        # Delete the document
        result = document_uploader.delete_document(document_key)
        
        if result['success']:
            deleted_items = []
            deleted_items.append(f"Document: {result['deleted_document']}")
            deleted_items.extend([f"Metadata: {m}" for m in result['deleted_metadata']])
            deleted_items.extend([f"Chunk: {c}" for c in result['deleted_chunks']])
            
            return f"""✅ Document '{document_name}' deleted successfully!

🗑️ Deleted items:
{chr(10).join(['  • ' + item for item in deleted_items])}

The document has been completely removed from the knowledge base."""
        else:
            return f"❌ Failed to delete document: {result.get('error', 'Unknown error')}"
        
    except Exception as e:
        return f"❌ Failed to delete document: {str(e)}"

@tool
def get_storage_statistics() -> str:
    """
    Get statistics about the knowledge base storage
    
    Returns:
        str: Storage statistics
    """
    try:
        storage_manager = S3StorageManager()
        stats = storage_manager.get_storage_stats()
        
        result = f"""📊 Knowledge Base Storage Statistics

📁 Total Objects: {stats['total_objects']}
📄 Documents: {stats['documents_count']}
🧩 Text Chunks: {stats['chunks_count']}
💾 Total Size: {stats['total_size_mb']} MB ({stats['total_size_bytes']:,} bytes)

📈 Storage Health: {"✅ Healthy" if stats.get('error') is None else "❌ Issues detected"}"""

        if stats.get('error'):
            result += f"\n⚠️ Error: {stats['error']}"
        
        return result
        
    except Exception as e:
        return f"❌ Failed to get storage statistics: {str(e)}"

@tool
def validate_pdf_file(file_path: str) -> str:
    """
    Validate a PDF file before processing
    
    Args:
        file_path: Path to the PDF file to validate
        
    Returns:
        str: Validation result
    """
    try:
        pdf_processor = PDFProcessor()
        validation = pdf_processor.validate_pdf(file_path)
        
        result = f"🔍 PDF Validation Results for: {file_path}\n\n"
        
        if validation['valid']:
            result += "✅ PDF is valid and processable\n\n"
        else:
            result += "❌ PDF validation failed\n\n"
        
        result += f"📄 File readable: {'✅ Yes' if validation['readable'] else '❌ No'}\n"
        result += f"📝 Contains text: {'✅ Yes' if validation['has_text'] else '❌ No'}\n"
        result += f"📊 Page count: {validation['page_count']}\n"
        result += f"💾 File size: {round(validation['file_size'] / (1024 * 1024), 2)} MB\n"
        
        if validation['errors']:
            result += f"\n⚠️ Issues found:\n"
            for error in validation['errors']:
                result += f"  • {error}\n"
        
        if validation['valid']:
            result += "\n🚀 This PDF is ready for processing!"
        else:
            result += "\n❌ This PDF cannot be processed. Please check the issues above."
        
        return result
        
    except Exception as e:
        return f"❌ Failed to validate PDF: {str(e)}"