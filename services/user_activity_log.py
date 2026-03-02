"""
Raw text-based user activity log for analytics and parsing.
Logs app opens, logins, logouts, reviews completed with NG/NA/OK counts.

Format: tab-separated (TSV). One line per event.
  Column 1: timestamp (ISO UTC)
  Column 2: event (app_open|login|logout|review_started|review_completed)
  Column 3+: key=value pairs (user_id, user_name, ok, ng, na, skipped, unanswered, etc.)

Example lines:
  2026-03-03T10:00:00Z	app_open	user_id=	user_name=
  2026-03-03T10:01:00Z	login	user_id=john	user_name=John	roles=fo,architect
  2026-03-03T10:02:00Z	review_completed	user_id=john	ok=20	ng=5	na=10	skipped=0	unanswered=0	total_items=35	duration_seconds=300

Parse with: awk -F'\\t' '{print $1,$2,$3}' data/user_activity.log
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from utils.path_utils import get_writable_data_dir
except ImportError:
    def get_writable_data_dir() -> Path:
        return Path(__file__).resolve().parent.parent

_LOG_NAME = "user_activity.log"


def _log_path() -> Path:
    data_dir = get_writable_data_dir() / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / _LOG_NAME


def _escape(val: Any) -> str:
    """Escape tabs and newlines for single-line log entries."""
    s = str(val) if val is not None else ""
    return s.replace("\t", " ").replace("\n", " ").replace("\r", " ")


def _write_line(parts: list) -> None:
    """Write a single tab-separated line to the log."""
    try:
        line = "\t".join(_escape(p) for p in parts) + "\n"
        with open(_log_path(), "a", encoding="utf-8") as f:
            f.write(line)
    except OSError as e:
        logging.getLogger(__name__).warning("User activity log write failed: %s", e)


def log_app_open(user_id: str = "", user_name: str = "") -> None:
    """Log when user opens the app (index or dashboard)."""
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_line([ts, "app_open", f"user_id={user_id or ''}", f"user_name={user_name or ''}"])


def log_login(user_id: str = "", user_name: str = "", roles: Optional[list] = None) -> None:
    """Log when user logs in."""
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    parts = [ts, "login", f"user_id={user_id or ''}", f"user_name={user_name or ''}"]
    if roles:
        parts.append(f"roles={','.join(roles)}")
    _write_line(parts)


def log_logout(user_id: str = "", user_name: str = "") -> None:
    """Log when user logs out."""
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_line([ts, "logout", f"user_id={user_id or ''}", f"user_name={user_name or ''}"])


def log_review_completed(
    user_id: str = "",
    user_name: str = "",
    ok: int = 0,
    ng: int = 0,
    na: int = 0,
    skipped: int = 0,
    unanswered: int = 0,
    total_items: int = 0,
    duration_seconds: int = 0,
    roles: Optional[list] = None,
) -> None:
    """Log when user completes a review (reaches summary)."""
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    parts = [
        ts,
        "review_completed",
        f"user_id={user_id or ''}",
        f"user_name={user_name or ''}",
        f"ok={ok}",
        f"ng={ng}",
        f"na={na}",
        f"skipped={skipped}",
        f"unanswered={unanswered}",
        f"total_items={total_items}",
        f"duration_seconds={duration_seconds}",
    ]
    if roles:
        parts.append(f"roles={','.join(roles)}")
    _write_line(parts)


def log_review_started(user_id: str = "", user_name: str = "", roles: Optional[list] = None) -> None:
    """Log when user starts a new review."""
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    parts = [ts, "review_started", f"user_id={user_id or ''}", f"user_name={user_name or ''}"]
    if roles:
        parts.append(f"roles={','.join(roles)}")
    _write_line(parts)
