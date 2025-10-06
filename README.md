# CodeCritique

Professional code review tool with role-based, category-driven checklists for comprehensive quality assurance.

## 🚀 Features

- ✅ **Role-based Reviews**: Self, Peer, Tech Lead, FO, Architect
- ✅ **Category-driven Checklists**: Different categories per role
- ✅ **Real-time Timing**: Track review duration
- ✅ **Export Reports**: HTML and PDF downloads
- ✅ **Excel Integration**: Convert Excel checklists to Markdown
- ✅ **Responsive Design**: Works on desktop and mobile
- ✅ **PWA Support**: Progressive Web App with offline capabilities
- ✅ **Offline Capable**: No internet required after setup
- ✅ **Apache 2.0 Licensed**: Open source and trusted dependencies

## 📋 Quick Start

### Windows (Recommended)

1. **Double-click `scripts/batch/setup.bat`** - This will automatically:
   - Check Python installation
   - Create virtual environment
   - Install dependencies
   - Convert Excel files to Markdown

2. **Double-click `scripts/batch/start.bat`** - This will start the application

3. **Open browser to http://localhost:5000**

### Alternative: PowerShell

1. **Right-click `scripts/powershell/setup.ps1` → "Run with PowerShell"**
2. **Right-click `scripts/powershell/start.ps1` → "Run with PowerShell"**

### Manual Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Convert Excel files
python scripts/py/convert_excel_to_markdown.py --all

# Start application
python app.py
```

## 🏗️ Project Structure

```
critique/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── LICENSE                         # Apache 2.0 License
├── DEPENDENCIES.md               # Dependency verification
├── .gitignore                     # Git ignore rules
├── config/                         # Configuration files
│   ├── app_config.json            # Application settings
│   ├── checklist_columns.json     # Checklist column definitions
│   ├── conversion_config.json     # Conversion settings
│   └── roles.json                 # Role configuration
├── checklists/                     # Checklist data
│   ├── excel/                     # Excel source files
│   └── markdown/                  # Markdown files (used by app)
├── scripts/                        # All scripts organized
│   ├── batch/                     # Windows batch scripts
│   ├── powershell/               # PowerShell scripts
│   ├── shell/                    # Unix shell scripts
│   ├── convert_excel_advanced.py # Advanced conversion script
│   ├── convert_excel_to_markdown.py # Basic conversion script
│   └── run.py                     # Main script runner
├── services/                       # Business logic services
│   ├── checklist_loader.py        # Loads checklist data
│   ├── excel_importer.py          # Excel processing
│   └── gitlab_client.py           # GitLab integration
├── static/                         # Static assets
│   ├── css/                       # Stylesheets
│   ├── js/                        # JavaScript files
│   ├── icons/                     # PWA icons
│   ├── screenshots/              # PWA screenshots
│   ├── manifest.json             # PWA manifest
│   └── sw.js                      # Service worker
├── templates/                      # HTML templates
│   ├── base.html                  # Base template with PWA support
│   ├── index.html                 # Home page
│   ├── start_review.html          # Review start page
│   ├── review_*.html             # Review pages
│   └── summary.html               # Summary page
└── logs/                          # Application logs
```

## 🔧 Configuration

### Application Configuration

Edit `config/app_config.json` to customize:
- Roles and categories
- UI settings
- Review settings
- Security settings
- Feature flags

### Checklist Configuration

Edit `config/checklist_columns.json` to customize:
- Column definitions for each role
- Validation rules
- Export settings

### Conversion Configuration

Edit `config/conversion_config.json` to customize:
- Column mapping
- Validation settings
- Output formatting

## 📱 PWA Features

CodeCritique is a Progressive Web App with:
- **Offline Support**: Works without internet connection
- **Installable**: Can be installed on desktop and mobile
- **Responsive**: Adapts to any screen size
- **Fast Loading**: Cached resources for quick access
- **Background Sync**: Syncs data when connection is restored

## 🛠️ Development

### Scripts

All scripts are organized in the `scripts/` directory:

```bash
# Run setup
python scripts/py/run.py setup

# Start application
python scripts/py/run.py start

# Convert Excel files
python scripts/py/run.py convert

# Refresh checklists
python scripts/py/run.py refresh
```

### Advanced Conversion

Use the advanced conversion script for more control:

```bash
# Convert all files with validation
python scripts/py/convert_excel_advanced.py --verbose

# Convert specific file
python scripts/py/convert_excel_advanced.py --file path/to/file.xlsx

# Dry run (no changes)
python scripts/py/convert_excel_advanced.py --dry-run

# Disable validation
python scripts/py/convert_excel_advanced.py --no-validation
```

## 🔒 Security

- **Apache 2.0 License**: Open source and permissive
- **Trusted Dependencies**: All dependencies verified as open source
- **No External Connections**: Works completely offline
- **Secure Session Management**: CSRF protection and secure cookies
- **Rate Limiting**: Protection against abuse

## 📊 Dependencies

All dependencies are open source and trusted:

- **Flask 3.0.3**: BSD-3-Clause (Web framework)
- **ReportLab 4.2.2**: BSD-3-Clause (PDF generation)
- **Pandas 2.1.4**: BSD-3-Clause (Data manipulation)
- **OpenPyXL 3.1.2**: MIT (Excel processing)
- **PyInstaller 6.3.0**: GPL-2.0-or-later (Packaging)

See `DEPENDENCIES.md` for detailed verification.

## 🚀 Usage

### 1. Start Review
- Open http://localhost:5000
- Enter your name (pre-filled with system username)
- Select a review role
- Click "Start Review"

### 2. Complete Categories
- Review items are displayed in tabular format
- Select status for each item: OK, NG, NA, or leave unanswered
- Add comments if needed
- Navigate through categories

### 3. View Summary
- See overall statistics
- Review timing information
- Download HTML or PDF reports

## 🔄 Converting Excel to Markdown

If you need to update checklists:

```bash
# Convert all Excel files to Markdown
python scripts/py/convert_excel_to_markdown.py --all

# Convert a specific file
python scripts/py/convert_excel_to_markdown.py --excel checklists/excel/self/correctness.xlsx
```

## 📝 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the [Issues](https://github.com/codecritique/codecritique/issues) page
- Review the documentation
- Contact the maintainers

## 🎯 Roadmap

- [ ] GitLab integration
- [ ] GitHub integration
- [ ] JIRA integration
- [ ] Slack notifications
- [ ] Advanced analytics
- [ ] Team collaboration features
- [ ] Custom checklist templates
- [ ] API endpoints
- [ ] Docker support
- [ ] Kubernetes deployment

---

**CodeCritique** - Making code reviews more efficient and comprehensive.