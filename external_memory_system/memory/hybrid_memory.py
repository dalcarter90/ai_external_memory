"""
Hybrid memory system that combines vector, key-value, and graph stores.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import time

from .base import (
    BaseMemoryStore, MemoryItem, 
    ShortTermMemory, LongTermMemory, 
    EpisodicMemory, SemanticMemory,
    DedicatedModelMemory, SharedMemoryPool
)
from .vector_store import InMemoryVectorStore
from .key_value_store import InMemoryKeyValueStore
from .graph_store import InMemoryGraphStore

try:
    from .pinecone_store import PineconeVectorStore
except ImportError:
    # Define a placeholder if Pinecone is not installed
    PineconeVectorStore = None


class HybridMemory(
    ShortTermMemory, 
    LongTermMemory, 
    EpisodicMemory, 
    SemanticMemory,
    DedicatedModelMemory,
    SharedMemoryPool
):
    """
    Hybrid memory system that combines vector, key-value, and graph stores
    to provide comprehensive memory capabilities.
    """
    
    def __init__(
        self,
        vector_store: Optional[Union[InMemoryVectorStore, PineconeVectorStore]] = None,
        key_value_store: Optional[InMemoryKeyValueStore] = None,
        graph_store: Optional[InMemoryGraphStore] = None,
        vector_dimension: int = 1536,
        vector_metric: str = "cosine",
        kv_expire_time: int = 86400
    ):
        """
        Initialize the hybrid memory system.
        
        Args:
            vector_store: Vector store for semantic memory (or None to create a new one)
            key_value_store: Key-value store for short-term memory (or None to create a new one)
            graph_store: Graph store for episodic and long-term memory (or None to create a new one)
            vector_dimension: Dimension for vector embeddings if creating a new vector store
            vector_metric: Similarity metric for vector store if creating a new one
            kv_expire_time: Default expiration time for key-value store if creating a new one
        """
        # Initialize or use provided stores
        self.vector_store = vector_store or InMemoryVectorStore()
        self.key_value_store = key_value_store or InMemoryKeyValueStore(
            expire_time=kv_expire_time
        )
        self.graph_store = graph_store or InMemoryGraphStore()
        
        # Model-specific memory
        self.model_memories = {}  # model_id -> dict of preferences
        
        # Shared memory contexts
        self.shared_contexts = {}  # context_id -> set of item_ids
    
    def add(self, item: MemoryItem) -> str:
        """
        Add an item to memory, storing it in appropriate stores based on metadata.
        
        The item is stored in:
        - Vector store for semantic search
        - Key-value store if it's short-term memory
        - Graph store if it's long-term or episodic memory
        """
        # Determine which stores to use based on metadata
        use_vector = True  # Always use vector store for semantic search
        use_kv = "memory_type" in item.metadata and item.metadata["memory_type"] == "short_term"
        use_graph = "memory_type" in item.metadata and item.metadata["memory_type"] in ["long_term", "episodic"]
        
        # Default to all stores if not specified
        if "memory_type" not in item.metadata:
            use_kv = True
            use_graph = True
        
        # Add to vector store
        if use_vector:
            self.vector_store.add(item)
        
        # Add to key-value store with expiration if it's short-term
        if use_kv:
            expire_time = item.metadata.get("expire_time", None)
            self.key_value_store.add(item, expire_time=expire_time)
        
        # Add to graph store if it's long-term or episodic
        if use_graph:
            self.graph_store.add(item)
        
        # Handle model-specific memory
        if "model_id" in item.metadata:
            model_id = item.metadata["model_id"]
            if "preferences" in item.metadata:
                self._update_model_preferences(model_id, item.metadata["preferences"])
        
        # Handle shared memory contexts
        if "shared_context_id" in item.metadata:
            context_id = item.metadata["shared_context_id"]
            if context_id not in self.shared_contexts:
                self.shared_contexts[context_id] = set()
            self.shared_contexts[context_id].add(item.item_id)
        
        return item.item_id
    
    def get(self, item_id: str) -> Optional[MemoryItem]:
        """
        Retrieve an item by ID from the appropriate store.
        
        Checks all stores and returns the first match.
        """
        # Try key-value store first (fastest)
        item = self.key_value_store.get(item_id)
        if item:
            return item
        
        # Try graph store
        item = self.graph_store.get(item_id)
        if item:
            return item
        
        # Try vector store
        item = self.vector_store.get(item_id)
        return item
    
    def update(self, item_id: str, item: MemoryItem) -> bool:
        """
        Update an item in all stores where it exists.
        """
        success = False
        
        # Update in vector store
        if self.vector_store.get(item_id):
            success = self.vector_store.update(item_id, item) or success
        
        # Update in key-value store
        if self.key_value_store.get(item_id):
            expire_time = item.metadata.get("expire_time", None)
            success = self.key_value_store.update(item_id, item, expire_time=expire_time) or success
        
        # Update in graph store
        if self.graph_store.get(item_id):
            success = self.graph_store.update(item_id, item) or success
        
        # Handle model-specific memory updates
        if "model_id" in item.metadata and "preferences" in item.metadata:
            model_id = item.metadata["model_id"]
            self._update_model_preferences(model_id, item.metadata["preferences"])
            success = True
        
        # Handle shared memory context updates
        old_item = self.get(item_id)
        if old_item and "shared_context_id" in old_item.metadata:
            old_context = old_item.metadata["shared_context_id"]
            if old_context in self.shared_contexts and item_id in self.shared_contexts[old_context]:
                self.shared_contexts[old_context].remove(item_id)
        
        if "shared_context_id" in item.metadata:
            new_context = item.metadata["shared_context_id"]
            if new_context not in self.shared_contexts:
                self.shared_contexts[new_context] = set()
            self.shared_contexts[new_context].add(item_id)
        
        return success
    
    def delete(self, item_id: str) -> bool:
        """
        Delete an item from all stores.
        """
        success = False
        
        # Delete from vector store
        if self.vector_store.get(item_id):
            success = self.vector_store.delete(item_id) or success
        
        # Delete from key-value store
        if self.key_value_store.get(item_id):
            success = self.key_value_store.delete(item_id) or success
        
        # Delete from graph store
        if self.graph_store.get(item_id):
            success = self.graph_store.delete(item_id) or success
        
        # Remove from shared contexts
        for context_id, item_ids in self.shared_contexts.items():
            if item_id in item_ids:
                item_ids.remove(item_id)
                success = True
        
        return success
    
    def search(self, query: Any, limit: int = 10) -> List[Tuple[MemoryItem, float]]:
        """
        Search for items matching the query across all stores.
        
        Prioritizes semantic search from vector store but combines results
        from all stores for comprehensive retrieval.
        """
        # Get results from each store
        vector_results = self.vector_store.search(query, limit=limit)
        kv_results = self.key_value_store.search(query, limit=limit)
        graph_results = self.graph_store.search(query, limit=limit)
        
        # Combine and deduplicate results
        combined_results = {}
        
        # Add vector results (highest priority for semantic search)
        for item, score in vector_results:
            combined_results[item.item_id] = (item, score)
        
        # Add key-value results
        for item, score in kv_results:
            if item.item_id not in combined_results or score > combined_results[item.item_id][1]:
                combined_results[item.item_id] = (item, score)
        
        # Add graph results
        for item, score in graph_results:
            if item.item_id not in combined_results or score > combined_results[item.item_id][1]:
                combined_results[item.item_id] = (item, score)
        
        # Sort by score (descending)
        results = list(combined_results.values())
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:limit]
    
    def list(self, filter_criteria: Optional[Dict[str, Any]] = None, limit: int = 100) -> List[MemoryItem]:
        """
        List items based on filter criteria across all stores.
        """
        # Determine which store to use based on filter criteria
        if filter_criteria and "memory_type" in filter_criteria:
            memory_type = filter_criteria["memory_type"]
            if memory_type == "short_term":
                return self.key_value_store.list(filter_criteria, limit)
            elif memory_type in ["long_term", "episodic"]:
                return self.graph_store.list(filter_criteria, limit)
        
        # If no specific memory type or multiple types, combine results
        kv_results = self.key_value_store.list(filter_criteria, limit)
        graph_results = self.graph_store.list(filter_criteria, limit)
        
        # Combine and deduplicate
        combined_results = {}
        for item in kv_results + graph_results:
            combined_results[item.item_id] = item
        
        return list(combined_results.values())[:limit]
    
    def clear(self) -> bool:
        """
        Clear all memory stores.
        """
        vector_success = self.vector_store.clear()
        kv_success = self.key_value_store.clear()
        graph_success = self.graph_store.clear()
        
        self.model_memories.clear()
        self.shared_contexts.clear()
        
        return vector_success and kv_success and graph_success
    
    # ShortTermMemory implementation
    
    def get_recent(self, limit: int = 10) -> List[MemoryItem]:
        """
        Get the most recent items from short-term memory.
        """
        return self.key_value_store.get_recent(limit)
    
    def get_context(self, context_id: str) -> List[MemoryItem]:
        """
        Get items related to a specific context from short-term memory.
        """
        return self.key_value_store.get_context(context_id)
    
    # LongTermMemory implementation
    
    def get_by_importance(self, min_importance: float = 0.0, max_importance: float = 1.0, limit: int = 10) -> List[MemoryItem]:
        """
        Get items within an importance range from long-term memory.
        """
        return self.graph_store.get_by_importance(min_importance, max_importance, limit)
    
    def get_by_tags(self, tags: List[str], match_all: bool = False, limit: int = 10) -> List[MemoryItem]:
        """
        Get items with specific tags from long-term memory.
        """
        return self.graph_store.get_by_tags(tags, match_all, limit)
    
    # EpisodicMemory implementation
    
    def get_by_timerange(self, start_time: float, end_time: float, limit: int = 10) -> List[MemoryItem]:
        """
        Get items within a time range from episodic memory.
        """
        return self.graph_store.get_by_timerange(start_time, end_time, limit)
    
    def get_episodes(self, episode_id: str) -> List[MemoryItem]:
        """
        Get all items in a specific episode from episodic memory.
        """
        return self.graph_store.get_episodes(episode_id)
    
    # SemanticMemory implementation
    
    def semantic_search(self, query: str, limit: int = 10) -> List[Tuple[MemoryItem, float]]:
        """
        Perform semantic search on memory items.
        """
        return self.vector_store.semantic_search(query, limit)
    
    def get_related(self, item_id: str, limit: int = 10) -> List[Tuple[MemoryItem, float]]:
        """
        Get items semantically related to a specific item.
        """
        return self.vector_store.get_related(item_id, limit)
    
    # DedicatedModelMemory implementation
    
    def _update_model_preferences(self, model_id: str, preferences: Dict[str, Any]):
        """
        Update preferences for a specific model.
        """
        if model_id not in self.model_memories:
            self.model_memories[model_id] = {}
        
        self.model_memories[model_id].update(preferences)
    
    def get_model_preferences(self, model_id: str) -> Dict[str, Any]:
        """
        Get preferences for a specific model.
        """
        return self.model_memories.get(model_id, {})
    
    def set_model_preferences(self, model_id: str, preferences: Dict[str, Any]) -> bool:
        """
        Set preferences for a specific model.
        """
        self.model_memories[model_id] = preferences
        return True
    
    # SharedMemoryPool implementation
    
    def get_shared_context(self, context_id: str) -> List[MemoryItem]:
        """
        Get shared context items.
        """
        if context_id not in self.shared_contexts:
            return []
        
        results = []
        for item_id in self.shared_contexts[context_id]:
            item = self.get(item_id)
            if item:
                results.append(item)
        
        # Sort by timestamp (ascending)
        results.sort(key=lambda x: x.timestamp)
        
        return results
    
    def add_to_shared_context(self, context_id: str, item: MemoryItem) -> str:
        """
        Add an item to a shared context.
        """
        # Add shared context to metadata
        item.metadata["shared_context_id"] = context_id
        
        # Add to memory
        return self.add(item)
