#!/usr/bin/env python3
"""
Excel to Markdown Converter that groups by MainCategory column
This script converts Excel files but groups items by MainCategory instead of treating each file as a separate category.
"""

import pandas as pd
import os
import sys
from pathlib import Path
import argparse
from typing import Dict, List, Any
from collections import defaultdict

def get_project_root():
    """Get the project root directory"""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def convert_excel_by_category(excel_file: str, role_dir: str, markdown_dir: str) -> bool:
    """
    Convert Excel file to markdown format, grouping by MainCategory column.
    Creates one markdown file per MainCategory found in the Excel file.
    
    Args:
        excel_file: Path to the Excel file
        role_dir: Role directory name (e.g., 'self', 'peer')
        markdown_dir: Directory to output Markdown files
    """
    try:
        # Read Excel file
        df = pd.read_excel(excel_file)
        
        # Check if MainCategory column exists
        if 'MainCategory' not in df.columns:
            print(f"Warning: MainCategory column not found in {excel_file}")
            # Fallback to Category column if available
            if 'Category' in df.columns:
                df['MainCategory'] = df['Category']
            else:
                print(f"Error: No MainCategory or Category column found in {excel_file}")
                return False
        
        # Group by MainCategory
        categories = defaultdict(list)
        
        for _, row in df.iterrows():
            main_category = str(row.get('MainCategory', '')).strip()
            if main_category and main_category.lower() not in ['nan', 'none', '']:
                categories[main_category].append(row)
        
        if not categories:
            print(f"Warning: No valid MainCategory values found in {excel_file}")
            return False
        
        # Create markdown files for each category
        success_count = 0
        for category_name, rows in categories.items():
            # Create safe filename from category name
            safe_category_name = category_name.lower().replace(' ', '_').replace('-', '_').replace('/', '_')
            markdown_filename = f"{safe_category_name}.md"
            markdown_path = Path(markdown_dir) / role_dir / markdown_filename
            
            # Ensure directory exists
            markdown_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate markdown content for this category
            markdown_content = generate_category_markdown(category_name, rows)
            
            # Write markdown file
            try:
                with open(markdown_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                print(f"Created: {markdown_path}")
                success_count += 1
            except Exception as e:
                print(f"Error writing {markdown_path}: {e}")
                return False
        
        print(f"Successfully converted {excel_file} -> {len(categories)} categories")
        return success_count == len(categories)
        
    except Exception as e:
        print(f"Error processing {excel_file}: {e}")
        return False

def generate_category_markdown(category_name: str, rows: List[pd.Series]) -> str:
    """Generate markdown content for a specific category"""
    markdown_lines = []
    
    # Add category header
    markdown_lines.append(f"# {category_name}")
    markdown_lines.append("")
    
    # Process each row in this category
    for _, row in rows:
        # Get values from columns
        sr_no = str(row.get('SrNo', '')).strip()
        sub_category = str(row.get('SubCategory', '')).strip()
        description = str(row.get('Description', '')).strip()
        how_to_measure = str(row.get('How to Measure', '')).strip()
        severity = str(row.get('Severity', '')).strip()
        rule_reference = str(row.get('Rule-Reference', '')).strip()
        additional_info = str(row.get('AdditionalInfo', '')).strip()
        
        # Skip empty rows
        if not sub_category or sub_category.lower() in ['nan', 'none', '']:
            continue
        
        # Determine item type based on severity
        item_type = "MUST"
        if severity:
            severity_lower = severity.lower().strip()
            if severity_lower in ['good', 'recommended', 'should', 'prefer']:
                item_type = "GOOD"
            elif severity_lower in ['suggested', 'optional', 'nice to have', 'consider', 'may']:
                item_type = "OPTIONAL"
        
        # Add main checklist item with serial number
        if sr_no and sr_no.lower() not in ['nan', 'none', '']:
            markdown_lines.append(f"**{sr_no}.** {sub_category} ({item_type})")
        else:
            markdown_lines.append(f"- {sub_category} ({item_type})")
        
        # Add expandable details section
        details_section = []
        
        # Add description if available
        if description and description.lower() not in ['nan', 'none', '']:
            details_section.append(f"  - **Description:** {description}")
        
        # Add how to measure if available
        if how_to_measure and how_to_measure.lower() not in ['nan', 'none', '']:
            details_section.append(f"  - **How to Measure:** {how_to_measure}")
        
        # Add rule reference if available
        if rule_reference and rule_reference.lower() not in ['nan', 'none', '']:
            details_section.append(f"  - **Rule Reference:** {rule_reference}")
        
        # Add additional info if available
        if additional_info and additional_info.lower() not in ['nan', 'none', '']:
            details_section.append(f"  - **Additional Info:** {additional_info}")
        
        # Add details section if there are any details
        if details_section:
            markdown_lines.extend(details_section)
        
        markdown_lines.append("")
    
    return '\n'.join(markdown_lines)

def convert_all_excel_files_by_category(excel_dir: str = "checklists/excel", markdown_dir: str = "checklists/markdown") -> bool:
    """
    Convert all Excel files, grouping by MainCategory column.
    
    Args:
        excel_dir: Directory containing Excel files
        markdown_dir: Directory to output Markdown files
    """
    excel_path = Path(excel_dir)
    markdown_path = Path(markdown_dir)
    
    if not excel_path.exists():
        print(f"Excel directory does not exist: {excel_dir}")
        return False
    
    # Create markdown directory if it doesn't exist
    markdown_path.mkdir(parents=True, exist_ok=True)
    
    converted_count = 0
    total_count = 0
    
    # Find all Excel files
    for excel_file in excel_path.rglob("*.xlsx"):
        total_count += 1
        
        # Get role directory name
        role_dir = excel_file.parent.name
        
        # Skip guidelines directory
        if role_dir == "guidelines":
            continue
        
        # Convert file by category
        if convert_excel_by_category(str(excel_file), role_dir, str(markdown_path)):
            converted_count += 1
    
    print(f"\nConversion complete: {converted_count}/{total_count} files converted successfully")
    return converted_count == total_count

def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description="Convert Excel files to Markdown, grouping by MainCategory")
    parser.add_argument("--excel-dir", default="checklists/excel", help="Excel directory path")
    parser.add_argument("--markdown-dir", default="checklists/markdown", help="Markdown directory path")
    parser.add_argument("--file", help="Convert specific Excel file")
    parser.add_argument("--role", help="Role directory for specific file conversion")
    
    args = parser.parse_args()
    
    # Change to project root directory
    project_root = get_project_root()
    os.chdir(project_root)
    
    if args.file:
        # Convert specific file
        if not args.role:
            print("Error: --role is required when converting a specific file")
            return False
        
        return convert_excel_by_category(args.file, args.role, args.markdown_dir)
    else:
        # Convert all files
        return convert_all_excel_files_by_category(args.excel_dir, args.markdown_dir)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


