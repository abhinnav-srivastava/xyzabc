\
"""
Auto-update script for checklists with category-based conversion
Converts Excel files to markdown, grouping by MainCategory column
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
import shutil

\
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def get_project_root():
    """Get the project root directory"""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def convert_excel_by_category(excel_file: str, role_dir: str, markdown_dir: str) -> bool:
    """
    Convert Excel file to markdown format, grouping by MainCategory column.
    Creates one consolidated markdown file with all categories for the role.
    """
    try:
        \
        df = pd.read_excel(excel_file)

        \
        category_column = None
        if 'Main Category' in df.columns:
            category_column = 'Main Category'
        elif 'Category' in df.columns:
            category_column = 'Category'
        else:
            print(f"Error: No Category or Main Category column found in {excel_file}")
            print(f"Available columns: {list(df.columns)}")
            return False

        categories = {}

        for _, row in df.iterrows():
            main_category = str(row.get(category_column, '')).strip()
            if main_category and main_category.lower() not in ['nan', 'none', '']:
                if main_category not in categories:
                    categories[main_category] = []
                categories[main_category].append(row)

        if not categories:
            print(f"Warning: No valid Category values found in {excel_file}")
            return False

        markdown_filename = f"{role_dir}_consolidated.md"
        markdown_path = Path(markdown_dir) / role_dir / markdown_filename

        \
        markdown_path.parent.mkdir(parents=True, exist_ok=True)

        \
        markdown_content = generate_consolidated_markdown(categories)

        \
        try:
            with open(markdown_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            print(f"Created: {markdown_path}")
            print(f"Successfully converted {excel_file} -> {len(categories)} categories in consolidated file")
            return True
        except Exception as e:
            print(f"Error writing {markdown_path}: {e}")
            return False

    except Exception as e:
        print(f"Error processing {excel_file}: {e}")
        return False

def generate_category_markdown(category_name: str, rows: List[pd.Series]) -> str:
    """Generate markdown content for a specific category"""
    markdown_lines = []

    \
    markdown_lines.append(f"# {category_name}")
    markdown_lines.append("")

    \
    for row in rows:
        \
        sr_no = str(row.get('SrNo', row.get('Sr.No.', ''))).strip()
        sub_category = str(row.get('SubCategory', row.get('Sub Category', ''))).strip()
        description = str(row.get('Description', '')).strip()
        how_to_measure = str(row.get('How to Measure', '')).strip()
        severity = str(row.get('Severity', '')).strip()
        rule_reference = str(row.get('Rule-Reference', '')).strip()
        additional_info = str(row.get('AdditionalInfo', '')).strip()

        \
        if not sub_category or sub_category.lower() in ['nan', 'none', '']:
            continue

        item_type = "GOOD"
        if severity and severity.lower().strip() not in ['nan', 'none', '']:
            severity_lower = severity.lower().strip()
            if severity_lower in ['must', 'required', 'critical', 'essential', 'mandatory']:
                item_type = "MUST"
            elif severity_lower in ['good', 'recommended', 'should', 'prefer']:
                item_type = "GOOD"
            elif severity_lower in ['suggested', 'optional', 'nice to have', 'consider', 'may']:
                item_type = "OPTIONAL"

        if sr_no and sr_no.lower() not in ['nan', 'none', '']:
            markdown_lines.append(f"**{sr_no}.** {sub_category} ({item_type})")
        else:
            markdown_lines.append(f"- {sub_category} ({item_type})")

        details_section = []

        \
        if description and description.lower() not in ['nan', 'none', '']:
            details_section.append(f"  - **Description:** {description}")

        if how_to_measure and how_to_measure.lower() not in ['nan', 'none', '']:
            details_section.append(f"  - How to Measure: {how_to_measure}")

\

        if additional_info and additional_info.lower() not in ['nan', 'none', '']:
            details_section.append(f"  - Additional Info: {additional_info}")

        if details_section:
            markdown_lines.extend(details_section)

        markdown_lines.append("")

    return '\n'.join(markdown_lines)

def generate_consolidated_markdown(categories: Dict[str, List[pd.Series]]) -> str:
    """Generate consolidated markdown content with all categories"""
    markdown_lines = []

    \
    markdown_lines.append("# Self Review")
    markdown_lines.append("")

    \
    for category_name, rows in categories.items():
        \
        markdown_lines.append(f"## {category_name}")
        markdown_lines.append("")

        \
        for row in rows:
            \
            sr_no = str(row.get('SrNo', row.get('Sr.No.', ''))).strip()
            sub_category = str(row.get('SubCategory', row.get('Sub Category', ''))).strip()
            description = str(row.get('Description', '')).strip()
            how_to_measure = str(row.get('How to Measure', '')).strip()
            severity = str(row.get('Severity', '')).strip()
            rule_reference = str(row.get('Rule-Reference', '')).strip()
            additional_info = str(row.get('AdditionalInfo', '')).strip()

            \
            if not sub_category or sub_category.lower() in ['nan', 'none', '']:
                continue

            item_type = "GOOD"
            if severity and severity.lower().strip() not in ['nan', 'none', '']:
                severity_lower = severity.lower().strip()
                if severity_lower in ['must', 'required', 'critical', 'essential', 'mandatory']:
                    item_type = "MUST"
                elif severity_lower in ['good', 'recommended', 'should', 'prefer']:
                    item_type = "RECOMMENDED"
                elif severity_lower in ['suggested', 'optional', 'nice to have', 'consider', 'may']:
                    item_type = "OPTIONAL"

            markdown_lines.append(f"- {item_type}: {sub_category} - {description}")

            \
            details_section = []

            \
\
            if how_to_measure and how_to_measure.lower() not in ['nan', 'none', '']:
                details_section.append(f"  - How to Measure: {how_to_measure}")

            if rule_reference and rule_reference.lower() not in ['nan', 'none', '']:
                details_section.append(f"  - Rule Reference: {rule_reference}")

            if additional_info and additional_info.lower() not in ['nan', 'none', '']:
                details_section.append(f"  - Additional Info: {additional_info}")

            if details_section:
                markdown_lines.extend(details_section)

            markdown_lines.append("")

    return '\n'.join(markdown_lines)

def convert_role_excel_files(excel_files: List[Path], role_name: str, markdown_dir: str) -> bool:
    """
    Convert all Excel files for a role into a single consolidated markdown file.
    """
    try:
        all_categories = {}

        \
        for excel_file in excel_files:
            print(f"Processing {excel_file}...")

            \
            df = pd.read_excel(excel_file)

            \
            category_column = None
            if 'Main Category' in df.columns:
                category_column = 'Main Category'
            elif 'Category' in df.columns:
                category_column = 'Category'
            else:
                print(f"Warning: No Category or Main Category column found in {excel_file}")
                print(f"Available columns: {list(df.columns)}")
                continue

            for _, row in df.iterrows():
                main_category = str(row.get(category_column, '')).strip()
                if main_category and main_category.lower() not in ['nan', 'none', '']:
                    if main_category not in all_categories:
                        all_categories[main_category] = []
                    all_categories[main_category].append(row)

        if not all_categories:
            print(f"Warning: No valid Category values found for role {role_name}")
            return False

        markdown_filename = f"{role_name}_consolidated.md"
        markdown_path = Path(markdown_dir) / role_name / markdown_filename

        \
        markdown_path.parent.mkdir(parents=True, exist_ok=True)

        \
        markdown_content = generate_consolidated_markdown(all_categories)

        \
        try:
            with open(markdown_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            print(f"Created: {markdown_path}")
            print(f"Successfully converted {len(excel_files)} Excel files -> {len(all_categories)} categories in consolidated file")
            return True
        except Exception as e:
            print(f"Error writing {markdown_path}: {e}")
            return False

    except Exception as e:
        print(f"Error processing role {role_name}: {e}")
        return False

def convert_guidelines_excel(excel_dir: str = "checklists/excel", markdown_dir: str = "checklists/markdown") -> bool:
    """
    Convert guidelines Excel file to markdown format.
    """
    try:
        guidelines_excel = Path(excel_dir) / "guidelines" / "android_coding_guidelines.xlsx"
        if not guidelines_excel.exists():
            print(f"Guidelines Excel file not found: {guidelines_excel}")
            return False
        
        # Read the guidelines Excel file
        df = pd.read_excel(guidelines_excel)
        
        # Create the guidelines markdown directory
        guidelines_md_dir = Path(markdown_dir) / "guidelines"
        guidelines_md_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate markdown content
        markdown_lines = []
        markdown_lines.append('# Android Coding Guidelines')
        markdown_lines.append('')
        
        current_category = ''
        current_subcategory = ''
        
        for _, row in df.iterrows():
            rule_id = str(row.get('Rule ID', '')).strip()
            main_category = str(row.get('Main Category', '')).strip()
            sub_category = str(row.get('Sub Category', '')).strip()
            description = str(row.get('Guidelines Description', '')).strip()
            good_example = str(row.get('Good Example', '')).strip()
            bad_example = str(row.get('Bad Example', '')).strip()
            measurement = str(row.get('Measurement Reference', '')).strip()
            severity = str(row.get('Severity (MUST/GOOD/MAY)', '')).strip()
            external_refs = str(row.get('External Refs', '')).strip()
            
            # Skip empty rows
            if not rule_id or rule_id.lower() in ['nan', 'none', '']:
                continue
            
            # Add category header
            if main_category and main_category != current_category:
                current_category = main_category
                markdown_lines.append(f'## {main_category}')
                markdown_lines.append('')
                current_subcategory = ''
            
            # Add subcategory header
            if sub_category and sub_category != current_subcategory:
                current_subcategory = sub_category
                markdown_lines.append(f'### {sub_category}')
                markdown_lines.append('')
            
            # Add guideline
            severity_text = f'({severity})' if severity and severity.lower() not in ['nan', 'none', ''] else ''
            markdown_lines.append(f'**{rule_id}** {severity_text}: {description}')
            
            # Add details
            details = []
            
            if good_example and good_example.lower() not in ['nan', 'none', '']:
                details.append(f'  - **Good Example:**')
                details.append(f'```kotlin')
                details.append(good_example)
                details.append(f'```')
            
            if bad_example and bad_example.lower() not in ['nan', 'none', '']:
                details.append(f'  - **Bad Example:**')
                details.append(f'```kotlin')
                details.append(bad_example)
                details.append(f'```')
            
            if measurement and measurement.lower() not in ['nan', 'none', '']:
                details.append(f'  - **Measurement:** {measurement}')
            
            if external_refs and external_refs.lower() not in ['nan', 'none', '']:
                details.append(f'  - **Reference:** {external_refs}')
            
            if details:
                markdown_lines.extend(details)
            
            markdown_lines.append('')
        
        # Write the markdown file
        markdown_file = guidelines_md_dir / 'android_coding_guidelines.md'
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(markdown_lines))
        
        print(f"Successfully created guidelines: {markdown_file}")
        print(f"Generated {len(df)} guidelines")
        return True
        
    except Exception as e:
        print(f"Error processing guidelines: {e}")
        return False

def convert_all_excel_files_by_category(excel_dir: str = "checklists/excel", markdown_dir: str = "checklists/markdown") -> bool:
    """
    Convert all Excel files, grouping by role and MainCategory column.

    Args:
        excel_dir: Directory containing Excel files
        markdown_dir: Directory to output Markdown files
    """
    excel_path = Path(excel_dir)
    markdown_path = Path(markdown_dir)

    if not excel_path.exists():
        print(f"Excel directory does not exist: {excel_dir}")
        return False

    markdown_path.mkdir(parents=True, exist_ok=True)

    converted_count = 0
    total_roles = 0

    \
    for role_dir in excel_path.iterdir():
        if not role_dir.is_dir() or role_dir.name == "guidelines":
            continue

        total_roles += 1
        role_name = role_dir.name

        \
        excel_files = list(role_dir.glob("*.xlsx"))
        if not excel_files:
            print(f"No Excel files found for role: {role_name}")
            continue

        if convert_role_excel_files(excel_files, role_name, str(markdown_path)):
            converted_count += 1

    print(f"\nConversion complete: {converted_count}/{total_roles} roles converted successfully")
    \
    success_rate = converted_count / total_roles if total_roles > 0 else 0
    return success_rate >= 0.8

def update_roles_json() -> bool:
    """Update roles.json with dynamic categories from markdown files"""
    try:
        \
        roles_file = Path("config/roles.json")
        if not roles_file.exists():
            print("Error: config/roles.json not found")
            return False

        with open(roles_file, 'r', encoding='utf-8') as f:
            roles_config = json.load(f)

        markdown_dir = Path("checklists/markdown")
        if not markdown_dir.exists():
            print("Error: checklists/markdown directory not found")
            return False

        filtered_roles = []
        for role in roles_config.get('roles', []):
            role_id = role.get('id')

            \
            if role_id == "guidelines":
                print(f"Skipping guidelines role (not a review role)")
                continue

            role_markdown_dir = markdown_dir / role_id
            if role_markdown_dir.exists():
                categories = []
                \
                consolidated_files = list(role_markdown_dir.glob("*_consolidated.md"))
                if consolidated_files:
                    \
                    consolidated_file = consolidated_files[0]
                    categories.append({
                        "id": f"{role_id}_consolidated",
                        "name": f"{role_id.title()} Review",
                        "type": "markdown",
                        "path": str(consolidated_file)
                    })
                else:
                    \
                    for markdown_file in role_markdown_dir.glob("*.md"):
                        category_name = markdown_file.stem.replace('_', ' ').title()
                        categories.append({
                            "id": markdown_file.stem,
                            "name": category_name,
                            "type": "markdown",
                            "path": str(markdown_file)
                        })

                categories.sort(key=lambda x: x['name'])
                role['categories'] = categories
                print(f"Updated {role_id}: {len(categories)} categories")
            else:
                role['categories'] = []
                print(f"No markdown files found for {role_id}")

            filtered_roles.append(role)

        roles_config['roles'] = filtered_roles

        \
        with open(roles_file, 'w', encoding='utf-8') as f:
            json.dump(roles_config, f, indent=2)

        print("Successfully updated roles.json")
        return True

    except Exception as e:
        print(f"Error updating roles.json: {e}")
        return False

def main():
    """Main function to run the auto-update process"""
    print("Starting auto-update process with category-based conversion...")

    \
    project_root = get_project_root()
    os.chdir(project_root)
    print(f"Working directory: {os.getcwd()}")

    \
    print("\n1. Converting Excel files to markdown (grouped by MainCategory)...")
    if not convert_all_excel_files_by_category():
        print("Error: Failed to convert Excel files")
        return False

    print("\n1.5. Converting guidelines Excel file to markdown...")
    if not convert_guidelines_excel():
        print("Warning: Failed to convert guidelines Excel file")

    print("\n2. Updating roles.json with dynamic categories...")
    if not update_roles_json():
        print("Error: Failed to update roles.json")
        return False

    print("\nAuto-update completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
