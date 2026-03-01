#!/usr/bin/env bash
# CodeCritique - Development environment setup (Linux / macOS / WSL)
# Run from project root: ./scripts/setup-dev.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=== CodeCritique Dev Setup ==="
echo "Project root: $PROJECT_ROOT"
echo ""

# Python
echo "--- Python ---"
if command -v python3 &>/dev/null; then
  PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
  PYTHON_CMD="python"
else
  echo "ERROR: Python 3.8+ required. Install from https://www.python.org/"
  exit 1
fi

$PYTHON_CMD --version
if ! $PYTHON_CMD -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
  echo "ERROR: Python 3.8+ required"
  exit 1
fi

echo "Installing Python dependencies..."
$PYTHON_CMD -m pip install --upgrade pip -q
$PYTHON_CMD -m pip install -r requirements.txt -q
echo "  OK"
echo ""

# Node (for Electron)
echo "--- Node.js ---"
if command -v node &>/dev/null; then
  NODE_VER=$(node -v | sed 's/v//' | cut -d. -f1)
  if [ "$NODE_VER" -ge 18 ] 2>/dev/null; then
    echo "Node $(node -v) found"
    echo "Installing npm dependencies..."
    npm install --silent
    echo "  OK"
  else
    echo "Node 18+ recommended for Electron. Current: $(node -v)"
    echo "Skipping npm install. Run 'npm install' when ready."
  fi
else
  echo "Node.js not found. Optional for web-only dev."
  echo "Install from https://nodejs.org/ for Electron (npm start, npm run build:win)"
fi
echo ""

# Data dir
mkdir -p data
echo "Data dir: $PROJECT_ROOT/data"
echo ""

echo "=== Setup complete ==="
echo ""
echo "Run options:"
echo "  Web only:     $PYTHON_CMD app.py --dev-server"
echo "  Web (prod):   $PYTHON_CMD app.py"
echo "  Electron:     npm start"
echo "  Docker:       docker compose up"
echo ""
