"""
User access tokens for Git authentication (e.g. GitLab PAT, GitHub PAT).
Stored in data/access_tokens.json, keyed by user_id.
Tokens are used for git operations only — no API calls. Data upload/download via git only.
"""

import json
import re
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    from utils.path_utils import get_writable_data_dir
except ImportError:
    def get_writable_data_dir() -> Path:
        return Path(__file__).resolve().parent.parent

_TOKENS_FILE = "access_tokens.json"


def _tokens_path() -> Path:
    data_dir = get_writable_data_dir() / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / _TOKENS_FILE


def _load_raw() -> Dict[str, List[Dict[str, Any]]]:
    path = _tokens_path()
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_raw(data: Dict[str, List[Dict[str, Any]]]) -> None:
    path = _tokens_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _mask_token(token: str) -> str:
    """Return masked token for display (e.g. glpat-****xyz1)."""
    if not token or len(token) < 8:
        return "****"
    return token[:4] + "****" + token[-4:]


def get_tokens(user_id: str) -> List[Dict[str, Any]]:
    """Get all tokens for a user. Tokens are masked for display."""
    user_id = user_id.strip()
    if not user_id:
        return []
    data = _load_raw()
    tokens = data.get(user_id, [])
    return [
        {
            **t,
            "token_masked": _mask_token(t.get("token", "")),
        }
        for t in tokens
    ]


def get_token_for_host(user_id: str, host: str) -> Optional[str]:
    """
    Get the raw token for a host (e.g. gitlab.com). Used by git operations.
    Returns None if no token found.
    """
    user_id = user_id.strip()
    host = (host or "").strip().lower()
    if not user_id or not host:
        return None
    data = _load_raw()
    for t in data.get(user_id, []):
        if (t.get("host") or "").strip().lower() == host:
            return t.get("token")
    return None


def add_token(
    user_id: str,
    name: str,
    host: str,
    token: str,
) -> Optional[Dict[str, Any]]:
    """
    Add an access token. host should be the git host (e.g. gitlab.com, github.com).
    Returns the added token (with masked token) or None if invalid.
    """
    user_id = user_id.strip()
    name = (name or "").strip()
    host = (host or "").strip().lower()
    token = (token or "").strip()
    if not user_id or not host or not token:
        return None
    # Basic host validation (domain-like)
    if not re.match(r"^[\w.-]+(\.[\w.-]+)+$", host):
        return None
    data = _load_raw()
    tokens = data.setdefault(user_id, [])
    entry = {
        "id": str(uuid.uuid4()),
        "name": name or host,
        "host": host,
        "token": token,
    }
    tokens.append(entry)
    _save_raw(data)
    return {
        **entry,
        "token_masked": _mask_token(token),
    }


def remove_token(user_id: str, token_id: str) -> bool:
    """Remove a token by id. Returns True if removed."""
    user_id = user_id.strip()
    if not user_id or not token_id:
        return False
    data = _load_raw()
    tokens = data.get(user_id, [])
    original_len = len(tokens)
    tokens[:] = [t for t in tokens if t.get("id") != token_id]
    if len(tokens) < original_len:
        _save_raw(data)
        return True
    return False
