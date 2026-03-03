#!/usr/bin/env python3
"""
Production WSGI configuration for Restore app name
Use this with production WSGI servers like Gunicorn, uWSGI, or Waitress
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment variables for production
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('FLASK_DEBUG', 'False')

# Import the Flask app
from app import create_app

# Create the application instance
application = create_app()

if __name__ == "__main__":
    # This allows running the WSGI file directly for testing
    application.run(host='0.0.0.0', port=5000, debug=False)
