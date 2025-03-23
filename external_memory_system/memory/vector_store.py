"""Integration with Pinecone vector storage."""

import pinecone
from typing import List, Dict, Any, Optional
import uuid
import json
import time
from ..config import PINECONE_API_KEY, PINECONE_ENVIRONMENT, PINECONE_INDEX_NAME
from ..models.local_llm import LocalLLM

class PineconeVectorStore:
    """Interface for interacting with Pinecone vector database."""
    
    def __init__(self, namespace: str = "accounting"):
        """Initialize the Pinecone vector store.
        
        Args:
            namespace: Namespace to use in Pinecone
        """
        # Initialize Pinecone
        pinecone.init(
            api_key=PINECONE_API_KEY,
            environment=PINECONE_ENVIRONMENT
        )
        
        # Connect to index
        self.index = pinecone.Index(PINECONE_INDEX_NAME)
        self.namespace = namespace
        
        # Initialize local LLM for embeddings
        self.llm = LocalLLM()
        
        # Local cache for memory items
        self.cache = {}
    
    def add_item(
        self, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None,
        item_id: Optional[str] = None
    ) -> str:
        """Add an item to the vector store.
        
        Args:
            content: Text content to store
            metadata: Additional metadata for the item
            item_id: Optional ID for the item (generated if not provided)
            
        Returns:
            ID of the stored item
        """
        # Generate embedding using local LLM
        embedding = self.llm.embed(content)
        
        # Generate ID if not provided
        if item_id is None:
            item_id = str(uuid.uuid4())
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        
        # Add content and timestamp to metadata
        full_metadata = {
            **metadata,
            "content": content,
            "timestamp": time.time()
        }
        
        # Upsert to Pinecone
        self.index.upsert(
            vectors=[(item_id, embedding, full_metadata)],
            namespace=self.namespace
        )
        
        # Update local cache
        self.cache[item_id] = {
            "id": item_id,
            "content": content,
            "embedding": embedding,
            "metadata": metadata,
            "timestamp": full_metadata["timestamp"]
        }
        
        return item_id
    
    def search(
        self, 
        query: str, 
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar items in the vector store.
        
        Args:
            query: Query text to search for
            top_k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of matching items with scores
        """
        # Generate embedding for query
        query_embedding = self.llm.embed(query)
        
        # Search in Pinecone
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            namespace=self.namespace,
            filter=filter,
            include_metadata=True
        )
        
        # Format results
        formatted_results = []
        for match in results.matches:
            item = {
                "id": match.id,
                "score": match.score,
                "content": match.metadata.get("content", ""),
                "metadata": {k: v for k, v in match.metadata.items() if k != "content"}
            }
            formatted_results.append(item)
            
            # Update cache
            self.cache[match.id] = {
                "id": match.id,
                "content": item["content"],
                "metadata": item["metadata"],
                "score": match.score
            }
        
        return formatted_results
    
    def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get an item by ID.
        
        Args:
            item_id: ID of the item to retrieve
            
        Returns:
            Item data or None if not found
        """
        # Check cache first
        if item_id in self.cache:
            return self.cache[item_id]
        
        # Fetch from Pinecone
        response = self.index.fetch(
            ids=[item_id],
            namespace=self.namespace
        )
        
        # Check if item was found
        if item_id not in response.vectors:
            return None
        
        # Get vector data
        vector_data = response.vectors[item_id]
        
        # Format item
        item = {
            "id": item_id,
            "content": vector_data.metadata.get("content", ""),
            "embedding": vector_data.values,
            "metadata": {k: v for k, v in vector_data.metadata.items() if k != "content"}
        }
        
        # Update cache
        self.cache[item_id] = item
        
        return item
    
    def delete_item(self, item_id: str) -> bool:
        """Delete an item from the vector store.
        
        Args:
            item_id: ID of the item to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete from Pinecone
            self.index.delete(
                ids=[item_id],
                namespace=self.namespace
            )
            
            # Remove from cache
            if item_id in self.cache:
                del self.cache[item_id]
            
            return True
        except Exception:
            return False
    
    def clear_cache(self):
        """Clear the local cache."""
        self.cache = {}
        
class InMemoryVectorStore:
    """Simple in-memory vector store for testing purposes."""
    
    def __init__(self):
        self.vectors = {}
        
    def add_vectors(self, vectors, texts, metadatas=None):
        if metadatas is None:
            metadatas = [{} for _ in texts]
        
        for i, (vector, text, metadata) in enumerate(zip(vectors, texts, metadatas)):
            self.vectors[str(i)] = {
                "vector": vector,
                "text": text,
                "metadata": metadata
            }
        
        return [str(i) for i in range(len(vectors))]
    
    def similarity_search(self, query_vector, k=5):
        # Simple implementation - in a real scenario you'd use cosine similarity
        results = []
        for id, data in self.vectors.items():
            results.append((id, data["text"], data["metadata"]))
        
        # Return up to k results
        return results[:k]

