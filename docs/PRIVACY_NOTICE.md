# Privacy Notice — CodeReview

This document describes data collection, retention, and deletion for corporate compliance (GDPR, etc.).

## Data We Store

| Data | Location | Purpose |
|------|----------|---------|
| User profiles | `data/profiles.json` | Name, username, preferred roles |
| Patch content | `temp/patch_store/*.json` | Uploaded diff files for review |
| Audit log | `data/audit.jsonl` | Login, logout, role selection, review actions |
| Session | Server memory / cookie | Active review state |

## Retention

- **Patch store**: Configurable via `config/app_config.json` → `data_retention.patch_retention_days` (default: 30). Run `python scripts/py/cleanup_data_retention.py` to purge old files.
- **Profiles**: Stored until user deletes profile from Profile page.
- **Audit log**: Append-only; rotate or archive per your policy.

## Deletion

- **Profiles**: User can delete their profile from the Profile page.
- **Patch data**: Automatically removed when user clears patch or after retention period (run cleanup script).
- **Audit**: Retain per compliance requirements; implement rotation externally.

## Data Egress

- **Dev:** Downloads allowed (deps, tools). No uploads.
- **Built app:** No downloads, no uploads. Blocks auto-enabled when packaged.

## Corporate Deployment

For production:

1. Set `FLASK_SECRET_KEY` from a secure vault (never use defaults).
2. Set `security.secure_cookies: true` when using HTTPS.
3. Restrict `security.allowed_origins` (never use `*`).
4. Enable `auth.use_remote_user: true` for reverse-proxy SSO.
5. Schedule `cleanup_data_retention.py` (e.g. daily cron).
