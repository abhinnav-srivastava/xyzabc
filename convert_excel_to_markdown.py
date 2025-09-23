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
    required_columns = ['Main Category', 'Sub Category', 'Description']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"Error: Missing required columns: {missing_columns}")
        print(f"Available columns: {list(df.columns)}")
        return False
    
    # Generate markdown content
    markdown_lines = []
    
    # Get main category from first row for the header
    main_category = ""
    if len(df) > 0:
        main_category = str(df.iloc[0].get('Main Category', '')).strip()
    
    # Add header with main category as title
    if main_category and main_category.lower() not in ['nan', 'none', '']:
        markdown_lines.append(f"# {main_category}")
    else:
        markdown_lines.append("# Code Review Checklist")
    markdown_lines.append("")
    
    # Process each row
    for index, row in df.iterrows():
        # Get values from new format columns
        sub_category = str(row.get('Sub Category', '')).strip()
        description = str(row.get('Description', '')).strip()
        technical_desc = str(row.get('Technical Description', '')).strip()
        how_to_measure = str(row.get('How to Measure', '')).strip()
        
        # Skip empty rows
        if not sub_category or sub_category.lower() in ['nan', 'none', '']:
            continue
        
        # Determine item type based on content (default to MUST)
        item_type = "MUST"
        if any(keyword in sub_category.lower() for keyword in ['good', 'recommended', 'should', 'prefer']):
            item_type = "GOOD"
        elif any(keyword in sub_category.lower() for keyword in ['optional', 'nice to have', 'consider']):
            item_type = "OPTIONAL"
        
        # Add main checklist item (sub category is the main item text)
        markdown_lines.append(f"- {sub_category} ({item_type})")
        
        # Add expandable details section
        details_section = []
        
        # Add description if available
        if description and description.lower() not in ['nan', 'none', '']:
            details_section.append(f"  - **Description:** {description}")
        
        # Add technical description if available
        if technical_desc and technical_desc.lower() not in ['nan', 'none', '']:
            details_section.append(f"  - **Technical Details:** {technical_desc}")
        
        # Add how to measure if available
        if how_to_measure and how_to_measure.lower() not in ['nan', 'none', '']:
            details_section.append(f"  - **How to Measure:** {how_to_measure}")
        
        # Add details section if there are any details
        if details_section:
            markdown_lines.extend(details_section)
        
        markdown_lines.append("")
    
    # Write markdown file
    if markdown_path is None:
        # Generate markdown path from excel path
        excel_file = Path(excel_path)
        markdown_path = excel_file.with_suffix('.md')
    
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
