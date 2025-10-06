#!/bin/bash
# Shell script for manual dependency installation on Linux/macOS/WSL

echo "========================================"
echo "CodeCritique - Manual Dependency Installation"
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

echo "Virtual environment activated!"
echo

echo "Installing dependencies with advanced proxy detection..."
python proxy_setup.py
if [ $? -ne 0 ]; then
    echo
    echo "Manual installation options:"
    echo "1. Try without proxy: pip install -r requirements.txt"
    echo "2. Try with specific proxy: pip install --proxy http://your-proxy:port -r requirements.txt"
    echo "3. Try with trusted hosts: pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt"
    echo
    read -p "Press Enter to exit..."
    exit 1
fi

echo
echo "Dependencies installed successfully!"
echo "You can now run CodeCritique using ./start.sh"
echo

read -p "Press Enter to exit..."
