#!/bin/bash
# Production deployment script for CodeReview
# This script provides options for running CodeReview in production

echo "CodeReview Production Deployment Options"
echo "========================================="
echo ""
echo "Choose your deployment method:"
echo "1. Flask Development Server (Production Mode)"
echo "2. Waitress WSGI Server (Cross-platform)"
echo "3. Gunicorn WSGI Server (Linux/Mac)"
echo ""

read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        echo "Starting Flask in production mode..."
        python app.py --production --no-browser --host 0.0.0.0 --port 5000
        ;;
    2)
        echo "Installing Waitress if not available..."
        pip install waitress
        echo "Starting Waitress WSGI server..."
        waitress-serve --host=0.0.0.0 --port=5000 wsgi:application
        ;;
    3)
        echo "Installing Gunicorn if not available..."
        pip install gunicorn
        echo "Starting Gunicorn WSGI server..."
        gunicorn --bind 0.0.0.0:5000 --workers 4 wsgi:application
        ;;
    *)
        echo "Invalid choice. Please run the script again."
        ;;
esac
