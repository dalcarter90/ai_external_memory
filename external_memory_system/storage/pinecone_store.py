"""
Pinecone vector store implementation for the External Memory System.
"""

import os
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union

import pinecone
from external_memory_system.memory.base import BaseMemoryStore, MemoryItem, SemanticMemory


class PineconeVectorStore(SemanticMemory):
    """Vector store implementation using Pinecone."""

    def __init__(
            self,
            api_key: Optional[str] = None,
            environment: Optional[str] = None,
            index_name: str = "external-memory",
            namespace: str = "default",
            dimension: int = 1536,
            metric: str = "cosine",
            api_key_env: str = "PINECONE_API_KEY",
            environment_env: str = "PINECONE_ENVIRONMENT"
    ):
        """
        Initialize the Pinecone vector store.

        Args:
            api_key: Pinecone API key (if None, will use environment variable)
            environment: Pinecone environment (if None, will use environment variable)
            index_name: Name of the Pinecone index
            namespace: Namespace within the index
            dimension: Dimension of the vectors
            metric: Distance metric to use
            api_key_env: Name of environment variable containing API key
            environment_env: Name of environment variable containing environment
        """
        super().__init__()

        self.api_key = api_key or os.environ.get(api_key_env)
        self.environment = environment or os.environ.get(environment_env)
        self.index_name = index_name
        self.namespace = namespace
        self.dimension = dimension
        self.metric = metric

        if not self.api_key:
            raise ValueError(
                f"Pinecone API key not found. Please provide it directly or set the {api_key_env} environment variable.")

        if not self.environment:
            raise ValueError(
                f"Pinecone environment not found. Please provide it directly or set the {environment_env} environment variable.")

        # Initialize Pinecone
        pinecone.init(api_key=self.api_key, environment=self.environment)

        # Check if index exists, create if not
        if self.index_name not in pinecone.list_indexes():
            pinecone.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric=self.metric
            )

        # Connect to index
        self.index = pinecone.Index(self.index_name)

        # Local cache for memory items
        self.items = {}

    def add(self, item: MemoryItem) -> str:
        """
        Add an item to memory.

        Args:
            item: The memory item to add

        Returns:
            The ID of the added item
        """
        # Generate ID if not provided
        if not item.item_id:
            item.item_id = str(uuid.uuid4())

        # Get embedding for the content
        embedding = item.embedding

        # If no embedding is provided, we can't add to vector store
        if embedding is None:
            raise ValueError("Item must have an embedding to be added to vector store")

        # Store in Pinecone
        self.index.upsert(
            vectors=[(item.item_id, embedding, {
                "content": str(item.content)[:1000],  # Truncate for metadata
                "source": item.source or "unknown",
                "timestamp": item.timestamp,
                "importance": item.importance
            })],
            namespace=self.namespace
        )

        # Store in local cache
        self.items[item.item_id] = item

        return item.item_id

    def get(self, item_id: str) -> Optional[MemoryItem]:
        """
        Get an item from memory by ID.

        Args:
            item_id: The ID of the item to get

        Returns:
            The memory item, or None if not found
        """
        # Check local cache first
        if item_id in self.items:
            return self.items[item_id]

        # Query Pinecone
        result = self.index.fetch(ids=[item_id], namespace=self.namespace)

        if item_id in result.vectors:
            vector = result.vectors[item_id]

            # Create memory item from vector
            item = MemoryItem(
                content=vector.metadata.get("content", ""),
                metadata={
                    "source": vector.metadata.get("source", "unknown"),
                    "importance": float(vector.metadata.get("importance", 0.5))
                },
                item_id=item_id,
                timestamp=float(vector.metadata.get("timestamp", time.time())),
                embedding=vector.values
            )

            # Update local cache
            self.items[item_id] = item

            return item

        return None

    def update(self, item: MemoryItem) -> bool:
        """
        Update an item in memory.

        Args:
            item: The memory item to update

        Returns:
            True if the update was successful, False otherwise
        """
        # Check if item exists
        if not item.item_id or item.item_id not in self.items:
            return False

        # Get embedding for the content
        embedding = item.embedding

        # If no embedding is provided, we can't update in vector store
        if embedding is None:
            raise ValueError("Item must have an embedding to be updated in vector store")

        # Update in Pinecone
        self.index.upsert(
            vectors=[(item.item_id, embedding, {
                "content": str(item.content)[:1000],  # Truncate for metadata
                "source": item.source or "unknown",
                "timestamp": item.timestamp,
                "importance": item.importance
            })],
            namespace=self.namespace
        )

        # Update local cache
        self.items[item.item_id] = item

        return True

    def delete(self, item_id: str) -> bool:
        """
        Delete an item from memory.

        Args:
            item_id: The ID of the item to delete

        Returns:
            True if the deletion was successful, False otherwise
        """
        # Check if item exists
        if item_id not in self.items:
            return False

        # Delete from Pinecone
        self.index.delete(ids=[item_id], namespace=self.namespace)

        # Delete from local cache
        del self.items[item_id]

        return True

    def search(self, query: str, limit: int = 10) -> List[Tuple[MemoryItem, float]]:
        """
        Search for items in memory.

        Args:
            query: The search query
            limit: Maximum number of results

        Returns:
            List of (item, score) tuples
        """
        # Get embedding for query
        # Note: This requires access to a model for embedding
        # You'll need to modify this to use your embedding model
        embedding = self._get_embedding_for_query(query)

        if embedding is None:
            return []

        # Query Pinecone
        results = self.index.query(
            vector=embedding,
            top_k=limit,
            namespace=self.namespace,
            include_metadata=True,
            include_values=True
        )

        # Convert results to memory items
        items = []
        for match in results.matches:
            item_id = match.id
            score = match.score

            # Get or create memory item
            if item_id in self.items:
                item = self.items[item_id]
            else:
                item = MemoryItem(
                    content=match.metadata.get("content", ""),
                    metadata={
                        "source": match.metadata.get("source", "unknown"),
                        "importance": float(match.metadata.get("importance", 0.5))
                    },
                    item_id=item_id,
                    timestamp=float(match.metadata.get("timestamp", time.time())),
                    embedding=match.values
                )
                self.items[item_id] = item

            items.append((item, score))

        return items

    def semantic_search(self, query: str, limit: int = 10) -> List[Tuple[MemoryItem, float]]:
        """
        Search for semantically similar items.

        Args:
            query: The search query
            limit: Maximum number of results

        Returns:
            List of (item, score) tuples
        """
        return self.search(query, limit)

    def _get_embedding_for_query(self, query: str) -> Optional[List[float]]:
        """
        Get embedding for a query.

        Args:
            query: The query text

        Returns:
            The embedding vector
        """
        try:
            from external_memory_system.models import ChatGPTModel

            # Create model instance
            model = ChatGPTModel()
            model.initialize()

            # Get embedding
            embedding = model.embed(query)

            # Close model
            model.close()

            return embedding

        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None

    def close(self):
        """Close the connection to Pinecone."""
        # Pinecone client doesn't require explicit closing
        pass


