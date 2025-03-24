"""Integration with local LLM using Ollama."""

import requests
import json
from typing import Dict, List, Any, Optional
from external_memory_system.config import OLLAMA_BASE_URL, DEFAULT_MODEL, MODEL_TEMPERATURE, MODEL_MAX_TOKENS

'''
class MockLLM(LocalLLM):
    """
    Mock implementation of LocalLLM for testing purposes.
    """
    
    def __init__(self):
        """Initialize the mock LLM."""
        print("Initialized MockLLM")
    
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
        else:
            return "I've processed your request successfully."
'''

class LocalLLM:
    """Interface for interacting with local LLM through Ollama."""
    
    def __init__(
        self, 
        model: str = DEFAULT_MODEL,
        temperature: float = MODEL_TEMPERATURE,
        max_tokens: int = MODEL_MAX_TOKENS
    ) :
        """Initialize the LocalLLM.
        
        Args:
            model: Name of the Ollama model to use
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
        """
        self.base_url = OLLAMA_BASE_URL
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    def generate(self, prompt: str) -> str:
        """Generate text based on the prompt.
        
        Args:
            prompt: Input text prompt
            
        Returns:
            Generated text response
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"Error generating text: {response.text}")
        
        # Parse the response
        result = response.json()
        return result.get("response", "")
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Chat with the model using a conversation format.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            
        Returns:
            Model's response text
        """
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"Error in chat: {response.text}")
        
        # Parse the response
        result = response.json()
        return result.get("message", {}).get("content", "")
    
    def embed(self, text: str) -> List[float]:
        """Generate embeddings for the given text.
        
        Args:
            text: Input text to embed
            
        Returns:
            Vector embedding as a list of floats
        """
        url = f"{self.base_url}/api/embeddings"
        
        payload = {
            "model": self.model,
            "prompt": text
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"Error generating embeddings: {response.text}")
        
        # Parse the response
        result = response.json()
        return result.get("embedding", [])
