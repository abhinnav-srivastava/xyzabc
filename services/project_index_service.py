"""
Project index service for CodeReview.

When a project is added, we scan its directory and build a persistent index:
- File tree (paths, types: source, test, manifest, gradle, resources, other)
- Classes and methods (Java/Kotlin via tree-sitter when available, else regex)
- Test cases (test method names)

Index is stored in data/project_indexes/<project_id>.json and invalidated when
git HEAD changes (for git repos) or on manual refresh.
"""

import json
import logging
import os
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from utils.path_utils import get_writable_data_dir
except ImportError:
    def get_writable_data_dir() -> Path:
        return Path(__file__).resolve().parent.parent

try:
    from services.patch_parser import classify_file_type as _classify_android
except ImportError:
    def _classify_android(path: str) -> str:
        return "other"


def _classify_file(path: str) -> str:
    """Classify file: use Android categories, plus Python source/test detection."""
    ft = _classify_android(path)
    if ft == "other" and path.lower().endswith(".py"):
        path_n = path.replace("\\", "/").lower()
        if "/test" in path_n or "\\test" in path_n or path_n.startswith("test_") or path_n.endswith("_test.py"):
            return "test"
        return "source"
    return ft

logger = logging.getLogger(__name__)

_INDEX_VERSION = 1
_INDEX_DIR = "project_indexes"

# Directories to skip when walking (common build/cache dirs)
_SKIP_DIRS: Set[str] = {
    ".git", ".svn", ".hg", "node_modules", "__pycache__", ".pycache",
    "build", "dist", "out", ".gradle", ".idea", ".vscode", "venv", ".venv",
    "target", "bin", "obj", ".tox", ".mypy_cache", ".pytest_cache",
    "coverage", ".coverage", "htmlcov", ".eggs", "*.egg-info",
}


def _normalize_path(p: str) -> str:
    return p.replace("\\", "/").lstrip("./")


def _get_index_path(project_id: str) -> Path:
    data_dir = get_writable_data_dir() / "data" / _INDEX_DIR
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / f"{project_id}.json"


def _get_git_head(project_path: str) -> Optional[str]:
    """Return current git HEAD hash for repo, or None if not a git repo."""
    try:
        from services.git_operations import get_git_head
        return get_git_head(Path(project_path))
    except Exception:
        pass
    return None


def _should_skip_dir(dirname: str) -> bool:
    dn = dirname.lower()
    if dn in _SKIP_DIRS:
        return True
    if dn.startswith(".") and dn != "..":
        return True
    return False


def _walk_project_files(project_path: str) -> List[Dict[str, Any]]:
    """Walk project directory and return list of file entries with path and type."""
    files: List[Dict[str, Any]] = []
    root = Path(project_path)
    if not root.is_dir():
        return files
    try:
        for entry in root.rglob("*"):
            if not entry.is_file():
                continue
            rel = entry.relative_to(root)
            parts = rel.parts
            if any(_should_skip_dir(p) for p in parts):
                continue
            rel_str = _normalize_path(str(rel))
            file_type = _classify_file(rel_str)
            files.append({
                "path": rel_str,
                "type": file_type,
                "ext": entry.suffix.lower(),
            })
    except (OSError, PermissionError) as e:
        logger.warning("Error walking project %s: %s", project_path, e)
    return files


# Regex patterns for Java/Kotlin (fallback when tree-sitter not available)
_METHOD_PATTERNS = [
    re.compile(r"\b(?:override\s+|suspend\s+)?fun\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", re.MULTILINE),
    re.compile(r"\b(?:public|private|protected)\s+(?:static\s+)?(?:final\s+)?(?:[\w<>,\s\[\]]+)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", re.MULTILINE),
    re.compile(r"\bvoid\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", re.MULTILINE),
]
_CLASS_PATTERNS = [
    re.compile(r"\b(?:public\s+)?(?:abstract\s+)?class\s+([a-zA-Z_][a-zA-Z0-9_]*)", re.MULTILINE),
    re.compile(r"\b(?:public\s+)?(?:abstract\s+)?(?:data\s+)?class\s+([a-zA-Z_][a-zA-Z0-9_]*)", re.MULTILINE),
    re.compile(r"\bobject\s+([a-zA-Z_][a-zA-Z0-9_]*)", re.MULTILINE),
    re.compile(r"\binterface\s+([a-zA-Z_][a-zA-Z0-9_]*)", re.MULTILINE),
]
_TEST_METHOD_PATTERNS = [
    re.compile(r"\b(?:fun|void)\s+(test[A-Za-z0-9_]*)\s*\(", re.IGNORECASE),
    re.compile(r"\b(test[A-Za-z0-9_]*)\s*\([^)]*\)\s*\{", re.IGNORECASE),
    re.compile(r"\b(when_[a-zA-Z0-9_]+)\s*\(", re.IGNORECASE),
    re.compile(r"\b(given_[a-zA-Z0-9_]+)\s*\(", re.IGNORECASE),
]
# Python
_PY_CLASS_PATTERN = re.compile(r"^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)", re.MULTILINE)
_PY_TEST_PATTERN = re.compile(r"^\s*def\s+(test_[a-zA-Z0-9_]+)\s*\(", re.MULTILINE)


