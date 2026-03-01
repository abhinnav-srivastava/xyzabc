"""
User projects: remote git URLs or local paths.
Stored in data/projects.json, keyed by user_id.
Data upload/download via git only (clone, pull, push, fetch) — no APIs.
"""

import json
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    from utils.path_utils import get_writable_data_dir
except ImportError:
    def get_writable_data_dir() -> Path:
        return Path(__file__).resolve().parent.parent

_PROJECTS_FILE = "projects.json"


def _is_git_remote(url: str) -> bool:
    """Return True if url is a git remote URL (https, http, git@, ssh://)."""
    url = (url or "").strip()
    if url.startswith(("https://", "http://")):
        return True
    if url.startswith("git@") and ":" in url:
        return True
    if url.startswith("ssh://"):
        return True
    return False


def _projects_path() -> Path:
    data_dir = get_writable_data_dir() / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / _PROJECTS_FILE


def _load_raw() -> Dict[str, List[Dict[str, Any]]]:
    path = _projects_path()
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_raw(data: Dict[str, List[Dict[str, Any]]]) -> None:
    path = _projects_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_projects(user_id: str) -> List[Dict[str, Any]]:
    """Get all projects for a user."""
    user_id = user_id.strip()
    if not user_id:
        return []
    data = _load_raw()
    return data.get(user_id, [])


def get_project(user_id: str, project_id: str) -> Optional[Dict[str, Any]]:
    """Get a project by id for a user."""
    for p in get_projects(user_id):
        if p.get("id") == project_id:
            return p
    return None


def add_project(
    user_id: str,
    name: str,
    url_or_path: str,
    project_type: str = "remote",
) -> Optional[Dict[str, Any]]:
    """
    Add a project. Accepts remote git URLs (https, git@, ssh://) or local paths.
    Data upload/download via git only (clone, pull, push, fetch) — no APIs.
    Returns the added project or None if invalid.
    """
    user_id = user_id.strip()
    name = (name or "").strip()
    url_or_path = (url_or_path or "").strip()
    if not user_id or not url_or_path:
        return None
    if project_type not in ("remote", "local"):
        project_type = "remote" if _is_git_remote(url_or_path) else "local"
    if not name:
        if "/" in url_or_path or "\\" in url_or_path:
            name = url_or_path.replace("\\", "/").split("/")[-1].replace(".git", "")
        else:
            name = url_or_path
    data = _load_raw()
    projects = data.setdefault(user_id, [])
    project = {
        "id": str(uuid.uuid4()),
        "name": name,
        "type": project_type,
        "url_or_path": url_or_path,
    }
    projects.append(project)
    _save_raw(data)
    return project


def remove_project(user_id: str, project_id: str) -> bool:
    """Remove a project by id. Returns True if removed."""
    user_id = user_id.strip()
    if not user_id or not project_id:
        return False
    data = _load_raw()
    projects = data.get(user_id, [])
    original_len = len(projects)
    projects[:] = [p for p in projects if p.get("id") != project_id]
    if len(projects) < original_len:
        _save_raw(data)
        return True
    return False
