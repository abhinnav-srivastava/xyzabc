import os
import sys
import io
import time
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_file,
    make_response,
)

\
try:
    from utils.path_utils import get_scripts_path, get_checklists_path, get_templates_path, get_project_root, get_temp_dir
except ImportError:
    \
    import sys
    def get_base_dir() -> str:
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            return sys._MEIPASS
        return os.path.dirname(__file__)
    def get_scripts_path(script_file: str = "") -> Path:
        base_path = Path(get_base_dir()) / "scripts"
        if script_file:
            return base_path / script_file
        return base_path

    def get_checklists_path(subpath: str = "") -> Path:
        base_path = Path(get_base_dir()) / "checklists"
        if subpath:
            return base_path / subpath
        return base_path

    def get_templates_path(template_file: str = "") -> Path:
        base_path = Path(get_base_dir()) / "templates"
        if template_file:
            return base_path / template_file
        return base_path

    def get_project_root() -> Path:
        return Path(get_base_dir())

    def get_temp_dir() -> Path:
        temp_dir = get_project_root() / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir

from services.checklist_loader import (
    load_roles_config,
    build_all_steps,
)
from services.user_profile import (
    get_last_used_name,
    get_last_used_user_id,
    get_last_patch_selection,
    get_profile,
    save_profile,
    get_all_profiles,
    set_last_used,
    update_last_patch_selection,
    update_profile_roles,
)
from services.network_security import network_security
from services.audit_log import audit_log
from services.user_activity_log import (
    log_app_open,
    log_login,
    log_logout,
    log_review_completed,
    log_review_started,
)
from services.dynamic_categories import dynamic_categories
from services.patch_parser import (
    parse_patch,
    file_diffs_to_json_serializable,
    file_diffs_from_session,
)
from services.git_operations import (
    git_pull,
    git_push,
    get_commits,
    get_branches,
    get_commit_patch,
    get_diff_between_branches,
    get_credential_helper_info,
)
from services.projects_service import (
    get_projects,
    get_project as get_user_project,
    add_project as add_user_project,
    remove_project as remove_user_project,
)
from services.project_index_service import (
    get_project_index,
    get_project_summary,
    schedule_index_build,
    invalidate_index,
    build_source_hierarchy,
)
from services.access_tokens_service import (
    get_tokens as get_user_tokens,
    add_token as add_user_token,
    remove_token as remove_user_token,
)