def _extract_classes_methods_regex(content: str, path: str) -> Tuple[List[str], List[Tuple[str, int]]]:
    """Extract class names and (method_name, line) from Java/Kotlin via regex."""
    ext = os.path.splitext(path)[1].lower()
    if ext not in (".java", ".kt"):
        return [], []
    classes: List[str] = []
    methods: List[Tuple[str, int]] = []
    seen_methods: Set[str] = set()
    for pat in _CLASS_PATTERNS:
        for m in pat.finditer(content):
            c = m.group(1).strip()
            if c and c not in classes:
                classes.append(c)
    for pat in _METHOD_PATTERNS:
        for m in pat.finditer(content):
            name = m.group(1).strip()
            if name and name not in seen_methods:
                if name.lower().startswith("test") or "test" in name.lower():
                    continue
                line_no = content[: m.start()].count("\n") + 1
                seen_methods.add(name)
                methods.append((name, line_no))
    return classes, sorted(methods, key=lambda x: x[1])


def _extract_test_cases_regex(content: str, path: str) -> List[Tuple[str, int]]:
    """Extract test method names from Java/Kotlin/Python test files."""
    ext = os.path.splitext(path)[1].lower()
    result: List[Tuple[str, int]] = []
    seen: Set[str] = set()
    if ext in (".java", ".kt"):
        for pat in _TEST_METHOD_PATTERNS:
            for m in pat.finditer(content):
                for g in m.groups():
                    if g and g not in seen:
                        seen.add(g)
                        line_no = content[: m.start()].count("\n") + 1
                        result.append((g, line_no))
    elif ext == ".py":
        for m in _PY_TEST_PATTERN.finditer(content):
            name = m.group(1)
            if name and name not in seen:
                seen.add(name)
                line_no = content[: m.start()].count("\n") + 1
                result.append((name, line_no))
    return result


def _extract_py_classes(content: str) -> List[str]:
    """Extract class names from Python file."""
    classes: List[str] = []
    for m in _PY_CLASS_PATTERN.finditer(content):
        c = m.group(1)
        if c and c not in classes:
            classes.append(c)
    return classes


def _extract_ast_java_kt(content: str, path: str, lang: str) -> Tuple[List[str], List[Tuple[str, int]]]:
    """Extract classes and methods using tree-sitter (when available)."""
    try:
        import tree_sitter
        if lang == "java":
            import tree_sitter_java
            parser = tree_sitter.Language(tree_sitter_java.language(), "java")
        else:
            import tree_sitter_kotlin
            parser = tree_sitter.Language(tree_sitter_kotlin.language(), "kotlin")
        ts_parser = tree_sitter.Parser(parser)
        content_bytes = content.encode("utf-8")
        tree = ts_parser.parse(content_bytes)
        root = tree.root_node
        classes: List[str] = []
        methods: List[Tuple[str, int]] = []
        for node in _iter_nodes(root):
            if node.type in ("class_declaration", "object_declaration", "interface_declaration"):
                name_node = _child_by_type(node, "identifier") or _child_by_type(node, "simple_identifier")
                if name_node:
                    name = content_bytes[name_node.start_byte : name_node.end_byte].decode("utf-8", errors="replace")
                    if name and name not in classes:
                        classes.append(name)
            elif node.type in ("method_declaration", "function_declaration"):
                name_node = _child_by_type(node, "identifier") or _child_by_type(node, "simple_identifier")
                if name_node:
                    name = content_bytes[name_node.start_byte : name_node.end_byte].decode("utf-8", errors="replace")
                    if name and not name.lower().startswith("test"):
                        methods.append((name, node.start_point[0] + 1))
        return classes, sorted(methods, key=lambda x: x[1])
    except Exception:
        return _extract_classes_methods_regex(content, path)


def _iter_nodes(node) -> list:
    """Yield node and descendants."""
    yield node
    for c in node.children:
        yield from _iter_nodes(c)


def _child_by_type(node, typ: str):
    for c in node.children:
        if c.type == typ:
            return c
    return None


def _extract_for_file(
    project_path: str,
    rel_path: str,
    content: str,
    file_type: str,
) -> Dict[str, Any]:
    """Extract classes, methods, test_cases for a single file."""
    ext = os.path.splitext(rel_path)[1].lower()
    classes: List[str] = []
    methods: List[Tuple[str, int]] = []
    test_cases: List[Tuple[str, int]] = []

    if ext in (".java", ".kt"):
        try:
            import tree_sitter
            import tree_sitter_java
            import tree_sitter_kotlin
            lang = "java" if ext == ".java" else "kotlin"
            classes, methods = _extract_ast_java_kt(content, rel_path, lang)
        except ImportError:
            classes, methods = _extract_classes_methods_regex(content, rel_path)
        if file_type == "test":
            test_cases = _extract_test_cases_regex(content, rel_path)
    elif ext == ".py":
        classes = _extract_py_classes(content)
        if file_type == "test" or "test" in rel_path.lower():
            test_cases = _extract_test_cases_regex(content, rel_path)

    return {
        "classes": classes,
        "methods": [{"name": m[0], "line": m[1]} for m in methods],
        "test_cases": [{"name": t[0], "line": t[1]} for t in test_cases],
    }


