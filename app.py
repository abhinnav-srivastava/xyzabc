import os
import io
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Tuple
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
    from utils.path_utils import get_scripts_path, get_checklists_path, get_templates_path, get_project_root
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

from services.checklist_loader import (
    load_roles_config,
    build_all_steps,
)
from services.network_security import network_security
from services.dynamic_categories import dynamic_categories

def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

    \
    config_path = Path(__file__).parent / "config" / "app_config.json"
    app_config = {}
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            app_config = json.load(f)
    else:
        pass

    @app.context_processor
    def inject_config():
        return {'app_config': app_config}

    def debug_log(message):
        if app_config.get('features', {}).get('debug_logging', False):
            print(message)

    try:
        import subprocess
        import sys

        \
\
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
    def validate_request():
        """Validate incoming requests for security"""
        client_ip = request.environ.get('REMOTE_ADDR', '127.0.0.1')
        is_allowed, reason = network_security.validate_request(client_ip)

        if not is_allowed:
            return f"Access denied: {reason}", 403

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

        selected_role = session.get("selected_role")
        if selected_role:
            steps = [step for step in all_steps if step["role_id"] == selected_role]
        else:
            steps = all_steps

        return steps

    def _process_review_form_data(responses: Dict[str, Dict[str, Any]], form_data: dict) -> Dict[str, Dict[str, Any]]:
        """
        Common function to process review form data for both individual and all-categories modes.
        Returns updated responses dictionary.
        """
        debug_log("DEBUG: _process_review_form_data called")
        debug_log("DEBUG: Form data keys: " + str(list(form_data.keys())))

        \
        skip_enabled = app_config.get('features', {}).get('skip_categories', False)
        debug_log("DEBUG: Skip feature enabled: " + str(skip_enabled))

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
            elif skip_enabled and key.startswith("category_skip_"):
                if key.endswith("_status"):
                    continue
                category_id = key[14:]
                skip_comment = form_data.get(f"category_skip_comment_{category_id}", "")

                if value == "on":
                    if category_id not in responses:
                        responses[category_id] = {}
                    responses[category_id]["skipped"] = True
                    responses[category_id]["skip_comment"] = skip_comment
                    debug_log(f"DEBUG: Category {category_id} marked as skipped")

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
        skip_enabled = app_config.get('features', {}).get('skip_categories', False)
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

    @app.route("/")
    def index():
        config = load_roles_config()
        return render_template("index.html", config=config)

    @app.route("/start-review")
    def start_review_page():
        """Display the start review page with form."""
        config = load_roles_config()
        \
        import getpass
        windows_username = getpass.getuser()
        return render_template("start_review.html", config=config, default_username=windows_username)

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

    @app.route("/start", methods=["POST"])
    def start_review():
        reviewer_name = request.form.get("reviewer_name", "").strip()
        selected_role = request.form.get("selected_role", "").strip()
        single_page_mode = request.form.get("single_page_mode") == "on"

        \
        mr_link = request.form.get("mr_link", "").strip()
        branch_name = request.form.get("branch_name", "").strip()
        commit_hash = request.form.get("commit_hash", "").strip()
        project_name = request.form.get("project_name", "").strip()

        if not reviewer_name or not selected_role:
            return redirect(url_for("index"))

        current_time = datetime.now()
        session["review_start_time"] = current_time.isoformat()
        session["review_start_timestamp"] = current_time.timestamp()

        session["responses"] = {}
        session["current_category"] = 0
        session["reviewer_name"] = reviewer_name
        session["selected_role"] = selected_role
        session["single_page_mode"] = single_page_mode

        \
        session["mr_details"] = {
            "mr_link": mr_link,
            "branch_name": branch_name,
            "commit_hash": commit_hash,
            "project_name": project_name
        }

        \
        if single_page_mode:
            return redirect(url_for("review_all_categories"))
        else:
            return redirect(url_for("review_category", idx=0))

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

                \
\
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

        \
        all_steps = _get_steps()
        total_items = len(all_steps)
        answered_items = 0

        for step in all_steps:
            key = f"{step['role_id']}|{step['category_id']}|{step['item_id']}"
            if key in saved_responses:
                response = saved_responses[key].get("status", "")
                if response and response != "UNANSWERED":
                    answered_items += 1

        progress = {
            "answered_items": answered_items,
            "total_items": total_items,
            "percent": int((answered_items / total_items) * 100) if total_items > 0 else 0,
        }

        return render_template(
            "review_all_categories.html",
            categories=categories,
            progress=progress,
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
        selected_role = session.get("selected_role", "All Roles")

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
        else:
            debug_log("DEBUG: Review already marked as completed")

        review_timing = _calculate_review_time()
        mr_details = session.get("mr_details", {})

        debug_log("DEBUG: Final review_timing: " + str(review_timing))

        return render_template(
            "summary.html",
            summary=summary_data,
            counts_overall=counts_overall,
            reviewer_name=reviewer_name,
            selected_role=selected_role,
            review_timing=review_timing,
            mr_details=mr_details,
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
            selected_role = session.get("selected_role", "Unknown")
            review_timing = _calculate_review_time()
            mr_details = session.get("mr_details", {})

            html = render_template("report_standalone.html",
                                 summary=summary_data,
                                 counts_overall=counts_overall,
                                 reviewer_name=reviewer_name,
                                 selected_role=selected_role,
                                 review_timing=review_timing,
                                 mr_details=mr_details)
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
        selected_role = session.get("selected_role", "Unknown")
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
            ['Review Started:', review_timing['start_time']],
            ['Review Completed:', review_timing['end_time']],
            ['Duration:', review_timing['duration']]
        ]

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

        if app_config.get('features', {}).get('skip_categories', False):
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

    app.config['app_config'] = app_config

    return app

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='CodeCritique Flask Application')
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

    args = parser.parse_args()

    app = create_app()

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

    print(f"Starting CodeCritique on http://{host}:{port}")
    
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
