"""
Utility script to run the external memory system.
"""

import os
import time
import logging
import argparse
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("memory_system")

# Import our components
from external_memory_system.memory import HybridMemory
from external_memory_system.models import ChatGPTModel, GeminiModel
from external_memory_system.agents import MemoryAgent

from external_memory_system.storage.pinecone_store import PineconeVectorStore
from external_memory_system.models.ollama_pinecone_integration import PineconeOllamaIntegration

def main():
    # Initialize Pinecone store
    pinecone_store = PineconeVectorStore(
        index_name=os.getenv("PINECONE_INDEX_NAME"),
        namespace="accounting"
    )
    
    # Create integration with local LLM
    integration = PineconeOllamaIntegration(pinecone_store)
    
    # Example: Add accounting knowledge to memory
    integration.add_to_memory(
        "The accounting equation is Assets = Liabilities + Equity. This fundamental equation forms the basis of double-entry bookkeeping.",
        metadata={"category": "accounting_principles", "importance": 0.9}
    )
    
    # Example: Query memory and generate response
    query = "Explain the accounting equation"
    response = integration.generate_with_context(query)
    print(f"Query: {query}")
    print(f"Response: {response}")

if __name__ == "__main__":
    main()

def setup_environment(use_pinecone=False, pinecone_api_key=None, pinecone_environment=None):
    """Set up the environment with models and memory."""
    logger.info("Setting up environment")
    
    # Check for API keys
    openai_key = os.environ.get("OPENAI_API_KEY")
    google_key = os.environ.get("GOOGLE_API_KEY")
    
    if not openai_key:
        logger.warning("OPENAI_API_KEY not found in environment variables")
        openai_key = input("Please enter your OpenAI API key: ")
        os.environ["OPENAI_API_KEY"] = openai_key
    
    if not google_key:
        logger.warning("GOOGLE_API_KEY not found in environment variables")
        google_key = input("Please enter your Google API key: ")
        os.environ["GOOGLE_API_KEY"] = google_key
    
    # Initialize models
    chatgpt_model = ChatGPTModel(api_key=openai_key)
    gemini_model = GeminiModel(api_key=google_key)

    # Initialize memory
    memory = None

    # Set up Pinecone if requested and available
    if use_pinecone:
        try:
            from external_memory_system.memory import PineconeVectorStore

            # Get Pinecone API key and environment
            pinecone_key = pinecone_api_key or os.environ.get("PINECONE_API_KEY")
            pinecone_env = pinecone_environment or os.environ.get("PINECONE_ENVIRONMENT")

            if not pinecone_key:
                logger.warning("PINECONE_API_KEY not found")
                pinecone_key = input("Please enter your Pinecone API key: ")
                os.environ["PINECONE_API_KEY"] = pinecone_key

            if not pinecone_env:
                logger.warning("PINECONE_ENVIRONMENT not found")
                pinecone_env = input("Please enter your Pinecone environment: ")
                os.environ["PINECONE_ENVIRONMENT"] = pinecone_env

            try:
                # Initialize Pinecone vector store
                vector_store = PineconeVectorStore(
                    api_key=pinecone_key,
                    environment=pinecone_env
                )

                # Create hybrid memory with Pinecone vector store
                memory = HybridMemory(vector_store=vector_store)
                logger.info("Successfully initialized Pinecone vector store")

            except Exception as e:
                logger.error(f"Error initializing Pinecone: {e}")
                logger.warning("Falling back to in-memory vector store")
                memory = None

        except ImportError:
            logger.warning("Pinecone not available. Install with: pip install pinecone")
            logger.warning("Falling back to in-memory vector store")

    # Use default memory if not set up with Pinecone
    if memory is None:
        memory = HybridMemory()
    
    # Initialize agent
    agent = MemoryAgent(
        memory=memory,
        chatgpt_model=chatgpt_model,
        gemini_model=gemini_model,
        run_interval=30  # 30 seconds between background runs
    )
    
    return agent.memory, chatgpt_model, gemini_model, agent

def on_memory_update(data: Dict[str, Any]):
    """Callback for memory updates."""
    logger.info(f"Memory update: {data}")

def on_model_communication(data: Dict[str, Any]):
    """Callback for model communication events."""
    logger.info(f"Model communication: {data['source_model']} -> {data['target_model']}")
    logger.info(f"Source response: {data['source_response'][:100]}...")
    logger.info(f"Target response: {data['target_response'][:100]}...")
    
    # Print full responses
    print("\n" + "="*80)
    print(f"QUERY: {data.get('query', 'Unknown query')}")
    print("-"*80)
    print(f"{data['source_model'].upper()} RESPONSE:")
    print(data['source_response'])
    print("-"*80)
    print(f"{data['target_model'].upper()} RESPONSE:")
    print(data['target_response'])
    print("="*80 + "\n")

def on_error(data: Dict[str, Any]):
    """Callback for error events."""
    logger.error(f"Error in agent: {data['error']} (source: {data['source']})")

