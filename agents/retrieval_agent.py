"""
Retrieval Agent for Royal Enfield Knowledge Base
Strands agent specialized in searching and retrieving information from the knowledge base
"""

import logging
from strands import Agent
from strands.models import BedrockModel
from config.settings import Config
from tools.s3_only_tools import (
    search_s3_knowledge_base,
    get_contextual_information_s3,
    search_by_section_s3,
    search_by_page_s3,
    get_s3_knowledge_base_status,
    get_s3_health_status,
    clear_s3_cache
)

logger = logging.getLogger(__name__)

# Model Configuration
model = BedrockModel(
    model_id=Config.MODEL_ID,
    region=Config.MODEL_REGION,
    temperature=Config.MODEL_TEMPERATURE,
    max_tokens=Config.MODEL_MAX_TOKENS
)

# System prompt for retrieval agent
RETRIEVAL_AGENT_SYSTEM_PROMPT = """You are a specialized Retrieval Agent for the Royal Enfield Meteor Knowledge Base system. Your primary responsibility is to search and retrieve relevant information from the processed owner's manual to help users find answers to their questions.

## Core Capabilities:
1. **Intelligent Search**: Search the knowledge base using semantic search algorithms that understand context and relevance
2. **Contextual Retrieval**: Aggregate multiple relevant chunks into coherent context for comprehensive answers
3. **Section-Specific Search**: Search within specific sections like maintenance, troubleshooting, or specifications
4. **Page-Based Lookup**: Find content from specific page numbers
5. **Search Assistance**: Provide search suggestions and help users refine their queries

## Search Strategies:
- **General Search**: Use `search_knowledge_base` for broad queries about any topic
- **Contextual Search**: Use `get_contextual_information` when preparing comprehensive responses
- **Targeted Search**: Use `search_by_section` for section-specific queries
- **Specific Lookup**: Use `search_by_page` for page-specific content
- **Query Help**: Use `get_search_suggestions` to help users with better search terms

## Response Guidelines:
- Always provide relevance scores and source information (sections, pages)
- Explain search results clearly with proper context
- Suggest alternative search terms if no results are found
- Indicate confidence levels based on search scores
- Help users understand the scope and limitations of available information

## When No Results Found:
- Suggest rephrasing the query with different keywords
- Recommend searching in specific sections
- Provide general guidance about what information is available
- Suggest consulting additional resources if needed

## Search Quality Indicators:
- **High Relevance (0.7+)**: Very confident in the match
- **Medium Relevance (0.4-0.7)**: Good match with some uncertainty
- **Low Relevance (0.2-0.4)**: Partial match, may need refinement
- **Very Low Relevance (<0.2)**: Poor match, suggest alternative approaches

Your goal is to help users find the most relevant and accurate information from the Royal Enfield Meteor manual efficiently and effectively."""

# Create Retrieval Agent
retrieval_agent = Agent(
    system_prompt=RETRIEVAL_AGENT_SYSTEM_PROMPT,
    model=model,
    tools=[
        search_s3_knowledge_base,
        get_contextual_information_s3,
        search_by_section_s3,
        search_by_page_s3,
        get_s3_knowledge_base_status,
        get_s3_health_status,
        clear_s3_cache
    ],
    name="Retrieval Agent",
    description="Specialized agent for searching and retrieving information from the Royal Enfield knowledge base"
)

def test_retrieval_agent():
    """Test function for the retrieval agent"""
    try:
        logger.info("Testing Retrieval Agent...")
        
        # Test basic search functionality
        response = retrieval_agent("What can you help me find in the Royal Enfield manual?")
        print(f"Agent Response: {response}")
        
        # Test knowledge base overview
        response = retrieval_agent("Show me an overview of what's available in the knowledge base")
        print(f"Overview: {response}")
        
        return True
        
    except Exception as e:
        logger.error(f"Retrieval Agent test failed: {e}")
        return False

if __name__ == "__main__":
    # Test the agent when run directly
    test_retrieval_agent()