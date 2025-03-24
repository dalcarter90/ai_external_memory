// Dashboard JavaScript
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
}