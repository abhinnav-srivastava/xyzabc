"""
Test coverage analysis for CodeReview — Android (Java/Kotlin) focused.

Analyzes changed/added methods in the patch and checks whether tests exist in the
**project** (not just patch). When project_path is provided, scans the project
filesystem for test files. Flags methods/classes needing tests or test updates.
"""

import os
import re
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def _normalize_path(p: str) -> str:
    return p.replace("\\", "/").lstrip("./")


def _source_to_test_paths(source_path: str) -> List[str]:
    """
    Derive expected test file paths from source path (Android/Gradle convention).
    e.g. app/src/main/java/com/example/Foo.kt -> app/src/test/java/com/example/FooTest.kt
    """
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


# ---------------------------------------------------------------------------
# Extract changed/added methods from patch (methods touched by diff)
# ---------------------------------------------------------------------------

# Method declaration patterns with capture for name
_METHOD_PATTERNS = [
    re.compile(r"\b(?:override\s+|suspend\s+)?fun\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", re.MULTILINE),
    re.compile(r"\b(?:public|private|protected)\s+(?:static\s+)?(?:final\s+)?(?:[\w<>,\s\[\]]+)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", re.MULTILINE),
    re.compile(r"\bvoid\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", re.MULTILINE),
]

_SKIP_METHODS = frozenset(("equals", "hashCode", "toString", "clone", "finalize"))


def _extract_methods_with_lines(content: str, path: str) -> List[Tuple[str, int]]:
    """Extract (method_name, line_number) from source. Excludes test* methods."""
    ext = os.path.splitext(path)[1].lower()
    if ext not in (".java", ".kt"):
        return []
    lines = content.splitlines()
    result: List[Tuple[str, int]] = []
    seen: Set[str] = set()
    for pat in _METHOD_PATTERNS:
        for m in pat.finditer(content):
            name = m.group(1).strip()
            if not name or name in seen or name in _SKIP_METHODS:
                continue
            if name.lower().startswith("test") or "test" in name.lower():
                continue
            # Find line number
            pos = m.start()
            line_no = content[:pos].count("\n") + 1
            seen.add(name)
            result.append((name, line_no))
    return sorted(result, key=lambda x: x[1])


def _get_touched_line_numbers(fd: Any) -> Set[int]:
    """Get set of line numbers that were added or removed in this file's hunks."""
    touched: Set[int] = set()
    for h in getattr(fd, "hunks", []) or []:
        for line in getattr(h, "lines", []) or []:
            kind = getattr(line, "kind", "")
            if kind == "added":
                ln = getattr(line, "new_lineno", None)
                if ln is not None:
                    touched.add(ln)
            elif kind == "removed":
                ln = getattr(line, "old_lineno", None)
                if ln is not None:
                    touched.add(ln)
    return touched


def _get_changed_methods(
    content: str,
    path: str,
    fd: Any,
) -> List[str]:
    """
    Return method names that were changed or added (their lines appear in diff).
    Uses (method_name, start_line) and assumes method extent to next method.
    """
    methods_with_lines = _extract_methods_with_lines(content, path)
    if not methods_with_lines:
        return []
    touched_lines = _get_touched_line_numbers(fd)
    if not touched_lines:
        return []  # No changes in this file
    # Build line ranges: method i spans [start_i, start_{i+1}-1]
    changed: List[str] = []
    for i, (name, start) in enumerate(methods_with_lines):
        end = methods_with_lines[i + 1][1] - 1 if i + 1 < len(methods_with_lines) else 999999
        for ln in touched_lines:
            if start <= ln <= end:
                changed.append(name)
                break
    return changed


# ---------------------------------------------------------------------------
# Read test files from project filesystem
# ---------------------------------------------------------------------------

