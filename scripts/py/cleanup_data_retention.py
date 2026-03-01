#!/usr/bin/env python3
"""
Data retention cleanup for corporate compliance.
Removes old patch_store files and optionally audit logs beyond retention period.
Run periodically (cron/scheduled task) or manually.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    from utils.path_utils import get_temp_dir, get_writable_data_dir
except ImportError:
    def get_temp_dir():
        return Path(__file__).resolve().parent.parent.parent / "temp"
    def get_writable_data_dir():
        return Path(__file__).resolve().parent.parent.parent


def load_retention_days() -> int:
    """Load patch_retention_days from config. Default 30."""
    config_path = Path(__file__).resolve().parent.parent.parent / "config" / "app_config.json"
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            data_cfg = cfg.get("data_retention", {})
            return int(data_cfg.get("patch_retention_days", 30))
        except (json.JSONDecodeError, ValueError):
            pass
    return 30


def cleanup_patch_store(retention_days: int) -> int:
    """Remove patch_store files older than retention_days. Returns count deleted."""
    patch_dir = get_temp_dir() / "patch_store"
    if not patch_dir.exists():
        return 0
    cutoff = datetime.now() - timedelta(days=retention_days)
    deleted = 0
    for f in patch_dir.glob("*.json"):
        try:
            if datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
                f.unlink()
                deleted += 1
        except OSError:
            pass
    return deleted


def main():
    retention = load_retention_days()
    deleted = cleanup_patch_store(retention)
    print(f"Cleaned {deleted} patch files older than {retention} days")


if __name__ == "__main__":
    main()
