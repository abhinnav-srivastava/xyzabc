#!/bin/bash
# Shell script to start CodeCritique on Linux/macOS/WSL

echo "========================================"
echo "Starting CodeCritique"
echo "========================================"
echo

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "ERROR: Virtual environment not found"
    echo "Please run ./setup.sh first"
    exit 1
fi

# Check if activation script exists
if [ ! -f ".venv/bin/activate" ]; then
    echo "ERROR: Virtual environment activation script not found"
    echo "Please run ./setup.sh first"
    exit 1
fi

echo "Activating virtual environment..."
source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment"
    echo "Please run ./setup.sh first"
    exit 1
fi

echo "Starting CodeCritique server..."
echo
echo "The application will be available at: http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo

# Check if Python is available in the virtual environment
if ! command_exists python; then
    echo "ERROR: Python not found in virtual environment"
    echo "Please run ./setup.sh first"
    exit 1
fi

python app.py