def interactive_mode(agent: MemoryAgent):
    """Run the system in interactive mode."""
    logger.info("Starting interactive mode")
    
    # Create a shared context for this session
    context_id = f"interactive_session_{int(time.time())}"
    
    # Add initial context
    agent.add_memory(
        content="This is an interactive session with the external memory system for AI models.",
        metadata={
            "source": "system",
            "shared_context_id": context_id,
            "memory_type": "short_term"
        }
    )
    
    print("\nExternal Memory System for AI Models")
    print("===================================")
    print("Type 'exit' to quit, 'help' for commands\n")
    
    while True:
        try:
            command = input("\nEnter command or query: ").strip()
            
            if not command:
                continue
            
            if command.lower() == 'exit':
                print("Exiting interactive mode...")
                break
            
            if command.lower() == 'help':
                print("\nAvailable commands:")
                print("  query <text>     - Search memory for relevant items")
                print("  chatgpt <text>   - Get response from ChatGPT")
                print("  gemini <text>    - Get response from Gemini")
                print("  chat <text>      - Get responses from both models")
                print("  help             - Show this help message")
                print("  exit             - Exit interactive mode")
                continue
            
            if command.lower().startswith('query '):
                query = command[6:].strip()
                print(f"Searching memory for: {query}")
                
                def query_callback(results):
                    print(f"\nFound {len(results)} results:")
                    for i, (item, score) in enumerate(results, 1):
                        source = item.source or "unknown"
                        print(f"{i}. [{source}] ({score:.2f}): {item.content[:100]}...")
                
                agent.query_memory(query=query, callback=query_callback)
            
            elif command.lower().startswith('chatgpt '):
                query = command[8:].strip()
                print(f"Asking ChatGPT: {query}")
                
                # Add to memory
                agent.add_memory(
                    content=query,
                    metadata={
                        "source": "user",
                        "shared_context_id": context_id,
                        "memory_type": "short_term"
                    }
                )
                
                # Get response from ChatGPT only
                def response_callback(results):
                    if results and len(results) > 0:
                        print("\nChatGPT response:")
                        print(results[0][0].content)
                
                # Use the agent's query mechanism
                agent.communicate(
                    source_model="chatgpt",
                    target_model="chatgpt",  # Same model for single-model query
                    query=query,
                    context_id=context_id
                )
            
            elif command.lower().startswith('gemini '):
                query = command[7:].strip()
                print(f"Asking Gemini: {query}")
                
                # Add to memory
                agent.add_memory(
                    content=query,
                    metadata={
                        "source": "user",
                        "shared_context_id": context_id,
                        "memory_type": "short_term"
                    }
                )
                
                # Get response from Gemini only
                agent.communicate(
                    source_model="gemini",
                    target_model="gemini",  # Same model for single-model query
                    query=query,
                    context_id=context_id
                )
            
            elif command.lower().startswith('chat '):
                query = command[5:].strip()
                print(f"Asking both models: {query}")
                
                # Add to memory
                agent.add_memory(
                    content=query,
                    metadata={
                        "source": "user",
                        "shared_context_id": context_id,
                        "memory_type": "short_term"
                    }
                )
                
                # Get responses from both models
                print("Processing... (this may take a moment)")
                agent.communicate(
                    source_model="chatgpt",
                    target_model="gemini",
                    query=query,
                    context_id=context_id
                )
            
            else:
                # Treat as a chat query by default
                print(f"Asking both models: {command}")
                
                # Add to memory
                agent.add_memory(
                    content=command,
                    metadata={
                        "source": "user",
                        "shared_context_id": context_id,
                        "memory_type": "short_term"
                    }
                )
                
                # Get responses from both models
                print("Processing... (this may take a moment)")
                agent.communicate(
                    source_model="chatgpt",
                    target_model="gemini",
                    query=command,
                    context_id=context_id
                )
            
            # Wait a bit for background processing
            time.sleep(1)
        
        except KeyboardInterrupt:
            print("\nInterrupted by user. Exiting...")
            break
        
        except Exception as e:
            logger.error(f"Error in interactive mode: {e}")
            print(f"Error: {e}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="External Memory System for AI Models")
    parser.add_argument("--test", action="store_true", help="Run communication tests")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--use-pinecone", action="store_true", help="Use Pinecone for vector storage")
    parser.add_argument("--pinecone-api-key", help="Pinecone API key")
    parser.add_argument("--pinecone-environment", help="Pinecone environment")

    args = parser.parse_args()
    
    # Set up environment
    memory, chatgpt_model, gemini_model, agent = setup_environment(
        use_pinecone=args.use_pinecone,
        pinecone_api_key=args.pinecone_api_key,
        pinecone_environment=args.pinecone_environment
    )
    
    # Register callbacks
    agent.register_callback("on_memory_update", on_memory_update)
    agent.register_callback("on_model_communication", on_model_communication)
    agent.register_callback("on_error", on_error)
    
    # Start the agent
    agent.start()
    
    try:
        if args.test:
            # Import and run tests
            from external_memory_system.test_communication import run_tests
            run_tests()
        elif args.interactive:
            # Run in interactive mode
            interactive_mode(agent)
        else:
            # Default to interactive mode
            interactive_mode(agent)

    finally:
        # Stop the agent
        agent.stop()
        logger.info("Agent stopped")

if __name__ == "__main__":
    main()
