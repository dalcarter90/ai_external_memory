"""
Memory management agent for the External Memory System.
"""

import time
import threading
import queue
import logging
from typing import Any, Dict, List, Optional, Tuple, Union, Callable

from external_memory_system.memory import HybridMemory, MemoryItem
from external_memory_system.models import BaseModel, ChatGPTModel, GeminiModel


class MemoryAgent:
    """
    Agent for managing external memory between AI models.
    
    This agent runs in the background to facilitate communication between
    different AI models (ChatGPT and Google Gemini) through a shared memory system.
    """
    
    def __init__(
        self,
        memory: Optional[HybridMemory] = None,
        chatgpt_model: Optional[BaseModel] = None,
        gemini_model: Optional[BaseModel] = None,
        run_interval: int = 60,
        log_level: str = "INFO",
        use_pinecone: bool = False,
        pinecone_api_key: Optional[str] = None,
        pinecone_environment: Optional[str] = None
    ):
        """
        Initialize the memory management agent.
        
        Args:
            memory: Hybrid memory system (or None to create a new one)
            chatgpt_model: ChatGPT model interface (or None to create a new one)
            gemini_model: Gemini model interface (or None to create a new one)
            run_interval: Interval between agent runs in seconds
            log_level: Logging level
            use_pinecone: Whether to use Pinecone for vector storage
            pinecone_api_key: Pinecone API key
            pinecone_environment: Pinecone environment
        """
        # Initialize memory
        # Initialize memory
        if memory is None:
            if use_pinecone:
                from external_memory_system.memory import PineconeVectorStore
                vector_store = PineconeVectorStore(
                    api_key=pinecone_api_key,
                    environment=pinecone_environment
                )
                memory = HybridMemory(vector_store=vector_store)
            else:
                memory = HybridMemory()

        self.memory = memory
        
        # Initialize models
        self.chatgpt_model = chatgpt_model or ChatGPTModel()
        self.gemini_model = gemini_model or GeminiModel()
        
        # Agent settings
        self.run_interval = run_interval
        self.running = False
        self.thread = None
        self.task_queue = queue.Queue()
        
        # User intervention
        self.user_callbacks = {
            "on_memory_update": [],
            "on_model_communication": [],
            "on_error": []
        }
        
        # Setup logging
        self.logger = logging.getLogger("MemoryAgent")
        level = getattr(logging, log_level.upper(), logging.INFO)
        self.logger.setLevel(level)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def start(self):
        """Start the agent in the background."""
        if self.running:
            self.logger.warning("Agent is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.daemon = True
        self.thread.start()
        
        self.logger.info("Memory agent started")
    
    def stop(self):
        """Stop the agent."""
        if not self.running:
            self.logger.warning("Agent is not running")
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5.0)
            self.thread = None
        
        self.logger.info("Memory agent stopped")
    
    def _run_loop(self):
        """Main agent loop running in background thread."""
        try:
            # Initialize models
            self.chatgpt_model.initialize()
            self.gemini_model.initialize()
            
            while self.running:
                try:
                    # Process any queued tasks
                    self._process_tasks()
                    
                    # Perform regular memory management
                    self._manage_memory()
                    
                    # Sleep until next run
                    time.sleep(self.run_interval)
                
                except Exception as e:
                    self.logger.error(f"Error in agent run loop: {e}")
                    self._notify_callbacks("on_error", {"error": str(e), "source": "run_loop"})
        
        finally:
            # Clean up resources
            try:
                self.chatgpt_model.close()
                self.gemini_model.close()
            except Exception as e:
                self.logger.error(f"Error closing models: {e}")
    
    def _process_tasks(self):
        """Process tasks from the queue."""
        try:
            # Process up to 10 tasks per run to avoid blocking too long
            for _ in range(10):
                try:
                    task = self.task_queue.get(block=False)
                    self._execute_task(task)
                    self.task_queue.task_done()
                except queue.Empty:
                    break
        
        except Exception as e:
            self.logger.error(f"Error processing tasks: {e}")
            self._notify_callbacks("on_error", {"error": str(e), "source": "process_tasks"})
    
    def _execute_task(self, task):
        """Execute a specific task."""
        task_type = task.get("type")
        
        if task_type == "add_memory":
            self._add_memory_item(task.get("content"), task.get("metadata", {}))
        
        elif task_type == "query_memory":
            result = self._query_memory(task.get("query"), task.get("limit", 10))
            callback = task.get("callback")
            if callback:
                callback(result)
        
        elif task_type == "model_communication":
            self._facilitate_model_communication(
                task.get("source_model"),
                task.get("target_model"),
                task.get("query"),
                task.get("context_id")
            )
        
        elif task_type == "update_model_preferences":
            self._update_model_preferences(
                task.get("model_id"),
                task.get("preferences", {})
            )
        
        else:
            self.logger.warning(f"Unknown task type: {task_type}")
    
    def _manage_memory(self):
        """Perform regular memory management tasks."""
        try:
            # Refresh shared contexts
            self._refresh_shared_contexts()
            
            # Update model knowledge
            self._update_model_knowledge()
            
            # Clean up old memories
            self._cleanup_old_memories()
        
        except Exception as e:
            self.logger.error(f"Error in memory management: {e}")
            self._notify_callbacks("on_error", {"error": str(e), "source": "manage_memory"})
    
    def _refresh_shared_contexts(self):
        """Refresh shared memory contexts."""
        # This would update shared contexts based on recent interactions
        # For demonstration purposes, we'll just log the action
        self.logger.debug("Refreshing shared contexts")
    
    def _update_model_knowledge(self):
        """Update model knowledge based on memory contents."""
        # This would update model knowledge based on memory contents
        # For demonstration purposes, we'll just log the action
        self.logger.debug("Updating model knowledge")
    
    def _cleanup_old_memories(self):
        """Clean up old or less important memories."""
        # This would clean up old or less important memories
        # For demonstration purposes, we'll just log the action
        self.logger.debug("Cleaning up old memories")
    
    def _add_memory_item(self, content, metadata=None):
        """Add an item to memory."""
        try:
            # Create memory item
            item = MemoryItem(
                content=content,
                metadata=metadata or {},
                source=metadata.get("source") if metadata else None
            )
            
            # Add to memory
            item_id = self.memory.add(item)
            
            self.logger.info(f"Added memory item: {item_id}")
            self._notify_callbacks("on_memory_update", {"action": "add", "item_id": item_id})
            
            return item_id
        
        except Exception as e:
            self.logger.error(f"Error adding memory item: {e}")
            self._notify_callbacks("on_error", {"error": str(e), "source": "add_memory_item"})
            return None
    
    def _query_memory(self, query, limit=10):
        """Query memory for relevant items."""
        try:
            results = self.memory.search(query, limit=limit)
            
            self.logger.info(f"Memory query: '{query}' returned {len(results)} results")
            
            return results
        
        except Exception as e:
            self.logger.error(f"Error querying memory: {e}")
            self._notify_callbacks("on_error", {"error": str(e), "source": "query_memory"})
            return []
    
    def _facilitate_model_communication(self, source_model, target_model, query, context_id=None):
        """Facilitate communication between models."""
        try:
            # Get the appropriate model interfaces
            source = self._get_model_interface(source_model)
            target = self._get_model_interface(target_model)
            
            if not source or not target:
                self.logger.error(f"Invalid model specified: {source_model} or {target_model}")
                return None
            
            # Get context from memory if provided
            context = ""
            if context_id:
                context_items = self.memory.get_shared_context(context_id)
                context = "\n".join([str(item.content) for item in context_items])
            
            # Prepare prompt for source model
            source_prompt = f"Context:\n{context}\n\nQuery: {query}\n\nPlease provide your response:"
            
            # Get response from source model
            source_response = source.generate(source_prompt)
            
            # Add to memory
            source_memory_id = self._add_memory_item(
                content=source_response,
                metadata={
                    "source": source_model,
                    "query": query,
                    "context_id": context_id,
                    "memory_type": "short_term"
                }
            )
            
            # Prepare prompt for target model
            target_prompt = f"Context:\n{context}\n\nQuery: {query}\n\nResponse from {source_model}:\n{source_response}\n\nPlease provide your response or improvement:"
            
            # Get response from target model
            target_response = target.generate(target_prompt)
            
            # Add to memory
            target_memory_id = self._add_memory_item(
                content=target_response,
                metadata={
                    "source": target_model,
                    "query": query,
                    "context_id": context_id,
                    "related_to": [source_memory_id] if source_memory_id else [],
                    "memory_type": "short_term"
                }
            )
            
            # Create a combined response
            combined_response = {
                "source_model": source_model,
                "source_response": source_response,
                "source_memory_id": source_memory_id,
                "target_model": target_model,
                "target_response": target_response,
                "target_memory_id": target_memory_id,
                "context_id": context_id
            }
            
            self.logger.info(f"Facilitated communication between {source_model} and {target_model}")
            self._notify_callbacks("on_model_communication", combined_response)
            
            return combined_response
        
        except Exception as e:
            self.logger.error(f"Error facilitating model communication: {e}")
            self._notify_callbacks("on_error", {"error": str(e), "source": "facilitate_model_communication"})
            return None
    
    def _get_model_interface(self, model_id):
        """Get the appropriate model interface based on model ID."""
        if model_id.lower() in ["chatgpt", "gpt", "openai"]:
            return self.chatgpt_model
        elif model_id.lower() in ["gemini", "google"]:
            return self.gemini_model
        else:
            return None
    
    def _update_model_preferences(self, model_id, preferences):
        """Update preferences for a specific model."""
        try:
            success = self.memory.set_model_preferences(model_id, preferences)
            
            if success:
                self.logger.info(f"Updated preferences for model: {model_id}")
                self._notify_callbacks("on_memory_update", {
                    "action": "update_preferences",
                    "model_id": model_id
                })
            
            return success
        
        except Exception as e:
            self.logger.error(f"Error updating model preferences: {e}")
            self._notify_callbacks("on_error", {"error": str(e), "source": "update_model_preferences"})
            return False
    
    def _notify_callbacks(self, event_type, data):
        """Notify registered callbacks for an event."""
        if event_type in self.user_callbacks:
            for callback in self.user_callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    self.logger.error(f"Error in callback for {event_type}: {e}")
    
    # Public API methods
    
    def add_memory(self, content, metadata=None):
        """
        Add an item to memory (queued for background processing).
        
        Args:
            content: The content to store
            metadata: Additional metadata
            
        Returns:
            Task ID for the queued task
        """
        task_id = f"task_{time.time()}_{id(content)}"
        self.task_queue.put({
            "id": task_id,
            "type": "add_memory",
            "content": content,
            "metadata": metadata or {}
        })
        return task_id
    
    def query_memory(self, query, limit=10, callback=None):
        """
        Query memory for relevant items (queued for background processing).
        
        Args:
            query: The search query
            limit: Maximum number of results
            callback: Function to call with results
            
        Returns:
            Task ID for the queued task
        """
        task_id = f"task_{time.time()}_{id(query)}"
        self.task_queue.put({
            "id": task_id,
            "type": "query_memory",
            "query": query,
            "limit": limit,
            "callback": callback
        })
        return task_id
    
    def communicate(self, source_model, target_model, query, context_id=None):
        """
        Facilitate communication between models (queued for background processing).
        
        Args:
            source_model: ID of the source model
            target_model: ID of the target model
            query: The query or prompt
            context_id: Optional context ID for shared memory
            
        Returns:
            Task ID for the queued task
        """
        task_id = f"task_{time.time()}_{id(query)}"
        self.task_queue.put({
            "id": task_id,
            "type": "model_communication",
            "source_model": source_model,
            "target_model": target_model,
            "query": query,
            "context_id": context_id
        })
        return task_id
    
    def update_preferences(self, model_id, preferences):
        """
        Update preferences for a specific model (queued for background processing).
        
        Args:
            model_id: ID of the model
            preferences: Dictionary of preferences
            
        Returns:
            Task ID for the queued task
        """
        task_id = f"task_{time.time()}_{id(preferences)}"
        self.task_queue.put({
            "id": task_id,
            "type": "update_model_preferences",
            "model_id": model_id,
            "preferences": preferences
        })
        return task_id
    
    def register_callback(self, event_type, callback):
        """
        Register a callback for a specific event type.
        
        Args:
            event_type: Type of event ("on_memory_update", "on_model_communication", "on_error")
            callback: Function to call when event occurs
            
        Returns:
            True if registration was successful, False otherwise
        """
        if event_type in self.user_callbacks:
            self.user_callbacks[event_type].append(callback)
            return True
        return False
    
    def unregister_callback(self, event_type, callback):
        """
        Unregister a callback for a specific event type.
        
        Args:
            event_type: Type of event
            callback: Function to unregister
            
        Returns:
            True if unregistration was successful, False otherwise
        """
        if event_type in self.user_callbacks and callback in self.user_callbacks[event_type]:
            self.user_callbacks[event_type].remove(callback)
            return True
        return False
