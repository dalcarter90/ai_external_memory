"""
Google Gemini model adapter for the External Memory System.
"""

import os
import json
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import requests

from .base import BaseModel


class GeminiModel(BaseModel):
    """Interface for interacting with Google's Gemini models."""
    
    def __init__(
        self,
        model: str = "gemini-pro",
        api_key: Optional[str] = None,
        api_key_env: str = "GOOGLE_API_KEY",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        timeout: int = 60
    ):
        """
        Initialize the Gemini model interface.
        
        Args:
            model: The model name to use
            api_key: Google API key (if None, will use environment variable)
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
        model = kwargs.get("model", self.model)
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        
        # Construct the API URL
        api_url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={self.api_key}"
        
        # Prepare the request payload
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "topP": kwargs.get("top_p", 0.95),
                "topK": kwargs.get("top_k", 40)
            }
        }
        
        try:
            response = self.session.post(
                api_url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            
            # Extract the generated text from the response
            generated_text = result["candidates"][0]["content"]["parts"][0]["text"]
            return generated_text
        
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
        
        # Construct the API URL for embeddings
        api_url = f"https://generativelanguage.googleapis.com/v1/models/embedding-001:embedContent?key={self.api_key}"
        
        # Prepare the request payload
        payload = {
            "content": {"parts": [{"text": text}]},
            "taskType": "RETRIEVAL_DOCUMENT"
        }
        
        try:
            response = self.session.post(
                api_url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            
            # Extract the embedding from the response
            embedding = result["embedding"]["values"]
            return embedding
        
        except Exception as e:
            print(f"Error generating embedding: {e}")
            # Return a zero vector as fallback (Gemini embeddings are 768-dimensional)
            return [0.0] * 768
    
    def close(self) -> None:
        """Close the model connection and release resources."""
        if self.session:
            self.session.close()
            self.session = None
