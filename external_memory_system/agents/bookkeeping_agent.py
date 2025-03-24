# external_memory_system/agents/bookkeeping_agent.py
# Renamed from accounting_agent.py

import os
import sys
from typing import Dict, Any, Optional

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.local_llm import LocalLLM
from storage.pinecone_store import PineconeVectorStore

class BookkeepingAgent:
    """
    Specialized agent for bookkeeping tasks.
    Handles journal entries, transaction categorization, and chart of accounts management.
    """
    
    def __init__(self, llm: Optional[LocalLLM] = None, vector_store: Optional[PineconeVectorStore] = None):
        """
        Initialize the bookkeeping agent.
        
        Args:
            llm: The language model to use
            vector_store: The vector store for knowledge retrieval
        """
        self.llm = llm or LocalLLM()
        self.vector_store = vector_store or PineconeVectorStore(namespace="bookkeeping")
    
    def process_task(self, task: Dict) -> Dict:
        """
        Process a bookkeeping task.
        
        Args:
            task: The task to process
            
        Returns:
            The result of processing the task
        """
        task_type = task.get("type")
        
        if task_type == "journal_entry":
            return self._process_journal_entry(task)
        elif task_type == "categorize_transaction":
            return self._categorize_transaction(task)
        elif task_type == "chart_of_accounts":
            return self._manage_chart_of_accounts(task)
        else:
            return {
                "status": "error",
                "message": f"Unknown task type for bookkeeping agent: {task_type}"
            }
    
    def _process_journal_entry(self, task: Dict) -> Dict:
        """Process a journal entry task."""
        # Extract task data
        data = task.get("data", {})
        description = data.get("description", "")
        amount = data.get("amount", 0.0)
        date = data.get("date", "")
        
        # In a real implementation, this would create a journal entry in QuickBooks
        # For now, we'll just simulate the process
        
        # Use the LLM to validate the journal entry
        prompt = f"""
        You are a bookkeeping agent responsible for validating journal entries.
        
        Journal Entry:
        Description: {description}
        Amount: ${amount}
        Date: {date}
        
        Is this a valid journal entry? If not, explain why.
        If valid, suggest the appropriate accounts to debit and credit.
        """
        
        validation_result = self.llm.generate(prompt)
        
        # Store the journal entry information in the vector store
        self.vector_store.add_texts(
            [f"Journal Entry: {description} for ${amount} on {date}"],
            metadata={
                "type": "journal_entry",
                "amount": amount,
                "date": date,
                "validation": validation_result[:100]  # Store a summary of the validation
            }
        )
        
        return {
            "status": "success",
            "message": "Journal entry processed",
            "validation": validation_result,
            "entry_details": {
                "description": description,
                "amount": amount,
                "date": date
            }
        }
    
    def _categorize_transaction(self, task: Dict) -> Dict:
        """Categorize a transaction."""
        # Extract task data
        data = task.get("data", {})
        description = data.get("description", "")
        amount = data.get("amount", 0.0)
        
        # Use the LLM to categorize the transaction
        prompt = f"""
        You are a bookkeeping agent responsible for categorizing transactions.
        
        Transaction:
        Description: {description}
        Amount: ${amount}
        
        What is the most appropriate account category for this transaction?
        Provide the account name and explain your reasoning.
        """
        
        categorization_result = self.llm.generate(prompt)
        
        return {
            "status": "success",
            "message": "Transaction categorized",
            "categorization": categorization_result,
            "transaction_details": {
                "description": description,
                "amount": amount
            }
        }
    
    def _manage_chart_of_accounts(self, task: Dict) -> Dict:
        """Manage the chart of accounts."""
        # Extract task data
        data = task.get("data", {})
        action = data.get("action", "")
        account_name = data.get("account_name", "")
        account_type = data.get("account_type", "")
        
        # Use the LLM to validate the chart of accounts action
        prompt = f"""
        You are a bookkeeping agent responsible for managing the chart of accounts.
        
        Requested Action: {action}
        Account Name: {account_name}
        Account Type: {account_type}
        
        Is this a valid chart of accounts action? If not, explain why.
        If valid, explain how this would affect the accounting system.
        """
        
        validation_result = self.llm.generate(prompt)
        
        return {
            "status": "success",
            "message": f"Chart of accounts {action} processed",
            "validation": validation_result,
            "account_details": {
                "name": account_name,
                "type": account_type,
                "action": action
            }
        }

def main():
    """Main function to demonstrate bookkeeping agent functionality."""
    # Initialize the bookkeeping agent
    agent = BookkeepingAgent()
    
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
    
    # Process the task
    result = agent.process_task(task)
    print(f"Task result: {result}")

if __name__ == "__main__":
    main()
