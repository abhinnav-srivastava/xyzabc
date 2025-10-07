import json
import os
import sys
import re
from typing import Dict, List, Any
from functools import lru_cache
from pathlib import Path

# Define BASE_DIR for path resolution
def get_base_dir() -> str:
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS  # type: ignore[attr-defined]
    return os.path.dirname(os.path.dirname(__file__))

BASE_DIR = get_base_dir()

# Import path utilities
try:
    from utils.path_utils import get_roles_config_path, get_checklists_path, get_project_root
except ImportError:
    # Fallback for when utils module is not available
    def get_base_dir() -> str:
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            return sys._MEIPASS  # type: ignore[attr-defined]
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
            
            # Check for main category header (# or ##)
            if (stripped.startswith("# ") and not stripped.startswith("## ")) or (stripped.startswith("## ") and not stripped.startswith("### ")):
                # Save previous item if exists
                if current_item and current_category:
                    if current_category not in categories:
                        categories[current_category] = []
                    categories[current_category].append(current_item)
                    current_item = None
                
                # Start new category
                current_category = stripped[2:].strip() if stripped.startswith("# ") else stripped[3:].strip()
                continue
                
            # Check for main item (starts with - or * or **number.** and is not indented)
            if ((stripped.startswith("- ") or stripped.startswith("* ")) and not line.startswith("  ")) or re.match(r'\*\*\d+\.\*\*', stripped):
                # Save previous item if exists
                if current_item and current_category:
                    if current_category not in categories:
                        categories[current_category] = []
                    categories[current_category].append(current_item)
                
                # Start new item
                if re.match(r'\*\*\d+\.\*\*', stripped):
                    # Handle **number.** format
                    text = re.sub(r'\*\*\d+\.\*\*', '', stripped).strip()
                else:
                    text = stripped[2:].strip()
                
                # Parse new format: **MUST:**, **GOOD:**, **SUGGESTED:**
                import re
                item_type = "good"  # default
                
                # Check for **MUST:**, **GOOD:**, **SUGGESTED:** patterns
                must_match = re.match(r'\*\*MUST:\*\*(.*)', text)
                good_match = re.match(r'\*\*GOOD:\*\*(.*)', text)
                suggested_match = re.match(r'\*\*SUGGESTED:\*\*(.*)', text)
                
                if must_match:
                    item_type = "must"
                    text = must_match.group(1).strip()
                elif good_match:
                    item_type = "good"
                    text = good_match.group(1).strip()
                elif suggested_match:
                    item_type = "optional"
                    text = suggested_match.group(1).strip()
                else:
                    # Fallback to old pattern detection
                    if any(keyword in text.lower() for keyword in ["must", "required", "critical", "essential", "mandatory"]):
                        item_type = "must"
                    elif any(keyword in text.lower() for keyword in ["should", "recommended", "preferred", "optional", "nice to have"]):
                        item_type = "optional"
                
                current_item = {
                    "id": str(len(categories.get(current_category, [])) if current_category else 0),
                    "text": text,
                    "type": item_type,
                }
            # Check for details (starts with spaces or tabs, then - or *)
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
            # Skip headers
            elif stripped.startswith("#"):
                continue
    
    # Add the last item if exists
    if current_item and current_category:
        if current_category not in categories:
            categories[current_category] = []
        categories[current_category].append(current_item)
    
    # If no categories found, treat the whole file as one category
    if not categories and current_item:
        categories["General"] = [current_item]
    
    # Convert details list to HTML for all items
    for category_items in categories.values():
        for item in category_items:
            if "details" in item:
                details_html = "<ul class='mb-0'>"
                for detail in item["details"]:
                    # Convert Markdown formatting to HTML
                    detail_html = detail
                    # Convert **text** to <strong>text</strong>
                    import re
                    detail_html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', detail_html)
                    details_html += f"<li>{detail_html}</li>"
                details_html += "</ul>"
                item["item_details"] = details_html
                del item["details"]  # Remove the list version
    
    # Return all items from all categories as a flat list
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
            
            # Check for main category header (# or ##)
            if (stripped.startswith("# ") and not stripped.startswith("## ")) or (stripped.startswith("## ") and not stripped.startswith("### ")):
                # Save previous item if exists
                if current_item and current_category:
                    if current_category not in categories:
                        categories[current_category] = []
                    categories[current_category].append(current_item)
                    current_item = None
                
                # Start new category
                current_category = stripped[2:].strip() if stripped.startswith("# ") else stripped[3:].strip()
                continue
                
            # Check for main item (starts with - or * or **number.** and is not indented)
            if ((stripped.startswith("- ") or stripped.startswith("* ")) and not line.startswith("  ")) or re.match(r'\*\*\d+\.\*\*', stripped):
                # Save previous item if exists
                if current_item and current_category:
                    if current_category not in categories:
                        categories[current_category] = []
                    categories[current_category].append(current_item)
                
                # Start new item
                if re.match(r'\*\*\d+\.\*\*', stripped):
                    # Handle **number.** format
                    text = re.sub(r'\*\*\d+\.\*\*', '', stripped).strip()
                else:
                    text = stripped[2:].strip()
                
                # Parse new format: **MUST:**, **GOOD:**, **SUGGESTED:**
                import re
                item_type = "good"  # default
                
                # Check for **MUST:**, **GOOD:**, **SUGGESTED:** patterns
                must_match = re.match(r'\*\*MUST:\*\*(.*)', text)
                good_match = re.match(r'\*\*GOOD:\*\*(.*)', text)
                suggested_match = re.match(r'\*\*SUGGESTED:\*\*(.*)', text)
                
                if must_match:
                    item_type = "must"
                    text = must_match.group(1).strip()
                elif good_match:
                    item_type = "good"
                    text = good_match.group(1).strip()
                elif suggested_match:
                    item_type = "optional"
                    text = suggested_match.group(1).strip()
                else:
                    # Fallback to old pattern detection
                    if any(keyword in text.lower() for keyword in ["must", "required", "critical", "essential", "mandatory"]):
                        item_type = "must"
                    elif any(keyword in text.lower() for keyword in ["should", "recommended", "preferred", "optional", "nice to have"]):
                        item_type = "optional"
                
                current_item = {
                    "id": str(len(categories.get(current_category, [])) if current_category else 0),
                    "text": text,
                    "type": item_type,
                }
            # Check for details (starts with spaces or tabs, then - or *)
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
            # Skip headers
            elif stripped.startswith("#"):
                continue
    
    # Add the last item if exists
    if current_item and current_category:
        if current_category not in categories:
            categories[current_category] = []
        categories[current_category].append(current_item)
    
    # If no categories found, treat the whole file as one category
    if not categories and current_item:
        categories["General"] = [current_item]
    
    # Convert details list to HTML for all items
    for category_items in categories.values():
        for item in category_items:
            if "details" in item:
                details_html = "<ul class='mb-0'>"
                for detail in item["details"]:
                    # Convert Markdown formatting to HTML
                    detail_html = detail
                    # Convert **text** to <strong>text</strong>
                    import re
                    detail_html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', detail_html)
                    details_html += f"<li>{detail_html}</li>"
                details_html += "</ul>"
                item["item_details"] = details_html
                del item["details"]  # Remove the list version
    
    return categories


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
        # For Excel files, treat as single category
        sheet = category.get("sheet")
        items = _load_excel_items(abs_path, sheet_name=sheet)
        return {category.get("name", "General"): items}
    # Unknown type: try markdown parsing as fallback
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
            
            # Load items with subcategories
            subcategories = load_category_items_with_subcategories(category)
            
            # If no subcategories found, use the original method
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
                # Create separate steps for each subcategory
                for subcat_name, items in subcategories.items():
                    # Create a unique category ID for each subcategory
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
