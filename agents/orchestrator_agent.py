"""
Orchestrator Agent for Royal Enfield Knowledge Base
Main coordination agent that routes requests to specialized agents
"""

import logging
from strands import Agent, tool
from strands.models import BedrockModel
from config.settings import Config

logger = logging.getLogger(__name__)

# Import specialized agents
from agents.retrieval_agent import retrieval_agent
from agents.chat_agent import chat_agent
from agents.s3_management_agent import s3_management_agent

# Model Configuration
model = BedrockModel(
    model_id=Config.MODEL_ID,
    region=Config.MODEL_REGION,
    temperature=Config.MODEL_TEMPERATURE,
    max_tokens=Config.MODEL_MAX_TOKENS
)

@tool
def route_to_s3_management_agent(request: str) -> str:
    """
    Route S3 document management requests to the S3 Management Agent
    
    Args:
        request: S3 management request (upload, process, delete, stats)
        
    Returns:
        str: Response from S3 Management Agent
    """
    try:
        logger.info(f"Routing to S3 Management Agent: {request}")
        response = s3_management_agent(request)
        return str(response)
    except Exception as e:
        logger.error(f"S3 management routing failed: {e}")
        return f"❌ S3 management operation failed: {str(e)}"

@tool
def route_to_knowledge_base_manager(request: str) -> str:
    """
    Route knowledge base status requests to the Retrieval Agent
    
    Args:
        request: Knowledge base status request
        
    Returns:
        str: Response from Retrieval Agent
    """
    try:
        logger.info(f"Routing to Knowledge Base Manager: {request}")
        response = retrieval_agent(request)
        return str(response)
    except Exception as e:
        logger.error(f"Knowledge base management routing failed: {e}")
        return f"❌ Knowledge base operation failed: {str(e)}"

@tool
def route_to_retrieval_agent(request: str) -> str:
    """
    Route search and retrieval requests to the Retrieval Agent
    
    Args:
        request: Search or retrieval request
        
    Returns:
        str: Response from Retrieval Agent
    """
    try:
        logger.info(f"Routing to Retrieval Agent: {request}")
        response = retrieval_agent(request)
        return str(response)
    except Exception as e:
        logger.error(f"Retrieval agent routing failed: {e}")
        return f"❌ Search failed: {str(e)}"

@tool
def route_to_chat_agent(request: str) -> str:
    """
    Route conversational requests to the Chat Agent
    
    Args:
        request: Conversational request or question
        
    Returns:
        str: Response from Chat Agent
    """
    try:
        logger.info(f"Routing to Chat Agent: {request}")
        response = chat_agent(request)
        return str(response)
    except Exception as e:
        logger.error(f"Chat agent routing failed: {e}")
        return f"❌ Chat response failed: {str(e)}"

# System prompt for orchestrator agent
ORCHESTRATOR_SYSTEM_PROMPT = """You are the Orchestrator Agent for the Royal Enfield Meteor Knowledge Base system. Your role is to analyze incoming requests and route them to the appropriate specialized agent based on the request type and intent.

## Available Specialized Agents:

### 1. S3 Management Agent (`route_to_s3_management_agent`)
**Use for:**
- PDF upload to S3
- Document processing and management
- S3 storage statistics and analytics
- Document deletion and cleanup
- Advanced search with filters
- S3 document lifecycle management

**Keywords to watch for:** upload, process, delete, storage, statistics, S3, document, PDF, manage

### 2. Knowledge Base Manager (`route_to_knowledge_base_manager`)
**Use for:**
- S3 knowledge base status and health checks
- Cache management and refresh operations
- Knowledge base readiness checks
- S3 connection status

**Keywords to watch for:** knowledge base, status, health, cache, refresh, ready

### 3. Retrieval Agent (`route_to_retrieval_agent`)
**Use for:**
- Direct search requests in the knowledge base
- Section-specific searches
- Page-specific lookups
- Search suggestions and query help
- Knowledge base overview requests
- Technical search operations

**Keywords to watch for:** search, find, lookup, section, page, overview, suggestions, knowledge base

### 4. Chat Agent (`route_to_chat_agent`)
**Use for:**
- Natural language questions about Royal Enfield Meteor
- Conversational interactions
- Questions requiring contextual responses
- General help and assistance requests
- Questions about motorcycle maintenance, specifications, troubleshooting
- Any user question that needs a comprehensive, conversational response

**Keywords to watch for:** how, what, why, when, where, help, question, problem, issue, maintenance, engine, brake, oil, troubleshoot

## Routing Decision Logic:

1. **S3 Document Management** → S3 Management Agent
   - "Upload PDF to S3"
   - "Process S3 PDF"
   - "List S3 documents"
   - "Delete document from S3"
   - "Show S3 storage statistics"
   - "Advanced search with filters"

2. **S3 Knowledge Base Status** → Knowledge Base Manager
   - "Check S3 knowledge base status"
   - "Get S3 health status"
   - "Refresh S3 cache"
   - "Clear S3 cache"

3. **Technical Search Operations** → Retrieval Agent
   - "Search for information about..."
   - "Find content in section..."
   - "Show me page 25"
   - "Get search suggestions"
   - "What's in the knowledge base?"

4. **Conversational Questions** → Chat Agent
   - "How do I change the oil?"
   - "What should I do if my engine won't start?"
   - "Tell me about brake maintenance"
   - "Help me with troubleshooting"
   - General questions requiring contextual, conversational responses

## Default Behavior:
- If the request type is unclear, route to the Chat Agent as it can handle general queries
- For ambiguous requests, choose the agent most likely to provide a helpful response
- Always route user questions about motorcycle topics to the Chat Agent

## Response Format:
- Simply return the response from the chosen agent
- Do not add additional commentary unless there's an error
- Let the specialized agents handle the formatting and presentation

Your goal is to ensure users get routed to the right specialist for the best possible assistance."""

# Create Orchestrator Agent
orchestrator_agent = Agent(
    system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
    model=model,
    tools=[
        route_to_s3_management_agent,
        route_to_knowledge_base_manager,
        route_to_retrieval_agent,
        route_to_chat_agent
    ],
    name="Orchestrator Agent",
    description="Main coordination agent that routes requests to specialized agents"
)

def test_orchestrator_agent():
    """Test function for the orchestrator agent"""
    try:
        logger.info("Testing Orchestrator Agent...")
        
        # Test routing to chat agent
        response = orchestrator_agent("How do I change the oil in my Royal Enfield Meteor?")
        print(f"Orchestrator Response (Chat): {response}")
        
        # Test routing to document processor
        response = orchestrator_agent("Show me the storage statistics")
        print(f"Orchestrator Response (Doc Processor): {response}")
        
        return True
        
    except Exception as e:
        logger.error(f"Orchestrator Agent test failed: {e}")
        return False

if __name__ == "__main__":
    # Test the agent when run directly
    test_orchestrator_agent()