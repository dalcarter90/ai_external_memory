# external_memory_system/atlas/monitoring.py
import logging
import time
from typing import Dict, List, Optional, Any
import os
import json
from datetime import datetime, timedelta

class CommunicationMonitor:
    """
    Monitors and analyzes communications between Atlas and agents.
    Provides reporting capabilities for human oversight.
    """
    
    def __init__(self, log_file: str = "logs/atlas_communications.log"):
        """
        Initialize the communication monitor.
        
        Args:
            log_file: Path to the log file to monitor
        """
        self.log_file = log_file
        self.logger = logging.getLogger("Atlas.Monitor")
        
        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    def parse_logs(self, hours: int = 24) -> List[Dict]:
        """
        Parse the log file for communications in the specified time period.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            A list of parsed log entries
        """
        if not os.path.exists(self.log_file):
            self.logger.warning(f"Log file not found: {self.log_file}")
            return []
        
        # Calculate the cutoff time
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        log_entries = []
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        # Parse the log line
                        # Example format: 2025-03-24 01:30:45,123 - Atlas - INFO - Sending task to bookkeeping agent
                        parts = line.split(' - ', 3)
                        if len(parts) < 4:
                            continue
                        
                        timestamp_str = parts[0]
                        component = parts[1]
                        level = parts[2]
                        message = parts[3].strip()
                        
                        # Parse the timestamp
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                        
                        # Skip entries older than the cutoff
                        if timestamp < cutoff_time:
                            continue
                        
                        log_entries.append({
                            "timestamp": timestamp,
                            "component": component,
                            "level": level,
                            "message": message
                        })
                    except Exception as e:
                        self.logger.error(f"Error parsing log line: {e}")
                        continue
        except Exception as e:
            self.logger.error(f"Error reading log file: {e}")
        
        return log_entries
    
    def generate_report(self, hours: int = 24) -> Dict:
        """
        Generate a report of communications for the specified time period.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            A report of communications during the specified period
        """
        log_entries = self.parse_logs(hours)
        
        # Count entries by level
        levels = {}
        for entry in log_entries:
            level = entry["level"]
            levels[level] = levels.get(level, 0) + 1
        
        # Extract agent communications
        agent_communications = []
        for entry in log_entries:
            message = entry["message"]
            
            # Look for messages about sending tasks to agents
            if "Sending task to" in message:
                agent = message.split("Sending task to ")[1].split(" ")[0]
                agent_communications.append({
                    "timestamp": entry["timestamp"],
                    "direction": "to",
                    "agent": agent
                })
            
            # Look for messages about receiving results from agents
            elif "Received result from" in message:
                agent = message.split("Received result from ")[1].split(" ")[0]
                agent_communications.append({
                    "timestamp": entry["timestamp"],
                    "direction": "from",
                    "agent": agent
                })
        
        # Count communications by agent
        agent_counts = {}
        for comm in agent_communications:
            agent = comm["agent"]
            direction = comm["direction"]
            key = f"{agent}_{direction}"
            agent_counts[key] = agent_counts.get(key, 0) + 1
        
        # Format the report
        report = {
            "period": {
                "hours": hours,
                "start": (datetime.now() - timedelta(hours=hours)).isoformat(),
                "end": datetime.now().isoformat()
            },
            "total_log_entries": len(log_entries),
            "entries_by_level": levels,
            "agent_communications": {
                "total": len(agent_communications),
                "by_agent": agent_counts
            },
            "potential_issues": self._identify_issues(log_entries, agent_communications)
        }
        
        return report
    
    def _identify_issues(self, log_entries: List[Dict], agent_communications: List[Dict]) -> List[Dict]:
        """
        Identify potential issues in the communications.
        
        Args:
            log_entries: Parsed log entries
            agent_communications: Extracted agent communications
            
        Returns:
            A list of potential issues
        """
        issues = []
        
        # Look for error messages
        for entry in log_entries:
            if entry["level"] == "ERROR":
                issues.append({
                    "type": "error",
                    "timestamp": entry["timestamp"].isoformat(),
                    "message": entry["message"]
                })
        
        # Look for agents that receive tasks but don't return results
        agents_sent = {}
        agents_received = {}
        
        for comm in agent_communications:
            agent = comm["agent"]
            if comm["direction"] == "to":
                agents_sent[agent] = agents_sent.get(agent, 0) + 1
            else:
                agents_received[agent] = agents_received.get(agent, 0) + 1
        
        for agent, sent_count in agents_sent.items():
            received_count = agents_received.get(agent, 0)
            if sent_count > received_count:
                issues.append({
                    "type": "missing_responses",
                    "agent": agent,
                    "tasks_sent": sent_count,
                    "results_received": received_count,
                    "missing": sent_count - received_count
                })
        
        return issues
    
    def save_report(self, report: Dict, filename: Optional[str] = None) -> str:
        """
        Save a report to a file.
        
        Args:
            report: The report to save
            filename: The filename to save to (defaults to a timestamped filename)
            
        Returns:
            The path to the saved report file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"logs/communication_report_{timestamp}.json"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Convert datetime objects to strings
        report_json = json.dumps(report, default=str, indent=2)
        
        with open(filename, 'w') as f:
            f.write(report_json)
        
        self.logger.info(f"Saved communication report to {filename}")
        return filename

def main():
    """Main function to demonstrate monitoring functionality."""
    # Create a sample log file for testing
    os.makedirs("logs", exist_ok=True)
    with open("logs/atlas_communications.log", 'w') as f:
        f.write("2025-03-24 01:30:45,123 - Atlas - INFO - Sending task to bookkeeping agent\n")
        f.write("2025-03-24 01:30:46,456 - Atlas - DEBUG - Task details: {'id': 'task_001', 'type': 'journal_entry'}\n")
        f.write("2025-03-24 01:30:47,789 - Atlas - INFO - Received result from bookkeeping agent\n")
        f.write("2025-03-24 01:30:48,012 - Atlas - DEBUG - Result details: {'status': 'success'}\n")
        f.write("2025-03-24 01:31:45,123 - Atlas - INFO - Sending task to accounts_payable agent\n")
        f.write("2025-03-24 01:31:46,456 - Atlas - DEBUG - Task details: {'id': 'task_002', 'type': 'bill'}\n")
        f.write("2025-03-24 01:31:47,789 - Atlas - ERROR - Error executing task on accounts_payable agent: Agent not implemented\n")
    
    # Initialize the monitor
    monitor = CommunicationMonitor()
    
    # Generate a report
    report = monitor.generate_report()
    
    # Save the report
    report_file = monitor.save_report(report)
    
    print(f"Generated report: {report_file}")
    print(json.dumps(report, default=str, indent=2))

if __name__ == "__main__":
    main()
