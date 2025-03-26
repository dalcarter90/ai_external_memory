"""
Test script for communication between models using the external memory system.
"""

import os
import time
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_communication")

# Import our components
from external_memory_system.memory import HybridMemory
from external_memory_system.models import ChatGPTModel, GeminiModel
from external_memory_system.agents import MemoryAgent
from external_memory_system.agents import ReconciliationAgent


def setup_test_environment():
    """Set up the test environment with models and memory."""
    logger.info("Setting up test environment")
    
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
    
    # Initialize memory
    memory = HybridMemory()
    
    # Initialize models
    chatgpt_model = ChatGPTModel(api_key=openai_key)
    gemini_model = GeminiModel(api_key=google_key)
    
    # Initialize agent
    agent = MemoryAgent(
        memory=memory,
        chatgpt_model=chatgpt_model,
        gemini_model=gemini_model,
        run_interval=5  # Short interval for testing
    )
    
    return memory, chatgpt_model, gemini_model, agent

def on_memory_update(data: Dict[str, Any]):
    """Callback for memory updates."""
    logger.info(f"Memory update: {data}")

def on_model_communication(data: Dict[str, Any]):
    """Callback for model communication events."""
    logger.info(f"Model communication: {data['source_model']} -> {data['target_model']}")
    logger.info(f"Source response: {data['source_response'][:100]}...")
    logger.info(f"Target response: {data['target_response'][:100]}...")

def on_error(data: Dict[str, Any]):
    """Callback for error events."""
    logger.error(f"Error in agent: {data['error']} (source: {data['source']})")

def test_chatgpt_to_memory(agent: MemoryAgent):
    """Test storing ChatGPT responses in memory."""
    logger.info("=== Testing ChatGPT to Memory ===")
    
    # Add a test query to memory
    task_id = agent.add_memory(
        content="What are the key challenges in implementing external memory for AI models?",
        metadata={
            "source": "user",
            "memory_type": "short_term",
            "importance": 0.8
        }
    )
    
    logger.info(f"Added query to memory, task ID: {task_id}")
    
    # Wait for processing
    time.sleep(2)
    
    # Query memory to verify
    def query_callback(results):
        logger.info(f"Memory query returned {len(results)} results")
        for item, score in results:
            logger.info(f"Item: {item.content[:100]}... (score: {score:.4f})")
    
    agent.query_memory(
        query="challenges in external memory",
        callback=query_callback
    )
    
    # Wait for processing
    time.sleep(5)
    
    logger.info("ChatGPT to Memory test completed")

def test_gemini_to_memory(agent: MemoryAgent):
    """Test storing Gemini responses in memory."""
    logger.info("=== Testing Gemini to Memory ===")
    
    # Add a test query to memory
    task_id = agent.add_memory(
        content="How can we optimize vector databases for AI memory storage?",
        metadata={
            "source": "user",
            "memory_type": "short_term",
            "importance": 0.7
        }
    )
    
    logger.info(f"Added query to memory, task ID: {task_id}")
    
    # Wait for processing
    time.sleep(2)
    
    # Query memory to verify
    def query_callback(results):
        logger.info(f"Memory query returned {len(results)} results")
        for item, score in results:
            logger.info(f"Item: {item.content[:100]}... (score: {score:.4f})")
    
    agent.query_memory(
        query="vector database optimization",
        callback=query_callback
    )
    
    # Wait for processing
    time.sleep(5)
    
    logger.info("Gemini to Memory test completed")

def test_bidirectional_communication(agent: MemoryAgent):
    """Test bidirectional communication between ChatGPT and Gemini."""
    logger.info("=== Testing Bidirectional Communication ===")
    
    # Create a shared context
    context_id = f"test_context_{int(time.time())}"
    
    # Add initial context
    agent.add_memory(
        content="We are discussing approaches to implement external memory for AI agents that can facilitate knowledge sharing between different models.",
        metadata={
            "source": "user",
            "shared_context_id": context_id,
            "memory_type": "short_term"
        }
    )
    
    # Wait for processing
    time.sleep(2)
    
    # Test ChatGPT to Gemini communication
    logger.info("Testing ChatGPT to Gemini communication")
    agent.communicate(
        source_model="chatgpt",
        target_model="gemini",
        query="What are the advantages of using a hybrid memory approach combining vector, key-value, and graph databases?",
        context_id=context_id
    )
    
    # Wait for processing
    time.sleep(10)
    
    # Test Gemini to ChatGPT communication
    logger.info("Testing Gemini to ChatGPT communication")
    agent.communicate(
        source_model="gemini",
        target_model="chatgpt",
        query="How can we ensure data consistency across different memory types in a hybrid memory system?",
        context_id=context_id
    )
    
    # Wait for processing
    time.sleep(10)
    
    # Query the shared context to see the conversation
    def context_callback(results):
        logger.info(f"Shared context query returned {len(results)} results")
        for item, score in results:
            logger.info(f"Source: {item.source}, Content: {item.content[:100]}...")
    
    agent.query_memory(
        query=f"context_id:{context_id}",
        callback=context_callback
    )
    
    # Wait for processing
    time.sleep(5)
    
    logger.info("Bidirectional Communication test completed")

