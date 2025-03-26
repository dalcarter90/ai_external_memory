# external_memory_system/integrations/quickbooks_integration.py

import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from quickbooks import QuickBooks
from quickbooks.objects.customer import Customer
from quickbooks.objects.account import Account
from quickbooks.objects.journalentry import JournalEntry, JournalEntryLine
from quickbooks.objects.vendor import Vendor
from quickbooks.objects.bill import Bill
from quickbooks.objects.invoice import Invoice

class QuickBooksIntegration:
    """Integration with QuickBooks Online API."""
    
    def __init__(self, client_id: str, client_secret: str, environment: str = "sandbox"):
        """Initialize the QuickBooks integration.
        
        Args:
            client_id: QuickBooks API client ID
            client_secret: QuickBooks API client secret
            environment: 'sandbox' for development, 'production' for live data
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.environment = environment
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # These will be set during authentication
        self.access_token = None
        self.refresh_token = None
        self.realm_id = None
        self.qb_client = None
        
        self.logger.info(f"QuickBooks integration initialized in {environment} environment")
    
    def authenticate(self, access_token: str, refresh_token: str, realm_id: str):
        """Authenticate with QuickBooks API.
        
        Args:
            access_token: OAuth access token
            refresh_token: OAuth refresh token
            realm_id: QuickBooks company ID
        """
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.realm_id = realm_id
        
        # Initialize the QuickBooks client
        self.qb_client = QuickBooks(
            client_id=self.client_id,
            client_secret=self.client_secret,
            access_token=self.access_token,
            refresh_token=self.refresh_token,
            company_id=self.realm_id,
            sandbox=self.environment == "sandbox"
        )
        
        self.logger.info(f"Authenticated with QuickBooks for company ID: {realm_id}")
    
    def get_chart_of_accounts(self) -> List[Dict]:
        """Get the chart of accounts from QuickBooks.
        
        Returns:
            List of account objects
        """
        self.logger.info("Retrieving chart of accounts from QuickBooks")
        
        try:
            accounts = Account.all(qb=self.qb_client)
            
            # Convert to simplified dictionary format
            account_list = []
            for account in accounts:
                account_list.append({
                    "id": account.Id,
                    "name": account.Name,
                    "account_type": account.AccountType,
                    "account_sub_type": account.AccountSubType,
                    "active": account.Active
                })
            
            self.logger.info(f"Retrieved {len(account_list)} accounts from QuickBooks")
            return account_list
        except Exception as e:
            self.logger.error(f"Error retrieving chart of accounts: {str(e)}")
            raise
    
    def create_journal_entry(self, entry_data: Dict) -> Dict:
        """Create a journal entry in QuickBooks.
        
        Args:
            entry_data: Journal entry data with lines for debits and credits
            
        Returns:
            Created journal entry object
        """
        self.logger.info(f"Creating journal entry: {entry_data.get('description')}")
        
        try:
            # Create a new journal entry
            journal_entry = JournalEntry()
            
            # Set journal entry properties
            journal_entry.DocNumber = entry_data.get("reference_number", "")
            journal_entry.TxnDate = entry_data.get("date", datetime.now().strftime("%Y-%m-%d"))
            journal_entry.PrivateNote = entry_data.get("description", "")
            
            # Add journal entry lines
            for line in entry_data.get("lines", []):
                journal_line = JournalEntryLine()
                journal_line.Description = line.get("description", "")
                journal_line.Amount = line.get("amount", 0.0)
                journal_line.PostingType = line.get("posting_type", "Debit")  # "Debit" or "Credit"
                
                # Set the account reference
                account_ref = {
                    "value": line.get("account_id"),
                    "name": line.get("account_name", "")
                }
                journal_line.AccountRef = account_ref
                
                journal_entry.Line.append(journal_line)
            
            # Save the journal entry to QuickBooks
            created_entry = journal_entry.save(qb=self.qb_client)
            
            self.logger.info(f"Journal entry created with ID: {created_entry.Id}")
            
            # Return the created entry
            return {
                "id": created_entry.Id,
                "reference_number": created_entry.DocNumber,
                "date": created_entry.TxnDate,
                "description": created_entry.PrivateNote,
                "status": "created"
            }
        except Exception as e:
            self.logger.error(f"Error creating journal entry: {str(e)}")
            raise
    
    def get_transactions(self, start_date: str, end_date: str, account_id: Optional[str] = None) -> List[Dict]:
        """Get transactions from QuickBooks.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            account_id: Optional account ID to filter by
            
        Returns:
            List of transaction objects
        """
        self.logger.info(f"Retrieving transactions from {start_date} to {end_date}")
        
        try:
            # For a real implementation, you would use the appropriate QuickBooks query
            # This is a simplified example
            query = f"SELECT * FROM JournalEntry WHERE TxnDate >= '{start_date}' AND TxnDate <= '{end_date}'"
            
            if account_id:
                # In a real implementation, you would need to join with line items
                # This is a placeholder for the concept
                query += f" AND AccountRef = '{account_id}'"
            
            journal_entries = JournalEntry.query(query, qb=self.qb_client)
            
            # Convert to simplified dictionary format
            transaction_list = []
            for entry in journal_entries:
                transaction = {
                    "id": entry.Id,
                    "date": entry.TxnDate,
                    "reference_number": entry.DocNumber,
                    "description": entry.PrivateNote,
                    "lines": []
                }
                
                # Add lines
                for line in entry.Line:
                    transaction["lines"].append({
                        "description": line.Description,
                        "amount": line.Amount,
                        "posting_type": line.PostingType,
                        "account_id": line.AccountRef.value if line.AccountRef else None,
                        "account_name": line.AccountRef.name if line.AccountRef else None
                    })
                
                transaction_list.append(transaction)
            
            self.logger.info(f"Retrieved {len(transaction_list)} transactions from QuickBooks")
            return transaction_list
        except Exception as e:
            self.logger.error(f"Error retrieving transactions: {str(e)}")
            raise
    
    def get_bank_transactions(self, account_id: str, start_date: str, end_date: str) -> List[Dict]:
        """Get bank transactions for reconciliation.
        
        Args:
            account_id: Bank account ID
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            List of bank transaction objects
        """
        self.logger.info(f"Retrieving bank transactions for account {account_id} from {start_date} to {end_date}")
        
        try:
            # For a real implementation, you would use the appropriate QuickBooks query
            # This is a simplified example that would need to be expanded
            query = f"SELECT * FROM BankAccountTransactions WHERE AccountRef = '{account_id}' AND TxnDate >= '{start_date}' AND TxnDate <= '{end_date}'"
            
            # In a real implementation, you would execute this query
            # For now, return a mock response
            return [
                {
                    "id": "bank_txn_001",
                    "date": "2025-03-24",
                    "description": "HARDWARE STORE INC",
                    "amount": 45.67,
                    "type": "debit"
                },
                {
                    "id": "bank_txn_002",
                    "date": "2025-03-23",
                    "description": "OFFICE SUPPLIES CO",
                    "amount": 127.89,
                    "type": "debit"
                },
                {
                    "id": "bank_txn_003",
                    "date": "2025-03-22",
                    "description": "CLIENT PAYMENT",
                    "amount": 1500.00,
                    "type": "credit"
                }
            ]
        except Exception as e:
            self.logger.error(f"Error retrieving bank transactions: {str(e)}")
            raise
