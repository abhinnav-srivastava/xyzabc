"""
Patch Parser Service for Restore app name
Parses unified diff / git patch format. Uses git binary for exact stats (GitLab-accurate)
when available; falls back to pure-Python parsing. Android-focused categories.
"""

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, field

try:
    from utils.path_utils import get_git_executable, get_cloc_executable
except ImportError:
    def get_git_executable() -> str:
        return "git"
    def get_cloc_executable() -> str:
        return "cloc"


# Android file_type categories for summary
ANDROID_FILE_TYPES = ("manifest", "gradle", "resources", "source", "test", "other")

# Test: paths and filename patterns
ANDROID_TEST_PATTERNS = (
    r"/test/",
    r"/androidTest/",
    r"/src/test/",
    r"/src/androidTest/",
    r"\\test\\",
    r"\\androidTest\\",
    r"\\src\\test\\",
    r"\\src\\androidTest\\",
    r"test/java/",
    r"test/kotlin/",
    r"androidTest/java/",
    r"androidTest/kotlin/",
)
ANDROID_TEST_FILE_PATTERNS = (
    r"Test\.java$",
    r"Test\.kt$",
    r"Tests\.kt$",
    r".*Test\.java$",
    r".*Test\.kt$",
    r".*Tests\.kt$",
)
# Manifest: AndroidManifest.xml, manifest*.xml
ANDROID_MANIFEST_PATTERNS = (
    r"AndroidManifest\.xml$",
    r"manifest\.xml$",
    r"/manifest/.*\.xml$",
)
# Gradle: build config and wrapper
ANDROID_GRADLE_PATTERNS = (
    r"\.gradle$",
    r"\.gradle\.kts$",
    r"gradle\.properties$",
    r"settings\.gradle$",
    r"settings\.gradle\.kts$",
    r"gradle-wrapper\.properties$",
    r"build\.gradle$",
    r"build\.gradle\.kts$",
)
# Resources: under res/ (layout, drawable, values, xml, mipmap, anim, etc.)
ANDROID_RES_PATTERN = re.compile(r"/res/|\\\\res\\\\", re.IGNORECASE)
# Source: Kotlin/Java under src/main (or any .java/.kt not already classified)
ANDROID_SOURCE_EXTENSIONS = (".java", ".kt")


@dataclass
class DiffLine:
    """Single line in a hunk."""
    kind: str  # "context", "removed", "added"
    old_lineno: int | None  # 1-based, None for added-only
    new_lineno: int | None  # 1-based, None for removed-only
    content: str  # without leading space/-/+


@dataclass
class Hunk:
    """One hunk (@@ ... @@ block)."""
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    context_line: str
    lines: List[DiffLine] = field(default_factory=list)


@dataclass
class FileDiff:
    """One file in the patch."""
    old_path: str
    new_path: str
    is_new: bool
    is_deleted: bool
    hunks: List[Hunk] = field(default_factory=list)
    # Computed
    lines_added: int = 0
    lines_deleted: int = 0
    file_type: str = "other"  # "manifest" | "gradle" | "resources" | "source" | "test" | "other"


def classify_file_type(path: str) -> str:
    """
    Classify path into Android-specific categories: manifest, gradle, resources, source, test, other.
    Public API for use by project_index_service and other callers.
    """
    return _classify_android_file(path)


def _classify_android_file(path: str) -> str:
    """Classify into Android-specific categories: manifest, gradle, resources, source, test, other."""
    path_n = path.replace("\\", "/")
    path_lower = path_n.lower()

    # Test first (paths and *Test.* names)
    for pat in ANDROID_TEST_PATTERNS:
        if re.search(re.escape(pat.replace("\\", "/")), path_lower):
            return "test"
    for pat in ANDROID_TEST_FILE_PATTERNS:
        if re.search(pat, path_n, re.IGNORECASE):
            return "test"

    # Manifest
    for pat in ANDROID_MANIFEST_PATTERNS:
        if re.search(pat, path_n, re.IGNORECASE):
            return "manifest"

    # Gradle
    for pat in ANDROID_GRADLE_PATTERNS:
        if re.search(pat, path_n, re.IGNORECASE):
            return "gradle"

    # Resources (res/ layout, drawable, values, xml, etc.)
    if ANDROID_RES_PATTERN.search(path_n):
        return "resources"

    # Kotlin/Java source
    for ext in ANDROID_SOURCE_EXTENSIONS:
        if path_lower.endswith(ext):
            return "source"

    # XML/navigation/proguard etc. not under res/ → other (or could add "config" later)
    return "other"


