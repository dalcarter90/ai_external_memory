"""
Base memory interfaces for the External Memory System.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union


class MemoryItem:
    """Base class for items stored in memory."""
    
    def __init__(
        self,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
        item_id: Optional[str] = None,
        source: Optional[str] = None,
        timestamp: Optional[float] = None,
        importance: float = 0.5,
        tags: Optional[List[str]] = None
    ):
        """
        Initialize a memory item.
        
        Args:
            content: The content to store in memory
            metadata: Additional metadata about the content
            item_id: Unique identifier for the item
            source: Source of the memory (e.g., "chatgpt", "gemini")
            timestamp: Creation time of the memory item
            importance: Importance score (0.0 to 1.0)
            tags: List of tags for categorization
        """
        import time
        import uuid
        
        self.content = content
        self.metadata = metadata or {}
        self.item_id = item_id or str(uuid.uuid4())
        self.source = source
        self.timestamp = timestamp or time.time()
        self.importance = max(0.0, min(1.0, importance))  # Clamp between 0 and 1
        self.tags = tags or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the memory item to a dictionary."""
        return {
            "item_id": self.item_id,
            "content": self.content,
            "metadata": self.metadata,
            "source": self.source,
            "timestamp": self.timestamp,
            "importance": self.importance,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryItem':
        """Create a memory item from a dictionary."""
        return cls(
            content=data["content"],
            metadata=data.get("metadata", {}),
            item_id=data.get("item_id"),
            source=data.get("source"),
            timestamp=data.get("timestamp"),
            importance=data.get("importance", 0.5),
            tags=data.get("tags", [])
        )


class BaseMemoryStore(ABC):
    """Abstract base class for memory storage implementations."""
    
    @abstractmethod
    def add(self, item: MemoryItem) -> str:
        """
        Add an item to memory.
        
        Args:
            item: The memory item to add
            
        Returns:
            The ID of the added item
        """
        pass
    
    @abstractmethod
    def get(self, item_id: str) -> Optional[MemoryItem]:
        """
        Retrieve an item from memory by ID.
        
        Args:
            item_id: The ID of the item to retrieve
            
        Returns:
            The memory item if found, None otherwise
        """
        pass
    
    @abstractmethod
    def update(self, item_id: str, item: MemoryItem) -> bool:
        """
        Update an existing item in memory.
        
        Args:
            item_id: The ID of the item to update
            item: The updated memory item
            
        Returns:
            True if the update was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def delete(self, item_id: str) -> bool:
        """
        Delete an item from memory.
        
        Args:
            item_id: The ID of the item to delete
            
        Returns:
            True if the deletion was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def search(self, query: Any, limit: int = 10) -> List[Tuple[MemoryItem, float]]:
        """
        Search for items in memory.
        
        Args:
            query: The search query
            limit: Maximum number of results to return
            
        Returns:
            List of (item, score) tuples, where score indicates relevance
        """
        pass
    
    @abstractmethod
    def list(self, filter_criteria: Optional[Dict[str, Any]] = None, limit: int = 100) -> List[MemoryItem]:
        """
        List items in memory based on filter criteria.
        
        Args:
            filter_criteria: Dictionary of criteria to filter by
            limit: Maximum number of results to return
            
        Returns:
            List of memory items matching the criteria
        """
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """
        Clear all items from memory.
        
        Returns:
            True if the operation was successful, False otherwise
        """
        pass


class ShortTermMemory(BaseMemoryStore):
    """Interface for short-term memory storage."""
    
    @abstractmethod
    def get_recent(self, limit: int = 10) -> List[MemoryItem]:
        """
        Get the most recent items from memory.
        
        Args:
            limit: Maximum number of items to return
            
        Returns:
            List of recent memory items
        """
        pass
    
    @abstractmethod
    def get_context(self, context_id: str) -> List[MemoryItem]:
        """
        Get items related to a specific context.
        
        Args:
            context_id: The context identifier
            
        Returns:
            List of memory items in the context
        """
        pass


class LongTermMemory(BaseMemoryStore):
    """Interface for long-term memory storage."""
    
    @abstractmethod
    def get_by_importance(self, min_importance: float = 0.0, max_importance: float = 1.0, limit: int = 10) -> List[MemoryItem]:
        """
        Get items within an importance range.
        
        Args:
            min_importance: Minimum importance score
            max_importance: Maximum importance score
            limit: Maximum number of items to return
            
        Returns:
            List of memory items within the importance range
        """
        pass
    
    @abstractmethod
    def get_by_tags(self, tags: List[str], match_all: bool = False, limit: int = 10) -> List[MemoryItem]:
        """
        Get items with specific tags.
        
        Args:
            tags: List of tags to match
            match_all: If True, items must have all tags; if False, any tag
            limit: Maximum number of items to return
            
        Returns:
            List of memory items with matching tags
        """
        pass


class EpisodicMemory(BaseMemoryStore):
    """Interface for episodic memory storage."""
    
    @abstractmethod
    def get_by_timerange(self, start_time: float, end_time: float, limit: int = 10) -> List[MemoryItem]:
        """
        Get items within a time range.
        
        Args:
            start_time: Start timestamp
            end_time: End timestamp
            limit: Maximum number of items to return
            
        Returns:
            List of memory items within the time range
        """
        pass
    
    @abstractmethod
    def get_episodes(self, episode_id: str) -> List[MemoryItem]:
        """
        Get all items in a specific episode.
        
        Args:
            episode_id: The episode identifier
            
        Returns:
            List of memory items in the episode
        """
        pass


class SemanticMemory(BaseMemoryStore):
    """Interface for semantic memory storage."""
    
    @abstractmethod
    def semantic_search(self, query: str, limit: int = 10) -> List[Tuple[MemoryItem, float]]:
        """
        Perform semantic search on memory items.
        
        Args:
            query: The search query
            limit: Maximum number of results to return
            
        Returns:
            List of (item, score) tuples, where score indicates semantic similarity
        """
        pass
    
    @abstractmethod
    def get_related(self, item_id: str, limit: int = 10) -> List[Tuple[MemoryItem, float]]:
        """
        Get items semantically related to a specific item.
        
        Args:
            item_id: The ID of the reference item
            limit: Maximum number of results to return
            
        Returns:
            List of (item, score) tuples, where score indicates semantic relatedness
        """
        pass


class DedicatedModelMemory(BaseMemoryStore):
    """Interface for model-specific memory storage."""
    
    @abstractmethod
    def get_model_preferences(self, model_id: str) -> Dict[str, Any]:
        """
        Get preferences for a specific model.
        
        Args:
            model_id: The model identifier
            
        Returns:
            Dictionary of model preferences
        """
        pass
    
    @abstractmethod
    def set_model_preferences(self, model_id: str, preferences: Dict[str, Any]) -> bool:
        """
        Set preferences for a specific model.
        
        Args:
            model_id: The model identifier
            preferences: Dictionary of model preferences
            
        Returns:
            True if the operation was successful, False otherwise
        """
        pass


class SharedMemoryPool(BaseMemoryStore):
    """Interface for shared memory storage."""
    
    @abstractmethod
    def get_shared_context(self, context_id: str) -> List[MemoryItem]:
        """
        Get shared context items.
        
        Args:
            context_id: The context identifier
            
        Returns:
            List of memory items in the shared context
        """
        pass
    
    @abstractmethod
    def add_to_shared_context(self, context_id: str, item: MemoryItem) -> str:
        """
        Add an item to a shared context.
        
        Args:
            context_id: The context identifier
            item: The memory item to add
            
        Returns:
            The ID of the added item
        """
        pass