def create_app() -> Flask:
    app = Flask(__name__)

    config_path = Path(__file__).parent / "config" / "app_config.json"
    app_config = {}
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            app_config = json.load(f)

    # Built app (frozen): no downloads, no uploads. Dev: downloads ok (deps, CDN), no uploads.
    is_frozen = getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")
    if is_frozen:
        app_config.setdefault("data_egress", {})
        app_config["data_egress"]["block_external_resources"] = True
        app_config["data_egress"]["block_external_downloads"] = True
        app_config["data_egress"]["block_git_remote"] = True

    # Secrets: env overrides config; reject defaults in production server (not portable/Electron)
    sec = app_config.get("security", {})
    secret = os.environ.get("FLASK_SECRET_KEY") or sec.get("session_secret_key") or "dev-secret-key"
    is_production_server = (
        os.environ.get("FLASK_ENV") == "production"
        and not (getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"))
    )
    if is_production_server and secret in ("dev-secret-key", "dev-secret-key-change-in-production"):
        raise RuntimeError(
            "Production server requires FLASK_SECRET_KEY (env) or security.session_secret_key in config. "
            "Do not use default secrets. Use a vault or secure secret store."
        )
    app.secret_key = secret
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=365)

    # Cookies: secure when over HTTPS
    app.config["SESSION_COOKIE_SECURE"] = sec.get("secure_cookies", False)
    app.config["SESSION_COOKIE_HTTPONLY"] = sec.get("http_only_cookies", True)
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    @app.context_processor
    def inject_config():
        return {'app_config': app_config}

    def debug_log(message):
        if app_config.get('features', {}).get('debug_logging', False):
            print(message)

    try:
        import subprocess

        is_portable = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
        auto_update_enabled = app_config.get('features', {}).get('auto_update', True)
        env_disabled = os.environ.get('AUTO_UPDATE_CHECKLISTS', '').lower() == 'false'

        if is_portable:
            pass
        elif auto_update_enabled and not env_disabled:
            \
            pass
            try:
                dynamic_categories.update_all_configs()
                pass
            except Exception as e:
                pass

            script_path = get_scripts_path("py/auto_update_checklists_category.py")
            if script_path.exists():
                pass
                result = subprocess.run([sys.executable, str(script_path)],
                                      capture_output=True, text=True, cwd=get_project_root())
                if result.returncode == 0:
                    pass
                    if result.stdout:
                        pass
                else:
                    pass
                    if result.stdout:
                        pass
            else:
                pass
    except Exception as e:
        pass

    @app.before_request
    def redirect_localhost_to_127():
        """Redirect localhost to 127.0.0.1 so app works when WiFi is off (localhost may not resolve)."""
        host = request.environ.get("HTTP_HOST", "")
        if host and host.startswith("localhost"):
            url = request.url.replace("localhost", "127.0.0.1", 1)
            return redirect(url, code=301)

    @app.before_request
    def check_remote_user():
        """Corporate: trust REMOTE_USER from reverse proxy (SSO/LDAP)."""
        auth_cfg = app_config.get("auth", {})
        if not auth_cfg.get("use_remote_user"):
            return None
        remote = request.environ.get("REMOTE_USER") or request.environ.get("HTTP_X_FORWARDED_USER")
        if remote and not session.get("user_name"):
            session.permanent = True
            session["user_name"] = remote
            session["user_username"] = remote
            profile = get_profile(remote)
            if profile and profile.get("preferred_roles"):
                session["user_roles"] = profile["preferred_roles"]
            else:
                session["user_roles"] = []
                save_profile(user_id=remote, name=remote, preferred_roles=[])

    @app.before_request
    def require_login():
        """Redirect to login if not authenticated. Landing (index) and login are public."""
        if request.endpoint in (None, "static", "manifest", "service_worker", "offline"):
            return None
        if request.endpoint in ("index", "login", "logout", "select_roles"):
            return None
        if session.get("user_name"):
            return None
        return redirect(url_for("login", next=request.url))

    @app.before_request
    def require_roles_if_logged_in():
        """If user is logged in but has no roles, redirect to select_roles (first-time flow)."""
        if request.endpoint in (None, "static", "manifest", "service_worker", "offline", "login", "logout", "index", "select_roles"):
            return None
        if session.get("user_name") and not session.get("user_roles"):
            return redirect(url_for("select_roles", next=request.url))
        return None

    @app.before_request
    def validate_request():
        """Validate incoming requests for security"""
        client_ip = request.environ.get('REMOTE_ADDR', '127.0.0.1')
        is_allowed, reason = network_security.validate_request(client_ip)

        if not is_allowed:
            return f"Access denied: {reason}", 403

    @app.before_request
    def log_app_open_once():
        """Log app open once per session when user hits index or dashboard."""
        if request.endpoint in ("index", "dashboard") and not session.get("_user_activity_app_open_logged"):
            session["_user_activity_app_open_logged"] = True
            log_app_open(
                user_id=session.get("user_username", ""),
                user_name=session.get("user_name", ""),
            )

    @app.after_request
    def add_security_headers(response):
        """CORS and Content-Security-Policy. When block_external_resources, prevent external fetches."""
        origins = sec.get("allowed_origins") or []
        if origins:
            if "*" in origins:
                response.headers["Access-Control-Allow-Origin"] = "*"
            else:
                origin = request.environ.get("HTTP_ORIGIN")
                if origin and origin in origins:
                    response.headers["Access-Control-Allow-Origin"] = origin
        if app_config.get("data_egress", {}).get("block_external_resources"):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; font-src 'self' data:; connect-src 'self'; frame-ancestors 'none'"
            )
        return response

    def _get_steps() -> List[Dict[str, Any]]:
        config = load_roles_config()
        all_steps = build_all_steps(config)

        \
        if not all_steps:
            \
            is_portable = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
            if is_portable:
                pass
            else:
                debug_log("No steps found, attempting to auto-refresh from Excel files...")
                try:
                    \
                    from services.dynamic_categories import dynamic_categories
                    import subprocess
                    import sys

                    \
                    dynamic_categories.update_all_configs()

                    \
                    script_path = get_scripts_path("py/auto_update_checklists_category.py")
                    if script_path.exists():
                        result = subprocess.run([sys.executable, str(script_path)],
                                              capture_output=True, text=True, cwd=get_project_root())
                        if result.returncode == 0:
                            debug_log("Auto-refresh successful, reloading config...")
                            \
                            config = load_roles_config()
                            all_steps = build_all_steps(config)
                        else:
                            debug_log(f"Auto-refresh failed: {result.stderr}")
                except Exception as e:
                    debug_log(f"Auto-refresh error: {str(e)}")

        selected_roles = session.get("selected_roles") or session.get("selected_role")
        if isinstance(selected_roles, str):
            selected_roles = [selected_roles] if selected_roles else []
        if selected_roles:
            steps = [step for step in all_steps if step["role_id"] in selected_roles]
        else:
            steps = all_steps

        return steps

    def _process_review_form_data(responses: Dict[str, Dict[str, Any]], form_data: dict) -> Dict[str, Dict[str, Any]]:
        """
        Process review form data. Returns updated responses dictionary.
        Handles status/comment per item and category skip.
        """
        debug_log("DEBUG: _process_review_form_data called")
        skip_enabled = app_config.get('features', {}).get('skip_categories', True)

        # Clear skipped for categories not marked as skipped in form
        if skip_enabled:
            for cat in _get_categories():
                cid = cat["category_id"]
                if form_data.get(f"category_skip_{cid}") != "on":
                    if cid in responses:
                        responses[cid]["skipped"] = False
                    else:
                        responses[cid] = {"skipped": False}

        for key, value in form_data.items():
            if key.startswith("status_"):
                item_key = key[7:]
                if item_key not in responses:
                    responses[item_key] = {}
                responses[item_key]["status"] = value
            elif key.startswith("comment_"):
                item_key = key[8:]
                if item_key not in responses:
                    responses[item_key] = {}
                responses[item_key]["comment"] = value
            elif skip_enabled and key.startswith("category_skip_") and not key.endswith("_status"):
                category_id = key[14:]
                skip_comment = form_data.get(f"category_skip_comment_{category_id}", "")
                if value == "on":
                    if category_id not in responses:
                        responses[category_id] = {}
                    responses[category_id]["skipped"] = True
                    responses[category_id]["skip_comment"] = skip_comment

        debug_log("DEBUG: Final responses after processing: " + str(list(responses.keys())))
        return responses

    def _get_categories() -> List[Dict[str, Any]]:
        """Group steps by category for category-based review"""
        steps = _get_steps()

        \
        if not steps:
            debug_log("No steps found in _get_categories, attempting auto-refresh...")
            \
            return []

        categories = {}

        for step in steps:
            \
            cat_key = f"{step['role_id']}|{step['category_name']}"
            if cat_key not in categories:
                \
                consistent_category_id = step['category_name'].lower().replace(' ', '_').replace('-', '_')
                categories[cat_key] = {
                    "role_id": step["role_id"],
                    "role_name": step["role_name"],
                    "category_id": consistent_category_id,
                    "category_name": step["category_name"],
                    "item_list": []
                }
            guideline_info = _get_guideline_info_for_checklist_item(step)
            step["guideline_category"] = guideline_info["category"]
            categories[cat_key]["item_list"].append(step)

        return list(categories.values())

    def _calculate_review_time() -> Dict[str, Any]:
        """Calculate review timing information."""
        debug_log("DEBUG: _calculate_review_time called")
        debug_log("DEBUG: Session keys: " + str(list(session.keys())))
        debug_log("DEBUG: review_completed: " + str(session.get("review_completed")))
        debug_log("DEBUG: review_start_time: " + str(session.get("review_start_time")))

        if session.get("review_completed"):
            debug_log("DEBUG: Review is completed, checking stored timing")
            start_time_str = session.get("review_start_time", "Unknown")
            end_time_str = session.get("review_end_time", "Unknown")
            duration_str = session.get("review_duration", "Unknown")
            duration_seconds = session.get("review_duration_seconds", 0)

            \
            if end_time_str == "Unknown" or duration_str == "Unknown":
                debug_log("DEBUG: Stored timing is Unknown, recalculating...")
                if start_time_str != "Unknown":
                    try:
                        start_time = datetime.fromisoformat(start_time_str)
                        end_time = datetime.now()
                        duration = end_time - start_time

                        \
                        total_seconds = int(duration.total_seconds())
                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60
                        seconds = total_seconds % 60

                        if hours > 0:
                            duration_str = f"{hours}h {minutes}m {seconds}s"
                        elif minutes > 0:
                            duration_str = f"{minutes}m {seconds}s"
                        else:
                            duration_str = f"{seconds}s"

                        session["review_end_time"] = end_time.strftime("%Y-%m-%d %H:%M:%S")
                        session["review_duration"] = duration_str
                        session["review_duration_seconds"] = total_seconds

                        debug_log("DEBUG: Timing recalculated and stored")
                    except Exception as e:
                        debug_log(f"DEBUG: Error recalculating timing: {e}")
                        end_time_str = "Unknown"
                        duration_str = "Unknown"
                        duration_seconds = 0

            if start_time_str != "Unknown":
                try:
                    start_time = datetime.fromisoformat(start_time_str)
                    start_time_formatted = start_time.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    start_time_formatted = start_time_str
            else:
                start_time_formatted = "Unknown"

            return {
                "start_time": start_time_formatted,
                "end_time": session.get("review_end_time", "Unknown"),
                "duration": session.get("review_duration", "Unknown"),
                "duration_seconds": session.get("review_duration_seconds", 0)
            }

        start_time_str = session.get("review_start_time")
        start_timestamp = session.get("review_start_timestamp")

        if not start_time_str or not start_timestamp:
            debug_log("DEBUG: No start time found, returning Unknown")
            return {
                "start_time": "Unknown",
                "end_time": "Unknown",
                "duration": "Unknown",
                "duration_seconds": 0
            }

        debug_log("DEBUG: Calculating timing from start time: " + str(start_time_str))
        start_time = datetime.fromisoformat(start_time_str)
        end_time = datetime.now()
        duration = end_time - start_time

        \
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            duration_str = f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            duration_str = f"{minutes}m {seconds}s"
        else:
            duration_str = f"{seconds}s"

        debug_log("DEBUG: Calculated timing: " + str({
            "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": duration_str,
            "duration_seconds": total_seconds
        }))

        return {
            "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": duration_str,
            "duration_seconds": total_seconds
        }

    def _compute_summary(steps: List[Dict[str, Any]], responses: Dict[str, Dict[str, Any]]):
        summary: Dict[str, Any] = {}

        \
        skip_enabled = app_config.get('features', {}).get('skip_categories', True)
        debug_log("DEBUG: Skip feature enabled in summary: " + str(skip_enabled))

        if skip_enabled:
            counts_overall = {"OK": 0, "NG": 0, "NA": 0, "UNANSWERED": 0, "SKIPPED": 0}
        else:
            counts_overall = {"OK": 0, "NG": 0, "NA": 0, "UNANSWERED": 0}

        for step in steps:
            key = f"{step['role_id']}|{step['category_id']}|{step['item_id']}"
            role_id = step["role_id"]
            cat_id = step["category_id"]

            role_bucket = summary.setdefault(role_id, {
                "role_name": step["role_name"],
                "categories": {},
            })

            if skip_enabled:
                cat_bucket = role_bucket["categories"].setdefault(cat_id, {
                    "category_name": step["category_name"],
                    "item_list": [],
                    "counts": {"OK": 0, "NG": 0, "NA": 0, "UNANSWERED": 0, "SKIPPED": 0},
                })
            else:
                cat_bucket = role_bucket["categories"].setdefault(cat_id, {
                    "category_name": step["category_name"],
                    "item_list": [],
                    "counts": {"OK": 0, "NG": 0, "NA": 0, "UNANSWERED": 0},
                })

            record = {
                "item_text": step["item_text"],
                "response": None,
                "comment": "",
            }

            \
            if skip_enabled and cat_id in responses and "skipped" in responses[cat_id]:
                \
                record["response"] = "SKIPPED"
                record["comment"] = responses[cat_id].get("skip_comment", "")
                cat_bucket["counts"]["SKIPPED"] += 1
                counts_overall["SKIPPED"] += 1
            elif key in responses:
                \
                if "status" in responses[key]:
                    record["response"] = responses[key]["status"]
                    record["comment"] = responses[key].get("comment", "")
                    cat_bucket["counts"][record["response"]] += 1
                    counts_overall[record["response"]] += 1
                else:
                    record["response"] = "UNANSWERED"
                    cat_bucket["counts"]["UNANSWERED"] += 1
                    counts_overall["UNANSWERED"] += 1
            else:
                record["response"] = "UNANSWERED"
                cat_bucket["counts"]["UNANSWERED"] += 1
                counts_overall["UNANSWERED"] += 1

            cat_bucket["item_list"].append(record)
        return summary, counts_overall

    @app.route("/login", methods=["GET", "POST"])
    def login():
        """Login page: name and username. No password. First-time users go to select_roles."""
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            username = request.form.get("username", "").strip()
            if name and username:
                session.permanent = True
                session["user_name"] = name
                session["user_username"] = username
                profile = get_profile(username)
                if profile and profile.get("preferred_roles"):
                    session["user_roles"] = profile["preferred_roles"]
                    save_profile(user_id=username, name=name, preferred_roles=profile["preferred_roles"])
                    audit_log("login", user_id=username, user_name=name, roles=profile["preferred_roles"],
                              ip=request.environ.get("REMOTE_ADDR"))
                    log_login(user_id=username, user_name=name, roles=profile["preferred_roles"])
                    next_url = request.args.get("next") or url_for("dashboard")
                    return redirect(next_url)
                else:
                    save_profile(user_id=username, name=name, preferred_roles=[])
                    audit_log("login", user_id=username, user_name=name, roles=[],
                              ip=request.environ.get("REMOTE_ADDR"))
                    log_login(user_id=username, user_name=name, roles=[])
                    next_url = request.args.get("next") or url_for("dashboard")
                    return redirect(url_for("select_roles", next=next_url))
        if session.get("user_name") and session.get("user_roles"):
            next_url = request.args.get("next") or url_for("dashboard")
            return redirect(next_url)
        if session.get("user_name") and not session.get("user_roles"):
            return redirect(url_for("select_roles", next=request.args.get("next") or url_for("dashboard")))
        config = load_roles_config()
        profiles = get_all_profiles()
        last_used_id = get_last_used_user_id()
        last_profile = get_profile(last_used_id) if last_used_id else None
        return render_template(
            "login.html",
            config=config,
            profiles=profiles,
            last_profile=last_profile,
        )

    @app.route("/select-roles", methods=["GET", "POST"])
    def select_roles():
        """First-time role selection: chip-based UI. Requires user_name from login."""
        if not session.get("user_name") or not session.get("user_username"):
            return redirect(url_for("login", next=url_for("select_roles")))
        if request.method == "POST":
            roles = request.form.getlist("roles")
            roles = [r.strip() for r in roles if r and r.strip()]
            if roles:
                username = session.get("user_username", "")
                name = session.get("user_name", "")
                session["user_roles"] = roles
                save_profile(user_id=username, name=name, preferred_roles=roles)
                audit_log("select_roles", user_id=username, user_name=name, roles=roles,
                          ip=request.environ.get("REMOTE_ADDR"))
                next_url = request.args.get("next") or url_for("dashboard")
                return redirect(next_url)
        if session.get("user_roles"):
            next_url = request.args.get("next") or url_for("dashboard")
            return redirect(next_url)
        config = load_roles_config()
        return render_template("select_roles.html", config=config)

    @app.route("/logout")
    def logout():
        """Clear session and redirect to landing page."""
        user_id = session.get("user_username")
        user_name = session.get("user_name")
        audit_log("logout", user_id=user_id, user_name=user_name, ip=request.environ.get("REMOTE_ADDR"))
        log_logout(user_id=user_id or "", user_name=user_name or "")
        session.clear()
        return redirect(url_for("index"))

    @app.route("/")
    def index():
        if session.get("user_name"):
            return redirect(url_for("dashboard"))
        config = load_roles_config()
        return render_template("index.html", config=config)

    def _format_roles_display(role_ids: List[str], role_map: Dict[str, str]) -> str:
        """Format role IDs as display string (e.g. 'FO, Developer Review')."""
        if isinstance(role_ids, str):
            role_ids = [role_ids] if role_ids else []
        names = [role_map.get(r, r) for r in role_ids if r]
        return ", ".join(names) if names else "—"

    @app.route("/dashboard")
    def dashboard():
        """Simple dashboard for logged-in users."""
        if not session.get("user_name"):
            return redirect(url_for("login", next=url_for("dashboard")))
        config = load_roles_config()
        role_map = {r["id"]: r["name"] for r in config.get("roles", [])}
        user_roles = session.get("user_roles", []) or ([session.get("user_role")] if session.get("user_role") else [])
        role_name = _format_roles_display(user_roles, role_map)
        user_id = session.get("user_username") or session.get("reviewer_username") or ""
        if not user_id:
            from services.user_profile import get_profile_by_name, get_last_used_user_id
            profile = get_profile_by_name(session.get("user_name", ""))
            if profile:
                user_id = profile.get("user_id") or profile.get("username") or ""
            if not user_id:
                user_id = get_last_used_user_id() or ""
        projects = get_projects(user_id) or []
        project_summaries = []
        for p in projects:
            proj_id = p.get("id", "")
            proj_path = p.get("url_or_path", "")
            summary = get_project_summary(proj_id, proj_path) if proj_id and proj_path else None
            project_summaries.append({
                "id": proj_id,
                "name": p.get("name", ""),
                "type": p.get("type", "local"),
                "summary": summary,
            })
        return render_template(
            "dashboard.html",
            role_name=role_name,
            project_summaries=project_summaries,
        )

    def _resolve_user_id():
        """Resolve user_id from session (for project routes)."""
        user_id = session.get("user_username") or session.get("reviewer_username") or ""
        if not user_id:
            from services.user_profile import get_profile_by_name, get_last_used_user_id
            profile = get_profile_by_name(session.get("user_name", ""))
            if profile:
                user_id = profile.get("user_id") or profile.get("username") or ""
            if not user_id:
                user_id = get_last_used_user_id() or ""
        return user_id

    @app.route("/project/<project_id>")
    def project_details(project_id: str):
        """Project details page: file tree, classes, methods, test cases."""
        if not session.get("user_name"):
            return redirect(url_for("login", next=url_for("project_details", project_id=project_id)))
        user_id = _resolve_user_id()
        if not user_id:
            from flask import flash
            flash("Session expired. Please sign in again.", "warning")
            return redirect(url_for("login", next=url_for("project_details", project_id=project_id)))
        project = get_user_project(user_id, project_id)
        if not project:
            from flask import flash
            flash("Project not found.", "warning")
            return redirect(url_for("dashboard"))
        url_or_path = project.get("url_or_path", "")
        proj_type = project.get("type", "local")
        force = request.args.get("refresh", "").lower() in ("1", "true", "yes")
        index = get_project_index(project_id, url_or_path, force_rebuild=force) if proj_type == "local" and url_or_path else None
        files_by_type = {}
        stats = {"classes": 0, "methods": 0, "test_cases": 0}
        if index and index.get("files"):
            for f in index["files"]:
                ft = f.get("type", "other")
                files_by_type.setdefault(ft, []).append(f)
                stats["classes"] += len(f.get("classes", []))
                stats["methods"] += len(f.get("methods", []))
                stats["test_cases"] += len(f.get("test_cases", []))
        return render_template(
            "project_details.html",
            project=project,
            index=index,
            files_by_type=files_by_type,
            stats=stats,
        )

    @app.route("/profile", methods=["GET", "POST"])
    def profile_page():
        """Profile management: view, set default, edit roles, credentials, projects."""
        if not session.get("user_name") or not session.get("user_username"):
            return redirect(url_for("login", next=url_for("profile_page")))
        current_user_id = session.get("user_username")
        if request.method == "POST":
            action = request.form.get("action")
            user_id = request.form.get("user_id", "").strip()
            if user_id and user_id != current_user_id and action not in ("add_project", "add_token", "remove_token"):
                from flask import flash
                flash("You can only modify your own profile.", "warning")
                return redirect(url_for("profile_page"))
            if action == "set_default" and user_id:
                if set_last_used(user_id):
                    from flask import flash
                    p = get_profile(user_id)
                    display_name = p.get("name", user_id) if p else user_id
                    flash(f"'{display_name}' is now your default profile.", "success")
            elif action == "edit_roles" and user_id:
                roles = request.form.getlist("roles")
                roles = [r.strip() for r in roles if r and r.strip()]
                if roles and update_profile_roles(user_id, roles):
                    from flask import flash
                    flash("Roles updated.", "success")
                    session["user_roles"] = roles
            elif action == "add_project":
                name = request.form.get("project_name", "").strip()
                url_or_path = request.form.get("project_url_or_path", "").strip()
                is_remote_url = url_or_path.startswith(("https://", "http://", "git@", "ssh://"))
                if is_remote_url:
                    from flask import flash
                    flash("Only local paths are supported. Remote git URLs are not allowed.", "warning")
                elif url_or_path:
                    proj = add_user_project(current_user_id, name, url_or_path, "local")
                    if proj:
                        from flask import flash
                        flash(f"Project '{proj.get('name', '')}' added.", "success")
                        schedule_index_build(proj["id"], url_or_path)
                    else:
                        from flask import flash
                        flash("Invalid project. Provide a valid local path.", "warning")
                else:
                    from flask import flash
                    flash("Please enter a local path.", "warning")
            elif action == "remove_project":
                project_id = request.form.get("project_id", "").strip()
                if project_id and remove_user_project(current_user_id, project_id):
                    invalidate_index(project_id)
                    from flask import flash
                    flash("Project removed.", "info")
            elif action == "add_token":
                token_name = request.form.get("token_name", "").strip()
                token_host = request.form.get("token_host", "").strip()
                token_value = request.form.get("token_value", "").strip()
                if token_host and token_value:
                    tok = add_user_token(current_user_id, token_name, token_host, token_value)
                    if tok:
                        from flask import flash
                        flash(f"Access token for {tok.get('host', '')} added.", "success")
                    else:
                        from flask import flash
                        flash("Invalid token. Provide host (e.g. gitlab.com) and token.", "warning")
                else:
                    from flask import flash
                    flash("Please enter host and token.", "warning")
            elif action == "remove_token":
                token_id = request.form.get("token_id", "").strip()
                if token_id and remove_user_token(current_user_id, token_id):
                    from flask import flash
                    flash("Access token removed.", "info")
            return redirect(url_for("profile_page"))
        profile = get_profile(current_user_id)
        if not profile:
            profile = {
                "user_id": current_user_id,
                "name": session.get("user_name", current_user_id),
                "username": current_user_id,
                "preferred_roles": session.get("user_roles", []),
                "last_used": "",
            }
        profiles = [profile]
        last_used_id = get_last_used_user_id()
        config = load_roles_config()
        role_map = {r["id"]: r["name"] for r in config.get("roles", [])}
        credentials_info = get_credential_helper_info()
        projects = get_projects(current_user_id)
        access_tokens = get_user_tokens(current_user_id)
        return render_template(
            "profile.html",
            profiles=profiles,
            last_used_id=last_used_id,
            role_map=role_map,
            config=config,
            credentials_info=credentials_info,
            projects=projects,
            access_tokens=access_tokens,
        )

    @app.route("/guidelines")
    def guidelines():
        """Display Android coding guidelines with filtering capabilities"""
        \
        guidelines_file = "checklists/markdown/guidelines/android_coding_guidelines.md"

        if not os.path.exists(guidelines_file):
            return render_template("empty.html", message="Guidelines file not found")

        with open(guidelines_file, 'r', encoding='utf-8') as f:
            content = f.read()

        guidelines_data = _parse_guidelines_markdown(content)

        \
        category_filter = request.args.get('category', '')
        subcategory_filter = request.args.get('subcategory', '')

        \
        filtered_guidelines = guidelines_data
        if category_filter:
            filtered_guidelines = [g for g in filtered_guidelines if g['category'].lower() == category_filter.lower()]
        if subcategory_filter:
            filtered_guidelines = [g for g in filtered_guidelines if g['subcategory'].lower() == subcategory_filter.lower()]

        categories = sorted(list(set([g['category'] for g in guidelines_data])))
        subcategories = sorted(list(set([g['subcategory'] for g in guidelines_data])))

        return render_template("guidelines.html",
                             guidelines=filtered_guidelines,
                             all_guidelines=guidelines_data,
                             categories=categories,
                             subcategories=subcategories,
                             selected_category=category_filter,
                             selected_subcategory=subcategory_filter)

    @app.route("/guideline/<rule_id>")
    def individual_guideline(rule_id: str):
        """Display a specific guideline by Rule ID"""
        \
        guidelines_file = "checklists/markdown/guidelines/android_coding_guidelines.md"

        if not os.path.exists(guidelines_file):
            return render_template("empty.html", message="Guidelines file not found")

        with open(guidelines_file, 'r', encoding='utf-8') as f:
            content = f.read()

        guidelines_data = _parse_guidelines_markdown(content)

        \
        target_guideline = None
        for guideline in guidelines_data:
            if guideline['rule_id'].upper() == rule_id.upper():
                target_guideline = guideline
                break

        if not target_guideline:
            return render_template("empty.html", message=f"Guideline {rule_id} not found")

        categories = sorted(list(set([g['category'] for g in guidelines_data])))

        return render_template("individual_guideline.html",
                             guideline=target_guideline,
                             categories=categories)

    @app.route("/refresh-categories")
    def refresh_categories():
        """Refresh dynamic categories from Excel files"""
        try:
            success = dynamic_categories.update_all_configs()
            if success:
                return {"status": "success", "message": "Dynamic categories and roles updated successfully"}, 200
            else:
                return {"status": "error", "message": "Failed to update dynamic categories and roles"}, 500
        except Exception as e:
            return {"status": "error", "message": f"Error updating categories and roles: {str(e)}"}, 500

    @app.route("/refresh-all")
    def refresh_all():
        """Refresh everything: categories, checklists, and markdown files"""
        try:
            import subprocess
            import sys
            import os

            \
            debug_log("Refreshing dynamic categories...")
            categories_success = dynamic_categories.update_all_configs()

            \
            debug_log("Refreshing checklists with category-based conversion...")
            script_path = get_scripts_path("py/auto_update_checklists_category.py")

            if script_path.exists():
                result = subprocess.run([sys.executable, str(script_path)],
                                      capture_output=True, text=True, cwd=get_project_root())

                if result.returncode == 0:
                    return {
                        "status": "success",
                        "message": "Everything refreshed successfully",
                        "categories_updated": categories_success,
                        "checklists_updated": True,
                        "output": result.stdout
                    }, 200
                else:
                    return {
                        "status": "error",
                        "message": "Failed to refresh checklists",
                        "categories_updated": categories_success,
                        "checklists_updated": False,
                        "output": result.stdout,
                        "error": result.stderr
                    }, 500
            else:
                return {
                    "status": "error",
                    "message": "Auto-update script not found",
                    "categories_updated": categories_success,
                    "checklists_updated": False
                }, 500

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error refreshing everything: {str(e)}"
            }, 500

    @app.route("/refresh")
    def refresh_checklists():
        """Refresh checklists by running the auto-update script"""
        try:
            import subprocess
            import sys
            import os

            \
            script_path = get_scripts_path("py/auto_update_checklists.py")

            \
            result = subprocess.run([sys.executable, str(script_path)],
                                  capture_output=True, text=True, cwd=get_project_root())

            if result.returncode == 0:
                \
                try:
                    dynamic_categories.update_all_configs()
                except Exception as e:
                    debug_log(f"Warning: Dynamic categories update failed: {e}")

                from services.checklist_loader import load_roles_config

                \
                return {
                    "status": "success",
                    "message": "Checklists and categories refreshed successfully",
                    "output": result.stdout
                }, 200
            else:
                return {
                    "status": "error",
                    "message": "Failed to refresh checklists",
                    "output": result.stdout,
                    "error": result.stderr
                }, 500

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error refreshing checklists: {str(e)}"
            }, 500

    def _get_category_mapping() -> Dict[str, str]:
        """Map checklist categories to guideline categories"""
        return {
            "architecture": "Architecture",
            "design": "Architecture",
            "correctness": "Error Handling",
            "readability": "Style",
            "tests": "Testing",
            "functionality": "Logic",
            "style": "CodeStyle",
            "ops": "Performance"
        }

    def _get_guideline_info_for_checklist_item(item: Dict[str, Any]) -> Dict[str, str]:
        """Get the appropriate guideline category and suggested rule ID for a checklist item"""
        category_mapping = _get_category_mapping()
        category_id = item.get("category_id", "").lower()
        item_text = item.get("item_text", "").lower()

        \
        if category_id in category_mapping:
            category = category_mapping[category_id]
        else:
            \
            if any(keyword in item_text for keyword in ["error", "exception", "try", "catch", "fail"]):
                category = "Error Handling"
            elif any(keyword in item_text for keyword in ["test", "unit", "integration", "mock"]):
                category = "Testing"
            elif any(keyword in item_text for keyword in ["style", "format", "naming", "code"]):
                category = "CodeStyle"
            elif any(keyword in item_text for keyword in ["performance", "memory", "speed", "optimize"]):
                category = "Performance"
            elif any(keyword in item_text for keyword in ["security", "auth", "permission", "encrypt"]):
                category = "Security"
            elif any(keyword in item_text for keyword in ["ui", "ux", "interface", "user"]):
                category = "UI/UX"
            elif any(keyword in item_text for keyword in ["api", "network", "http", "retrofit"]):
                category = "API Usage"
            elif any(keyword in item_text for keyword in ["thread", "async", "coroutine", "background"]):
                category = "Threading"
            elif any(keyword in item_text for keyword in ["log", "debug", "trace"]):
                category = "Logging"
            elif any(keyword in item_text for keyword in ["mvvm", "repository", "pattern", "architecture"]):
                category = "Architecture"
            elif any(keyword in item_text for keyword in ["di", "inject", "dependency", "hilt"]):
                category = "DI"
            elif any(keyword in item_text for keyword in ["storage", "database", "room", "preference"]):
                category = "Storage"
            elif any(keyword in item_text for keyword in ["git", "commit", "branch", "merge"]):
                category = "Git"
            else:
                category = "Style"
        return {
            "category": category
        }

    def _get_guideline_category_for_checklist_item(item: Dict[str, Any]) -> str:
        """Get the appropriate guideline category for a checklist item (backward compatibility)"""
        return _get_guideline_info_for_checklist_item(item)["category"]

    def _parse_guidelines_markdown(content: str) -> List[Dict[str, Any]]:
        """Parse the guidelines markdown file to extract structured data"""
        guidelines = []
        lines = content.split('\n')

        current_category = ""
        current_subcategory = ""
        current_guideline = {}

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            \
            if line.startswith('## ') and not line.startswith('### '):
                current_category = line[3:].strip()
                current_subcategory = ""

            elif line.startswith('### '):
                current_subcategory = line[4:].strip()

            elif line.startswith('**AND-') and '**' in line:
                \
                if current_guideline:
                    guidelines.append(current_guideline)

                import re
                match = re.match(r'\*\*(AND-\d+)\*\* \((MUST|GOOD|MAY)\): (.+)', line)
                if match:
                    rule_id = match.group(1)
                    severity = match.group(2)
                    description = match.group(3)

                    current_guideline = {
                        'rule_id': rule_id,
                        'category': current_category,
                        'subcategory': current_subcategory,
                        'description': description,
                        'severity': severity,
                        'good_example': '',
                        'bad_example': '',
                        'measurement_reference': '',
                        'external_refs': ''
                    }

            elif current_guideline:
                if line.startswith('  - **Good Example:**'):
                    \
                    pass
                elif line.startswith('  - **Bad Example:**'):
                    \
                    pass
                elif line.startswith('  - **Measurement:**'):
                    current_guideline['measurement_reference'] = line[18:].strip()
                elif line.startswith('  - **Reference:**'):
                    current_guideline['external_refs'] = line[16:].strip()
                elif line.startswith('```kotlin'):
                    i += 1
                    example_content = []
                    while i < len(lines) and not lines[i].strip().startswith('```'):
                        example_content.append(lines[i])
                        i += 1

                    j = i - len(example_content) - 2
                    while j >= 0 and j < len(lines):
                        if '**Good Example:**' in lines[j]:
                            current_guideline['good_example'] = '\n'.join(example_content).strip()
                            break
                        elif '**Bad Example:**' in lines[j]:
                            current_guideline['bad_example'] = '\n'.join(example_content).strip()
                            break
                        j -= 1

            i += 1

        if current_guideline:
            guidelines.append(current_guideline)

        return guidelines

    @app.route("/start", methods=["GET", "POST"])
    def start_review():
        if request.method == "GET":
            reviewer_name = session.get("user_name", "").strip()
            selected_roles = session.get("user_roles", [])
            if not reviewer_name or not selected_roles:
                return redirect(url_for("login", next=url_for("start_review")))
        else:
            reviewer_name = request.form.get("reviewer_name", "").strip()
            selected_roles = request.form.getlist("selected_roles") or [request.form.get("selected_role", "").strip()]
            selected_roles = [r for r in selected_roles if r and r.strip()]
            if not reviewer_name or not selected_roles:
                return redirect(url_for("index"))

        current_time = datetime.now()
        session["review_start_time"] = current_time.isoformat()
        session["review_start_timestamp"] = current_time.timestamp()

        session["responses"] = {}
        session["current_category"] = 0
        session.pop("review_completed", None)  # New review
        session["reviewer_name"] = reviewer_name
        from services.user_profile import get_profile_by_name
        profile = get_profile_by_name(reviewer_name) if reviewer_name else None
        profile_user_id = (profile.get("user_id") or profile.get("username") or "") if profile else ""
        reviewer_user_id = profile_user_id or session.get("user_username", "")
        session["reviewer_username"] = reviewer_user_id
        session["selected_roles"] = selected_roles
        session["selected_role"] = selected_roles[0] if selected_roles else ""  # backward compat
        session["single_page_mode"] = True  # Single-page mode only
        session["mr_details"] = {}

        save_profile(user_id=reviewer_user_id, name=reviewer_name, preferred_roles=selected_roles)

        log_review_started(
            user_id=session.get("user_username", ""),
            user_name=reviewer_name,
            roles=selected_roles,
        )

        # Flow: Start → Patch → Patch summary → Checklist
        return redirect(url_for("review_patch"))

    @app.route("/review/patch", methods=["GET", "POST"])
    def review_patch():
        """Step 2: Upload patch (or skip). Requires session from POST /start."""
        if request.method == "POST":
            # Update MR/Commit details from form (both parse and skip paths)
            patch_mode = request.form.get("patch_mode", "mr").strip() or "mr"
            mr_link = request.form.get("mr_link", "").strip()
            source_branch = request.form.get("source_branch", "").strip()
            target_branch = request.form.get("target_branch", "").strip()
            branch_name = request.form.get("branch_name", "").strip()
            commit_hash = request.form.get("commit_hash", "").strip()
            project_id = request.form.get("project_id", "").strip()
            user_id = session.get("user_username") or session.get("reviewer_username") or ""
            if not user_id:
                from services.user_profile import get_profile_by_name
                profile = get_profile_by_name(session.get("reviewer_name", "")) if session.get("reviewer_name") else None
                if profile:
                    user_id = profile.get("user_id") or profile.get("username") or ""
            project_name = ""
            project_path = ""
            if project_id and user_id:
                proj = get_user_project(user_id, project_id)
                if proj:
                    project_name = proj.get("name") or proj.get("url_or_path") or ""
                    if proj.get("type") == "local":
                        project_path = proj.get("url_or_path") or ""
            session["mr_details"] = {
                "project_id": project_id,
                "project_name": project_name,
                "project_path": project_path,
                "patch_mode": patch_mode,
                "mr_link": mr_link,
                "source_branch": source_branch,
                "target_branch": target_branch,
                "branch_name": branch_name,
                "commit_hash": commit_hash,
            }
            if user_id:
                if project_id:
                    update_last_patch_selection(
                        user_id,
                        project_id=project_id,
                        patch_mode=patch_mode,
                        branch_name=branch_name,
                        commit_hash=commit_hash,
                        source_branch=source_branch,
                        target_branch=target_branch,
                        project_name=project_name,
                        project_path=project_path,
                        mr_link=mr_link,
                    )
                else:
                    last = get_last_patch_selection(user_id)
                    base = last.copy() if last else {}
                    update_last_patch_selection(
                        user_id,
                        project_id=base.get("project_id", ""),
                        patch_mode=patch_mode,
                        branch_name=base.get("branch_name", ""),
                        commit_hash=base.get("commit_hash", ""),
                        source_branch=source_branch or base.get("source_branch", ""),
                        target_branch=target_branch or base.get("target_branch", ""),
                        project_name=base.get("project_name", ""),
                        project_path=base.get("project_path", ""),
                        mr_link=mr_link or base.get("mr_link", ""),
                    )

            skip = request.form.get("skip_patch") == "1"
            if skip:
                return _redirect_to_checklist()
            content = request.form.get("patch_content", "").strip()
            if not content:
                f = request.files.get("patch_file") if request.files else None
                if f and f.filename:
                    try:
                        raw = f.read()
                        content = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
                    except Exception:
                        content = raw.decode("latin-1", errors="replace") if isinstance(raw, bytes) else ""
            if not content or not content.strip():
                from flask import flash
                flash("Please upload a .patch file (or drag and drop), or click Skip.", "warning")
                return redirect(url_for("review_patch"))
            try:
                project_path = ""
                if project_id and user_id:
                    proj = get_user_project(user_id, project_id)
                    if proj and proj.get("type") == "local":
                        project_path = proj.get("url_or_path") or ""
                files, summary = parse_patch(content, project_path=project_path or None)
                if not files:
                    from flask import flash
                    flash("No valid diff content found. Use a unified diff (e.g. from GitLab MR).", "warning")
                    return redirect(url_for("review_patch"))
                patch_data = {
                    "summary": summary,
                    "files": file_diffs_to_json_serializable(files),
                }
                session["patch_data_key"] = _save_patch_data(patch_data)
                audit_log("patch_upload",
                          user_id=session.get("user_username"),
                          user_name=session.get("user_name"),
                          ip=request.environ.get("REMOTE_ADDR"),
                          details={"files_count": len(files)})
                return redirect(url_for("patch_summary"))
            except Exception as e:
                from flask import flash
                flash(f"Failed to parse patch: {str(e)}", "danger")
                return redirect(url_for("review_patch"))
        # GET: must have started a review (session has reviewer_name, selected_roles)
        selected_roles = session.get("selected_roles") or session.get("selected_role")
        if not session.get("reviewer_name") or not selected_roles:
            return redirect(url_for("start_review"))
        mr_details = session.get("mr_details") or {}
        user_id = session.get("user_username") or session.get("reviewer_username") or ""
        if not user_id:
            from services.user_profile import get_profile_by_name, get_last_used_user_id
            reviewer_name = session.get("reviewer_name", "")
            profile = get_profile_by_name(reviewer_name) if reviewer_name else None
            if profile:
                user_id = profile.get("user_id") or profile.get("username") or ""
            if not user_id:
                user_id = get_last_used_user_id() or ""
        if not mr_details and user_id:
            last = get_last_patch_selection(user_id)
            if last:
                mr_details = last
        projects = get_projects(user_id) if user_id else []
        return render_template("review_patch.html", mr_details=mr_details, projects=projects or [])

    def _redirect_to_checklist():
        return redirect(url_for("review_all_categories"))

    def _patch_store_dir() -> Path:
        d = get_temp_dir() / "patch_store"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _save_patch_data(patch_data: Dict[str, Any]) -> str:
        key = str(uuid.uuid4())
        path = _patch_store_dir() / f"{key}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(patch_data, f, ensure_ascii=False)
        return key

    def _load_patch_data(key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        k = key or session.get("patch_data_key")
        if not k:
            return session.get("patch_data")
        path = _patch_store_dir() / f"{k}.json"
        if not path.exists():
            return session.get("patch_data")
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return session.get("patch_data")

    def _clear_patch_storage():
        k = session.pop("patch_data_key", None)
        session.pop("patch_data", None)
        if k:
            path = _patch_store_dir() / f"{k}.json"
            try:
                if path.exists():
                    path.unlink()
            except Exception:
                pass

    @app.route("/upload-patch", methods=["GET", "POST"])
    def upload_patch():
        """Upload a git patch (.patch file, drag and drop)."""
        if request.method == "POST":
            content = None
            f = request.files.get("patch_file") if request.files else None
            if f and f.filename:
                try:
                    raw = f.read()
                    content = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
                except Exception:
                    content = raw.decode("latin-1", errors="replace") if isinstance(raw, bytes) else None
            if not content or not content.strip():
                from flask import flash
                flash("Please upload a .patch file (or drag and drop).", "warning")
                return redirect(url_for("upload_patch"))
            try:
                files, summary = parse_patch(content, project_path=None)
                if not files:
                    from flask import flash
                    flash("No valid diff content found. Use a unified diff (e.g. from GitLab MR).", "warning")
                    return redirect(url_for("upload_patch"))
                patch_data = {
                    "summary": summary,
                    "files": file_diffs_to_json_serializable(files),
                }
                session["patch_data_key"] = _save_patch_data(patch_data)
                audit_log("patch_upload",
                          user_id=session.get("user_username"),
                          user_name=session.get("user_name"),
                          ip=request.environ.get("REMOTE_ADDR"),
                          details={"files_count": len(files)})
                return redirect(url_for("patch_summary"))
            except Exception as e:
                from flask import flash
                flash(f"Failed to parse patch: {str(e)}", "danger")
                return redirect(url_for("upload_patch"))
        return render_template("upload_patch.html")

    def _ensure_top_changed_files(patch_data: dict, summary: dict) -> dict:
        """Add top_changed_files to summary when missing (backward compat for older stored patches)."""
        if "top_changed_files" in summary or not patch_data:
            return summary
        files = patch_data.get("files", [])
        if not files:
            return summary
        with_changes = []
        for i, f in enumerate(files):
            add = f.get("lines_added", 0) or 0
            del_ = f.get("lines_deleted", 0) or 0
            path = f.get("new_path", "") or f.get("old_path", "")
            with_changes.append({"path": path, "added": add, "deleted": del_, "total": add + del_, "file_index": i})
        top = sorted(with_changes, key=lambda x: x["total"], reverse=True)[:10]
        summary = dict(summary)
        summary["top_changed_files"] = top
        return summary

    @app.route("/patch-summary")
    def patch_summary():
        """Patch analysis & summary. In review flow: allow no patch (then show Continue to checklist)."""
        selected_roles = session.get("selected_roles") or session.get("selected_role")
        in_review_flow = bool(session.get("reviewer_name") and selected_roles)
        patch_data = _load_patch_data()
        if not in_review_flow and not patch_data:
            return redirect(url_for("upload_patch"))
        if not in_review_flow and patch_data:
            summary = _ensure_top_changed_files(patch_data, patch_data.get("summary", {}))
            return render_template("patch_summary.html", summary=summary, in_review_flow=False, has_patch=True)
        if in_review_flow:
            summary = (patch_data or {}).get("summary", {}) if patch_data else {}
            summary = _ensure_top_changed_files(patch_data or {}, summary)
            return render_template(
                "patch_summary.html",
                summary=summary,
                in_review_flow=True,
                has_patch=bool(patch_data),
            )
        return redirect(url_for("upload_patch"))

    @app.route("/test-coverage")
    @app.route("/test_coverage")  # alias for common typo
    def test_coverage():
        """Dedicated test coverage page with AST-based analysis and flagged issues."""
        patch_data = _load_patch_data()
        if not patch_data:
            return redirect(url_for("upload_patch"))
        summary = patch_data.get("summary") or {}
        summary = _ensure_top_changed_files(patch_data, summary)
        return render_template(
            "test_coverage.html",
            summary=summary,
            in_review_flow=bool(session.get("reviewer_name") and (session.get("selected_roles") or session.get("selected_role"))),
            has_patch=True,
        )

    @app.route("/patch-clear", methods=["POST"])
    def patch_clear():
        """Remove patch from session and storage."""
        _clear_patch_storage()
        selected_roles = session.get("selected_roles") or session.get("selected_role")
        if session.get("reviewer_name") and selected_roles:
            return redirect(url_for("patch_summary"))
        return redirect(url_for("upload_patch"))

    def _build_file_tree(files):
        """Build a nested tree (folders + files) for the left sidebar. Each node is a dict."""
        root = []
        for i, f in enumerate(files):
            path = (getattr(f, "new_path", None) or "").replace("\\", "/")
            parts = path.split("/") if path else []
            if not parts:
                root.append({"type": "file", "name": path or "(unnamed)", "path": path, "file_index": i})
                continue
            current = root
            for j, part in enumerate(parts):
                is_leaf = j == len(parts) - 1
                if is_leaf:
                    node = {
                        "type": "file",
                        "name": part,
                        "path": path,
                        "file_index": i,
                        "add": getattr(f, "lines_added", 0),
                        "del": getattr(f, "lines_deleted", 0),
                        "file_type": getattr(f, "file_type", "other"),
                    }
                    current.append(node)
                else:
                    child = next((n for n in current if n.get("type") == "folder" and n.get("name") == part), None)
                    if not child:
                        child = {"type": "folder", "name": part, "children": []}
                        current.append(child)
                    current = child["children"]
        return root

    def _build_methods_by_file_index(files, summary):
        """Build list of method names per file index for test-focused highlighting."""
        tca = (summary or {}).get("test_coverage_analysis") or {}
        mwt = tca.get("methods_without_tests") or []
        if not mwt:
            return []

        def _norm(p):
            return (p or "").replace("\\", "/").lstrip("./")

        path_to_methods: Dict[str, List[str]] = {}
        for item in mwt:
            path = _norm(item.get("source_path", ""))
            method = item.get("method", "")
            if path and method:
                path_to_methods.setdefault(path, []).append(method)

        result = []
        for f in files:
            path = _norm(getattr(f, "new_path", None) or getattr(f, "old_path", ""))
            result.append(path_to_methods.get(path, []))

        return result

    @app.route("/code")
    def code_browser():
        """
        Generic code browser and navigator. Reusable from:
        - Patch review: source=patch (diff view, test_focus for highlighting)
        - Project details: source=project&project_id=<id> (index hierarchy)
        """
        source = request.args.get("source", "").lower() or "patch"
        project_id = request.args.get("project_id", "")
        test_focus = request.args.get("test_focus", "").lower() in ("1", "true", "yes")

        # Project mode: show project index hierarchy
        if source == "project" and project_id:
            if not session.get("user_name"):
                return redirect(url_for("login", next=url_for("code_browser", source="project", project_id=project_id)))
            user_id = _resolve_user_id()
            if not user_id:
                from flask import flash
                flash("Session expired. Please sign in again.", "warning")
                return redirect(url_for("login", next=url_for("code_browser", source="project", project_id=project_id)))
            project = get_user_project(user_id, project_id)
            if not project:
                from flask import flash
                flash("Project not found.", "warning")
                return redirect(url_for("dashboard"))
            url_or_path = project.get("url_or_path", "")
            proj_type = project.get("type", "local")
            index = get_project_index(project_id, url_or_path, force_rebuild=False) if proj_type == "local" and url_or_path else None
            files_by_type = {}
            stats = {"classes": 0, "methods": 0, "test_cases": 0}
            if index and index.get("files"):
                for f in index["files"]:
                    ft = f.get("type", "other")
                    if ft in ("source", "test"):
                        files_by_type.setdefault(ft, []).append(f)
                        stats["classes"] += len(f.get("classes", []))
                        stats["methods"] += len(f.get("methods", []))
                        stats["test_cases"] += len(f.get("test_cases", []))
            source_hierarchy = build_source_hierarchy(index) if index else []
            return render_template(
                "project_code.html",
                project=project,
                index=index,
                files_by_type=files_by_type,
                stats=stats,
                source_hierarchy=source_hierarchy,
                code_browser_context="project",
            )

        # Patch mode: diff viewer (default)
        patch_data = _load_patch_data()
        if not patch_data:
            return redirect(url_for("upload_patch"))
        files = file_diffs_from_session(patch_data.get("files", []))
        file_tree = _build_file_tree(files)
        summary = patch_data.get("summary") or {}
        methods_by_file_index = _build_methods_by_file_index(files, summary)
        has_highlightable = any(m for m in methods_by_file_index) if methods_by_file_index else False
        return render_template(
            "review_code.html",
            files=files,
            files_count=len(files),
            file_tree=file_tree,
            summary=summary,
            test_focus=test_focus,
            methods_by_file_index=methods_by_file_index,
            has_highlightable=has_highlightable,
            code_browser_context="patch",
        )

    @app.route("/review/code")
    def review_code():
        """Redirect to generic code browser (patch mode). Kept for backward compatibility."""
        return redirect(url_for("code_browser", source="patch", **{k: v for k, v in request.args.items()}))

    @app.route("/project/<project_id>/code")
    def project_code(project_id: str):
        """Redirect to generic code browser (project mode). Kept for backward compatibility."""
        return redirect(url_for("code_browser", source="project", project_id=project_id, **{k: v for k, v in request.args.items() if k != "project_id"}))

    @app.route("/review/all", methods=["GET", "POST"])
    def review_all_categories():
        if request.method == "POST":
            debug_log("DEBUG: POST request received in review_all_categories")
            debug_log("DEBUG: Form data: " + str(dict(request.form)))

            try:
                \
                responses = session.get("responses", {})
                responses = _process_review_form_data(responses, dict(request.form))

                session["responses"] = responses

                audit_log("review_submit",
                          user_id=session.get("user_username"),
                          user_name=session.get("user_name"),
                          roles=session.get("user_roles"),
                          ip=request.environ.get("REMOTE_ADDR"),
                          details={"total_items": len(responses)})

                debug_log("DEBUG: Redirecting to summary")
                return redirect(url_for("summary"))
            except Exception as e:
                debug_log(f"ERROR: Failed to process review submission: {str(e)}")
                from flask import flash
                flash(f"Error processing review: {str(e)}", "danger")
                return redirect(url_for("review_all_categories"))

        categories = _get_categories()
        if not categories:
            return render_template("empty.html")

        saved_responses = session.get("responses", {})

        return render_template(
            "review_all_categories.html",
            categories=categories,
            saved_responses=saved_responses,
        )

    @app.route("/review/category/<int:idx>", methods=["GET", "POST"])
    def review_category(idx: int):
        categories = _get_categories()
        total = len(categories)
        if total == 0:
            return render_template("empty.html")

        if idx < 0:
            return redirect(url_for("review_category", idx=0))
        if idx >= total:
            return redirect(url_for("summary"))

        if request.method == "POST":
            action = request.form.get("action", "next")
            responses: Dict[str, Dict[str, Any]] = session.get("responses", {})

            \
            category = categories[idx]
            for item in category["item_list"]:
                item_key = f"{item['role_id']}|{item['category_id']}|{item['item_id']}"
                status = request.form.get(f"status_{item_key}")
                comment = request.form.get(f"comment_{item_key}", "").strip()

                \
                if not status:
                    status = "UNANSWERED"

                responses[item_key] = {
                    "status": status,
                    "comment": comment,
                    "role_id": item["role_id"],
                    "role_name": item["role_name"],
                    "category_id": item["category_id"],
                    "category_name": item["category_name"],
                    "item_text": item["item_text"],
                }

            session["responses"] = responses

            if action == "prev":
                return redirect(url_for("review_category", idx=max(0, idx - 1)))
            elif action == "finish":
                return redirect(url_for("summary"))
            else:
                return redirect(url_for("review_category", idx=min(total - 1, idx + 1)))

        category = categories[idx]

        \
        saved_responses = {}
        for item in category["item_list"]:
            item_key = f"{item['role_id']}|{item['category_id']}|{item['item_id']}"
            saved_responses[item_key] = session.get("responses", {}).get(item_key, {})

        all_steps = _get_steps()
        total_items = len(all_steps)
        answered_items = 0

        for step in all_steps:
            key = f"{step['role_id']}|{step['category_id']}|{step['item_id']}"
            if key in session.get("responses", {}):
                response = session["responses"][key].get("status", "")
                if response and response != "UNANSWERED":
                    answered_items += 1

        progress = {
            "current": idx + 1,
            "total": total,
            "answered_items": answered_items,
            "total_items": total_items,
            "percent": int((answered_items / total_items) * 100) if total_items > 0 else 0,
        }

        return render_template(
            "review_category_table.html",
            category=category,
            idx=idx,
            progress=progress,
            saved_responses=saved_responses,
            is_last=(idx == total - 1),
        )

    @app.route("/summary")
    def summary():
        debug_log("DEBUG: Summary route called")
        debug_log("DEBUG: Session keys: " + str(list(session.keys())))

        steps = _get_steps()
        responses: Dict[str, Dict[str, Any]] = session.get("responses", {})
        summary_data, counts_overall = _compute_summary(steps, responses)

        reviewer_name = session.get("reviewer_name", "Unknown")
        reviewer_username = session.get("reviewer_username", "")
        config = load_roles_config()
        role_map = {r["id"]: r["name"] for r in config.get("roles", [])}
        selected_roles = session.get("selected_roles", []) or ([session.get("selected_role")] if session.get("selected_role") else [])
        selected_role = _format_roles_display(selected_roles, role_map) or "All Roles"

        if "review_completed" not in session:
            debug_log("DEBUG: Marking review as completed")
            session["review_completed"] = True

            \
            start_time_str = session.get("review_start_time")
            start_timestamp = session.get("review_start_timestamp")

            if start_time_str and start_timestamp:
                try:
                    start_time = datetime.fromisoformat(start_time_str)
                    end_time = datetime.now()
                    duration = end_time - start_time

                    \
                    total_seconds = int(duration.total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    seconds = total_seconds % 60

                    if hours > 0:
                        duration_str = f"{hours}h {minutes}m {seconds}s"
                    elif minutes > 0:
                        duration_str = f"{minutes}m {seconds}s"
                    else:
                        duration_str = f"{seconds}s"

                    session["review_end_time"] = end_time.strftime("%Y-%m-%d %H:%M:%S")
                    session["review_duration"] = duration_str
                    session["review_duration_seconds"] = total_seconds
                    debug_log("DEBUG: Review marked as completed with calculated timing")
                except Exception as e:
                    debug_log(f"DEBUG: Error calculating timing: {e}")
                    session["review_end_time"] = "Unknown"
                    session["review_duration"] = "Unknown"
                    session["review_duration_seconds"] = 0
            else:
                session["review_end_time"] = "Unknown"
                session["review_duration"] = "Unknown"
                session["review_duration_seconds"] = 0
                debug_log("DEBUG: No start time found, storing Unknown values")

            log_review_completed(
                user_id=reviewer_username or session.get("user_username", ""),
                user_name=reviewer_name,
                ok=counts_overall.get("OK", 0),
                ng=counts_overall.get("NG", 0),
                na=counts_overall.get("NA", 0),
                skipped=counts_overall.get("SKIPPED", 0),
                unanswered=counts_overall.get("UNANSWERED", 0),
                total_items=len(steps),
                duration_seconds=session.get("review_duration_seconds", 0),
                roles=selected_roles,
            )
        else:
            debug_log("DEBUG: Review already marked as completed")

        review_timing = _calculate_review_time()
        mr_details = session.get("mr_details", {})

        patch_summary = {}
        try:
            patch_data = _load_patch_data()
            if patch_data:
                patch_summary = patch_data.get("summary", {})
        except Exception:
            pass

        debug_log("DEBUG: Final review_timing: " + str(review_timing))

        return render_template(
            "summary.html",
            summary=summary_data,
            counts_overall=counts_overall,
            reviewer_name=reviewer_name,
            reviewer_username=reviewer_username,
            selected_role=selected_role,
            review_timing=review_timing,
            mr_details=mr_details,
            patch_summary=patch_summary,
        )

    @app.route("/download/html")
    def download_html():
        try:
            steps = _get_steps()
            responses: Dict[str, Dict[str, Any]] = session.get("responses", {})

            if not steps:
                return "No review data available. Please complete a review first.", 400

            summary_data, counts_overall = _compute_summary(steps, responses)
            reviewer_name = session.get("reviewer_name", "Unknown")
            reviewer_username = session.get("reviewer_username", "")
            config = load_roles_config()
            role_map = {r["id"]: r["name"] for r in config.get("roles", [])}
            selected_roles = session.get("selected_roles", []) or ([session.get("selected_role")] if session.get("selected_role") else [])
            selected_role = _format_roles_display(selected_roles, role_map) or "Unknown"
            review_timing = _calculate_review_time()
            mr_details = session.get("mr_details", {})

            # When block_external_resources, inline CSS so downloaded HTML needs no external fetches
            inline_bootstrap_css = None
            inline_icons_css = None
            if app_config.get("data_egress", {}).get("block_external_resources"):
                import base64
                import re
                static_root = Path(__file__).parent / "static"
                bs_css = static_root / "vendor" / "bootstrap" / "css" / "bootstrap.min.css"
                icons_css_path = static_root / "vendor" / "bootstrap-icons" / "bootstrap-icons.css"
                icons_font_woff2 = static_root / "vendor" / "bootstrap-icons" / "fonts" / "bootstrap-icons.woff2"
                if bs_css.exists():
                    inline_bootstrap_css = bs_css.read_text(encoding="utf-8", errors="replace")
                if icons_css_path.exists():
                    inline_icons_css = icons_css_path.read_text(encoding="utf-8", errors="replace")
                    if icons_font_woff2.exists():
                        font_b64 = base64.b64encode(icons_font_woff2.read_bytes()).decode("ascii")
                        inline_icons_css = re.sub(
                            r'url\("fonts/bootstrap-icons\.woff2[^"]*"\)',
                            f'url("data:font/woff2;base64,{font_b64}")',
                            inline_icons_css,
                        )
                    woff_path = static_root / "vendor" / "bootstrap-icons" / "fonts" / "bootstrap-icons.woff"
                    if woff_path.exists():
                        woff_b64 = base64.b64encode(woff_path.read_bytes()).decode("ascii")
                        inline_icons_css = re.sub(
                            r'url\("fonts/bootstrap-icons\.woff[^"]*"\)',
                            f'url("data:font/woff;base64,{woff_b64}")',
                            inline_icons_css,
                        )

            patch_summary = {}
            try:
                patch_data = _load_patch_data()
                if patch_data:
                    patch_summary = patch_data.get("summary", {})
            except Exception:
                pass

            html = render_template("report_standalone.html",
                                 summary=summary_data,
                                 counts_overall=counts_overall,
                                 reviewer_name=reviewer_name,
                                 reviewer_username=reviewer_username,
                                 selected_role=selected_role,
                                 review_timing=review_timing,
                                 mr_details=mr_details,
                                 patch_summary=patch_summary,
                                 inline_bootstrap_css=inline_bootstrap_css,
                                 inline_icons_css=inline_icons_css)
            response = make_response(html)
            response.headers["Content-Type"] = "text/html; charset=utf-8"
            response.headers["Content-Disposition"] = "attachment; filename=code_review_report.html"
            return response
        except Exception as e:
            return f"Error generating HTML report: {str(e)}", 500

    @app.route("/download/pdf")
    def download_pdf():
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import mm
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        except ImportError:
            from flask import flash, redirect, url_for
            flash("PDF export requires 'reportlab' library. Please install it with: pip install reportlab", "warning")
            return redirect(url_for("summary"))

        steps = _get_steps()
        responses: Dict[str, Dict[str, Any]] = session.get("responses", {})
        reviewer_name = session.get("reviewer_name", "Unknown")
        reviewer_username = session.get("reviewer_username", "")
        config = load_roles_config()
        role_map = {r["id"]: r["name"] for r in config.get("roles", [])}
        selected_roles = session.get("selected_roles", []) or ([session.get("selected_role")] if session.get("selected_role") else [])
        selected_role = _format_roles_display(selected_roles, role_map) or "Unknown"
        review_timing = _calculate_review_time()

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                              rightMargin=20*mm, leftMargin=20*mm,
                              topMargin=20*mm, bottomMargin=20*mm)

        styles = getSampleStyleSheet()
        story = []

        \
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        )

        subheading_style = ParagraphStyle(
            'CustomSubHeading',
            parent=styles['Heading3'],
            fontSize=12,
            spaceAfter=8,
            textColor=colors.darkgreen
        )

        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )

        story.append(Paragraph("Code Review Report", title_style))
        story.append(Spacer(1, 20))

        metadata_data = [
            ['Reviewer:', reviewer_name],
            ['Role:', selected_role],
        ]
        if reviewer_username:
            metadata_data.insert(1, ['Username:', reviewer_username])
        metadata_data += [
            ['Review Started:', review_timing['start_time']],
            ['Review Completed:', review_timing['end_time']],
            ['Duration:', review_timing['duration']]
        ]
        try:
            patch_data = _load_patch_data()
            if patch_data:
                ps = patch_data.get("summary", {})
                if ps:
                    metadata_data += [
                        ['Methods:', str(ps.get("total_methods_count", 0))],
                        ['Test cases:', f"+{ps.get('test_cases_added_count', 0)} added, −{ps.get('test_cases_removed_count', 0)} removed"],
                    ]
                    pac = ps.get("patch_ast_changes", {})
                    if pac and any(pac.values()):
                        metadata_data.append([
                            'AST changes:',
                            f"Classes +{pac.get('classes_added', 0)}/−{pac.get('classes_deleted', 0)}/{pac.get('classes_modified', 0)} · "
                            f"Methods +{pac.get('methods_added', 0)}/−{pac.get('methods_deleted', 0)}/{pac.get('methods_modified', 0)} · "
                            f"Tests +{pac.get('tests_added', 0)}/−{pac.get('tests_deleted', 0)}/{pac.get('tests_modified', 0)}",
                        ])
        except Exception:
            pass

        metadata_table = Table(metadata_data, colWidths=[60*mm, 100*mm])
        metadata_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        story.append(metadata_table)
        story.append(Spacer(1, 20))

        summary_data, counts_overall = _compute_summary(steps, responses)
        story.append(Paragraph("Overall Statistics", heading_style))

        stats_data = [
            ['Status', 'Count', 'Percentage'],
            ['OK', str(counts_overall['OK']), f"{(counts_overall['OK'] / len(steps) * 100):.1f}%" if len(steps) > 0 else "0%"],
            ['NG', str(counts_overall['NG']), f"{(counts_overall['NG'] / len(steps) * 100):.1f}%" if len(steps) > 0 else "0%"],
            ['N/A', str(counts_overall['NA']), f"{(counts_overall['NA'] / len(steps) * 100):.1f}%" if len(steps) > 0 else "0%"],
            ['Unanswered', str(counts_overall['UNANSWERED']), f"{(counts_overall['UNANSWERED'] / len(steps) * 100):.1f}%" if len(steps) > 0 else "0%"]
        ]

        if app_config.get('features', {}).get('skip_categories', True):
            stats_data.insert(-1, ['Skipped', str(counts_overall.get('SKIPPED', 0)), f"{(counts_overall.get('SKIPPED', 0) / len(steps) * 100):.1f}%" if len(steps) > 0 else "0%"])

        stats_table = Table(stats_data, colWidths=[40*mm, 30*mm, 30*mm])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(stats_table)
        story.append(Spacer(1, 20))

        story.append(Paragraph("Detailed Review Results", heading_style))

        current_role = None
        current_cat = None

        for step in steps:
            key = f"{step['role_id']}|{step['category_id']}|{step['item_id']}"
            resp = responses.get(key, {})
            status = resp.get("status", "UNANSWERED")
            comment = resp.get("comment", "")

            if current_role != step["role_id"]:
                story.append(Spacer(1, 10))
                story.append(Paragraph(f"Role: {step['role_name']}", subheading_style))
                current_role = step["role_id"]
                current_cat = None

            if current_cat != step["category_id"]:
                story.append(Paragraph(f"Category: {step['category_name']}", normal_style))
                current_cat = step["category_id"]

            status_color = {
                'OK': colors.green,
                'NG': colors.red,
                'NA': colors.grey,
                'UNANSWERED': colors.orange,
                'SKIPPED': colors.blue
            }.get(status, colors.black)

            item_text = step["item_text"]
            status_text = f"<font color='{status_color.hexval()}'><b>[{status}]</b></font> {item_text}"
            story.append(Paragraph(status_text, normal_style))

            if comment:
                comment_text = f"<i>Note: {comment}</i>"
                story.append(Paragraph(comment_text, normal_style))

        doc.build(story)
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"code_review_report_{reviewer_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mimetype="application/pdf",
        )

    @app.route("/manifest.json")
    def manifest():
        """Serve the PWA manifest file"""
        return send_file("static/manifest.json", mimetype="application/json")

    @app.route("/sw.js")
    def service_worker():
        """Serve the service worker file"""
        return send_file("static/sw.js", mimetype="application/javascript")

    @app.route("/offline")
    def offline():
        """Offline page for PWA"""
        return render_template("offline.html")

    @app.route("/api/sync-offline-data", methods=["POST"])
    def sync_offline_data():
        """API endpoint to sync offline data"""
        try:
            data = request.get_json()
            \