def clear(self) -> bool:
    """
    Clear all items from memory.

    Returns:
        True if the operation was successful, False otherwise
    """
    try:
        # Delete all vectors in the namespace
        self.index.delete(delete_all=True, namespace=self.namespace)

        # Clear local cache
        self.items = {}

        return True

    except Exception as e:
        print(f"Error clearing Pinecone store: {e}")
        return False


def get_related(self, item_id: str, limit: int = 10) -> List[Tuple[MemoryItem, float]]:
    """
    Get items related to a specific item.

    Args:
        item_id: The ID of the reference item
        limit: Maximum number of results

    Returns:
        List of (item, score) tuples
    """
    # Get the item
    item = self.get(item_id)

    if not item or not item.embedding:
        return []

    # Query Pinecone using the item's embedding
    results = self.index.query(
        vector=item.embedding,
        top_k=limit + 1,  # Add 1 to account for the item itself
        namespace=self.namespace,
        include_metadata=True,
        include_values=True
    )

    # Convert results to memory items, excluding the query item itself
    items = []
    for match in results.matches:
        if match.id != item_id:  # Skip the query item
            match_item_id = match.id
            score = match.score

            # Get or create memory item
            if match_item_id in self.items:
                match_item = self.items[match_item_id]
            else:
                match_item = MemoryItem(
                    content=match.metadata.get("content", ""),
                    metadata={
                        "source": match.metadata.get("source", "unknown"),
                        "importance": float(match.metadata.get("importance", 0.5))
                    },
                    item_id=match_item_id,
                    timestamp=float(match.metadata.get("timestamp", time.time())),
                    embedding=match.values
                )
                self.items[match_item_id] = match_item

            items.append((match_item, score))

    return items


def list(self, limit: int = 100) -> List[MemoryItem]:
    """
    List all items in memory.

    Args:
        limit: Maximum number of items to return

    Returns:
        List of memory items
    """
    # This is a bit tricky with Pinecone as it doesn't have a direct "list all" operation
    # We'll use the local cache for this, which might not be complete

    # If local cache is empty or has fewer items than limit, try to fetch some items
    if len(self.items) < limit:
        try:
            # Create a dummy query that should match many items
            # This is not ideal but a workaround for Pinecone's lack of "list all" functionality
            results = self.index.query(
                vector=[0.0] * self.dimension,  # Zero vector
                top_k=limit,
                namespace=self.namespace,
                include_metadata=True,
                include_values=True
            )

            # Add results to local cache
            for match in results.matches:
                item_id = match.id

                if item_id not in self.items:
                    item = MemoryItem(
                        content=match.metadata.get("content", ""),
                        metadata={
                            "source": match.metadata.get("source", "unknown"),
                            "importance": float(match.metadata.get("importance", 0.5))
                        },
                        item_id=item_id,
                        timestamp=float(match.metadata.get("timestamp", time.time())),
                        embedding=match.values
                    )
                    self.items[item_id] = item

        except Exception as e:
            print(f"Error listing items from Pinecone: {e}")

    # Return items from local cache, limited to the requested number
    return list(self.items.values())[:limit]
