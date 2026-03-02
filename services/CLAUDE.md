# Services — AI context

For full project context, see **repository root `CLAUDE.md`**.

Main modules:

- **patch_parser.py** — Unified diff parsing, `git apply --numstat`, rename/delete handling, CLOC on reconstructed files, Android categories, test-case extraction. Entry: `parse_patch(content)`.
- **code_metrics.py** — Diffstat (binary or Python fallback), pygount, radon; `run_patch_metrics()`. Uses `path_utils.get_*_executable()`; only native exes for diffstat (no JAR).
- **test_coverage_analysis.py** — Test coverage analysis (Level A/B/C): source without tests, methods without tests. Android Java/Kotlin. Level C uses tree-sitter when available.
- **project_index_service.py** — Project index: file tree, classes, methods, test cases. Built when project added; persisted in `data/project_indexes/<id>.json`; invalidated when git HEAD changes. `get_project_index()`, `schedule_index_build()`, `build_project_index()`.
- **checklist_loader.py** — Roles, markdown checklists, steps. **dynamic_categories.py** — Excel → categories. **network_security.py** — Request validation.

Tool paths: `utils/path_utils.py` (`get_git_executable`, `get_cloc_executable`, `get_diffstat_executable`).
