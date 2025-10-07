#!/bin/bash
# Shell script for CodeCritique setup on Linux/macOS/WSL

set -e  # Exit on any error

echo "========================================"
echo "CodeCritique Setup Script"
echo "========================================"
echo

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Python is available
if command_exists python3; then
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
elif command_exists python; then
    PYTHON_CMD="python"
    PIP_CMD="pip"
else
    echo "ERROR: Python is not installed or not in PATH"
    echo "Please install Python 3.8+ from https://www.python.org/downloads/"
    echo "On Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "On macOS: brew install python3"
    exit 1
fi

echo "Found Python: $($PYTHON_CMD --version)"
echo

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "ERROR: Python 3.8+ is required. Found Python $PYTHON_VERSION"
    echo "Please upgrade Python and try again"
    exit 1
fi

echo "Creating virtual environment..."
$PYTHON_CMD -m venv .venv
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create virtual environment"
    echo "Make sure python3-venv is installed:"
    echo "  Ubuntu/Debian: sudo apt install python3-venv"
    echo "  macOS: python3 -m ensurepip --upgrade"
    exit 1
fi

echo "Virtual environment created!"
echo

echo "Activating virtual environment..."
source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment"
    exit 1
fi

echo "Virtual environment activated!"
echo

echo "Installing dependencies..."
echo "Using advanced proxy detection..."

$PYTHON_CMD proxy_setup.py
if [ $? -ne 0 ]; then
    echo
    echo "WARNING: Failed to install dependencies automatically"
    echo "You can continue with setup and install dependencies manually later"
    echo
    read -p "Continue with setup? (y/n): " continue_setup
    case $continue_setup in
        [Yy]* )
            echo "Skipping dependency installation..."
            echo "You can install dependencies later by running:"
            echo "  source .venv/bin/activate"
            echo "  pip install -r requirements.txt"
            echo
            ;;
        * )
            echo "Setup cancelled by user"
            exit 1
            ;;
    esac
else
    echo "Dependencies installed successfully!"
fi
echo

echo "Converting Excel files to Markdown..."
$PYTHON_CMD convert_excel_to_markdown.py --all
if [ $? -ne 0 ]; then
    echo "WARNING: Failed to convert Excel files (this is optional)"
fi

echo
echo "========================================"
echo "Setup completed successfully!"
echo "========================================"
echo
echo "To start CodeCritique:"
echo "1. Run: ./start.sh"
echo "2. Or manually: source .venv/bin/activate && python app.py"
echo "3. Open browser to: http://localhost:5000"
echo

read -p "Press Enter to exit..."
