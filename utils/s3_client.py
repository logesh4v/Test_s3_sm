"""
S3 Client for Royal Enfield Knowledge Base
Handles all AWS S3 operations for document storage and retrieval
"""

import boto3
import json
import logging
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Dict, List, Optional, Any
from config.settings import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class S3Client:
    """
    S3 client for managing knowledge base storage operations
    """
    
    def __init__(self):
        """Initialize S3 client with configuration"""
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                region_name=Config.AWS_REGION
            )
            self.bucket_name = Config.S3_BUCKET_NAME
            self.region = Config.AWS_REGION
            logger.info(f"S3 client initialized for bucket: {self.bucket_name}")
            
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise ValueError("AWS credentials not configured properly")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise
    
    def create_bucket(self) -> bool:
        """
        Create S3 bucket if it doesn't exist
        
        Returns:
            bool: True if bucket exists or was created successfully
        """
        try:
            # Check if bucket already exists
            if self.bucket_exists():
                logger.info(f"Bucket {self.bucket_name} already exists")
                return True
            
            # Create bucket
            if self.region == 'us-east-1':
                # us-east-1 doesn't need LocationConstraint
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            
            logger.info(f"Successfully created bucket: {self.bucket_name}")
            
            # Set up bucket folder structure
            self._create_folder_structure()
            
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'BucketAlreadyOwnedByYou':
                logger.info(f"Bucket {self.bucket_name} already owned by you")
                return True
            elif error_code == 'BucketAlreadyExists':
                logger.error(f"Bucket name {self.bucket_name} already exists globally")
                raise ValueError(f"Bucket name {self.bucket_name} is not available")
            else:
                logger.error(f"Failed to create bucket: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error creating bucket: {e}")
            raise
    
    def bucket_exists(self) -> bool:
        """
        Check if the S3 bucket exists and is accessible
        
        Returns:
            bool: True if bucket exists and is accessible
        """
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                return False
            else:
                logger.error(f"Error checking bucket existence: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error checking bucket: {e}")
            raise
    
    def _create_folder_structure(self) -> None:
        """
        Create the folder structure in S3 bucket for organized storage
        """
        folders = [
            'documents/',
            'processed/chunks/',
            'processed/metadata/',
            'indexes/'
        ]
        
        for folder in folders:
            try:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=folder,
                    Body=''
                )
                logger.info(f"Created folder: {folder}")
            except Exception as e:
                logger.warning(f"Could not create folder {folder}: {e}")
    
    def validate_bucket_permissions(self) -> Dict[str, bool]:
        """
        Validate that the bucket has the required permissions
        
        Returns:
            Dict[str, bool]: Dictionary of permission checks
        """
        permissions = {
            'read': False,
            'write': False,
            'list': False
        }
        
        try:
            # Test list permission
            self.s3_client.list_objects_v2(Bucket=self.bucket_name, MaxKeys=1)
            permissions['list'] = True
            
            # Test write permission by creating a test object
            test_key = 'test/permission_check.txt'
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=test_key,
                Body='Permission test'
            )
            permissions['write'] = True
            
            # Test read permission
            self.s3_client.get_object(Bucket=self.bucket_name, Key=test_key)
            permissions['read'] = True
            
            # Clean up test object
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=test_key)
            
        except ClientError as e:
            logger.error(f"Permission validation failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during permission validation: {e}")
        
        return permissions
    
    def get_bucket_info(self) -> Dict[str, Any]:
        """
        Get information about the S3 bucket
        
        Returns:
            Dict[str, Any]: Bucket information including region, creation date, etc.
        """
        try:
            # Get bucket location
            location_response = self.s3_client.get_bucket_location(Bucket=self.bucket_name)
            bucket_region = location_response.get('LocationConstraint') or 'us-east-1'
            
            # Get bucket creation date (requires listing buckets)
            buckets_response = self.s3_client.list_buckets()
            creation_date = None
            for bucket in buckets_response['Buckets']:
                if bucket['Name'] == self.bucket_name:
                    creation_date = bucket['CreationDate']
                    break
            
            # Get object count and size
            objects_response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            object_count = objects_response.get('KeyCount', 0)
            
            return {
                'name': self.bucket_name,
                'region': bucket_region,
                'creation_date': creation_date,
                'object_count': object_count,
                'exists': True
            }
            
        except ClientError as e:
            logger.error(f"Failed to get bucket info: {e}")
            return {
                'name': self.bucket_name,
                'exists': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error getting bucket info: {e}")
            return {
                'name': self.bucket_name,
                'exists': False,
                'error': str(e)
            }
    
    def list_objects(self, prefix: str = '', max_keys: int = 1000) -> List[Dict[str, Any]]:
        """
        List objects in the S3 bucket with optional prefix filter
        
        Args:
            prefix: Prefix to filter objects
            max_keys: Maximum number of objects to return
            
        Returns:
            List[Dict[str, Any]]: List of object information
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            objects = []
            for obj in response.get('Contents', []):
                objects.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'etag': obj['ETag']
                })
            
            return objects
            
        except ClientError as e:
            logger.error(f"Failed to list objects: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error listing objects: {e}")
            raise
    
    def delete_object(self, key: str) -> bool:
        """
        Delete an object from S3
        
        Args:
            key: S3 object key to delete
            
        Returns:
            bool: True if deletion was successful
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info(f"Successfully deleted object: {key}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete object {key}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting object {key}: {e}")
            raise
    
    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get the current connection status and configuration
        
        Returns:
            Dict[str, Any]: Connection status information
        """
        try:
            # Test connection by listing buckets
            self.s3_client.list_buckets()
            
            bucket_info = self.get_bucket_info()
            permissions = self.validate_bucket_permissions()
            
            return {
                'connected': True,
                'region': self.region,
                'bucket': bucket_info,
                'permissions': permissions,
                'error': None
            }
            
        except Exception as e:
            return {
                'connected': False,
                'region': self.region,
                'bucket': {'name': self.bucket_name, 'exists': False},
                'permissions': {'read': False, 'write': False, 'list': False},
                'error': str(e)
            }