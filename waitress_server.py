# waitress_server.py
import os
import sys
from pathlib import Path
from waitress import serve
from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent

# Add the project directory to Python path
sys.path.insert(0, str(BASE_DIR))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'minimart_pos.settings')

# Get WSGI application
application = get_wsgi_application()

# Wrap with StaticFilesHandler for static files
application = StaticFilesHandler(application)

# Custom middleware to handle AJAX print requests
class PrintMiddleware:
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        # Handle print-specific paths
        path = environ.get('PATH_INFO', '')
        
        if '/print-direct/' in path:
            # Don't buffer print responses
            environ['wsgi.input_terminated'] = True
        
        return self.app(environ, start_response)

# Wrap application with middleware
application = PrintMiddleware(application)

if __name__ == '__main__':
    print("=" * 60)
    print("Minimart POS Server Starting...")
    print(f"Django Version: {sys.modules['django'].__version__}")
    print(f"Server: http://localhost:8020")
    print(f"POS Interface: http://localhost:8020/pos/")
    print("=" * 60)
    
    # Configure for production
    serve(
        application,
        host='0.0.0.0',
        port=8020,
        threads=8,
        channel_timeout=120,  # Increased timeout
        asyncore_loop_timeout=1,
        connection_limit=100,
        cleanup_interval=30,
        ident=None,
        expose_tracebacks=False,  # Disable tracebacks in production
    )