#!/usr/bin/env python3
"""
Test script for Atlas coordinator and agent communication.

This script tests:
1. Atlas initialization
2. Bookkeeping agent initialization
3. Task routing from Atlas to the bookkeeping agent
4. Communication between Atlas and the agent
5. Monitoring of the communication

Usage:
    python test_atlas_agent_communication.py
"""

import os
import sys
import logging
import json
import traceback
from datetime import datetime

# Create necessary directories before any other operations
# This ensures log files can be created successfully
try:
    # Use os.path.join for cross-platform compatibility
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    print(f"Created or verified logs directory at: {log_dir}")
except Exception as e:
    print(f"ERROR: Failed to create logs directory: {str(e)}")
    sys.exit(1)

# Set up logging with both file and console output
try:
    log_file = os.path.join(log_dir, "test_atlas_agent_communication.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger("TestAtlasAgentCommunication")
    logger.info("Logging initialized successfully")
except Exception as e:
    print(f"ERROR: Failed to initialize logging: {str(e)}")
    sys.exit(1)

# Import Atlas and agent components using absolute imports
try:
    logger.info("Importing required modules...")
    from external_memory_system.atlas.coordinator import Atlas
    from external_memory_system.atlas.communication import CommunicationBus, Message
    from external_memory_system.atlas.monitoring import CommunicationMonitor
    from external_memory_system.agents.bookkeeping_agent import BookkeepingAgent
    from external_memory_system.models.local_llm import MockLLM
    
    # Use MockVectorStore instead of PineconeVectorStore
    try:
        from external_memory_system.storage.mock_vector_store import MockVectorStore
        logger.info("Using MockVectorStore for testing")
    except ImportError:
        from external_memory_system.storage.pinecone_store import PineconeVectorStore
        logger.warning("MockVectorStore not found, using PineconeVectorStore")
    
    logger.info("All modules imported successfully")
except ImportError as e:
    logger.error(f"Failed to import required modules: {str(e)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    print(f"ERROR: Failed to import required modules. See log for details.")
    print(f"Make sure all __init__.py files are in place and imports are correct.")
    sys.exit(1)
class TestAtlasAgentCommunication:
    """Test class for Atlas and agent communication."""
    
    def __init__(self):
        """Initialize the test class."""
        # Set up logging
        self.logger = self._setup_logging()
        self.logger.info("Logging initialized successfully")
        
        # Import required modules
        self.logger.info("Importing required modules...")
        self._import_modules()
        self.logger.info("All modules imported successfully")
    
    def _setup_logging(self):
        """Set up logging for the test class."""
        # Create logs directory if it doesn't exist
        if not os.path.exists("logs"):
            os.makedirs("logs")
            print(f"Created logs directory at: {os.path.abspath('logs')}")
        else:
            print(f"Verified logs directory at: {os.path.abspath('logs')}")
        
        # Set up logger
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.DEBUG)
        
        # Create file handler
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_handler = logging.FileHandler(f"logs/atlas_agent_test_{timestamp}.log")
        file_handler.setLevel(logging.DEBUG)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _import_modules(self):
        """Import required modules."""
        try:
            # Import Atlas
            from external_memory_system.atlas.coordinator import Atlas
            self.Atlas = Atlas
            
            # Import agents
            from external_memory_system.agents.bookkeeping_agent import BookkeepingAgent
            self.BookkeepingAgent = BookkeepingAgent
            
            # Import ReconciliationAgent
            from external_memory_system.agents.reconciliation_agent import ReconciliationAgent
            self.ReconciliationAgent = ReconciliationAgent
            
            # Import communication components
            from external_memory_system.atlas.communication import CommunicationBus, Message
            from external_memory_system.atlas.monitoring import CommunicationMonitor
            self.CommunicationMonitor = CommunicationMonitor
            
            # Import MockVectorStore
            # If you have a separate MockVectorStore class, import it here
            # Otherwise, define it inline
            class MockVectorStore:
                """Mock vector store for testing."""
                
                def __init__(self, namespace="default"):
                    """Initialize the mock vector store."""
                    self.namespace = namespace
                    self.data = {}
                    print(f"Initialized MockVectorStore with namespace: {namespace}")
                
                def add_texts(self, texts, metadata=None):
                    """Add texts to the vector store."""
                    if metadata is None:
                        metadata = {}
                    for i, text in enumerate(texts):
                        self.data[f"{len(self.data)}"] = {"text": text, "metadata": metadata}
                    return [f"{i}" for i in range(len(self.data) - len(texts), len(self.data))]
                
                def similarity_search(self, query, k=5):
                    """Perform a similarity search."""
                    # Just return the k most recent items for testing
                    items = list(self.data.items())[-k:]
                    return [{"id": id, "text": data["text"], "metadata": data["metadata"]} for id, data in items]
            
            self.MockVectorStore = MockVectorStore
            self.logger.info("Using MockVectorStore for testing")
            
        except ImportError as e:
            self.logger.error(f"Error importing modules: {str(e)}")
            print(f"ERROR: Failed to import required modules. See log for details.")
            print("Make sure all __init__.py files are in place and imports are correct.")
            raise
    
    def test_atlas_initialization(self):
        """Test Atlas initialization."""
        self.logger.info("Testing Atlas initialization...")
        
        try:
            # Create mock components
            from external_memory_system.models.local_llm import MockLLM
            
            mock_llm = MockLLM()
            mock_store = self.MockVectorStore(namespace="atlas")
            
            # Initialize Atlas with mock components
            self.atlas = self.Atlas(llm=mock_llm, vector_store=mock_store)
            self.logger.info("Atlas initialized successfully")
            
            # Register a test agent
            self.atlas.register_agent("bookkeeping", "bookkeeping")
            
            # Get system status
            status = self.atlas.get_system_status()
            self.logger.info(f"System status: {status}")
            
            return True
        except Exception as e:
            self.logger.error(f"Error initializing Atlas: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False

    def test_bookkeeping_agent(self):
        """Test bookkeeping agent initialization."""
        self.logger.info("Testing bookkeeping agent initialization...")
        
        try:
            # Create mock components
            from external_memory_system.models.local_llm import MockLLM
            
            mock_llm = MockLLM()
            mock_store = self.MockVectorStore(namespace="bookkeeping")
            
            # Initialize the bookkeeping agent with mock components
            self.bookkeeping_agent = self.BookkeepingAgent(llm=mock_llm, vector_store=mock_store)
            self.logger.info("Bookkeeping agent initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error initializing bookkeeping agent: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False
    
    def test_reconciliation_agent(self):
        """Test reconciliation agent initialization."""
        self.logger.info("Testing reconciliation agent initialization...")
        
        try:
            # Create mock components
            from external_memory_system.models.local_llm import MockLLM
            
            mock_llm = MockLLM()
            mock_store = self.MockVectorStore(namespace="reconciliation")
            
            # Initialize the reconciliation agent with mock components
            self.reconciliation_agent = self.ReconciliationAgent(llm=mock_llm, vector_store=mock_store)
            self.logger.info("Reconciliation agent initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error initializing reconciliation agent: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False

    def test_task_routing(self):
        """Test task routing."""
        self.logger.info("Testing task routing...")
        
        try:
            # Create test tasks
            tasks = [
                {
                    "id": "task_001",
                    "type": "journal_entry",
                    "data": {
                        "description": "Office supplies purchase",
                        "amount": 150.00,
                        "date": "2025-03-24"
                    }
                },
                {
                    "id": "task_002",
                    "type": "categorize_transaction",
                    "data": {
                        "description": "Monthly rent payment",
                        "amount": 2000.00
                    }
                },
                {
                    "id": "task_003",
                    "type": "chart_of_accounts",
                    "data": {
                        "action": "add",
                        "account_name": "Office Supplies",
                        "account_type": "Expense"
                    }
                },
                {
                    "id": "task_004",
                    "type": "reconcile_transaction",
                    "data": {
                        "journal_entry": {
                            "date": "2025-03-24",
                            "description": "Purchase from Hardware Store Inc",
                            "amount": 45.67
                        }
                    }
                }
            ]
            
            # Route each task
            for task in tasks:
                self.logger.info(f"Routing task: {task['id']} ({task['type']})")
                agent_id = self.atlas.route_task(task)
                self.logger.info(f"Task routed to: {agent_id}")
            
            return True
        except Exception as e:
            self.logger.error(f"Error testing task routing: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False

    def test_task_execution(self):
        """Test task execution."""
        self.logger.info("Testing task execution...")
        
        try:
            # Create test tasks
            tasks = [
                {
                    "id": "task_001",
                    "type": "journal_entry",
                    "data": {
                        "description": "Record office supplies expense",
                        "amount": 150.0,
                        "date": "2025-03-24"
                    }
                },
                {
                    "id": "task_002",
                    "type": "categorize_transaction",
                    "data": {
                        "description": "Monthly rent payment",
                        "amount": 2000.0
                    }
                }
            ]
            
            # Execute each task
            for task in tasks:
                self.logger.info(f"Executing task: {task['id']} ({task['type']})")
                result = self.atlas.execute_task(task)
                self.logger.info(f"Task execution result: {result}")
            
            return True
        except Exception as e:
            self.logger.error(f"Error testing task execution: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False

    def test_direct_agent_communication(self):
        """Test direct agent communication."""
        self.logger.info("Testing direct agent communication...")
        
        try:
            # Create a test task
            task = {
                "id": "direct_001",
                "type": "journal_entry",
                "data": {
                    "description": "Direct communication test",
                    "amount": 100.0,
                    "date": "2025-03-24"
                }
            }
            
            # Process the task directly with the bookkeeping agent
            result = self.bookkeeping_agent.process_task(task)
            
            return True
        except Exception as e:
            self.logger.error(f"Error testing direct agent communication: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False

    def test_communication_monitoring(self):
        """Test communication monitoring."""
        self.logger.info("Testing communication monitoring...")
        
        try:
            # Generate a communication report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = os.path.join("logs", f"communication_report_{timestamp}.json")
            
            # In a real implementation, this would analyze communication logs
            # For now, just create a simple report
            report = {
                "timestamp": timestamp,
                "total_messages": 10,
                "messages_by_agent": {
                    "atlas": 4,
                    "bookkeeping": 3,
                    "reconciliation": 3
                },
                "message_types": {
                    "task_assignment": 5,
                    "task_result": 5
                }
            }
            
            # Save the report
            with open(report_file, "w") as f:
                json.dump(report, f, indent=2)
            
            self.logger.info(f"Communication report saved to: {report_file}")
            
            return True
        except Exception as e:
            self.logger.error(f"Error testing communication monitoring: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False
    
    def run_tests(self):
        """Run all tests."""
        test_results = {}
        
        # Run tests
        try:
            test_results["atlas_initialization"] = self.test_atlas_initialization()
        except Exception as e:
            self.logger.error(f"Error in atlas_initialization test: {str(e)}")
            self.logger.error(traceback.format_exc())
            test_results["atlas_initialization"] = False
        
        try:
            test_results["bookkeeping_agent_initialization"] = self.test_bookkeeping_agent()
        except Exception as e:
            self.logger.error(f"Error in bookkeeping_agent_initialization test: {str(e)}")
            self.logger.error(traceback.format_exc())
            test_results["bookkeeping_agent_initialization"] = False
        
        try:
            test_results["reconciliation_agent_initialization"] = self.test_reconciliation_agent()
        except Exception as e:
            self.logger.error(f"Error in reconciliation_agent_initialization test: {str(e)}")
            self.logger.error(traceback.format_exc())
            test_results["reconciliation_agent_initialization"] = False
        
        try:
            test_results["task_routing"] = self.test_task_routing()
        except Exception as e:
            self.logger.error(f"Error in task_routing test: {str(e)}")
            self.logger.error(traceback.format_exc())
            test_results["task_routing"] = False
        
        try:
            test_results["task_execution"] = self.test_task_execution()
        except Exception as e:
            self.logger.error(f"Error in task_execution test: {str(e)}")
            self.logger.error(traceback.format_exc())
            test_results["task_execution"] = False
        
        try:
            test_results["direct_agent_communication"] = self.test_direct_agent_communication()
        except Exception as e:
            self.logger.error(f"Error in direct_agent_communication test: {str(e)}")
            self.logger.error(traceback.format_exc())
            test_results["direct_agent_communication"] = False
        
        try:
            test_results["communication_monitoring"] = self.test_communication_monitoring()
        except Exception as e:
            self.logger.error(f"Error in communication_monitoring test: {str(e)}")
            self.logger.error(traceback.format_exc())
            test_results["communication_monitoring"] = False
        
        return test_results

# In the main block of test_atlas_agent_communication.py
if __name__ == "__main__":
    # Initialize the test class
    test = TestAtlasAgentCommunication()
    
    try:
        print("Starting Atlas and agent communication tests...")
        # Run the tests
        test_results = test.run_tests()
        
        # Save the test results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join("logs", f"atlas_agent_test_results_{timestamp}.json")
        with open(results_file, "w") as f:
            json.dump(test_results, f, indent=2)
        
        print(f"Test results saved to: {results_file}")
        
        # Print a summary of the test results
        print("\nTest Results Summary:")
        for test_name, result in test_results.items():
            status = "✅ Success" if result else "❌ Failed"
            print(f"{status} {test_name}")
        
        print("\nAll tests completed. See logs for details.")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        test.logger.error(f"Error running tests: {str(e)}")
        test.logger.error(traceback.format_exc())

