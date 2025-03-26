"""Bookkeeping agent for accounting tasks."""

import logging
import json
from typing import Dict, Any, Optional

from external_memory_system.storage.pinecone_store import PineconeVectorStore
from external_memory_system.models.local_llm import LocalLLM, MockLLM
from external_memory_system.dashboard.client import DashboardClient

# Create a mock vector store for testing
class MockVectorStore:
    """Mock implementation of a vector store for testing."""
    
    def __init__(self, namespace: str = "default"):
        """Initialize the mock vector store.
        
        Args:
            namespace: The namespace for the vector store
        """
        self.namespace = namespace
        self.data = {}
        print(f"Initialized MockVectorStore with namespace: {namespace}")
        
    def add_texts(self, texts: list, metadata: Dict = None):
        """Add texts to the vector store."""
        if metadata is None:
            metadata = {}
        for i, text in enumerate(texts):
            self.data[f"{len(self.data)}"] = {"text": text, "metadata": metadata}
        return [f"{i}" for i in range(len(self.data) - len(texts), len(self.data))]
    
    def similarity_search(self, query: str, k: int = 5):
        """Perform a similarity search."""
        # Just return the k most recent items for testing
        items = list(self.data.items())[-k:]
        return [{"id": id, "text": data["text"], "metadata": data["metadata"]} for id, data in items]

