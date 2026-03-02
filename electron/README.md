# CodeReview Electron App

Desktop wrapper for CodeReview. **Fully bundled** — no Python or Flask required on the target machine.

## Prerequisites (build time only)

- **Node.js** (v18+)
- **Python** (3.8+) with Flask, waitress, etc. — for running PyInstaller
- **npm**

## Development

```bash
# From project root
npm install
npm start
```

Uses Python from PATH to run the Flask app. Opens the app in Electron.

## Build Windows Desktop App (fully bundled)

```bash
npm run build:win
```

Or:

```bash
node scripts/build-electron-win.js
```

This will:
1. Run **PyInstaller** to bundle the Flask app + Python + deps into `CodeReview.exe`
2. Run **electron-builder** to package it as a Windows app

Output: `dist-electron/` — installer (NSIS) and portable exe. **No Python required** on the target machine.

### If Electron build fails (network, proxy, etc.)

- **Retries:** The script retries electron-builder up to 3 times.
- **PyInstaller-only:** `npm run build:win:pyonly` — builds `dist/CodeReview.exe` only (skip Electron).
- **Proxy:** Set `HTTPS_PROXY` and `HTTP_PROXY` if behind a firewall.
