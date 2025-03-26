# external_memory_system/dashboard/client.py

import requests
import logging
import json
from typing import Dict, Any, Optional
import uuid

class DashboardClient:
    """Client for agents to report activities to the dashboard."""
    
    def __init__(self, dashboard_url: str = "http://localhost:5000") :
        """Initialize the dashboard client.
        
        Args:
            dashboard_url: URL of the dashboard API
        """
        self.dashboard_url = dashboard_url
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def register_agent(self, agent_id: str, agent_name: str, agent_type: str) -> bool:
        """Register an agent with the dashboard.
        
        Args:
            agent_id: Unique identifier for the agent
            agent_name: Display name for the agent
            agent_type: Type of agent (e.g., "bookkeeping", "reconciliation")
            
        Returns:
            True if registration was successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.dashboard_url}/api/agent/register",
                json={
                    "id": agent_id,
                    "name": agent_name,
                    "type": agent_type,
                    "status": "active"
                }
            )
            
            if response.status_code == 200:
                self.logger.info(f"Agent {agent_name} registered successfully")
                return True
            else:
                self.logger.error(f"Failed to register agent: {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Error registering agent: {str(e)}")
            return False
    
    def create_task(self, task_id: str, agent_id: str, task_type: str, description: str = "") -> bool:
        """Create a new task in the dashboard.
        
        Args:
            task_id: Unique identifier for the task
            agent_id: ID of the agent handling the task
            task_type: Type of task (e.g., "journal_entry", "reconcile_transaction")
            description: Optional description of the task
            
        Returns:
            True if task creation was successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.dashboard_url}/api/task/create",
                json={
                    "id": task_id,
                    "agent_id": agent_id,
                    "type": task_type,
                    "status": "pending",
                    "description": description
                }
            )
            
            if response.status_code == 200:
                self.logger.info(f"Task {task_id} created successfully")
                return True
            else:
                self.logger.error(f"Failed to create task: {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Error creating task: {str(e)}")
            return False
    
    def update_task(self, task_id: str, status: str, result: Optional[Dict] = None) -> bool:
        """Update a task's status and result.
        
        Args:
            task_id: ID of the task to update
            status: New status (e.g., "completed", "error", "pending")
            result: Optional result data
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.dashboard_url}/api/task/update",
                json={
                    "id": task_id,
                    "status": status,
                    "result": json.dumps(result) if result else ""
                }
            )
            
            if response.status_code == 200:
                self.logger.info(f"Task {task_id} updated successfully")
                return True
            else:
                self.logger.error(f"Failed to update task: {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Error updating task: {str(e)}")
            return False
    
    def log_message(self, agent_id: str, level: str, message: str) -> bool:
        """Log a message to the dashboard.
        
        Args:
            agent_id: ID of the agent logging the message
            level: Log level (e.g., "INFO", "WARNING", "ERROR")
            message: Log message
            
        Returns:
            True if logging was successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.dashboard_url}/api/log",
                json={
                    "agent_id": agent_id,
                    "level": level,
                    "message": message
                }
            )
            
            if response.status_code == 200:
                return True
            else:
                self.logger.error(f"Failed to log message: {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Error logging message: {str(e)}")
            return False
