#!/bin/bash
# Shell script to convert Excel files to Markdown format
# This script uses the existing convert_excel_to_markdown.py script

echo "========================================"
echo "CodeCritique - Excel to Markdown Converter"
echo "========================================"
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "ERROR: Python is not installed or not in PATH"
        echo "Please install Python and try again"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

echo "Found Python: $($PYTHON_CMD --version)"

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

if [ $? -ne 0 ]; then
    echo
    echo "ERROR: Conversion failed"
    echo "Please check the error messages above"
    exit 1
fi

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
if [ "$start_app" = "y" ] || [ "$start_app" = "Y" ]; then
    echo
    echo "Starting CodeCritique application..."
    echo "The application will be available at: http://localhost:5000"
    echo "Press Ctrl+C to stop the application"
    echo
    $PYTHON_CMD app.py
else
    echo
    echo "You can start the application later by running: $PYTHON_CMD app.py"
fi

read -p "Press Enter to exit"
