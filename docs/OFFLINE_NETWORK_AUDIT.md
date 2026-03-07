# Offline / Network Usage Audit

Detailed audit of every area that uses internet or network in the app.

**Requirement:** The app must behave identically whether internet is connected or not. No external outbound requests. All traffic is localhost only. Same behavior when: internet connected at start, internet disconnected at start, or internet disconnected after start.

---

## 1. Frontend – CDN / External Resources

| Location | What | Network? | Fix for Offline |
|----------|------|----------|-----------------|
| **templates/base.html** | Bootstrap CSS, Bootstrap Icons, styles.css, app.js, pwa.js | **No** – uses `url_for('static', ...)` (local) | Already local ✓ |
| **templates/report_standalone.html** | Bootstrap CSS, Bootstrap Icons, Bootstrap JS | **Yes** – CDN when `block_external_resources` is false | Set `data_egress.block_external_resources: true` so HTML export inlines CSS/fonts |
| **checklists/markdown/guidelines/*.md** | Reference links (e.g. `https://developer.android.com/...`) | **No** – plain text, not fetched | N/A |

---

## 2. Frontend – JavaScript `fetch()` Calls

| Location | Endpoint | Network? | Notes |
|----------|----------|----------|-------|
| **templates/review_patch.html** | `/api/last-patch-selection` | Internal (Flask) | Same-origin ✓ |
| **templates/review_patch.html** | `/api/project/<id>/branches` | Internal | Same-origin ✓ |
| **templates/review_patch.html** | `/api/project/<id>/commits` | Internal | Same-origin ✓ |
| **templates/review_patch.html** | `/api/project/<id>/diff` | Internal | Same-origin ✓ |
| **templates/review_patch.html** | `/api/project/<id>/commit/<hash>/patch` | Internal | Same-origin ✓ |
| **static/js/app.js** | `/api/sync-data` | Internal | Route may not exist; would 404 |
| **static/js/pwa.js** | `/api/sync-offline-data` | Internal | Same-origin ✓ |
| **static/sw.js** | `fetch(request)` | Internal for same-origin | SW fetches from app server only |
| **static/sw.js** | `/api/sync-reviews` (in syncReviewData) | Internal | Same-origin ✓ |

All frontend fetches are to the same origin (Flask backend). No external API calls.

---

## 3. Backend – Python Network Usage

| Location | What | Network? | Fix for Offline |
|----------|------|----------|-----------------|
| **scripts/download_metrics_tools.py** | `urllib.request.urlretrieve()` – downloads CLOC from GitHub | **Yes** | Run once during setup; then `block_external_downloads: true` or skip. Tools live in `tools/cloc/`. |
| **services/git_operations.py** | `git pull`, `git push`, `git fetch` | **Yes** (when remote URL) | `block_git_remote: true` disables. For offline: use **local paths only** for projects. |
| **services/projects_service.py** | `_is_git_remote()` | No – just checks URL format | N/A |
| **app.py** | `webbrowser.open()` | No – opens localhost | N/A |
| **app.py** | `dynamic_categories`, `auto_update_checklists` | **No** – reads local Excel/Markdown | N/A |

---

## 4. Git Operations (When Used)

| Operation | Network? | When |
|-----------|----------|------|
| **git clone** | Yes | Adding project with remote URL – **disabled** (app only allows local paths) |
| **git pull** | Yes | If `block_git_remote` false and user triggers pull | Set `block_git_remote: true` |
| **git push** | Yes | Same as above | Set `block_git_remote: true` |
| **git fetch** | Yes | Same | Set `block_git_remote: true` |
| **git log, git diff, git show** | **No** | Local repo only | Works offline ✓ |
| **git apply --numstat** | **No** | Patch parsing | Works offline ✓ |

Projects are **local paths only** (remote URLs blocked in profile). Git is used only for local operations (commits, branches, diff) – no network.

---

## 5. Content Security Policy (CSP)

When `block_external_resources: true`:
- CSP header blocks external script/style/font/img/connect
- `connect-src 'self'` – no external API calls from frontend

---

## 6. Built App (PyInstaller / Electron)

When `sys.frozen` (built app), these are **automatically enforced**:
- `block_external_resources = True`
- `block_external_downloads = True`
- `block_git_remote = True`

So the portable build is already offline-ready.

---

## 7. Development Setup – One-Time Downloads

| Step | Network? | When |
|------|----------|------|
| `pip install -r requirements.txt` | Yes | Once during setup |
| `npm install` | Yes | Once (Electron build) |
| `python scripts/download_metrics_tools.py` | Yes | Once – fetches CLOC into `tools/cloc/` |
| Git, diffstat | Manual | Download once, put in `tools/git/`, `tools/diffstat/` |

---

## 8. Summary – Config for Offline-Only (Dev)

To run the app **offline-only** in development (after setup):

**Option A – Command-line flag (no config change):**
```bash
python app.py --offline
# or with dev server:
python app.py --dev-server --offline
```
The `--offline` flag enforces `block_external_resources`, `block_external_downloads`, and `block_git_remote` for that run.

**Option B – Config file** (`config/app_config.json`):
```json
"data_egress": {
  "block_external_resources": true,
  "block_external_downloads": true,
  "block_git_remote": true
}
```

| Setting | Effect |
|---------|--------|
| `block_external_resources` | HTML export inlines Bootstrap/Icons; CSP blocks CDN |
| `block_external_downloads` | `download_metrics_tools.py` skips GitHub fetch |
| `block_git_remote` | Git pull/push/fetch disabled |

---

## 9. Checklist for Offline-Only Setup

1. **One-time (with network):**
   - `pip install -r requirements.txt`
   - `npm install` (if using Electron)
   - `python scripts/download_metrics_tools.py` (CLOC)
   - Add Git, diffstat to `tools/` per `tools/*/README.md`
   - Bootstrap, Bootstrap Icons already in `static/vendor/` ✓

2. **Config:** Set `data_egress` as above in `config/app_config.json`, or use `--offline` flag when running

3. **Projects:** Use **local paths only** (e.g. `C:\repos\myproject`), not `https://gitlab.com/...`

4. **PWA:** Visit key pages once while online so the service worker caches them (or run app, then go offline)
