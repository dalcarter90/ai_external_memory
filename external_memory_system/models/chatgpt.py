"""
ChatGPT model adapter for the External Memory System.
"""

import os
import json
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import requests

from .base import BaseModel


class ChatGPTModel(BaseModel):
    """Interface for interacting with OpenAI's ChatGPT models."""
    
    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: Optional[str] = None,
        api_key_env: str = "OPENAI_API_KEY",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        timeout: int = 60
    ):
        """
        Initialize the ChatGPT model interface.
        
        Args:
            model: The model name to use
            api_key: OpenAI API key (if None, will use environment variable)
            api_key_env: Name of environment variable containing API key
            max_tokens: Maximum tokens in response
            temperature: Temperature for generation (0.0 to 1.0)
            timeout: Request timeout in seconds
        """
        self.model = model
        self.api_key = api_key or os.environ.get(api_key_env)
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.session = None
        
        if not self.api_key:
            raise ValueError(f"API key not found. Please provide it directly or set the {api_key_env} environment variable.")
    
    def initialize(self) -> bool:
        """Initialize the model connection."""
        import requests
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
        return True
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate a response from the model.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional model-specific parameters
            
        Returns:
            The generated response
        """
        if not self.session:
            self.initialize()
        
        # Override default parameters with any provided in kwargs
        params = {
            "model": kwargs.get("model", self.model),
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
        }
        
        # Add optional parameters if provided
        for param in ["top_p", "frequency_penalty", "presence_penalty", "stop"]:
            if param in kwargs:
                params[param] = kwargs[param]
        
        try:
            response = self.session.post(
                "https://api.openai.com/v1/chat/completions",
                json=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            
            return result["choices"][0]["message"]["content"]
        
        except Exception as e:
            print(f"Error generating response: {e}")
            return f"Error: {str(e)}"
    
    def embed(self, text: str) -> List[float]:
        """
        Generate an embedding for the given text.
        
        Args:
            text: The text to embed
            
        Returns:
            The embedding vector as a list of floats
        """
        if not self.session:
            self.initialize()
        
        try:
            response = self.session.post(
                "https://api.openai.com/v1/embeddings",
                json={
                    "model": "text-embedding-3-large",
                    "input": text
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            
            return result["data"][0]["embedding"]
        
        except Exception as e:
            print(f"Error generating embedding: {e}")
            # Return a zero vector as fallback
            return [0.0] * 1536
    
    def close(self) -> None:
        """Close the model connection and release resources."""
        if self.session:
            self.session.close()
            self.session = None
