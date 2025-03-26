# external_memory_system/models/mock_llm.py

class MockLLM:
    """
    Mock implementation of LocalLLM for testing purposes.
    """
    
    def __init__(self, model: str = "mock-model"):
        """Initialize the mock LLM."""
        self.model = model
        print(f"Initialized MockLLM with model: {model}")
    
    def generate(self, prompt: str) -> str:
        """
        Generate a response to the given prompt.
        
        Args:
            prompt: The prompt to generate a response for
            
        Returns:
            A generated response
        """
        print(f"MockLLM received prompt: {prompt[:50]}...")
        
        # Return different responses based on prompt content
        if "journal entry" in prompt.lower():
            return "This journal entry is valid. Debit Office Supplies Expense, Credit Cash."
        elif "categorize" in prompt.lower():
            return "This transaction should be categorized as Rent Expense."
        elif "chart of accounts" in prompt.lower():
            return "Adding Marketing Expenses to the chart of accounts is valid."
        elif "route" in prompt.lower() and "task" in prompt.lower():
            return "bookkeeping"
        else:
            return "I've processed your request successfully."
