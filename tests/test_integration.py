"""Test integration between local LLM and Pinecone."""

import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from external_memory_system.models.local_llm import LocalLLM
from external_memory_system.memory.vector_store import PineconeVectorStore
from external_memory_system.agents.accounting_agent import AccountingAgent
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

def test_local_llm():
    """Test the local LLM integration."""
    llm = LocalLLM()
    
    # Test text generation
    prompt = "Explain double-entry bookkeeping in simple terms."
    response = llm.generate(prompt)
    print(f"LLM Response: {response}\n")
    
    # Test chat functionality
    messages = [
        {"role": "system", "content": "You are an accounting assistant."},
        {"role": "user", "content": "What is the difference between cash and accrual accounting?"}
    ]
    chat_response = llm.chat(messages)
    print(f"Chat Response: {chat_response}\n")
    
    # Test embedding generation
    text = "Accounts receivable represents money owed to a business by its clients."
    embedding = llm.embed(text)
    print(f"Embedding (first 5 values): {embedding[:5]}\n")
    
    return True

def test_pinecone_integration():
    """Test the Pinecone vector store integration."""
    vector_store = PineconeVectorStore(namespace="test")
    
    # Add items to vector store
    item1_id = vector_store.add_item(
        content="Accounts receivable represents money owed to a business by its clients.",
        metadata={"category": "accounting_terms", "importance": "high"}
    )
    
    item2_id = vector_store.add_item(
        content="Accounts payable represents money a business owes to its suppliers or vendors.",
        metadata={"category": "accounting_terms", "importance": "high"}
    )
    
    item3_id = vector_store.add_item(
        content="Cash flow statement shows how changes in balance sheet accounts and income affect cash and cash equivalents.",
        metadata={"category": "financial_statements", "importance": "medium"}
    )
    
    print(f"Added items with IDs: {item1_id}, {item2_id}, {item3_id}\n")
    
    # Search for items
    results = vector_store.search("money owed to business")
    print("Search results:")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['content']} (Score: {result['score']})")
    
    print("\n")
    
    # Get item by ID
    item = vector_store.get_item(item1_id)
    print(f"Retrieved item: {item['content']}\n")
    
    # Clean up (optional)
    # vector_store.delete_item(item1_id)
    # vector_store.delete_item(item2_id)
    # vector_store.delete_item(item3_id)
    
    return True

def test_accounting_agent():
    """Test the accounting agent."""
    agent = AccountingAgent(name="TestAccountant")
    
    # Add knowledge to agent's memory
    agent.add_to_memory(
        "Accounts receivable represents money owed to a business by its clients.",
        metadata={"category": "accounting_terms"}
    )
    
    agent.add_to_memory(
        "Accounts payable represents money a business owes to its suppliers or vendors.",
        metadata={"category": "accounting_terms"}
    )
    
    agent.add_to_memory(
        "The accounting equation is: Assets = Liabilities + Equity.",
        metadata={"category": "accounting_principles"}
    )
    
    # Test agent with a query
    query = "Explain the difference between accounts receivable and accounts payable."
    response = agent.process_query(query)
    
    print(f"Agent response to query: {response}\n")
    
    # Test chat functionality
    chat_response = agent.chat("How does accounts receivable affect the accounting equation?")
    print(f"Agent chat response: {chat_response}\n")
    
    return True

if __name__ == "__main__":
    print("Testing Local LLM...")
    test_local_llm()
    
    print("Testing Pinecone Integration...")
    test_pinecone_integration()
    
    print("Testing Accounting Agent...")
    test_accounting_agent()
    
    print("All tests completed!")
