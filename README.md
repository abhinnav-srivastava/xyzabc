# CodeReview – Project Analysis

## What It Is

**CodeReview** is a **code review checklist app**: reviewers go through role-based, category-driven checklists and record pass/fail/comment per item. It’s a **Flask** web app with **PWA** support, optional **offline**, and **HTML/PDF export**.

---

## Architecture Overview

| Layer | Tech / Location |
|-------|------------------|
| **Web** | Flask 3.x, Jinja2 templates, Bootstrap 5, Bootstrap Icons |
| **Checklists** | Markdown (primary) + Excel (source for dynamic categories) |
| **Config** | JSON (`app_config.json`, `roles.json`, `network_security.json`, etc.) |
| **Paths** | `utils/path_utils.py` (dev + PyInstaller portable) |
| **Deploy** | Waitress (default) or Flask dev server; `wsgi.py` for WSGI |

---

## Directory Layout

- **`app.py`** – Flask app factory, routes, session-based review state, summary/export logic.
- **`config/`** – `app_config.json` (app/UI/export/security), `roles.json` (roles → markdown checklists), `network_security.json`, etc.
- **`services/`**
  - **`checklist_loader.py`** – Loads `roles.json`, parses markdown checklists (per-role `.md`), builds flat “steps” (role|category|item). Item types: MUST / RECOMMENDED / GOOD / OPTIONAL.
  - **`dynamic_categories.py`** – Scans Excel under `checklists/excel`, reads `MainCategory`/`Category`, updates `roles.json` and category metadata.
  - **`patch_parser.py`** – Parses unified diff / git patch. Uses **git** (bundled in `tools/git/` or PATH) for **git apply --numstat** (exact, GitLab-accurate stats); uses **cloc** (bundled in `tools/cloc/` or PATH) for lines-of-code breakdown by language. Falls back to pure-Python parsing when git is unavailable. Produces Android-focused categories and per-file hunks for the diff viewer.
  - **`network_security.py`** – Validates requests (IP/allowlist); used in `@app.before_request`.
  - **`git_operations.py`** – Git pull/push using system credential helper (Windows Credential Manager, Git Credential Manager, etc.); `get_credential_helper_info()` for detection.
- **`checklists/markdown/`** – One consolidated markdown per role (e.g. `self/self_consolidated.md`, `peer/peer_consolidated.md`). Structure: `# Role`, `## Category`, then list items (MUST:/RECOMMENDED:/GOOD:/OPTIONAL: and optional “How to Measure”, “Rule Reference”, etc.).
- **`checklists/markdown/guidelines/`** – Reference guidelines (e.g. `android_coding_guidelines.md`) used for the “Guidelines” section.
- **`templates/`** – `base.html` (nav, PWA meta), `index.html`, `start_review.html`, `review_all_categories.html`, `review_category_table.html`, `summary.html`, `guidelines.html`, `individual_guideline.html`, `report_standalone.html`, `offline.html`, `empty.html`.
- **`static/`** – CSS, JS (`app.js`, `pwa.js`), service worker (`sw.js`), manifest, icons.
- **`scripts/py/`** – `auto_update_checklists.py`, `auto_update_checklists_category.py` (Excel → markdown / category updates), `convert_excel_to_markdown.py`.
- **`utils/path_utils.py`** – Base dir, project root, config/checklists/scripts/static/templates paths; supports frozen (PyInstaller) and dev.
- **`build.py`** – Orchestrates portable/desktop builds (e.g. PyInstaller, desktop setup).

---

## Main User Flows

1. **Home** (`/`) – Landing with “Start Review”. Login required; name/role from login.
2. **Start Review** (`/start`) – GET initializes review from session (login data); redirects to **Patch** (step 2).
3. **Patch** (`/review/patch`) – Step 2: Upload a `.patch` file or paste a unified diff (e.g. from GitLab MR), or **Skip** to go straight to checklist. No system Git required; parsing is in-app. Android-focused (source vs test file classification).
4. **Patch analysis & summary** (`/patch-summary`) – MR-style summary: lines added/deleted, source vs test files. “View changes” (diff) and **Continue to checklist review**.
5. **Review code** (`/review/code`) – GitLab-style diff viewer: file list and per-file unified diff (line numbers, added/removed highlighting).
6. **Checklist review**  
   - **Single-page** – `/review/all`: one page with all categories and items; POST submits all and redirects to summary.  
   - **Category-by-category** – `/review/category/<idx>`: one category at a time; each form POST saves to session and moves prev/next or to summary.
