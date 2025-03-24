# external_memory_system/atlas/coordinator.py
import logging
from typing import Dict, Any, List, Optional
import os
import sys

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.local_llm import LocalLLM
from storage.pinecone_store import PineconeVectorStore
from agents.bookkeeping_agent import BookkeepingAgent
# Import other agents as they are implemented

class Atlas:
    """
    Atlas central coordinator for the accounting agent system.
    Acts as the "brain" that manages specialized accounting agents.
    """
    
    def __init__(self, llm: Optional[LocalLLM] = None, vector_store: Optional[PineconeVectorStore] = None):
        """
        Initialize the Atlas coordinator.
        
        Args:
            llm: The language model to use for decision making
            vector_store: The vector store for knowledge retrieval
        """
        self.llm = llm or self._initialize_llm()
        self.vector_store = vector_store or self._initialize_vector_store()
        self.agents = {}  # Dictionary of available specialized agents
        self.state = {}   # Current system state
        self.logger = self._setup_logger()
        
        # Register default agents
        self._register_default_agents()
    
    def _initialize_llm(self) -> LocalLLM:
        """Initialize the language model."""
        # Use the same initialization as in your existing code
        return LocalLLM()
    
    def _initialize_vector_store(self):
        """Initialize the vector store."""
        try:
            # First try to import and use MockVectorStore for testing
            from external_memory_system.storage.mock_vector_store import MockVectorStore
            return MockVectorStore(namespace="atlas")
        except ImportError:
            # Fall back to PineconeVectorStore for production
            return PineconeVectorStore(namespace="atlas")
    
    def _setup_logger(self):
        """Set up enhanced logging for communication monitoring."""
        logger = logging.getLogger("Atlas")
        logger.setLevel(logging.DEBUG)
        
        # Ensure log directory exists
        os.makedirs("logs", exist_ok=True)
        
        # File handler for detailed logs
        file_handler = logging.FileHandler("logs/atlas_communications.log")
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler for important messages
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter and add to handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _register_default_agents(self):
        """Register the default set of agents."""
        # Initialize and register the bookkeeping agent
        bookkeeping_agent = BookkeepingAgent(self.llm, self.vector_store)
        self.register_agent("bookkeeping", bookkeeping_agent)
        
        # Add other agents as they are implemented
    
    def register_agent(self, agent_name: str, agent_instance: Any):
        """Register a specialized agent with Atlas."""
        self.agents[agent_name] = agent_instance
        self.logger.info(f"Registered agent: {agent_name}")
    
    def route_task(self, task: Dict) -> str:
        """
        Determine which agent should handle a given task.
        
        Args:
            task: The task to route
            
        Returns:
            The name of the agent that should handle the task
        """
        task_type = task.get("type")
        self.logger.debug(f"Routing task of type: {task_type}")
        
        # Use the LLM to make routing decisions for complex tasks
        if task_type in ["complex", "unknown"]:
            prompt = f"""
            You are Atlas, the central coordinator for an accounting agent system.
            You need to decide which specialized agent should handle this task:
            
            Task: {task}
            
            Available agents:
            {', '.join(self.agents.keys())}
            
            Which agent should handle this task? Respond with just the agent name.
            """
            
            response = self.llm.generate(prompt)
            agent_name = response.strip().lower()
            
            if agent_name in self.agents:
                self.logger.info(f"LLM routed task to: {agent_name}")
                return agent_name
            else:
                self.logger.warning(f"LLM suggested invalid agent: {agent_name}")
                # Fall back to default routing
        
        # Simple routing logic for common task types
        if task_type == "journal_entry":
            return "bookkeeping"
        elif task_type == "invoice":
            return "accounts_receivable"
        elif task_type == "bill":
            return "accounts_payable"
        elif task_type == "reconciliation":
            return "reconciliation"
        elif task_type == "report":
            return "financial_reporting"
        else:
            self.logger.warning(f"Unknown task type: {task_type}, routing to bookkeeping")
            return "bookkeeping"  # Default to bookkeeping for unknown tasks
    
    def execute_task(self, task: Dict) -> Dict:
        """
        Execute a task by routing it to the appropriate agent.
        
        Args:
            task: The task to execute
            
        Returns:
            The result of the task execution
        """
        agent_name = self.route_task(task)
        
        if agent_name not in self.agents:
            self.logger.error(f"Agent {agent_name} not registered")
            return {"status": "error", "message": f"Agent {agent_name} not available"}
        
        # Log the communication
        self.logger.info(f"Sending task to {agent_name} agent")
        self.logger.debug(f"Task details: {task}")
        
        # Execute the task on the appropriate agent
        try:
            result = self.agents[agent_name].process_task(task)
            self.logger.info(f"Received result from {agent_name} agent")
            self.logger.debug(f"Result details: {result}")
            
            # Update system state with task result
            self._update_state(task, result, agent_name)
            
            return result
        except Exception as e:
            self.logger.error(f"Error executing task on {agent_name} agent: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _update_state(self, task: Dict, result: Dict, agent_name: str):
        """Update the system state with task results."""
        # Implement state tracking logic here
        task_id = task.get("id", "unknown")
        
        if "tasks" not in self.state:
            self.state["tasks"] = {}
        
        self.state["tasks"][task_id] = {
            "task": task,
            "result": result,
            "agent": agent_name,
            "status": result.get("status", "unknown")
        }
    
    def get_system_status(self) -> Dict:
        """
        Get the current status of the entire system.
        
        Returns:
            A dictionary containing system status information
        """
        status = {
            "agents": list(self.agents.keys()),
            "state": self.state,
            "tasks_completed": len(self.state.get("tasks", {})),
            "tasks_by_status": self._count_tasks_by_status()
        }
        return status
    
    def _count_tasks_by_status(self) -> Dict[str, int]:
        """Count tasks by their status."""
        counts = {}
        for task_id, task_info in self.state.get("tasks", {}).items():
            status = task_info.get("status", "unknown")
            counts[status] = counts.get(status, 0) + 1
        return counts
    
    def generate_communication_report(self, time_period="day") -> Dict:
        """
        Generate a report of all communications for the specified time period.
        
        Args:
            time_period: The time period to generate the report for ("day", "week", "month")
            
        Returns:
            A report of communications during the specified period
        """
        # This would analyze the log files and generate a report
        # For now, return a placeholder
        return {
            "period": time_period,
            "total_communications": len(self.state.get("tasks", {})),
            "agents_involved": list(self.agents.keys()),
            "status": "Report generation not fully implemented yet"
        }

def main():
    """Main function to demonstrate Atlas functionality."""
    # Initialize Atlas
    atlas = Atlas()
    
    # Example task
    task = {
        "id": "task_001",
        "type": "journal_entry",
        "data": {
            "description": "Record office supplies expense",
            "amount": 150.00,
            "date": "2025-03-24"
        }
    }
    
    # Execute the task
    result = atlas.execute_task(task)
    print(f"Task result: {result}")
    
    # Get system status
    status = atlas.get_system_status()
    print(f"System status: {status}")
    
    # Generate communication report
    report = atlas.generate_communication_report()
    print(f"Communication report: {report}")

if __name__ == "__main__":
    main()
