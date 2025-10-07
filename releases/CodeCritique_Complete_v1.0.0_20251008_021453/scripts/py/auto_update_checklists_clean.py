#!/usr/bin/env python3
"""
Auto-update script for checklists
Converts Excel files to markdown and updates roles.json automatically
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
import shutil

# Add the project root directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def get_project_root():
    """Get the project root directory"""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def convert_excel_to_markdown_dynamic(excel_file: str, markdown_file: str) -> bool:
    """Convert Excel file to markdown format with dynamic column detection"""
    try:
        # Read the Excel file
        df = pd.read_excel(excel_file)
        
        # Create markdown content
        markdown_content = f"# {Path(markdown_file).stem.replace('_', ' ').title()}\n\n"
        
        # Get available columns for dynamic processing
        available_columns = df.columns.tolist()
        
        # Determine the structure based on available columns
        if 'Category' in available_columns and 'SubCategory' in available_columns:
            # New structure with Category, SubCategory, Description, etc.
            current_category = None
            current_subcategory = None
            
            for _, row in df.iterrows():
                # Check if we have a new category
                if pd.notna(row.get('Category', '')) and row['Category'] != current_category:
                    current_category = row['Category']
                    current_subcategory = None
                    markdown_content += f"## {current_category}\n\n"
                
                # Check if we have a new subcategory
                if pd.notna(row.get('SubCategory', '')) and row['SubCategory'] != current_subcategory:
                    current_subcategory = row['SubCategory']
                    markdown_content += f"### {current_subcategory}\n\n"
                
                # Add the item if we have a description
                if pd.notna(row.get('Description', '')):
                    item_text = row['Description']
                    severity = row.get('Severity', 'good').lower()
                    
                    # Determine bullet point style based on severity
                    if severity == 'must':
                        bullet = "- **MUST:** "
                    elif severity == 'good':
                        bullet = "- **GOOD:** "
                    elif severity == 'suggested':
                        bullet = "- **SUGGESTED:** "
                    else:
                        bullet = "- "
                    
                    markdown_content += f"{bullet}{item_text}\n"
                    
                    # Add additional fields dynamically
                    if pd.notna(row.get('How to Measure', '')):
                        markdown_content += f"  - **How to Measure:** {row['How to Measure']}\n"
                    
                    if pd.notna(row.get('AdditionalInfo', '')):
                        markdown_content += f"  - **Additional Info:** {row['AdditionalInfo']}\n"
                    
                    if pd.notna(row.get('Rule-Reference', '')):
                        markdown_content += f"  - **Rule Reference:** {row['Rule-Reference']}\n"
                    
                    markdown_content += "\n"
        
        elif 'Category' in available_columns:
            # Structure with Category column only
            categories = df['Category'].dropna().unique()
            
            for category in categories:
                if pd.notna(category):
                    category_df = df[df['Category'] == category]
                    markdown_content += f"## {category}\n\n"
                    
                    for _, row in category_df.iterrows():
                        if pd.notna(row.get('Description', '')):
                            item_text = row['Description']
                            severity = row.get('Severity', 'good').lower()
                            
                            # Determine bullet point style based on severity
                            if severity == 'must':
                                bullet = "- **MUST:** "
                            elif severity == 'good':
                                bullet = "- **GOOD:** "
                            elif severity == 'suggested':
                                bullet = "- **SUGGESTED:** "
                            else:
                                bullet = "- "
                            
                            markdown_content += f"{bullet}{item_text}\n"
                            
                            # Add additional fields dynamically
                            if pd.notna(row.get('How to Measure', '')):
                                markdown_content += f"  - **How to Measure:** {row['How to Measure']}\n"
                            
                            if pd.notna(row.get('AdditionalInfo', '')):
                                markdown_content += f"  - **Additional Info:** {row['AdditionalInfo']}\n"
                            
                            if pd.notna(row.get('Rule-Reference', '')):
                                markdown_content += f"  - **Rule Reference:** {row['Rule-Reference']}\n"
                            
                            markdown_content += "\n"
        else:
            # Simple list structure - process all rows
            for _, row in df.iterrows():
                if pd.notna(row.get('Description', '')):
                    item_text = row['Description']
                    severity = row.get('Severity', 'good').lower()
                    
                    # Determine bullet point style based on severity
                    if severity == 'must':
                        bullet = "- **MUST:** "
                    elif severity == 'good':
                        bullet = "- **GOOD:** "
                    elif severity == 'suggested':
                        bullet = "- **SUGGESTED:** "
                    else:
                        bullet = "- "
                    
                    markdown_content += f"{bullet}{item_text}\n"
                    
                    # Add additional fields dynamically
                    if pd.notna(row.get('How to Measure', '')):
                        markdown_content += f"  - **How to Measure:** {row['How to Measure']}\n"
                    
                    if pd.notna(row.get('AdditionalInfo', '')):
                        markdown_content += f"  - **Additional Info:** {row['AdditionalInfo']}\n"
                    
                    if pd.notna(row.get('Rule-Reference', '')):
                        markdown_content += f"  - **Rule Reference:** {row['Rule-Reference']}\n"
                    
                    markdown_content += "\n"
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(markdown_file), exist_ok=True)
        
        # Write the markdown file
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"SUCCESS: Converted {excel_file} -> {markdown_file}")
        return True
        
    except Exception as e:
        print(f"ERROR: Converting {excel_file}: {e}")
        return False

def convert_excel_to_markdown(excel_file: str, markdown_file: str) -> bool:
    """Convert Excel file to markdown format (legacy function for compatibility)"""
    # Use the new dynamic function
    return convert_excel_to_markdown_dynamic(excel_file, markdown_file)

def convert_all_excel_files() -> bool:
    """Convert all Excel files to markdown"""
    project_root = get_project_root()
    excel_dir = os.path.join(project_root, "checklists", "excel")
    markdown_dir = os.path.join(project_root, "checklists", "markdown")
    
    success_count = 0
    total_count = 0
    
    # Find all Excel files
    for root, dirs, files in os.walk(excel_dir):
        for file in files:
            if file.endswith('.xlsx'):
                excel_path = os.path.join(root, file)
                rel_path = os.path.relpath(excel_path, excel_dir)
                
                # Create corresponding markdown path
                markdown_file = file.replace('.xlsx', '.md')
                if rel_path != file:
                    rel_dir = os.path.dirname(rel_path)
                    markdown_path = os.path.join(markdown_dir, rel_dir, markdown_file)
                else:
                    markdown_path = os.path.join(markdown_dir, markdown_file)
                
                total_count += 1
                if convert_excel_to_markdown(excel_path, markdown_path):
                    success_count += 1
    
    print(f"Conversion Summary: {success_count}/{total_count} files converted successfully")
    return success_count == total_count

def update_roles_json() -> bool:
    """Update roles.json with dynamic categories"""
    try:
        project_root = get_project_root()
        roles_path = os.path.join(project_root, "config", "roles.json")
        
        # Load current roles
        with open(roles_path, 'r', encoding='utf-8') as f:
            roles_config = json.load(f)
        
        # Scan for categories in each role directory
        excel_dir = os.path.join(project_root, "checklists", "excel")
        roles = []
        
        for role_dir in os.listdir(excel_dir):
            role_path = os.path.join(excel_dir, role_dir)
            if os.path.isdir(role_path):
                categories = []
                
                # Find all Excel files in this role directory
                for file in os.listdir(role_path):
                    if file.endswith('.xlsx'):
                        # Extract category from filename or Excel content
                        category_name = file.replace('.xlsx', '').replace('_', ' ').title()
                        category_id = file.replace('.xlsx', '').lower().replace(' ', '_')
                        
                        categories.append({
                            "id": category_id,
                            "name": category_name,
                            "type": "markdown",
                            "path": f"checklists/markdown/{role_dir}/{category_id}.md"
                        })
                
                if categories:
                    roles.append({
                        "id": role_dir,
                        "name": role_dir.replace('_', ' ').title(),
                        "categories": categories
                    })
        
        # Update roles config
        roles_config['roles'] = roles
        
        # Save updated config
        with open(roles_path, 'w', encoding='utf-8') as f:
            json.dump(roles_config, f, indent=2, ensure_ascii=False)
        
        print(f"SUCCESS: Updated roles.json with {len(roles)} roles")
        return True
        
    except Exception as e:
        print(f"ERROR: Updating roles.json: {e}")
        return False

def main():
    """Main function"""
    try:
        print("Starting auto-update process...")
        
        # Step 1: Convert all Excel files to markdown
        print("\nStep 1: Converting Excel files to markdown...")
        convert_success = convert_all_excel_files()
        
        # Step 2: Update roles.json
        print("\nStep 2: Updating roles.json...")
        roles_success = update_roles_json()
        
        if convert_success and roles_success:
            print("\nSUCCESS: Auto-update completed successfully!")
            print("You can now refresh the application to see the changes.")
            return True
        else:
            print("\nERROR: Auto-update completed with errors.")
            return False
            
    except Exception as e:
        print(f"ERROR: Auto-update failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


