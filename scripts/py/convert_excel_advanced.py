#!/usr/bin/env python3
"""
Advanced Excel to Markdown Converter for CodeCritique
Enhanced with flexible column mapping, validation, and error handling.
"""

import pandas as pd
import os
import sys
import json
import logging
from pathlib import Path
import argparse
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('conversion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ItemType(Enum):
    MUST = "MUST"
    GOOD = "GOOD"
    OPTIONAL = "OPTIONAL"
    MAY = "MAY"

@dataclass
class ConversionConfig:
    """Configuration for Excel to Markdown conversion"""
    excel_dir: str = "checklists/excel"
    markdown_dir: str = "checklists/markdown"
    config_file: str = "config/conversion_config.json"
    backup_enabled: bool = True
    validation_enabled: bool = True
    dry_run: bool = False

@dataclass
class ColumnMapping:
    """Column mapping configuration"""
    checklist_id: str = "Checklist-ID"
    sr_no: str = "SrNo"
    category: str = "Category"
    sub_category: str = "SubCategory"
    description: str = "Description"
    how_to_measure: str = "How to Measure"
    severity: str = "Severity"
    rule_reference: str = "Rule-Reference"
    additional_info: str = "AdditionalInfo"

class ExcelConverter:
    """Advanced Excel to Markdown converter"""
    
    def __init__(self, config: ConversionConfig):
        self.config = config
        self.column_mapping = self._load_column_mapping()
        self.conversion_stats = {
            'total_files': 0,
            'successful_conversions': 0,
            'failed_conversions': 0,
            'errors': []
        }
    
    def _load_column_mapping(self) -> ColumnMapping:
        """Load column mapping from config file"""
        config_path = Path(self.config.config_file)
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    return ColumnMapping(**config_data.get('column_mapping', {}))
            except Exception as e:
                logger.warning(f"Failed to load column mapping config: {e}")
        
        return ColumnMapping()
    
    def _detect_item_type_from_severity(self, severity: str) -> ItemType:
        """Detect item type based on severity value"""
        if not severity:
            return ItemType.MUST
        
        severity_lower = severity.lower().strip()
        
        if severity_lower in ['must', 'required', 'critical', 'essential']:
            return ItemType.MUST
        elif severity_lower in ['good', 'recommended', 'should', 'prefer']:
            return ItemType.GOOD
        elif severity_lower in ['suggested', 'optional', 'nice to have', 'consider', 'may']:
            return ItemType.OPTIONAL
        
        return ItemType.MUST  # Default
    
    def _validate_excel_file(self, df: pd.DataFrame, file_path: str) -> Tuple[bool, List[str]]:
        """Validate Excel file structure and content"""
        errors = []
        
        # Check if dataframe is empty
        if df.empty:
            errors.append("Excel file is empty")
            return False, errors
        
        # Check required columns
        required_columns = [
            self.column_mapping.sr_no,
            self.column_mapping.category,
            self.column_mapping.sub_category,
            self.column_mapping.description,
            self.column_mapping.severity
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            errors.append(f"Missing required columns: {missing_columns}")
        
        # Check for empty required fields
        for index, row in df.iterrows():
            if pd.isna(row.get(self.column_mapping.sub_category, '')) or str(row.get(self.column_mapping.sub_category, '')).strip() == '':
                errors.append(f"Row {index + 1}: Empty sub category")
        
        # Check for duplicate sub categories
        sub_categories = df[self.column_mapping.sub_category].dropna()
        duplicates = sub_categories[sub_categories.duplicated()]
        if not duplicates.empty:
            errors.append(f"Duplicate sub categories found: {duplicates.tolist()}")
        
        return len(errors) == 0, errors
    
    def _create_backup(self, file_path: str) -> Optional[str]:
        """Create backup of existing markdown file"""
        if not self.config.backup_enabled:
            return None
        
        backup_path = f"{file_path}.backup"
        try:
            if os.path.exists(file_path):
                import shutil
                shutil.copy2(file_path, backup_path)
                logger.info(f"Backup created: {backup_path}")
                return backup_path
        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")
        
        return None
    
    def _generate_markdown_content(self, df: pd.DataFrame, file_path: str) -> str:
        """Generate markdown content from Excel data"""
        markdown_lines = []
        
        # Get category from first row
        category = ""
        if len(df) > 0:
            category = str(df.iloc[0].get(self.column_mapping.category, '')).strip()
        
        # Add header
        if category and category.lower() not in ['nan', 'none', '']:
            markdown_lines.append(f"# {category}")
        else:
            # Extract category from filename
            category_name = Path(file_path).stem.replace('_', ' ').title()
            markdown_lines.append(f"# {category_name}")
        
        markdown_lines.append("")
        
        # Process each row
        for index, row in df.iterrows():
            # Extract data
            sr_no = str(row.get(self.column_mapping.sr_no, '')).strip()
            sub_category = str(row.get(self.column_mapping.sub_category, '')).strip()
            description = str(row.get(self.column_mapping.description, '')).strip()
            how_to_measure = str(row.get(self.column_mapping.how_to_measure, '')).strip()
            severity = str(row.get(self.column_mapping.severity, '')).strip()
            rule_reference = str(row.get(self.column_mapping.rule_reference, '')).strip()
            additional_info = str(row.get(self.column_mapping.additional_info, '')).strip()
            
            # Skip empty rows
            if not sub_category or sub_category.lower() in ['nan', 'none', '']:
                continue
            
            # Determine item type based on severity
            item_type = self._detect_item_type_from_severity(severity)
            
            # Add main checklist item with serial number
            if sr_no and sr_no.lower() not in ['nan', 'none', '']:
                markdown_lines.append(f"**{sr_no}.** {sub_category} ({item_type.value})")
            else:
                markdown_lines.append(f"- {sub_category} ({item_type.value})")
            
            # Add expandable details section
            details_section = []
            
            if description and description.lower() not in ['nan', 'none', '']:
                details_section.append(f"  - **Description:** {description}")
            
            if how_to_measure and how_to_measure.lower() not in ['nan', 'none', '']:
                details_section.append(f"  - **How to Measure:** {how_to_measure}")
            
            if rule_reference and rule_reference.lower() not in ['nan', 'none', '']:
                details_section.append(f"  - **Rule Reference:** {rule_reference}")
            
            if additional_info and additional_info.lower() not in ['nan', 'none', '']:
                details_section.append(f"  - **Additional Info:** {additional_info}")
            
            # Add details section if there are any details
            if details_section:
                markdown_lines.extend(details_section)
            
            markdown_lines.append("")
        
        return '\n'.join(markdown_lines)
    
    def convert_file(self, excel_path: str, markdown_path: str = None) -> bool:
        """Convert a single Excel file to Markdown"""
        try:
            logger.info(f"Converting: {excel_path}")
            
            # Read Excel file
            try:
                df = pd.read_excel(excel_path)
            except Exception as e:
                logger.error(f"Error reading Excel file {excel_path}: {e}")
                self.conversion_stats['errors'].append(f"Read error in {excel_path}: {e}")
                return False
            
            # Validate file
            if self.config.validation_enabled:
                is_valid, errors = self._validate_excel_file(df, excel_path)
                if not is_valid:
                    logger.error(f"Validation failed for {excel_path}: {errors}")
                    self.conversion_stats['errors'].extend([f"Validation error in {excel_path}: {error}" for error in errors])
                    return False
            
            # Generate markdown content
            markdown_content = self._generate_markdown_content(df, excel_path)
            
            # Determine output path
            if markdown_path is None:
                excel_file = Path(excel_path)
                # Get the relative path from the excel directory
                try:
                    relative_path = excel_file.relative_to(Path("checklists/excel"))
                    markdown_path = Path("checklists/markdown") / relative_path.with_suffix('.md')
                except ValueError:
                    # If the file is not in checklists/excel, create a default path
                    markdown_path = Path("checklists/markdown") / excel_file.name.replace('.xlsx', '.md')
            
            # Create backup if enabled
            if not self.config.dry_run:
                self._create_backup(str(markdown_path))
            
            # Write markdown file
            if not self.config.dry_run:
                try:
                    # Ensure directory exists
                    Path(markdown_path).parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(markdown_path, 'w', encoding='utf-8') as f:
                        f.write(markdown_content)
                    
                    logger.info(f"Successfully converted: {excel_path} -> {markdown_path}")
                    return True
                except Exception as e:
                    logger.error(f"Error writing markdown file {markdown_path}: {e}")
                    self.conversion_stats['errors'].append(f"Write error for {markdown_path}: {e}")
                    return False
            else:
                logger.info(f"Dry run: Would convert {excel_path} -> {markdown_path}")
                return True
                
        except Exception as e:
            logger.error(f"Unexpected error converting {excel_path}: {e}")
            self.conversion_stats['errors'].append(f"Unexpected error in {excel_path}: {e}")
            return False
    
    def convert_all_files(self) -> bool:
        """Convert all Excel files in the configured directory"""
        excel_path = Path(self.config.excel_dir)
        markdown_path = Path(self.config.markdown_dir)
        
        if not excel_path.exists():
            logger.error(f"Excel directory does not exist: {self.config.excel_dir}")
            return False
        
        # Create markdown directory if it doesn't exist
        if not self.config.dry_run:
            markdown_path.mkdir(parents=True, exist_ok=True)
        
        # Find all Excel files
        excel_files = list(excel_path.rglob("*.xlsx"))
        self.conversion_stats['total_files'] = len(excel_files)
        
        if not excel_files:
            logger.warning("No Excel files found in the specified directory")
            return True
        
        logger.info(f"Found {len(excel_files)} Excel files to convert")
        
        # Convert each file
        for excel_file in excel_files:
            # Determine relative path and create corresponding markdown path
            relative_path = excel_file.relative_to(excel_path)
            markdown_file = markdown_path / relative_path.with_suffix('.md')
            
            # Create subdirectories if needed
            if not self.config.dry_run:
                markdown_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert file
            if self.convert_file(str(excel_file), str(markdown_file)):
                self.conversion_stats['successful_conversions'] += 1
            else:
                self.conversion_stats['failed_conversions'] += 1
        
        # Log summary
        logger.info(f"Conversion complete: {self.conversion_stats['successful_conversions']}/{self.conversion_stats['total_files']} files converted successfully")
        
        if self.conversion_stats['errors']:
            logger.error(f"Errors encountered: {len(self.conversion_stats['errors'])}")
            for error in self.conversion_stats['errors']:
                logger.error(f"  - {error}")
        
        return self.conversion_stats['failed_conversions'] == 0
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate conversion report"""
        return {
            'total_files': self.conversion_stats['total_files'],
            'successful_conversions': self.conversion_stats['successful_conversions'],
            'failed_conversions': self.conversion_stats['failed_conversions'],
            'success_rate': (self.conversion_stats['successful_conversions'] / self.conversion_stats['total_files'] * 100) if self.conversion_stats['total_files'] > 0 else 0,
            'errors': self.conversion_stats['errors']
        }

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Advanced Excel to Markdown Converter')
    parser.add_argument('--excel-dir', default='checklists/excel', help='Excel directory path')
    parser.add_argument('--markdown-dir', default='checklists/markdown', help='Markdown directory path')
    parser.add_argument('--config', default='config/conversion_config.json', help='Configuration file path')
    parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without writing files')
    parser.add_argument('--no-backup', action='store_true', help='Disable backup creation')
    parser.add_argument('--no-validation', action='store_true', help='Disable validation')
    parser.add_argument('--file', help='Convert a specific file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create configuration
    config = ConversionConfig(
        excel_dir=args.excel_dir,
        markdown_dir=args.markdown_dir,
        config_file=args.config,
        backup_enabled=not args.no_backup,
        validation_enabled=not args.no_validation,
        dry_run=args.dry_run
    )
    
    # Create converter
    converter = ExcelConverter(config)
    
    try:
        if args.file:
            # Convert single file
            success = converter.convert_file(args.file)
        else:
            # Convert all files
            success = converter.convert_all_files()
        
        # Generate and display report
        report = converter.generate_report()
        print(f"\nConversion Report:")
        print(f"Total files: {report['total_files']}")
        print(f"Successful: {report['successful_conversions']}")
        print(f"Failed: {report['failed_conversions']}")
        print(f"Success rate: {report['success_rate']:.1f}%")
        
        if report['errors']:
            print(f"\nErrors:")
            for error in report['errors']:
                print(f"  - {error}")
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("Conversion interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
