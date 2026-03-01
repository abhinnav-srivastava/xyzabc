"""
Code metrics for CodeReview: patch-level and (future) project-level.

Patch-level: run on patch content or on reconstructed files from the patch.
- Git, CLOC: used in patch_parser.
- diffstat: optional binary on patch stdin.
- pygount: optional Python lib for LOC by language.
- radon: optional Python lib for complexity/maintainability on .py files.

Project-level (future): repo_path + commit_id(s) -> Detekt, Android Lint, ktlint, PMD, Semgrep.
"""

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from utils.path_utils import get_tools_dir, get_diffstat_executable, get_cloc_executable
except ImportError:
    def get_tools_dir() -> Path:
        return Path("tools")
    def get_diffstat_executable() -> str:
        return "diffstat"
    def get_cloc_executable() -> str:
        return "cloc"


# ---------------------------------------------------------------------------
# Diffstat (patch stdin) — binary or pure-Python fallback
# ---------------------------------------------------------------------------

def run_diffstat_on_patch(patch_content: str) -> Optional[Dict[str, Any]]:
    """
    Run diffstat on patch (insertions/deletions per file and total).
    Uses binary (or java -jar for .jar in tools/diffstat) if available, else parses in Python.
    JARs are run with patch written to a temp file and path passed as first arg (many JARs don't read stdin).
    """
    cmd_path = get_diffstat_executable()
    if cmd_path.lower().endswith(".jar"):
        # JAR: write patch to temp file and pass path (DiffStats.jar etc. often expect file path)
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".patch",
                delete=False,
                encoding="utf-8",
                errors="replace",
            ) as f:
                f.write(patch_content)
                patch_file = f.name
            try:
                result = subprocess.run(
                    ["java", "-jar", cmd_path, patch_file],
                    capture_output=True,
                    timeout=15,
                )
            finally:
                Path(patch_file).unlink(missing_ok=True)
        except Exception:
            return _diffstat_from_patch_parse(patch_content)
        out = (result.stdout or b"").decode("utf-8", errors="replace")
        if result.stderr:
            out += "\n" + (result.stderr).decode("utf-8", errors="replace")
        summary = _parse_diffstat_output(out)
        if summary is None:
            return _diffstat_from_patch_parse(patch_content)
        summary["raw"] = out.strip() or None
        return summary
    # Binary: stdin
    run_cmd = [cmd_path, "-p1", "-u", "-t"]
    try:
        result = subprocess.run(
            run_cmd,
            input=patch_content.encode("utf-8", errors="replace"),
            capture_output=True,
            timeout=15,
        )
        if result.returncode != 0:
            return _diffstat_from_patch_parse(patch_content)
        out = result.stdout.decode("utf-8", errors="replace")
        if result.stderr:
            out += "\n" + result.stderr.decode("utf-8", errors="replace")
        summary = _parse_diffstat_output(out)
        if summary is None:
            return _diffstat_from_patch_parse(patch_content)
        summary["raw"] = out.strip()
        return summary
    except (FileNotFoundError, subprocess.TimeoutExpired, UnicodeDecodeError, OSError):
        return _diffstat_from_patch_parse(patch_content)


def _parse_diffstat_output(out: str) -> Optional[Dict[str, Any]]:
    """Parse diffstat or JAR output for files changed, insertions, deletions."""
    summary = {"raw": None, "files_changed": 0, "insertions": 0, "deletions": 0}
    m = re.search(r"(\d+)\s+files?\s+changed", out, re.IGNORECASE)
    if m:
        summary["files_changed"] = int(m.group(1))
    m = re.search(r"(\d+)\s+insertions?\s*\(\+\)", out, re.IGNORECASE)
    if m:
        summary["insertions"] = int(m.group(1))
    m = re.search(r"(\d+)\s+deletions?\s*\(-\)", out, re.IGNORECASE)
    if m:
        summary["deletions"] = int(m.group(1))
    # Also accept numeric patterns without "insertions"/"deletions" (e.g. "+N -M")
    if summary["insertions"] == 0 and summary["deletions"] == 0:
        m = re.search(r"\+(\d+)\s*[,\s]\s*\-(\d+)", out)
        if m:
            summary["insertions"] = int(m.group(1))
            summary["deletions"] = int(m.group(2))
    if summary["files_changed"] == 0:
        m = re.search(r"(\d+)\s+file", out, re.IGNORECASE)
        if m:
            summary["files_changed"] = int(m.group(1))
    if summary["files_changed"] or summary["insertions"] or summary["deletions"]:
        return summary
    return None


def _diffstat_from_patch_parse(patch_content: str) -> Dict[str, Any]:
    """Pure-Python: count insertions/deletions from unified diff lines."""
    insertions = deletions = 0
    files_seen = set()
    current_file = None
    for line in patch_content.splitlines():
        if line.startswith("diff --git "):
            m = re.match(r"diff --git\s+a/(.+?)\s+b/(.+?)(?:\s|$)", line)
            if m:
                current_file = m.group(2).strip()
                if current_file and current_file not in ("/dev/null", "null"):
                    files_seen.add(current_file)
        elif line.startswith("+++ ") and "dev/null" not in line:
            p = line[4:].strip().lstrip("b/")
            if p and p not in ("/dev/null", "null"):
                files_seen.add(p)
        elif len(line) > 0:
            if line[0] == "+" and not line.startswith("+++"):
                insertions += 1
            elif line[0] == "-" and not line.startswith("---"):
                deletions += 1
    return {
        "raw": None,
        "files_changed": len(files_seen),
        "insertions": insertions,
        "deletions": deletions,
        "source": "parsed",
    }


# ---------------------------------------------------------------------------
# Pygount (LOC by language) — Python package
# ---------------------------------------------------------------------------

