"""
Dynamic Categories Service
Generates categories dynamically from Excel files based on MainCategory column
"""

import os
import pandas as pd
import json
from typing import Dict, List, Any, Set
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DynamicCategoriesService:
    """Service for generating dynamic categories from Excel files"""
    
    def __init__(self, excel_dir: str = "checklists/excel"):
        self.excel_dir = Path(excel_dir)
        self.categories_cache = {}
        
    def scan_excel_files(self) -> Dict[str, List[Dict[str, Any]]]:
        """Scan Excel files and extract categories with ordering information"""
        role_categories = {}
        
        if not self.excel_dir.exists():
            logger.warning(f"Excel directory not found: {self.excel_dir}")
            return role_categories
        
        # Scan each role directory (exclude guidelines)
        for role_dir in self.excel_dir.iterdir():
            if not role_dir.is_dir():
                continue
            
            # Skip guidelines directory as it's not a review role
            if role_dir.name == "guidelines":
                continue
                
            role_name = role_dir.name
            categories_info = {}  # category_name -> {order, file_count, files}
            
            # Scan Excel files in this role directory
            excel_files = sorted(role_dir.glob("*.xlsx"))
            for file_order, excel_file in enumerate(excel_files):
                try:
                    df = pd.read_excel(excel_file)
                    
                    # Check if MainCategory column exists
                    if 'MainCategory' in df.columns:
                        # Extract unique categories
                        main_categories = df['MainCategory'].dropna().unique()
                        for category in main_categories:
                            if pd.notna(category) and str(category).strip():
                                category_name = str(category).strip()
                                if category_name not in categories_info:
                                    categories_info[category_name] = {
                                        'name': category_name,
                                        'order': file_order,
                                        'file_count': 0,
                                        'files': []
                                    }
                                categories_info[category_name]['file_count'] += 1
                                categories_info[category_name]['files'].append(excel_file.name)
                    elif 'Category' in df.columns:
                        # Fallback to Category column
                        main_categories = df['Category'].dropna().unique()
                        for category in main_categories:
                            if pd.notna(category) and str(category).strip():
                                category_name = str(category).strip()
                                if category_name not in categories_info:
                                    categories_info[category_name] = {
                                        'name': category_name,
                                        'order': file_order,
                                        'file_count': 0,
                                        'files': []
                                    }
                                categories_info[category_name]['file_count'] += 1
                                categories_info[category_name]['files'].append(excel_file.name)
                    
                except Exception as e:
                    logger.error(f"Error reading Excel file {excel_file}: {e}")
                    continue
            
            if categories_info:
                # Sort categories by order (file order) and then by name
                sorted_categories = sorted(
                    categories_info.values(),
                    key=lambda x: (x['order'], x['name'])
                )
                role_categories[role_name] = sorted_categories
        
        return role_categories
    
    def generate_category_config(self, role_categories: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Generate category configuration from scanned categories"""
        categories = {}
        order = 1
        
        # Collect all unique categories across roles with their ordering info
        all_categories = {}  # category_name -> category_info
        for role_cats in role_categories.values():
            for cat_info in role_cats:
                category_name = cat_info['name']
                if category_name not in all_categories:
                    all_categories[category_name] = cat_info
                else:
                    # If category appears in multiple roles, use the minimum order
                    all_categories[category_name]['order'] = min(
                        all_categories[category_name]['order'],
                        cat_info['order']
                    )
        
        # Sort categories by order and then by name
        sorted_categories = sorted(
            all_categories.values(),
            key=lambda x: (x['order'], x['name'])
        )
        
        # Generate category config for each category
        for cat_info in sorted_categories:
            category_name = cat_info['name']
            category_id = self._generate_category_id(category_name)
            categories[category_id] = {
                "id": category_id,
                "name": category_name,
                "description": f"{category_name} review checklist",
                "icon": self._get_category_icon(category_name),
                "color": self._get_category_color(category_name),
                "enabled": True,
                "order": order,
                "file_count": cat_info.get('file_count', 1),
                "files": cat_info.get('files', [])
            }
            order += 1
        
        return categories
    
    def _generate_category_id(self, category_name: str) -> str:
        """Generate a category ID from category name"""
        # Convert to lowercase, replace spaces with underscores, remove special chars
        import re
        category_id = re.sub(r'[^a-zA-Z0-9\s]', '', category_name.lower())
        category_id = re.sub(r'\s+', '_', category_id.strip())
        return category_id
    
    def _get_category_icon(self, category_name: str) -> str:
        """Get appropriate icon for category"""
        category_lower = category_name.lower()
        
        icon_mapping = {
            'correctness': 'bi-check-circle',
            'readability': 'bi-book',
            'tests': 'bi-bug',
            'functionality': 'bi-lightning',
            'style': 'bi-palette',
            'architecture': 'bi-diagram-3',
            'design': 'bi-layout-text-window',
            'ops': 'bi-gear-wide',
            'security': 'bi-shield-check',
            'performance': 'bi-speedometer2',
            'quality': 'bi-award',
            'maintainability': 'bi-tools',
            'documentation': 'bi-file-text',
            'code review': 'bi-eye',
            'testing': 'bi-bug-fill'
        }
        
        for key, icon in icon_mapping.items():
            if key in category_lower:
                return icon
        
        return 'bi-list-check'  # Default icon
    
    def _get_category_color(self, category_name: str) -> str:
        """Get appropriate color for category"""
        category_lower = category_name.lower()
        
        color_mapping = {
            'correctness': '#28a745',
            'readability': '#17a2b8',
            'tests': '#ffc107',
            'functionality': '#6f42c1',
            'style': '#e83e8c',
            'architecture': '#dc3545',
            'design': '#fd7e14',
            'ops': '#20c997',
            'security': '#dc3545',
            'performance': '#6f42c1',
            'quality': '#28a745',
            'maintainability': '#17a2b8',
            'documentation': '#6c757d',
            'code review': '#007bff',
            'testing': '#ffc107'
        }
        
        for key, color in color_mapping.items():
            if key in category_lower:
                return color
        
        return '#6c757d'  # Default color
    
    def update_app_config(self, config_path: str = "config/app_config.json"):
        """Update app_config.json with dynamic categories"""
        try:
            # Load current config
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Scan Excel files for categories
            role_categories = self.scan_excel_files()
            
            # Generate dynamic categories
            dynamic_categories = self.generate_category_config(role_categories)
            
            # Update categories in config
            config['categories'] = dynamic_categories
            
            # Update role categories
            for role_id, role_config in config.get('roles', {}).items():
                if role_id in role_categories:
                    role_config['categories'] = [
                        self._generate_category_id(cat['name']) 
                        for cat in role_categories[role_id]
                    ]
            
            # Save updated config
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Updated app_config.json with {len(dynamic_categories)} dynamic categories")
            return True
            
        except Exception as e:
            logger.error(f"Error updating app_config.json: {e}")
            return False
    
    def update_roles_config(self, roles_path: str = "config/roles.json"):
        """Update roles.json with dynamic categories based on Excel files"""
        try:
            # Load current roles config
            with open(roles_path, 'r', encoding='utf-8') as f:
                roles_config = json.load(f)
            
            # Scan Excel files for categories
            role_categories = self.scan_excel_files()
            
            # Filter out guidelines role and update each remaining role with dynamic categories
            filtered_roles = []
            for role in roles_config.get('roles', []):
                role_id = role.get('id')
                
                # Skip guidelines role as it's not a review role
                if role_id == "guidelines":
                    logger.info(f"Skipping guidelines role (not a review role)")
                    continue
                    
                if role_id in role_categories:
                    # Generate categories for this role based on Excel files
                    categories = []
                    for cat_info in role_categories[role_id]:
                        category_id = self._generate_category_id(cat_info['name'])
                        category_name = cat_info['name']
                        
                        # Generate markdown file path
                        markdown_path = f"checklists/markdown/{role_id}/{category_id}.md"
                        
                        categories.append({
                            "id": category_id,
                            "name": category_name,
                            "type": "markdown",
                            "path": markdown_path
                        })
                    
                    # Update role categories
                    role['categories'] = categories
                    logger.info(f"Updated role '{role_id}' with {len(categories)} dynamic categories")
                
                # Add role to filtered list
                filtered_roles.append(role)
            
            # Update roles list to exclude guidelines
            roles_config['roles'] = filtered_roles
            
            # Save updated roles config
            with open(roles_path, 'w', encoding='utf-8') as f:
                json.dump(roles_config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Updated roles.json with dynamic categories")
            return True
            
        except Exception as e:
            logger.error(f"Error updating roles.json: {e}")
            return False
    
    def update_all_configs(self):
        """Update both app_config.json and roles.json with dynamic categories"""
        try:
            # Update app_config.json
            app_success = self.update_app_config()
            
            # Update roles.json
            roles_success = self.update_roles_config()
            
            if app_success and roles_success:
                logger.info("✅ Successfully updated both app_config.json and roles.json")
                return True
            else:
                logger.error("❌ Failed to update one or more config files")
                return False
                
        except Exception as e:
            logger.error(f"Error updating configs: {e}")
            return False
    
    def get_dynamic_categories(self) -> Dict[str, Any]:
        """Get current dynamic categories"""
        if not self.categories_cache:
            role_categories = self.scan_excel_files()
            self.categories_cache = self.generate_category_config(role_categories)
        
        return self.categories_cache

# Global instance
dynamic_categories = DynamicCategoriesService()