7. **Summary** (after checklist) (`/summary`) – Computes pass/fail/unanswered counts, shows results, stores “review completed” and duration in session.
8. **Export** – `/download/html`, `/download/pdf` – generate report from session data.
9. **Guidelines** – `/guidelines` (list/filter), `/guideline/<rule_id>` (single guideline). Data from markdown under `checklists/markdown/guidelines/`.

Additional routes: `/refresh`, `/refresh-categories`, `/refresh-all` (reload checklists/categories); `/offline`, `/api/sync-offline-data`; `/manifest.json`, `/sw.js` for PWA. **Git sync:** `POST /api/git/pull`, `POST /api/git/push` (use system credential helper for auth); `GET /api/git/credentials-info` (detect credential helper).

---

## Data Model (Conceptual)

- **Roles** – From `roles.json` (e.g. self, peer, techlead, fo, architect), each pointing to one or more markdown checklists.
- **Categories** – Sections inside each markdown (`## Category Name`); can be driven by Excel via `dynamic_categories`.
- **Items** – Bullet items under a category; optional type (MUST/RECOMMENDED/GOOD/OPTIONAL) and subfields (How to Measure, Rule Reference, etc.).
- **Responses** – In Flask session: key = `role_id|category_id|item_id`; value = `{ status, comment, ... }`. No DB; session-only (plus optional offline sync).
- **Patch data** (optional) – In Flask session: `patch_data` = `{ summary, files }` after uploading a git patch; used for code-first review (MR summary + diff viewer). No system Git required.

---

## Security and Config

- **Network** – `network_security` service validates each request (e.g. IP allowlist); config in `config/network_security.json`.
- **App config** – `app_config.json`: roles/categories (overlap with `roles.json`), review settings, UI, export, security, logging, features (PWA, offline, auto-launch browser, etc.).
- **Corporate** – See `docs/SECURITY_CORPORATE.md` for secrets, CORS, SSO (REMOTE_USER), audit logging, data retention. `docs/PRIVACY_NOTICE.md` for data handling.

---

## Checklist Pipeline

1. **Excel** (optional) – In `checklists/excel/<role>/`; columns like `MainCategory`/`Category`.
2. **Dynamic categories** – `dynamic_categories.update_all_configs()` scans Excel and updates `roles.json` (and related config) so roles know which categories/files to use.
3. **Markdown** – Per-role consolidated markdown in `checklists/markdown/<role>/*.md` (e.g. `self_consolidated.md`). Scripts can regenerate these from Excel.
4. **Runtime** – `checklist_loader.load_roles_config()` + `build_all_steps()` read `roles.json` and markdown, produce a flat list of steps; the app then groups them by category for the review UI.

---

## Bundled tools and code metrics (optional)

You can **pack git, cloc, and diffstat** in the project so patch metrics work without system installs:

- **`tools/git/`** – Portable Git (e.g. Git for Windows → `cmd/git.exe`). See `tools/git/README.md`. Used for exact file/line counts (GitLab-accurate).
- **`tools/cloc/`** – CLOC binary from [cloc releases](https://github.com/AlDanial/cloc/releases). See `tools/cloc/README.md`. Used for “Lines of code” by language.
- **`tools/diffstat/`** – diffstat binary (optional). See `tools/diffstat/README.md`. If missing, a pure-Python equivalent is used.

**Optional Python libs** (for extra metrics on the patch): `pip install -r requirements-optional.txt` (adds **pygount** for LOC and **radon** for Python complexity/maintainability).

**Download script:** `python scripts/download_metrics_tools.py` can fetch CLOC for Windows into `tools/cloc/`.

**Full list and future project-level tools** (Detekt, Android Lint, ktlint, PMD, Semgrep for repo + commit analysis): see **`docs/CODE_METRICS_AND_TOOLS.md`**.

## Build and Run

- **Run (dev)** – `python app.py --dev-server` (Flask dev server, debug on).
- **Run (default)** – `python app.py` uses Waitress if available.
- **Portable (recommended)** – `npm run build:win` produces fully bundled Windows artifacts in `dist-electron/`:
  - **CodeReview 1.0.0.exe** — single file, copy to target and run. No install, no admin.
  - **CodeReview-portable.zip** — unzip anywhere, run `CodeReview.exe`.
  - **win-unpacked/** — copy folder to target, run `CodeReview.exe`.
  Requires: Node.js, Python (build time only). Target machine needs nothing.

---

## Summary

CodeReview is a **session-based, role-driven code review checklist app**: config and checklists come from **JSON + Markdown (+ optional Excel)**, the **Flask app** serves the UI and API, **services** handle checklist loading and categories, and **network_security** enforces access rules. The same codebase supports **web**, **PWA/offline**, and **portable desktop** builds.
