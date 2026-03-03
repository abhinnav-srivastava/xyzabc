"""
Project index service for Restore app name.

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

_INDEX_VERSION = 2
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
    re.compile(r"\b(?:fun|void)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", re.MULTILINE),  # any Kotlin/Java method
]
_FIXTURE_METHODS = frozenset(("setup", "teardown", "beforeeach", "aftereach", "beforeall", "afterall", "before", "after"))
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

    def _add(name: str, pos: int) -> None:
        if not name or name in seen:
            return
        if name.lower() in _FIXTURE_METHODS:
            return
        seen.add(name)
        line_no = content[:pos].count("\n") + 1
        result.append((name, line_no))

    if ext in (".java", ".kt"):
        for pat in _TEST_METHOD_PATTERNS:
            for m in pat.finditer(content):
                for g in m.groups():
                    if g:
                        _add(g.strip(), m.start())
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


def _extract_test_cases_ast(content: str, path: str, lang: str) -> List[Tuple[str, int]]:
    """Extract all methods from test file via tree-sitter (accurate, includes any naming)."""
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
        result: List[Tuple[str, int]] = []
        seen: Set[str] = set()
        for node in _iter_nodes(root):
            if node.type in ("method_declaration", "function_declaration"):
                name_node = _child_by_type(node, "identifier") or _child_by_type(node, "simple_identifier")
                if name_node:
                    name = content_bytes[name_node.start_byte : name_node.end_byte].decode("utf-8", errors="replace")
                    if name and name.lower() not in _FIXTURE_METHODS and name not in seen:
                        seen.add(name)
                        result.append((name, node.start_point[0] + 1))
        return sorted(result, key=lambda x: x[1])
    except Exception:
        return _extract_test_cases_regex(content, path)


def _extract_references_ast(
    content: str, path: str, lang: str
) -> Tuple[Set[str], Set[str]]:
    """
    Extract class and method references from file via tree-sitter.
    Returns (instantiated_types, invoked_method_names).
    """
    instantiated: Set[str] = set()
    invoked: Set[str] = set()
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

        def _last_identifier(node) -> Optional[str]:
            """Get rightmost identifier from expression (for Kotlin foo.bar.baz())."""
            if node.type in ("identifier", "simple_identifier", "_reserved_identifier"):
                return content_bytes[node.start_byte : node.end_byte].decode("utf-8", errors="replace")
            for c in reversed(node.children):
                r = _last_identifier(c)
                if r:
                    return r
            return None

        for node in _iter_nodes(root):
            if node.type == "method_invocation":
                name_node = None
                try:
                    name_node = node.child_by_field_name("name")
                except (AttributeError, TypeError):
                    pass
                if not name_node:
                    for c in node.children:
                        if c.type in ("identifier", "_reserved_identifier"):
                            name_node = c
                            break
                if name_node:
                    name = content_bytes[name_node.start_byte : name_node.end_byte].decode("utf-8", errors="replace")
                    if name and not name.startswith("_"):
                        invoked.add(name)
            elif node.type in ("object_creation_expression", "_unqualified_object_creation_expression"):
                for c in node.children:
                    if c.type in ("type_identifier", "scoped_type_identifier", "generic_type"):
                        type_name = content_bytes[c.start_byte : c.end_byte].decode("utf-8", errors="replace")
                        if type_name and type_name not in ("new",):
                            base = type_name.split("<")[0].split(".")[-1]
                            if base and len(base) > 0 and base[0].isupper():
                                instantiated.add(base)
                        break
            elif node.type == "constructor_invocation":
                for c in node.children:
                    if c.type in ("user_type", "type_identifier", "simple_identifier"):
                        type_name = content_bytes[c.start_byte : c.end_byte].decode("utf-8", errors="replace")
                        if type_name:
                            base = type_name.split("<")[0].split(".")[-1]
                            if base and len(base) > 0 and base[0].isupper():
                                instantiated.add(base)
                        break
            elif node.type == "call_expression":
                if node.children:
                    receiver = node.children[0]
                    name = _last_identifier(receiver)
                    if name and not name.startswith("_"):
                        invoked.add(name)
    except Exception:
        pass
    return (instantiated, invoked)


def extract_methods_with_lines_ast(content: str, path: str) -> List[Tuple[str, int]]:
    """
    Extract (method_name, line) from Java/Kotlin source. Uses tree-sitter when available.
    Excludes test* methods. Public API for test coverage analysis.
    """
    ext = os.path.splitext(path)[1].lower()
    if ext not in (".java", ".kt"):
        return []
    try:
        import tree_sitter
        import tree_sitter_java
        import tree_sitter_kotlin
        lang = "java" if ext == ".java" else "kotlin"
        _, meth_list = _extract_ast_java_kt(content, path, lang)
        return meth_list
    except Exception:
        _, meth_list = _extract_classes_methods_regex(content, path)
        return meth_list


def extract_entities_ast(content: str, path: str, file_type: str) -> Dict[str, List[str]]:
    """
    Extract classes, methods, and test_cases from content via tree-sitter.
    Public API for patch AST analysis. Returns {"classes": [...], "methods": [...], "test_cases": [...]}.
    """
    ext = os.path.splitext(path)[1].lower()
    classes: List[str] = []
    methods: List[str] = []
    test_cases: List[str] = []
    if ext in (".java", ".kt"):
        try:
            import tree_sitter
            import tree_sitter_java
            import tree_sitter_kotlin
            lang = "java" if ext == ".java" else "kotlin"
            cls_list, meth_list = _extract_ast_java_kt(content, path, lang)
            classes = cls_list
            methods = [m[0] for m in meth_list]
            if file_type == "test":
                tc_list = _extract_test_cases_ast(content, path, lang)
                test_cases = [t[0] for t in tc_list]
        except Exception:
            classes, meth_tuples = _extract_classes_methods_regex(content, path)
            methods = [m[0] for m in meth_tuples]
            if file_type == "test":
                tc_tuples = _extract_test_cases_regex(content, path)
                test_cases = [t[0] for t in tc_tuples]
    return {"classes": classes, "methods": methods, "test_cases": test_cases}


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
            if file_type == "test":
                test_cases = _extract_test_cases_ast(content, rel_path, lang)
            else:
                test_cases = []
        except ImportError:
            classes, methods = _extract_classes_methods_regex(content, rel_path)
            if file_type == "test":
                test_cases = _extract_test_cases_regex(content, rel_path)
            else:
                test_cases = []
    elif ext == ".py":
        classes = _extract_py_classes(content)
        if file_type == "test" or "test" in rel_path.lower():
            test_cases = _extract_test_cases_regex(content, rel_path)

    refs_instantiated: List[str] = []
    refs_invoked: List[str] = []
    if ext in (".java", ".kt"):
        try:
            import tree_sitter
            import tree_sitter_java
            import tree_sitter_kotlin
            lang = "java" if ext == ".java" else "kotlin"
            inst, inv = _extract_references_ast(content, rel_path, lang)
            refs_instantiated = sorted(inst)
            refs_invoked = sorted(inv)
        except ImportError:
            pass

    return {
        "classes": classes,
        "methods": [{"name": m[0], "line": m[1]} for m in methods],
        "test_cases": [{"name": t[0], "line": t[1]} for t in test_cases],
        "refs_instantiated": refs_instantiated,
        "refs_invoked": refs_invoked,
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
        f["refs_instantiated"] = extracted.get("refs_instantiated", [])
        f["refs_invoked"] = extracted.get("refs_invoked", [])

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
    """Return True if index is stale (version mismatch, path/git change)."""
    if index.get("version", 0) < _INDEX_VERSION:
        return True
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


def _source_to_test_paths(source_path: str) -> List[str]:
    """Derive expected test file paths from source path (Android/Gradle convention)."""
    path = _normalize_path(source_path)
    base = os.path.basename(path)
    name, ext = os.path.splitext(base)
    if ext not in (".java", ".kt"):
        return []
    result: List[str] = []
    for main, test_dir in [("src/main", "src/test"), ("src/main", "src/androidTest")]:
        if main in path:
            test_path = path.replace(main, test_dir, 1)
            for suffix in ("Test", "Tests"):
                candidate = test_path.replace(f"{name}{ext}", f"{name}{suffix}{ext}")
                result.append(candidate)
    return result


def _method_matches_test(source_method: str, test_methods: List[str]) -> bool:
    """Heuristic: does any test method likely cover this source method?"""
    src_lower = source_method.lower()
    src_camel = source_method[0].upper() + source_method[1:] if source_method else ""
    for tm in test_methods:
        tm_lower = tm.lower()
        if src_lower in tm_lower:
            return True
        if f"test{src_camel}" in tm or f"test_{src_lower}" in tm_lower:
            return True
        if tm_lower.startswith("when_") and src_lower in tm_lower:
            return True
        if tm_lower.startswith("given_") and src_lower in tm_lower:
            return True
    return False


def build_source_hierarchy(index: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Build hierarchical view: File -> Class -> Methods, with AST-based class/method refs in test files.
    Uses refs_instantiated and refs_invoked from tree-sitter for accurate cross-file references.
    """
    files = index.get("files", [])
    test_path_to_file: Dict[str, Dict[str, Any]] = {}
    for f in files:
        if f.get("type") == "test":
            test_path_to_file[_normalize_path(f["path"])] = f

    # Build: class_name -> [test_file_paths that reference it via AST]
    class_to_tests: Dict[str, List[str]] = {}
    # Build: method_name -> [test_file_paths that invoke it via AST]
    method_to_tests: Dict[str, List[str]] = {}

    for tf_path, tf in test_path_to_file.items():
        for cls in tf.get("classes", []):
            class_to_tests.setdefault(cls, []).append(tf_path)
        for t in tf.get("refs_instantiated", []):
            class_to_tests.setdefault(t, []).append(tf_path)
        for m in tf.get("refs_invoked", []):
            method_to_tests.setdefault(m, []).append(tf_path)

    result: List[Dict[str, Any]] = []
    for f in files:
        if f.get("type") != "source":
            continue
        path = f.get("path", "")
        path_norm = _normalize_path(path)
        classes = f.get("classes", [])
        methods = f.get("methods", [])

        # Class refs: test files that reference any of our classes (AST or path convention)
        expected_test_paths = _source_to_test_paths(path)
        seen_test_paths: Set[str] = set()
        class_refs_in_test: List[Dict[str, Any]] = []

        for cls in (classes or ["(no class)"]):
            if cls == "(no class)":
                continue
            for tp in class_to_tests.get(cls, []):
                if tp not in seen_test_paths:
                    seen_test_paths.add(tp)
                    tf = test_path_to_file.get(tp)
                    test_methods = [t.get("name", "") for t in (tf or {}).get("test_cases", [])]
                    class_refs_in_test.append({"path": tp, "test_cases": test_methods})

        for tp in expected_test_paths:
            tp_norm = _normalize_path(tp)
            if tp_norm not in seen_test_paths and tp_norm in test_path_to_file:
                seen_test_paths.add(tp_norm)
                tf = test_path_to_file[tp_norm]
                test_methods = [t.get("name", "") for t in tf.get("test_cases", [])]
                class_refs_in_test.append({"path": tp_norm, "test_cases": test_methods})

        # Method refs: test files that invoke this method (AST) or heuristic match
        method_refs: List[Dict[str, Any]] = []
        for m in methods:
            mname = m.get("name", "") if isinstance(m, dict) else str(m)
            refs: List[Dict[str, str]] = []
            seen_refs: Set[Tuple[str, str]] = set()
            for tp in method_to_tests.get(mname, []):
                tf = test_path_to_file.get(tp)
                if tf:
                    for tc in tf.get("test_cases", []):
                        tc_name = tc.get("name", "") if isinstance(tc, dict) else str(tc)
                        key = (tp, tc_name)
                        if key not in seen_refs:
                            seen_refs.add(key)
                            refs.append({"test_file": tp, "test_method": tc_name})
            if not refs:
                for ref in class_refs_in_test:
                    for tc in ref.get("test_cases", []):
                        tc_name = tc if isinstance(tc, str) else tc.get("name", "")
                        if _method_matches_test(mname, [tc_name]):
                            refs.append({"test_file": ref["path"], "test_method": tc_name})
                            break
            method_refs.append({
                "name": mname,
                "line": m.get("line") if isinstance(m, dict) else None,
                "refs_in_test": refs if refs else None,
            })

        result.append({
            "path": path,
            "classes": classes or ["(no class)"],
            "methods": method_refs,
            "class_refs_in_test": class_refs_in_test if class_refs_in_test else None,
        })
    return result


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