\
            return {"status": "success", "message": "Offline data synced successfully"}, 200
        except Exception as e:
            return {"status": "error", "message": str(e)}, 500

    @app.route("/api/git/pull", methods=["POST"])
    def api_git_pull():
        """Pull from remote using system git credentials (credential helper)."""
        try:
            data = request.get_json(silent=True) or {}
            remote = data.get("remote", "origin")
            branch = data.get("branch")
            result = git_pull(repo_path=get_project_root(), remote=remote, branch=branch)
            if result["success"]:
                return {"status": "success", "message": result["message"], "stdout": result["stdout"]}, 200
            return {"status": "error", "message": result["message"], "stderr": result["stderr"]}, 400
        except Exception as e:
            return {"status": "error", "message": str(e)}, 500

    @app.route("/api/git/push", methods=["POST"])
    def api_git_push():
        """Push to remote using system git credentials (credential helper)."""
        try:
            data = request.get_json(silent=True) or {}
            remote = data.get("remote", "origin")
            branch = data.get("branch")
            result = git_push(repo_path=get_project_root(), remote=remote, branch=branch)
            if result["success"]:
                return {"status": "success", "message": result["message"], "stdout": result["stdout"]}, 200
            return {"status": "error", "message": result["message"], "stderr": result["stderr"]}, 400
        except Exception as e:
            return {"status": "error", "message": str(e)}, 500

    @app.route("/api/git/credentials-info", methods=["GET"])
    def api_git_credentials_info():
        """Return detected credential helper info (no credentials exposed)."""
        try:
            info = get_credential_helper_info(repo_path=get_project_root())
            return {"status": "success", "credentials_info": info}, 200
        except Exception as e:
            return {"status": "error", "message": str(e)}, 500

    @app.route("/api/project/<project_id>/commits", methods=["GET"])
    def api_project_commits(project_id: str):
        """Fetch recent commits for a project (local repos only)."""
        try:
            user_id = session.get("user_username") or session.get("reviewer_username") or ""
            if not user_id:
                from services.user_profile import get_profile_by_name
                reviewer_name = session.get("reviewer_name", "")
                profile = get_profile_by_name(reviewer_name) if reviewer_name else None
                if profile:
                    user_id = profile.get("user_id") or profile.get("username") or ""
            if not user_id or not project_id:
                return {"status": "error", "message": "Not authenticated"}, 401
            project = get_user_project(user_id, project_id)
            if not project:
                return {"status": "error", "message": "Project not found"}, 404
            url_or_path = project.get("url_or_path", "")
            proj_type = project.get("type", "remote")
            if proj_type != "local":
                return {"status": "success", "commits": [], "message": "Commit fetch only for local projects"}, 200
            path = Path(url_or_path)
            branch = request.args.get("branch", "").strip() or None
            commits = get_commits(path, limit=30, branch=branch)
            return {"status": "success", "commits": commits}, 200
        except Exception as e:
            return {"status": "error", "message": str(e)}, 500

    @app.route("/api/project/<project_id>/branches", methods=["GET"])
    def api_project_branches(project_id: str):
        """Fetch branches for a project (local repos only)."""
        try:
            user_id = session.get("user_username") or session.get("reviewer_username") or ""
            if not user_id:
                from services.user_profile import get_profile_by_name
                reviewer_name = session.get("reviewer_name", "")
                profile = get_profile_by_name(reviewer_name) if reviewer_name else None
                if profile:
                    user_id = profile.get("user_id") or profile.get("username") or ""
            if not user_id or not project_id:
                return {"status": "error", "message": "Not authenticated"}, 401
            project = get_user_project(user_id, project_id)
            if not project:
                return {"status": "error", "message": "Project not found"}, 404
            url_or_path = project.get("url_or_path", "")
            proj_type = project.get("type", "remote")
            if proj_type != "local":
                return {"status": "success", "branches": [], "message": "Branch fetch only for local projects"}, 200
            path = Path(url_or_path)
            branches = get_branches(path, include_remote=False)
            return {"status": "success", "branches": branches}, 200
        except Exception as e:
            return {"status": "error", "message": str(e)}, 500

    @app.route("/api/project/<project_id>/commit/<commit_hash>/patch", methods=["GET"])
    def api_project_commit_patch(project_id: str, commit_hash: str):
        """Fetch patch content for a commit (local repos only)."""
        try:
            user_id = session.get("user_username") or session.get("reviewer_username") or ""
            if not user_id:
                from services.user_profile import get_profile_by_name
                reviewer_name = session.get("reviewer_name", "")
                profile = get_profile_by_name(reviewer_name) if reviewer_name else None
                if profile:
                    user_id = profile.get("user_id") or profile.get("username") or ""
            if not user_id or not project_id or not commit_hash:
                return {"status": "error", "message": "Not authenticated"}, 401
            project = get_user_project(user_id, project_id)
            if not project:
                return {"status": "error", "message": "Project not found"}, 404
            url_or_path = project.get("url_or_path", "")
            proj_type = project.get("type", "remote")
            if proj_type != "local":
                return {"status": "error", "message": "Patch fetch only for local projects"}, 400
            path = Path(url_or_path)
            patch = get_commit_patch(path, commit_hash)
            if patch is None:
                return {"status": "error", "message": "Commit not found or has no changes"}, 404
            return {"status": "success", "patch": patch}, 200
        except Exception as e:
            return {"status": "error", "message": str(e)}, 500

    @app.route("/api/project/<project_id>/diff", methods=["GET"])
    def api_project_diff(project_id: str):
        """Fetch diff between source and target branches (GitLab MR style, local repos only)."""
        try:
            if app_config.get("features", {}).get("disable_mr_diff_fetch"):
                return {"status": "error", "message": "MR diff fetch is temporarily disabled"}, 403
            user_id = session.get("user_username") or session.get("reviewer_username") or ""
            if not user_id:
                from services.user_profile import get_profile_by_name
                reviewer_name = session.get("reviewer_name", "")
                profile = get_profile_by_name(reviewer_name) if reviewer_name else None
                if profile:
                    user_id = profile.get("user_id") or profile.get("username") or ""
            if not user_id or not project_id:
                return {"status": "error", "message": "Not authenticated"}, 401
            project = get_user_project(user_id, project_id)
            if not project:
                return {"status": "error", "message": "Project not found"}, 404
            url_or_path = project.get("url_or_path", "")
            proj_type = project.get("type", "remote")
            if proj_type != "local":
                return {"status": "error", "message": "Diff fetch only for local projects"}, 400
            source = request.args.get("source", "").strip()
            target = request.args.get("target", "").strip()
            if not source or not target:
                return {"status": "error", "message": "Source and target branches required"}, 400
            path = Path(url_or_path)
            diff = get_diff_between_branches(path, target, source)
            if diff is None:
                return {"status": "error", "message": "Diff failed or branches not found"}, 404
            if not diff.strip():
                return {"status": "error", "message": "No changes between branches"}, 404
            return {"status": "success", "patch": diff}, 200
        except Exception as e:
            return {"status": "error", "message": str(e)}, 500

    @app.route("/api/project/<project_id>/index", methods=["GET"])
    def api_project_index(project_id: str):
        """Get project index (file tree, classes, test cases). Builds if missing or stale."""
        try:
            user_id = session.get("user_username") or session.get("reviewer_username") or ""
            if not user_id:
                from services.user_profile import get_profile_by_name
                reviewer_name = session.get("reviewer_name", "")
                profile = get_profile_by_name(reviewer_name) if reviewer_name else None
                if profile:
                    user_id = profile.get("user_id") or profile.get("username") or ""
            if not user_id or not project_id:
                return {"status": "error", "message": "Not authenticated"}, 401
            project = get_user_project(user_id, project_id)
            if not project:
                return {"status": "error", "message": "Project not found"}, 404
            url_or_path = project.get("url_or_path", "")
            proj_type = project.get("type", "remote")
            if proj_type != "local":
                return {"status": "error", "message": "Index only for local projects"}, 400
            force = request.args.get("refresh", "").lower() in ("1", "true", "yes")
            index = get_project_index(project_id, url_or_path, force_rebuild=force)
            if not index:
                return {"status": "error", "message": "Project path not found or not a directory"}, 404
            return {"status": "success", "index": index}, 200
        except Exception as e:
            return {"status": "error", "message": str(e)}, 500

    @app.route("/api/project/<project_id>/index/refresh", methods=["POST"])
    def api_project_index_refresh(project_id: str):
        """Trigger project index rebuild in background."""
        try:
            user_id = session.get("user_username") or session.get("reviewer_username") or ""
            if not user_id:
                from services.user_profile import get_profile_by_name
                reviewer_name = session.get("reviewer_name", "")
                profile = get_profile_by_name(reviewer_name) if reviewer_name else None
                if profile:
                    user_id = profile.get("user_id") or profile.get("username") or ""
            if not user_id or not project_id:
                return {"status": "error", "message": "Not authenticated"}, 401
            project = get_user_project(user_id, project_id)
            if not project:
                return {"status": "error", "message": "Project not found"}, 404
            url_or_path = project.get("url_or_path", "")
            proj_type = project.get("type", "remote")
            if proj_type != "local":
                return {"status": "error", "message": "Index only for local projects"}, 400
            schedule_index_build(project_id, url_or_path)
            return {"status": "success", "message": "Index rebuild scheduled"}, 200
        except Exception as e:
            return {"status": "error", "message": str(e)}, 500

    @app.route("/api/last-patch-selection", methods=["POST"])
    def api_save_last_patch_selection():
        """Save last patch selection to profile (called on change, not just submit)."""
        try:
            user_id = session.get("user_username") or session.get("reviewer_username") or ""
            if not user_id:
                from services.user_profile import get_profile_by_name
                reviewer_name = session.get("reviewer_name", "")
                profile = get_profile_by_name(reviewer_name) if reviewer_name else None
                if profile:
                    user_id = profile.get("user_id") or profile.get("username") or ""
            if not user_id:
                return {"status": "error", "message": "Not authenticated"}, 401
            data = request.get_json(silent=True) or {}
            project_id = (data.get("project_id") or "").strip()
            patch_mode = (data.get("patch_mode") or "mr").strip() or "mr"
            branch_name = (data.get("branch_name") or "").strip()
            commit_hash = (data.get("commit_hash") or "").strip()
            source_branch = (data.get("source_branch") or "").strip()
            target_branch = (data.get("target_branch") or "").strip()
            mr_link = (data.get("mr_link") or "").strip()
            project_name = ""
            project_path = ""
            if project_id:
                proj = get_user_project(user_id, project_id)
                if proj:
                    project_name = proj.get("name") or proj.get("url_or_path") or ""
                    if proj.get("type") == "local":
                        project_path = proj.get("url_or_path") or ""
            if project_id:
                update_last_patch_selection(
                    user_id,
                    project_id=project_id,
                    patch_mode=patch_mode,
                    branch_name=branch_name,
                    commit_hash=commit_hash,
                    source_branch=source_branch,
                    target_branch=target_branch,
                    project_name=project_name,
                    project_path=project_path,
                    mr_link=mr_link,
                )
            else:
                last = get_last_patch_selection(user_id)
                base = last.copy() if last else {}
                update_last_patch_selection(
                    user_id,
                    project_id=base.get("project_id", ""),
                    patch_mode=patch_mode,
                    branch_name=base.get("branch_name", ""),
                    commit_hash=base.get("commit_hash", ""),
                    source_branch=source_branch or base.get("source_branch", ""),
                    target_branch=target_branch or base.get("target_branch", ""),
                    project_name=base.get("project_name", ""),
                    project_path=base.get("project_path", ""),
                    mr_link=mr_link or base.get("mr_link", ""),
                )
            return {"status": "success"}, 200
        except Exception as e:
            return {"status": "error", "message": str(e)}, 500

    app.config['app_config'] = app_config

    return app

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Restore app name Flask Application')
    parser.add_argument('--no-browser', action='store_true',
                       help='Disable auto-launch browser')
    parser.add_argument('--port', type=int, default=5000,
                       help='Port to run the server on (default: 5000)')
    parser.add_argument('--host', default='127.0.0.1',
                       help='Host to run the server on (default: 127.0.0.1)')
    parser.add_argument('--bind-all', action='store_true',
                       help='Bind to all addresses (0.0.0.0) instead of localhost only')
    parser.add_argument('--production', action='store_true',
                       help='Run in production mode (disable debug mode)')
    parser.add_argument('--dev-server', action='store_true',
                       help='Use Flask development server (not recommended for production)')
    parser.add_argument('--offline', action='store_true',
                       help='Enforce offline mode: block external resources, git remote, and downloads')

    args = parser.parse_args()

    if args.offline:
        os.environ['BLOCK_GIT_REMOTE'] = '1'
        print("Offline mode enabled: external resources, git remote, and downloads blocked")

    app = create_app()

    if args.offline:
        app.config.setdefault('app_config', {}).setdefault('data_egress', {})
        app.config['app_config']['data_egress']['block_external_resources'] = True
        app.config['app_config']['data_egress']['block_external_downloads'] = True
        app.config['app_config']['data_egress']['block_git_remote'] = True

    \
    if args.no_browser:
        print("Auto-launch browser disabled by command line")
        \
        if 'app_config' in app.config and 'features' in app.config['app_config']:
            app.config['app_config']['features']['auto_launch_browser'] = False
    else:
        \
        auto_launch = app.config.get('app_config', {}).get('features', {}).get('auto_launch_browser', False)
        if auto_launch:
            try:
                import webbrowser
                import threading
                import time

                def launch_browser():
                    time.sleep(1.5)
                    webbrowser.open(f'http://{args.host}:{args.port}')
                    print("Browser launched automatically")
                threading.Thread(target=launch_browser, daemon=True).start()
            except Exception as e:
                print(f"Failed to auto-launch browser: {e}")

    port = args.port
    host = '0.0.0.0' if args.bind_all else args.host

    print(f"Starting Restore app name on http://{host}:{port}")
    
    # Default to production WSGI server unless dev-server is explicitly requested
    if args.dev_server:
        print("Using Flask development server (not recommended for production)")
        debug_mode = not args.production
        if args.production:
            print("Running in production mode (debug disabled)")
            import warnings
            warnings.filterwarnings("ignore", message=".*development server.*")
        else:
            print("Running in development mode (debug enabled)")
        app.run(host=host, port=port, debug=debug_mode)
    else:
        # Use production WSGI server by default
        try:
            import waitress
            print("Using Waitress production WSGI server")
            print("Running in production mode (debug disabled)")
            waitress.serve(app, host=host, port=port, threads=4)
        except ImportError:
            print("Waitress not available, falling back to Flask development server")
            print("WARNING: This is a development server. Install waitress for production.")
            app.run(host=host, port=port, debug=False)
        except Exception as e:
            print(f"Error starting Waitress: {e}")
            print("Falling back to Flask development server")
            print("WARNING: This is a development server.")
            app.run(host=host, port=port, debug=False)
