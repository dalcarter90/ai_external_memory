"""
Implementation of the accounting agent using local LLM and Pinecone vector storage.
"""

import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path to fix import issues
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Use absolute imports
from external_memory_system.memory.pinecone_store import PineconeVectorStore
from external_memory_system.models.ollama_pinecone_integration import PineconeOllamaIntegration

# Load environment variables
load_dotenv()

def main():
    """Main function to run the accounting agent."""
    print("Initializing Accounting Agent...")
    
    # Initialize Pinecone store with custom implementation for abstract methods
    class CompletePineconeVectorStore(PineconeVectorStore):
        """Extended PineconeVectorStore with implementation of abstract methods."""
        
        def clear(self) -> bool:
            """Clear all items from memory."""
            try:
                # Delete all vectors in the namespace
                self.index.delete(delete_all=True, namespace=self.namespace)
                # Clear local cache
                self.items = {}
                return True
            except Exception as e:
                print(f"Error clearing Pinecone store: {e}")
                return False
        
        def get_related(self, item_id: str, limit: int = 10):
            """Get items related to a specific item."""
            item = self.get(item_id)
            if not item or not item.embedding:
                return []
            
            # Use the item's embedding to find similar items
            results = self.index.query(
                vector=item.embedding,
                top_k=limit + 1,  # +1 because the item itself will be included
                namespace=self.namespace,
                include_metadata=True,
                include_values=True
            )
            
            # Convert results to memory items, excluding the query item
            items = []
            for match in results.matches:
                if match.id != item_id:  # Skip the original item
                    match_item = self.get(match.id)
                    if match_item:
                        items.append((match_item, match.score))
            
            return items
        
        def list(self, limit: int = 100):
            """List items in memory."""
            # This is a simplified implementation
            # In a real implementation, you would fetch items from Pinecone
            return list(self.items.values())[:limit]
    
    try:
        # Initialize the complete Pinecone store
        pinecone_store = CompletePineconeVectorStore(
            index_name=os.getenv("PINECONE_INDEX_NAME"),
            namespace="accounting"
        )
        
        print("Pinecone store initialized successfully.")
        
        # Create integration with local LLM
        integration = PineconeOllamaIntegration(pinecone_store)
        print("Local LLM integration initialized successfully.")
        
        # Example: Add accounting knowledge to memory
        print("Adding accounting knowledge to memory...")
        item_id = integration.add_to_memory(
            "The accounting equation is Assets = Liabilities + Equity. This fundamental equation forms the basis of double-entry bookkeeping.",
            metadata={"category": "accounting_principles", "importance": 0.9}
        )
        
        if item_id:
            print(f"Successfully added item with ID: {item_id}")
        else:
            print("Failed to add item to memory.")
        
        # Example: Query memory and generate response
        print("\nTesting query and response generation...")
        query = "Explain the accounting equation"
        print(f"Query: {query}")
        
        response = integration.generate_with_context(query)
        print(f"Response: {response}")
        
        print("\nAccounting Agent test completed successfully.")
        
    except Exception as e:
        print(f"Error initializing accounting agent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
