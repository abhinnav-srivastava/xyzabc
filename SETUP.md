# CodeCritique Setup Guide

This guide will help you set up CodeCritique on a new PC.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Quick Setup

### 1. Install Python Dependencies

```bash
# Navigate to the CodeCritique directory
cd path/to/critique

# Create a virtual environment (recommended)
python -m venv .venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 2. Run the Application

```bash
# Start the Flask application
python app.py
```

The application will be available at: http://localhost:5000

## Detailed Setup Instructions

### Step 1: Verify Python Installation

Check if Python is installed:
```bash
python --version
# Should show Python 3.8 or higher
```

If Python is not installed, download it from: https://www.python.org/downloads/

### Step 2: Clone or Copy the Project

If you have the project files:
- Copy the entire `critique` folder to your desired location
- Navigate to the project directory

### Step 3: Set Up Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# You should see (.venv) in your command prompt
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- Flask (web framework)
- ReportLab (PDF generation)
- pandas (Excel processing)
- openpyxl (Excel file handling)
- PyInstaller (for creating executables)

### Step 5: Verify Installation

```bash
python app.py
```

You should see output like:
```
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://[your-ip]:5000
```

### Step 6: Access the Application

Open your web browser and go to: http://localhost:5000

## Project Structure

```
critique/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── config/
│   └── roles.json                 # Role and category configuration
├── checklists/
│   ├── excel/                     # Excel source files
│   │   ├── self/
│   │   ├── peer/
│   │   ├── techlead/
│   │   ├── fo/
│   │   └── architect/
│   └── markdown/                  # Markdown files (used by app)
│       ├── self/
│       ├── peer/
│       ├── techlead/
│       ├── fo/
│       └── architect/
├── services/
│   ├── checklist_loader.py        # Loads checklist data
│   └── excel_importer.py          # Excel processing
├── static/
│   └── css/
│       └── styles.css             # Custom styling
├── templates/                     # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── review_category_table.html
│   └── summary.html
└── convert_excel_to_markdown.py   # Excel to Markdown converter
```

## Usage

### 1. Start a Review
- Open http://localhost:5000
- Enter your name (pre-filled with system username)
- Select a review role
- Click "Start Review"

### 2. Complete Review Categories
- Review items are displayed in tabular format
- Select status for each item: OK, NG, NA, or leave unanswered
- Add comments if needed
- Navigate through categories

### 3. View Summary
- See overall statistics
- Review timing information
- Download HTML or PDF reports

## Converting Excel to Markdown

If you need to update checklists:

```bash
# Convert all Excel files to Markdown
python convert_excel_to_markdown.py --all

# Convert a specific file
python convert_excel_to_markdown.py --excel checklists/excel/self/correctness.xlsx
```

## Creating Executable (Optional)

To create a standalone executable:

```bash
# Install PyInstaller if not already installed
pip install PyInstaller

# Create executable
pyinstaller --onefile --add-data "config;config" --add-data "checklists;checklists" --add-data "templates;templates" --add-data "static;static" app.py

# The executable will be in the 'dist' folder
```

## Troubleshooting

### Common Issues

1. **Port 5000 already in use**
   ```bash
   # Use a different port
   set PORT=5001 && python app.py
   ```

2. **Dependency installation fails**
   - The setup script will ask if you want to continue without dependencies
   - You can install dependencies later using:
     - `install_deps.bat` (Windows batch)
     - `install_deps.ps1` (PowerShell)
     - Or manually: `.venv\Scripts\activate` then `pip install -r requirements.txt`

3. **Module not found errors**
   ```bash
   # Make sure virtual environment is activated
   # Reinstall dependencies
   pip install -r requirements.txt
   ```

4. **Permission errors on Windows**
   - Run Command Prompt as Administrator
   - Or use PowerShell with appropriate permissions

5. **Excel files not found**
   - Ensure checklists/excel/ folder exists
   - Run the conversion script to generate markdown files

6. **Proxy/Network issues**
   - The setup script includes advanced proxy detection
   - You can manually enter proxy settings if automatic detection fails
   - Try different proxy configurations or contact IT support

### Getting Help

- Check that all files are present in the project structure
- Verify Python version (3.8+)
- Ensure virtual environment is activated
- Check that all dependencies are installed

## Features

- **Role-based Reviews**: Self, Peer, Tech Lead, FO, Architect
- **Category-driven**: Different categories per role
- **Real-time Timing**: Track review duration
- **Export Reports**: HTML and PDF downloads
- **Excel Integration**: Convert Excel checklists to Markdown
- **Responsive Design**: Works on desktop and mobile
- **Offline Capable**: No internet required after setup

## Configuration

Edit `config/roles.json` to modify:
- Available roles
- Categories per role
- File paths for checklists

The application will automatically load the configuration on startup.