def run_tests():
    """Run all communication tests."""
    logger.info("Starting communication tests")
    
    # Set up test environment
    memory, chatgpt_model, gemini_model, agent = setup_test_environment()
    
    # Register callbacks
    agent.register_callback("on_memory_update", on_memory_update)
    agent.register_callback("on_model_communication", on_model_communication)
    agent.register_callback("on_error", on_error)
    
    # Start the agent
    agent.start()
    
    try:
        # Run tests
        test_chatgpt_to_memory(agent)
        test_gemini_to_memory(agent)
        test_bidirectional_communication(agent)
        
        logger.info("All tests completed successfully")
    
    finally:
        # Stop the agent
        agent.stop()
        logger.info("Agent stopped")
        
# Add a setup method for the reconciliation agent
def setup_reconciliation_agent(self):
    """Set up a reconciliation agent for testing."""
    self.logger.info("Testing reconciliation agent initialization...")
    vector_store = MockVectorStore(namespace="reconciliation")
    llm = MockLLM(model_name="test-model")
    self.reconciliation_agent = ReconciliationAgent(llm=llm, vector_store=vector_store)
    self.logger.info("Reconciliation agent initialized successfully")

# Add a test method for the reconciliation agent
def test_reconciliation_agent(self):
    """Test the reconciliation agent functionality."""
    self.logger.info("Testing reconciliation agent...")
    
    # Create a test task
    task = {
        "id": "task_004",
        "type": "reconcile_transaction",
        "data": {
            "journal_entry": {
                "date": "2025-03-24",
                "description": "Purchase from Hardware Store Inc by Employee1",
                "debit_account": "Office Supplies Expense",
                "credit_account": "Company Credit Card",
                "amount": 45.67,
                "reference": "Receipt-2025-03-24-Employee1"
            }
        }
    }
    
    # Process the task
    result = self.reconciliation_agent.process_task(task)
    
    # Log the result
    self.logger.info(f"Reconciliation result: {result}")
    
    # Verify the result
    assert result["status"] == "success"
    assert result["reconciliation_status"] == "reconciled"
    
    self.logger.info("Reconciliation agent test passed")
    return True

# Update the Atlas coordinator to register the reconciliation agent
def setup_atlas(self):
    """Set up Atlas for testing."""
    self.logger.info("Testing Atlas initialization...")
    vector_store = MockVectorStore(namespace="atlas")
    llm = MockLLM(model_name="test-model")
    self.atlas = Atlas(llm=llm, vector_store=vector_store)
    # Register test agents
    self.atlas.register_agent("bookkeeping", "bookkeeping")
    self.atlas.register_agent("reconciliation", "reconciliation")
    self.logger.info("Atlas initialized successfully")

# Add a test for Atlas to route tasks to the reconciliation agent
def test_atlas_reconciliation_routing(self):
    """Test Atlas routing tasks to the reconciliation agent."""
    self.logger.info("Testing Atlas routing to reconciliation agent...")
    
    # Create a test task
    task = {
        "id": "task_005",
        "type": "reconcile_transaction",
        "data": {
            "journal_entry": {
                "date": "2025-03-24",
                "description": "Purchase from Hardware Store Inc by Employee1",
                "debit_account": "Office Supplies Expense",
                "credit_account": "Company Credit Card",
                "amount": 45.67,
                "reference": "Receipt-2025-03-24-Employee1"
            }
        }
    }
    
    # Get the agent for this task
    agent_id = self.atlas.route_task(task)
    
    # Log the result
    self.logger.info(f"Task routed to: {agent_id}")
    
    # Verify the result
    assert agent_id == "reconciliation"
    
    self.logger.info("Atlas reconciliation routing test passed")
    return True

# Update the main test execution to include the new tests
def run_tests(self):
    """Run all tests."""
    test_results = {}
    
    # Run existing tests
    test_results["atlas_initialization"] = self.test_atlas_initialization()
    test_results["bookkeeping_agent_initialization"] = self.test_bookkeeping_agent()
    test_results["task_routing"] = self.test_task_routing()
    test_results["task_execution"] = self.test_task_execution()
    test_results["direct_agent_communication"] = self.test_direct_agent_communication()
    
    # Run new tests
    test_results["reconciliation_agent_initialization"] = self.setup_reconciliation_agent()
    test_results["reconciliation_agent_functionality"] = self.test_reconciliation_agent()
    test_results["atlas_reconciliation_routing"] = self.test_atlas_reconciliation_routing()
    
    # Run communication monitoring test
    test_results["communication_monitoring"] = self.test_communication_monitoring()
    
    return test_results

if __name__ == "__main__":
    run_tests()