def run_pygount_on_files(
    file_paths_with_content: List[Tuple[str, str]],
    timeout: int = 60,
) -> Optional[Dict[str, Any]]:
    """
    Run pygount on a list of (path, content). Writes to temp dir and runs pygount.
    Returns e.g. {"by_lang": {"Kotlin": {"code": 100, "files": 2}}, "SUM": {...}} or None.
    """
    try:
        from pygount import ProjectSummary, SourceAnalysis
    except ImportError:
        return None

    if not file_paths_with_content:
        return None

    try:
        with tempfile.TemporaryDirectory(prefix="pygount_") as tmp:
            root = Path(tmp)
            written: List[Path] = []
            for path, content in file_paths_with_content:
                dest = root / path.replace("\\", "/")
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(content, encoding="utf-8", errors="replace")
                written.append(dest)

            project_summary = ProjectSummary()
            for path in written:
                try:
                    analysis = SourceAnalysis.from_file(str(path), "language")
                    project_summary.add(analysis)
                except Exception:
                    continue

            lang_map = getattr(project_summary, "language_to_language_summary_map", None)
            if not lang_map:
                return None
            by_lang: Dict[str, Dict[str, Any]] = {}
            total_code = total_files = 0
            for lang, summary in lang_map.items():
                code = getattr(summary, "code_count", 0) or getattr(summary, "code", 0)
                n_files = getattr(summary, "file_count", 0) or getattr(summary, "files", 0)
                if not n_files and code:
                    n_files = 1
                by_lang[lang] = {"code": code, "files": n_files}
                total_code += code
                total_files += n_files
            return {
                "by_lang": by_lang,
                "SUM": {"code": total_code, "files": total_files},
                "source": "pygount",
            }
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Radon (complexity, maintainability) — Python files only
# ---------------------------------------------------------------------------

def run_radon_on_python_files(
    file_paths_with_content: List[Tuple[str, str]],
    timeout: int = 30,
) -> Optional[Dict[str, Any]]:
    """
    Run radon cc (cyclomatic complexity) and mi (maintainability) on .py files.
    Returns e.g. {"cc": [...], "mi": [...]} or None.
    """
    try:
        import radon.complexity as radon_cc
        import radon.metrics as radon_mi
    except ImportError:
        return None

    py_files = [(p, c) for p, c in file_paths_with_content if p.endswith(".py")]
    if not py_files:
        return None

    out_cc: List[Dict[str, Any]] = []
    out_mi: List[Dict[str, Any]] = []
    try:
        for path, content in py_files:
            try:
                cc_result = radon_cc.cc_visit(content)
                for block in cc_result:
                    out_cc.append({
                        "file": path,
                        "name": getattr(block, "name", ""),
                        "complexity": getattr(block, "complexity", 0),
                        "line": getattr(block, "lineno", 0),
                    })
            except Exception:
                pass
            try:
                mi = radon_mi.mi_visit(content, True)
                out_mi.append({"file": path, "mi": mi, "rank": radon_mi.mi_rank(mi)})
            except Exception:
                pass
        if not out_cc and not out_mi:
            return None
        return {"cc": out_cc, "mi": out_mi, "source": "radon"}
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Unified: run all patch metrics (optional tools)
# ---------------------------------------------------------------------------

def run_patch_metrics(
    patch_content: str,
    files: List[Any],
    summary: Dict[str, Any],
    reconstruct_file_content_fn,
    timeout_per_tool: int = 60,
) -> Dict[str, Any]:
    """
    Run all enabled patch-level metrics and return extra dict to merge into summary.
    - diffstat: always (binary or parsed)
    - pygount: if installed, on reconstructed files (alternative/extra to CLOC)
    - radon: if installed, on reconstructed .py files only

    files: list of FileDiff-like objects with .new_path, .is_deleted, etc.
    reconstruct_file_content_fn(f) -> str | None.
    """
    extra: Dict[str, Any] = {}

    # 1) Diffstat on raw patch
    ds = run_diffstat_on_patch(patch_content)
    if ds:
        extra["diffstat"] = ds

    # 2) Reconstruct file list for Python-based tools
    to_analyze: List[Tuple[str, str]] = []
    for f in files:
        if getattr(f, "is_deleted", True):
            continue
        path = (getattr(f, "new_path", None) or "").replace("\\", "/")
        if not path:
            continue
        content = reconstruct_file_content_fn(f)
        if content is not None:
            to_analyze.append((path, content))

    # 3) Pygount (if CLOC not already in summary, or as extra)
    try:
        pg = run_pygount_on_files(to_analyze, timeout=timeout_per_tool)
        if pg and (not summary.get("cloc") or summary.get("metrics_include_pygount")):
            extra["pygount"] = pg
    except Exception:
        pass

    # 4) Radon on Python files only
    try:
        radon_result = run_radon_on_python_files(to_analyze, timeout=timeout_per_tool)
        if radon_result:
            extra["radon"] = radon_result
    except Exception:
        pass

    return extra


# ---------------------------------------------------------------------------
# Future: project-level analysis (stub)
# ---------------------------------------------------------------------------

def run_project_metrics(
    repo_path: str,
    commit_ids: Optional[List[str]] = None,
    base_commit: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Stub for full project analysis: Detekt, Android Lint, ktlint, PMD, Semgrep.
    Requires repo_path to exist. If commit_ids provided, analyze only those commits' changes;
    else analyze full working tree.
    """
    result: Dict[str, Any] = {
        "repo_path": repo_path,
        "commit_ids": commit_ids,
        "base_commit": base_commit,
        "detekt": None,
        "android_lint": None,
        "ktlint": None,
        "pmd": None,
        "semgrep": None,
        "message": "Project metrics not implemented yet. See docs/CODE_METRICS_AND_TOOLS.md.",
    }
    return result
