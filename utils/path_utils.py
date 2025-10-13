"""
Path Utilities for CodeCritique
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

def get_data_dir() -> Path:
    """
    Get the data directory for the application.
    In portable mode, this is the same as the base directory.
    In development mode, this is the project root.

    Returns:
        Path to the data directory
    """
    return get_project_root()

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

    Returns:
        Path to the temporary directory
    """
    temp_dir = get_project_root() / "temp"
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
