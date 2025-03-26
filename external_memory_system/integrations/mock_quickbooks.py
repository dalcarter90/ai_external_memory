# external_memory_system/integrations/mock_quickbooks.py

import logging
import json
import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class MockQuickBooksIntegration:
    """Mock implementation of QuickBooks integration for development and testing."""
    
    def __init__(self, data_dir: str = None):
        """Initialize the mock QuickBooks integration.
        
        Args:
            data_dir: Directory to store mock data files
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.data_dir = data_dir or os.path.join(os.getcwd(), "mock_data")
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize data files
        self.accounts_file = os.path.join(self.data_dir, "accounts.json")
        self.journal_entries_file = os.path.join(self.data_dir, "journal_entries.json")
        self.bank_transactions_file = os.path.join(self.data_dir, "bank_transactions.json")
        
        # Initialize data if files don't exist
        self._initialize_data()
        
        self.logger.info("Mock QuickBooks integration initialized")
    
    def _initialize_data(self):
        """Initialize mock data files if they don't exist."""
        # Initialize accounts
        if not os.path.exists(self.accounts_file):
            accounts = [
                {
                    "id": "account_001",
                    "name": "Cash",
                    "account_type": "Bank",
                    "account_sub_type": "Checking",
                    "active": True
                },
                {
                    "id": "account_002",
                    "name": "Accounts Receivable",
                    "account_type": "Accounts Receivable",
                    "account_sub_type": "Accounts Receivable",
                    "active": True
                },
                {
                    "id": "account_003",
                    "name": "Accounts Payable",
                    "account_type": "Accounts Payable",
                    "account_sub_type": "Accounts Payable",
                    "active": True
                },
                {
                    "id": "account_004",
                    "name": "Office Supplies Expense",
                    "account_type": "Expense",
                    "account_sub_type": "Office Supplies",
                    "active": True
                },
                {
                    "id": "account_005",
                    "name": "Rent Expense",
                    "account_type": "Expense",
                    "account_sub_type": "Rent",
                    "active": True
                },
                {
                    "id": "account_006",
                    "name": "Company Credit Card",
                    "account_type": "Credit Card",
                    "account_sub_type": "Credit Card",
                    "active": True
                }
            ]
            
            with open(self.accounts_file, "w") as f:
                json.dump(accounts, f, indent=2)
        
        # Initialize journal entries
        if not os.path.exists(self.journal_entries_file):
            journal_entries = []
            with open(self.journal_entries_file, "w") as f:
                json.dump(journal_entries, f, indent=2)
        
        # Initialize bank transactions
        if not os.path.exists(self.bank_transactions_file):
            bank_transactions = []
            with open(self.bank_transactions_file, "w") as f:
                json.dump(bank_transactions, f, indent=2)
    
    def authenticate(self, access_token: str = None, refresh_token: str = None, realm_id: str = None):
        """Mock authentication with QuickBooks API."""
        self.logger.info("Mock authentication successful")
        return True
    
    def get_chart_of_accounts(self) -> List[Dict]:
        """Get the mock chart of accounts."""
        self.logger.info("Retrieving mock chart of accounts")
        
        try:
            with open(self.accounts_file, "r") as f:
                accounts = json.load(f)
            
            self.logger.info(f"Retrieved {len(accounts)} mock accounts")
            return accounts
        except Exception as e:
            self.logger.error(f"Error retrieving mock chart of accounts: {str(e)}")
            raise
    
    def create_journal_entry(self, entry_data: Dict) -> Dict:
        """Create a mock journal entry."""
        self.logger.info(f"Creating mock journal entry: {entry_data.get('description')}")
        
        try:
            # Load existing journal entries
            with open(self.journal_entries_file, "r") as f:
                journal_entries = json.load(f)
            
            # Create a new entry with a unique ID
            entry_id = f"je_{len(journal_entries) + 1:03d}"
            
            new_entry = {
                "id": entry_id,
                "reference_number": entry_data.get("reference_number", f"REF-{entry_id}"),
                "date": entry_data.get("date", datetime.now().strftime("%Y-%m-%d")),
                "description": entry_data.get("description", ""),
                "lines": entry_data.get("lines", []),
                "created_at": datetime.now().isoformat()
            }
            
            # Add to journal entries
            journal_entries.append(new_entry)
            
            # Save updated journal entries
            with open(self.journal_entries_file, "w") as f:
                json.dump(journal_entries, f, indent=2)
            
            # If this is a bank transaction, also add to bank transactions
            if any(line.get("account_id") in ["account_001", "account_006"] for line in entry_data.get("lines", [])):
                self._create_bank_transaction(new_entry)
            
            self.logger.info(f"Mock journal entry created with ID: {entry_id}")
            
            return {
                "id": entry_id,
                "reference_number": new_entry["reference_number"],
                "date": new_entry["date"],
                "description": new_entry["description"],
                "status": "created"
            }
        except Exception as e:
            self.logger.error(f"Error creating mock journal entry: {str(e)}")
            raise
    
    def _create_bank_transaction(self, journal_entry: Dict):
        """Create a corresponding bank transaction for a journal entry."""
        try:
            # Load existing bank transactions
            with open(self.bank_transactions_file, "r") as f:
                bank_transactions = json.load(f)
            
            # Find the bank account line
            bank_lines = [line for line in journal_entry.get("lines", []) 
                         if line.get("account_id") in ["account_001", "account_006"]]
            
            if not bank_lines:
                return
            
            bank_line = bank_lines[0]
            
            # Create a new bank transaction
            transaction_id = f"bank_txn_{len(bank_transactions) + 1:03d}"
            
            # Add a random delay of 0-2 days for the bank transaction
            transaction_date = datetime.strptime(journal_entry["date"], "%Y-%m-%d")
            delay_days = random.randint(0, 2)
            transaction_date = transaction_date + timedelta(days=delay_days)
            
            new_transaction = {
                "id": transaction_id,
                "date": transaction_date.strftime("%Y-%m-%d"),
                "description": journal_entry["description"].upper(),  # Banks often use uppercase
                "amount": bank_line.get("amount", 0.0),
                "type": "debit" if bank_line.get("posting_type") == "Credit" else "credit",
                "account_id": bank_line.get("account_id"),
                "related_journal_entry_id": journal_entry["id"]
            }
            
            # Add to bank transactions
            bank_transactions.append(new_transaction)
            
            # Save updated bank transactions
            with open(self.bank_transactions_file, "w") as f:
                json.dump(bank_transactions, f, indent=2)
            
            self.logger.info(f"Mock bank transaction created with ID: {transaction_id}")
        except Exception as e:
            self.logger.error(f"Error creating mock bank transaction: {str(e)}")
    
    def get_transactions(self, start_date: str, end_date: str, account_id: Optional[str] = None) -> List[Dict]:
        """Get mock transactions."""
        self.logger.info(f"Retrieving mock transactions from {start_date} to {end_date}")
        
        try:
            # Load journal entries
            with open(self.journal_entries_file, "r") as f:
                journal_entries = json.load(f)
            
            # Filter by date range
            filtered_entries = [
                entry for entry in journal_entries
                if start_date <= entry["date"] <= end_date
            ]
            
            # Filter by account if specified
            if account_id:
                filtered_entries = [
                    entry for entry in filtered_entries
                    if any(line.get("account_id") == account_id for line in entry.get("lines", []))
                ]
            
            self.logger.info(f"Retrieved {len(filtered_entries)} mock transactions")
            return filtered_entries
        except Exception as e:
            self.logger.error(f"Error retrieving mock transactions: {str(e)}")
            raise
    
    def get_bank_transactions(self, account_id: str, start_date: str, end_date: str) -> List[Dict]:
        """Get mock bank transactions for reconciliation."""
        self.logger.info(f"Retrieving mock bank transactions for account {account_id} from {start_date} to {end_date}")
        
        try:
            # Load bank transactions
            with open(self.bank_transactions_file, "r") as f:
                bank_transactions = json.load(f)
            
            # Filter by account and date range
            filtered_transactions = [
                txn for txn in bank_transactions
                if txn.get("account_id") == account_id and start_date <= txn["date"] <= end_date
            ]
            
            self.logger.info(f"Retrieved {len(filtered_transactions)} mock bank transactions")
            return filtered_transactions
        except Exception as e:
            self.logger.error(f"Error retrieving mock bank transactions: {str(e)}")
            raise
