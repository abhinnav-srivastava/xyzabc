#!/bin/bash
# Simple shell script to convert Excel files to Markdown format
# Compatible with most Unix-like systems (Linux, macOS, WSL)

set -e  # Exit on any error

echo "========================================"
echo "CodeCritique - Excel to Markdown Converter"
echo "========================================"
echo

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Python is available
if command_exists python3; then
    PYTHON_CMD="python3"
elif command_exists python; then
    PYTHON_CMD="python"
else
    echo "ERROR: Python is not installed or not in PATH"
    echo "Please install Python and try again"
    exit 1
fi

echo "Using Python: $($PYTHON_CMD --version)"

# Check if the conversion script exists
if [ ! -f "convert_excel_to_markdown.py" ]; then
    echo "ERROR: convert_excel_to_markdown.py not found"
    echo "Please make sure you're running this script from the CodeCritique directory"
    exit 1
fi

echo "Converting all Excel files to Markdown format..."
echo

# Run the conversion script
$PYTHON_CMD convert_excel_to_markdown.py --all

echo
echo "========================================"
echo "Conversion completed successfully!"
echo "========================================"
echo
echo "Excel files have been converted to Markdown format in:"
echo "- checklists/markdown/ folder"
echo
echo "You can now use the CodeCritique application with the updated checklists."
echo

# Ask if user wants to start the application
read -p "Do you want to start the CodeCritique application now? (y/n): " start_app
case $start_app in
    [Yy]* )
        echo
        echo "Starting CodeCritique application..."
        echo "The application will be available at: http://localhost:5000"
        echo "Press Ctrl+C to stop the application"
        echo
        $PYTHON_CMD app.py
        ;;
    * )
        echo
        echo "You can start the application later by running: $PYTHON_CMD app.py"
        ;;
esac

echo
echo "Press Enter to exit..."
read
