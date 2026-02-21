# CodeCritique — Cursor / AI context

**Primary context:** See **project root `CLAUDE.md`** for full project overview, key paths, conventions, and run instructions.

**Short summary:** Flask code review checklist app with optional patch upload, Android-focused patch summary, GitLab-style diff viewer, and role-based checklists. Intended for **portable Windows / Electron** (no install); all tools (Git, CLOC, diffstat) are **native executables** under `tools/` — JARs are not used (they open a window). Paths and tool resolution in `utils/path_utils.py`; patch parsing and metrics in `services/patch_parser.py` and `services/code_metrics.py`.
