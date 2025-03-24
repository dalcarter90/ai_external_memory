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
    from external_memory_system.models.local_llm import LocalLLM
    
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

def test_atlas_initialization():
    """
    Test Atlas initialization.
    
    This function attempts to initialize the Atlas central coordinator
    and verify that it's working correctly by checking its system status.
    
    Returns:
        Atlas: An initialized Atlas instance if successful
        
    Raises:
        Exception: If Atlas initialization fails
    """
    logger.info("Testing Atlas initialization...")
    
    try:
        # Initialize Atlas
        atlas = Atlas()
        logger.info("Atlas initialized successfully")
        
        # Get system status
        status = atlas.get_system_status()
        logger.info(f"System status: {status}")
        
        return atlas
    except Exception as e:
        logger.error(f"Error initializing Atlas: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

def test_bookkeeping_agent_initialization():
    """
    Test bookkeeping agent initialization.
    
    This function attempts to initialize the BookkeepingAgent
    and verify that it's working correctly.
    
    Returns:
        BookkeepingAgent: An initialized BookkeepingAgent instance if successful
        
    Raises:
        Exception: If BookkeepingAgent initialization fails
    """
    logger.info("Testing bookkeeping agent initialization...")
    
    try:
        # Initialize the bookkeeping agent
        agent = BookkeepingAgent()
        logger.info("Bookkeeping agent initialized successfully")
        return agent
    except Exception as e:
        logger.error(f"Error initializing bookkeeping agent: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

def test_task_routing(atlas):
    """
    Test task routing from Atlas to agents.
    
    This function tests Atlas's ability to route different types of
    accounting tasks to the appropriate specialized agents.
    
    Args:
        atlas: An initialized Atlas instance
        
    Returns:
        list: Results of task routing tests
        
    Raises:
        Exception: If task routing fails
    """
    logger.info("Testing task routing...")
    
    # Create test tasks with different accounting scenarios
    tasks = [
        {
            "id": "task_001",
            "type": "journal_entry",
            "data": {
                "description": "Record office supplies expense",
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
                "account_name": "Marketing Expenses",
                "account_type": "Expense"
            }
        }
    ]
    
    results = []
    for task in tasks:
        try:
            logger.info(f"Routing task: {task['id']} ({task['type']})")
            agent_name = atlas.route_task(task)
            logger.info(f"Task routed to: {agent_name}")
            results.append({
                "task_id": task["id"],
                "task_type": task["type"],
                "routed_to": agent_name,
                "status": "success"
            })
        except Exception as e:
            logger.error(f"Error routing task {task['id']}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            results.append({
                "task_id": task["id"],
                "task_type": task["type"],
                "status": "error",
                "error": str(e)
            })
    
    return results

def test_task_execution(atlas):
    """
    Test task execution through Atlas.
    
    This function tests Atlas's ability to execute tasks by routing them
    to the appropriate agent and returning the results.
    
    Args:
        atlas: An initialized Atlas instance
        
    Returns:
        list: Results of task execution tests
        
    Raises:
        Exception: If task execution fails
    """
    logger.info("Testing task execution...")
    
    # Create test tasks with realistic accounting scenarios
    tasks = [
        {
            "id": "task_001",
            "type": "journal_entry",
            "data": {
                "description": "Record office supplies expense",
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
        }
    ]
    
    results = []
    for task in tasks:
        try:
            logger.info(f"Executing task: {task['id']} ({task['type']})")
            result = atlas.execute_task(task)
            logger.info(f"Task execution result: {result}")
            results.append({
                "task_id": task["id"],
                "task_type": task["type"],
                "result": result,
                "status": "success"
            })
        except Exception as e:
            logger.error(f"Error executing task {task['id']}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            results.append({
                "task_id": task["id"],
                "task_type": task["type"],
                "status": "error",
                "error": str(e)
            })
    
    return results

def test_communication_monitoring():
    """
    Test communication monitoring.
    
    This function tests the CommunicationMonitor's ability to
    generate reports on inter-agent communications.
    
    Returns:
        dict: A monitoring report
        
    Raises:
        Exception: If communication monitoring fails
    """
    logger.info("Testing communication monitoring...")
    
    try:
        # Initialize the monitor
        monitor = CommunicationMonitor()
        
        # Generate a report
        report = monitor.generate_report(hours=24)
        
        # Save the report to a file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(log_dir, f"communication_report_{timestamp}.json")
        
        with open(report_file, 'w') as f:
            json.dump(report, default=str, indent=2, fp=f)
        
        logger.info(f"Communication report saved to: {report_file}")
        return report
    except Exception as e:
        logger.error(f"Error testing communication monitoring: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

def test_direct_agent_communication():
    """
    Test direct communication with the bookkeeping agent.
    
    This function tests the BookkeepingAgent's ability to process
    tasks directly, without going through Atlas.
    
    Returns:
        dict: Result of direct task execution
        
    Raises:
        Exception: If direct agent communication fails
    """
    logger.info("Testing direct agent communication...")
    
    try:
        # Initialize the bookkeeping agent
        agent = BookkeepingAgent()
        
        # Create a test task with realistic accounting data
        task = {
            "id": "direct_task_001",
            "type": "journal_entry",
            "data": {
                "description": "Direct communication test",
                "amount": 100.00,
                "date": "2025-03-24"
            }
        }
        
        # Process the task directly
        result = agent.process_task(task)
        logger.info(f"Direct task execution result: {result}")
        
        return result
    except Exception as e:
        logger.error(f"Error testing direct agent communication: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

def run_all_tests():
    """
    Run all tests and generate a comprehensive report.
    
    This function runs all the test functions and compiles
    the results into a comprehensive report.
    
    Returns:
        dict: Comprehensive test results
        
    Raises:
        Exception: If testing fails
    """
    logger.info("Starting comprehensive testing of Atlas and agent communication...")
    
    test_results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {}
    }
    
    try:
        # Test Atlas initialization
        try:
            atlas = test_atlas_initialization()
            test_results["tests"]["atlas_initialization"] = "success"
        except Exception as e:
            test_results["tests"]["atlas_initialization"] = {
                "status": "error",
                "error": str(e)
            }
            # If Atlas initialization fails, we can't continue with tests that require Atlas
            logger.error("Atlas initialization failed, skipping tests that require Atlas")
            raise
        
        # Test bookkeeping agent initialization
        try:
            agent = test_bookkeeping_agent_initialization()
            test_results["tests"]["bookkeeping_agent_initialization"] = "success"
        except Exception as e:
            test_results["tests"]["bookkeeping_agent_initialization"] = {
                "status": "error",
                "error": str(e)
            }
            # Continue with other tests even if this fails
        
        # Test task routing
        try:
            routing_results = test_task_routing(atlas)
            test_results["tests"]["task_routing"] = {
                "status": "success",
                "results": routing_results
            }
        except Exception as e:
            test_results["tests"]["task_routing"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Test task execution
        try:
            execution_results = test_task_execution(atlas)
            test_results["tests"]["task_execution"] = {
                "status": "success",
                "results": execution_results
            }
        except Exception as e:
            test_results["tests"]["task_execution"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Test direct agent communication
        try:
            direct_result = test_direct_agent_communication()
            test_results["tests"]["direct_agent_communication"] = {
                "status": "success",
                "result": direct_result
            }
        except Exception as e:
            test_results["tests"]["direct_agent_communication"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Test communication monitoring
        try:
            monitoring_report = test_communication_monitoring()
            test_results["tests"]["communication_monitoring"] = {
                "status": "success",
                "report_summary": {
                    "total_log_entries": monitoring_report.get("total_log_entries", 0),
                    "potential_issues": len(monitoring_report.get("potential_issues", []))
                }
            }
        except Exception as e:
            test_results["tests"]["communication_monitoring"] = {
                "status": "error",
                "error": str(e)
            }
        
    except Exception as e:
        # This catches any errors not caught by the individual try/except blocks
        logger.error(f"Unexpected error during testing: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        test_results["error"] = str(e)
    
    finally:
        # Save the results regardless of success or failure
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = os.path.join(log_dir, f"atlas_agent_test_results_{timestamp}.json")
            
            with open(results_file, 'w') as f:
                json.dump(test_results, default=str, indent=2, fp=f)
            
            logger.info(f"Comprehensive test results saved to: {results_file}")
            print(f"Test results saved to: {results_file}")
        except Exception as e:
            logger.error(f"Error saving test results: {str(e)}")
            print(f"ERROR: Failed to save test results: {str(e)}")
    
    # Print a summary of the test results
    print("\nTest Results Summary:")
    for test_name, result in test_results["tests"].items():
        if isinstance(result, str) and result == "success":
            print(f"✅ {test_name}: Success")
        elif isinstance(result, dict) and result.get("status") == "success":
            print(f"✅ {test_name}: Success")
        else:
            print(f"❌ {test_name}: Failed - {result.get('error', 'Unknown error')}")
    
    return test_results

if __name__ == "__main__":
    try:
        print("Starting Atlas and agent communication tests...")
        run_all_tests()
        print("\nAll tests completed. See logs for details.")
    except Exception as e:
        print(f"\nERROR: Test execution failed: {str(e)}")
        sys.exit(1)
