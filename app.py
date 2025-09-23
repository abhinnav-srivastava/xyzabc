import os
import io
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple

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

from services.checklist_loader import (
    load_roles_config,
    build_all_steps,
)


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

    def _get_steps() -> List[Dict[str, Any]]:
        config = load_roles_config()
        all_steps = build_all_steps(config)
        
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
        categories = {}
        
        for step in steps:
            cat_key = f"{step['role_id']}|{step['category_id']}"
            if cat_key not in categories:
                categories[cat_key] = {
                    "role_id": step["role_id"],
                    "role_name": step["role_name"],
                    "category_id": step["category_id"],
                    "category_name": step["category_name"],
                    "item_list": []
                }
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
        counts_overall = {"OK": 0, "NG": 0, "NA": 0, "UNANSWERED": 0}
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
                "counts": {"OK": 0, "NG": 0, "NA": 0, "UNANSWERED": 0},
            })

            record = {
                "item_text": step["item_text"],
                "response": None,
                "comment": "",
            }

            if key in responses:
                record["response"] = responses[key]["status"]
                record["comment"] = responses[key].get("comment", "")
                cat_bucket["counts"][record["response"]] += 1
                counts_overall[record["response"]] += 1
            else:
                record["response"] = "UNANSWERED"
                cat_bucket["counts"]["UNANSWERED"] += 1
                counts_overall["UNANSWERED"] += 1

            cat_bucket["item_list"].append(record)
        return summary, counts_overall

    @app.route("/")
    def index():
        config = load_roles_config()
        # Get Windows username
        import getpass
        windows_username = getpass.getuser()
        return render_template("index.html", config=config, default_username=windows_username)

    @app.route("/start", methods=["POST"])
    def start_review():
        reviewer_name = request.form.get("reviewer_name", "").strip()
        selected_role = request.form.get("selected_role", "").strip()
        
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
        return redirect(url_for("review_category", idx=0))

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

        progress = {
            "current": idx + 1,
            "total": total,
            "percent": int(((idx + 1) / total) * 100),
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
        
        return render_template(
            "summary.html",
            summary=summary_data,
            counts_overall=counts_overall,
            reviewer_name=reviewer_name,
            selected_role=selected_role,
            review_timing=review_timing,
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
            
            html = render_template("summary.html", 
                                 summary=summary_data, 
                                 counts_overall=counts_overall,
                                 reviewer_name=reviewer_name,
                                 selected_role=selected_role,
                                 review_timing=review_timing)
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


    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
