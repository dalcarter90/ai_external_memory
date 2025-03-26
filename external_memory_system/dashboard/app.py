# external_memory_system/dashboard/app.py

from flask import Flask, render_template, request, jsonify
import os
import json
import logging
from datetime import datetime, timedelta
import sqlite3
import threading
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dashboard.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AgentDashboard")

# Initialize Flask app
app = Flask(__name__)

# Database setup
DB_PATH = os.path.join(os.path.dirname(__file__), 'agent_activities.db')

def init_db():
    """Initialize the database with required tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS agents (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        status TEXT NOT NULL,
        last_active TIMESTAMP NOT NULL,
        created_at TIMESTAMP NOT NULL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        agent_id TEXT NOT NULL,
        type TEXT NOT NULL,
        status TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP NOT NULL,
        completed_at TIMESTAMP,
        result TEXT,
        FOREIGN KEY (agent_id) REFERENCES agents (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS agent_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT NOT NULL,
        level TEXT NOT NULL,
        message TEXT NOT NULL,
        timestamp TIMESTAMP NOT NULL,
        FOREIGN KEY (agent_id) REFERENCES agents (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS system_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP NOT NULL,
        active_agents INTEGER NOT NULL,
        pending_tasks INTEGER NOT NULL,
        completed_tasks INTEGER NOT NULL,
        error_tasks INTEGER NOT NULL
    )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized")

# Initialize database on startup
init_db()

# API Routes for agents to report activities
@app.route('/api/agent/register', methods=['POST'])
def register_agent():
    """Register a new agent or update existing agent."""
    data = request.json
    
    if not data or not all(k in data for k in ['id', 'name', 'type']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if agent already exists
    cursor.execute("SELECT id FROM agents WHERE id = ?", (data['id'],))
    existing = cursor.fetchone()
    
    now = datetime.now().isoformat()
    
    if existing:
        # Update existing agent
        cursor.execute(
            "UPDATE agents SET name = ?, type = ?, status = ?, last_active = ? WHERE id = ?",
            (data['name'], data['type'], data.get('status', 'active'), now, data['id'])
        )
        message = 'Agent updated'
    else:
        # Insert new agent
        cursor.execute(
            "INSERT INTO agents (id, name, type, status, last_active, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (data['id'], data['name'], data['type'], data.get('status', 'active'), now, now)
        )
        message = 'Agent registered'
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': message, 'agent_id': data['id']}), 200

@app.route('/api/task/create', methods=['POST'])
def create_task():
    """Create a new task."""
    data = request.json
    
    if not data or not all(k in data for k in ['id', 'agent_id', 'type']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    # Insert new task
    cursor.execute(
        "INSERT INTO tasks (id, agent_id, type, status, description, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (data['id'], data['agent_id'], data['type'], data.get('status', 'pending'), 
         data.get('description', ''), now)
    )
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Task created', 'task_id': data['id']}), 200

@app.route('/api/task/update', methods=['POST'])
def update_task():
    """Update an existing task."""
    data = request.json
    
    if not data or not all(k in data for k in ['id', 'status']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    completed_at = now if data['status'] in ['completed', 'error'] else None
    
    # Update task
    cursor.execute(
        "UPDATE tasks SET status = ?, result = ?, completed_at = ? WHERE id = ?",
        (data['status'], data.get('result', ''), completed_at, data['id'])
    )
    
    # Update agent last_active
    cursor.execute(
        "UPDATE agents SET last_active = ? WHERE id = (SELECT agent_id FROM tasks WHERE id = ?)",
        (now, data['id'])
    )
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Task updated', 'task_id': data['id']}), 200

@app.route('/api/log', methods=['POST'])
def log_message():
    """Log a message from an agent."""
    data = request.json
    
    if not data or not all(k in data for k in ['agent_id', 'level', 'message']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    # Insert log
    cursor.execute(
        "INSERT INTO agent_logs (agent_id, level, message, timestamp) VALUES (?, ?, ?, ?)",
        (data['agent_id'], data['level'], data['message'], now)
    )
    
    # Update agent last_active
    cursor.execute(
        "UPDATE agents SET last_active = ? WHERE id = ?",
        (now, data['agent_id'])
    )
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Log recorded'}), 200

# Dashboard Routes
@app.route('/')
def dashboard():
    """Main dashboard view."""
    return render_template('dashboard.html')

@app.route('/agents')
def agents_view():
    """View all agents."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM agents ORDER BY last_active DESC")
    agents = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return render_template('agents.html', agents=agents)

