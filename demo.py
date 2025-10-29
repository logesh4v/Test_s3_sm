"""
Demo script for Royal Enfield Chatbot
Demonstrates key functionality and usage examples
"""

import os
import sys
import time
from config.settings import Config
from utils.logger import setup_logging

def main():
    """Run the demo"""
    print("🏍️ Royal Enfield Meteor Chatbot Demo")
    print("=" * 50)
    
    # Setup logging
    logger = setup_logging()
    
    try:
        # Validate configuration
        Config.validate_config()
        print("✅ Configuration validated")
        
        # Import agents after config validation
        from agents.orchestrator_agent import orchestrator_agent
        
        print("\n🤖 Testing Orchestrator Agent...")
        
        # Demo queries
        demo_queries = [
            "Show me the storage statistics",
            "How do I change the engine oil?",
            "What are the engine specifications?",
            "Search for brake maintenance information",
            "List all processed documents"
        ]
        
        for i, query in enumerate(demo_queries, 1):
            print(f"\n📝 Demo Query {i}: {query}")
            print("-" * 40)
            
            try:
                response = orchestrator_agent(query)
                print(f"🤖 Response: {response}")
            except Exception as e:
                print(f"❌ Error: {e}")
            
            time.sleep(1)  # Brief pause between queries
        
        print("\n✅ Demo completed successfully!")
        print("\n💡 To start the web interface, run: python main.py")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()