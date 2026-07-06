# production_server.py
from waitress import serve
from minimart_pos.wsgi import application
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/waitress.log'),
        logging.StreamHandler()
    ]
)

if __name__ == '__main__':
    print("Starting Waitress server on http://127.0.0.1:8000")
    print("Access from network: http://10.0.27.157")
    serve(
        application,
        host='0.0.0.0',
        port=8000,
        threads=4,
        channel_timeout=120
    )