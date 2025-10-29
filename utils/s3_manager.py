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