def build_project_index(project_id: str, project_path: str) -> Dict[str, Any]:
    """
    Build a full project index: file tree, classes, methods, test cases.
    Persists to data/project_indexes/<project_id>.json.
    Returns the index dict.
    """
    project_path = str(Path(project_path).resolve())
    if not os.path.isdir(project_path):
        logger.warning("Project path is not a directory: %s", project_path)
        return {}

    files = _walk_project_files(project_path)
    git_head = _get_git_head(project_path)

    classes: List[Dict[str, Any]] = []
    test_files: List[Dict[str, Any]] = []
    file_count = 0
    source_count = 0
    test_count = 0

    for f in files:
        path = f["path"]
        ftype = f["type"]
        file_count += 1
        if ftype == "source":
            source_count += 1
        elif ftype == "test":
            test_count += 1

        full_path = os.path.join(project_path, path)
        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as fp:
                content = fp.read()
        except (OSError, IOError):
            continue

        extracted = _extract_for_file(project_path, path, content, ftype)
        f["classes"] = extracted["classes"]
        f["methods"] = extracted["methods"]
        f["test_cases"] = extracted["test_cases"]

        if ftype == "test" and (extracted["test_cases"] or extracted["classes"]):
            test_files.append({
                "path": path,
                "test_cases": extracted["test_cases"],
                "classes": extracted["classes"],
            })

    index = {
        "version": _INDEX_VERSION,
        "project_id": project_id,
        "project_path": project_path,
        "indexed_at": datetime.now(timezone.utc).isoformat(),
        "git_head": git_head,
        "file_count": file_count,
        "source_count": source_count,
        "test_count": test_count,
        "files": files,
        "test_files": test_files,
    }

    index_path = _get_index_path(project_id)
    try:
        with open(index_path, "w", encoding="utf-8") as fp:
            json.dump(index, fp, indent=2, ensure_ascii=False)
    except (OSError, IOError) as e:
        logger.warning("Failed to save project index: %s", e)

    return index


def _load_index(project_id: str) -> Optional[Dict[str, Any]]:
    """Load index from disk if it exists."""
    path = _get_index_path(project_id)
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as fp:
            return json.load(fp)
    except (json.JSONDecodeError, IOError):
        return None


def is_index_stale(project_path: str, index: Dict[str, Any]) -> bool:
    """Return True if index is stale (git HEAD changed or path mismatch)."""
    stored_path = (index.get("project_path") or "").replace("\\", "/")
    current_path = str(Path(project_path).resolve()).replace("\\", "/")
    if stored_path != current_path:
        return True
    current_head = _get_git_head(project_path)
    stored_head = index.get("git_head")
    if current_head is None and stored_head is None:
        return False
    return current_head != stored_head


def get_project_index(
    project_id: str,
    project_path: str,
    force_rebuild: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    Get project index from cache or build it.
    If force_rebuild=True or index is missing/stale, rebuilds and persists.
    """
    project_path = str(Path(project_path).resolve())
    if not os.path.isdir(project_path):
        return None

    if not force_rebuild:
        index = _load_index(project_id)
        if index and not is_index_stale(project_path, index):
            return index

    return build_project_index(project_id, project_path)


def get_project_summary(project_id: str, project_path: str) -> Optional[Dict[str, Any]]:
    """
    Get summary from cached index (no build). Returns None if not cached or stale.
    Use for dashboard display — fast, never blocks.
    """
    index = _load_index(project_id)
    if not index:
        return None
    project_path = str(Path(project_path).resolve())
    if not os.path.isdir(project_path) or is_index_stale(project_path, index):
        return None
    return {
        "file_count": index.get("file_count", 0),
        "source_count": index.get("source_count", 0),
        "test_count": index.get("test_count", 0),
        "indexed_at": index.get("indexed_at", ""),
    }


def schedule_index_build(project_id: str, project_path: str) -> None:
    """Schedule index build in a background thread (non-blocking)."""
    def _run():
        try:
            build_project_index(project_id, project_path)
            logger.info("Project index built for %s", project_id)
        except Exception as e:
            logger.warning("Project index build failed for %s: %s", project_id, e)

    t = threading.Thread(target=_run, daemon=True)
    t.start()


def invalidate_index(project_id: str) -> bool:
    """Remove cached index. Returns True if removed."""
    path = _get_index_path(project_id)
    if path.exists():
        try:
            path.unlink()
            return True
        except OSError:
            pass
    return False
