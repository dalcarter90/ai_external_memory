"""
Base model interface for the External Memory System.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union


class BaseModel(ABC):
    """Abstract base class for AI model interfaces."""
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the model connection.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate a response from the model.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional model-specific parameters
            
        Returns:
            The generated response
        """
        pass
    
    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """
        Generate an embedding for the given text.
        
        Args:
            text: The text to embed
            
        Returns:
            The embedding vector as a list of floats
        """
        pass
    
    @abstractmethod
    def close(self) -> None:
        """
        Close the model connection and release resources.
        """
        pass
