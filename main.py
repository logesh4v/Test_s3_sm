"""
Royal Enfield Meteor Knowledge Base Chatbot - S3 V3
Main entry point for the application

Version: 3.0.0 (S3-V3)
Features: Real PDF Processing, Complete S3 Management, Advanced Search
Architecture: S3 Download → Local Processing → S3 Upload → Knowledge Base
"""

import os
import sys
from config.settings import Config

def main():
    """Main application entry point"""
    try:
        # Show version information
        from config.version import print_version_info
        print_version_info()
        print()
        
        # Validate configuration
        Config.validate_config()
        print("✅ Configuration validated successfully")
        
        # Check S3 knowledge base status
        print("📚 Checking S3 knowledge base...")
        from utils.s3_only_knowledge_base import S3OnlyKnowledgeBase
        
        kb = S3OnlyKnowledgeBase()
        
        if kb.is_knowledge_base_ready():
            stats = kb.get_knowledge_base_stats()
            print(f"✅ S3 knowledge base ready with {stats['total_chunks']} chunks")
            print(f"☁️ Stored in AWS S3: {stats.get('storage_stats', {}).get('total_size_mb', 0)} MB")
        else:
            print("⚠️  S3 knowledge base not available")
            print("💡 Ensure processed Royal Enfield manual data exists in your S3 bucket")
        
        # Import and start the application
        from web.app import create_app
        
        app = create_app()
        
        print("🚀 Starting Royal Enfield Chatbot...")
        print(f"📖 Royal Enfield Meteor manual loaded and ready")
        print(f"🌐 Web interface available at http://localhost:5000")
        
        # Run the Flask application
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=Config.FLASK_DEBUG
        )
        
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("💡 Please check your .env file and ensure all required variables are set")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Application Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()