import os
import io
import time
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

# Import path utilities
try:
    from utils.path_utils import get_scripts_path, get_checklists_path, get_templates_path, get_project_root
except ImportError:
    # Fallback for when utils module is not available
    import sys
    def get_base_dir() -> str:
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            return sys._MEIPASS  # type: ignore[attr-defined]
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

    # Auto-update checklists and dynamic categories on startup (optional - can be disabled for production)
    try:
        import subprocess
        import sys
        
        # Check if we should auto-update (can be disabled with environment variable)
        # Skip auto-update in portable mode to avoid subprocess issues
        is_portable = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
        if is_portable:
            print("Running in portable mode - skipping auto-update process")
        elif os.environ.get('AUTO_UPDATE_CHECKLISTS', 'true').lower() == 'true':
            # Update dynamic categories first
            print("Updating dynamic categories from Excel files...")
            try:
                dynamic_categories.update_all_configs()
                print("Dynamic categories updated successfully")
            except Exception as e:
                print(f"Dynamic categories update failed: {str(e)}")
            
            # Then update checklists with category-based conversion
            script_path = get_scripts_path("py/auto_update_checklists_category.py")
            if script_path.exists():
                print("Auto-updating checklists with category-based conversion...")
                result = subprocess.run([sys.executable, str(script_path)], 
                                      capture_output=True, text=True, cwd=get_project_root())
                if result.returncode == 0:
                    print("Checklists auto-updated successfully")
                    if result.stdout:
                        print("Update output:", result.stdout.strip())
                else:
                    print(f"Auto-update failed: {result.stderr}")
                    if result.stdout:
                        print("Update output:", result.stdout.strip())
            else:
                print("Auto-update script not found, skipping...")
    except Exception as e:
        print(f"Auto-update error: {str(e)}")

    # Network security middleware
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
        
        # Check if we have any steps, if not, try to auto-refresh from Excel
        if not all_steps:
            # Skip auto-refresh in portable mode
            is_portable = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
            if is_portable:
                print("Portable mode: No steps found, but skipping auto-refresh")
            else:
                print("No steps found, attempting to auto-refresh from Excel files...")
                try:
                    # Try to refresh from Excel files
                    from services.dynamic_categories import dynamic_categories
                    import subprocess
                    import sys
                    
                    # Update dynamic categories first
                    dynamic_categories.update_all_configs()
                    
                    # Run auto-update script
                    script_path = get_scripts_path("py/auto_update_checklists_category.py")
                    if script_path.exists():
                        result = subprocess.run([sys.executable, str(script_path)], 
                                              capture_output=True, text=True, cwd=get_project_root())
                        if result.returncode == 0:
                            print("Auto-refresh successful, reloading config...")
                            # Reload config and try again
                            config = load_roles_config()
                            all_steps = build_all_steps(config)
                        else:
                            print(f"Auto-refresh failed: {result.stderr}")
                except Exception as e:
                    print(f"Auto-refresh error: {str(e)}")
        
        # Filter by selected role if specified
        selected_role = session.get("selected_role")
        if selected_role:
            steps = [step for step in all_steps if step["role_id"] == selected_role]
        else:
            steps = all_steps
            
        return steps

    def _get_categories() -> List[Dict[str, Any]]:
        """Group steps by category for category-based review"""
        steps = _get_steps()
        
        # If no steps found, try auto-refresh
        if not steps:
            print("No steps found in _get_categories, attempting auto-refresh...")
            # The auto-refresh logic is already in _get_steps(), so just return empty for now
            return []
        
        categories = {}
        
        for step in steps:
            # Group by role_id and category_name (not category_id) to merge same MainCategory
            cat_key = f"{step['role_id']}|{step['category_name']}"
            if cat_key not in categories:
                # Generate a consistent category_id based on the category_name
                consistent_category_id = step['category_name'].lower().replace(' ', '_').replace('-', '_')
                categories[cat_key] = {
                    "role_id": step["role_id"],
                    "role_name": step["role_name"],
                    "category_id": consistent_category_id,
                    "category_name": step["category_name"],
                    "item_list": []
                }
            # Add guideline category mapping to each step
            guideline_info = _get_guideline_info_for_checklist_item(step)
            step["guideline_category"] = guideline_info["category"]
            step["suggested_rule_id"] = guideline_info["suggested_rule_id"]
            categories[cat_key]["item_list"].append(step)
        
        return list(categories.values())

    def _calculate_review_time() -> Dict[str, Any]:
        """Calculate review timing information."""
        start_time_str = session.get("review_start_time")
        start_timestamp = session.get("review_start_timestamp")
        
        if not start_time_str or not start_timestamp:
            return {
                "start_time": "Unknown",
                "end_time": "Unknown", 
                "duration": "Unknown",
                "duration_seconds": 0
            }
        
        start_time = datetime.fromisoformat(start_time_str)
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Format duration
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
        
        return {
            "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": duration_str,
            "duration_seconds": total_seconds
        }

    def _compute_summary(steps: List[Dict[str, Any]], responses: Dict[str, Dict[str, Any]]):
        summary: Dict[str, Any] = {}
        counts_overall = {"OK": 0, "NG": 0, "NA": 0, "UNANSWERED": 0, "SKIPPED": 0}
        for step in steps:
            key = f"{step['role_id']}|{step['category_id']}|{step['item_id']}"
            role_id = step["role_id"]
            cat_id = step["category_id"]

            role_bucket = summary.setdefault(role_id, {
                "role_name": step["role_name"],
                "categories": {},
            })
            cat_bucket = role_bucket["categories"].setdefault(cat_id, {
                "category_name": step["category_name"],
                "item_list": [],
                "counts": {"OK": 0, "NG": 0, "NA": 0, "UNANSWERED": 0, "SKIPPED": 0},
            })

            record = {
                "item_text": step["item_text"],
                "response": None,
                "comment": "",
            }

            # Check if the category is skipped first
            if cat_id in responses and "skipped" in responses[cat_id]:
                # Category is skipped, mark all items as SKIPPED
                record["response"] = "SKIPPED"
                record["comment"] = responses[cat_id].get("skip_comment", "")
                cat_bucket["counts"]["SKIPPED"] += 1
                counts_overall["SKIPPED"] += 1
            elif key in responses:
                # Check if this is an item response (has status)
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
        # Get Windows username
        import getpass
        windows_username = getpass.getuser()
        return render_template("start_review.html", config=config, default_username=windows_username)

    @app.route("/guidelines")
    def guidelines():
        """Display Android coding guidelines with filtering capabilities"""
        # Read the guidelines markdown file and parse it
        guidelines_file = "checklists/markdown/guidelines/android_coding_guidelines.md"
        
        if not os.path.exists(guidelines_file):
            return render_template("empty.html", message="Guidelines file not found")
        
        with open(guidelines_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the markdown content to extract guidelines
        guidelines_data = _parse_guidelines_markdown(content)
        
        # Get filter parameters
        category_filter = request.args.get('category', '')
        subcategory_filter = request.args.get('subcategory', '')
        
        # Apply filters
        filtered_guidelines = guidelines_data
        if category_filter:
            filtered_guidelines = [g for g in filtered_guidelines if g['category'].lower() == category_filter.lower()]
        if subcategory_filter:
            filtered_guidelines = [g for g in filtered_guidelines if g['subcategory'].lower() == subcategory_filter.lower()]
        
        # Get unique categories and subcategories for filter dropdowns
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
        # Read the guidelines markdown file and parse it
        guidelines_file = "checklists/markdown/guidelines/android_coding_guidelines.md"
        
        if not os.path.exists(guidelines_file):
            return render_template("empty.html", message="Guidelines file not found")
        
        with open(guidelines_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the guidelines content to extract structured data
        guidelines_data = _parse_guidelines_markdown(content)
        
        # Find the specific guideline by rule ID
        target_guideline = None
        for guideline in guidelines_data:
            if guideline['rule_id'].upper() == rule_id.upper():
                target_guideline = guideline
                break
        
        if not target_guideline:
            return render_template("empty.html", message=f"Guideline {rule_id} not found")
        
        # Get all categories for navigation
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
            
            # Step 1: Update dynamic categories
            print("Refreshing dynamic categories...")
            categories_success = dynamic_categories.update_all_configs()
            
            # Step 2: Run auto-update script with category-based conversion
            print("Refreshing checklists with category-based conversion...")
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
            
            # Get the script path
            script_path = get_scripts_path("py/auto_update_checklists.py")
            
            # Run the auto-update script
            result = subprocess.run([sys.executable, str(script_path)], 
                                  capture_output=True, text=True, cwd=get_project_root())
            
            if result.returncode == 0:
                # Also update dynamic categories
                try:
                    dynamic_categories.update_all_configs()
                except Exception as e:
                    print(f"Warning: Dynamic categories update failed: {e}")
                
                # Clear any cached data
                from services.checklist_loader import load_roles_config
                
                # Return success message
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
        
        # Direct mapping
        if category_id in category_mapping:
            category = category_mapping[category_id]
        else:
            # Fallback based on item text content
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
                category = "Style"  # Default fallback
        
        # Suggest specific rule IDs based on content
        suggested_rule_id = None
        if "retrofit" in item_text or "api" in item_text:
            suggested_rule_id = "AND-023"
        elif "error" in item_text and "handling" in item_text:
            suggested_rule_id = "AND-024"
        elif "memory" in item_text or "leak" in item_text:
            suggested_rule_id = "AND-013"
        elif "test" in item_text and "unit" in item_text:
            suggested_rule_id = "AND-059"
        elif "mvvm" in item_text or "viewmodel" in item_text:
            suggested_rule_id = "AND-038"
        elif "hilt" in item_text or "dependency" in item_text:
            suggested_rule_id = "AND-009"
        elif "log" in item_text:
            suggested_rule_id = "AND-017"
        elif "coroutine" in item_text or "thread" in item_text:
            suggested_rule_id = "AND-020"
        elif "security" in item_text or "keystore" in item_text:
            suggested_rule_id = "AND-027"
        
        return {
            "category": category,
            "suggested_rule_id": suggested_rule_id
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
            
            # Parse category headers (## Category Name)
            if line.startswith('## ') and not line.startswith('### '):
                current_category = line[3:].strip()
                current_subcategory = ""
            
            # Parse subcategory headers (### Sub Category)
            elif line.startswith('### '):
                current_subcategory = line[4:].strip()
            
            # Parse guideline headers (**AND-XXX** (SEVERITY): Description)
            elif line.startswith('**AND-') and '**' in line:
                # Save previous guideline if exists
                if current_guideline:
                    guidelines.append(current_guideline)
                
                # Parse new guideline
                # Extract rule ID and severity
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
            
            # Parse guideline content
            elif current_guideline:
                if line.startswith('  - **Good Example:**'):
                    # Skip the "Good Example:" line and get the next code block
                    pass
                elif line.startswith('  - **Bad Example:**'):
                    # Skip the "Bad Example:" line and get the next code block
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
                    
                    # Determine if this is good or bad example based on context
                    # Look back to find which type this is
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
        
        # Don't forget the last guideline
        if current_guideline:
            guidelines.append(current_guideline)
        
        return guidelines

    @app.route("/start", methods=["POST"])
    def start_review():
        reviewer_name = request.form.get("reviewer_name", "").strip()
        selected_role = request.form.get("selected_role", "").strip()
        single_page_mode = request.form.get("single_page_mode") == "on"
        
        # MR/GitLab details (optional)
        mr_link = request.form.get("mr_link", "").strip()
        branch_name = request.form.get("branch_name", "").strip()
        commit_hash = request.form.get("commit_hash", "").strip()
        project_name = request.form.get("project_name", "").strip()
        
        if not reviewer_name or not selected_role:
            return redirect(url_for("index"))
        
        # Record review start time
        current_time = datetime.now()
        session["review_start_time"] = current_time.isoformat()
        session["review_start_timestamp"] = current_time.timestamp()
        
        session["responses"] = {}
        session["current_category"] = 0
        session["reviewer_name"] = reviewer_name
        session["selected_role"] = selected_role
        session["single_page_mode"] = single_page_mode
        
        # Store MR/GitLab details
        session["mr_details"] = {
            "mr_link": mr_link,
            "branch_name": branch_name,
            "commit_hash": commit_hash,
            "project_name": project_name
        }
        
        # Redirect based on mode
        if single_page_mode:
            return redirect(url_for("review_all_categories"))
        else:
            return redirect(url_for("review_category", idx=0))

    @app.route("/review/all", methods=["GET", "POST"])
    def review_all_categories():
        if request.method == "POST":
            # Handle form submission for all categories
            responses = session.get("responses", {})
            
            # Process all form data
            for key, value in request.form.items():
                if key.startswith("status_"):
                    item_key = key[7:]  # Remove "status_" prefix
                    if item_key not in responses:
                        responses[item_key] = {}
                    responses[item_key]["status"] = value
                elif key.startswith("comment_"):
                    item_key = key[8:]  # Remove "comment_" prefix
                    if item_key not in responses:
                        responses[item_key] = {}
                    responses[item_key]["comment"] = value
                elif key.startswith("category_skip_"):
                    category_id = key[14:]  # Remove "category_skip_" prefix
                    skip_comment = request.form.get(f"category_skip_comment_{category_id}", "")
                    if category_id not in responses:
                        responses[category_id] = {}
                    responses[category_id]["skipped"] = True
                    responses[category_id]["skip_comment"] = skip_comment
            
            session["responses"] = responses
            
            # Check if all categories are completed or skipped
            categories = _get_categories()
            all_completed = True
            for category in categories:
                category_id = category["category_id"]
                category_responses = [key for key in responses.keys() if key.startswith(f"{category['role_id']}|{category_id}|")]
                
                # Check if category is skipped
                if category_id in responses and responses[category_id].get("skipped"):
                    continue
                
                # Check if all items in category are answered
                for item in category["item_list"]:
                    item_key = f"{item['role_id']}|{item['category_id']}|{item['item_id']}"
                    if item_key not in responses or not responses[item_key].get("status"):
                        all_completed = False
                        break
                
                if not all_completed:
                    break
            
            if all_completed:
                return redirect(url_for("summary"))
        
        # GET request - show all categories
        categories = _get_categories()
        if not categories:
            return render_template("empty.html")
        
        # Get saved responses
        saved_responses = session.get("responses", {})
        
        # Calculate progress
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
            
            # Process all form data for this category
            category = categories[idx]
            for item in category["item_list"]:
                item_key = f"{item['role_id']}|{item['category_id']}|{item['item_id']}"
                status = request.form.get(f"status_{item_key}")
                comment = request.form.get(f"comment_{item_key}", "").strip()

                # If no status provided, default to "UNANSWERED"
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
        
        # Get saved responses for this category
        saved_responses = {}
        for item in category["item_list"]:
            item_key = f"{item['role_id']}|{item['category_id']}|{item['item_id']}"
            saved_responses[item_key] = session.get("responses", {}).get(item_key, {})

        # Calculate actual progress based on answered items
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
        steps = _get_steps()
        responses: Dict[str, Dict[str, Any]] = session.get("responses", {})
        summary_data, counts_overall = _compute_summary(steps, responses)
        
        reviewer_name = session.get("reviewer_name", "Unknown")
        selected_role = session.get("selected_role", "All Roles")
        review_timing = _calculate_review_time()
        mr_details = session.get("mr_details", {})
        
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
            
            html = render_template("summary.html", 
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
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import mm

        steps = _get_steps()
        responses: Dict[str, Dict[str, Any]] = session.get("responses", {})
        reviewer_name = session.get("reviewer_name", "Unknown")
        selected_role = session.get("selected_role", "Unknown")
        review_timing = _calculate_review_time()

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        margin_x = 20 * mm
        margin_y = 20 * mm
        y = height - margin_y

        def draw_line(text: str, font_size: int = 10, bold: bool = False):
            nonlocal y
            if y < 30 * mm:
                c.showPage()
                y = height - margin_y
            
            # Handle long text by wrapping
            max_width = width - 2 * margin_x
            c.setFont("Helvetica-Bold" if bold else "Helvetica", font_size)
            
            # Simple text wrapping
            words = text.split()
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                if c.stringWidth(test_line, "Helvetica-Bold" if bold else "Helvetica", font_size) <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                        current_line = word
                    else:
                        lines.append(word)
            
            if current_line:
                lines.append(current_line)
            
            for line in lines:
                if y < 30 * mm:
                    c.showPage()
                    y = height - margin_y
                c.drawString(margin_x, y, line)
                y -= (font_size + 6)

        draw_line("Code Review Report", font_size=16, bold=True)
        draw_line("")
        draw_line(f"Reviewer: {reviewer_name}", font_size=12, bold=True)
        draw_line(f"Role: {selected_role}", font_size=12, bold=True)
        draw_line(f"Review Started: {review_timing['start_time']}", font_size=10)
        draw_line(f"Review Completed: {review_timing['end_time']}", font_size=10)
        draw_line(f"Duration: {review_timing['duration']}", font_size=10)
        draw_line("")

        # Calculate overall statistics
        summary_data, counts_overall = _compute_summary(steps, responses)
        draw_line("Overall Statistics:", font_size=12, bold=True)
        draw_line(f"OK: {counts_overall['OK']}, NG: {counts_overall['NG']}, N/A: {counts_overall['NA']}, Unanswered: {counts_overall['UNANSWERED']}", font_size=10)
        draw_line("")

        current_role = None
        current_cat = None
        for step in steps:
            key = f"{step['role_id']}|{step['category_id']}|{step['item_id']}"
            resp = responses.get(key, {})
            status = resp.get("status", "UNANSWERED")
            comment = resp.get("comment", "")

            if current_role != step["role_id"]:
                draw_line("")
                draw_line(f"Role: {step['role_name']}", font_size=12, bold=True)
                current_role = step["role_id"]
                current_cat = None

            if current_cat != step["category_id"]:
                draw_line(f"Category: {step['category_name']}", font_size=11, bold=True)
                current_cat = step["category_id"]

            item_text = step["item_text"]
            draw_line(f"- [{status}] {item_text}")
            if comment:
                draw_line(f"   Note: {comment}")

        c.showPage()
        c.save()
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name="code_review_report.pdf",
            mimetype="application/pdf",
        )

    # PWA Routes
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
            # Here you would process the offline data
            # For now, just return success
            return {"status": "success", "message": "Offline data synced successfully"}, 200
        except Exception as e:
            return {"status": "error", "message": str(e)}, 500


    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=True)
