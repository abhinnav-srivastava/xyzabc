import json
import os
import sys
from typing import Dict, List, Any
from functools import lru_cache


def get_base_dir() -> str:
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS  # type: ignore[attr-defined]
    return os.path.dirname(os.path.dirname(__file__))


BASE_DIR = get_base_dir()
CONFIG_PATH = os.path.join(BASE_DIR, "config", "roles.json")


def load_roles_config() -> Dict[str, Any]:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=128)
def _load_markdown_items(file_path: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    current_item = None
    
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
                
            # Check for main item (starts with - or *)
            if stripped.startswith("- ") or stripped.startswith("* "):
                # Save previous item if exists
                if current_item:
                    items.append(current_item)
                
                # Start new item
                text = stripped[2:].strip()
                
                # Determine item type based on text patterns
                item_type = "good"  # default
                if any(keyword in text.lower() for keyword in ["must", "required", "critical", "essential", "mandatory"]):
                    item_type = "must"
                elif any(keyword in text.lower() for keyword in ["should", "recommended", "preferred", "optional", "nice to have"]):
                    item_type = "optional"
                
                current_item = {
                    "id": str(len(items)),
                    "text": text,
                    "type": item_type,
                }
            # Check for details (starts with spaces or tabs, then - or *)
            elif current_item and (stripped.startswith("  - ") or stripped.startswith("  * ") or 
                                 stripped.startswith("\t- ") or stripped.startswith("\t* ")):
                details_text = stripped.strip()
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
            # Skip headers
            elif stripped.startswith("#"):
                continue
            # Treat as main item if no current item
            elif not current_item:
                # Determine item type based on text patterns
                item_type = "good"  # default
                if any(keyword in stripped.lower() for keyword in ["must", "required", "critical", "essential", "mandatory"]):
                    item_type = "must"
                elif any(keyword in stripped.lower() for keyword in ["should", "recommended", "preferred", "optional", "nice to have"]):
                    item_type = "optional"
                
                current_item = {
                    "id": str(len(items)),
                    "text": stripped,
                    "type": item_type,
                }
    
    # Add the last item
    if current_item:
        items.append(current_item)
    
    # Convert details list to HTML
    for item in items:
        if "details" in item:
            details_html = "<ul class='mb-0'>"
            for detail in item["details"]:
                details_html += f"<li>{detail}</li>"
            details_html += "</ul>"
            item["item_details"] = details_html
            del item["details"]  # Remove the list version
    
    return items


@lru_cache(maxsize=64)
def _load_excel_items(file_path: str, sheet_name: str = None) -> List[Dict[str, Any]]:  # type: ignore[override]
    import pandas as pd
    df = pd.read_excel(file_path, sheet_name=sheet_name)  # type: ignore[arg-type]
    # Expect at least a 'criteria' column; optional 'description'
    normalized_cols = {c.lower(): c for c in df.columns}
    crit_col = normalized_cols.get("criteria")
    desc_col = normalized_cols.get("description")
    if crit_col is None:
        # fallback: use first column as criteria
        crit_col = df.columns[0]
    items: List[Dict[str, Any]] = []
    for idx, row in df.iterrows():
        text = str(row.get(crit_col, "")).strip()
        if not text:
            continue
        item = {
            "id": str(len(items)),
            "text": text,
        }
        if desc_col is not None and desc_col in row and str(row[desc_col]).strip():
            item["description"] = str(row[desc_col]).strip()
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
    # Unknown type: try markdown parsing as fallback
    return _load_markdown_items(abs_path)


def build_all_steps(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    steps: List[Dict[str, Any]] = []
    roles = config.get("roles", [])
    for role in roles:
        role_id = role.get("id")
        role_name = role.get("name", role_id)
        for category in role.get("categories", []):
            cat_id = category.get("id")
            cat_name = category.get("name", cat_id)
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
    return steps
