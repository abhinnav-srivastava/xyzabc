# Services — AI context

For full project context, see **repository root `CLAUDE.md`**.

Main modules:

- **patch_parser.py** — Unified diff parsing, `git apply --numstat`, rename/delete handling, CLOC on reconstructed files, Android categories, test-case extraction. Entry: `parse_patch(content)`.
- **code_metrics.py** — Diffstat (binary or Python fallback), pygount, radon; `run_patch_metrics()`. Uses `path_utils.get_*_executable()`; only native exes for diffstat (no JAR).
- **checklist_loader.py** — Roles, markdown checklists, steps. **dynamic_categories.py** — Excel → categories. **network_security.py** — Request validation.

Tool paths: `utils/path_utils.py` (`get_git_executable`, `get_cloc_executable`, `get_diffstat_executable`).
