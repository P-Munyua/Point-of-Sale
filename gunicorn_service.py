# gunicorn_service.py
import os
import sys
import subprocess
import time

# Set working directory
os.chdir(r"C:\Users\admin\EXPLORER\POINT-OF-SALE")

# Gunicorn command
gunicorn_cmd = [
    "gunicorn",
    "--config", "gunicorn_config.py",
    "minimart_pos.wsgi:application"
]

# Run Gunicorn
subprocess.run(gunicorn_cmd)