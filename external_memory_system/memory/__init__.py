"""
Initialization file for memory package.
"""

__all__ = [
    'MemoryItem',
    'BaseMemoryStore',
    'ShortTermMemory',
    'LongTermMemory',
    'EpisodicMemory',
    'SemanticMemory',
    'DedicatedModelMemory',
    'SharedMemoryPool',
    'InMemoryVectorStore',
    'InMemoryKeyValueStore',
    'InMemoryGraphStore',
    'HybridMemory'
]

from .base import (
    MemoryItem,
    BaseMemoryStore,
    ShortTermMemory,
    LongTermMemory,
    EpisodicMemory,
    SemanticMemory,
    DedicatedModelMemory,
    SharedMemoryPool
)

from .vector_store import InMemoryVectorStore
from .key_value_store import InMemoryKeyValueStore
from .graph_store import InMemoryGraphStore
from .hybrid_memory import HybridMemory

# Add Pinecone if available
try:
    from .pinecone_store import PineconeVectorStore
    __all__.append('PineconeVectorStore')
except ImportError:
    # Pinecone not installed
    pass

