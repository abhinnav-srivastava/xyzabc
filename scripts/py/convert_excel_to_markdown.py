#!/usr/bin/env python3
"""
Standalone script to convert Excel checklists to Markdown format.
This script can be used to convert Excel files from the excel/ folder to markdown/ folder.
"""

import pandas as pd
import os
import sys
from pathlib import Path
import argparse

def convert_excel_to_markdown(excel_path: str, markdown_path: str = None):
    """
    Convert an Excel checklist file to Markdown format.
    
    Args:
        excel_path: Path to the Excel file
        markdown_path: Path for the output Markdown file (optional)
    """
    
    # Read Excel file
    try:
        df = pd.read_excel(excel_path)
    except Exception as e:
        print(f"Error reading Excel file {excel_path}: {e}")
        return False
    
    # Validate required columns for new format
    required_columns = ['SrNo', 'Category', 'SubCategory', 'Description', 'Severity']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"Error: Missing required columns: {missing_columns}")
        print(f"Available columns: {list(df.columns)}")
        return False
    
    # Generate markdown content
    markdown_lines = []
    
    # Get category from first row for the header
    category = ""
    if len(df) > 0:
        category = str(df.iloc[0].get('Category', '')).strip()
    
    # Add header with category as title
    if category and category.lower() not in ['nan', 'none', '']:
        markdown_lines.append(f"# {category}")
    else:
        markdown_lines.append("# Code Review Checklist")
    markdown_lines.append("")
    
    # Process each row
    for index, row in df.iterrows():
        # Get values from new format columns
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
    
    # Write markdown file
    if markdown_path is None:
        # Generate markdown path from excel path, ensuring it goes to markdown directory
        excel_file = Path(excel_path)
        # Get the relative path from the excel directory
        try:
            relative_path = excel_file.relative_to(Path("checklists/excel"))
            markdown_path = Path("checklists/markdown") / relative_path.with_suffix('.md')
        except ValueError:
            # If the file is not in checklists/excel, create a default path
            markdown_path = Path("checklists/markdown") / excel_file.name.replace('.xlsx', '.md')
    
    try:
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(markdown_lines))
        print(f"Successfully converted: {excel_path} -> {markdown_path}")
        return True
    except Exception as e:
        print(f"Error writing markdown file {markdown_path}: {e}")
        return False

def convert_all_excel_files(excel_dir: str = "checklists/excel", markdown_dir: str = "checklists/markdown"):
    """
    Convert all Excel files in the excel directory to markdown files in the markdown directory.
    
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
        
        # Determine relative path and create corresponding markdown path
        relative_path = excel_file.relative_to(excel_path)
        markdown_file = markdown_path / relative_path.with_suffix('.md')
        
        # Create subdirectories if needed
        markdown_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert file
        if convert_excel_to_markdown(str(excel_file), str(markdown_file)):
            converted_count += 1
    
    print(f"\nConversion complete: {converted_count}/{total_count} files converted successfully")
    return converted_count == total_count

def main():
    """Main function to handle command line arguments."""
    
    parser = argparse.ArgumentParser(description="Convert Excel checklists to Markdown format")
    parser.add_argument("--excel", "-e", help="Path to Excel file to convert")
    parser.add_argument("--markdown", "-m", help="Path for output Markdown file")
    parser.add_argument("--all", "-a", action="store_true", help="Convert all Excel files in checklists/excel/")
    parser.add_argument("--excel-dir", default="checklists/excel", help="Excel directory (default: checklists/excel)")
    parser.add_argument("--markdown-dir", default="checklists/markdown", help="Markdown directory (default: checklists/markdown)")
    
    args = parser.parse_args()
    
    if args.all:
        # Convert all files
        success = convert_all_excel_files(args.excel_dir, args.markdown_dir)
        sys.exit(0 if success else 1)
    elif args.excel:
        # Convert single file
        success = convert_excel_to_markdown(args.excel, args.markdown)
        sys.exit(0 if success else 1)
    else:
        # Show help
        parser.print_help()
        print("\nExamples:")
        print("  python convert_excel_to_markdown.py --all")
        print("  python convert_excel_to_markdown.py --excel checklists/excel/self/correctness.xlsx")
        print("  python convert_excel_to_markdown.py --excel checklists/excel/peer/style.xlsx --markdown checklists/markdown/peer/style.md")

if __name__ == "__main__":
    main()