def _parse_unified_diff(text: str) -> List[FileDiff]:
    """Parse unified diff content into list of FileDiff. Handles git diff output."""
    files: List[FileDiff] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        # Start of file: "diff --git a/x b/x" or "--- a/x" then "+++ b/x"
        old_path = ""
        new_path = ""
        is_new = False
        is_deleted = False

        if line.startswith("diff --git "):
            # diff --git a/path b/path
            m = re.match(r"diff --git\s+a/(.+?)\s+b/(.+?)(?:\s|$)", line)
            if m:
                old_path = m.group(1).strip()
                new_path = m.group(2).strip()
                if old_path == "/dev/null" or old_path == "null":
                    is_new = True
                if new_path == "/dev/null" or new_path == "null":
                    is_deleted = True
            i += 1
            # Skip index, mode, etc. until --- or first @@
            while i < len(lines) and not lines[i].startswith("---") and not lines[i].startswith("@@"):
                i += 1
        elif line.startswith("--- "):
            # --- a/path or --- /dev/null
            old_path = line[4:].strip()
            if old_path.startswith("a/"):
                old_path = old_path[2:]
            if old_path == "/dev/null" or old_path == "null":
                is_new = True
            i += 1
            if i < len(lines) and lines[i].startswith("+++ "):
                new_path = lines[i][4:].strip()
                if new_path.startswith("b/"):
                    new_path = new_path[2:]
                if new_path == "/dev/null" or new_path == "null":
                    is_deleted = True
                i += 1
            if not new_path and not is_deleted:
                new_path = old_path
        else:
            i += 1
            continue

        if not old_path and not new_path:
            i += 1
            continue
        if not new_path:
            new_path = old_path
        if not old_path:
            old_path = new_path

        file_diff = FileDiff(
            old_path=old_path,
            new_path=new_path,
            is_new=is_new,
            is_deleted=is_deleted,
        )
        file_diff.file_type = _classify_android_file(new_path)

        # Parse hunks
        while i < len(lines):
            hline = lines[i]
            if hline.startswith("@@ "):
                # @@ -old_start,old_count +new_start,new_count @@
                hm = re.match(r"@@\s+-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s+@@\s*(.*)$", hline)
                if hm:
                    old_start = int(hm.group(1))
                    old_count = int(hm.group(2) or 1)
                    new_start = int(hm.group(3))
                    new_count = int(hm.group(4) or 1)
                    context_line = hm.group(5) or ""
                    hunk = Hunk(
                        old_start=old_start,
                        old_count=old_count,
                        new_start=new_start,
                        new_count=new_count,
                        context_line=context_line,
                    )
                    i += 1
                    old_ln = old_start
                    new_ln = new_start
                    while i < len(lines):
                        cl = lines[i]
                        if cl.startswith("@@") or cl.startswith("diff --git "):
                            break
                        if cl.startswith("\\ "):
                            i += 1
                            continue
                        if not cl:
                            i += 1
                            continue
                        prefix = cl[0] if cl else " "
                        body = cl[1:] if len(cl) > 1 else ""
                        if prefix == " ":
                            hunk.lines.append(DiffLine("context", old_ln, new_ln, body))
                            old_ln += 1
                            new_ln += 1
                            file_diff.lines_added += 0
                            file_diff.lines_deleted += 0
                        elif prefix == "-":
                            hunk.lines.append(DiffLine("removed", old_ln, None, body))
                            old_ln += 1
                            file_diff.lines_deleted += 1
                        elif prefix == "+":
                            hunk.lines.append(DiffLine("added", None, new_ln, body))
                            new_ln += 1
                            file_diff.lines_added += 1
                        i += 1
                    file_diff.hunks.append(hunk)
                else:
                    i += 1
            elif hline.startswith("diff --git ") or (hline.startswith("--- ") and file_diff.hunks):
                break
            else:
                i += 1

        files.append(file_diff)
    return files


def _git_apply_numstat(patch_content: str) -> Optional[List[Tuple[str, int, int]]]:
    """
    Run `git apply --numstat` to get exact add/delete counts per file (GitLab-accurate).
    Uses bundled git from tools/git if present, else PATH. Returns list of (path, additions, deletions) or None.
    """
    git_cmd = get_git_executable()
    try:
        result = subprocess.run(
            [git_cmd, "apply", "--numstat", "-"],
            input=patch_content.encode("utf-8"),
            capture_output=True,
            timeout=30,
        )
        if result.returncode != 0:
            return None
        out = result.stdout.decode("utf-8", errors="replace")
        lines_out: List[Tuple[str, int, int]] = []
        for line in out.splitlines():
            line = line.rstrip("\n\r")
            if not line:
                continue
            parts = line.split("\t", 2)
            if len(parts) < 3:
                continue
            add_s, del_s, path = parts[0], parts[1], parts[2].strip()
            add = int(add_s) if add_s != "-" else 0
            del_ = int(del_s) if del_s != "-" else 0
            lines_out.append((path, add, del_))
        return lines_out
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        return None


