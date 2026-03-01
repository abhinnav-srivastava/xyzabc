# CodeCritique — context for AI assistants

Use this file for project context when editing or reviewing this codebase.

## What this project is

**CodeCritique** is a **code review checklist app**: role-based checklists (from Markdown/Excel), optional **patch upload** (unified diff), **patch summary** (Android categories, LOC, test cases), **GitLab-style diff viewer**, then checklist review and export (HTML/PDF). Target: **portable Windows / Electron** distribution with **no installation required** (all tools bundled; no system Python/Java/PATH).

- **Stack:** Flask 3.x, Jinja2, Bootstrap 5, PWA, Waitress.
- **Paths:** `utils/path_utils.py` — all paths (dev + PyInstaller/portable); `get_tools_dir()`, `get_git_executable()`, `get_cloc_executable()`, `get_diffstat_executable()`.

## Key paths

| Area | Location |
|------|----------|
| App & routes | `app.py` — `create_app()`, routes for `/`, `/login`, `/start`, `/review/patch`, `/patch-summary`, `/review/code`, `/upload-patch`, `/patch-clear`, review/summary/download |
| Patch parsing & metrics | `services/patch_parser.py` — unified diff parsing, `git apply --numstat`, rename/delete-from handling, CLOC on reconstructed files, `parse_patch()`, Android categories (manifest, gradle, resources, source, test, other), test-case extraction |
| Code metrics (patch) | `services/code_metrics.py` — diffstat (binary or Python fallback), pygount, radon; `run_patch_metrics()`; project-level stub |
| Paths & tools | `utils/path_utils.py` — `get_project_root()`, `get_tools_dir()`, `get_git_executable()`, `get_cloc_executable()`, `get_diffstat_executable()` (native exe only; JARs ignored to avoid GUI windows) |
| Checklists | `services/checklist_loader.py`, `checklists/markdown/`, `config/roles.json`, `services/dynamic_categories.py` (Excel → categories) |
| Config | `config/app_config.json`, `config/roles.json`, `config/metrics_tools.json` (tools registry) |
| Patch storage | Patch data in `temp/patch_store/<uuid>.json`; session holds `patch_data_key` |
| Templates | `templates/` — `base.html`, `review_patch.html`, `patch_summary.html`, `review_code.html`, `review_code_tree.html`, `upload_patch.html`, etc. |
| Bundled tools | `tools/git/`, `tools/cloc/`, `tools/diffstat/` — native executables only (e.g. `git.exe`, `cloc.exe`, `diffstat.exe`). JARs in `tools/diffstat/` are **not** used (they open a window). |

## Conventions

- **Portable first:** Prefer bundled binaries under `tools/`; no reliance on system PATH, pip, or Java for core features. See `docs/PORTABLE_AND_ELECTRON.md`.
- **Patch flow:** Upload patch → parse with `parse_patch()` → summary (stats, Android categories, CLOC, diffstat, optional pygount/radon) → diff viewer (file tree + stacked diffs) → checklist.
- **Diffstat:** Only native `diffstat.exe` / `diffstat` is used; JARs are ignored. Fallback: pure-Python parsing in `code_metrics.py`.
- **Session:** Review state and patch reference in Flask session; patch content in server-side files under `temp/patch_store/`.

## Run & build

- **Dev:** `python app.py --dev-server` (or `python app.py` for Waitress).
- **Portable:** `build.py` for PyInstaller; bundle `tools/git`, `tools/cloc`, `tools/diffstat` (exes only).
- **Electron:** See `docs/PORTABLE_AND_ELECTRON.md` for what to bundle (Git, CLOC, diffstat as Windows exes; no JAR, no pip at runtime).

## Docs

- **README.md** — Overview, layout, flows, bundled tools, run.
- **docs/CODE_METRICS_AND_TOOLS.md** — Patch and project-level tools, install/bundle notes.
- **docs/PORTABLE_AND_ELECTRON.md** — Portable Windows/Electron checklist, no-install requirements.
- **tools/*/README.md** — What to put in each tool folder (git, cloc, diffstat).

## When editing

- Use `path_utils` for any path under the project or tools; support both dev and frozen (PyInstaller) if adding new paths.
- Adding a new patch-level metric: implement in `services/code_metrics.py`, call from `run_patch_metrics()`; register in `config/metrics_tools.json` if desired.
- Adding routes: add in `app.py` and corresponding template; preserve session flow for review/patch.
