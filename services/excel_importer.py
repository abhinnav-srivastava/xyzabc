import os
import pandas as pd
from typing import Dict, List, Any, Optional
from pathlib import Path


class ExcelImporter:
    """Service to import Excel checklists and convert them to Markdown format"""
    
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.checklists_dir = os.path.join(base_dir, "checklists")
    
    def parse_excel_file(self, file_path: str, sheet_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Parse an Excel file and extract checklist items
        
        Expected Excel format:
        - Column A: Item Text (required)
        - Column B: Item Type (MUST/GOOD/OPTIONAL) (optional)
        - Column C: Details/Guidelines (optional)
        - Column D: Description (optional)
        """
        try:
            # Read Excel file
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            else:
                df = pd.read_excel(file_path)
            
            # Normalize column names (case insensitive)
            df.columns = df.columns.str.strip().str.lower()
            
            # Map columns to expected names
            column_mapping = {}
            for col in df.columns:
                if 'item' in col and 'text' in col:
                    column_mapping[col] = 'item_text'
                elif 'type' in col:
                    column_mapping[col] = 'item_type'
                elif 'detail' in col or 'guideline' in col:
                    column_mapping[col] = 'details'
                elif 'description' in col or 'desc' in col:
                    column_mapping[col] = 'description'
            
            # If no explicit mapping found, use first few columns
            if not column_mapping:
                columns = list(df.columns)
                if len(columns) >= 1:
                    column_mapping[columns[0]] = 'item_text'
                if len(columns) >= 2:
                    column_mapping[columns[1]] = 'item_type'
                if len(columns) >= 3:
                    column_mapping[columns[2]] = 'details'
                if len(columns) >= 4:
                    column_mapping[columns[3]] = 'description'
            
            # Rename columns
            df = df.rename(columns=column_mapping)
            
            # Extract items
            items = []
            for idx, row in df.iterrows():
                item_text = str(row.get('item_text', '')).strip()
                if not item_text or item_text.lower() in ['nan', 'none', '']:
                    continue
                
                item_type = str(row.get('item_type', '')).strip().lower()
                if item_type in ['nan', 'none', '']:
                    item_type = 'good'  # default
                elif 'must' in item_type or 'required' in item_type or 'critical' in item_type:
                    item_type = 'must'
                elif 'optional' in item_type or 'recommended' in item_type:
                    item_type = 'optional'
                else:
                    item_type = 'good'
                
                details = str(row.get('details', '')).strip()
                if details in ['nan', 'none', '']:
                    details = None
                
                description = str(row.get('description', '')).strip()
                if description in ['nan', 'none', '']:
                    description = None
                
                items.append({
                    'text': item_text,
                    'type': item_type,
                    'details': details,
                    'description': description
                })
            
            return items
            
        except Exception as e:
            raise Exception(f"Error parsing Excel file: {str(e)}")
    
    def convert_to_markdown(self, items: List[Dict[str, Any]]) -> str:
        """Convert checklist items to Markdown format"""
        markdown_lines = []
        
        for item in items:
            # Main item line
            item_text = item['text']
            item_type = item.get('type', 'good')
            
            # Add type annotation to the text
            if item_type == 'must':
                item_text += " (MUST)"
            elif item_type == 'optional':
                item_text += " (OPTIONAL)"
            # 'good' items don't need annotation as it's the default
            
            markdown_lines.append(f"- {item_text}")
            
            # Add details if present
            if item.get('details'):
                details = item['details']
                # Split details by common separators if it's a long text
                if ';' in details:
                    detail_items = [d.strip() for d in details.split(';') if d.strip()]
                elif '\n' in details:
                    detail_items = [d.strip() for d in details.split('\n') if d.strip()]
                else:
                    detail_items = [details]
                
                for detail in detail_items:
                    markdown_lines.append(f"  - {detail}")
            
            # Add description if present (as a comment)
            if item.get('description'):
                markdown_lines.append(f"  <!-- {item['description']} -->")
        
        return '\n'.join(markdown_lines)
    
    def import_excel_to_markdown(self, excel_path: str, role_id: str, category_id: str, 
                                sheet_name: Optional[str] = None) -> str:
        """
        Import Excel file and convert to Markdown, saving to the appropriate location
        
        Returns the path to the created Markdown file
        """
        # Parse Excel file
        items = self.parse_excel_file(excel_path, sheet_name)
        
        # Convert to Markdown
        markdown_content = self.convert_to_markdown(items)
        
        # Create directory structure
        role_dir = os.path.join(self.checklists_dir, role_id)
        os.makedirs(role_dir, exist_ok=True)
        
        # Save Markdown file
        markdown_filename = f"{category_id}.md"
        markdown_path = os.path.join(role_dir, markdown_filename)
        
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return markdown_path
    
    def get_excel_sheets(self, excel_path: str) -> List[str]:
        """Get list of sheet names from an Excel file"""
        try:
            excel_file = pd.ExcelFile(excel_path)
            return excel_file.sheet_names
        except Exception as e:
            raise Exception(f"Error reading Excel file: {str(e)}")
    
    def validate_excel_format(self, excel_path: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate Excel file format and return information about the structure
        
        Returns:
        {
            'valid': bool,
            'message': str,
            'columns': List[str],
            'row_count': int,
            'sample_data': List[Dict]
        }
        """
        try:
            # Read Excel file
            if sheet_name:
                df = pd.read_excel(excel_path, sheet_name=sheet_name)
            else:
                df = pd.read_excel(excel_path)
            
            # Get basic info
            columns = list(df.columns)
            row_count = len(df)
            
            # Get sample data (first 3 rows)
            sample_data = []
            for idx, row in df.head(3).iterrows():
                sample_data.append(row.to_dict())
            
            # Check if we have at least one column with item text
            has_item_text = any('item' in col.lower() or 'text' in col.lower() or 'criteria' in col.lower() 
                              for col in columns)
            
            if not has_item_text:
                return {
                    'valid': False,
                    'message': 'No column found that appears to contain item text. Please ensure you have a column with item descriptions.',
                    'columns': columns,
                    'row_count': row_count,
                    'sample_data': sample_data
                }
            
            return {
                'valid': True,
                'message': f'Excel file format looks good. Found {row_count} rows with {len(columns)} columns.',
                'columns': columns,
                'row_count': row_count,
                'sample_data': sample_data
            }
            
        except Exception as e:
            return {
                'valid': False,
                'message': f'Error reading Excel file: {str(e)}',
                'columns': [],
                'row_count': 0,
                'sample_data': []
            }
