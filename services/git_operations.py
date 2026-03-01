"""
Git operations service for CodeReview.
Provides git pull/push with automatic credential detection from the system.
Uses Git's credential helper (Windows Credential Manager, Git Credential Manager, etc.)
when running git commands — no manual credential handling required.
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

try:
    from utils.path_utils import get_git_executable, get_project_root
except ImportError:
    import sys

    def get_project_root() -> Path:
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS)
        return Path(__file__).resolve().parent.parent

    def get_git_executable() -> str:
        return "git"

logger = logging.getLogger(__name__)


def _git_env() -> Dict[str, str]:
    """
    Build environment for git subprocess so credential helpers work.
    Inherits user's HOME/USERPROFILE so Git finds ~/.gitconfig and credential stores.
    """
    env = os.environ.copy()
    # Ensure HOME is set on Windows (Git uses it for config lookup)
    if "HOME" not in env and "USERPROFILE" in env:
        env["HOME"] = env["USERPROFILE"]
    return env


def _run_git(
    repo_path: Path,
    args: list,
    timeout: int = 120,
) -> Tuple[bool, str, str]:
    """
    Run a git command in the given repo. Returns (success, stdout, stderr).
    Uses system credential helper automatically when git needs auth.
    """
    git_cmd = get_git_executable()
    full_args = [git_cmd] + args
    try:
        result = subprocess.run(
            full_args,
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=_git_env(),
        )
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        return result.returncode == 0, stdout, stderr
    except subprocess.TimeoutExpired as e:
        return False, "", str(e)
    except FileNotFoundError:
        return False, "", f"Git executable not found: {git_cmd}"
    except Exception as e:
        return False, "", str(e)


def get_credential_helper_info(repo_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Detect which credential helper Git is configured to use.
    Returns info useful for debugging; credentials are never exposed.
    """
    path = repo_path or get_project_root()
    info: Dict[str, Any] = {
        "credential_helper": None,
        "credential_helper_scope": None,
        "is_repo": False,
        "remote_url": None,
    }

    # Check if it's a git repo
    ok, out, _ = _run_git(path, ["rev-parse", "--is-inside-work-tree"])
    if not ok or "true" not in out.strip().lower():
        return info
    info["is_repo"] = True

    # Local credential helper
    ok, out, _ = _run_git(path, ["config", "--local", "credential.helper"])
    if ok and out.strip():
        info["credential_helper"] = out.strip()
        info["credential_helper_scope"] = "local"
        return info

    # Global credential helper
    ok, out, _ = _run_git(path, ["config", "--global", "credential.helper"])
    if ok and out.strip():
        info["credential_helper"] = out.strip()
        info["credential_helper_scope"] = "global"
        return info

    # System credential helper
    ok, out, _ = _run_git(path, ["config", "--system", "credential.helper"])
    if ok and out.strip():
        info["credential_helper"] = out.strip()
        info["credential_helper_scope"] = "system"

    # Remote URL (for context)
    ok, out, _ = _run_git(path, ["config", "--get", "remote.origin.url"])
    if ok and out.strip():
        info["remote_url"] = out.strip()

    return info


def git_pull(
    repo_path: Optional[Path] = None,
    remote: str = "origin",
    branch: Optional[str] = None,
    timeout: int = 120,
) -> Dict[str, Any]:
    """
    Pull from remote. Uses system credential helper for authentication.
    """
    path = Path(repo_path) if repo_path else get_project_root()
    result: Dict[str, Any] = {"success": False, "stdout": "", "stderr": "", "message": ""}

    # Verify repo
    ok, _, err = _run_git(path, ["rev-parse", "--is-inside-work-tree"])
    if not ok:
        result["message"] = f"Not a git repository: {path}"
        result["stderr"] = err
        return result

    args = ["pull", remote]
    if branch:
        args.append(branch)

    success, stdout, stderr = _run_git(path, args, timeout=timeout)
    result["success"] = success
    result["stdout"] = stdout
    result["stderr"] = stderr
    result["message"] = "Pull completed successfully" if success else (stderr or "Pull failed")

    if success:
        logger.info("Git pull succeeded: %s", path)
    else:
        logger.warning("Git pull failed: %s - %s", path, stderr)

    return result


def git_push(
    repo_path: Optional[Path] = None,
    remote: str = "origin",
    branch: Optional[str] = None,
    timeout: int = 120,
) -> Dict[str, Any]:
    """
    Push to remote. Uses system credential helper for authentication.
    """
    path = Path(repo_path) if repo_path else get_project_root()
    result: Dict[str, Any] = {"success": False, "stdout": "", "stderr": "", "message": ""}

    # Verify repo
    ok, _, err = _run_git(path, ["rev-parse", "--is-inside-work-tree"])
    if not ok:
        result["message"] = f"Not a git repository: {path}"
        result["stderr"] = err
        return result

    args = ["push", remote]
    if branch:
        args.append(branch)

    success, stdout, stderr = _run_git(path, args, timeout=timeout)
    result["success"] = success
    result["stdout"] = stdout
    result["stderr"] = stderr
    result["message"] = "Push completed successfully" if success else (stderr or "Push failed")

    if success:
        logger.info("Git push succeeded: %s", path)
    else:
        logger.warning("Git push failed: %s - %s", path, stderr)

    return result


def git_fetch(
    repo_path: Optional[Path] = None,
    remote: str = "origin",
    timeout: int = 120,
) -> Dict[str, Any]:
    """
    Fetch from remote. Uses system credential helper for authentication.
    """
    path = Path(repo_path) if repo_path else get_project_root()
    result: Dict[str, Any] = {"success": False, "stdout": "", "stderr": "", "message": ""}

    ok, _, err = _run_git(path, ["rev-parse", "--is-inside-work-tree"])
    if not ok:
        result["message"] = f"Not a git repository: {path}"
        result["stderr"] = err
        return result

    success, stdout, stderr = _run_git(path, ["fetch", remote], timeout=timeout)
    result["success"] = success
    result["stdout"] = stdout
    result["stderr"] = stderr
    result["message"] = "Fetch completed successfully" if success else (stderr or "Fetch failed")
    return result
