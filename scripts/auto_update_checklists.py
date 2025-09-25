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

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_project_root():
    """Get the project root directory"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def convert_excel_to_markdown(excel_file: str, markdown_file: str) -> bool:
    """Convert Excel file to markdown format"""
    try:
        # Read the Excel file
        df = pd.read_excel(excel_file)
        
        # Create markdown content
        markdown_content = f"# {Path(markdown_file).stem.replace('_', ' ').title()}\n\n"
        
        # Handle different Excel file structures
        if 'Rule ID' in df.columns and 'Guidelines Description' in df.columns:
            # Handle the guidelines structure
            current_category = None
            current_subcategory = None
            
            for _, row in df.iterrows():
                # Check if we have a new main category
                if pd.notna(row.get('Main Category', '')) and row['Main Category'] != current_category:
                    current_category = row['Main Category']
                    current_subcategory = None
                    markdown_content += f"## {current_category}\n\n"
                
                # Check if we have a new subcategory
                if pd.notna(row.get('Sub Category', '')) and row['Sub Category'] != current_subcategory:
                    current_subcategory = row['Sub Category']
                    markdown_content += f"### {current_subcategory}\n\n"
                
                # Add the guideline item
                if pd.notna(row.get('Guidelines Description', '')):
                    rule_id = row.get('Rule ID', '')
                    description = row['Guidelines Description']
                    severity = row.get('Severity (MUST/GOOD/MAY)', '')
                    
                    # Add rule ID as header if available
                    if rule_id:
                        markdown_content += f"**{rule_id}**"
                        if severity:
                            markdown_content += f" ({severity})"
                        markdown_content += f": {description}\n\n"
                    else:
                        markdown_content += f"- {description}\n"
                        if severity:
                            markdown_content += f"  - **Severity:** {severity}\n"
                    
                    # Add good example if available
                    if pd.notna(row.get('Good Example', '')):
                        markdown_content += f"  - **Good Example:**\n```kotlin\n{row['Good Example']}\n```\n"
                    
                    # Add bad example if available
                    if pd.notna(row.get('Bad Example', '')):
                        markdown_content += f"  - **Bad Example:**\n```kotlin\n{row['Bad Example']}\n```\n"
                    
                    # Add measurement reference if available
                    if pd.notna(row.get('Measurement Reference', '')):
                        markdown_content += f"  - **Measurement:** {row['Measurement Reference']}\n"
                    
                    # Add external references if available
                    if pd.notna(row.get('External Refs', '')):
                        markdown_content += f"  - **Reference:** {row['External Refs']}\n"
                    
                    markdown_content += "\n"
        
        elif 'Main Category' in df.columns:
            # Handle the current structure with Main Category, Sub Category, Description, etc.
            current_category = None
            current_subcategory = None
            
            for _, row in df.iterrows():
                # Check if we have a new main category
                if pd.notna(row.get('Main Category', '')) and row['Main Category'] != current_category:
                    current_category = row['Main Category']
                    current_subcategory = None
                    markdown_content += f"## {current_category}\n\n"
                
                # Check if we have a new subcategory
                if pd.notna(row.get('Sub Category', '')) and row['Sub Category'] != current_subcategory:
                    current_subcategory = row['Sub Category']
                    markdown_content += f"### {current_subcategory}\n\n"
                
                # Add the item if we have a description
                if pd.notna(row.get('Description', '')):
                    item_text = row['Description']
                    markdown_content += f"- {item_text}\n"
                    
                    # Add technical description if available
                    if pd.notna(row.get('Technical Description', '')):
                        markdown_content += f"  - **Technical Details:** {row['Technical Description']}\n"
                    
                    # Add measurement details if available
                    if pd.notna(row.get('How to Measure', '')):
                        markdown_content += f"  - **How to Measure:** {row['How to Measure']}\n"
                    
                    markdown_content += "\n"
        
        elif 'Category' in df.columns:
            # Handle structure with Category column
            categories = df['Category'].unique()
            for category in categories:
                if pd.notna(category):
                    category_df = df[df['Category'] == category]
                    markdown_content += f"## {category}\n\n"
                    
                    for _, row in category_df.iterrows():
                        if pd.notna(row.get('Item', '')):
                            item_type = row.get('Type', 'good').lower()
                            item_text = row['Item']
                            
                            # Determine bullet point style based on type
                            if item_type == 'must':
                                bullet = "- **MUST:** "
                            elif item_type == 'good':
                                bullet = "- **GOOD:** "
                            elif item_type == 'optional':
                                bullet = "- **OPTIONAL:** "
                            else:
                                bullet = "- "
                            
                            markdown_content += f"{bullet}{item_text}\n"
                            
                            # Add description if available
                            if pd.notna(row.get('Description', '')):
                                markdown_content += f"  - {row['Description']}\n"
                            
                            # Add details if available
                            if pd.notna(row.get('Details', '')):
                                markdown_content += f"  - **Details:** {row['Details']}\n"
                            
                            markdown_content += "\n"
        else:
            # Handle simple list structure
            for _, row in df.iterrows():
                if pd.notna(row.get('Item', '')):
                    item_type = row.get('Type', 'good').lower()
                    item_text = row['Item']
                    
                    # Determine bullet point style based on type
                    if item_type == 'must':
                        bullet = "- **MUST:** "
                    elif item_type == 'good':
                        bullet = "- **GOOD:** "
                    elif item_type == 'optional':
                        bullet = "- **OPTIONAL:** "
                    else:
                        bullet = "- "
                    
                    markdown_content += f"{bullet}{item_text}\n"
                    
                    # Add description if available
                    if pd.notna(row.get('Description', '')):
                        markdown_content += f"  - {row['Description']}\n"
                    
                    # Add details if available
                    if pd.notna(row.get('Details', '')):
                        markdown_content += f"  - **Details:** {row['Details']}\n"
                    
                    markdown_content += "\n"
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(markdown_file), exist_ok=True)
        
        # Write the markdown file
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"SUCCESS: Converted {excel_file} -> {markdown_file}")
        return True
        
    except Exception as e:
        print(f"ERROR: Converting {excel_file}: {str(e)}")
        return False

def scan_excel_folders() -> Dict[str, List[str]]:
    """Scan the excel folders and return the structure"""
    project_root = get_project_root()
    excel_dir = os.path.join(project_root, "checklists", "excel")
    
    structure = {}
    
    if not os.path.exists(excel_dir):
        print(f"ERROR: Excel directory not found: {excel_dir}")
        return structure
    
    for role_folder in os.listdir(excel_dir):
        role_path = os.path.join(excel_dir, role_folder)
        
        # Skip if not a directory or if it's the guidelines folder
        if not os.path.isdir(role_path) or role_folder == "guidelines":
            continue
        
        excel_files = []
        for file in os.listdir(role_path):
            if file.endswith('.xlsx'):
                excel_files.append(file.replace('.xlsx', ''))
        
        if excel_files:
            structure[role_folder] = excel_files
    
    return structure

def update_roles_json(structure: Dict[str, List[str]]) -> bool:
    """Update the roles.json file based on the folder structure"""
    try:
        project_root = get_project_root()
        config_file = os.path.join(project_root, "config", "roles.json")
        
        # Role name mapping
        role_names = {
            "self": "Self Review",
            "peer": "Peer Review", 
            "techlead": "Tech Lead Review",
            "fo": "FO Review",
            "architect": "Architect Review"
        }
        
        # Category name mapping
        category_names = {
            "correctness": "Correctness",
            "readability": "Readability", 
            "tests": "Test Review",
            "functionality": "Functionality",
            "style": "Style & Naming",
            "design": "Design Review",
            "architecture": "Architecture Review",
            "ops": "Operational Readiness"
        }
        
        roles = []
        
        for role_id, categories in structure.items():
            role_name = role_names.get(role_id, role_id.replace('_', ' ').title())
            
            role_categories = []
            for category_id in categories:
                category_name = category_names.get(category_id, category_id.replace('_', ' ').title())
                markdown_path = f"checklists/markdown/{role_id}/{category_id}.md"
                
                role_categories.append({
                    "id": category_id,
                    "name": category_name,
                    "type": "markdown",
                    "path": markdown_path
                })
            
            roles.append({
                "id": role_id,
                "name": role_name,
                "categories": role_categories
            })
        
        # Create the config structure
        config = {
            "roles": roles
        }
        
        # Write the updated config
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"SUCCESS: Updated roles.json with {len(roles)} roles")
        return True
        
    except Exception as e:
        print(f"ERROR: Updating roles.json: {str(e)}")
        return False

def convert_all_excel_files() -> bool:
    """Convert all Excel files to markdown"""
    project_root = get_project_root()
    excel_dir = os.path.join(project_root, "checklists", "excel")
    markdown_dir = os.path.join(project_root, "checklists", "markdown")
    
    success_count = 0
    total_count = 0
    
    for root, dirs, files in os.walk(excel_dir):
        for file in files:
            if file.endswith('.xlsx'):
                excel_path = os.path.join(root, file)
                
                # Calculate relative path from excel_dir
                rel_path = os.path.relpath(root, excel_dir)
                if rel_path == ".":
                    rel_path = ""
                
                # Create corresponding markdown path
                markdown_file = file.replace('.xlsx', '.md')
                if rel_path:
                    markdown_path = os.path.join(markdown_dir, rel_path, markdown_file)
                else:
                    markdown_path = os.path.join(markdown_dir, markdown_file)
                
                total_count += 1
                if convert_excel_to_markdown(excel_path, markdown_path):
                    success_count += 1
    
    print(f"Conversion Summary: {success_count}/{total_count} files converted successfully")
    return success_count == total_count

def main():
    """Main function to run the auto-update process"""
    try:
        print("Starting auto-update process...")
        
        # Step 1: Convert all Excel files to markdown
        print("\nStep 1: Converting Excel files to markdown...")
        convert_success = convert_all_excel_files()
        
        # Step 2: Scan folder structure
        print("\nStep 2: Scanning folder structure...")
        structure = scan_excel_folders()
        
        if not structure:
            print("ERROR: No roles found in Excel folders")
            return False
        
        print(f"Found {len(structure)} roles:")
        for role_id, categories in structure.items():
            print(f"  - {role_id}: {', '.join(categories)}")
        
        # Step 3: Update roles.json
        print("\nStep 3: Updating roles.json...")
        config_success = update_roles_json(structure)
        
        if convert_success and config_success:
            print("\nSUCCESS: Auto-update completed successfully!")
            print("You can now refresh the application to see the changes.")
            return True
        else:
            print("\nERROR: Auto-update completed with errors.")
            return False
    except UnicodeEncodeError:
        # Fallback for systems that don't support Unicode emojis
        print("Starting auto-update process...")
        print("\nStep 1: Converting Excel files to markdown...")
        convert_success = convert_all_excel_files()
        print("\nStep 2: Scanning folder structure...")
        structure = scan_excel_folders()
        
        if not structure:
            print("ERROR: No roles found in Excel folders")
            return False
        
        print(f"Found {len(structure)} roles:")
        for role_id, categories in structure.items():
            print(f"  - {role_id}: {', '.join(categories)}")
        
        print("\nStep 3: Updating roles.json...")
        config_success = update_roles_json(structure)
        
        if convert_success and config_success:
            print("\nSUCCESS: Auto-update completed successfully!")
            print("You can now refresh the application to see the changes.")
            return True
        else:
            print("\nERROR: Auto-update completed with errors.")
            return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