def _normalize_path(p: str) -> str:
    """Normalize path for matching (forward slashes, no leading ./)."""
    return p.replace("\\", "/").lstrip("./")


# Regex to detect test method names in diff lines (Kotlin: fun testX, Java: void testX, or testX()
_TEST_METHOD_PATTERN = re.compile(
    r"\b(?:fun|void)\s+(test[A-Za-z0-9_]*)\s*\(|\b(test[A-Za-z0-9_]*)\s*\(",
    re.IGNORECASE,
)


def _extract_test_case_names(fd: "FileDiff") -> Tuple[List[str], List[str]]:
    """
    Scan hunks for added/removed lines that look like test method declarations.
    Returns (added_names, removed_names).
    """
    added_names: List[str] = []
    removed_names: List[str] = []
    seen_added: set = set()
    seen_removed: set = set()

    for hunk in fd.hunks:
        for line in hunk.lines:
            if line.kind == "added":
                for m in _TEST_METHOD_PATTERN.finditer(line.content):
                    name = (m.group(1) or m.group(2) or "").strip()
                    if name and name not in seen_added:
                        seen_added.add(name)
                        added_names.append(name)
            elif line.kind == "removed":
                for m in _TEST_METHOD_PATTERN.finditer(line.content):
                    name = (m.group(1) or m.group(2) or "").strip()
                    if name and name not in seen_removed:
                        seen_removed.add(name)
                        removed_names.append(name)
    return (added_names, removed_names)


def _parse_rename_old_paths(patch_content: str) -> set:
    """
    Parse patch for 'rename from PATH' lines. Returns set of normalized old paths.
    GitLab counts renames as one file; excluding these from the list avoids double-counting.
    """
    out = set()
    for line in patch_content.splitlines():
        s = line.strip()
        if s.startswith("rename from "):
            path = s[12:].strip()
            if path:
                out.add(_normalize_path(path))
    return out


def _parse_deleted_paths_with_matching_create(patch_content: str) -> set:
    """
    Parse 'delete mode 100644 path' and 'create mode 100644 path'. Returns set of
    normalized paths that were deleted and have a create with the same basename
    (delete+create pair = logical rename). Hiding these from the list avoids showing
    the same file twice (old path and new path).
    """
    deleted_paths: List[str] = []
    create_basenames: set = set()
    for line in patch_content.splitlines():
        s = line.strip()
        if s.startswith("delete mode ") and " " in s[12:]:
            path = s.split(" ", 3)[-1].strip()
            if path:
                deleted_paths.append(_normalize_path(path))
        elif s.startswith("create mode ") and " " in s[12:]:
            path = s.split(" ", 3)[-1].strip()
            if path:
                create_basenames.add(os.path.basename(path.replace("\\", "/")))
    return {
        p for p in deleted_paths
        if os.path.basename(p.replace("\\", "/")) in create_basenames
    }


def _reconstruct_new_file_content(fd: FileDiff) -> Optional[str]:
    """Reconstruct the new (post-patch) file content from hunks. Returns None for deleted/binary."""
    if fd.is_deleted or not fd.hunks:
        return None
    lines: List[str] = []
    for hunk in fd.hunks:
        for line in hunk.lines:
            if line.kind in ("context", "added"):
                lines.append(line.content)
    return "\n".join(lines)


def _reconstruct_old_file_content(fd: FileDiff) -> Optional[str]:
    """Reconstruct the old (pre-patch) file content from hunks. Returns None for new file."""
    if fd.is_new or not fd.hunks:
        return None
    lines: List[str] = []
    for hunk in fd.hunks:
        for line in hunk.lines:
            if line.kind in ("context", "removed"):
                lines.append(line.content)
    return "\n".join(lines)


