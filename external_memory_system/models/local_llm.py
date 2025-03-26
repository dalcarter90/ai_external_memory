"""Integration with local LLM using Ollama."""

import requests
import json
import random
import time
import logging
from typing import Dict, List, Any, Optional
from external_memory_system.config import OLLAMA_BASE_URL, DEFAULT_MODEL, MODEL_TEMPERATURE, MODEL_MAX_TOKENS

class LocalLLM:
    """Integration with local LLM using Ollama."""
    
    def __init__(self, model_name: str = DEFAULT_MODEL):
        """Initialize the LLM.
        
        Args:
            model_name: Name of the model to use
        """
        self.model_name = model_name
        self.api_url = f"{OLLAMA_BASE_URL}/api/generate"
        self.headers = {"Content-Type": "application/json"}
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def generate(self, prompt: str) -> str:
        """Generate a response using the LLM."""
        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "temperature": MODEL_TEMPERATURE,
                    "max_tokens": MODEL_MAX_TOKENS
                },
                headers=self.headers
            )
            
            try:
                # Try to parse as regular JSON first
                result = response.json()
                return result.get('response', prompt + " [No valid response]")
            except requests.exceptions.JSONDecodeError as e:
                self.logger.warning(f"JSON decode error: {str(e)}")
                # If JSON parsing fails, return the raw text
                return response.text
                
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return f"Error: {str(e)}"


class MockLLM:
    """Mock implementation of a language model for testing purposes."""
    
    def __init__(self, model_name: str = "mock-model"):
        """Initialize the mock LLM.
        
        Args:
            model_name: Name of the mock model
        """
        self.model_name = model_name
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"Initialized MockLLM with model: {model_name}")
        
    def generate(self, prompt: str) -> str:
        """Generate a mock response based on the prompt.
        
        Args:
            prompt: The input prompt
            
        Returns:
            A mock response
        """
        # Simulate processing delay
        time.sleep(random.uniform(0.5, 2.0))
        
        # Generate a response based on the prompt content
        response_text = ""
        
        if "journal entry" in prompt.lower():
            response_text = "This journal entry appears valid. Debit Office Supplies Expense, Credit Cash or Accounts Payable."
        elif "categorize" in prompt.lower() or "transaction" in prompt.lower():
            response_text = "Based on the description, this should be categorized as 'Rent Expense'."
        elif "chart of accounts" in prompt.lower():
            response_text = "This account appears valid. Suggested account number: 5000 - Office Supplies Expense under Operating Expenses."
        elif "validate" in prompt.lower():
            response_text = "The data has been validated successfully."
        else:
            response_text = f"I've processed your request regarding: {prompt[:50]}..."
            
        self.logger.debug(f"MockLLM generated response for prompt: {prompt[:50]}...")
        return response_text
