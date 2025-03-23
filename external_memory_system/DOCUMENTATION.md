# External Memory System for AI Models: System Documentation

## Overview

This document provides a comprehensive overview of the External Memory System for AI Models, a system designed to facilitate communication and knowledge sharing between different AI models, specifically ChatGPT and Google Gemini. The system leverages concepts from AutoGen and SuperAGI frameworks to create a robust, scalable, and efficient memory management architecture.

## System Architecture

The External Memory System is built with a layered architecture that separates concerns and provides clear interfaces between components:

### 1. Memory Layer

The memory layer forms the foundation of the system, providing storage and retrieval capabilities for different types of information:

#### 1.1 Memory Types

- **Short-Term Memory**: Temporary storage for ongoing conversations and recent context
- **Long-Term Memory**: Persistent storage for important knowledge and insights
- **Episodic Memory**: Chronological record of interactions and events
- **Semantic Memory**: Conceptual knowledge independent of specific episodes
- **Dedicated Model Memory**: Specific memory spaces for each AI model
- **Shared Memory Pool**: Common knowledge accessible to all models

#### 1.2 Storage Backends

- **Vector Store**: Implements semantic search capabilities using embedding-based retrieval
- **Key-Value Store**: Provides fast access to structured data with expiration capabilities
- **Graph Store**: Represents relationships between concepts and entities
- **Hybrid Memory**: Combines all three stores for comprehensive memory management

### 2. Model Layer

The model layer provides standardized interfaces for interacting with different AI models:

#### 2.1 Model Interfaces

- **Base Model Interface**: Abstract interface defining common operations
- **ChatGPT Adapter**: Implementation for OpenAI's ChatGPT models
- **Gemini Adapter**: Implementation for Google's Gemini models

### 3. Agent Layer

The agent layer manages the memory system and facilitates communication between models:

#### 3.1 Memory Agent

- **Background Processing**: Continuous operation in a separate thread
- **Task Queue**: Asynchronous processing of memory operations
- **User Intervention**: Callback system for user control
- **Communication Facilitation**: Methods for model interaction

### 4. Application Layer

The application layer provides interfaces for users to interact with the system:

#### 4.1 Interactive Interface

- **Command-Line Interface**: User-friendly interface for direct interaction
- **Query Capabilities**: Search and retrieval from memory
- **Model Communication**: Facilitation of inter-model communication

#### 4.2 Testing Framework

- **Automated Tests**: Verification of system functionality
- **Communication Tests**: Validation of model interaction

## Component Details

### Memory Components

#### MemoryItem

The fundamental unit of storage in the system, representing a piece of information with metadata:

```python
class MemoryItem:
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
        # ...
```

#### Vector Store

Implements semantic search capabilities using embedding-based retrieval:

```python
class InMemoryVectorStore(BaseMemoryStore, SemanticMemory):
    def __init__(self, dimension: int = 1536, metric: str = "cosine"):
        # ...
    
    def semantic_search(self, query: str, limit: int = 10) -> List[Tuple[MemoryItem, float]]:
        # ...
```

#### Key-Value Store

Provides fast access to structured data with expiration capabilities:

```python
class InMemoryKeyValueStore(BaseMemoryStore, ShortTermMemory):
    def __init__(self, expire_time: int = 86400):
        # ...
    
    def get_recent(self, limit: int = 10) -> List[MemoryItem]:
        # ...
```

#### Graph Store

Represents relationships between concepts and entities:

```python
class InMemoryGraphStore(BaseMemoryStore, EpisodicMemory, LongTermMemory):
    def __init__(self):
        # ...
    
    def get_episodes(self, episode_id: str) -> List[MemoryItem]:
        # ...
```

#### Hybrid Memory

Combines all three stores for comprehensive memory management:

```python
class HybridMemory(
    BaseMemoryStore, 
    ShortTermMemory, 
    LongTermMemory, 
    EpisodicMemory, 
    SemanticMemory,
    DedicatedModelMemory,
    SharedMemoryPool
):
    def __init__(
        self,
        vector_store: Optional[InMemoryVectorStore] = None,
        key_value_store: Optional[InMemoryKeyValueStore] = None,
        graph_store: Optional[InMemoryGraphStore] = None,
        # ...
    ):
        # ...
```

### Model Components

#### Base Model Interface

Abstract interface defining common operations for AI models:

```python
class BaseModel(ABC):
    @abstractmethod
    def initialize(self) -> bool:
        # ...
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        # ...
    
    @abstractmethod
    def embed(self, text: str) -> List[float]:
        # ...
```

#### ChatGPT Adapter

