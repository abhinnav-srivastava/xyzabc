# Corporate Security & Compliance

Checklist for deploying CodeReview in a corporate environment.

## Data Egress Policy

**Development machine:** Downloads OK (pip, npm, tools, CDN). No uploads.

**Built app (shared/deployed):** No downloads, no uploads. Fully self-contained.

When the app is built (PyInstaller/Electron), `data_egress` is **automatically enforced**:
- `block_external_resources` = true (HTML export inlines assets, strict CSP)
- `block_external_downloads` = true
- `block_git_remote` = true

For dev, set in `config/app_config.json` → `data_egress` (defaults false):

| Option | Dev default | Built app | Effect |
|--------|-------------|-----------|--------|
| `block_external_resources` | false | **always true** | HTML inlines CSS/fonts; no CDN. CSP blocks external. |
| `block_external_downloads` | false | **always true** | `download_metrics_tools.py` skips downloads. |
| `block_git_remote` | false | **always true** | Git pull/push/fetch blocked. |

Env overrides (dev only): `NO_EXTERNAL_DOWNLOADS=1`, `BLOCK_GIT_REMOTE=1`.

## 1. Secrets

- **Never use default secrets in production.**
- Set `FLASK_SECRET_KEY` via environment (from vault/secret store).
- Or set `config/app_config.json` → `security.session_secret_key`.
- When `FLASK_ENV=production`, the app will refuse to start with default secrets.

## 2. Cookies

- Set `security.secure_cookies: true` when running over HTTPS.
- `http_only_cookies` is `true` by default.

## 3. CORS

- Replace `allowed_origins: ["*"]` with specific origins, e.g.:
  ```json
  "allowed_origins": ["https://your-app.example.com", "http://127.0.0.1:5000"]
  ```
- For Electron desktop app, include `http://127.0.0.1:5000` and `http://localhost:5000`.

## 4. Auth (SSO / Reverse Proxy)

- Set `auth.use_remote_user: true` when using a reverse proxy that does SSO/LDAP.
- The proxy must set `REMOTE_USER` or `X-Forwarded-User` with the authenticated username.
- Example nginx:
  ```nginx
  proxy_set_header X-Forwarded-User $remote_user;
  ```

## 5. Data Retention

- Configure `data_retention.patch_retention_days` (default: 30).
- Run `python scripts/py/cleanup_data_retention.py` periodically (e.g. daily cron).
- See `docs/PRIVACY_NOTICE.md` for data handling.

## 6. Audit Logging

- Auth and review events are logged to `data/audit.jsonl` (JSON Lines).
- Events: `login`, `logout`, `select_roles`, `review_submit`, `patch_upload`, `profile_delete`.
- Rotate or archive per your retention policy.

## 7. Dependencies

- Run `python scripts/audit-deps.py` (requires `pip install pip-audit`).
- Or: `pip install pip-audit && pip-audit -r requirements.txt`
- Keep dependencies updated.
