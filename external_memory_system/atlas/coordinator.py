# external_memory_system/atlas/coordinator.py
import logging
from typing import Dict, Any, List, Optional
import os
import sys

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from external_memory_system.models.local_llm import LocalLLM, MockLLM
from external_memory_system.agents.bookkeeping_agent import BookkeepingAgent, MockVectorStore
from agents.bookkeeping_agent import BookkeepingAgent
from external_memory_system.dashboard.client import DashboardClient
# Import other agents as they are implemented

class Atlas:
    """
    Atlas central coordinator for the accounting agent system.
    Acts as the "brain" that manages specialized accounting agents.
    """
    
    def __init__(self, llm=None, vector_store=None, dashboard_url="http://localhost:5000") :
        """Initialize Atlas."""
        self.llm = llm or MockLLM()
        self.vector_store = vector_store or MockVectorStore(namespace="atlas")
        self.agents = {}
        self.state = {}
        self.tasks_completed = 0
        self.tasks_by_status = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize dashboard client
        self.dashboard = DashboardClient(dashboard_url)
        self.dashboard.register_agent("atlas", "Atlas Coordinator", "coordinator")
        self.dashboard.log_message("atlas", "INFO", "Atlas coordinator initialized")
    
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
    
    def register_agent(self, agent_id, agent_type):
        """Register an agent with Atlas."""
        self.agents[agent_id] = agent_type
        self.logger.info(f"Registered agent: {agent_id}")
        
        # Register agent with dashboard
        self.dashboard.register_agent(agent_id, agent_id.capitalize(), agent_type)
        self.dashboard.log_message("atlas", "INFO", f"Registered agent: {agent_id} ({agent_type})")
    
    def route_task(self, task: Dict) -> str:
        """
        Determine which agent should handle a given task.
        
        Args:
            task: The task to route
            
        Returns:
            The name of the agent that should handle the task
        """
        self.logger.debug(f"Routing task of type: {task_type}")
        
        task_type = task.get("type")
        
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
        
        # Route based on task type
        if task_type in ["journal_entry", "categorize_transaction", "chart_of_accounts"]:
            return "bookkeeping"
        elif task_type in ["reconcile_transaction", "bank_reconciliation"]:
            return "reconciliation"
        else:
            # Default to bookkeeping for unknown task types
            self.logger.warning(f"Unknown task type: {task_type}, routing to bookkeeping")
            return "bookkeeping"
    
    def execute_task(self, task):
        """Execute a task by routing it to the appropriate agent."""
        task_id = task.get("id")
        task_type = task.get("type")
        
        # Log task to dashboard
        self.dashboard.create_task(
            task_id, 
            "atlas", 
            task_type, 
            f"Routing task: {task.get('description', task_type)}"
        )
        
        # Route the task
        agent_id = self.route_task(task)
        self.logger.debug(f"Routing task of type: {task_type}")
        
        if agent_id not in self.agents:
            error_msg = f"Agent {agent_id} not registered"
            self.logger.error(error_msg)
            self.dashboard.update_task(task_id, "error", {"error": error_msg})
            return {"status": "error", "message": error_msg}
        
        # Get the agent instance
        agent_type = self.agents[agent_id]
        
        try:
            # Send the task to the agent
            self.logger.info(f"Sending task to {agent_id} agent")
            self.dashboard.log_message("atlas", "INFO", f"Sending task {task_id} to {agent_id} agent")
            
            # In a real implementation, you would have a way to get the agent instance
            # For now, we'll create a new instance for demonstration
            if agent_id == "bookkeeping":
                from external_memory_system.agents.bookkeeping_agent import BookkeepingAgent
                agent = BookkeepingAgent(llm=self.llm, vector_store=self.vector_store)
            elif agent_id == "reconciliation":
                from external_memory_system.agents.reconciliation_agent import ReconciliationAgent
                agent = ReconciliationAgent(llm=self.llm, vector_store=self.vector_store)
            else:
                error_msg = f"Unknown agent type: {agent_type}"
                self.logger.error(error_msg)
                self.dashboard.update_task(task_id, "error", {"error": error_msg})
                return {"status": "error", "message": error_msg}
            
            # Log task details
            self.logger.debug(f"Task details: {task}")
            
            # Execute the task
            result = agent.process_task(task)
            
            # Update task status in dashboard
            self.dashboard.update_task(task_id, result.get("status", "completed"), result)
            
            return result
        except Exception as e:
            error_msg = f"Error executing task on {agent_id} agent: {str(e)}"
            self.logger.error(error_msg)
            self.dashboard.update_task(task_id, "error", {"error": str(e)})
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
    
    def get_system_status(self):
        """
        Get the current status of the entire system.
        
        Returns:
            A dictionary containing system status information
        """
        return {
            "agents": list(self.agents.keys()),
            "state": self.state,
            "tasks_completed": self.tasks_completed,
            "tasks_by_status": self.tasks_by_status
        }
    
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
 
    def process_receipt_workflow(self, receipt_data: Dict) -> Dict:
        """Process a complete receipt workflow from submission to reconciliation.
        
        Args:
            receipt_data: The receipt submission data
            
        Returns:
            The workflow result
        """
        self.logger.info(f"Starting receipt processing workflow for employee: {receipt_data.get('employee')}")
        
        # Step 1: Create a task for the BookkeepingAgent to process the receipt
        bookkeeping_task = {
            "id": f"receipt_{self._generate_task_id()}",
            "type": "process_receipt",
            "data": receipt_data,
            "priority": "normal",
            "deadline": None
        }
        
        # Send task to BookkeepingAgent
        bookkeeping_result = self.execute_task(bookkeeping_task)
        
        # Step 2: Review the BookkeepingAgent's work
        if bookkeeping_result.get("requires_review", False):
            review_result = self._review_bookkeeping_result(bookkeeping_result)
            
            if not review_result.get("approved", False):
                # If not approved, return the result with the review feedback
                return {
                    "status": "rejected",
                    "message": "Receipt processing rejected during review",
                    "bookkeeping_result": bookkeeping_result,
                    "review_result": review_result
                }
        
        # Step 3: Create a task for the ReconciliationAgent to reconcile the transaction
        reconciliation_task = {
            "id": f"reconcile_{self._generate_task_id()}",
            "type": "reconcile_transaction",
            "data": {
                "journal_entry": bookkeeping_result.get("journal_entry"),
                "receipt_data": bookkeeping_result.get("receipt_data")
            },
            "priority": "normal",
            "deadline": None
        }
        
        # Send task to ReconciliationAgent
        reconciliation_result = self.execute_task(reconciliation_task)
        
        # Step 4: Handle the reconciliation result
        if reconciliation_result.get("reconciliation_status") == "reconciled":
            # Transaction reconciled successfully
            return {
                "status": "success",
                "message": "Receipt processed and transaction reconciled successfully",
                "bookkeeping_result": bookkeeping_result,
                "reconciliation_result": reconciliation_result
            }
        elif reconciliation_result.get("reconciliation_status") == "pending":
            # Transaction not found yet, schedule a retry
            self._schedule_task_retry(reconciliation_task, reconciliation_result.get("retry_after"))
            
            return {
                "status": "pending",
                "message": "Receipt processed, reconciliation pending",
                "bookkeeping_result": bookkeeping_result,
                "reconciliation_result": reconciliation_result,
                "retry_scheduled": True,
                "retry_date": reconciliation_result.get("retry_after")
            }
        else:
            # Transaction could not be reconciled, notify user
            if reconciliation_result.get("requires_review", False):
                self._notify_user_of_unreconciled_transaction(
                    bookkeeping_result, 
                    reconciliation_result
                )
            
            return {
                "status": "warning",
                "message": "Receipt processed, but transaction could not be reconciled",
                "bookkeeping_result": bookkeeping_result,
                "reconciliation_result": reconciliation_result,
                "user_notified": True
            }
        
    def _review_bookkeeping_result(self, result: Dict) -> Dict:
        """Review the BookkeepingAgent's work.
        
        Args:
            result: The result from the BookkeepingAgent
            
        Returns:
            The review result
        """
        self.logger.info(f"Reviewing bookkeeping result: {result.get('task_id')}")
        
        # Use LLM to review the bookkeeping result
        prompt = f"""
        You are Atlas, the central coordinator reviewing a BookkeepingAgent's work.
        
        Bookkeeping Result:
        Receipt Data: {result.get('receipt_data')}
        Validation Result: {result.get('validation_result')}
        Journal Entry: {result.get('journal_entry')}
        
        Review this bookkeeping work and determine if it's correct.
        Consider:
        1. Is the journal entry appropriate for the receipt?
        2. Are the accounts correctly chosen?
        3. Is the amount correct?
        4. Is there any potential fraud or policy violation?
        
        Provide your assessment and decision to approve or reject.
        """
        
        review_analysis = self.llm.generate(prompt)
        
        # In a real implementation, parse the LLM response to determine approval
        # For now, assume it's approved if there's a journal entry
        approved = result.get('journal_entry') is not None
        
        return {
            "approved": approved,
            "review_analysis": review_analysis,
            "reviewer": "Atlas",
            "review_date": self._get_current_date()
        }

    def _schedule_task_retry(self, task: Dict, retry_date: str) -> None:
        """Schedule a task to be retried at a later date.
        
        Args:
            task: The task to retry
            retry_date: The date to retry the task
        """
        self.logger.info(f"Scheduling task {task.get('id')} for retry on {retry_date}")
        
        # In a real implementation, use a task scheduler
        # For now, just log the scheduled retry
        self.logger.info(f"Task {task.get('id')} scheduled for retry on {retry_date}")

    def _notify_user_of_unreconciled_transaction(self, bookkeeping_result: Dict, reconciliation_result: Dict) -> None:
        """Notify the user of an unreconciled transaction.
        
        Args:
            bookkeeping_result: The result from the BookkeepingAgent
            reconciliation_result: The result from the ReconciliationAgent
        """
        self.logger.info(f"Notifying user of unreconciled transaction: {reconciliation_result.get('task_id')}")
        
        # In a real implementation, send an email or notification
        # For now, just log the notification
        self.logger.warning(f"NOTIFICATION: Unreconciled transaction detected")
        self.logger.warning(f"Journal Entry: {bookkeeping_result.get('journal_entry')}")
        self.logger.warning(f"Reconciliation Status: {reconciliation_result.get('reconciliation_status')}")
        self.logger.warning(f"Review Reason: {reconciliation_result.get('review_reason')}")

    def _get_current_date(self) -> str:
        """Get the current date in YYYY-MM-DD format."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d")

    def _generate_task_id(self) -> str:
        """Generate a unique task ID."""
        import uuid
        return str(uuid.uuid4())[:8]
    
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
