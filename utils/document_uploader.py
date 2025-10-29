"""
Document Upload Manager for Royal Enfield Knowledge Base
Handles PDF upload, organization, and metadata management
"""

import os
import json
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from .s3_manager import S3StorageManager

logger = logging.getLogger(__name__)

class DocumentUploader:
    """
    Manages document upload and organization in S3
    """
    
    def __init__(self):
        """Initialize document uploader with S3 storage manager"""
        self.storage_manager = S3StorageManager()
    
    def upload_pdf_document(self, file_path: str, document_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload PDF document to S3 with proper organization and metadata
        
        Args:
            file_path: Local path to the PDF file
            document_name: Optional custom name for the document
            
        Returns:
            Dict[str, Any]: Upload result with metadata
        """
        try:
            # Validate file
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            if not file_path.lower().endswith('.pdf'):
                raise ValueError("Only PDF files are supported")
            
            # Generate document metadata
            file_stats = os.stat(file_path)
            file_hash = self._calculate_file_hash(file_path)
            
            if not document_name:
                document_name = Path(file_path).stem
            
            # Create S3 key for document
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            s3_key = f"documents/{document_name}_{timestamp}.pdf"
            
            # Prepare metadata
            metadata = {
                'original_filename': os.path.basename(file_path),
                'document_name': document_name,
                'file_size': str(file_stats.st_size),
                'file_hash': file_hash,
                'upload_timestamp': datetime.now().isoformat(),
                'document_type': 'royal_enfield_manual',
                'content_type': 'application/pdf'
            }
            
            # Upload document to S3
            logger.info(f"Uploading document: {file_path} -> {s3_key}")
            success = self.storage_manager.upload_file(
                file_path=file_path,
                s3_key=s3_key,
                metadata=metadata
            )
            
            if success:
                # Store document metadata separately
                metadata_key = f"processed/metadata/{document_name}_{timestamp}_metadata.json"
                metadata_content = json.dumps(metadata, indent=2)
                
                self.storage_manager.upload_content(
                    content=metadata_content,
                    s3_key=metadata_key,
                    content_type='application/json'
                )
                
                result = {
                    'success': True,
                    'document_key': s3_key,
                    'metadata_key': metadata_key,
                    'metadata': metadata,
                    'message': f"Successfully uploaded {document_name}"
                }
                
                logger.info(f"Document upload completed: {s3_key}")
                return result
            else:
                raise Exception("Upload failed")
                
        except Exception as e:
            logger.error(f"Failed to upload document: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Failed to upload document: {e}"
            }
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """
        Calculate SHA256 hash of the file for integrity checking
        
        Args:
            file_path: Path to the file
            
        Returns:
            str: SHA256 hash of the file
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def check_document_exists(self, document_hash: str) -> Optional[Dict[str, Any]]:
        """
        Check if a document with the same hash already exists
        
        Args:
            document_hash: SHA256 hash of the document
            
        Returns:
            Optional[Dict[str, Any]]: Existing document info if found
        """
        try:
            # List all metadata files
            metadata_objects = self.storage_manager.s3_client.list_objects(prefix='processed/metadata/')
            
            for obj in metadata_objects:
                if obj['key'].endswith('_metadata.json'):
                    try:
                        metadata_content = self.storage_manager.get_object_content(obj['key'])
                        metadata = json.loads(metadata_content)
                        
                        if metadata.get('file_hash') == document_hash:
                            return {
                                'exists': True,
                                'document_key': metadata.get('document_key'),
                                'metadata': metadata,
                                'uploaded_at': metadata.get('upload_timestamp')
                            }
                    except Exception as e:
                        logger.warning(f"Could not read metadata from {obj['key']}: {e}")
                        continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking document existence: {e}")
            return None
    
    def list_uploaded_documents(self) -> List[Dict[str, Any]]:
        """
        List all uploaded documents with their metadata
        
        Returns:
            List[Dict[str, Any]]: List of document information
        """
        try:
            documents = []
            
            # Get all documents
            document_objects = self.storage_manager.list_documents()
            
            for doc_obj in document_objects:
                if doc_obj['key'].endswith('.pdf'):
                    # Try to find corresponding metadata
                    doc_name = Path(doc_obj['key']).stem
                    metadata = self._get_document_metadata(doc_name)
                    
                    doc_info = {
                        'key': doc_obj['key'],
                        'name': doc_name,
                        'size': doc_obj['size'],
                        'last_modified': doc_obj['last_modified'],
                        'metadata': metadata
                    }
                    documents.append(doc_info)
            
            return documents
            
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return []
    
    def _get_document_metadata(self, document_name: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific document
        
        Args:
            document_name: Name of the document
            
        Returns:
            Optional[Dict[str, Any]]: Document metadata if found
        """
        try:
            # List metadata files and find matching one
            metadata_objects = self.storage_manager.s3_client.list_objects(prefix='processed/metadata/')
            
            for obj in metadata_objects:
                if document_name in obj['key'] and obj['key'].endswith('_metadata.json'):
                    try:
                        metadata_content = self.storage_manager.get_object_content(obj['key'])
                        return json.loads(metadata_content)
                    except Exception as e:
                        logger.warning(f"Could not read metadata from {obj['key']}: {e}")
                        continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting document metadata: {e}")
            return None
    
    def delete_document(self, document_key: str) -> Dict[str, Any]:
        """
        Delete a document and its associated metadata
        
        Args:
            document_key: S3 key of the document to delete
            
        Returns:
            Dict[str, Any]: Deletion result
        """
        try:
            # Extract document name from key
            doc_name = Path(document_key).stem
            
            # Delete the document
            self.storage_manager.s3_client.delete_object(document_key)
            
            # Find and delete associated metadata
            metadata_objects = self.storage_manager.s3_client.list_objects(prefix='processed/metadata/')
            deleted_metadata = []
            
            for obj in metadata_objects:
                if doc_name in obj['key'] and obj['key'].endswith('_metadata.json'):
                    self.storage_manager.s3_client.delete_object(obj['key'])
                    deleted_metadata.append(obj['key'])
            
            # Find and delete associated chunks
            chunk_objects = self.storage_manager.s3_client.list_objects(prefix='processed/chunks/')
            deleted_chunks = []
            
            for obj in chunk_objects:
                if doc_name in obj['key']:
                    self.storage_manager.s3_client.delete_object(obj['key'])
                    deleted_chunks.append(obj['key'])
            
            return {
                'success': True,
                'deleted_document': document_key,
                'deleted_metadata': deleted_metadata,
                'deleted_chunks': deleted_chunks,
                'message': f"Successfully deleted document and associated data"
            }
            
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Failed to delete document: {e}"
            }
    
    def get_upload_progress(self, document_name: str) -> Dict[str, Any]:
        """
        Get upload and processing progress for a document
        
        Args:
            document_name: Name of the document
            
        Returns:
            Dict[str, Any]: Progress information
        """
        try:
            progress = {
                'document_uploaded': False,
                'metadata_created': False,
                'chunks_processed': False,
                'ready_for_chat': False
            }
            
            # Check if document exists
            documents = self.storage_manager.list_documents()
            for doc in documents:
                if document_name in doc['key']:
                    progress['document_uploaded'] = True
                    break
            
            # Check if metadata exists
            metadata = self._get_document_metadata(document_name)
            if metadata:
                progress['metadata_created'] = True
            
            # Check if chunks exist
            chunks = self.storage_manager.list_processed_chunks()
            chunk_count = sum(1 for chunk in chunks if document_name in chunk['key'])
            if chunk_count > 0:
                progress['chunks_processed'] = True
                progress['chunk_count'] = chunk_count
            
            # Document is ready if all steps are complete
            progress['ready_for_chat'] = all([
                progress['document_uploaded'],
                progress['metadata_created'],
                progress['chunks_processed']
            ])
            
            return progress
            
        except Exception as e:
            logger.error(f"Error getting upload progress: {e}")
            return {
                'document_uploaded': False,
                'metadata_created': False,
                'chunks_processed': False,
                'ready_for_chat': False,
                'error': str(e)
            }