class BookkeepingAgent:
    """Agent for bookkeeping tasks."""
    
    def __init__(self, llm=None, vector_store=None, dashboard_url="http://localhost:5000") :
        """Initialize the bookkeeping agent."""
        self.llm = llm or MockLLM()
        self.vector_store = vector_store or MockVectorStore(namespace="bookkeeping")
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize dashboard client
        self.dashboard = DashboardClient(dashboard_url)
        self.agent_id = "bookkeeping"
        self.dashboard.register_agent(self.agent_id, "Bookkeeping Agent", "bookkeeping")
        self.dashboard.log_message(self.agent_id, "INFO", "Bookkeeping agent initialized")
        
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
            if task_type == "journal_entry":
                result = self._process_journal_entry(task)
            elif task_type == "categorize_transaction":
                result = self._process_categorize_transaction(task)
            elif task_type == "chart_of_accounts":
                result = self._process_chart_of_accounts(task)
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
    
    # Update BookkeepingAgent to use QuickBooks integration

    def _process_journal_entry(self, task: Dict) -> Dict:
        """Process a journal entry task."""
        # Extract task data
        data = task.get("data", {})
        description = data.get("description", "")
        amount = data.get("amount", 0)
        date = data.get("date", "")
        
        # Validate the journal entry using LLM
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
        
        # Get QuickBooks integration
        from external_memory_system.integrations.mock_quickbooks import MockQuickBooksIntegration
        qb = MockQuickBooksIntegration()
        
        # Get chart of accounts
        accounts = qb.get_chart_of_accounts()
        
        # Create journal entry lines based on validation result
        # This is a simplified example - in a real implementation, you would parse the LLM response
        # to determine the appropriate accounts
        lines = [
            {
                "description": description,
                "amount": amount,
                "posting_type": "Debit",
                "account_id": "account_004",  # Office Supplies Expense
                "account_name": "Office Supplies Expense"
            },
            {
                "description": description,
                "amount": amount,
                "posting_type": "Credit",
                "account_id": "account_006",  # Company Credit Card
                "account_name": "Company Credit Card"
            }
        ]
    
    # Create journal entry in QuickBooks
    journal_entry = qb.create_journal_entry({
        "description": description,
        "date": date,
        "reference_number": f"JE-{task.get('id')}",
        "lines": lines
    })
    
    # Return the result
    return {
        "status": "success",
        "message": "Journal entry processed",
        "task_id": task.get("id"),
        "validation": validation_result,
        "journal_entry": journal_entry,
        "entry_details": {
            "description": description,
            "amount": amount,
            "date": date
        }
    }

    
    def _process_categorize_transaction(self, task: Dict) -> Dict:
        """Categorize a financial transaction."""
        # Extract task data
        data = task.get("data", {})
        description = data.get("description", "")
        amount = data.get("amount", 0)
        
        # Use LLM to categorize the transaction
        prompt = f"""
        You are a bookkeeping agent responsible for categorizing transactions.
        
        Transaction:
        Description: {description}
        Amount: ${amount}
        
        What is the most appropriate account category for this transaction?
        Provide the account name and explain your reasoning.
        """
        
        categorization_result = self.llm.generate(prompt)
        
        # Return the result
        return {
            "status": "success",
            "message": "Transaction categorized",
            "task_id": task.get("id"),
            "categorization": categorization_result,
            "transaction_details": {
                "description": description,
                "amount": amount
            }
        }
    
    def _process_chart_of_accounts(self, task: Dict) -> Dict:
        """Process a chart of accounts task."""
        # Extract task data
        data = task.get("data", {})
        action = data.get("action", "")
        account_name = data.get("account_name", "")
        account_type = data.get("account_type", "")
        
        # Use LLM to process the chart of accounts task
        prompt = f"""
        You are a bookkeeping agent responsible for managing the chart of accounts.
        
        Task:
        Action: {action}
        Account Name: {account_name}
        Account Type: {account_type}
        
        Provide guidance on this chart of accounts task.
        """
        
        processing_result = self.llm.generate(prompt)
        
        # Return the result
        return {
            "status": "success",
            "message": f"Chart of accounts task processed: {action}",
            "task_id": task.get("id"),
            "processing_result": processing_result,
            "account_details": {
                "name": account_name,
                "type": account_type,
                "action": action
            }
        }
    
    def _process_default(self, task: Dict) -> Dict:
        """Default task processor when no specific handler exists."""
        self.logger.info(f"Using default processor for task: {task.get('id')}")
        
        # Use LLM to generate a response
        prompt = f"""
        You are a specialized accounting agent.
        Process this task using your accounting expertise:
        
        Task: {task}
        
        Provide a detailed response with your analysis and recommendations.
        """
        
        response = self.llm.generate(prompt)
        
        return {
            "status": "success",
            "message": "Task processed with default handler",
            "task_id": task.get("id"),
            "result": response
        }
    def _process_receipt(self, task: Dict) -> Dict:
        """Process a receipt and create a journal entry.
        
        Args:
            task: The receipt processing task
            
        Returns:
            The result of processing the receipt
        """
        self.logger.info(f"Processing receipt: {task.get('id')}")
        
        # Extract task data
        data = task.get("data", {})
        receipt_image = data.get("receipt_image", "")
        employee = data.get("employee", "")
        submission_date = data.get("submission_date", "")
        
        # Step 1: Extract data from receipt using OCR (simplified for now)
        receipt_data = self._extract_receipt_data(receipt_image)
        
        # Step 2: Validate the receipt data
        validation_result = self._validate_receipt_data(receipt_data, employee)
        
        # Step 3: Create a journal entry based on the receipt
        journal_entry = self._create_journal_entry_from_receipt(receipt_data, employee)
        
        # Step 4: Store the receipt information for future reference
        self._store_receipt_data(receipt_data, journal_entry, receipt_image)
        
        return {
            "status": "success",
            "message": "Receipt processed and journal entry created",
            "task_id": task.get("id"),
            "receipt_data": receipt_data,
            "validation_result": validation_result,
            "journal_entry": journal_entry,
            "requires_review": True  # Flag for Atlas to review
        }

    def _extract_receipt_data(self, receipt_image: str) -> Dict:
        """Extract data from a receipt image using OCR.
        
        In a real implementation, this would use OCR services.
        For now, we'll simulate the extraction.
        
        Args:
            receipt_image: Path or URL to the receipt image
            
        Returns:
            Extracted receipt data
        """
        # In a real implementation, use OCR service like Google Vision API
        # For now, simulate extraction with LLM
        prompt = f"""
        You are an OCR system processing a receipt image.
        The image is from: {receipt_image}
        
        Extract the following information:
        1. Vendor name
        2. Date of purchase
        3. Total amount
        4. List of items purchased
        5. Payment method
        
        Format the response as structured data.
        """
        
        # Use LLM to simulate OCR extraction
        extraction_result = self.llm.generate(prompt)
        
        # In a real implementation, parse the OCR result
        # For now, create a simulated structured result
        return {
            "vendor": "Hardware Store Inc.",
            "date": "2025-03-24",
            "total_amount": 45.67,
            "items": [
                {"name": "Hammer", "price": 15.99},
                {"name": "Nails", "price": 8.99},
                {"name": "Screwdriver", "price": 12.99},
                {"name": "Tax", "price": 7.70}
            ],
            "payment_method": "Company Card"
        }

    def _validate_receipt_data(self, receipt_data: Dict, employee: str) -> Dict:
        """Validate the extracted receipt data.
        
        Args:
            receipt_data: The extracted receipt data
            employee: The employee who submitted the receipt
            
        Returns:
            Validation result
        """
        # Use LLM to validate the receipt data
        prompt = f"""
        You are a bookkeeping agent validating receipt data.
        
        Receipt Data:
        Vendor: {receipt_data.get('vendor')}
        Date: {receipt_data.get('date')}
        Total Amount: ${receipt_data.get('total_amount')}
        Items: {receipt_data.get('items')}
        Payment Method: {receipt_data.get('payment_method')}
        Submitted by: {employee}
        
        Validate this receipt data and identify any issues or concerns.
        Is this a valid business expense? Explain your reasoning.
        """
        
        validation_result = self.llm.generate(prompt)
        
        return {
            "is_valid": True,  # In a real implementation, determine based on LLM response
            "reasoning": validation_result
        }

    def _create_journal_entry_from_receipt(self, receipt_data: Dict, employee: str) -> Dict:
        """Create a journal entry based on receipt data.
        
        Args:
            receipt_data: The extracted receipt data
            employee: The employee who submitted the receipt
            
        Returns:
            Journal entry details
        """
        # Use LLM to determine the appropriate accounts
        prompt = f"""
        You are a bookkeeping agent creating a journal entry from a receipt.
        
        Receipt Data:
        Vendor: {receipt_data.get('vendor')}
        Date: {receipt_data.get('date')}
        Total Amount: ${receipt_data.get('total_amount')}
        Items: {receipt_data.get('items')}
        Payment Method: {receipt_data.get('payment_method')}
        Submitted by: {employee}
        
        Determine the appropriate accounts to debit and credit for this transaction.
        Provide a description for the journal entry.
        """
        
        accounting_guidance = self.llm.generate(prompt)
        
        # Create the journal entry
        journal_entry = {
            "date": receipt_data.get('date'),
            "description": f"Purchase from {receipt_data.get('vendor')} by {employee}",
            "debit_account": "Office Supplies Expense",  # In a real implementation, parse from LLM response
            "credit_account": "Company Credit Card",  # In a real implementation, parse from LLM response
            "amount": receipt_data.get('total_amount'),
            "reference": f"Receipt-{receipt_data.get('date')}-{employee}",
            "accounting_guidance": accounting_guidance
        }
        
        return journal_entry

    def _store_receipt_data(self, receipt_data: Dict, journal_entry: Dict, receipt_image: str) -> None:
        """Store receipt data and journal entry in the vector store.
        
        Args:
            receipt_data: The extracted receipt data
            journal_entry: The created journal entry
            receipt_image: Path or URL to the receipt image
        """
        if self.vector_store:
            # Create a text representation of the receipt and journal entry
            content = f"""
            Receipt Data:
            Vendor: {receipt_data.get('vendor')}
            Date: {receipt_data.get('date')}
            Total Amount: ${receipt_data.get('total_amount')}
            Items: {receipt_data.get('items')}
            Payment Method: {receipt_data.get('payment_method')}
            
            Journal Entry:
            Date: {journal_entry.get('date')}
            Description: {journal_entry.get('description')}
            Debit Account: {journal_entry.get('debit_account')}
            Credit Account: {journal_entry.get('credit_account')}
            Amount: ${journal_entry.get('amount')}
            Reference: {journal_entry.get('reference')}
            """
            
            # Create metadata for retrieval
            metadata = {
                "type": "receipt",
                "vendor": receipt_data.get('vendor'),
                "date": receipt_data.get('date'),
                "amount": receipt_data.get('total_amount'),
                "journal_entry_reference": journal_entry.get('reference'),
                "receipt_image": receipt_image
            }
            
            # Add to vector store
            self.vector_store.add_texts([content], metadata=metadata)
            self.logger.debug(f"Stored receipt data and journal entry in vector store")

