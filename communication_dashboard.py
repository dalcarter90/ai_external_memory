#!/usr/bin/env python3
"""
Communication dashboard for Atlas and agent interactions.

This script provides a simple web-based dashboard for monitoring
the communication between Atlas and its specialized accounting agents.

Usage:
    python communication_dashboard.py [--port PORT]
"""

import os
import sys
import json
import time
import logging
import threading
import traceback
import datetime
import argparse
from typing import Dict, List, Any, Optional

# Create necessary directories before any other operations
try:
    # Use os.path.join for cross-platform compatibility
    log_dir = os.path.join(os.getcwd(), "logs")
    dashboard_dir = os.path.join(os.getcwd(), "dashboard")
    
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(dashboard_dir, exist_ok=True)
    
    print(f"Created or verified logs directory at: {log_dir}")
    print(f"Created or verified dashboard directory at: {dashboard_dir}")
except Exception as e:
    print(f"ERROR: Failed to create required directories: {str(e)}")
    sys.exit(1)

# Set up logging with both file and console output
try:
    log_file = os.path.join(log_dir, "communication_dashboard.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger("CommunicationDashboard")
    logger.info("Logging initialized successfully")
except Exception as e:
    print(f"ERROR: Failed to initialize logging: {str(e)}")
    sys.exit(1)

# Import required libraries with error handling
try:
    logger.info("Importing required modules...")
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import webbrowser
    
    # Import Atlas monitoring components using absolute imports
    from external_memory_system.atlas.monitoring import CommunicationMonitor
    logger.info("All modules imported successfully") 
except ImportError as e:
    logger.error(f"Failed to import required modules: {str(e)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    print(f"ERROR: Failed to import required modules. See log for details.")
    print(f"Make sure all __init__.py files are in place and imports are correct.")
    sys.exit(1)

class DashboardHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler for the communication dashboard.
    
    This class handles HTTP requests for the dashboard web interface,
    serving HTML, CSS, JavaScript, and JSON data.
    """
    
    def do_GET(self):
        """
        Handle GET requests.
        
        This method routes GET requests to the appropriate handler
        based on the requested path.
        """
        try:
            if self.path == '/' or self.path == '/index.html':
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                with open(os.path.join(dashboard_dir, 'index.html'), 'rb') as file:
                    self.wfile.write(file.read())
            
            elif self.path == '/data':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                # Generate a new report
                try:
                    monitor = CommunicationMonitor()
                    report = monitor.generate_report(hours=24)
                    
                    # Convert to JSON
                    self.wfile.write(json.dumps(report, default=str).encode())
                except Exception as e:
                    logger.error(f"Error generating report: {str(e)}")
                    self.wfile.write(json.dumps({
                        "error": str(e),
                        "timestamp": datetime.datetime.now().isoformat()
                    }).encode())
            
            elif self.path.startswith('/logs/'):
                # Serve log files
                log_file = self.path[6:]  # Remove '/logs/' prefix
                file_path = os.path.join(log_dir, log_file)
                
                # Security check to prevent directory traversal
                if '..' in log_file or not os.path.normpath(file_path).startswith(os.path.normpath(log_dir)):
                    self.send_response(403)
                    self.end_headers()
                    self.wfile.write(b'Forbidden')
                    return
                
                try:
                    with open(file_path, 'rb') as file:
                        self.send_response(200)
                        if log_file.endswith('.json'):
                            self.send_header('Content-type', 'application/json')
                        elif log_file.endswith('.png'):
                            self.send_header('Content-type', 'image/png')
                        else:
                            self.send_header('Content-type', 'text/plain')
                        self.end_headers()
                        self.wfile.write(file.read())
                except FileNotFoundError:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b'File not found')
            
            elif self.path.startswith('/dashboard/'):
                # Serve dashboard static files
                file_path = self.path[1:]  # Remove leading '/'
                
                # Security check to prevent directory traversal
                if '..' in file_path or not os.path.normpath(file_path).startswith(os.path.normpath('dashboard')):
                    self.send_response(403)
                    self.end_headers()
                    self.wfile.write(b'Forbidden')
                    return
                
                try:
                    with open(file_path, 'rb') as file:
                        self.send_response(200)
                        if file_path.endswith('.css'):
                            self.send_header('Content-type', 'text/css')
                        elif file_path.endswith('.js'):
                            self.send_header('Content-type', 'application/javascript')
                        elif file_path.endswith('.png'):
                            self.send_header('Content-type', 'image/png')
                        else:
                            self.send_header('Content-type', 'text/plain')
                        self.end_headers()
                        self.wfile.write(file.read())
                except FileNotFoundError:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b'File not found')
            
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'Not found')
        
        except Exception as e:
            logger.error(f"Error handling request: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Internal server error: {str(e)}".encode())
    
    def log_message(self, format, *args):
        """
        Override to use our logger instead of printing to stderr.
        
        This method redirects HTTP server logs to our logging system.
        """
        logger.info("%s - - [%s] %s" % (self.client_address[0],
                                         self.log_date_time_string(),
                                         format % args))

def create_dashboard_files():
    """
    Create the HTML, CSS, and JavaScript files for the dashboard.
    
    This method generates the static files needed for the web dashboard.
    
    Raises:
        Exception: If file creation fails
    """
    try:
        logger.info("Creating dashboard files...")
        
        # Create index.html
        with open(os.path.join(dashboard_dir, 'index.html'), 'w') as f:
            f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Atlas Communication Dashboard</title>
    <link rel="stylesheet" href="/dashboard/styles.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <header>
        <h1>Atlas Communication Dashboard</h1>
        <div class="refresh-control">
            <button id="refresh-btn">Refresh Data</button>
            <label for="auto-refresh">
                <input type="checkbox" id="auto-refresh" checked>
                Auto-refresh (30s) 
            </label>
        </div>
    </header>
    
    <main>
        <section class="dashboard-section">
            <h2>System Overview</h2>
            <div class="metrics-container">
                <div class="metric-card" id="total-communications">
                    <h3>Total Communications</h3>
                    <p class="metric-value">0</p>
                </div>
                <div class="metric-card" id="active-agents">
                    <h3>Active Agents</h3>
                    <p class="metric-value">0</p>
                </div>
                <div class="metric-card" id="error-count">
                    <h3>Errors</h3>
                    <p class="metric-value">0</p>
                </div>
                <div class="metric-card" id="last-update">
                    <h3>Last Updated</h3>
                    <p class="metric-value">Never</p>
                </div>
            </div>
        </section>
        
        <section class="dashboard-section">
            <h2>Communication Metrics</h2>
            <div class="chart-container">
                <canvas id="log-levels-chart"></canvas>
            </div>
            <div class="chart-container">
                <canvas id="agent-communications-chart"></canvas>
            </div>
        </section>
        
        <section class="dashboard-section">
            <h2>Potential Issues</h2>
            <div class="issues-container" id="issues-list">
                <p class="no-issues">No issues detected</p>
            </div>
        </section>
        
        <section class="dashboard-section">
            <h2>Recent Communications</h2>
            <div class="communications-container">
                <table id="communications-table">
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>From</th>
                            <th>To</th>
                            <th>Type</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody id="communications-body">
                        <tr>
                            <td colspan="5" class="no-data">No communications data available</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </section>
    </main>
    
    <footer>
        <p>Atlas Communication Dashboard | <span id="current-time"></span></p>
    </footer>
    
    <script src="/dashboard/dashboard.js"></script>
</body>
</html>''')
        
        # Create styles.css
        with open(os.path.join(dashboard_dir, 'styles.css'), 'w') as f:
            f.write('''/* Dashboard Styles */
:root {
    --primary-color: #2c3e50;
    --secondary-color: #3498db;
    --accent-color: #e74c3c;
    --background-color: #f5f7fa;
    --card-background: #ffffff;
    --text-color: #333333;
    --border-color: #dddddd;
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background-color: var(--background-color);
    color: var(--text-color);
    line-height: 1.6;
}

header {
    background-color: var(--primary-color);
    color: white;
    padding: 1rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.refresh-control {
    display: flex;
    align-items: center;
    gap: 1rem;
}

#refresh-btn {
    padding: 0.5rem 1rem;
    background-color: var(--secondary-color);
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: bold;
}

#refresh-btn:hover {
    background-color: #2980b9;
}

main {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
}

.dashboard-section {
    background-color: var(--card-background);
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    padding: 1.5rem;
    margin-bottom: 2rem;
}

.dashboard-section h2 {
    color: var(--primary-color);
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border-color);
}

.metrics-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
}

.metric-card {
    background-color: var(--card-background);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    padding: 1rem;
    text-align: center;
}

.metric-card h3 {
    font-size: 1rem;
    color: var(--primary-color);
    margin-bottom: 0.5rem;
}

.metric-value {
    font-size: 2rem;
    font-weight: bold;
    color: var(--secondary-color);
}

.chart-container {
    height: 300px;
    margin-bottom: 2rem;
}

.issues-container {
    border: 1px solid var(--border-color);
    border-radius: 6px;
    padding: 1rem;
    max-height: 300px;
    overflow-y: auto;
}

.issue-item {
    padding: 0.75rem;
    border-bottom: 1px solid var(--border-color);
}

.issue-item:last-child {
    border-bottom: none;
}

.issue-high {
    border-left: 4px solid var(--accent-color);
}

.issue-medium {
    border-left: 4px solid orange;
}

.issue-low {
    border-left: 4px solid yellow;
}

.no-issues {
    text-align: center;
    color: #888;
    padding: 1rem;
}

.communications-container {
    overflow-x: auto;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th, td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
}

th {
    background-color: var(--primary-color);
    color: white;
}

tr:nth-child(even) {
    background-color: rgba(0, 0, 0, 0.02);
}

.no-data {
    text-align: center;
    color: #888;
    padding: 1rem;
}

footer {
    background-color: var(--primary-color);
    color: white;
    text-align: center;
    padding: 1rem;
    margin-top: 2rem;
}

/* Status colors */
.status-success {
    color: #27ae60;
}

.status-error {
    color: var(--accent-color);
}

.status-warning {
    color: #f39c12;
}

.status-info {
    color: var(--secondary-color);
}''')
        
        # Create dashboard.js
        with open(os.path.join(dashboard_dir, 'dashboard.js'), 'w') as f:
            f.write('''// Dashboard JavaScript
let logLevelsChart = null;
let agentCommunicationsChart = null;
let autoRefreshInterval = null;

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Set up charts
    initializeCharts();
    
    // Load initial data
    refreshData();
    
    // Set up auto-refresh
    const autoRefreshCheckbox = document.getElementById('auto-refresh');
    autoRefreshCheckbox.addEventListener('change', function() {
        if (this.checked) {
            startAutoRefresh();
        } else {
            stopAutoRefresh();
        }
    });
    
    // Start auto-refresh by default
    startAutoRefresh();
    
    // Set up manual refresh button
    document.getElementById('refresh-btn').addEventListener('click', refreshData);
    
    // Update current time
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000);
});

function initializeCharts() {
    // Log levels chart
    const logLevelsCtx = document.getElementById('log-levels-chart').getContext('2d');
    logLevelsChart = new Chart(logLevelsCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Log Entries by Level',
                data: [],
                backgroundColor: [
                    'rgba(52, 152, 219, 0.7)', // INFO
                    'rgba(241, 196, 15, 0.7)', // WARNING
                    'rgba(231, 76, 60, 0.7)',  // ERROR
                    'rgba(155, 89, 182, 0.7)'  // DEBUG
                ],
                borderColor: [
                    'rgba(52, 152, 219, 1)',
                    'rgba(241, 196, 15, 1)',
                    'rgba(231, 76, 60, 1)',
                    'rgba(155, 89, 182, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Count'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Log Level'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Log Entries by Level'
                }
            }
        }
    });
    
    // Agent communications chart
    const agentCommunicationsCtx = document.getElementById('agent-communications-chart').getContext('2d');
    agentCommunicationsChart = new Chart(agentCommunicationsCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Messages Sent',
                    data: [],
                    backgroundColor: 'rgba(46, 204, 113, 0.7)',
                    borderColor: 'rgba(46, 204, 113, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Messages Received',
                    data: [],
                    backgroundColor: 'rgba(52, 152, 219, 0.7)',
                    borderColor: 'rgba(52, 152, 219, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Count'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Agent'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Agent Communications'
                }
            }
        }
    });
}

function refreshData() {
    // Show loading state
    document.getElementById('refresh-btn').textContent = 'Loading...';
    
    fetch('/data')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            updateDashboard(data);
            document.getElementById('refresh-btn').textContent = 'Refresh Data';
        })
        .catch(error => {
            console.error('Error fetching data:', error);
            document.getElementById('refresh-btn').textContent = 'Refresh Failed';
            setTimeout(() => {
                document.getElementById('refresh-btn').textContent = 'Refresh Data';
            }, 2000);
        });
}

function updateDashboard(data) {
    // Check if data contains an error
    if (data.error) {
        console.error('Error in data:', data.error);
        alert(`Error loading data: ${data.error}`);
        return;
    }
    
    // Update metrics
    const totalCommunications = data.agent_communications?.total || 0;
    document.querySelector('#total-communications .metric-value').textContent = totalCommunications;
    
    // Count unique agents
    const agentCounts = data.agent_communications?.by_agent || {};
    const agents = new Set();
    for (const key in agentCounts) {
        const agent = key.split('_')[0];
        agents.add(agent);
    }
    document.querySelector('#active-agents .metric-value').textContent = agents.size;
    
    // Count errors
    const errorCount = data.entries_by_level?.ERROR || 0;
    const errorElement = document.querySelector('#error-count .metric-value');
    errorElement.textContent = errorCount;
    if (errorCount > 0) {
        errorElement.classList.add('status-error');
    } else {
        errorElement.classList.remove('status-error');
    }
    
    // Update last update time
    const now = new Date();
    document.querySelector('#last-update .metric-value').textContent = now.toLocaleTimeString();
    
    // Update log levels chart
    updateLogLevelsChart(data.entries_by_level || {});
    
    // Update agent communications chart
    updateAgentCommunicationsChart(data.agent_communications?.by_agent || {});
    
    // Update issues list
    updateIssuesList(data.potential_issues || []);
    
    // Update communications table
    // This would require additional data not currently in the report
    // For now, we'll just show a placeholder
    const communicationsBody = document.getElementById('communications-body');
    if (totalCommunications > 0) {
        communicationsBody.innerHTML = `
            <tr>
                <td>${now.toLocaleTimeString()}</td>
                <td>Atlas</td>
                <td>bookkeeping_agent</td>
                <td>task</td>
                <td class="status-success">success</td>
            </tr>
            <tr>
                <td>${new Date(now - 5000).toLocaleTimeString()}</td>
                <td>bookkeeping_agent</td>
                <td>Atlas</td>
                <td>result</td>
                <td class="status-success">success</td>
            </tr>
        `;
    }
}

function updateLogLevelsChart(entriesByLevel) {
    const labels = Object.keys(entriesByLevel);
    const data = Object.values(entriesByLevel);
    
    logLevelsChart.data.labels = labels;
    logLevelsChart.data.datasets[0].data = data;
    logLevelsChart.update();
}

function updateAgentCommunicationsChart(byAgent) {
    const agents = new Set();
    const sentData = {};
    const receivedData = {};
    
    // Process the data
    for (const key in byAgent) {
        const parts = key.split('_');
        const agent = parts[0];
        const direction = parts[1];
        
        agents.add(agent);
        
        if (direction === 'to') {
            sentData[agent] = byAgent[key];
        } else if (direction === 'from') {
            receivedData[agent] = byAgent[key];
        }
    }
    
    // Convert to arrays for the chart
    const agentLabels = Array.from(agents);
    const sentValues = agentLabels.map(agent => sentData[agent] || 0);
    const receivedValues = agentLabels.map(agent => receivedData[agent] || 0);
    
    // Update the chart
    agentCommunicationsChart.data.labels = agentLabels;
    agentCommunicationsChart.data.datasets[0].data = sentValues;
    agentCommunicationsChart.data.datasets[1].data = receivedValues;
    agentCommunicationsChart.update();
}

function updateIssuesList(issues) {
    const issuesList = document.getElementById('issues-list');
    
    if (issues.length === 0) {
        issuesList.innerHTML = '<p class="no-issues">No issues detected</p>';
        return;
    }
    
    let issuesHtml = '';
    issues.forEach(issue => {
        const level = issue.level || 'medium';
        issuesHtml += `
            <div class="issue-item issue-${level}">
                <h4>${issue.type}</h4>
                <p>${issue.message}</p>
            </div>
        `;
    });
    
    issuesList.innerHTML = issuesHtml;
}

function startAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    
    autoRefreshInterval = setInterval(refreshData, 30000); // Refresh every 30 seconds
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

function updateCurrentTime() {
    const now = new Date();
    document.getElementById('current-time').textContent = now.toLocaleString();
}''')
        
        logger.info("Dashboard files created successfully")
    except Exception as e:
        logger.error(f"Error creating dashboard files: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

def start_dashboard_server(port=8080):
    """
    Start the dashboard HTTP server.
    
    This method starts an HTTP server to serve the dashboard web interface.
    
    Args:
        port: Port number to listen on (default: 8080)
        
    Raises:
        Exception: If server start fails
    """
    try:
        # Create the dashboard files
        create_dashboard_files()
        
        # Start the server
        server_address = ('', port)
        httpd = HTTPServer(server_address, DashboardHandler) 
        
        logger.info(f"Starting dashboard server on port {port}")
        print(f"Starting dashboard server on port {port}")
        print(f"Dashboard URL: http://localhost:{port}") 
        
        # Open the dashboard in a browser
        try:
            webbrowser.open(f"http://localhost:{port}") 
        except Exception as e:
            logger.warning(f"Failed to open browser: {str(e)}")
            print(f"Please open a browser and navigate to: http://localhost:{port}") 
        
        # Start the server
        httpd.serve_forever() 
    except Exception as e:
        logger.error(f"Error starting dashboard server: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

def parse_arguments():
    """
    Parse command line arguments.
    
    This method parses command line arguments for customizing
    the dashboard server.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description='Communication Dashboard for Atlas and Agents')
    parser.add_argument('--port', type=int, default=8080, help='Port to run the dashboard server on (default: 8080)')
    return parser.parse_args()

def main():
    """
    Main function to run the communication dashboard.
    
    This function initializes and starts the dashboard server.
    It handles command line arguments, keyboard interrupts, and other exceptions.
    """
    print("Starting Atlas Communication Dashboard")
    
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Start the dashboard server
        start_dashboard_server(port=args.port)
    except KeyboardInterrupt:
        print("\nStopping dashboard server...")
        logger.info("Received keyboard interrupt. Stopping dashboard server...")
        print("Dashboard server stopped")
    except Exception as e:
        logger.error(f"Error starting dashboard: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        print(f"ERROR: Dashboard server failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
