# CodeCritique Shell Scripts

This document describes the shell scripts available for Linux, macOS, and WSL users.

## Available Scripts

### Setup Scripts
- **`setup.sh`** - Complete setup script for Linux/macOS/WSL
- **`start.sh`** - Start the CodeCritique application
- **`install_deps.sh`** - Manual dependency installation

### Conversion Scripts
- **`convert_excel_to_md.sh`** - Convert all Excel files to Markdown
- **`convert_excel_advanced.sh`** - Interactive Excel conversion with menu
- **`convert_excel_simple.sh`** - Simple, compatible Excel conversion

## Prerequisites

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

### Linux (CentOS/RHEL/Fedora)
```bash
sudo yum install python3 python3-pip python3-venv
# or for newer versions:
sudo dnf install python3 python3-pip python3-venv
```

### macOS
```bash
# Using Homebrew
brew install python3

# Or download from python.org
```

### WSL (Windows Subsystem for Linux)
```bash
# Same as Linux
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

## Usage

### 1. Initial Setup
```bash
# Make scripts executable
chmod +x *.sh

# Run setup
./setup.sh
```

### 2. Start Application
```bash
./start.sh
```

### 3. Manual Dependency Installation
```bash
./install_deps.sh
```

### 4. Convert Excel Files
```bash
# Convert all files
./convert_excel_to_md.sh

# Interactive conversion
./convert_excel_advanced.sh

# Simple conversion
./convert_excel_simple.sh
```

## Script Details

### setup.sh
- Checks Python installation and version (requires 3.8+)
- Creates virtual environment
- Activates virtual environment
- Installs dependencies with proxy detection
- Converts Excel files to Markdown
- Provides setup completion instructions

### start.sh
- Activates virtual environment
- Starts the CodeCritique Flask application
- Shows server URL (http://localhost:5000)

### install_deps.sh
- Activates virtual environment
- Runs dependency installation with proxy detection
- Provides manual installation options if automatic installation fails

### convert_excel_to_md.sh
- Converts all Excel files to Markdown format
- Option to start application after conversion
- Error handling and user feedback

### convert_excel_advanced.sh
- Interactive menu system
- Options to convert all files or specific files
- List available Excel and Markdown files
- Better error handling

### convert_excel_simple.sh
- Simple, compatible version
- Works on most Unix-like systems
- Clean implementation with strict error handling

## Troubleshooting

### Python Not Found
```bash
# Check if Python is installed
python3 --version
# or
python --version

# Install Python if missing (Ubuntu/Debian)
sudo apt install python3 python3-pip python3-venv
```

### Permission Denied
```bash
# Make scripts executable
chmod +x *.sh
```

### Virtual Environment Issues
```bash
# Remove and recreate virtual environment
rm -rf .venv
./setup.sh
```

### Dependency Installation Issues
```bash
# Try manual installation
source .venv/bin/activate
pip install -r requirements.txt

# Or with proxy
pip install --proxy http://your-proxy:port -r requirements.txt

# Or with trusted hosts
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
```

## File Structure
```
CodeCritique/
├── setup.sh                    # Main setup script
├── start.sh                    # Start application
├── install_deps.sh             # Manual dependency installation
├── convert_excel_to_md.sh      # Convert all Excel files
├── convert_excel_advanced.sh   # Interactive Excel conversion
├── convert_excel_simple.sh     # Simple Excel conversion
├── .venv/                      # Virtual environment (created by setup)
├── checklists/
│   ├── excel/                  # Source Excel files
│   └── markdown/               # Generated Markdown files
└── app.py                      # Main Flask application
```

## Cross-Platform Compatibility

| Script | Windows | Linux | macOS | WSL |
|--------|---------|-------|-------|-----|
| setup.sh | ❌ | ✅ | ✅ | ✅ |
| start.sh | ❌ | ✅ | ✅ | ✅ |
| install_deps.sh | ❌ | ✅ | ✅ | ✅ |
| convert_excel_to_md.sh | ❌ | ✅ | ✅ | ✅ |
| convert_excel_advanced.sh | ❌ | ✅ | ✅ | ✅ |
| convert_excel_simple.sh | ❌ | ✅ | ✅ | ✅ |

For Windows users, use the corresponding `.bat` files instead.