def _read_project_file(project_path: Optional[str], relative_path: str) -> Optional[str]:
    """Read file from project. relative_path is e.g. app/src/test/java/.../FooTest.kt"""
    if not project_path or not relative_path:
        return None
    full = os.path.join(project_path, relative_path)
    try:
        if os.path.isfile(full):
            with open(full, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
    except (OSError, IOError):
        pass
    return None


def _find_test_file_in_project(project_path: str, expected_paths: List[str]) -> Optional[Tuple[str, str]]:
    """
    Find first existing test file in project. Returns (normalized_path, content) or None.
    """
    for ep in expected_paths:
        ep_norm = _normalize_path(ep)
        content = _read_project_file(project_path, ep_norm)
        if content:
            return (ep_norm, content)
    return None


# ---------------------------------------------------------------------------
# Test method extraction and matching
# ---------------------------------------------------------------------------

def _extract_test_methods_from_content(content: str) -> List[str]:
    """Extract test method names from test file content (regex)."""
    pat = re.compile(
        r"\b(?:fun|void)\s+(test[A-Za-z0-9_]*)\s*\(|"
        r"\b(test[A-Za-z0-9_]*)\s*\(|"
        r"\b(when_[a-zA-Z0-9_]+)\s*\(|"
        r"\b(given_[a-zA-Z0-9_]+)\s*\(",
        re.IGNORECASE,
    )
    seen: Set[str] = set()
    names: List[str] = []
    for m in pat.finditer(content):
        for g in m.groups():
            if g and g not in seen:
                seen.add(g)
                names.append(g)
    return names


def _method_matches_test(source_method: str, test_methods: List[str]) -> bool:
    """
    Heuristic: does any test method likely cover this source method?
    Conventions: login() -> testLogin(), test_login(), when_login_then_ok, given_login
    """
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


# ---------------------------------------------------------------------------
# Level A: Source files without tests (patch-only fallback)
# ---------------------------------------------------------------------------

def _find_source_without_tests(
    source_files: List[Any],
    test_paths_in_patch: Set[str],
) -> List[Dict[str, Any]]:
    """Source files that have no corresponding test file in the patch (when no project path)."""
    out: List[Dict[str, Any]] = []
    for f in source_files:
        path = _normalize_path(getattr(f, "new_path", "") or getattr(f, "old_path", ""))
        if not path or getattr(f, "is_deleted", False):
            continue
        if not path.endswith((".java", ".kt")):
            continue
        expected = _source_to_test_paths(path)
        if not expected:
            continue
        if not any(_normalize_path(ep) in test_paths_in_patch for ep in expected):
            out.append({
                "path": path,
                "expected_test_paths": expected[:3],
            })
    return out


# ---------------------------------------------------------------------------
# Main analysis entry
# ---------------------------------------------------------------------------

def run_test_coverage_analysis(
    files: List[Any],
    reconstruct_fn: Callable[[Any], Optional[str]],
    project_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run test coverage analysis.

    When project_path is provided:
    - Extracts changed/added methods from patch (methods touched by diff)
    - Scans project filesystem for test files (not just patch)
    - Flags methods needing tests or test updates

    When project_path is None:
    - Falls back to patch-only analysis (source files without tests in patch)
    """
    path_to_file: Dict[str, Any] = {}
    source_files: List[Any] = []
    test_paths_in_patch: Set[str] = set()

    for f in files:
        path = _normalize_path(getattr(f, "new_path", "") or getattr(f, "old_path", ""))
        if not path:
            continue
        path_to_file[path] = f
        ft = getattr(f, "file_type", "other")
        if ft == "source":
            source_files.append(f)
        elif ft == "test":
            test_paths_in_patch.add(path)

    source_without_tests: List[Dict[str, Any]] = []
    methods_without_tests: List[Dict[str, Any]] = []
    analysis_level = "A"

    if project_path and os.path.isdir(project_path):
        # Project-based analysis: changed methods vs project test files
        analysis_level = "B"
        try:
            import tree_sitter  # noqa: F401
            import tree_sitter_kotlin  # noqa: F401
            import tree_sitter_java  # noqa: F401
            analysis_level = "C"
        except ImportError:
            pass

        for f in source_files:
            path = _normalize_path(getattr(f, "new_path", "") or getattr(f, "old_path", ""))
            if not path.endswith((".java", ".kt")):
                continue
            if getattr(f, "is_deleted", False):
                continue
            content = reconstruct_fn(f)
            if not content:
                continue
            changed_methods = _get_changed_methods(content, path, f)
            if not changed_methods:
                continue
            expected_test_paths = _source_to_test_paths(path)
            if not expected_test_paths:
                continue
            test_result = _find_test_file_in_project(project_path, expected_test_paths)
            if not test_result:
                # No test file in project
                source_without_tests.append({
                    "path": path,
                    "expected_test_paths": expected_test_paths[:3],
                })
                for method in changed_methods:
                    methods_without_tests.append({
                        "source_path": path,
                        "method": method,
                        "reason": "no_test_file",
                        "expected_test_paths": expected_test_paths[:2],
                    })
                continue
            test_path, test_content = test_result
            test_methods = _extract_test_methods_from_content(test_content)
            test_in_patch = path_to_file.get(test_path)
            test_modified_in_patch = test_in_patch is not None and (
                getattr(test_in_patch, "lines_added", 0) > 0 or getattr(test_in_patch, "lines_deleted", 0) > 0
            )
            for method in changed_methods:
                if not _method_matches_test(method, test_methods):
                    reason = "test_update_required" if test_modified_in_patch else "no_coverage"
                    methods_without_tests.append({
                        "source_path": path,
                        "test_path": test_path,
                        "method": method,
                        "reason": reason,
                    })
    else:
        # Patch-only fallback: Level A + B/C on patch files only
        source_without_tests = _find_source_without_tests(source_files, test_paths_in_patch)
        try:
            import tree_sitter  # noqa: F401
            import tree_sitter_kotlin  # noqa: F401
            import tree_sitter_java  # noqa: F401
            analysis_level = "C"
        except ImportError:
            pass

        source_to_test_path: Dict[str, str] = {}
        for f in source_files:
            path = _normalize_path(getattr(f, "new_path", "") or getattr(f, "old_path", ""))
            expected = _source_to_test_paths(path)
            for ep in expected:
                ep_norm = _normalize_path(ep)
                if ep_norm in test_paths_in_patch:
                    source_to_test_path[path] = ep_norm
                    break

        for f in source_files:
            path = _normalize_path(getattr(f, "new_path", "") or getattr(f, "old_path", ""))
            if path not in source_to_test_path:
                continue
            if analysis_level == "A":
                analysis_level = "B"
            source_content = reconstruct_fn(f)
            if not source_content:
                continue
            test_path = source_to_test_path[path]
            test_file = path_to_file.get(test_path)
            if not test_file:
                continue
            test_content = reconstruct_fn(test_file)
            if not test_content:
                continue
            source_methods = _extract_methods_with_lines(source_content, path)
            source_method_names = [m[0] for m in source_methods]
            test_methods = _extract_test_methods_from_content(test_content)
            for method in source_method_names:
                if not _method_matches_test(method, test_methods):
                    methods_without_tests.append({
                        "source_path": path,
                        "test_path": test_path,
                        "method": method,
                    })

    return {
        "test_coverage_analysis": {
            "level": analysis_level,
            "source_without_tests": source_without_tests,
            "methods_without_tests": methods_without_tests,
            "source_with_tests_count": len(source_files) - len(source_without_tests),
            "source_total_count": len(source_files),
        },
    }
