"""
User profiles keyed by userId (username) as unique identifier.
Stores profiles in data/profiles.json.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    from utils.path_utils import get_writable_data_dir
except ImportError:
    def get_writable_data_dir() -> Path:
        return Path(__file__).resolve().parent.parent

_PROFILES_FILE = "profiles.json"


def _profiles_path() -> Path:
    data_dir = get_writable_data_dir() / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / _PROFILES_FILE


def _load_raw() -> Dict[str, Any]:
    path = _profiles_path()
    if not path.exists():
        return {"profiles": {}, "last_used_user_id": None}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Migrate old format (keyed by name) to new (keyed by userId)
        profiles = data.get("profiles", {})
        migrated = {}
        for k, v in profiles.items():
            if isinstance(v, dict) and "user_id" not in v and "userId" not in v:
                # Old format: key was name
                user_id = v.get("username") or v.get("user_id") or k
                migrated[user_id] = {
                    "user_id": user_id,
                    "name": v.get("name", k),
                    "username": v.get("username", user_id),
                    "preferred_roles": v.get("preferred_roles") or ([v.get("preferred_role")] if v.get("preferred_role") else []),
                    "last_used": v.get("last_used", ""),
                }
            else:
                migrated[k] = v
        data["profiles"] = migrated
        if "last_used_name" in data and "last_used_user_id" not in data:
            data["last_used_user_id"] = data.get("last_used_name")
        return data
    except (json.JSONDecodeError, IOError):
        return {"profiles": {}, "last_used_user_id": None}


def _save_raw(data: Dict[str, Any]) -> None:
    path = _profiles_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Get a profile by userId (username). Returns None if not found."""
    user_id = user_id.strip()
    if not user_id:
        return None
    data = _load_raw()
    profiles = data.get("profiles", {})
    if user_id in profiles:
        return profiles[user_id]
    # Fallback: match by name (old profiles)
    for p in profiles.values():
        if p.get("name") == user_id:
            return p
    return None


def get_profile_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Get first profile matching name (for backward compat)."""
    for p in get_all_profiles():
        if p.get("name") == name:
            return p
    return None


def save_profile(user_id: str, name: str, preferred_roles: Optional[List[str]] = None) -> None:
    """Create or update a profile. userId is the unique identifier."""
    user_id = user_id.strip()
    name = name.strip()
    if not user_id or not name:
        return
    data = _load_raw()
    profiles = data.setdefault("profiles", {})
    existing = profiles.get(user_id, {})
    roles = preferred_roles if preferred_roles is not None else existing.get("preferred_roles", [])
    profiles[user_id] = {
        "user_id": user_id,
        "name": name,
        "username": user_id,
        "preferred_roles": roles or [],
        "last_used": datetime.now().isoformat(),
    }
    data["last_used_user_id"] = user_id
    _save_raw(data)


def get_last_used_user_id() -> Optional[str]:
    """Return the last used userId, or None."""
    data = _load_raw()
    return data.get("last_used_user_id") or data.get("last_used_name")


def get_last_used_name() -> Optional[str]:
    """Return the last used name (for backward compat)."""
    uid = get_last_used_user_id()
    if not uid:
        return None
    p = get_profile(uid)
    return p.get("name") if p else uid


def get_all_profiles() -> List[Dict[str, Any]]:
    """Return all profiles sorted by last_used (most recent first)."""
    data = _load_raw()
    profiles = list(data.get("profiles", {}).values())
    profiles.sort(
        key=lambda p: p.get("last_used", ""),
        reverse=True,
    )
    return profiles


def delete_profile(user_id: str) -> bool:
    """Delete a profile by userId. Returns True if deleted."""
    user_id = user_id.strip()
    if not user_id:
        return False
    data = _load_raw()
    profiles = data.get("profiles", {})
    if user_id not in profiles:
        # Try by name for backward compat
        for uid, p in list(profiles.items()):
            if p.get("name") == user_id:
                user_id = uid
                break
        else:
            return False
    del profiles[user_id]
    if data.get("last_used_user_id") == user_id:
        data["last_used_user_id"] = next(iter(profiles.keys()), None) if profiles else None
    _save_raw(data)
    return True


def set_last_used(user_id: str) -> bool:
    """Set a profile as last used. Returns True if found."""
    user_id = user_id.strip()
    if not user_id:
        return False
    data = _load_raw()
    profiles = data.get("profiles", {})
    if user_id not in profiles:
        for uid, p in profiles.items():
            if p.get("name") == user_id:
                user_id = uid
                break
        else:
            return False
    data["last_used_user_id"] = user_id
    _save_raw(data)
    return True


def update_profile_roles(user_id: str, preferred_roles: List[str]) -> bool:
    """Update roles for a profile. Returns True if updated."""
    user_id = user_id.strip()
    if not user_id:
        return False
    data = _load_raw()
    profiles = data.get("profiles", {})
    if user_id not in profiles:
        return False
    profiles[user_id]["preferred_roles"] = [r for r in preferred_roles if r]
    profiles[user_id]["last_used"] = datetime.now().isoformat()
    _save_raw(data)
    return True
