#!/usr/bin/env python3
"""
Download optional metrics tools (CLOC, etc.) into tools/<name>/.
Run from project root: python scripts/download_metrics_tools.py

CLOC: downloads cloc-2.08.exe (Windows) or cloc tarball (Linux/macOS) from GitHub.
diffstat / Git: prints install links (no auto-download for all platforms).

Set NO_EXTERNAL_DOWNLOADS=1 or data_egress.block_external_downloads in config to skip downloads.
"""

import json
import os
import sys
import urllib.request
from pathlib import Path

# Project root (parent of scripts/)
ROOT = Path(__file__).resolve().parent.parent


def _block_external_downloads() -> bool:
    """Check if external downloads are blocked. Built app: always block. Dev: config/env."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return True  # Built app: no downloads
    if os.environ.get("NO_EXTERNAL_DOWNLOADS", "").lower() in ("1", "true", "yes"):
        return True
    config_path = ROOT / "config" / "app_config.json"
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            if cfg.get("data_egress", {}).get("block_external_downloads"):
                return True
        except (json.JSONDecodeError, KeyError):
            pass
    return False
TOOLS = ROOT / "tools"
CLOC_DIR = TOOLS / "cloc"
CLOC_WIN_URL = "https://github.com/AlDanial/cloc/releases/download/v2.08/cloc-2.08.exe"
CLOC_LINUX_URL = "https://github.com/AlDanial/cloc/releases/download/v2.08/cloc-2.08.tar.gz"


def download_file(url: str, dest: Path) -> bool:
    try:
        urllib.request.urlretrieve(url, dest)
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False


def main():
    os.chdir(ROOT)
    CLOC_DIR.mkdir(parents=True, exist_ok=True)

    if _block_external_downloads():
        print("External downloads disabled (NO_EXTERNAL_DOWNLOADS or data_egress.block_external_downloads).")
        print("Install tools manually. See docs/CODE_METRICS_AND_TOOLS.md")
        return

    if sys.platform == "win32":
        exe = CLOC_DIR / "cloc-2.08.exe"
        if exe.exists():
            print("CLOC already present at", exe)
        else:
            print("Downloading CLOC for Windows...")
            if download_file(CLOC_WIN_URL, exe):
                print("Saved to", exe)
            else:
                print("Manual: get", CLOC_WIN_URL, "and put in", CLOC_DIR)
    else:
        # Linux/macOS: prefer system package manager
        cloc_bin = CLOC_DIR / "cloc"
        if cloc_bin.exists() or (CLOC_DIR / "cloc.pl").exists():
            print("CLOC already present in", CLOC_DIR)
        else:
            print("Linux/macOS: install CLOC via package manager:")
            print("  apt install cloc   (Debian/Ubuntu)  |  brew install cloc   (macOS)")
            print("  Or download", CLOC_LINUX_URL, "and extract into", CLOC_DIR)

    print()
    print("Other tools (install manually if needed):")
    print("  diffstat: https://gnuwin32.sourceforge.net/packages/diffstat.htm (Win) | apt install diffstat | brew install diffstat")
    print("  Git:      https://git-scm.com/download/win (Win) | apt/brew install git")
    print("  Pygount:  pip install pygount")
    print("  Radon:    pip install radon")
    print()
    print("See docs/CODE_METRICS_AND_TOOLS.md for full list and project-level (Detekt, Android Lint) plans.")


if __name__ == "__main__":
    main()
