# Quick Start (after download)

1. **Restore app name** (optional; pass -Name to setup):
   ```powershell
   .\scripts\setup-dev.ps1 -Name "YourApp"
   ```

2. **Setup:**
   ```powershell
   .\scripts\setup-dev.ps1
   ```

3. **Run:**
   ```powershell
   python app.py --dev-server
   ```
   Or: `npm start` (Electron)

See [docs/DEV_SETUP.md](docs/DEV_SETUP.md) for full instructions.
