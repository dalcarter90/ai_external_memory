# external_memory_system/atlas/communication.py
import json
import logging
from typing import Dict, Any, List, Optional
import time

class Message:
    """Represents a message between Atlas and an agent."""
    
    def __init__(self, sender: str, receiver: str, content: Dict, message_type: str = "task"):
        """
        Initialize a new message.
        
        Args:
            sender: The sender of the message
            receiver: The receiver of the message
            content: The content of the message
            message_type: The type of message (task, result, error, etc.)
        """
        self.sender = sender
        self.receiver = receiver
        self.content = content
        self.message_type = message_type
        self.timestamp = time.time()
        self.message_id = f"{int(self.timestamp)}_{sender}_{receiver}"
    
    def to_dict(self) -> Dict:
        """Convert the message to a dictionary."""
        return {
            "id": self.message_id,
            "sender": self.sender,
            "receiver": self.receiver,
            "content": self.content,
            "type": self.message_type,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Message':
        """Create a message from a dictionary."""
        message = cls(
            sender=data["sender"],
            receiver=data["receiver"],
            content=data["content"],
            message_type=data["type"]
        )
        message.timestamp = data["timestamp"]
        message.message_id = data["id"]
        return message

class CommunicationBus:
    """
    Handles communication between Atlas and agents.
    Provides logging and monitoring of all communications.
    """
    
    def __init__(self):
        """Initialize the communication bus."""
        self.logger = logging.getLogger("Atlas.CommunicationBus")
        self.messages = []  # Store all messages for monitoring
    
    def send_message(self, message: Message) -> None:
        """
        Send a message from one component to another.
        
        Args:
            message: The message to send
        """
        self.logger.info(f"Message sent: {message.sender} -> {message.receiver} ({message.message_type})")
        self.logger.debug(f"Message content: {message.content}")
        
        # Store the message for monitoring
        self.messages.append(message.to_dict())
        
        # In a real implementation, this would actually deliver the message
        # For now, we just log it
    
    def get_messages(self, 
                    sender: Optional[str] = None, 
                    receiver: Optional[str] = None, 
                    message_type: Optional[str] = None,
                    start_time: Optional[float] = None,
                    end_time: Optional[float] = None) -> List[Dict]:
        """
        Get messages matching the specified criteria.
        
        Args:
            sender: Filter by sender
            receiver: Filter by receiver
            message_type: Filter by message type
            start_time: Filter by start time (timestamp)
            end_time: Filter by end time (timestamp)
            
        Returns:
            A list of messages matching the criteria
        """
        filtered_messages = self.messages
        
        if sender:
            filtered_messages = [m for m in filtered_messages if m["sender"] == sender]
        
        if receiver:
            filtered_messages = [m for m in filtered_messages if m["receiver"] == receiver]
        
        if message_type:
            filtered_messages = [m for m in filtered_messages if m["type"] == message_type]
        
        if start_time:
            filtered_messages = [m for m in filtered_messages if m["timestamp"] >= start_time]
        
        if end_time:
            filtered_messages = [m for m in filtered_messages if m["timestamp"] <= end_time]
        
        return filtered_messages
    
    def generate_report(self, 
                       start_time: Optional[float] = None,
                       end_time: Optional[float] = None) -> Dict:
        """
        Generate a report of communications.
        
        Args:
            start_time: Start time for the report period
            end_time: End time for the report period
            
        Returns:
            A report of communications during the specified period
        """
        # Default to last 24 hours if no time range specified
        if not end_time:
            end_time = time.time()
        
        if not start_time:
            start_time = end_time - (24 * 60 * 60)  # 24 hours
        
        messages = self.get_messages(start_time=start_time, end_time=end_time)
        
        # Count messages by type
        message_types = {}
        for message in messages:
            message_type = message["type"]
            message_types[message_type] = message_types.get(message_type, 0) + 1
        
        # Count messages by sender/receiver pair
        communication_pairs = {}
        for message in messages:
            pair = f"{message['sender']} -> {message['receiver']}"
            communication_pairs[pair] = communication_pairs.get(pair, 0) + 1
        
        return {
            "period": {
                "start": start_time,
                "end": end_time
            },
            "total_messages": len(messages),
            "message_types": message_types,
            "communication_pairs": communication_pairs
        }
