#!/usr/bin/env bash
# Restore app name after download. Run from project root.
# Usage: ./scripts/restore-name.sh "YourApp"
# Or use setup-dev: ./scripts/setup-dev.sh --name "YourApp"

NAME="${1:?Usage: $0 YourApp}"
ID=$(echo "$NAME" | tr '[:upper:]' '[:lower:]' | tr -d ' ')
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Restoring app name to: $NAME (id: $ID)"
echo "Project root: $PROJECT_ROOT"
echo ""

find "$PROJECT_ROOT" -type f \( -name "*.py" -o -name "*.js" -o -name "*.json" -o -name "*.html" -o -name "*.md" -o -name "*.yml" -o -name "*.sh" \) \
  ! -path "*/node_modules/*" ! -path "*/.git/*" ! -path "*/dist/*" ! -path "*/build/*" 2>/dev/null | while read -r f; do
  if grep -q -E 'Restore app name|Restore app name' "$f" 2>/dev/null; then
    perl -i -pe "s/Restore app name/$NAME/g; s/Restore app name/$ID/g" "$f" 2>/dev/null && echo "  ${f#$PROJECT_ROOT/}"
  fi
done

echo ""
echo "Done."
