# CodeCritique

Professional code review tool with role-based, category-driven checklists for comprehensive quality assurance.

## Quick Start

### Windows (Recommended)

1. **Double-click `setup.bat`** - This will automatically:
   - Check Python installation
   - Create virtual environment
   - Install dependencies
   - Convert Excel files to Markdown

2. **Double-click `start.bat`** - This will start the application

3. **Open browser to http://localhost:5000**

### Alternative: PowerShell

1. **Right-click `setup.ps1` → "Run with PowerShell"**
2. **Right-click `start.ps1` → "Run with PowerShell"**

### Manual Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Convert Excel files
python convert_excel_to_markdown.py --all

# Start application
python app.py
```

## Features

- ✅ **Role-based Reviews**: Self, Peer, Tech Lead, FO, Architect
- ✅ **Category-driven Checklists**: Different categories per role
- ✅ **Real-time Timing**: Track review duration
- ✅ **Export Reports**: HTML and PDF downloads
- ✅ **Excel Integration**: Convert Excel checklists to Markdown
- ✅ **Responsive Design**: Works on desktop and mobile
- ✅ **Offline Capable**: No internet required after setup

## Usage

1. **Start Review**: Enter name, select role, click "Start Review"
2. **Complete Categories**: Review items, select status (OK/NG/NA), add comments
3. **View Summary**: See statistics, timing, download reports

## File Structure

```
critique/
├── setup.bat              # Windows setup script
├── start.bat              # Windows start script
├── setup.ps1              # PowerShell setup script
├── start.ps1              # PowerShell start script
├── app.py                 # Main application
├── requirements.txt       # Python dependencies
├── config/roles.json      # Configuration
├── checklists/            # Checklist files
│   ├── excel/            # Excel source files
│   └── markdown/         # Markdown files (used by app)
└── templates/            # HTML templates
```

## Troubleshooting

- **Python not found**: Install Python 3.8+ from https://python.org
- **Port 5000 in use**: The app will show an error, try closing other applications
- **Permission errors**: Run Command Prompt as Administrator
- **Setup fails**: Check that all files are present in the project folder

## Support

For detailed setup instructions, see `SETUP.md`

---

**CodeCritique** - Professional Code Review Tool