"""
Key-value store implementation for the External Memory System.
"""

import time
from typing import Any, Dict, List, Optional, Tuple, Union

from .base import BaseMemoryStore, MemoryItem, ShortTermMemory


class InMemoryKeyValueStore(ShortTermMemory):
    """In-memory implementation of a key-value store for short-term memory."""
    
    def __init__(self, expire_time: int = 86400):
        """
        Initialize an in-memory key-value store.
        
        Args:
            expire_time: Default expiration time in seconds (24 hours by default)
        """
        self.items = {}  # id -> (MemoryItem, expiration_time)
        self.contexts = {}  # context_id -> set of item_ids
        self.default_expire_time = expire_time
    
    def _is_expired(self, item_id: str) -> bool:
        """Check if an item has expired."""
        if item_id not in self.items:
            return True
        
        _, expiration_time = self.items[item_id]
        if expiration_time is None:
            return False
        
        return time.time() > expiration_time
    
    def _cleanup_expired(self):
        """Remove expired items."""
        current_time = time.time()
        expired_ids = []
        
        for item_id, (_, expiration_time) in self.items.items():
            if expiration_time is not None and current_time > expiration_time:
                expired_ids.append(item_id)
        
        for item_id in expired_ids:
            self.delete(item_id)
    
    def add(self, item: MemoryItem, expire_time: Optional[int] = None) -> str:
        """
        Add an item to the key-value store.
        
        Args:
            item: The memory item to add
            expire_time: Expiration time in seconds from now, or None for no expiration
            
        Returns:
            The ID of the added item
        """
        # Calculate expiration time
        expiration_time = None
        if expire_time is not None:
            expiration_time = time.time() + expire_time
        elif self.default_expire_time > 0:
            expiration_time = time.time() + self.default_expire_time
        
        # Store the item
        self.items[item.item_id] = (item, expiration_time)
        
        # Add to context if specified in metadata
        if "context_id" in item.metadata:
            context_id = item.metadata["context_id"]
            if context_id not in self.contexts:
                self.contexts[context_id] = set()
            self.contexts[context_id].add(item.item_id)
        
        return item.item_id
    
    def get(self, item_id: str) -> Optional[MemoryItem]:
        """Retrieve an item by ID."""
        self._cleanup_expired()
        
        if item_id not in self.items or self._is_expired(item_id):
            return None
        
        item, _ = self.items[item_id]
        return item
    
    def update(self, item_id: str, item: MemoryItem, expire_time: Optional[int] = None) -> bool:
        """
        Update an existing item.
        
        Args:
            item_id: The ID of the item to update
            item: The updated memory item
            expire_time: New expiration time in seconds from now, or None to keep current
            
        Returns:
            True if the update was successful, False otherwise
        """
        if item_id not in self.items or self._is_expired(item_id):
            return False
        
        # Get current expiration
        _, current_expiration = self.items[item_id]
        
        # Calculate new expiration time
        expiration_time = current_expiration
        if expire_time is not None:
            expiration_time = time.time() + expire_time
        
        # Update the item
        self.items[item_id] = (item, expiration_time)
        
        # Update context mappings if needed
        old_item = self.get(item_id)
        if old_item and "context_id" in old_item.metadata:
            old_context = old_item.metadata["context_id"]
            if old_context in self.contexts and item_id in self.contexts[old_context]:
                self.contexts[old_context].remove(item_id)
        
        if "context_id" in item.metadata:
            new_context = item.metadata["context_id"]
            if new_context not in self.contexts:
                self.contexts[new_context] = set()
            self.contexts[new_context].add(item_id)
        
        return True
    
    def delete(self, item_id: str) -> bool:
        """Delete an item."""
        if item_id not in self.items:
            return False
        
        # Remove from contexts
        item, _ = self.items[item_id]
        if "context_id" in item.metadata:
            context_id = item.metadata["context_id"]
            if context_id in self.contexts and item_id in self.contexts[context_id]:
                self.contexts[context_id].remove(item_id)
                if not self.contexts[context_id]:
                    del self.contexts[context_id]
        
        # Remove the item
        del self.items[item_id]
        
        return True
    
    def search(self, query: Any, limit: int = 10) -> List[Tuple[MemoryItem, float]]:
        """
        Search for items matching the query.
        
        For key-value store, this is a simple text match on content.
        """
        self._cleanup_expired()
        
        results = []
        query_str = str(query).lower()
        
        for item_id, (item, _) in self.items.items():
            if self._is_expired(item_id):
                continue
            
            # Simple text matching for demonstration
            content_str = str(item.content).lower()
            if query_str in content_str:
                # Calculate a simple relevance score based on occurrence
                score = content_str.count(query_str) / len(content_str)
                results.append((item, score))
        
        # Sort by score (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:limit]
    
    def list(self, filter_criteria: Optional[Dict[str, Any]] = None, limit: int = 100) -> List[MemoryItem]:
        """List items based on filter criteria."""
        self._cleanup_expired()
        
        results = []
        
        for item_id, (item, _) in self.items.items():
            if self._is_expired(item_id):
                continue
            
            # Apply filters if provided
            if filter_criteria:
                match = True
                for key, value in filter_criteria.items():
                    if key == "context_id":
                        if key not in self.contexts or item_id not in self.contexts[value]:
                            match = False
                            break
                    elif key == "tags":
                        if not set(value).issubset(set(item.tags)):
                            match = False
                            break
                    elif key == "source":
                        if item.source != value:
                            match = False
                            break
                    elif key in item.metadata:
                        if item.metadata[key] != value:
                            match = False
                            break
                    else:
                        match = False
                        break
                
                if not match:
                    continue
            
            results.append(item)
            
            if len(results) >= limit:
                break
        
        return results
    
    def clear(self) -> bool:
        """Clear all items."""
        self.items.clear()
        self.contexts.clear()
        return True
    
    def get_recent(self, limit: int = 10) -> List[MemoryItem]:
        """Get the most recent items."""
        self._cleanup_expired()
        
        # Sort items by timestamp (descending)
        sorted_items = []
        for item_id, (item, _) in self.items.items():
            if not self._is_expired(item_id):
                sorted_items.append(item)
        
        sorted_items.sort(key=lambda x: x.timestamp, reverse=True)
        
        return sorted_items[:limit]
    
    def get_context(self, context_id: str) -> List[MemoryItem]:
        """Get items related to a specific context."""
        self._cleanup_expired()
        
        if context_id not in self.contexts:
            return []
        
        results = []
        for item_id in self.contexts[context_id]:
            if not self._is_expired(item_id):
                item, _ = self.items[item_id]
                results.append(item)
        
        # Sort by timestamp (ascending) to maintain conversation order
        results.sort(key=lambda x: x.timestamp)
        
        return results
