# gunicorn.conf.py
import os
import multiprocessing

# Project paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Ensure logs directory exists
os.makedirs(LOGS_DIR, exist_ok=True)

# Gunicorn configuration
bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"  # Use 'eventlet' or 'gevent' for async if needed
worker_connections = 1000
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = os.path.join(LOGS_DIR, "gunicorn_access.log")
errorlog = os.path.join(LOGS_DIR, "gunicorn_error.log")
loglevel = "info"
capture_output = True
enable_stdio_inheritance = True

# Process naming
proc_name = "minimart_pos"

# Environment
raw_env = [
    f"DJANGO_SETTINGS_MODULE=minimart_pos.settings",
    f"PYTHONPATH={BASE_DIR}",
]