# external_memory_system/storage/mock_vector_store.py

from typing import List, Dict, Any, Optional
from external_memory_system.storage.pinecone_store import PineconeVectorStore

class MockVectorStore(PineconeVectorStore):
    """
    Mock implementation of PineconeVectorStore for testing purposes.
    
    This class implements the abstract methods required by PineconeVectorStore
    with simple mock functionality for testing.
    """
    
    def __init__(self, namespace: str = "default"):
        """
        Initialize the mock vector store.
        
        Args:
            namespace: The namespace to use for this vector store
        """
        self.namespace = namespace
        self.vectors = {}  # Simple in-memory storage
        self.metadata = {}
        print(f"Initialized MockVectorStore with namespace: {namespace}")
    
    def add_texts(self, texts: List[str], metadata: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Add texts to the vector store.
        
        Args:
            texts: List of text strings to add
            metadata: Optional metadata to associate with the texts
            
        Returns:
            List of IDs for the added texts
        """
        ids = []
        for i, text in enumerate(texts):
            text_id = f"{self.namespace}_{len(self.vectors) + i}"
            self.vectors[text_id] = text
            if metadata:
                self.metadata[text_id] = metadata
            ids.append(text_id)
        
        print(f"Added {len(texts)} texts to MockVectorStore")
        return ids
    
    def similarity_search(self, query: str, k: int = 4) -> List[Dict[str, Any]]:
        """
        Perform a similarity search.
        
        Args:
            query: The query text
            k: Number of results to return
            
        Returns:
            List of similar documents with metadata
        """
        # For mock purposes, just return the first k items
        results = []
        for text_id, text in list(self.vectors.items())[:k]:
            result = {
                "id": text_id,
                "text": text,
                "score": 0.9,  # Mock similarity score
            }
            
            if text_id in self.metadata:
                result["metadata"] = self.metadata[text_id]
            
            results.append(result)
        
        print(f"Performed similarity search for: {query}")
        return results
    
    def clear(self) -> None:
        """
        Clear all vectors from the store.
        """
        self.vectors = {}
        self.metadata = {}
        print(f"Cleared all vectors from namespace: {self.namespace}")
    
    def get_related(self, text_id: str, k: int = 4) -> List[Dict[str, Any]]:
        """
        Get related texts for a given text ID.
        
        Args:
            text_id: The ID of the text to find related items for
            k: Number of results to return
            
        Returns:
            List of related documents with metadata
        """
        # For mock purposes, just return some other items
        results = []
        count = 0
        
        for other_id, text in self.vectors.items():
            if other_id != text_id and count < k:
                result = {
                    "id": other_id,
                    "text": text,
                    "score": 0.8,  # Mock similarity score
                }
                
                if other_id in self.metadata:
                    result["metadata"] = self.metadata[other_id]
                
                results.append(result)
                count += 1
        
        print(f"Found {len(results)} related items for: {text_id}")
        return results
    
    def list(self) -> List[str]:
        """
        List all text IDs in the store.
        
        Returns:
            List of text IDs
        """
        ids = list(self.vectors.keys())
        print(f"Listed {len(ids)} vectors from namespace: {self.namespace}")
        return ids
