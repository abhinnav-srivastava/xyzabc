#!/bin/bash
# Advanced shell script to convert Excel files to Markdown format
# This script provides options for converting all files or individual files

echo "========================================"
echo "CodeCritique - Advanced Excel Converter"
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

show_menu() {
    echo
    echo "Please select an option:"
    echo "1. Convert ALL Excel files to Markdown"
    echo "2. Convert a specific Excel file"
    echo "3. List available Excel files"
    echo "4. Exit"
    echo
}

convert_all() {
    echo
    echo "Converting all Excel files to Markdown format..."
    echo
    $PYTHON_CMD convert_excel_to_markdown.py --all
    if [ $? -ne 0 ]; then
        echo
        echo "ERROR: Conversion failed"
        read -p "Press Enter to continue..."
        return 1
    fi
    echo
    echo "All files converted successfully!"
    read -p "Press Enter to continue..."
    return 0
}

convert_specific() {
    echo
    echo "Available Excel files:"
    echo
    if [ -d "checklists/excel" ]; then
        find checklists/excel -name "*.xlsx" -type f 2>/dev/null
        if [ $? -ne 0 ]; then
            echo "No Excel files found in checklists/excel/ directory"
            read -p "Press Enter to continue..."
            return 1
        fi
    else
        echo "No Excel files found in checklists/excel/ directory"
        read -p "Press Enter to continue..."
        return 1
    fi
    echo
    read -p "Enter the full path to the Excel file: " excel_file
    if [ ! -f "$excel_file" ]; then
        echo "ERROR: File not found: $excel_file"
        read -p "Press Enter to continue..."
        return 1
    fi
    echo
    echo "Converting $excel_file..."
    $PYTHON_CMD convert_excel_to_markdown.py --excel "$excel_file"
    if [ $? -ne 0 ]; then
        echo
        echo "ERROR: Conversion failed"
        read -p "Press Enter to continue..."
        return 1
    fi
    echo
    echo "File converted successfully!"
    read -p "Press Enter to continue..."
    return 0
}

list_files() {
    echo
    echo "Excel files in checklists/excel/ directory:"
    echo
    if [ -d "checklists/excel" ]; then
        find checklists/excel -name "*.xlsx" -type f 2>/dev/null
        if [ $? -ne 0 ]; then
            echo "No Excel files found"
        fi
    else
        echo "No Excel files found"
    fi
    echo
    echo "Markdown files in checklists/markdown/ directory:"
    echo
    if [ -d "checklists/markdown" ]; then
        find checklists/markdown -name "*.md" -type f 2>/dev/null
        if [ $? -ne 0 ]; then
            echo "No Markdown files found"
        fi
    else
        echo "No Markdown files found"
    fi
    echo
    read -p "Press Enter to continue..."
}

# Main menu loop
while true; do
    show_menu
    read -p "Enter your choice (1-4): " choice
    
    case $choice in
        1)
            convert_all
            ;;
        2)
            convert_specific
            ;;
        3)
            list_files
            ;;
        4)
            echo
            echo "Goodbye!"
            exit 0
            ;;
        *)
            echo "Invalid choice. Please try again."
            ;;
    esac
done
