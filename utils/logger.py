"""
Logging and Monitoring utilities for Royal Enfield Chatbot
"""

import logging
import os
from datetime import datetime
from config.settings import Config

def setup_logging():
    """Setup comprehensive logging for the application"""
    
    # Create logs directory
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Setup file handler
    log_file = os.path.join(log_dir, f'royal_enfield_chatbot_{datetime.now().strftime("%Y%m%d")}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # Console output
        ]
    )
    
    # Set specific log levels for different components
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized")
    
    return logger