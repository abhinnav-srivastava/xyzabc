# Code Metrics & Tools — CodeCritique

This document describes the **patch-level** code metrics (used when analyzing an uploaded patch) and the **project-level** tools planned for full Android code review (repo path + commit IDs).

**Portable Windows / Electron:** For distribution with **no installation required** (no Python, Java, or PATH), bundle **native Windows executables only** (Git, CLOC, diffstat.exe). See **`docs/PORTABLE_AND_ELECTRON.md`** for the full checklist.

---

## Patch-level metrics (current)

These run on the **patch file** or on **reconstructed files** from the patch (e.g. after applying the diff in memory).

| Tool        | Type   | Purpose                          | How to get it | Where it runs        |
|------------|--------|----------------------------------|---------------|-----------------------|
| **Git**    | Binary | Exact stats (`git apply --numstat`) | Bundled in `tools/git/` or system PATH | Patch content (stdin) |
| **CLOC**   | Binary | Lines of code by language        | Bundled in `tools/cloc/` or PATH | Reconstructed files   |
| **diffstat** | Binary | Insertions/deletions summary    | Bundled in `tools/diffstat/` or PATH; else **parsed in Python** | Patch content (stdin) |
| **Pygount** | Python | LOC by language (alternative to CLOC) | `pip install pygount` | Reconstructed files   |
| **Radon**  | Python | Cyclomatic complexity & maintainability (**.py** only) | `pip install radon` | Reconstructed .py files |

- **Optional Python deps:** `pip install -r requirements-optional.txt` (pygount, radon).
- **Binaries:** Place in `tools/<name>/` or install on system. See below for download links.

### Diffstat (binary)

- **Linux:** `apt install diffstat` / `yum install diffstat`
- **macOS:** `brew install diffstat`
- **Windows:** [GnuWin32 diffstat](https://gnuwin32.sourceforge.net/packages/diffstat.htm) — extract to `tools/diffstat/` (e.g. `diffstat.exe`).  
  If not present, CodeCritique uses a **pure-Python** equivalent (parses the patch).

### CLOC

- **Releases (Windows exe, Linux, macOS):** [cloc releases on GitHub](https://github.com/AlDanial/cloc/releases)  
  Put the executable in `tools/cloc/` (e.g. `cloc.exe`, `cloc-2.08.exe`).
- **PATH:** Or install system-wide (`apt install cloc`, `brew install cloc`).

### Git

- **Windows:** [Git for Windows](https://git-scm.com/download/win) — optional: extract PortableGit to `tools/git/` (e.g. `cmd/git.exe`).
- **Others:** Use system Git (`git` on PATH).

---

## Project-level metrics (future: full Android code review)

The goal is to support **local Git project path + commit ID(s)** and run:

- **Change analysis:** Diff between base and commit(s) (we already have patch parsing).
- **Full project metrics:** Detekt, Android Lint, ktlint, PMD, Semgrep.

| Tool            | Purpose                               | Typical input        | How to get it |
|-----------------|----------------------------------------|----------------------|----------------|
| **Detekt**      | Kotlin static analysis (style, complexity, bugs) | Project root or file list | [Detekt releases](https://github.com/detekt/detekt/releases) — JAR or Gradle plugin |
| **Android Lint**| Android-specific issues (SDK, resources, security) | Android project root | Android SDK (`sdk/cmdline-tools/.../bin/lint`) or `./gradlew :app:lint` |
| **ktlint**      | Kotlin code style                     | Project or file list | [ktlint releases](https://github.com/pinterest/ktlint/releases) |
| **PMD**         | Java/Kotlin/XML static analysis       | Project root or sources | [PMD releases](https://github.com/pmd/pmd/releases) |
| **Semgrep**     | Pattern-based rules (many languages)  | Repo path or diff    | `pip install semgrep` or [Semgrep releases](https://github.com/semgrep/semgrep/releases) |

Planned flow:

1. **Input:** Repository path (e.g. `C:\projects\my-android-app`), optional **base commit**, optional **commit ID(s)** (e.g. MR head).
2. **Change scope:** If commits given, `git diff base..head` → patch; else analyze full working tree.
3. **Run:** For the changed files (or full project), run Detekt, Android Lint, ktlint, PMD, Semgrep as configured.
4. **Output:** Merge results into a single “Full Android Code Review” report (findings, LOC, complexity, lint issues).

The app currently has a **stub** `run_project_metrics(repo_path, commit_ids, base_commit)` in `services/code_metrics.py`; implementation will be added in a future update.

---

## Registry and configuration

- **Tool registry:** `config/metrics_tools.json` — lists patch-level and project-level tools, install notes, and download URLs.
- **Paths:** `utils/path_utils.py` — `get_tools_dir()`, `get_git_executable()`, `get_cloc_executable()`, `get_diffstat_executable()`, `get_tool_executable(tool_id, ...)`.
- **Patch metrics runner:** `services/code_metrics.py` — `run_diffstat_on_patch()`, `run_pygount_on_files()`, `run_radon_on_python_files()`, `run_patch_metrics()`, and `run_project_metrics()` (stub).

---

## Optional: download scripts

- **`scripts/download_metrics_tools.py`** (if present) — Can download CLOC (and optionally diffstat) into `tools/cloc/` and `tools/diffstat/` for the current platform. Run once after clone if you want bundled binaries without installing them system-wide.

---

## Summary

- **Patch today:** Git + CLOC (binaries in `tools/` or PATH), diffstat (binary or Python fallback), Pygount and Radon (optional pip packages). All run on the patch or reconstructed files.
- **Project later:** Repo path + commit(s) → Detekt, Android Lint, ktlint, PMD, Semgrep for a full Android code review and analysis tool.
