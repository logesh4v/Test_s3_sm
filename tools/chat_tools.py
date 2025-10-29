"""
Chat Tools for Royal Enfield Chatbot
Custom tools for the Chat Agent to handle conversations and response generation
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from strands import tool
from utils.s3_only_knowledge_base import S3OnlyKnowledgeBase

logger = logging.getLogger(__name__)

# Conversation history storage (in production, this would be in a database)
conversation_history = {}

@tool
def generate_response_with_context(user_query: str, session_id: str = "default") -> str:
    """
    Generate a comprehensive response to user query using knowledge base context
    
    Args:
        user_query: User's question about Royal Enfield Meteor
        session_id: Session identifier for conversation history
        
    Returns:
        str: Generated response with context and sources
    """
    try:
        logger.info(f"Generating response for query: '{user_query}' (session: {session_id})")
        
        # Initialize S3-only knowledge base
        kb = S3OnlyKnowledgeBase()
        
        # Ensure knowledge base is ready
        if not kb.is_knowledge_base_ready():
            return "❌ S3 knowledge base not available. The Royal Enfield manual data must be pre-processed and stored in the S3 bucket."
        
        # Search for relevant information
        search_results = kb.search_chunks(query=user_query, max_results=8)
        
        if not search_results:
            return _generate_no_results_response(user_query, session_id)
        
        # Generate response based on search results
        if search_results:
            response = _generate_contextual_response_local(user_query, search_results)
        else:
            response = _generate_no_results_response(user_query, session_id)
        
        # Store in conversation history
        _update_conversation_history(session_id, user_query, response, {'sources': search_results})
        
        return response
        
    except Exception as e:
        error_msg = f"❌ I apologize, but I encountered an error while searching the manual: {str(e)}"
        logger.error(f"Response generation failed: {e}")
        return error_msg

def _generate_contextual_response_local(user_query: str, search_results: List[Dict[str, Any]]) -> str:
    """Generate response when relevant context is available from local KB"""
    
    if not search_results:
        return _generate_no_results_response(user_query, "default")
    
    # Calculate average confidence
    avg_score = sum(result.get('relevance_score', 0) for result in search_results) / len(search_results)
    
    if avg_score >= 0.7:
        confidence = 'high'
        confidence_emoji = '🎯'
    elif avg_score >= 0.4:
        confidence = 'medium'
        confidence_emoji = '📋'
    else:
        confidence = 'low'
        confidence_emoji = '⚠️'
    
    # Build response
    response = f"🔧 **Royal Enfield Meteor Information**\n\n"
    response += f"{confidence_emoji} **Confidence Level:** {confidence.title()}\n\n"
    
    # Add main content from top results
    response += f"**Answer:**\n"
    
    # Combine content from top 3 results
    combined_content = []
    sections_used = set()
    pages_used = set()
    
    for result in search_results[:3]:
        content = result.get('content', '')
        metadata = result.get('metadata', {})
        
        sections_used.add(metadata.get('section', 'Unknown'))
        pages_used.update(metadata.get('page_numbers', []))
        
        # Add section context
        section = metadata.get('section', 'Unknown Section')
        combined_content.append(f"**From {section}:**\n{content}")
    
    response += "\n\n".join(combined_content)
    
    # Add source information
    if sections_used:
        response += f"\n\n📚 **Sources from Royal Enfield Meteor Manual:**\n"
        for section in sorted(sections_used):
            response += f"• {section}\n"
    
    if pages_used:
        sorted_pages = sorted(pages_used)
        response += f"\n📄 **Referenced Pages:** {', '.join(map(str, sorted_pages))}\n"
    
    # Add confidence-based disclaimer
    if confidence == 'low':
        response += f"\n⚠️ **Note:** The information found has limited relevance to your question. "
        response += f"You may want to rephrase your query or consult additional resources.\n"
    elif confidence == 'medium':
        response += f"\n💡 **Note:** This information is moderately relevant. "
        response += f"If you need more specific details, try rephrasing your question.\n"
    
    # Add helpful suggestions
    response += f"\n🔍 **Need more help?**\n"
    response += f"• Ask more specific questions for better results\n"
    response += f"• Try searching by section (e.g., 'maintenance', 'troubleshooting')\n"
    response += f"• Contact a Royal Enfield dealer for technical support\n"
    
    return response

def _generate_contextual_response(user_query: str, response_context: Dict[str, Any], 
                                aggregated_context: Dict[str, Any]) -> str:
    """Generate response when relevant context is available"""
    
    confidence = response_context['confidence_level']
    sources = aggregated_context.get('sources', [])
    statistics = aggregated_context.get('statistics', {})
    
    # Build response header
    response = f"🔧 **Royal Enfield Meteor Information**\n\n"
    
    # Add confidence indicator
    confidence_emoji = {
        'high': '🎯',
        'medium': '📋',
        'low': '⚠️',
        'very_low': '❓'
    }
    
    response += f"{confidence_emoji.get(confidence, '📋')} **Confidence Level:** {confidence.title()}\n\n"
    
    # Add main content from context
    context_content = response_context['formatted_context']
    
    # Extract the main content (before source information)
    main_content = context_content.split('\n\nSource Information:')[0]
    
    response += f"**Answer:**\n{main_content}\n\n"
    
    # Add source information
    if sources:
        response += "📚 **Sources from Royal Enfield Meteor Manual:**\n"
        unique_sections = set()
        all_pages = set()
        
        for source in sources:
            section = source.get('section', 'Unknown Section')
            pages = source.get('page_numbers', [])
            unique_sections.add(section)
            all_pages.update(pages)
        
        for section in sorted(unique_sections):
            response += f"• {section}\n"
        
        if all_pages:
            sorted_pages = sorted(all_pages)
            response += f"\n📄 **Referenced Pages:** {', '.join(map(str, sorted_pages))}\n"
    
    # Add confidence-based disclaimer
    if confidence in ['low', 'very_low']:
        response += f"\n⚠️ **Note:** The information found has limited relevance to your question. "
        response += f"You may want to rephrase your query or consult additional resources.\n"
    elif confidence == 'medium':
        response += f"\n💡 **Note:** This information is moderately relevant. "
        response += f"If you need more specific details, try rephrasing your question.\n"
    
    # Add helpful suggestions
    response += f"\n🔍 **Need more help?**\n"
    response += f"• Ask more specific questions for better results\n"
    response += f"• Try searching by section (e.g., 'maintenance', 'troubleshooting')\n"
    response += f"• Contact a Royal Enfield dealer for technical support\n"
    
    return response

def _generate_no_results_response(user_query: str, session_id: str) -> str:
    """Generate response when no relevant information is found"""
    
    response = f"🔍 **Search Results for:** \"{user_query}\"\n\n"
    response += f"❌ I couldn't find specific information about this topic in the Royal Enfield Meteor owner's manual.\n\n"
    
    response += f"💡 **Here's what you can try:**\n\n"
    response += f"**1. Rephrase your question:**\n"
    response += f"• Use different keywords (e.g., 'engine oil' instead of 'lubrication')\n"
    response += f"• Be more specific (e.g., 'brake pad replacement' instead of 'brakes')\n"
    response += f"• Try simpler terms\n\n"
    
    response += f"**2. Search by category:**\n"
    response += f"• Maintenance and service procedures\n"
    response += f"• Engine specifications and troubleshooting\n"
    response += f"• Safety information and warnings\n"
    response += f"• Operating procedures\n\n"
    
    response += f"**3. Alternative resources:**\n"
    response += f"• Contact your Royal Enfield dealer\n"
    response += f"• Visit an authorized service center\n"
    response += f"• Check the Royal Enfield official website\n"
    response += f"• Consult the complete owner's manual\n\n"
    
    response += f"🤔 **Common topics I can help with:**\n"
    response += f"• Oil change procedures\n"
    response += f"• Brake maintenance\n"
    response += f"• Engine specifications\n"
    response += f"• Troubleshooting common issues\n"
    response += f"• Safety guidelines\n"
    
    return response

@tool
def get_conversation_history(session_id: str = "default", limit: int = 5) -> str:
    """
    Get recent conversation history for context
    
    Args:
        session_id: Session identifier
        limit: Maximum number of recent exchanges to return
        
    Returns:
        str: Formatted conversation history
    """
    try:
        if session_id not in conversation_history:
            return "📝 **Conversation History**\n\nNo previous conversation found. This is the start of our chat!"
        
        history = conversation_history[session_id]
        recent_history = history[-limit:] if len(history) > limit else history
        
        if not recent_history:
            return "📝 **Conversation History**\n\nNo previous conversation found."
        
        response = f"📝 **Recent Conversation History** (Last {len(recent_history)} exchanges)\n\n"
        
        for i, exchange in enumerate(recent_history, 1):
            timestamp = exchange.get('timestamp', 'Unknown time')
            user_query = exchange.get('user_query', '')
            # Truncate long responses for history display
            bot_response = exchange.get('bot_response', '')[:200] + "..." if len(exchange.get('bot_response', '')) > 200 else exchange.get('bot_response', '')
            
            response += f"**Exchange {i}** ({timestamp})\n"
            response += f"👤 **You:** {user_query}\n"
            response += f"🤖 **Bot:** {bot_response}\n\n"
        
        return response
        
    except Exception as e:
        return f"❌ Failed to retrieve conversation history: {str(e)}"

@tool
def clear_conversation_history(session_id: str = "default") -> str:
    """
    Clear conversation history for a session
    
    Args:
        session_id: Session identifier to clear
        
    Returns:
        str: Confirmation message
    """
    try:
        if session_id in conversation_history:
            del conversation_history[session_id]
            return f"✅ Conversation history cleared for session: {session_id}"
        else:
            return f"📝 No conversation history found for session: {session_id}"
            
    except Exception as e:
        return f"❌ Failed to clear conversation history: {str(e)}"

@tool
def suggest_related_questions(user_query: str) -> str:
    """
    Suggest related questions based on the user's query
    
    Args:
        user_query: User's original query
        
    Returns:
        str: List of suggested related questions
    """
    try:
        # Analyze query to determine topic area
        query_lower = user_query.lower()
        
        # Define related questions by topic
        related_questions = {
            'maintenance': [
                "How often should I change the engine oil?",
                "What type of oil should I use?",
                "How do I check the oil level?",
                "When should I replace the air filter?",
                "How do I clean the chain?"
            ],
            'engine': [
                "What are the engine specifications?",
                "How do I check engine performance?",
                "What should I do if the engine won't start?",
                "How do I check the spark plug?",
                "What is the engine displacement?"
            ],
            'brake': [
                "How do I check brake fluid level?",
                "When should I replace brake pads?",
                "How do I adjust the brake lever?",
                "What should I do if brakes feel spongy?",
                "How often should I service the brakes?"
            ],
            'troubleshooting': [
                "Why won't my motorcycle start?",
                "What should I do if the engine overheats?",
                "How do I diagnose electrical problems?",
                "Why is my motorcycle making strange noises?",
                "What should I check if performance is poor?"
            ],
            'safety': [
                "What safety gear should I wear?",
                "How do I perform a pre-ride inspection?",
                "What are the important safety warnings?",
                "How should I ride in different weather conditions?",
                "What should I do in an emergency?"
            ]
        }
        
        # Determine most relevant topic
        topic_scores = {}
        for topic, questions in related_questions.items():
            score = 0
            topic_keywords = {
                'maintenance': ['maintain', 'service', 'oil', 'filter', 'clean', 'replace', 'check'],
                'engine': ['engine', 'motor', 'start', 'performance', 'power', 'displacement'],
                'brake': ['brake', 'stop', 'pad', 'fluid', 'lever'],
                'troubleshooting': ['problem', 'issue', 'trouble', 'fix', 'diagnose', 'error'],
                'safety': ['safety', 'safe', 'gear', 'helmet', 'warning', 'caution']
            }
            
            keywords = topic_keywords.get(topic, [])
            for keyword in keywords:
                if keyword in query_lower:
                    score += 1
            
            topic_scores[topic] = score
        
        # Get the best matching topic
        best_topic = max(topic_scores, key=topic_scores.get) if topic_scores else 'maintenance'
        
        if topic_scores[best_topic] == 0:
            # No specific topic match, provide general suggestions
            suggestions = [
                "How do I perform basic maintenance?",
                "What are the engine specifications?",
                "How do I troubleshoot common problems?",
                "What safety precautions should I take?",
                "How often should I service my motorcycle?"
            ]
        else:
            suggestions = related_questions[best_topic]
        
        response = f"💡 **Related Questions You Might Ask:**\n\n"
        response += f"Based on your question about \"{user_query}\", here are some related topics:\n\n"
        
        for i, question in enumerate(suggestions, 1):
            response += f"{i}. {question}\n"
        
        response += f"\n🔍 **Tip:** Click on any question above or ask me anything about your Royal Enfield Meteor!"
        
        return response
        
    except Exception as e:
        return f"❌ Failed to generate suggestions: {str(e)}"

def _update_conversation_history(session_id: str, user_query: str, bot_response: str, 
                               context: Dict[str, Any]) -> None:
    """Update conversation history with new exchange"""
    try:
        if session_id not in conversation_history:
            conversation_history[session_id] = []
        
        exchange = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'user_query': user_query,
            'bot_response': bot_response,
            'context_used': len(context.get('sources', [])),
            'confidence': context.get('metadata', {}).get('confidence_level', 'unknown')
        }
        
        conversation_history[session_id].append(exchange)
        
        # Keep only last 20 exchanges to prevent memory issues
        if len(conversation_history[session_id]) > 20:
            conversation_history[session_id] = conversation_history[session_id][-20:]
            
    except Exception as e:
        logger.error(f"Failed to update conversation history: {e}")

@tool
def analyze_query_intent(user_query: str) -> str:
    """
    Analyze user query to understand intent and provide guidance
    
    Args:
        user_query: User's query to analyze
        
    Returns:
        str: Analysis of query intent and suggestions
    """
    try:
        query_lower = user_query.lower()
        
        # Define intent patterns
        intent_patterns = {
            'how_to': ['how to', 'how do i', 'how can i', 'steps to', 'procedure'],
            'what_is': ['what is', 'what are', 'define', 'explain'],
            'troubleshooting': ['problem', 'issue', 'trouble', 'not working', 'broken', 'fix'],
            'specifications': ['spec', 'specification', 'dimension', 'weight', 'capacity'],
            'maintenance': ['maintain', 'service', 'replace', 'change', 'clean'],
            'safety': ['safe', 'safety', 'danger', 'warning', 'caution'],
            'when': ['when', 'how often', 'frequency', 'schedule'],
            'where': ['where', 'location', 'position']
        }
        
        # Analyze intent
        detected_intents = []
        for intent, patterns in intent_patterns.items():
            for pattern in patterns:
                if pattern in query_lower:
                    detected_intents.append(intent)
                    break
        
        response = f"🧠 **Query Analysis:** \"{user_query}\"\n\n"
        
        if detected_intents:
            response += f"🎯 **Detected Intent(s):** {', '.join(detected_intents).replace('_', ' ').title()}\n\n"
            
            # Provide intent-specific guidance
            if 'how_to' in detected_intents:
                response += f"📋 **Procedure Request Detected**\n"
                response += f"I'll search for step-by-step instructions in the manual.\n\n"
            
            if 'troubleshooting' in detected_intents:
                response += f"🔧 **Troubleshooting Request Detected**\n"
                response += f"I'll look for diagnostic and repair information.\n\n"
            
            if 'specifications' in detected_intents:
                response += f"📊 **Specification Request Detected**\n"
                response += f"I'll search for technical specifications and measurements.\n\n"
            
            if 'maintenance' in detected_intents:
                response += f"🛠️ **Maintenance Request Detected**\n"
                response += f"I'll find maintenance schedules and procedures.\n\n"
        else:
            response += f"🤔 **General Query Detected**\n"
            response += f"I'll perform a broad search across all manual sections.\n\n"
        
        # Extract key terms
        import re
        words = re.findall(r'\b\w+\b', query_lower)
        key_terms = [word for word in words if len(word) > 3 and word not in ['what', 'how', 'when', 'where', 'should', 'would', 'could']]
        
        if key_terms:
            response += f"🔑 **Key Terms Identified:** {', '.join(key_terms[:5])}\n\n"
        
        response += f"🔍 **Search Strategy:**\n"
        response += f"I'll use these insights to find the most relevant information in the Royal Enfield Meteor manual."
        
        return response
        
    except Exception as e:
        return f"❌ Failed to analyze query: {str(e)}"