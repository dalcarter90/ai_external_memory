"""
Integration module for connecting local Ollama models with Pinecone vector storage.
"""

import os
import requests
import json
from typing import List, Dict, Any, Optional, Tuple

class OllamaEmbedding:
    """Class for generating embeddings using local Ollama models."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "mistral:7b-instruct-q4_0",
        dimension: int = 1024
    ):
        """
        Initialize the Ollama embedding generator.
        
        Args:
            base_url: URL of the Ollama API
            model: Model to use for embeddings
            dimension: Dimension of the embeddings
        """
        self.base_url = base_url
        self.model = model
        self.dimension = dimension
        self.api_endpoint = f"{self.base_url}/api/embeddings"
    
    def embed(self, text: str) -> Optional[List[float]]:
        """
        Generate embeddings for the given text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values or None if embedding fails
        """
        try:
            payload = {
                "model": self.model,
                "prompt": text
            }
            
            response = requests.post(
                self.api_endpoint,
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload)
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("embedding")
            else:
                print(f"Error generating embedding: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Exception during embedding generation: {e}")
            return None


class LocalLLMClient:
    """Client for interacting with local LLM models via Ollama."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "mistral:7b-instruct-q4_0",
        temperature: float = 0.7,
        max_tokens: int = 2048
    ):
        """
        Initialize the local LLM client.
        
        Args:
            base_url: URL of the Ollama API
            model: Model to use for generation
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
        """
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_endpoint = f"{self.base_url}/api/generate"
    
    def generate(self, prompt: str) -> Optional[str]:
        """
        Generate text using the local LLM.
        
        Args:
            prompt: Prompt for generation
            
        Returns:
            Generated text or None if generation fails
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
            
            response = requests.post(
                self.api_endpoint,
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload)
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response")
            else:
                print(f"Error generating text: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Exception during text generation: {e}")
            return None


class PineconeOllamaIntegration:
    """Integration between Pinecone vector store and local Ollama models."""
    
    def __init__(
        self,
        pinecone_store,
        embedding_model: Optional[OllamaEmbedding] = None,
        llm_client: Optional[LocalLLMClient] = None
    ):
        """
        Initialize the integration.
        
        Args:
            pinecone_store: Instance of PineconeVectorStore
            embedding_model: Instance of OllamaEmbedding or None to create default
            llm_client: Instance of LocalLLMClient or None to create default
        """
        self.pinecone_store = pinecone_store
        self.embedding_model = embedding_model or OllamaEmbedding()
        self.llm_client = llm_client or LocalLLMClient()
    
    def add_to_memory(self, content: str, metadata: Dict[str, Any] = None) -> Optional[str]:
        """
        Add content to memory with embeddings from local model.
        
        Args:
            content: Content to add
            metadata: Additional metadata
            
        Returns:
            ID of the added item or None if failed
        """
        from external_memory_system.memory.base import MemoryItem
        
        # Generate embedding using local model
        embedding = self.embedding_model.embed(content)
        
        if embedding is None:
            print("Failed to generate embedding")
            return None
        
        # Create memory item
        metadata = metadata or {}
        item = MemoryItem(
            content=content,
            metadata=metadata,
            embedding=embedding
        )
        
        # Add to Pinecone
        try:
            item_id = self.pinecone_store.add(item)
            return item_id
        except Exception as e:
            print(f"Error adding to Pinecone: {e}")
            return None
    
    def query_with_local_embedding(self, query: str, limit: int = 5) -> List[Tuple[Any, float]]:
        """
        Query memory using embeddings from local model.
        
        Args:
            query: Query text
            limit: Maximum number of results
            
        Returns:
            List of (item, score) tuples
        """
        # Generate embedding using local model
        embedding = self.embedding_model.embed(query)
        
        if embedding is None:
            print("Failed to generate embedding")
            return []
        
        # Override the _get_embedding_for_query method temporarily
        original_method = self.pinecone_store._get_embedding_for_query
        self.pinecone_store._get_embedding_for_query = lambda _: embedding
        
        # Perform search
        try:
            results = self.pinecone_store.search(query, limit)
            return results
        finally:
            # Restore original method
            self.pinecone_store._get_embedding_for_query = original_method
    
    def generate_with_context(self, query: str, limit: int = 3) -> str:
        """
        Generate response with context from memory.
        
        Args:
            query: Query text
            limit: Maximum number of context items
            
        Returns:
            Generated response
        """
        # Retrieve relevant context
        context_items = self.query_with_local_embedding(query, limit)
        
        if not context_items:
            # No context found, generate without context
            return self.llm_client.generate(query) or "No response generated."
        
        # Format context for prompt
        context_text = "\n\n".join([
            f"Context {i+1}:\n{item[0].content}" 
            for i, item in enumerate(context_items)
        ])
        
        # Create prompt with context
        prompt = f"""Please answer the following question using the provided context. If the context doesn't contain relevant information, use your general knowledge.

Context:
{context_text}

Question: {query}

Answer:"""
        
        # Generate response
        response = self.llm_client.generate(prompt)
        return response or "No response generated."
