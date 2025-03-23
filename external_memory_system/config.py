"""
Configuration settings for the External Memory System.
"""

# From /home/ubuntu/ai_external_memory/external_memory_system/config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Pinecone configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

# Local LLM configuration
OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "mistral:7b-instruct-q4_0"
MODEL_TEMPERATURE = 0.7
MODEL_MAX_TOKENS = 4096

# Agent configuration
AGENT_NAME = "AccountingAssistant"

# Database configurations
VECTOR_DB_CONFIG = {
    "type": "in_memory",  # Options: "in_memory", "pinecone", "qdrant", "faiss"
    "dimension": 1536,    # Embedding dimension
    "metric": "cosine",   # Similarity metric
    "index_name": "external_memory_index"
}

KEY_VALUE_DB_CONFIG = {
    "type": "in_memory",  # Options: "in_memory", "redis"
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "expire_time": 86400  # Default expiration time in seconds (24 hours)
}

GRAPH_DB_CONFIG = {
    "type": "in_memory",  # Options: "in_memory", "neo4j"
    "uri": "bolt://localhost:7687",
    "user": "neo4j",
    "password": "password"
}

# Memory configurations
MEMORY_CONFIG = {
    "stm_capacity": 100,          # Maximum number of items in short-term memory
    "stm_retention_time": 3600,   # Short-term memory retention time in seconds (1 hour)
    "ltm_default_importance": 0.5, # Default importance score for long-term memory items
    "memory_refresh_interval": 300 # Memory refresh interval in seconds (5 minutes)
}

# Model configurations
MODEL_CONFIG = {
    "chatgpt": {
        "model": "gpt-4o",
        "api_key_env": "OPENAI_API_KEY",
        "max_tokens": 4096,
        "temperature": 0.7
    },
    "gemini": {
        "model": "gemini-pro",
        "api_key_env": "GOOGLE_API_KEY",
        "max_tokens": 4096,
        "temperature": 0.7
    }
}

# Agent configurations
AGENT_CONFIG = {
    "run_interval": 60,  # Agent run interval in seconds
    "log_level": "INFO", # Logging level
    "max_concurrent_tasks": 5
}

# Serialization configurations
SERIALIZATION_CONFIG = {
    "default_format": "json",  # Options: "json", "pickle", "msgpack"
    "compression": False,      # Whether to compress serialized data
    "encryption": False        # Whether to encrypt serialized data
}
