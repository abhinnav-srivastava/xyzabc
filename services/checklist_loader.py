import json
import os
import sys
import re
from typing import Dict, List, Any
from functools import lru_cache
from pathlib import Path

\
def get_base_dir() -> str:
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(__file__))
BASE_DIR = get_base_dir()

\
try:
    from utils.path_utils import get_roles_config_path, get_checklists_path, get_project_root
except ImportError:
    \
    def get_base_dir() -> str:
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            return sys._MEIPASS
        return os.path.dirname(os.path.dirname(__file__))
    def get_roles_config_path() -> Path:
        return Path(get_base_dir()) / "config" / "roles.json"

    def get_checklists_path(subpath: str = "") -> Path:
        base_path = Path(get_base_dir()) / "checklists"
        if subpath:
            return base_path / subpath
        return base_path

    def get_project_root() -> Path:
        return Path(get_base_dir())

CONFIG_PATH = get_roles_config_path()

def load_roles_config() -> Dict[str, Any]:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

@lru_cache(maxsize=128)
def _load_markdown_items(file_path: str) -> List[Dict[str, Any]]:
    """Load items from markdown file, treating each ## section as a separate category"""
    import re
    categories = {}
    current_category = None
    current_item = None

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue

            if (stripped.startswith("# ") and not stripped.startswith("## ")) or (stripped.startswith("## ") and not stripped.startswith("### ")):
                \
                if current_item and current_category:
                    if current_category not in categories:
                        categories[current_category] = []
                    categories[current_category].append(current_item)
                    current_item = None

                current_category = stripped[2:].strip() if stripped.startswith("# ") else stripped[3:].strip()
                continue

            if ((stripped.startswith("- ") or stripped.startswith("* ")) and not line.startswith("  ")) or re.match(r'\*\*\d+\.\*\*', stripped):
                \
                if current_item and current_category:
                    if current_category not in categories:
                        categories[current_category] = []
                    categories[current_category].append(current_item)

                if re.match(r'\*\*\d+\.\*\*', stripped):
                    \
                    text = re.sub(r'\*\*\d+\.\*\*', '', stripped).strip()
                else:
                    text = stripped[2:].strip()

                import re
                item_type = "good"
                \
\
                must_match = re.match(r'MUST:\s*(.*)', text)
                recommended_match = re.match(r'RECOMMENDED:\s*(.*)', text)
                good_match = re.match(r'GOOD:\s*(.*)', text)
                optional_match = re.match(r'OPTIONAL:\s*(.*)', text)

                if must_match:
                    item_type = "must"
                    text = must_match.group(1).strip()
                elif recommended_match:
                    item_type = "good"
                    text = recommended_match.group(1).strip()
                elif good_match:
                    item_type = "good"
                    text = good_match.group(1).strip()
                elif optional_match:
                    item_type = "optional"
                    text = optional_match.group(1).strip()
                else:
                    \
                    if any(keyword in text.lower() for keyword in ["must", "required", "critical", "essential", "mandatory"]):
                        item_type = "must"
                    elif any(keyword in text.lower() for keyword in ["should", "recommended", "preferred", "optional", "nice to have"]):
                        item_type = "optional"

                if " - " in text:
                    subcategory, description = text.split(" - ", 1)
                    subcategory = subcategory.strip()
                    description = description.strip()
                else:
                    subcategory = text.strip()
                    description = ""

                current_item = {
                    "id": str(len(categories.get(current_category, [])) if current_category else 0),
                    "text": text,
                    "subcategory": subcategory,
                    "description": description,
                    "type": item_type,
                }
            elif current_item and (line.startswith("  - ") or line.startswith("  * ") or
                                 line.startswith("\t- ") or line.startswith("\t* ")):
                details_text = line.strip()
                if details_text.startswith("  - "):
                    details_text = details_text[4:]
                elif details_text.startswith("  * "):
                    details_text = details_text[4:]
                elif details_text.startswith("\t- "):
                    details_text = details_text[3:]
                elif details_text.startswith("\t* "):
                    details_text = details_text[3:]

                if "details" not in current_item:
                    current_item["details"] = []
                current_item["details"].append(details_text)
            elif stripped.startswith("#"):
                continue

    if current_item and current_category:
        if current_category not in categories:
            categories[current_category] = []
        categories[current_category].append(current_item)

    if not categories and current_item:
        categories["General"] = [current_item]

    for category_items in categories.values():
        for item in category_items:
            if "details" in item:
                details_html = "<ul class='mb-0'>"
                seen_measurements = set()
                rule_reference = None
                \
                for detail in item["details"]:
                    \
                    if detail.strip().startswith("Rule Reference:") or detail.strip().startswith("**Rule Reference:**") or detail.strip().startswith("- Rule Reference:"):
                        \
                        rule_ref_text = detail.replace("Rule Reference:", "").replace("**Rule Reference:**", "").replace("- Rule Reference:", "").strip()
                        \
                        rule_ref_text = rule_ref_text.lstrip("- ").strip()
                        if rule_ref_text and rule_ref_text.lower() not in ['nan', 'none', '']:
                            rule_reference = rule_ref_text
                        continue
                    detail_html = detail
                    \
                    import re
                    detail_html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', detail_html)

                    \
                    if detail_html.startswith("<strong>How to Measure:</strong>"):
                        measurement_text = detail_html.replace("<strong>How to Measure:</strong>", "").strip()
                        if measurement_text in seen_measurements:
                            continue
                        seen_measurements.add(measurement_text)
                    details_html += f"<li>{detail_html}</li>"

                details_html += "</ul>"
                item["item_details"] = details_html

                \
                if rule_reference:
                    item["rule_reference"] = rule_reference

                del item["details"]
    all_items = []
    for category_items in categories.values():
        all_items.extend(category_items)

    return all_items

