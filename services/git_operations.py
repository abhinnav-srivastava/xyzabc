"""
Git operations service for Restore app name.
Provides git pull/push with automatic credential detection from the system.
Uses Git's credential helper (Windows Credential Manager, Git Credential Manager, etc.)
when running git commands — no manual credential handling required.
"""

import json
import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any


def _block_git_remote() -> bool:
    """Check if git remote operations are blocked. Built app: always block. Dev: config/env."""
    import sys
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return True  # Built app: no uploads
    if os.environ.get("BLOCK_GIT_REMOTE", "").lower() in ("1", "true", "yes"):
        return True
    try:
        config_path = get_project_root() / "config" / "app_config.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            if cfg.get("data_egress", {}).get("block_git_remote"):
                return True
    except Exception:
        pass
    return False

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
    Checks local (if in repo), then global, then system.
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
    if ok and "true" in out.strip().lower():
        info["is_repo"] = True
        # Local credential helper (repo-specific)
        ok, out, _ = _run_git(path, ["config", "--local", "credential.helper"])
        if ok and out.strip():
            info["credential_helper"] = out.strip()
            info["credential_helper_scope"] = "local"
            ok, out, _ = _run_git(path, ["config", "--get", "remote.origin.url"])
            if ok and out.strip():
                info["remote_url"] = out.strip()
            return info

    # Global credential helper (works from any directory)
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

    # Remote URL (if in repo)
    if info["is_repo"]:
        ok, out, _ = _run_git(path, ["config", "--get", "remote.origin.url"])
        if ok and out.strip():
            info["remote_url"] = out.strip()

    return info


def get_git_head(repo_path: Path) -> Optional[str]:
    """
    Return current git HEAD hash for the given repo path, or None if not a git repo.
    """
    path = Path(repo_path)
    if not path.is_dir():
        return None
    ok, out, _ = _run_git(path, ["rev-parse", "HEAD"], timeout=5)
    if ok and out.strip():
        return out.strip()
    return None


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

    if _block_git_remote():
        result["message"] = "Git remote operations disabled (data_egress.block_git_remote)"
        return result

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

    if _block_git_remote():
        result["message"] = "Git remote operations disabled (data_egress.block_git_remote)"
        return result

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


def get_commits(
    repo_path: Path,
    limit: int = 30,
    branch: Optional[str] = None,
    timeout: int = 15,
) -> list:
    """
    Get recent commits from a local git repo.
    Returns list of {"hash": str, "subject": str} (short hash + first line of message).
    If branch is given, shows commits from that branch; otherwise from HEAD.
    """
    path = Path(repo_path)
    if not path.exists() or not path.is_dir():
        return []
    ok, _, _ = _run_git(path, ["rev-parse", "--is-inside-work-tree"], timeout=5)
    if not ok:
        return []
    args = ["log", f"-{limit}", "--format=%h|%s"]
    if branch and branch.strip():
        args.append(branch.strip())
    ok, out, _ = _run_git(
        path,
        args,
        timeout=timeout,
    )
    if not ok or not out.strip():
        return []
    commits = []
    for line in out.strip().split("\n"):
        if "|" in line:
            h, s = line.split("|", 1)
            commits.append({"hash": h.strip(), "subject": s.strip()})
    return commits


def get_commit_patch(
    repo_path: Path,
    commit_hash: str,
    timeout: int = 30,
) -> Optional[str]:
    """
    Get the patch/diff for a commit. Returns unified diff string or None.
    Uses --first-parent so merge commits show diff against first parent
    (default git show on merges often returns no diff).
    """
    path = Path(repo_path)
    h = (commit_hash or "").strip()
    if not path.exists() or not path.is_dir() or not h:
        return None
    ok, _, _ = _run_git(path, ["rev-parse", "--is-inside-work-tree"], timeout=5)
    if not ok:
        return None
    ok, out, _ = _run_git(
        path,
        ["show", h, "--first-parent", "--no-color", "-p"],
        timeout=timeout,
    )
    if ok and out and out.strip():
        return out
    return None


def get_diff_between_branches(
    repo_path: Path,
    target_branch: str,
    source_branch: str,
    timeout: int = 60,
) -> Optional[str]:
    """
    Get diff between branches (GitLab MR style).
    Uses target...source (merge base) so the diff shows what would be merged.
    Returns unified diff string or None.
    """
    path = Path(repo_path)
    target = (target_branch or "").strip()
    source = (source_branch or "").strip()
    if not path.exists() or not path.is_dir() or not target or not source:
        return None
    ok, _, _ = _run_git(path, ["rev-parse", "--is-inside-work-tree"], timeout=5)
    if not ok:
        return None
    # target...source = merge base diff (like GitLab MR)
    ok, out, _ = _run_git(
        path,
        ["diff", "--no-color", target + "..." + source],
        timeout=timeout,
    )
    return out if ok else None


def get_branches(
    repo_path: Path,
    include_remote: bool = True,
    timeout: int = 15,
) -> list:
    """
    Get branches from a local git repo.
    Returns list of branch names (strings). Local first, then remote if include_remote.
    """
    path = Path(repo_path)
    if not path.exists() or not path.is_dir():
        return []
    ok, _, _ = _run_git(path, ["rev-parse", "--is-inside-work-tree"], timeout=5)
    if not ok:
        return []
    branches = []
    args = ["branch", "-a"] if include_remote else ["branch"]
    ok, out, _ = _run_git(path, args, timeout=timeout)
    if not ok or not out.strip():
        return []
    for line in out.strip().split("\n"):
        line = line.strip().lstrip("*").strip()
        if not line or "HEAD" in line:
            continue
        if line.startswith("remotes/"):
            # remotes/origin/feature-x -> origin/feature-x (needed for git log)
            parts = line.split("/", 2)
            if len(parts) >= 3 and parts[2] != "HEAD":
                name = parts[1] + "/" + parts[2]
                if name not in branches:
                    branches.append(name)
        else:
            if line not in branches:
                branches.append(line)
    return branches


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

    if _block_git_remote():
        result["message"] = "Git remote operations disabled (data_egress.block_git_remote)"
        return result

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