@app.route('/tasks')
def tasks_view():
    """View all tasks."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT t.*, a.name as agent_name 
    FROM tasks t 
    JOIN agents a ON t.agent_id = a.id 
    ORDER BY t.created_at DESC
    LIMIT 100
    """)
    tasks = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return render_template('tasks.html', tasks=tasks)

@app.route('/logs')
def logs_view():
    """View agent logs."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT l.*, a.name as agent_name 
    FROM agent_logs l 
    JOIN agents a ON l.agent_id = a.id 
    ORDER BY l.timestamp DESC
    LIMIT 100
    """)
    logs = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return render_template('logs.html', logs=logs)

# API endpoints for dashboard data
@app.route('/api/dashboard/stats')
def dashboard_stats():
    """Get dashboard statistics."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get agent stats
    cursor.execute("SELECT COUNT(*) FROM agents WHERE status = 'active'")
    active_agents = cursor.fetchone()[0]
    
    # Get task stats
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending'")
    pending_tasks = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'completed'")
    completed_tasks = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'error'")
    error_tasks = cursor.fetchone()[0]
    
    # Get recent activity
    cursor.execute("""
    SELECT t.id, t.type, t.status, t.created_at, a.name as agent_name 
    FROM tasks t 
    JOIN agents a ON t.agent_id = a.id 
    ORDER BY t.created_at DESC
    LIMIT 10
    """)
    recent_activity = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({
        'active_agents': active_agents,
        'pending_tasks': pending_tasks,
        'completed_tasks': completed_tasks,
        'error_tasks': error_tasks,
        'recent_activity': recent_activity
    })

@app.route('/api/dashboard/agent_activity')
def agent_activity():
    """Get agent activity data for charts."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get task counts by agent
    cursor.execute("""
    SELECT a.name, 
           COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed,
           COUNT(CASE WHEN t.status = 'pending' THEN 1 END) as pending,
           COUNT(CASE WHEN t.status = 'error' THEN 1 END) as error
    FROM agents a
    LEFT JOIN tasks t ON a.id = t.agent_id
    GROUP BY a.id
    """)
    agent_tasks = [dict(zip(['agent', 'completed', 'pending', 'error'], row)) for row in cursor.fetchall()]
    
    # Get task types distribution
    cursor.execute("""
    SELECT type, COUNT(*) as count
    FROM tasks
    GROUP BY type
    """)
    task_types = [dict(zip(['type', 'count'], row)) for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({
        'agent_tasks': agent_tasks,
        'task_types': task_types
    })

# Background task to collect system stats
def collect_stats():
    """Collect system statistics periodically."""
    while True:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Get current stats
            cursor.execute("SELECT COUNT(*) FROM agents WHERE status = 'active'")
            active_agents = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending'")
            pending_tasks = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'completed'")
            completed_tasks = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'error'")
            error_tasks = cursor.fetchone()[0]
            
            # Insert stats
            now = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO system_stats (timestamp, active_agents, pending_tasks, completed_tasks, error_tasks) VALUES (?, ?, ?, ?, ?)",
                (now, active_agents, pending_tasks, completed_tasks, error_tasks)
            )
            
            conn.commit()
            conn.close()
            
            # Sleep for 5 minutes
            time.sleep(300)
        except Exception as e:
            logger.error(f"Error collecting stats: {str(e)}")
            time.sleep(60)  # Sleep for 1 minute on error

# Start stats collection in a background thread
stats_thread = threading.Thread(target=collect_stats, daemon=True)
stats_thread.start()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