def _run_cloc_on_files(files: List[FileDiff]) -> Optional[Dict[str, Any]]:
    """
    Reconstruct new file contents, write to a temp dir, run cloc (bundled or PATH), return JSON summary.
    Returns e.g. {"by_lang": {"Kotlin": {"code": 100, "files": 2}, ...}, "header": {...}} or None.
    """
    cloc_cmd = get_cloc_executable()
    # Build path -> content for files we can reconstruct (skip deleted, empty)
    to_count: List[Tuple[str, str]] = []
    for f in files:
        if f.is_deleted:
            continue
        content = _reconstruct_new_file_content(f)
        if content is not None:
            path = f.new_path.replace("\\", "/")
            to_count.append((path, content))

    if not to_count:
        return None

    try:
        with tempfile.TemporaryDirectory(prefix="cloc_") as tmp:
            root = Path(tmp)
            for path, content in to_count:
                dest = root / path
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(content, encoding="utf-8", errors="replace")

            result = subprocess.run(
                [cloc_cmd, str(root), "--json", "--quiet"],
                capture_output=True,
                timeout=60,
                cwd=str(root),
            )
            if result.returncode != 0:
                return None
            out = result.stdout.decode("utf-8", errors="replace")
            data = json.loads(out)
            # cloc JSON: {"header": {...}, "Kotlin": {"nFiles": 2, "code": 100, ...}, "SUM": {...}}
            by_lang = {}
            for k, v in data.items():
                if k in ("header", "SUM"):
                    continue
                if isinstance(v, dict) and ("code" in v or "nFiles" in v):
                    by_lang[k] = {
                        "files": v.get("nFiles", v.get("files", 0)),
                        "code": v.get("code", 0),
                        "comment": v.get("comment", 0),
                        "blank": v.get("blank", 0),
                    }
            return {"by_lang": by_lang, "SUM": data.get("SUM"), "header": data.get("header")}
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        return None


def parse_patch(content: str, project_path: Optional[str] = None) -> Tuple[List[FileDiff], Dict[str, Any]]:
    """
    Parse patch: use git apply --numstat for exact stats (GitLab-accurate) when available;
    always use unified-diff parser for hunk content (diff viewer). Fall back to parser-only stats if git fails.
    """
    parsed_files = _parse_unified_diff(content)
    git_numstat = _git_apply_numstat(content)

    if git_numstat is not None and len(git_numstat) > 0:
        # GitLab's MR UI shows stats from base vs head with rename detection (e.g. 68 files, -762).
        # git apply --numstat only lists the *new* path per file, so we get patch-file stats
        # (e.g. 71 files, -953). Excluding rename-old paths would align if numstat listed old paths
        # too, but it does not, so we report what the patch file contains.
        rename_old_paths = _parse_rename_old_paths(content)

        path_to_parsed: Dict[str, FileDiff] = {}
        for f in parsed_files:
            path_to_parsed[_normalize_path(f.new_path)] = f
            path_to_parsed[_normalize_path(f.old_path)] = f

        files = []
        for path, add, del_ in git_numstat:
            key = _normalize_path(path)
            if key in rename_old_paths:
                continue  # skip old path of rename; GitLab counts only the new path as one file
            if key in path_to_parsed:
                fd = path_to_parsed[key]
                fd.lines_added = add
                fd.lines_deleted = del_
                fd.new_path = path
                files.append(fd)
            else:
                # File only in git (e.g. binary or edge case): create minimal FileDiff
                file_type = _classify_android_file(path)
                files.append(
                    FileDiff(
                        old_path=path,
                        new_path=path,
                        is_new=False,
                        is_deleted=False,
                        hunks=[],
                        lines_added=add,
                        lines_deleted=del_,
                        file_type=file_type,
                    )
                )
        total_added = sum(f.lines_added for f in files)
        total_deleted = sum(f.lines_deleted for f in files)
    else:
        # Fallback: parser-only (no git or git failed)
        files = parsed_files
        total_added = sum(f.lines_added for f in files)
        total_deleted = sum(f.lines_deleted for f in files)

    # Paths to hide so we don't show the same logical file twice (rename / delete+create).
    paths_to_hide = _parse_rename_old_paths(content) | _parse_deleted_paths_with_matching_create(content)
    files = [
        f for f in files
        if _normalize_path(f.new_path) not in paths_to_hide
        and not (f.is_deleted and _normalize_path(f.old_path) in paths_to_hide)
    ]
    total_added = sum(f.lines_added for f in files)
    total_deleted = sum(f.lines_deleted for f in files)

    by_type: Dict[str, List[FileDiff]] = {t: [] for t in ANDROID_FILE_TYPES}
    for f in files:
        by_type.setdefault(f.file_type, []).append(f)

    def file_list(ft: str) -> List[Dict[str, Any]]:
        if ft == "test":
            out = []
            for f in by_type.get(ft, []):
                added_names, removed_names = _extract_test_case_names(f)
                out.append({
                    "path": f.new_path,
                    "added": f.lines_added,
                    "deleted": f.lines_deleted,
                    "is_new": f.is_new,
                    "is_deleted": f.is_deleted,
                    "test_cases_added": added_names,
                    "test_cases_removed": removed_names,
                })
            return out
        return [{"path": f.new_path, "added": f.lines_added, "deleted": f.lines_deleted} for f in by_type.get(ft, [])]

    summary = {
        "lines_added": total_added,
        "lines_deleted": total_deleted,
        "files_count": len(files),
        "manifest_files_count": len(by_type.get("manifest", [])),
        "gradle_files_count": len(by_type.get("gradle", [])),
        "resource_files_count": len(by_type.get("resources", [])),
        "source_files_count": len(by_type.get("source", [])),
        "test_files_count": len(by_type.get("test", [])),
        "other_files_count": len(by_type.get("other", [])),
        "manifest_files": file_list("manifest"),
        "gradle_files": file_list("gradle"),
        "resource_files": file_list("resources"),
        "source_files": file_list("source"),
        "test_files": file_list("test"),
        "other_files": file_list("other"),
    }
    # Test-case counts (parsed from test file diffs)
    test_file_list = summary["test_files"]
    summary["test_cases_added_count"] = sum(len(t.get("test_cases_added") or []) for t in test_file_list)
    summary["test_cases_removed_count"] = sum(len(t.get("test_cases_removed") or []) for t in test_file_list)
    # Top changed files (by total lines changed) for at-a-glance summary
    path_to_index = {f.new_path: i for i, f in enumerate(files)}
    all_with_changes = [
        {"path": f.new_path, "added": f.lines_added, "deleted": f.lines_deleted, "total": f.lines_added + f.lines_deleted}
        for f in files
    ]
    top_sorted = sorted(all_with_changes, key=lambda x: x["total"], reverse=True)[:10]
    for item in top_sorted:
        item["file_index"] = path_to_index.get(item["path"], 0)
    summary["top_changed_files"] = top_sorted
    cloc_result = _run_cloc_on_files(files)
    if cloc_result:
        summary["cloc"] = cloc_result
    # Optional: diffstat, pygount, radon, test coverage (see services/code_metrics.py)
    try:
        from services.code_metrics import run_patch_metrics
        extra = run_patch_metrics(
            content, files, summary,
            reconstruct_file_content_fn=_reconstruct_new_file_content,
            project_path=project_path,
        )
        if extra:
            summary.update(extra)
    except Exception:
        pass
    return files, summary


