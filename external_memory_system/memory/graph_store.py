"""
Graph database implementation for the External Memory System.
"""

import time
from typing import Any, Dict, List, Optional, Tuple, Union, Set

from .base import BaseMemoryStore, MemoryItem, EpisodicMemory, LongTermMemory


class Node:
    """Node in the graph database."""
    
    def __init__(self, node_id: str, properties: Dict[str, Any] = None):
        self.node_id = node_id
        self.properties = properties or {}


class Edge:
    """Edge in the graph database."""
    
    def __init__(self, source_id: str, target_id: str, relation_type: str, properties: Dict[str, Any] = None):
        self.source_id = source_id
        self.target_id = target_id
        self.relation_type = relation_type
        self.properties = properties or {}


class InMemoryGraphStore(EpisodicMemory, LongTermMemory):
    """In-memory implementation of a graph database for episodic and long-term memory."""
    
    def __init__(self):
        """Initialize an in-memory graph store."""
        self.nodes = {}  # node_id -> Node
        self.edges = []  # list of Edge objects
        self.items = {}  # item_id -> MemoryItem
        self.episodes = {}  # episode_id -> set of item_ids
        self.tags_index = {}  # tag -> set of item_ids
        self.importance_index = {}  # importance (rounded to 0.1) -> set of item_ids
    
    def _add_to_episode(self, item_id: str, episode_id: str):
        """Add an item to an episode."""
        if episode_id not in self.episodes:
            self.episodes[episode_id] = set()
        self.episodes[episode_id].add(item_id)
    
    def _index_by_tags(self, item_id: str, tags: List[str]):
        """Index an item by its tags."""
        for tag in tags:
            if tag not in self.tags_index:
                self.tags_index[tag] = set()
            self.tags_index[tag].add(item_id)
    
    def _index_by_importance(self, item_id: str, importance: float):
        """Index an item by its importance (rounded to 0.1)."""
        # Round to nearest 0.1
        rounded_importance = round(importance * 10) / 10
        if rounded_importance not in self.importance_index:
            self.importance_index[rounded_importance] = set()
        self.importance_index[rounded_importance].add(item_id)
    
    def _create_node_from_item(self, item: MemoryItem) -> str:
        """Create a node from a memory item."""
        # Create node properties from item
        properties = {
            "item_id": item.item_id,
            "content_type": type(item.content).__name__,
            "timestamp": item.timestamp,
            "importance": item.importance,
            "source": item.source,
            "tags": item.tags
        }
        
        # Add metadata as properties
        for key, value in item.metadata.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                properties[f"metadata_{key}"] = value
        
        # Create the node
        node = Node(item.item_id, properties)
        self.nodes[item.item_id] = node
        
        return item.item_id
    
    def _create_edges_from_item(self, item: MemoryItem):
        """Create edges from a memory item to related entities."""
        # Create edges based on metadata
        if "related_to" in item.metadata and isinstance(item.metadata["related_to"], list):
            for related_id in item.metadata["related_to"]:
                if related_id in self.nodes:
                    edge = Edge(
                        source_id=item.item_id,
                        target_id=related_id,
                        relation_type="RELATED_TO",
                        properties={"timestamp": item.timestamp}
                    )
                    self.edges.append(edge)
        
        # Create edges for episode relationships
        if "episode_id" in item.metadata:
            episode_id = item.metadata["episode_id"]
            # Create episode node if it doesn't exist
            if episode_id not in self.nodes:
                episode_node = Node(episode_id, {"type": "episode"})
                self.nodes[episode_id] = episode_node
            
            # Create edge from item to episode
            edge = Edge(
                source_id=item.item_id,
                target_id=episode_id,
                relation_type="PART_OF_EPISODE",
                properties={"timestamp": item.timestamp}
            )
            self.edges.append(edge)
            
            # Add to episodes index
            self._add_to_episode(item.item_id, episode_id)
        
        # Create edges for sequential relationships
        if "previous_id" in item.metadata and item.metadata["previous_id"] in self.nodes:
            edge = Edge(
                source_id=item.metadata["previous_id"],
                target_id=item.item_id,
                relation_type="NEXT",
                properties={"timestamp": item.timestamp}
            )
            self.edges.append(edge)
    
    def add(self, item: MemoryItem) -> str:
        """Add an item to the graph store."""
        # Store the item
        self.items[item.item_id] = item
        
        # Create node and edges
        self._create_node_from_item(item)
        self._create_edges_from_item(item)
        
        # Index by tags and importance
        self._index_by_tags(item.item_id, item.tags)
        self._index_by_importance(item.item_id, item.importance)
        
        return item.item_id
    
    def get(self, item_id: str) -> Optional[MemoryItem]:
        """Retrieve an item by ID."""
        return self.items.get(item_id)
    
    def update(self, item_id: str, item: MemoryItem) -> bool:
        """Update an existing item."""
        if item_id not in self.items:
            return False
        
        # Remove old indices
        old_item = self.items[item_id]
        for tag in old_item.tags:
            if tag in self.tags_index and item_id in self.tags_index[tag]:
                self.tags_index[tag].remove(item_id)
        
        old_importance = round(old_item.importance * 10) / 10
        if old_importance in self.importance_index and item_id in self.importance_index[old_importance]:
            self.importance_index[old_importance].remove(item_id)
        
        # Update the item
        self.items[item_id] = item
        
        # Update node
        if item_id in self.nodes:
            node = self.nodes[item_id]
            node.properties.update({
                "content_type": type(item.content).__name__,
                "timestamp": item.timestamp,
                "importance": item.importance,
                "source": item.source,
                "tags": item.tags
            })
            
            # Update metadata properties
            for key in list(node.properties.keys()):
                if key.startswith("metadata_"):
                    del node.properties[key]
            
            for key, value in item.metadata.items():
                if isinstance(value, (str, int, float, bool)) or value is None:
                    node.properties[f"metadata_{key}"] = value
        
        # Re-index by tags and importance
        self._index_by_tags(item_id, item.tags)
        self._index_by_importance(item_id, item.importance)
        
        return True
    
    def delete(self, item_id: str) -> bool:
        """Delete an item."""
        if item_id not in self.items:
            return False
        
        # Remove from items
        item = self.items[item_id]
        del self.items[item_id]
        
        # Remove from nodes
        if item_id in self.nodes:
            del self.nodes[item_id]
        
        # Remove from edges
        self.edges = [edge for edge in self.edges 
                     if edge.source_id != item_id and edge.target_id != item_id]
        
        # Remove from episodes
        for episode_id, items in self.episodes.items():
            if item_id in items:
                items.remove(item_id)
        
        # Remove from indices
        for tag in item.tags:
            if tag in self.tags_index and item_id in self.tags_index[tag]:
                self.tags_index[tag].remove(item_id)
        
        importance = round(item.importance * 10) / 10
        if importance in self.importance_index and item_id in self.importance_index[importance]:
            self.importance_index[importance].remove(item_id)
        
        return True
    
    def search(self, query: Any, limit: int = 10) -> List[Tuple[MemoryItem, float]]:
        """
        Search for items matching the query.
        
        For graph store, this is a simple text match on content and properties.
        """
        results = []
        query_str = str(query).lower()
        
        for item_id, item in self.items.items():
            # Simple text matching for demonstration
            content_str = str(item.content).lower()
            if query_str in content_str:
                # Calculate a simple relevance score based on occurrence and importance
                score = (content_str.count(query_str) / len(content_str)) * (0.5 + item.importance / 2)
                results.append((item, score))
        
        # Sort by score (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:limit]
    
    def list(self, filter_criteria: Optional[Dict[str, Any]] = None, limit: int = 100) -> List[MemoryItem]:
        """List items based on filter criteria."""
        results = []
        
        # Start with all items
        candidate_ids = set(self.items.keys())
        
        # Apply filters if provided
        if filter_criteria:
            filtered_ids = set()
            
            # Filter by tags (intersection of all tag sets)
            if "tags" in filter_criteria:
                tag_ids = set()
                for tag in filter_criteria["tags"]:
                    if tag in self.tags_index:
                        if not tag_ids:
                            tag_ids = set(self.tags_index[tag])
                        else:
                            tag_ids &= set(self.tags_index[tag])
                
                if "match_all" in filter_criteria and filter_criteria["match_all"]:
                    # For match_all, we use the intersection
                    candidate_ids &= tag_ids
                else:
                    # For match_any, we use the union
                    filtered_ids |= tag_ids
            
            # Filter by importance range
            min_importance = filter_criteria.get("min_importance", 0.0)
            max_importance = filter_criteria.get("max_importance", 1.0)
            
            importance_ids = set()
            for imp, ids in self.importance_index.items():
                if min_importance <= imp <= max_importance:
                    importance_ids |= ids
            
            if importance_ids:
                if filtered_ids:
                    filtered_ids &= importance_ids
                else:
                    filtered_ids = importance_ids
            
            # Filter by time range
            if "min_timestamp" in filter_criteria or "max_timestamp" in filter_criteria:
                min_time = filter_criteria.get("min_timestamp", 0)
                max_time = filter_criteria.get("max_timestamp", float("inf"))
                
                time_ids = set()
                for item_id, item in self.items.items():
                    if min_time <= item.timestamp <= max_time:
                        time_ids.add(item_id)
                
                if time_ids:
                    if filtered_ids:
                        filtered_ids &= time_ids
                    else:
                        filtered_ids = time_ids
            
            # Filter by episode
            if "episode_id" in filter_criteria:
                episode_id = filter_criteria["episode_id"]
                if episode_id in self.episodes:
                    episode_ids = self.episodes[episode_id]
                    if filtered_ids:
                        filtered_ids &= episode_ids
                    else:
                        filtered_ids = episode_ids
            
            # Apply the filtered IDs to candidate IDs
            if filtered_ids:
                candidate_ids &= filtered_ids
        
        # Convert IDs to items
        for item_id in list(candidate_ids)[:limit]:
            results.append(self.items[item_id])
        
        return results
    
    def clear(self) -> bool:
        """Clear all items."""
        self.nodes.clear()
        self.edges.clear()
        self.items.clear()
        self.episodes.clear()
        self.tags_index.clear()
        self.importance_index.clear()
        return True
    
    def get_by_timerange(self, start_time: float, end_time: float, limit: int = 10) -> List[MemoryItem]:
        """Get items within a time range."""
        results = []
        
        for item_id, item in self.items.items():
            if start_time <= item.timestamp <= end_time:
                results.append(item)
        
        # Sort by timestamp (ascending)
        results.sort(key=lambda x: x.timestamp)
        
        return results[:limit]
    
    def get_episodes(self, episode_id: str) -> List[MemoryItem]:
        """Get all items in a specific episode."""
        if episode_id not in self.episodes:
            return []
        
        results = []
        for item_id in self.episodes[episode_id]:
            if item_id in self.items:
                results.append(self.items[item_id])
        
        # Sort by timestamp (ascending) to maintain episode order
        results.sort(key=lambda x: x.timestamp)
        
        return results
    
    def get_by_importance(self, min_importance: float = 0.0, max_importance: float = 1.0, limit: int = 10) -> List[MemoryItem]:
        """Get items within an importance range."""
        results = []
        
        for importance, item_ids in self.importance_index.items():
            if min_importance <= importance <= max_importance:
                for item_id in item_ids:
                    if item_id in self.items:
                        results.append(self.items[item_id])
        
        # Sort by importance (descending)
        results.sort(key=lambda x: x.importance, reverse=True)
        
        return results[:limit]
    
    def get_by_tags(self, tags: List[str], match_all: bool = False, limit: int = 10) -> List[MemoryItem]:
        """Get items with specific tags."""
        if not tags:
            return []
        
        # Find items with matching tags
        matching_ids = set()
        
        if match_all:
            # Items must have all tags
            for tag in tags:
                if tag in self.tags_index:
                    if not matching_ids:
                        matching_ids = set(self.tags_index[tag])
                    else:
                        matching_ids &= set(self.tags_index[tag])
                else:
                    # If any tag is missing, no items can match all tags
                    return []
        else:
            # Items can have any of the tags
            for tag in tags:
                if tag in self.tags_index:
                    matching_ids |= set(self.tags_index[tag])
        
        # Convert IDs to items
        results = []
        for item_id in matching_ids:
            if item_id in self.items:
                results.append(self.items[item_id])
        
        # Sort by importance (descending)
        results.sort(key=lambda x: x.importance, reverse=True)
        
        return results[:limit]