def _load_markdown_categories(file_path: str) -> Dict[str, List[Dict[str, Any]]]:
    """Load items from markdown file, returning categories as a dictionary"""
    import re
    categories = {}
    current_category = None
    current_item = None

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue

            if (stripped.startswith("# ") and not stripped.startswith("## ")) or (stripped.startswith("## ") and not stripped.startswith("### ")):
                \
                if current_item and current_category:
                    if current_category not in categories:
                        categories[current_category] = []
                    categories[current_category].append(current_item)
                    current_item = None

                current_category = stripped[2:].strip() if stripped.startswith("# ") else stripped[3:].strip()
                continue

            if ((stripped.startswith("- ") or stripped.startswith("* ")) and not line.startswith("  ")) or re.match(r'\*\*\d+\.\*\*', stripped):
                \
                if current_item and current_category:
                    if current_category not in categories:
                        categories[current_category] = []
                    categories[current_category].append(current_item)

                if re.match(r'\*\*\d+\.\*\*', stripped):
                    \
                    text = re.sub(r'\*\*\d+\.\*\*', '', stripped).strip()
                else:
                    text = stripped[2:].strip()

                import re
                item_type = "good"
                \
\
                must_match = re.match(r'MUST:\s*(.*)', text)
                recommended_match = re.match(r'RECOMMENDED:\s*(.*)', text)
                good_match = re.match(r'GOOD:\s*(.*)', text)
                optional_match = re.match(r'OPTIONAL:\s*(.*)', text)

                if must_match:
                    item_type = "must"
                    text = must_match.group(1).strip()
                elif recommended_match:
                    item_type = "good"
                    text = recommended_match.group(1).strip()
                elif good_match:
                    item_type = "good"
                    text = good_match.group(1).strip()
                elif optional_match:
                    item_type = "optional"
                    text = optional_match.group(1).strip()
                else:
                    \
                    if any(keyword in text.lower() for keyword in ["must", "required", "critical", "essential", "mandatory"]):
                        item_type = "must"
                    elif any(keyword in text.lower() for keyword in ["should", "recommended", "preferred", "optional", "nice to have"]):
                        item_type = "optional"

                if " - " in text:
                    subcategory, description = text.split(" - ", 1)
                    subcategory = subcategory.strip()
                    description = description.strip()
                else:
                    subcategory = text.strip()
                    description = ""

                current_item = {
                    "id": str(len(categories.get(current_category, [])) if current_category else 0),
                    "text": text,
                    "subcategory": subcategory,
                    "description": description,
                    "type": item_type,
                }
            elif current_item and (line.startswith("  - ") or line.startswith("  * ") or
                                 line.startswith("\t- ") or line.startswith("\t* ")):
                details_text = line.strip()
                if details_text.startswith("  - "):
                    details_text = details_text[4:]
                elif details_text.startswith("  * "):
                    details_text = details_text[4:]
                elif details_text.startswith("\t- "):
                    details_text = details_text[3:]
                elif details_text.startswith("\t* "):
                    details_text = details_text[3:]

                if "details" not in current_item:
                    current_item["details"] = []
                current_item["details"].append(details_text)
            elif stripped.startswith("#"):
                continue

    if current_item and current_category:
        if current_category not in categories:
            categories[current_category] = []
        categories[current_category].append(current_item)

    if not categories and current_item:
        categories["General"] = [current_item]

    for category_items in categories.values():
        for item in category_items:
            if "details" in item:
                details_html = "<ul class='mb-0'>"
                seen_measurements = set()
                rule_reference = None
                \
                for detail in item["details"]:
                    \
                    if detail.strip().startswith("Rule Reference:") or detail.strip().startswith("**Rule Reference:**") or detail.strip().startswith("- Rule Reference:"):
                        \
                        rule_ref_text = detail.replace("Rule Reference:", "").replace("**Rule Reference:**", "").replace("- Rule Reference:", "").strip()
                        \
                        rule_ref_text = rule_ref_text.lstrip("- ").strip()
                        if rule_ref_text and rule_ref_text.lower() not in ['nan', 'none', '']:
                            rule_reference = rule_ref_text
                        continue
                    detail_html = detail
                    \
                    import re
                    detail_html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', detail_html)

                    \
                    if detail_html.startswith("<strong>How to Measure:</strong>"):
                        measurement_text = detail_html.replace("<strong>How to Measure:</strong>", "").strip()
                        if measurement_text in seen_measurements:
                            continue
                        seen_measurements.add(measurement_text)
                    details_html += f"<li>{detail_html}</li>"

                details_html += "</ul>"
                item["item_details"] = details_html

                \
                if rule_reference:
                    item["rule_reference"] = rule_reference

                del item["details"]
    return categories

