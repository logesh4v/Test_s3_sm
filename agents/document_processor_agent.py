"""
Document Processor Agent for Royal Enfield Knowledge Base
Strands agent specialized in PDF processing and document management
"""

import logging
from strands import Agent
from strands.models import BedrockModel
from config.settings import Config
from tools.document_processing_tools import (
    process_pdf_document,
    check_document_status,
    list_processed_documents,
    delete_document,
    get_storage_statistics,
    validate_pdf_file
)

logger = logging.getLogger(__name__)

# Model Configuration
model = BedrockModel(
    model_id=Config.MODEL_ID,
    region=Config.MODEL_REGION,
    temperature=Config.MODEL_TEMPERATURE,
    max_tokens=Config.MODEL_MAX_TOKENS
)

# System prompt for document processing agent
DOCUMENT_PROCESSOR_SYSTEM_PROMPT = """You are a specialized Document Processor Agent for the Royal Enfield Meteor Knowledge Base system. Your primary responsibilities are:

1. **PDF Document Processing**: Process Royal Enfield owner's manual PDFs by extracting text, creating searchable chunks, and uploading to AWS S3
2. **Document Management**: Manage uploaded documents, check processing status, and handle document lifecycle
3. **Quality Assurance**: Validate PDFs before processing and ensure successful completion
4. **Storage Management**: Monitor storage usage and maintain the knowledge base

## Key Capabilities:
- Process PDF documents into searchable text chunks
- Validate PDF files for compatibility and readability
- Check document processing status and progress
- List all documents in the knowledge base
- Delete documents and associated data
- Provide storage statistics and health information

## Guidelines:
- Always validate PDFs before processing to ensure they contain extractable text
- Provide clear progress updates during document processing
- Handle errors gracefully and provide helpful error messages
- Maintain organized storage structure in S3
- Ensure all processed documents are ready for chat interactions

## Response Style:
- Be informative and provide detailed status updates
- Use emojis to make responses more engaging and clear
- Provide specific error messages when issues occur
- Offer next steps and recommendations when appropriate

When users ask about document processing, guide them through the process step by step and ensure they understand the current status of their documents."""

# Create Document Processor Agent
document_processor_agent = Agent(
    system_prompt=DOCUMENT_PROCESSOR_SYSTEM_PROMPT,
    model=model,
    tools=[
        process_pdf_document,
        check_document_status,
        list_processed_documents,
        delete_document,
        get_storage_statistics,
        validate_pdf_file
    ],
    name="Document Processor Agent",
    description="Specialized agent for processing Royal Enfield manual PDFs and managing the knowledge base"
)

def test_document_processor_agent():
    """Test function for the document processor agent"""
    try:
        logger.info("Testing Document Processor Agent...")
        
        # Test basic functionality
        response = document_processor_agent("What can you help me with regarding document processing?")
        print(f"Agent Response: {response}")
        
        # Test storage statistics
        response = document_processor_agent("Show me the current storage statistics")
        print(f"Storage Stats: {response}")
        
        return True
        
    except Exception as e:
        logger.error(f"Document Processor Agent test failed: {e}")
        return False

if __name__ == "__main__":
    # Test the agent when run directly
    test_document_processor_agent()