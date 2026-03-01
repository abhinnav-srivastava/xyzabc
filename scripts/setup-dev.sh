#!/usr/bin/env bash
# CodeReview - Development environment setup (Linux / macOS / WSL)
# Run from project root: ./scripts/setup-dev.sh
# Optional: ./scripts/setup-dev.sh --proxy http://proxy:8080 --name "YourApp" --build --venv
# With auth (no encoding needed): ./scripts/setup-dev.sh --proxy http://proxy:8080 --proxy-user user --proxy-pass 'sr!n@v9914'
# Env: PIP_PROXY, PIP_PROXY_USER, PIP_PROXY_PASS, APP_NAME

set -e

PIP_PROXY="${PIP_PROXY:-}"
PIP_PROXY_USER="${PIP_PROXY_USER:-}"
PIP_PROXY_PASS="${PIP_PROXY_PASS:-}"
APP_NAME="${APP_NAME:-}"
BUILD=false
VENV=false
while [[ $# -gt 0 ]]; do
  case $1 in
    --proxy)      PIP_PROXY="$2"; shift 2 ;;
    --proxy-user) PIP_PROXY_USER="$2"; shift 2 ;;
    --proxy-pass) PIP_PROXY_PASS="$2"; shift 2 ;;
    --name)       APP_NAME="$2"; shift 2 ;;
    --build)      BUILD=true; shift ;;
    --venv)       VENV=true; shift ;;
    *) shift ;;
  esac
done

# Build proxy URL with auth (auto URL-encodes special chars in user/pass)
if [[ -n "$PIP_PROXY" && -n "$PIP_PROXY_USER" && -n "$PIP_PROXY_PASS" ]]; then
  ENC_USER=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1], safe=''))" "$PIP_PROXY_USER")
  ENC_PASS=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1], safe=''))" "$PIP_PROXY_PASS")
  if [[ "$PIP_PROXY" =~ ^(https?)://(.+)$ ]]; then
    PIP_PROXY="${BASH_REMATCH[1]}://${ENC_USER}:${ENC_PASS}@${BASH_REMATCH[2]}"
  fi
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=== CodeReview Dev Setup ==="
echo "Project root: $PROJECT_ROOT"
if [[ -n "$PIP_PROXY" ]]; then
  DISPLAY_PROXY=$(echo "$PIP_PROXY" | sed -E 's|^([^:]+://)[^:]+:[^@]+@|\1***:***@|')
  echo "Pip proxy: $DISPLAY_PROXY"
fi
[[ -n "$APP_NAME" ]] && echo "Restore app name to: $APP_NAME"
$BUILD && echo "Run Electron build (build:win) after setup"
$VENV && echo "Create venv (.venv) for dependencies"
echo ""

# Restore app name (if --name passed)
if [[ -n "$APP_NAME" ]]; then
  echo "--- Restore app name ---"
  ID=$(echo "$APP_NAME" | tr '[:upper:]' '[:lower:]' | tr -d ' ')
  count=0
  while IFS= read -r f; do
    if grep -q -E 'CodeReview|codereview' "$f" 2>/dev/null; then
      perl -i -pe "s/CodeReview/$APP_NAME/g; s/codereview/$ID/g" "$f" 2>/dev/null && ((count++))
    fi
  done < <(find "$PROJECT_ROOT" -type f \( -name "*.py" -o -name "*.js" -o -name "*.json" -o -name "*.html" -o -name "*.md" -o -name "*.yml" -o -name "*.sh" -o -name "*.ps1" -o -name "*.bat" -o -name "*.spec" \) ! -path "*/node_modules/*" ! -path "*/.git/*" ! -path "*/dist/*" ! -path "*/build/*" 2>/dev/null)
  echo "  Updated $count files"
  echo ""
fi

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

# Create venv if --venv passed
if $VENV; then
  VENV_PATH="$PROJECT_ROOT/.venv"
  if [[ ! -d "$VENV_PATH" ]]; then
    echo "Creating venv at .venv..."
    $PYTHON_CMD -m venv "$VENV_PATH"
    echo "  Created"
  else
    echo "Venv .venv exists"
  fi
  PYTHON_CMD="$VENV_PATH/bin/python"
fi

echo "Installing Python dependencies..."
PIP_EXTRA="-q"
[[ "$VENV" != "true" ]] && [[ -z "${VIRTUAL_ENV:-}" ]] && PIP_EXTRA="--user -q"
[[ -n "$PIP_PROXY" ]] && PIP_EXTRA="$PIP_EXTRA --proxy $PIP_PROXY"
$PYTHON_CMD -m pip install --upgrade pip $PIP_EXTRA
$PYTHON_CMD -m pip install -r requirements.txt $PIP_EXTRA
echo "  OK"
[[ "$VENV" == "true" ]] && echo "Activate venv: source .venv/bin/activate"
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

# Electron build (if --build passed)
if $BUILD; then
  echo "--- Electron build (build:win) ---"
  if command -v node &>/dev/null; then
    npm run build:win
    echo "  OK"
  else
    echo "Node.js required for build. Skipping."
  fi
  echo ""
fi

echo "=== Setup complete ==="
echo ""
echo "Run options:"
echo "  Web only:     $PYTHON_CMD app.py --dev-server"
echo "  Web (prod):   $PYTHON_CMD app.py"
echo "  Electron:     npm start"
echo "  Docker:       docker compose up"
echo ""
