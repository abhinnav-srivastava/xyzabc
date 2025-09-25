# Automated Checklist Workflow

This document describes the automated workflow for managing checklists in CodeCritique.

## Overview

The system now automatically converts Excel files to markdown and updates the configuration, eliminating the need for manual updates when adding new checklists.

## Workflow

### 1. Add New Checklists
1. **Create Excel file** in the appropriate folder under `checklists/excel/`
   - For role-based checklists: `checklists/excel/{role}/{category}.xlsx`
   - For guidelines: `checklists/excel/guidelines/{guideline_name}.xlsx`

2. **Excel file structure** (choose one):
   
   **For Role-based Checklists:**
   ```
   Sr.No. | Main Category | Sub Category | Description | Technical Description | How to Measure
   ```
   
   **For Guidelines:**
   ```
   Rule ID | Main Category | Sub Category | Guidelines Description | Good Example | Bad Example | Measurement Reference | Severity (MUST/GOOD/MAY) | External Refs
   ```

### 2. Automatic Processing

The system will automatically:

1. **Convert Excel to Markdown**: 
   - Reads Excel files and converts them to structured markdown
   - Handles different column structures automatically
   - Creates proper markdown formatting with categories and subcategories

2. **Update Configuration**:
   - Scans the folder structure
   - Updates `config/roles.json` with new roles and categories
   - Maps folder names to role names and category names

3. **Auto-refresh on Startup**:
   - Runs automatically when the Flask app starts
   - Can be disabled by setting `AUTO_UPDATE_CHECKLISTS=false`

### 3. Manual Refresh Options

If you need to refresh checklists manually:

#### Option 1: Web Interface
- Click the "Refresh" button in the navigation bar
- The page will reload automatically after refresh

#### Option 2: Command Line Scripts
```bash
# Windows
refresh_checklists.bat

# Linux/Mac
./refresh_checklists.sh

# PowerShell
.\refresh_checklists.ps1
```

#### Option 3: Direct Python Script
```bash
python scripts/auto_update_checklists.py
```

#### Option 4: API Endpoint
```bash
curl http://localhost:5000/refresh
```

## File Structure

```
checklists/
├── excel/                          # Source Excel files
│   ├── self/                       # Self review checklists
│   │   ├── correctness.xlsx
│   │   ├── readability.xlsx
│   │   └── tests.xlsx
│   ├── peer/                       # Peer review checklists
│   │   ├── functionality.xlsx
│   │   └── style.xlsx
│   ├── techlead/                   # Tech lead checklists
│   │   ├── architecture.xlsx
│   │   └── design.xlsx
│   ├── fo/                         # FO review checklists
│   │   └── ops.xlsx
│   ├── architect/                  # Architect checklists
│   │   └── architecture.xlsx
│   └── guidelines/                 # Coding guidelines
│       └── android_coding_guidelines.xlsx
├── markdown/                       # Generated markdown files
│   ├── self/
│   ├── peer/
│   ├── techlead/
│   ├── fo/
│   ├── architect/
│   └── guidelines/
└── config/
    └── roles.json                  # Auto-generated configuration
```

## Configuration Mapping

The system automatically maps:

### Role Names
- `self` → "Self Review"
- `peer` → "Peer Review"
- `techlead` → "Tech Lead Review"
- `fo` → "FO Review"
- `architect` → "Architect Review"

### Category Names
- `correctness` → "Correctness"
- `readability` → "Readability"
- `tests` → "Test Review"
- `functionality` → "Functionality"
- `style` → "Style & Naming"
- `design` → "Design Review"
- `architecture` → "Architecture Review"
- `ops` → "Operational Readiness"

## Benefits

1. **Zero Manual Configuration**: Just add Excel files and refresh
2. **Consistent Formatting**: Automatic markdown generation with proper structure
3. **Version Control Friendly**: Markdown files are easier to track changes
4. **Multiple Refresh Options**: Web interface, scripts, or API
5. **Auto-startup**: Automatically updates on app restart
6. **Error Handling**: Graceful handling of missing files or invalid formats

## Troubleshooting

### Common Issues

1. **Excel file not converting**:
   - Check column names match expected structure
   - Ensure file is not corrupted or password-protected

2. **Role not appearing**:
   - Verify Excel file is in correct folder structure
   - Check folder name matches role mapping

3. **Auto-update not working**:
   - Check if `AUTO_UPDATE_CHECKLISTS` environment variable is set to `false`
   - Verify script permissions and dependencies

4. **Refresh button not working**:
   - Check browser console for JavaScript errors
   - Verify Flask app is running and accessible

### Environment Variables

- `AUTO_UPDATE_CHECKLISTS`: Set to `false` to disable auto-update on startup (default: `true`)
- `FLASK_SECRET_KEY`: Flask secret key for sessions

## Examples

### Adding a New Role Checklist

1. Create `checklists/excel/qa/quality.xlsx` with structure:
   ```
   Sr.No. | Main Category | Sub Category | Description | Technical Description | How to Measure
   1      | Functionality | Testing      | Test all edge cases | Use boundary value analysis | Verify with test cases
   ```

2. Run refresh (automatic or manual)

3. New "QA Review" role appears with "Quality" category

### Adding New Guidelines

1. Create `checklists/excel/guidelines/ios_coding_guidelines.xlsx`

2. Run refresh

3. Guidelines appear in `/guidelines` page

The system is now fully automated - just add Excel files and refresh!
