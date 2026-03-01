#!/usr/bin/env python3
"""
Audit Python dependencies for known vulnerabilities.
Run: python scripts/audit-deps.py
Requires: pip install pip-audit
"""

import subprocess
import sys
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "audit", "-r", str(root / "requirements.txt")],
            cwd=root,
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)
    except FileNotFoundError:
        print("pip-audit not found. Install with: pip install pip-audit", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
