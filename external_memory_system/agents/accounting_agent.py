"""Basic accounting agent using local LLM and Pinecone."""

from typing import List, Dict, Any, Optional
from ..models.local_llm import LocalLLM
from ..memory.vector_store import PineconeVectorStore
from external_memory_system.memory.pinecone_store import PineconeVectorStore
from external_memory_system.models.ollama_pinecone_integration import PineconeOllamaIntegration

def main():
    # Initialize Pinecone store
    pinecone_store = PineconeVectorStore(
        index_name=os.getenv("PINECONE_INDEX_NAME"),
        namespace="accounting"
    )
    
    # Create integration with local LLM
    integration = PineconeOllamaIntegration(pinecone_store)
    
    # Example: Add accounting knowledge to memory
    integration.add_to_memory(
        "The accounting equation is Assets = Liabilities + Equity. This fundamental equation forms the basis of double-entry bookkeeping.",
        metadata={"category": "accounting_principles", "importance": 0.9}
    )
    
    # Example: Query memory and generate response
    query = "Explain the accounting equation"
    response = integration.generate_with_context(query)
    print(f"Query: {query}")
    print(f"Response: {response}")

if __name__ == "__main__":
    main()

class AccountingAgent:
    """Agent for handling accounting-related tasks."""
    
    def __init__(
        self,
        name: str = "AccountingAssistant",
        model: str = "mistral:7b-instruct-q4_0"
    ):
        """Initialize the accounting agent.
        
        Args:
            name: Name of the agent
            model: Name of the LLM model to use
        """
        self.name = name
        self.llm = LocalLLM(model=model)
        self.memory = PineconeVectorStore(namespace=f"agent_{name.lower()}")
        self.conversation_history = []
    
    def add_to_memory(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add information to the agent's memory.
        
        Args:
            content: Text content to remember
            metadata: Additional metadata
            
        Returns:
            ID of the memory item
        """
        if metadata is None:
            metadata = {}
        
        metadata["agent"] = self.name
        metadata["type"] = "knowledge"
        
        return self.memory.add_item(content, metadata)
    
    def search_memory(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search the agent's memory.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of matching memory items
        """
        return self.memory.search(
            query=query,
            top_k=top_k,
            filter={"agent": self.name}
        )
    
    def process_query(self, query: str) -> str:
        """Process a user query with memory augmentation.
        
        Args:
            query: User's query text
            
        Returns:
            Agent's response
        """
        # Search for relevant information in memory
        relevant_info = self.search_memory(query)
        
        # Construct context from relevant information
        context = ""
        if relevant_info:
            context = "Relevant information from memory:\n"
            for i, info in enumerate(relevant_info, 1):
                context += f"{i}. {info['content']}\n"
        
        # Construct prompt with context
        prompt = f"""You are {self.name}, an AI accounting assistant.
        
{context}

User query: {query}

Please provide a helpful response based on your accounting knowledge and the information provided.
"""
        
        # Generate response using LLM
        response = self.llm.generate(prompt)
        
        # Update conversation history
        self.conversation_history.append({
            "role": "user",
            "content": query
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        return response
    
    def chat(self, message: str) -> str:
        """Chat with the agent using conversation history.
        
        Args:
            message: User's message
            
        Returns:
            Agent's response
        """
        # Search for relevant information in memory
        relevant_info = self.search_memory(message)
        
        # Construct system message with context
        system_message = f"You are {self.name}, an AI accounting assistant."
        if relevant_info:
            system_message += "\n\nRelevant information from memory:\n"
            for i, info in enumerate(relevant_info, 1):
                system_message += f"{i}. {info['content']}\n"
        
        # Prepare messages for chat
        messages = [
            {"role": "system", "content": system_message}
        ]
        
        # Add conversation history (limited to last 10 exchanges)
        for item in self.conversation_history[-10:]:
            messages.append(item)
        
        # Add user's current message
        messages.append({"role": "user", "content": message})
        
        # Generate response using LLM
        response = self.llm.chat(messages)
        
        # Update conversation history
        self.conversation_history.append({
            "role": "user",
            "content": message
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        return response
