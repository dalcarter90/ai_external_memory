# run_dashboard.py
from external_memory_system.dashboard.app import app

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)