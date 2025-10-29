"""
S3 Storage Manager for Royal Enfield Knowledge Base
High-level interface for S3 operations with error handling and retry logic
"""

import time
import json
import logging
from typing import Dict, List, Optional, Any, Union
from botocore.exceptions import ClientError
from .s3_client import S3Client

logger = logging.getLogger(__name__)

class S3StorageManager:
    """
    High-level S3 storage manager with retry logic and error handling
    """
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Initialize S3 Storage Manager
        
        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retry attempts in seconds
        """
        self.s3_client = S3Client()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Check bucket exists (don't create automatically)
        self._check_bucket()
    
    def _check_bucket(self) -> None:
        """Check if S3 bucket exists and is accessible"""
        try:
            logger.info("Checking S3 bucket access...")
            
            # Check if bucket exists
            if not self.s3_client.bucket_exists():
                logger.warning(f"S3 bucket '{self.s3_client.bucket_name}' does not exist or is not accessible")
                return
            
            # Validate permissions
            permissions = self.s3_client.validate_bucket_permissions()
            if not all(permissions.values()):
                missing_perms = [k for k, v in permissions.items() if not v]
                logger.warning(f"Missing S3 permissions: {missing_perms}")
            
            logger.info("S3 bucket access verified")
            
        except Exception as e:
            logger.warning(f"S3 bucket check failed: {e}")
            # Don't raise exception, just log warning
    
    def _retry_operation(self, operation, *args, **kwargs):
        """
        Execute operation with retry logic
        
        Args:
            operation: Function to execute
            *args: Arguments for the operation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            Result of the operation
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    logger.warning(f"Operation failed (attempt {attempt + 1}), retrying in {self.retry_delay}s: {e}")
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error(f"Operation failed after {self.max_retries + 1} attempts: {e}")
        
        raise last_exception
    
    def upload_file(self, file_path: str, s3_key: str, metadata: Optional[Dict[str, str]] = None) -> bool:
        """
        Upload a file to S3 with retry logic
        
        Args:
            file_path: Local path to the file
            s3_key: S3 key (path) for the uploaded file
            metadata: Optional metadata to attach to the file
            
        Returns:
            bool: True if upload was successful
        """
        def _upload():
            extra_args = {}
            if metadata:
                extra_args['Metadata'] = metadata
            
            self.s3_client.s3_client.upload_file(
                file_path,
                self.s3_client.bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )
            logger.info(f"Successfully uploaded {file_path} to s3://{self.s3_client.bucket_name}/{s3_key}")
            return True
        
        return self._retry_operation(_upload)
    
    def upload_content(self, content: Union[str, bytes], s3_key: str, 
                      content_type: str = 'text/plain', metadata: Optional[Dict[str, str]] = None) -> bool:
        """
        Upload content directly to S3
        
        Args:
            content: Content to upload (string or bytes)
            s3_key: S3 key (path) for the uploaded content
            content_type: MIME type of the content
            metadata: Optional metadata to attach
            
        Returns:
            bool: True if upload was successful
        """
        def _upload():
            extra_args = {'ContentType': content_type}
            if metadata:
                extra_args['Metadata'] = metadata
            
            self.s3_client.s3_client.put_object(
                Bucket=self.s3_client.bucket_name,
                Key=s3_key,
                Body=content,
                **extra_args
            )
            logger.info(f"Successfully uploaded content to s3://{self.s3_client.bucket_name}/{s3_key}")
            return True
        
        return self._retry_operation(_upload)
    
    def download_file(self, s3_key: str, local_path: str) -> bool:
        """
        Download a file from S3
        
        Args:
            s3_key: S3 key of the file to download
            local_path: Local path to save the file
            
        Returns:
            bool: True if download was successful
        """
        def _download():
            self.s3_client.s3_client.download_file(
                self.s3_client.bucket_name,
                s3_key,
                local_path
            )
            logger.info(f"Successfully downloaded s3://{self.s3_client.bucket_name}/{s3_key} to {local_path}")
            return True
        
        return self._retry_operation(_download)
    
    def get_object_content(self, s3_key: str) -> str:
        """
        Get content of an S3 object as string
        
        Args:
            s3_key: S3 key of the object
            
        Returns:
            str: Content of the object
        """
        def _get_content():
            response = self.s3_client.s3_client.get_object(
                Bucket=self.s3_client.bucket_name,
                Key=s3_key
            )
            content = response['Body'].read().decode('utf-8')
            logger.info(f"Successfully retrieved content from s3://{self.s3_client.bucket_name}/{s3_key}")
            return content
        
        return self._retry_operation(_get_content)
    
    def get_object_metadata(self, s3_key: str) -> Dict[str, Any]:
        """
        Get metadata of an S3 object
        
        Args:
            s3_key: S3 key of the object
            
        Returns:
            Dict[str, Any]: Object metadata
        """
        def _get_metadata():
            response = self.s3_client.s3_client.head_object(
                Bucket=self.s3_client.bucket_name,
                Key=s3_key
            )
            return {
                'size': response.get('ContentLength'),
                'last_modified': response.get('LastModified'),
                'content_type': response.get('ContentType'),
                'metadata': response.get('Metadata', {}),
                'etag': response.get('ETag')
            }
        
        return self._retry_operation(_get_metadata)
    
    def object_exists(self, s3_key: str) -> bool:
        """
        Check if an object exists in S3
        
        Args:
            s3_key: S3 key to check
            
        Returns:
            bool: True if object exists
        """
        try:
            self.s3_client.s3_client.head_object(
                Bucket=self.s3_client.bucket_name,
                Key=s3_key
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all documents in the documents folder
        
        Returns:
            List[Dict[str, Any]]: List of document information
        """
        return self.s3_client.list_objects(prefix='documents/')
    
    def list_processed_chunks(self) -> List[Dict[str, Any]]:
        """
        List all processed chunks
        
        Returns:
            List[Dict[str, Any]]: List of chunk information
        """
        return self.s3_client.list_objects(prefix='processed/chunks/')
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics
        
        Returns:
            Dict[str, Any]: Storage statistics
        """
        try:
            documents = self.list_documents()
            chunks = self.list_processed_chunks()
            
            total_size = sum(obj['size'] for obj in documents + chunks)
            
            return {
                'total_objects': len(documents) + len(chunks),
                'documents_count': len(documents),
                'chunks_count': len(chunks),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {
                'total_objects': 0,
                'documents_count': 0,
                'chunks_count': 0,
                'total_size_bytes': 0,
                'total_size_mb': 0,
                'error': str(e)
            }
    
    def cleanup_test_objects(self) -> int:
        """
        Clean up any test objects that might have been created
        
        Returns:
            int: Number of objects cleaned up
        """
        try:
            test_objects = self.s3_client.list_objects(prefix='test/')
            count = 0
            
            for obj in test_objects:
                self.s3_client.delete_object(obj['key'])
                count += 1
            
            logger.info(f"Cleaned up {count} test objects")
            return count
            
        except Exception as e:
            logger.error(f"Failed to cleanup test objects: {e}")
            return 0
    
    def upload_pdf_document(self, pdf_file_path: str, document_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload a PDF document to S3
        
        Args:
            pdf_file_path: Local path to the PDF file
            document_name: Optional custom name for the document
            
        Returns:
            Dict[str, Any]: Upload result
        """
        try:
            import os
            from datetime import datetime
            
            # Generate document name if not provided
            if not document_name:
                document_name = os.path.splitext(os.path.basename(pdf_file_path))[0]
            
            # Create S3 key
            s3_key = f"documents/{document_name}.pdf"
            
            # Get file size
            file_size = os.path.getsize(pdf_file_path)
            
            # Upload with metadata
            metadata = {
                'document_name': document_name,
                'upload_time': datetime.utcnow().isoformat(),
                'original_filename': os.path.basename(pdf_file_path)
            }
            
            success = self.upload_file(pdf_file_path, s3_key, metadata)
            
            if success:
                return {
                    'success': True,
                    'document_name': document_name,
                    's3_key': s3_key,
                    'file_size_mb': round(file_size / (1024 * 1024), 2),
                    'upload_time': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': 'Upload failed'
                }
                
        except Exception as e:
            logger.error(f"Failed to upload PDF document: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_pdf_document(self, document_name: str) -> Dict[str, Any]:
        """
        Process a PDF document stored in S3 - REAL processing with local download
        
        Args:
            document_name: Name of the document to process
            
        Returns:
            Dict[str, Any]: Processing result
        """
        try:
            import os
            import tempfile
            import json
            from datetime import datetime
            from utils.pdf_processor import PDFProcessor
            from utils.text_chunker import TextChunker
            
            logger.info(f"Starting REAL PDF processing for: {document_name}")
            
            # Check if document exists in S3
            s3_key = f"documents/{document_name}.pdf"
            if not self.object_exists(s3_key):
                return {
                    'success': False,
                    'error': f'Document {document_name} not found in S3'
                }
            
            # Create temporary file for download
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_pdf_path = temp_file.name
            
            try:
                # Download PDF from S3
                logger.info(f"Downloading PDF from S3: {s3_key}")
                self.download_file(s3_key, temp_pdf_path)
                
                # Initialize processors
                pdf_processor = PDFProcessor()
                text_chunker = TextChunker()
                
                # Extract text from PDF
                logger.info("Extracting text from PDF...")
                extraction_result = pdf_processor.extract_text_from_pdf(temp_pdf_path)
                
                if not extraction_result['success']:
                    return {
                        'success': False,
                        'error': f"PDF text extraction failed: {extraction_result.get('error', 'Unknown error')}"
                    }
                
                full_text = extraction_result['text']
                pages_data = extraction_result['pages']
                
                if not full_text.strip():
                    return {
                        'success': False,
                        'error': 'PDF contains no extractable text'
                    }
                
                # Extract sections
                logger.info("Extracting sections...")
                sections = pdf_processor.extract_sections(full_text, pages_data)
                
                # Create chunks
                logger.info("Creating text chunks...")
                chunks = text_chunker.chunk_document(
                    text=full_text,
                    pages_data=pages_data,
                    sections=sections,
                    document_name=document_name
                )
                
                if not chunks:
                    return {
                        'success': False,
                        'error': 'Failed to create text chunks'
                    }
                
                # Upload chunks to S3
                logger.info(f"Uploading {len(chunks)} chunks to S3...")
                uploaded_chunks = 0
                total_storage_size = 0
                
                for chunk in chunks:
                    chunk_id = chunk.get('chunk_id', f"{document_name}_chunk_{uploaded_chunks}")
                    chunk_s3_key = f"processed/chunks/{chunk_id}.json"
                    
                    # Convert chunk to JSON
                    chunk_json = json.dumps(chunk, indent=2, default=str)
                    chunk_size = len(chunk_json.encode('utf-8'))
                    total_storage_size += chunk_size
                    
                    # Upload chunk to S3
                    success = self.upload_content(
                        content=chunk_json,
                        s3_key=chunk_s3_key,
                        content_type='application/json',
                        metadata={
                            'document_name': document_name,
                            'chunk_index': str(chunk.get('metadata', {}).get('chunk_index', uploaded_chunks)),
                            'processed_at': datetime.utcnow().isoformat()
                        }
                    )
                    
                    if success:
                        uploaded_chunks += 1
                    else:
                        logger.warning(f"Failed to upload chunk: {chunk_id}")
                
                # Create and upload document metadata
                doc_metadata = {
                    'document_name': document_name,
                    'processed_at': datetime.utcnow().isoformat(),
                    'total_pages': len(pages_data),
                    'total_sections': len(sections),
                    'total_chunks': uploaded_chunks,
                    'total_words': sum(chunk.get('metadata', {}).get('word_count', 0) for chunk in chunks),
                    'source_file': f"{document_name}.pdf",
                    'processing_method': 'local_with_s3_storage',
                    'sections': [section.get('title', 'Unknown') for section in sections]
                }
                
                metadata_s3_key = f"processed/metadata/{document_name}_metadata.json"
                metadata_json = json.dumps(doc_metadata, indent=2, default=str)
                
                self.upload_content(
                    content=metadata_json,
                    s3_key=metadata_s3_key,
                    content_type='application/json',
                    metadata={
                        'document_name': document_name,
                        'type': 'document_metadata',
                        'processed_at': datetime.utcnow().isoformat()
                    }
                )
                
                logger.info(f"Successfully processed {document_name}: {uploaded_chunks} chunks uploaded")
                
                return {
                    'success': True,
                    'total_chunks': uploaded_chunks,
                    'total_words': doc_metadata['total_words'],
                    'sections_count': len(sections),
                    'storage_size_mb': round(total_storage_size / (1024 * 1024), 2),
                    'processing_method': 'real_local_processing',
                    'sections': [section.get('title', 'Unknown') for section in sections[:5]]  # First 5 sections
                }
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_pdf_path):
                    os.unlink(temp_pdf_path)
                    
        except Exception as e:
            logger.error(f"Failed to process PDF document: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_document(self, document_name: str) -> Dict[str, Any]:
        """
        Delete a document and all its processed data from S3
        
        Args:
            document_name: Name of the document to delete
            
        Returns:
            Dict[str, Any]: Deletion result
        """
        try:
            deleted_objects = []
            total_size = 0
            
            # Delete original PDF
            pdf_key = f"documents/{document_name}.pdf"
            if self.object_exists(pdf_key):
                metadata = self.get_object_metadata(pdf_key)
                total_size += metadata.get('size', 0)
                self.s3_client.delete_object(pdf_key)
                deleted_objects.append(pdf_key)
            
            # Delete processed chunks
            chunks = self.s3_client.list_objects(prefix=f"processed/chunks/{document_name}_")
            for chunk in chunks:
                total_size += chunk.get('size', 0)
                self.s3_client.delete_object(chunk['key'])
                deleted_objects.append(chunk['key'])
            
            # Delete metadata
            metadata_key = f"processed/metadata/{document_name}_metadata.json"
            if self.object_exists(metadata_key):
                metadata = self.get_object_metadata(metadata_key)
                total_size += metadata.get('size', 0)
                self.s3_client.delete_object(metadata_key)
                deleted_objects.append(metadata_key)
            
            return {
                'success': True,
                'chunks_deleted': len([obj for obj in deleted_objects if 'chunks/' in obj]),
                'storage_freed_mb': round(total_size / (1024 * 1024), 2),
                'deleted_objects': deleted_objects
            }
            
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_storage_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive storage statistics
        
        Returns:
            Dict[str, Any]: Detailed storage statistics
        """
        try:
            from datetime import datetime
            
            # Get basic stats
            basic_stats = self.get_storage_stats()
            
            # Get documents
            documents = self.list_documents()
            processed_objects = self.s3_client.list_objects(prefix='processed/')
            
            # Count processed documents
            processed_docs = set()
            for obj in processed_objects:
                if 'chunks/' in obj['key']:
                    # Extract document name from chunk filename
                    filename = obj['key'].split('/')[-1]
                    if '_chunk_' in filename:
                        doc_name = filename.split('_chunk_')[0]
                        processed_docs.add(doc_name)
            
            # Calculate sizes
            docs_size = sum(obj.get('size', 0) for obj in documents)
            processed_size = sum(obj.get('size', 0) for obj in processed_objects)
            
            # Estimate costs (rough AWS S3 pricing)
            total_gb = (docs_size + processed_size) / (1024 * 1024 * 1024)
            estimated_cost = total_gb * 0.023  # ~$0.023 per GB/month for S3 Standard
            
            return {
                'bucket_name': self.s3_client.bucket_name,
                'region': self.s3_client.region,
                'total_documents': len(documents),
                'pdf_count': len([d for d in documents if d['key'].endswith('.pdf')]),
                'processed_count': len(processed_docs),
                'total_size_mb': round((docs_size + processed_size) / (1024 * 1024), 2),
                'documents_size_mb': round(docs_size / (1024 * 1024), 2),
                'processed_size_mb': round(processed_size / (1024 * 1024), 2),
                'metadata_size_mb': 0.1,  # Estimated
                'total_chunks': basic_stats.get('chunks_count', 0),
                'total_words': 0,  # Would need to calculate from processed data
                'sections_count': 0,  # Would need to calculate from processed data
                'estimated_cost_usd': round(estimated_cost, 2),
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage statistics: {e}")
            return {
                'bucket_name': 'unknown',
                'region': 'unknown',
                'total_documents': 0,
                'pdf_count': 0,
                'processed_count': 0,
                'total_size_mb': 0,
                'documents_size_mb': 0,
                'processed_size_mb': 0,
                'metadata_size_mb': 0,
                'total_chunks': 0,
                'total_words': 0,
                'sections_count': 0,
                'estimated_cost_usd': 0,
                'last_updated': datetime.utcnow().isoformat(),
                'error': str(e)
            }
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get comprehensive health status of S3 storage
        
        Returns:
            Dict[str, Any]: Health status information
        """
        try:
            connection_status = self.s3_client.get_connection_status()
            storage_stats = self.get_storage_stats()
            
            return {
                'healthy': connection_status['connected'] and all(connection_status['permissions'].values()),
                'connection': connection_status,
                'storage': storage_stats,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Failed to get health status: {e}")
            return {
                'healthy': False,
                'error': str(e),
                'timestamp': time.time()
            }

# Create alias for backward compatibility
S3Manager = S3StorageManager