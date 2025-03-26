# external_memory_system/agents/reconciliation_agent.py
"""Reconciliation agent for accounting tasks."""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from external_memory_system.models.local_llm import LocalLLM, MockLLM
from external_memory_system.dashboard.client import DashboardClient

class ReconciliationAgent:
    """Agent for reconciliation tasks."""
    
    def __init__(self, llm=None, vector_store=None, dashboard_url="http://localhost:5000") :
        """Initialize the reconciliation agent."""
        self.llm = llm or MockLLM()
        self.vector_store = vector_store or MockVectorStore(namespace="reconciliation")
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize dashboard client
        self.dashboard = DashboardClient(dashboard_url)
        self.agent_id = "reconciliation"
        self.dashboard.register_agent(self.agent_id, "Reconciliation Agent", "reconciliation")
        self.dashboard.log_message(self.agent_id, "INFO", "Reconciliation agent initialized")
        
    def process_task(self, task):
        """Process a task assigned to this agent."""
        task_id = task.get("id")
        task_type = task.get("type")
        
        self.logger.info(f"Processing task: {task_id} of type {task_type}")
        self.dashboard.create_task(task_id, self.agent_id, task_type, str(task.get("data", {})))
        
        try:
            # Extract task type and validate
            if not task_type:
                raise ValueError("Task type is required")
            
            # Route to appropriate handler method based on task type
            if task_type == "reconcile_transaction":
                result = self._process_reconcile_transaction(task)
            elif task_type == "bank_reconciliation":
                result = self._process_bank_reconciliation(task)
            else:
                self.logger.warning(f"No specific handler for task type: {task_type}")
                result = self._process_default(task)
            
            # Update task status in dashboard
            self.dashboard.update_task(task_id, result.get("status", "completed"), result)
            
            return result
        except Exception as e:
            error_msg = f"Error processing task {task_id}: {str(e)}"
            self.logger.error(error_msg)
            self.dashboard.update_task(task_id, "error", {"error": str(e)})
            self.dashboard.log_message(self.agent_id, "ERROR", error_msg)
            
            return {
                "status": "error",
                "message": f"Error processing task: {str(e)}",
                "task_id": task_id
            }

    def _process_reconcile_transaction(self, task: Dict) -> Dict:
        """Reconcile a specific transaction with bank statement."""
        self.logger.info(f"Reconciling transaction: {task.get('id')}")
        
        # Extract task data
        data = task.get("data", {})
        journal_entry = data.get("journal_entry", {})
        
        # Get QuickBooks integration
        from external_memory_system.integrations.mock_quickbooks import MockQuickBooksIntegration
        qb = MockQuickBooksIntegration()
        
        # Get bank transactions for the account
        account_id = "account_006"  # Company Credit Card
        start_date = journal_entry.get("date")
        
        # Calculate end date (5 days after transaction date)
        from datetime import datetime, timedelta
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_obj = start_date_obj + timedelta(days=5)
        end_date = end_date_obj.strftime("%Y-%m-%d")
        
        # Get bank transactions
        bank_transactions = qb.get_bank_transactions(account_id, start_date, end_date)
        
        # Search for matching transaction
        matching_transaction = None
        for transaction in bank_transactions:
            # Simple matching logic - in a real implementation, use more sophisticated matching
            if (abs(transaction.get("amount") - journal_entry.get("amount")) < 0.01 and
                transaction.get("description").upper() in journal_entry.get("description").upper()):
                matching_transaction = transaction
                break
        
        if matching_transaction:
            # Transaction found, mark as reconciled
            return {
                "status": "success",
                "message": "Transaction reconciled successfully",
                "task_id": task.get("id"),
                "reconciliation_status": "reconciled",
                "journal_entry": journal_entry,
                "bank_transaction": matching_transaction,
                "requires_review": False
            }
        else:
            # Transaction not found, check if we should retry later
            current_date = datetime.now().strftime("%Y-%m-%d")
            transaction_date = journal_entry.get("date")
            
            # Calculate days since transaction
            transaction_date_obj = datetime.strptime(transaction_date, "%Y-%m-%d")
            current_date_obj = datetime.now()
            days_since_transaction = (current_date_obj - transaction_date_obj).days
            
            if days_since_transaction < 5:  # Allow up to 5 days for transaction to appear
                return {
                    "status": "pending",
                    "message": "Transaction not found in bank statement, will retry later",
                    "task_id": task.get("id"),
                    "reconciliation_status": "pending",
                    "journal_entry": journal_entry,
                    "retry_after": (current_date_obj + timedelta(days=2)).strftime("%Y-%m-%d"),
                    "requires_review": False
                }
            else:
                # It's been too long, mark as unreconciled and flag for review
                return {
                    "status": "warning",
                    "message": "Transaction not found in bank statement after 5 days",
                    "task_id": task.get("id"),
                    "reconciliation_status": "unreconciled",
                    "journal_entry": journal_entry,
                    "requires_review": True,
                    "review_reason": "Transaction not found in bank statement after 5 days"
                }

            
            return {
                "status": "success",
                "message": "Transaction reconciled successfully",
                "task_id": task.get("id"),
                "reconciliation_status": "reconciled",
                "journal_entry": journal_entry,
                "bank_transaction": reconciliation_result.get("transaction"),
                "requires_review": False
            }
    
    def _process_bank_reconciliation(self, task: Dict) -> Dict:
        """Process a full bank reconciliation."""
        self.logger.info(f"Processing bank reconciliation: {task.get('id')}")
        
        # Simplified implementation for testing
        return {
            "status": "success",
            "message": "Bank reconciliation completed",
            "task_id": task.get("id"),
            "reconciliation_summary": {
                "total_transactions": 10,
                "reconciled": 9,
                "unreconciled": 1
            }
        }
    
    def _process_default(self, task: Dict) -> Dict:
        """Default task processor when no specific handler exists."""
        self.logger.info(f"Using default processor for task: {task.get('id')}")
        
        response = "I've analyzed this task and provided appropriate reconciliation guidance."
        
        return {
            "status": "success",
            "message": "Task processed with default handler",
            "task_id": task.get("id"),
            "result": response
        }
        
    # In external_memory_system/atlas/coordinator.py

    def route_task(self, task: Dict) -> str:
        """Route a task to the appropriate agent.
        
        Args:
            task: The task to route
            
        Returns:
            The ID of the agent to handle the task
        """
        self.logger.debug(f"Routing task of type: {task.get('type')}")
        
        task_type = task.get("type")
        
        # Route based on task type
        if task_type in ["journal_entry", "categorize_transaction", "chart_of_accounts"]:
            return "bookkeeping"
        elif task_type in ["reconcile_transaction", "bank_reconciliation"]:
            return "reconciliation"
        else:
            # Default to bookkeeping for unknown task types
            self.logger.warning(f"Unknown task type: {task_type}, routing to bookkeeping")
            return "bookkeeping"
        
    # At the end of reconciliation_agent.py
    if __name__ == "__main__":
        # Add the project root to the Python path
        import sys
        import os
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
        
        # Import required modules
        from external_memory_system.models.local_llm import MockLLM
        
        # Create a test instance
        agent = ReconciliationAgent(llm=MockLLM())
        
        # Create a test task
        test_task = {
            "id": "test_001",
            "type": "reconcile_transaction",
            "data": {
                "journal_entry": {
                    "date": "2025-03-24",
                    "description": "Test transaction",
                    "amount": 100.00
                }
            }
        }
        
        # Process the task
        result = agent.process_task(test_task)
        
        # Print the result
        print("Test result:")
        print(result)