@lru_cache(maxsize=64)
def _load_excel_items(file_path: str, sheet_name: str = None) -> List[Dict[str, Any]]:
    import pandas as pd
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    \
\
    normalized_cols = {c.lower().strip(): c for c in df.columns}

    \
\
    crit_col = normalized_cols.get("description") or normalized_cols.get("criteria")
    how_to_measure_col = normalized_cols.get("how to measure")
    severity_col = normalized_cols.get("severity")
    rule_ref_col = normalized_cols.get("rule reference")
    additional_info_col = normalized_cols.get("additional info")
    category_col = normalized_cols.get("category")
    subcategory_col = normalized_cols.get("subcategory")

    \
\
    skip_how_to_measure_in_details = True

    \
    if crit_col is None:
        crit_col = df.columns[0]

    items: List[Dict[str, Any]] = []
    for idx, row in df.iterrows():
        text = str(row.get(crit_col, "")).strip()
        if not text or text.lower() in ['nan', 'none', '']:
            continue

        item = {
            "id": str(len(items)),
            "text": text,
        }

        \
        details = []

\
\

        \
        if severity_col and severity_col in row:
            severity = str(row[severity_col]).strip()
            if severity and severity.lower() not in ['nan', 'none', '']:
                details.append(f"Severity: {severity}")

        if rule_ref_col and rule_ref_col in row:
            rule_ref = str(row[rule_ref_col]).strip()
            if rule_ref and rule_ref.lower() not in ['nan', 'none', '']:
                item["rule_reference"] = rule_ref

        if additional_info_col and additional_info_col in row:
            additional_info = str(row[additional_info_col]).strip()
            if additional_info and additional_info.lower() not in ['nan', 'none', '']:
                details.append(f"Additional Info: {additional_info}")

        if category_col and category_col in row:
            category = str(row[category_col]).strip()
            if category and category.lower() not in ['nan', 'none', '']:
                details.append(f"Category: {category}")

        if subcategory_col and subcategory_col in row:
            subcategory = str(row[subcategory_col]).strip()
            if subcategory and subcategory.lower() not in ['nan', 'none', '']:
                details.append(f"SubCategory: {subcategory}")

        if details:
            \
            details_html = "<ul class='mb-0'>"
            for detail in details:
                details_html += f"<li>{detail}</li>"
            details_html += "</ul>"
            item["item_details"] = details_html

        item_type = "good"
        if severity_col and severity_col in row:
            severity = str(row[severity_col]).strip().lower()
            if severity in ["must", "critical", "high", "required"]:
                item_type = "must"
            elif severity in ["should", "medium", "recommended"]:
                item_type = "good"
            elif severity in ["optional", "low", "nice to have"]:
                item_type = "optional"
        else:
            \
            text_lower = text.lower()
            if any(keyword in text_lower for keyword in ["must", "required", "critical", "essential", "mandatory"]):
                item_type = "must"
            elif any(keyword in text_lower for keyword in ["should", "recommended", "preferred", "optional", "nice to have"]):
                item_type = "optional"

        item["type"] = item_type
        items.append(item)

    return items

