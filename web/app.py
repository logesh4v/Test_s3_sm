"""
Flask Web Application for Royal Enfield Chatbot
Main web interface for user interactions
"""

import os
import logging
from flask import Flask, render_template, request, jsonify, session
from datetime import datetime
import uuid

# Import the orchestrator agent
from agents.orchestrator_agent import orchestrator_agent
from config.settings import Config

logger = logging.getLogger(__name__)

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    app.secret_key = Config.SECRET_KEY
    
    @app.route('/')
    def index():
        """Main chat interface"""
        return render_template('index.html')
    
    @app.route('/chat', methods=['POST'])
    def chat():
        """Handle chat messages"""
        try:
            data = request.get_json()
            user_message = data.get('message', '').strip()
            
            if not user_message:
                return jsonify({
                    'success': False,
                    'error': 'Empty message'
                })
            
            # Get or create session ID
            if 'session_id' not in session:
                session['session_id'] = str(uuid.uuid4())
            
            session_id = session['session_id']
            
            # Add session context to the message
            contextual_message = f"[Session: {session_id}] {user_message}"
            
            # Get response from orchestrator agent
            response = orchestrator_agent(contextual_message)
            
            return jsonify({
                'success': True,
                'response': str(response),
                'timestamp': datetime.now().isoformat(),
                'session_id': session_id
            })
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return jsonify({
                'success': False,
                'error': f'Sorry, I encountered an error: {str(e)}'
            })
    
    @app.route('/refresh-kb', methods=['POST'])
    def refresh_knowledge_base():
        """Refresh the S3 knowledge base cache"""
        try:
            refresh_request = "Clear the S3 knowledge base cache and refresh data"
            response = orchestrator_agent(refresh_request)
            
            return jsonify({
                'success': True,
                'response': str(response)
            })
            
        except Exception as e:
            logger.error(f"KB refresh error: {e}")
            return jsonify({
                'success': False,
                'error': f'Knowledge base refresh failed: {str(e)}'
            })
    
    @app.route('/status')
    def status():
        """Get system status"""
        try:
            status_request = "Show me the storage statistics and system status"
            response = orchestrator_agent(status_request)
            
            return jsonify({
                'success': True,
                'status': str(response)
            })
            
        except Exception as e:
            logger.error(f"Status error: {e}")
            return jsonify({
                'success': False,
                'error': f'Status check failed: {str(e)}'
            })
    
    @app.route('/clear-history', methods=['POST'])
    def clear_history():
        """Clear conversation history"""
        try:
            session_id = session.get('session_id', 'default')
            clear_request = f"Clear conversation history for session {session_id}"
            response = orchestrator_agent(clear_request)
            
            return jsonify({
                'success': True,
                'message': 'Conversation history cleared'
            })
            
        except Exception as e:
            logger.error(f"Clear history error: {e}")
            return jsonify({
                'success': False,
                'error': f'Failed to clear history: {str(e)}'
            })
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=Config.FLASK_DEBUG, host='0.0.0.0', port=5000)