# Development Setup

Quick setup for a new development machine.

> **Restore app name:** Pass `-Name "YourApp"` to setup: `.\scripts\setup-dev.ps1 -Name "YourApp"` or `./scripts/setup-dev.sh --name "YourApp"`  
> **Electron build:** Add `-Build` (PowerShell) or `--build` (bash) to run `npm run build:win` after setup.

## Option 1: Docker (web only)

No Python/Node install needed. Requires [Docker](https://docs.docker.com/get-docker/).

```bash
docker compose up
```

Open http://localhost:5000

## Option 2: Local install

### Linux / macOS / WSL

```bash
./scripts/setup-dev.sh
# With proxy: ./scripts/setup-dev.sh --proxy http://proxy:8080
# With build: ./scripts/setup-dev.sh --build
```

### Windows (PowerShell)

```powershell
.\scripts\setup-dev.ps1
# With proxy: .\scripts\setup-dev.ps1 -Proxy "http://proxy:8080"
# With build: .\scripts\setup-dev.ps1 -Build
```

### Prerequisites

- **Python 3.8+** — [python.org](https://www.python.org/)
- **Node.js 18+** (optional, for Electron) — [nodejs.org](https://nodejs.org/)

### After setup

| Command | Description |
|---------|-------------|
| `python app.py --dev-server` | Web dev (Flask debug) |
| `python app.py` | Web prod (Waitress) |
| `npm start` | Electron desktop app |
| `npm run build:win` | Build portable Windows exe |

## Optional: metrics tools

For patch stats (git, cloc, diffstat), add executables under `tools/`. See `tools/*/README.md`.

```bash
python scripts/download_metrics_tools.py   # fetches CLOC for Windows
```
