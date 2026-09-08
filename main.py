import os
import sys
from waitress import serve
from django.core.management import execute_from_command_line
from django.core.wsgi import get_wsgi_application

def run_server():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'minimart_pos.settings')
    
    # For static files
    from django.conf import settings
    from django.contrib.staticfiles.handlers import StaticFilesHandler
    application = StaticFilesHandler(get_wsgi_application())
    
    print("Starting POS system on http://localhost:8000")
    serve(application, host='0.0.0.0', port=8000)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'migrate':
        execute_from_command_line(sys.argv)
    else:
        run_server()