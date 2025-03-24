#!/usr/bin/env python3
"""
Enhanced monitoring system for Atlas and agent communication.

This script provides:
1. Real-time monitoring of agent communications
2. Visualization of communication patterns
3. Alert system for communication issues
4. Dashboard for human oversight

Usage:
    python enhanced_monitoring.py
"""

import os
import sys
import time
import json
import logging
import threading
import traceback
import datetime
from typing import Dict, List, Any, Optional

# Create necessary directories before any other operations
try:
    # Use os.path.join for cross-platform compatibility
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    print(f"Created or verified logs directory at: {log_dir}")
except Exception as e:
    print(f"ERROR: Failed to create logs directory: {str(e)}")
    sys.exit(1)

# Set up logging with both file and console output
try:
    log_file = os.path.join(log_dir, "enhanced_monitoring.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger("EnhancedMonitoring")
    logger.info("Logging initialized successfully")
except Exception as e:
    print(f"ERROR: Failed to initialize logging: {str(e)}")
    sys.exit(1)

# Import required libraries with error handling
try:
    logger.info("Importing required modules...")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation
    import numpy as np
    
    # Import Atlas monitoring components using absolute imports
    from external_memory_system.atlas.monitoring import CommunicationMonitor
    logger.info("All modules imported successfully")
except ImportError as e:
    logger.error(f"Failed to import required modules: {str(e)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    print(f"ERROR: Failed to import required modules. See log for details.")
    print(f"Make sure matplotlib is installed: pip install matplotlib")
    print(f"Make sure all __init__.py files are in place and imports are correct.")
    sys.exit(1)

class EnhancedMonitor:
    """
    Enhanced monitoring system for Atlas and agent communication.
    Provides real-time monitoring, visualization, and alerts.
    
    This class monitors communications between Atlas and specialized agents,
    generates visualizations, and alerts on potential issues.
    """
    
    def __init__(self, log_file: str = None, update_interval: int = 5):
        """
        Initialize the enhanced monitor.
        
        Args:
            log_file: Path to the log file to monitor (defaults to atlas_communications.log in logs dir)
            update_interval: Interval in seconds for updating the dashboard (default: 5)
        """
        # Set default log file if not provided
        if log_file is None:
            log_file = os.path.join(log_dir, "atlas_communications.log")
        
        self.log_file = log_file
        self.update_interval = update_interval
        self.monitor = CommunicationMonitor(log_file)
        self.running = False
        self.dashboard_thread = None
        self.alert_thread = None
        self.last_report = None
        
        # Alert thresholds - can be adjusted based on system requirements
        self.alert_thresholds = {
            "error_count": 1,  # Alert if there are any errors
            "missing_responses": 1,  # Alert if there are any missing responses
            "response_time": 10  # Alert if response time exceeds 10 seconds
        }
        
        logger.info(f"Enhanced monitor initialized with log file: {log_file}")
        logger.info(f"Update interval: {update_interval} seconds")
        logger.info(f"Alert thresholds: {self.alert_thresholds}")
    
    def start_monitoring(self):
        """
        Start the monitoring system.
        
        This method starts the dashboard and alert threads to begin
        monitoring Atlas and agent communications.
        
        Raises:
            RuntimeError: If monitoring system is already running
        """
        if self.running:
            logger.warning("Monitoring system is already running")
            return
        
        self.running = True
        
        try:
            # Start the dashboard thread
            self.dashboard_thread = threading.Thread(target=self._dashboard_loop)
            self.dashboard_thread.daemon = True
            self.dashboard_thread.start()
            logger.info("Dashboard thread started")
            
            # Start the alert thread
            self.alert_thread = threading.Thread(target=self._alert_loop)
            self.alert_thread.daemon = True
            self.alert_thread.start()
            logger.info("Alert thread started")
            
            logger.info("Monitoring system started successfully")
        except Exception as e:
            self.running = False
            logger.error(f"Failed to start monitoring threads: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise RuntimeError(f"Failed to start monitoring system: {str(e)}")
    
    def stop_monitoring(self):
        """
        Stop the monitoring system.
        
        This method stops the dashboard and alert threads and
        cleans up resources.
        
        Raises:
            RuntimeError: If monitoring system is not running
        """
        if not self.running:
            logger.warning("Monitoring system is not running")
            return
        
        try:
            self.running = False
            logger.info("Stopping monitoring system...")
            
            # Wait for threads to terminate
            if self.dashboard_thread:
                self.dashboard_thread.join(timeout=2)
                if self.dashboard_thread.is_alive():
                    logger.warning("Dashboard thread did not terminate within timeout")
            
            if self.alert_thread:
                self.alert_thread.join(timeout=2)
                if self.alert_thread.is_alive():
                    logger.warning("Alert thread did not terminate within timeout")
            
            logger.info("Monitoring system stopped")
        except Exception as e:
            logger.error(f"Error stopping monitoring system: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise RuntimeError(f"Failed to stop monitoring system: {str(e)}")
    
    def _dashboard_loop(self):
        """
        Main loop for updating the dashboard.
        
        This method runs in a separate thread and periodically
        generates reports and updates the dashboard.
        """
        logger.info("Dashboard loop started")
        
        while self.running:
            try:
                # Generate a new report
                report = self.monitor.generate_report(hours=1)  # Focus on recent activity
                self.last_report = report
                
                # Update the dashboard
                self._update_dashboard(report)
                
                # Save the report
                self._save_report(report)
                
                # Sleep for the update interval
                time.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error in dashboard loop: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                # Continue running despite errors
                time.sleep(self.update_interval)
    
    def _alert_loop(self):
        """
        Main loop for checking alerts.
        
        This method runs in a separate thread and periodically
        checks for alert conditions in the monitoring reports.
        """
        logger.info("Alert loop started")
        
        while self.running:
            try:
                if self.last_report:
                    # Check for alerts
                    alerts = self._check_alerts(self.last_report)
                    
                    # Handle any alerts
                    if alerts:
                        self._handle_alerts(alerts)
                
                # Sleep for half the update interval to be more responsive
                time.sleep(self.update_interval / 2)
            except Exception as e:
                logger.error(f"Error in alert loop: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                # Continue running despite errors
                time.sleep(self.update_interval)
    
    def _update_dashboard(self, report: Dict):
        """
        Update the dashboard with the latest report.
        
        This method updates the dashboard visualization with
        the latest monitoring data.
        
        Args:
            report: The latest monitoring report
        """
        # In a real implementation, this would update a web dashboard
        # For now, we'll just log the key metrics
        
        total_entries = report.get("total_log_entries", 0)
        entries_by_level = report.get("entries_by_level", {})
        agent_communications = report.get("agent_communications", {})
        potential_issues = report.get("potential_issues", [])
        
        logger.info(f"Dashboard update: {total_entries} log entries")
        logger.info(f"Entries by level: {entries_by_level}")
        logger.info(f"Agent communications: {agent_communications}")
        logger.info(f"Potential issues: {len(potential_issues)}")
        
        # Generate visualization
        try:
            self._generate_visualization(report)
        except Exception as e:
            logger.error(f"Error generating visualization: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _generate_visualization(self, report: Dict):
        """
        Generate visualization of the monitoring data.
        
        This method creates charts and graphs to visualize
        the monitoring data.
        
        Args:
            report: The monitoring report to visualize
            
        Raises:
            Exception: If visualization generation fails
        """
        try:
            # Create a figure with multiple subplots
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
            
            # Plot log entries by level
            entries_by_level = report.get("entries_by_level", {})
            levels = list(entries_by_level.keys())
            counts = list(entries_by_level.values())
            
            if levels and counts:
                ax1.bar(levels, counts)
                ax1.set_title('Log Entries by Level')
                ax1.set_xlabel('Log Level')
                ax1.set_ylabel('Count')
                
                # Add count labels on top of bars
                for i, count in enumerate(counts):
                    ax1.text(i, count + 0.1, str(count), ha='center')
            
            # Plot agent communications
            agent_communications = report.get("agent_communications", {})
            by_agent = agent_communications.get("by_agent", {})
            
            agents = []
            to_counts = []
            from_counts = []
            
            for key, count in by_agent.items():
                if "_to" in key:
                    agent = key.split("_to")[0]
                    if agent not in agents:
                        agents.append(agent)
                        to_counts.append(count)
                        # Find corresponding from count
                        from_key = f"{agent}_from"
                        from_counts.append(by_agent.get(from_key, 0))
            
            if agents and to_counts and from_counts:
                x = np.arange(len(agents))
                width = 0.35
                
                ax2.bar(x - width/2, to_counts, width, label='Messages Sent')
                ax2.bar(x + width/2, from_counts, width, label='Messages Received')
                
                ax2.set_title('Agent Communications')
                ax2.set_xlabel('Agent')
                ax2.set_ylabel('Count')
                ax2.set_xticks(x)
                ax2.set_xticklabels(agents)
                ax2.legend()
                
                # Add count labels on top of bars
                for i, count in enumerate(to_counts):
                    ax2.text(i - width/2, count + 0.1, str(count), ha='center')
                
                for i, count in enumerate(from_counts):
                    ax2.text(i + width/2, count + 0.1, str(count), ha='center')
            
            # Adjust layout and save
            plt.tight_layout()
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            visualization_file = os.path.join(log_dir, f"communication_visualization_{timestamp}.png")
            plt.savefig(visualization_file)
            plt.close()
            
            logger.info(f"Visualization saved to {visualization_file}")
        except Exception as e:
            logger.error(f"Error generating visualization: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def _save_report(self, report: Dict):
        """
        Save the monitoring report to a file.
        
        This method saves the monitoring report to a JSON file
        for later analysis.
        
        Args:
            report: The report to save
            
        Raises:
            Exception: If report saving fails
        """
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = os.path.join(log_dir, f"enhanced_monitoring_report_{timestamp}.json")
            
            with open(report_file, 'w') as f:
                json.dump(report, default=str, indent=2, fp=f)
            
            logger.info(f"Report saved to: {report_file}")
        except Exception as e:
            logger.error(f"Error saving report: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def _check_alerts(self, report: Dict) -> List[Dict]:
        """
        Check for alert conditions in the report.
        
        This method analyzes the monitoring report for conditions
        that should trigger alerts.
        
        Args:
            report: The report to check
            
        Returns:
            A list of alerts
            
        Raises:
            Exception: If alert checking fails
        """
        try:
            alerts = []
            
            # Check for errors
            entries_by_level = report.get("entries_by_level", {})
            error_count = entries_by_level.get("ERROR", 0)
            
            if error_count >= self.alert_thresholds["error_count"]:
                alerts.append({
                    "type": "error_count",
                    "message": f"Found {error_count} error(s) in the logs",
                    "level": "high" if error_count > 5 else "medium"
                })
            
            # Check for missing responses
            potential_issues = report.get("potential_issues", [])
            missing_responses = [issue for issue in potential_issues if issue.get("type") == "missing_responses"]
            
            if missing_responses:
                for issue in missing_responses:
                    agent = issue.get("agent", "unknown")
                    missing = issue.get("missing", 0)
                    
                    if missing >= self.alert_thresholds["missing_responses"]:
                        alerts.append({
                            "type": "missing_responses",
                            "message": f"Agent {agent} has {missing} missing response(s)",
                            "level": "high" if missing > 3 else "medium",
                            "agent": agent
                        })
            
            return alerts
        except Exception as e:
            logger.error(f"Error checking alerts: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    def _handle_alerts(self, alerts: List[Dict]):
        """
        Handle alerts by logging and potentially taking action.
        
        This method processes alerts and takes appropriate actions
        such as logging, sending notifications, etc.
        
        Args:
            alerts: The alerts to handle
            
        Raises:
            Exception: If alert handling fails
        """
        try:
            for alert in alerts:
                alert_type = alert.get("type", "unknown")
                message = alert.get("message", "No message")
                level = alert.get("level", "medium")
                
                if level == "high":
                    logger.error(f"HIGH ALERT: {message}")
                    print(f"HIGH ALERT: {message}")
                else:
                    logger.warning(f"ALERT: {message}")
                    print(f"ALERT: {message}")
                
                # In a real implementation, this could send notifications,
                # trigger automatic recovery actions, etc.
                
                # Save the alert to a file
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                alert_file = os.path.join(log_dir, f"alert_{alert_type}_{timestamp}.json")
                
                with open(alert_file, 'w') as f:
                    json.dump(alert, default=str, indent=2, fp=f)
                
                logger.info(f"Alert saved to: {alert_file}")
        except Exception as e:
            logger.error(f"Error handling alerts: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")

def main():
    """
    Main function to run the enhanced monitoring system.
    
    This function initializes and starts the enhanced monitoring system.
    It handles keyboard interrupts and other exceptions.
    """
    print("Starting Enhanced Monitoring System for Atlas and Agents")
    print("Press Ctrl+C to stop")
    
    # Initialize the enhanced monitor
    try:
        monitor = EnhancedMonitor()
        
        # Start monitoring
        monitor.start_monitoring()
        
        # Keep the main thread running
        logger.info("Enhanced monitoring system is running. Press Ctrl+C to stop.")
        
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\nStopping enhanced monitoring system...")
        logger.info("Received keyboard interrupt. Stopping monitoring system...")
        if 'monitor' in locals():
            monitor.stop_monitoring()
        print("Enhanced monitoring system stopped")
    
    except Exception as e:
        logger.error(f"Error in enhanced monitoring: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        print(f"ERROR: Enhanced monitoring system failed: {str(e)}")
        if 'monitor' in locals():
            try:
                monitor.stop_monitoring()
            except:
                pass
        sys.exit(1)

if __name__ == "__main__":
    main()
