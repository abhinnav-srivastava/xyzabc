"""
Audit logging for corporate compliance.
Logs auth events (login, logout, role selection) and review actions in structured JSON format.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from utils.path_utils import get_writable_data_dir
except ImportError:
    def get_writable_data_dir() -> Path:
        return Path(__file__).resolve().parent.parent

_AUDIT_LOG_NAME = "audit.jsonl"
def _safe_value(v: Any) -> bool:
    """Allow simple JSON-serializable values in details."""
    return isinstance(v, (str, int, float, bool, type(None)))


def _audit_log_path() -> Path:
    data_dir = get_writable_data_dir() / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / _AUDIT_LOG_NAME


def audit_log(
    event: str,
    user_id: Optional[str] = None,
    user_name: Optional[str] = None,
    roles: Optional[list] = None,
    ip: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Write a structured audit log entry.
    Events: login, logout, select_roles, review_start, review_submit, patch_upload, profile_delete
    """
    entry = {
        "event": event,
        "user_id": user_id,
        "user_name": user_name,
        "roles": roles,
        "ip": ip,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    if details:
        safe_details = {str(k): v for k, v in details.items() if isinstance(k, str) and _safe_value(v)}
        if safe_details:
            entry["details"] = safe_details
    try:
        path = _audit_log_path()
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as e:
        logging.getLogger(__name__).warning("Audit log write failed: %s", e)