def file_diffs_to_json_serializable(files: List[FileDiff]) -> List[Dict[str, Any]]:
    """Convert FileDiff list to JSON-serializable structure for session storage."""
    out = []
    for f in files:
        out.append({
            "old_path": f.old_path,
            "new_path": f.new_path,
            "is_new": f.is_new,
            "is_deleted": f.is_deleted,
            "lines_added": f.lines_added,
            "lines_deleted": f.lines_deleted,
            "file_type": f.file_type,
            "hunks": [
                {
                    "old_start": h.old_start,
                    "old_count": h.old_count,
                    "new_start": h.new_start,
                    "new_count": h.new_count,
                    "context_line": h.context_line,
                    "lines": [
                        {"kind": l.kind, "old_lineno": l.old_lineno, "new_lineno": l.new_lineno, "content": l.content}
                        for l in h.lines
                    ],
                }
                for h in f.hunks
            ],
        })
    return out


def file_diffs_from_session(data: List[Dict[str, Any]]) -> List[FileDiff]:
    """Reconstruct FileDiff list from session-stored dict (for rendering)."""
    files = []
    for d in data:
        hunks = []
        for h in d.get("hunks", []):
            lines = [
                DiffLine(
                    kind=l.get("kind", "context"),
                    old_lineno=l.get("old_lineno"),
                    new_lineno=l.get("new_lineno"),
                    content=l.get("content", ""),
                )
                for l in h.get("lines", [])
            ]
            hunks.append(Hunk(
                old_start=h.get("old_start", 0),
                old_count=h.get("old_count", 0),
                new_start=h.get("new_start", 0),
                new_count=h.get("new_count", 0),
                context_line=h.get("context_line", ""),
                lines=lines,
            ))
        fd = FileDiff(
            old_path=d.get("old_path", ""),
            new_path=d.get("new_path", ""),
            is_new=d.get("is_new", False),
            is_deleted=d.get("is_deleted", False),
            hunks=hunks,
            lines_added=d.get("lines_added", 0),
            lines_deleted=d.get("lines_deleted", 0),
            file_type=d.get("file_type", "other"),
        )
        files.append(fd)
    return files
