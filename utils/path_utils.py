"""
Path Utilities for CodeReview
Provides consistent path handling for both development and portable app environments
"""

import os
import sys
from pathlib import Path
from typing import Union, Optional

def get_base_dir() -> str:
    """
    Get the base directory of the application.
    Works correctly in both development and PyInstaller bundled environments.
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        \
        return sys._MEIPASS
    else:
        \
        return os.path.dirname(os.path.dirname(__file__))

def get_project_root() -> Path:
    """
    Get the project root directory as a Path object.
    """
    return Path(get_base_dir())

def get_config_path(config_file: str) -> Path:
    """
    Get the full path to a config file.

    Args:
        config_file: The config file name (e.g., 'roles.json', 'app_config.json')

    Returns:
        Path to the config file
    """
    return get_project_root() / "config" / config_file

def get_checklists_path(subpath: str = "") -> Path:
    """
    Get the path to the checklists directory.

    Args:
        subpath: Optional subpath within checklists directory

    Returns:
        Path to checklists directory or subpath
    """
    base_path = get_project_root() / "checklists"
    if subpath:
        return base_path / subpath
    return base_path

def get_scripts_path(script_file: str = "") -> Path:
    """
    Get the path to the scripts directory.

    Args:
        script_file: Optional script file name

    Returns:
        Path to scripts directory or specific script
    """
    base_path = get_project_root() / "scripts"
    if script_file:
        return base_path / script_file
    return base_path

def get_static_path(subpath: str = "") -> Path:
    """
    Get the path to the static directory.

    Args:
        subpath: Optional subpath within static directory

    Returns:
        Path to static directory or subpath
    """
    base_path = get_project_root() / "static"
    if subpath:
        return base_path / subpath
    return base_path

def get_templates_path(template_file: str = "") -> Path:
    """
    Get the path to the templates directory.

    Args:
        template_file: Optional template file name

    Returns:
        Path to templates directory or specific template
    """
    base_path = get_project_root() / "templates"
    if template_file:
        return base_path / template_file
    return base_path

def ensure_dir_exists(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path

    Returns:
        Path object to the directory
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj

def get_relative_path(target_path: Union[str, Path], from_path: Optional[Union[str, Path]] = None) -> Path:
    """
    Get a relative path from one location to another.

    Args:
        target_path: The target path
        from_path: The starting path (defaults to project root)

    Returns:
        Relative path
    """
    if from_path is None:
        from_path = get_project_root()

    return Path(target_path).relative_to(Path(from_path))

def is_portable_mode() -> bool:
    """
    Check if the application is running in portable mode (PyInstaller bundle).

    Returns:
        True if running in portable mode, False otherwise
    """
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

def get_writable_data_dir() -> Path:
    """
    Get a writable directory for app data (profiles, temp, patch_store).
    When frozen (PyInstaller): uses user app data dir so data persists.
    When dev: uses project root / data.
    """
    if is_portable_mode():
        if sys.platform == "win32":
            base = Path(os.environ.get("APPDATA", os.path.expanduser("~"))) / "CodeReview"
        elif sys.platform == "darwin":
            base = Path.home() / "Library" / "Application Support" / "CodeReview"
        else:
            base = Path.home() / ".local" / "share" / "CodeReview"
        base.mkdir(parents=True, exist_ok=True)
        return base
    return get_project_root()

def get_data_dir() -> Path:
    """
    Get the data directory for the application.
    In portable mode, uses writable user dir. In dev, uses project root.

    Returns:
        Path to the data directory
    """
    return get_writable_data_dir()

def get_logs_dir() -> Path:
    """
    Get the logs directory for the application.

    Returns:
        Path to the logs directory
    """
    logs_dir = get_project_root() / "logs"
    ensure_dir_exists(logs_dir)
    return logs_dir

def get_temp_dir() -> Path:
    """
    Get the temporary directory for the application.
    When frozen, uses writable_data_dir/temp so patch_store etc. persist.

    Returns:
        Path to the temporary directory
    """
    temp_dir = get_writable_data_dir() / "temp"
    ensure_dir_exists(temp_dir)
    return temp_dir

def get_roles_config_path() -> Path:
    """Get the path to roles.json config file."""
    return get_config_path("roles.json")

def get_app_config_path() -> Path:
    """Get the path to app_config.json config file."""
    return get_config_path("app_config.json")

def get_build_config_path() -> Path:
    """Get the path to build_config.json config file."""
    return get_config_path("build_config.json")

def get_network_security_config_path() -> Path:
    """Get the path to network_security.json config file."""
    return get_config_path("network_security.json")

def get_checklist_columns_config_path() -> Path:
    """Get the path to checklist_columns.json config file."""
    return get_config_path("checklist_columns.json")

def get_conversion_config_path() -> Path:
    """Get the path to conversion_config.json config file."""
    return get_config_path("conversion_config.json")


def get_tools_dir() -> Path:
    """Get the path to the tools directory (bundled git, cloc, etc.)."""
    return get_project_root() / "tools"


def get_git_executable() -> str:
    """
    Return path to git executable: prefer bundled tools/git, else 'git' (PATH).
    Bundled: tools/git/cmd/git.exe, or tools/git/PortableGit-*/cmd/git.exe after extracting .7z.
    """
    import sys
    tools = get_tools_dir()
    git_dir = tools / "git"
    if git_dir.exists():
        if sys.platform == "win32":
            for name in ("cmd/git.exe", "bin/git.exe", "git.exe"):
                p = git_dir / name
                if p.exists():
                    return str(p)
            for sub in git_dir.iterdir():
                if sub.is_dir():
                    for name in ("cmd/git.exe", "bin/git.exe"):
                        p = sub / name
                        if p.exists():
                            return str(p)
        else:
            for name in ("bin/git", "git"):
                p = git_dir / name
                if p.exists():
                    return str(p)
            for sub in git_dir.iterdir():
                if sub.is_dir():
                    p = sub / "bin" / "git"
                    if p.exists():
                        return str(p)
    return "git"


def get_cloc_executable() -> str:
    """
    Return path to cloc: prefer bundled tools/cloc, else 'cloc' (PATH).
    Bundled: cloc.exe, cloc-2.08.exe, or any cloc*.exe / cloc* in tools/cloc/.
    """
    import sys
    tools = get_tools_dir()
    cloc_dir = tools / "cloc"
    if cloc_dir.exists():
        if sys.platform == "win32":
            for name in ("cloc.exe", "cloc.pl"):
                p = cloc_dir / name
                if p.exists():
                    return str(p)
            for p in sorted(cloc_dir.glob("cloc*.exe")):
                return str(p)
        else:
            for name in ("cloc", "cloc.pl"):
                p = cloc_dir / name
                if p.exists():
                    return str(p)
            for p in sorted(cloc_dir.glob("cloc*")):
                if p.is_file() and os.access(p, os.X_OK):
                    return str(p)
    return "cloc"


def get_diffstat_executable() -> str:
    """
    Return path to diffstat: prefer bundled native binary only (no JAR).
    Bundled: diffstat.exe (Windows) or diffstat (Unix). JARs are ignored — they often
    open a GUI window and are not suitable for headless use when the app starts.
    """
    import sys
    tools = get_tools_dir()
    ds_dir = tools / "diffstat"
    if ds_dir.exists():
        if sys.platform == "win32":
            for p in sorted(ds_dir.glob("diffstat*.exe")):
                return str(p)
            p = ds_dir / "diffstat.exe"
            if p.exists():
                return str(p)
        else:
            for name in ("diffstat",):
                p = ds_dir / name
                if p.is_file() and os.access(p, os.X_OK):
                    return str(p)
        # Do not use *.jar — DiffStats.jar etc. are typically GUI apps and open a window
    return "diffstat"


def get_tool_executable(
    tool_id: str,
    exe_names: Optional[list] = None,
    glob_pattern: Optional[str] = None,
) -> str:
    """
    Generic lookup: tools/<tool_id>/ then PATH.
    exe_names: e.g. ["cloc.exe", "cloc"] for Windows then fallback.
    glob_pattern: e.g. "cloc*.exe" to find first match in tool dir.
    Returns executable path or bare command name for PATH.
    """
    import sys
    tools = get_tools_dir()
    tool_dir = tools / tool_id
    if not tool_dir.exists():
        return tool_id
    if exe_names:
        for name in exe_names:
            p = tool_dir / name
            if p.exists() and (p.is_file() or (p.is_dir() and (tool_dir / "bin" / name).exists())):
                if p.is_file():
                    return str(p)
                q = tool_dir / "bin" / name
                if q.exists():
                    return str(q)
    if glob_pattern:
        for p in sorted(tool_dir.glob(glob_pattern)):
            if p.is_file():
                if sys.platform != "win32" and not os.access(p, os.X_OK):
                    continue
                return str(p)
    return tool_id