Implementation for OpenAI's ChatGPT models:

```python
class ChatGPTModel(BaseModel):
    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: Optional[str] = None,
        # ...
    ):
        # ...
```

#### Gemini Adapter

Implementation for Google's Gemini models:

```python
class GeminiModel(BaseModel):
    def __init__(
        self,
        model: str = "gemini-pro",
        api_key: Optional[str] = None,
        # ...
    ):
        # ...
```

### Agent Components

#### Memory Agent

Manages the memory system and facilitates communication between models:

```python
class MemoryAgent:
    def __init__(
        self,
        memory: Optional[HybridMemory] = None,
        chatgpt_model: Optional[BaseModel] = None,
        gemini_model: Optional[BaseModel] = None,
        # ...
    ):
        # ...
    
    def communicate(self, source_model, target_model, query, context_id=None):
        # ...
```

## Communication Flow

The system facilitates communication between AI models through the following flow:

1. **User Query**: The user submits a query to the system
2. **Memory Retrieval**: Relevant context is retrieved from memory
3. **Source Model Generation**: The query and context are sent to the source model
4. **Memory Storage**: The source model's response is stored in memory
5. **Target Model Generation**: The query, context, and source response are sent to the target model
6. **Memory Update**: The target model's response is stored in memory
7. **Result Presentation**: Both responses are presented to the user

## Implementation Details

### Memory Storage

The memory storage implementation uses a hybrid approach combining:

1. **Vector Database**: For semantic search capabilities
   - In-memory implementation for prototype
   - Extensible to external vector databases (Pinecone, Qdrant, etc.)

2. **Key-Value Store**: For fast access to structured data
   - In-memory implementation with expiration capabilities
   - Extensible to external key-value stores (Redis, etc.)

3. **Graph Database**: For relationship representation
   - In-memory implementation with node and edge structures
   - Extensible to external graph databases (Neo4j, etc.)

### Model Integration

The model integration is implemented through adapters that provide a consistent interface:

1. **ChatGPT Integration**:
   - Uses OpenAI API for text generation and embeddings
   - Configurable model selection (default: gpt-4o)

2. **Gemini Integration**:
   - Uses Google AI API for text generation and embeddings
   - Configurable model selection (default: gemini-pro)

### Agent Implementation

The memory agent is implemented as a background service with:

1. **Threading**: Continuous operation in a separate thread
2. **Task Queue**: Asynchronous processing of memory operations
3. **Callback System**: User intervention points for control and monitoring

## Usage Guide

### Installation

To use the External Memory System, follow these steps:

1. Clone the repository
2. Install dependencies
3. Set up API keys for OpenAI and Google AI
4. Run the system

### Basic Usage

The system can be used through the interactive interface:

```bash
python run.py --interactive
```

This will start the system in interactive mode, allowing you to:

- Query the memory system directly
- Get responses from either ChatGPT or Gemini individually
- Facilitate communication between both models

### API Usage

The system can also be used programmatically:

```python
from external_memory_system.memory import HybridMemory
from external_memory_system.models import ChatGPTModel, GeminiModel
from external_memory_system.agent import MemoryAgent

# Initialize components
memory = HybridMemory()
chatgpt = ChatGPTModel(api_key="your_openai_key")
gemini = GeminiModel(api_key="your_google_key")

# Initialize agent
agent = MemoryAgent(memory=memory, chatgpt_model=chatgpt, gemini_model=gemini)

# Start the agent
agent.start()

# Facilitate communication
agent.communicate(
    source_model="chatgpt",
    target_model="gemini",
    query="What are the advantages of hybrid memory systems?",
    context_id="my_context"
)

# Stop the agent when done
agent.stop()
```

## Testing

The system includes a comprehensive testing framework:

```bash
python run.py --test
```

This will run tests for:

- ChatGPT to memory storage
- Google Gemini to memory storage
- Bidirectional communication between models

## Future Enhancements

The current implementation provides a solid foundation for external memory storage between AI models. Future enhancements could include:

1. **Persistent Storage**: Integration with external databases for persistent memory
2. **Additional Models**: Support for other AI models beyond ChatGPT and Gemini
3. **Advanced Memory Management**: Improved algorithms for memory prioritization and forgetting
4. **User Interface**: Web-based interface for easier interaction
5. **Distributed Operation**: Support for distributed memory across multiple instances

## Conclusion

The External Memory System for AI Models provides a robust framework for facilitating communication and knowledge sharing between different AI models. By leveraging concepts from AutoGen and SuperAGI frameworks, the system enables effective collaboration between ChatGPT and Google Gemini models, with the potential to extend to other AI models in the future.