def load_category_items(category: Dict[str, Any]) -> List[Dict[str, Any]]:
    cat_type = category.get("type", "markdown").lower()
    path = category.get("path")
    if not path:
        return []
    abs_path = path if os.path.isabs(path) else os.path.join(BASE_DIR, path)
    if not os.path.exists(abs_path):
        return []
    if cat_type == "markdown":
        return _load_markdown_items(abs_path)
    if cat_type in ("excel", "xlsx"):
        sheet = category.get("sheet")
        return _load_excel_items(abs_path, sheet_name=sheet)
    return _load_markdown_items(abs_path)

def load_category_items_with_subcategories(category: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """Load items from category, returning subcategories as a dictionary"""
    cat_type = category.get("type", "markdown").lower()
    path = category.get("path")
    if not path:
        return {}
    abs_path = path if os.path.isabs(path) else os.path.join(BASE_DIR, path)
    if not os.path.exists(abs_path):
        return {}
    if cat_type == "markdown":
        return _load_markdown_categories(abs_path)
    if cat_type in ("excel", "xlsx"):
        \
        sheet = category.get("sheet")
        items = _load_excel_items(abs_path, sheet_name=sheet)
        return {category.get("name", "General"): items}
    return _load_markdown_categories(abs_path)

def build_all_steps(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    steps: List[Dict[str, Any]] = []
    roles = config.get("roles", [])
    for role in roles:
        role_id = role.get("id")
        role_name = role.get("name", role_id)
        for category in role.get("categories", []):
            cat_id = category.get("id")
            cat_name = category.get("name", cat_id)

            \
            subcategories = load_category_items_with_subcategories(category)

            \
            if not subcategories:
                items = load_category_items(category)
                for item in items:
                    steps.append({
                        "role_id": role_id,
                        "role_name": role_name,
                        "category_id": cat_id,
                        "category_name": cat_name,
                        "item_id": item.get("id"),
                        "item_text": item.get("text", ""),
                        "item_description": item.get("description", ""),
                        "item_details": item.get("item_details", ""),
                        "item_type": item.get("type", "good"),
                    })
            else:
                \
                for subcat_name, items in subcategories.items():
                    \
                    subcat_id = f"{cat_id}_{subcat_name.lower().replace(' ', '_').replace('-', '_')}"
                    for item in items:
                        steps.append({
                            "role_id": role_id,
                            "role_name": role_name,
                            "category_id": subcat_id,
                            "category_name": subcat_name,
                            "item_id": item.get("id"),
                            "item_text": item.get("text", ""),
                            "item_description": item.get("description", ""),
                            "item_details": item.get("item_details", ""),
                            "item_type": item.get("type", "good"),
                        })
    return steps
