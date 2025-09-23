# CodeCritique

A configurable, role-based code review checklist tool built with Flask.

## Features
- Roles: Self, Peer, Tech Lead, FO, Architect (configurable via JSON)
- Categories per role with Markdown or Excel (xlsx) checklists (Markdown enabled by default)
- Step-by-step review flow storing responses in session
- Summary page with counts
- Export report as HTML (download) and PDF
- Offline-capable when packaged; no internet needed to run the binary

## Quickstart (dev)
```bash
# Windows PowerShell
cd C:\workspace\sources\critique
py -3 -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```
Open http://localhost:5000

## Configure roles/categories
See `config/roles.json`. Each category points to a checklist file under `checklists/` (Markdown by default).

## Build an offline executable (Windows)
```powershell
cd C:\workspace\sources\critique
./build.ps1
```
This produces `dist/CodeCritique.exe` that runs without internet.

## Notes
- To include Excel checklists, add `pandas` and `openpyxl` to `requirements.txt` during build, then repackage. The shipped EXE remains offline-capable.
