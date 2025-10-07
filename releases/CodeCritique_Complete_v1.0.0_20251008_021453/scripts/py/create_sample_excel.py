#!/usr/bin/env python3
"""
Create a sample Excel file with the new column structure for testing
"""

import pandas as pd
import os
from pathlib import Path

def create_sample_excel():
    """Create sample Excel files with the new column structure"""
    
    # Sample data for different roles
    sample_data = {
        'self': {
            'Category': 'Code Correctness',
            'data': [
                {
                    'SrNo': 1,
                    'Category': 'Code Correctness',
                    'SubCategory': 'Variable Naming',
                    'Description': 'Variables should have meaningful names that describe their purpose',
                    'How to Measure': 'Review variable names for clarity and purpose',
                    'Severity': 'Must',
                    'Rule-Reference': 'CLEAN-001',
                    'AdditionalInfo': 'Use camelCase for variables'
                },
                {
                    'SrNo': 2,
                    'Category': 'Code Correctness',
                    'SubCategory': 'Function Length',
                    'Description': 'Functions should be concise and focused on a single responsibility',
                    'How to Measure': 'Count lines of code in functions',
                    'Severity': 'Good',
                    'Rule-Reference': 'CLEAN-002',
                    'AdditionalInfo': 'Maximum 50 lines per function'
                },
                {
                    'SrNo': 3,
                    'Category': 'Code Correctness',
                    'SubCategory': 'Error Handling',
                    'Description': 'Proper error handling should be implemented',
                    'How to Measure': 'Check for try-catch blocks and error messages',
                    'Severity': 'Must',
                    'Rule-Reference': 'CLEAN-003',
                    'AdditionalInfo': 'Use specific exception types'
                }
            ]
        },
        'peer': {
            'Category': 'Code Review',
            'data': [
                {
                    'SrNo': 1,
                    'Category': 'Code Review',
                    'SubCategory': 'Logic Review',
                    'Description': 'Review the business logic for correctness',
                    'How to Measure': 'Trace through the logic flow',
                    'Severity': 'Must',
                    'Rule-Reference': 'REV-001',
                    'AdditionalInfo': 'Check edge cases'
                },
                {
                    'SrNo': 2,
                    'Category': 'Code Review',
                    'SubCategory': 'Performance Review',
                    'Description': 'Check for performance issues and optimizations',
                    'How to Measure': 'Analyze time complexity',
                    'Severity': 'Good',
                    'Rule-Reference': 'REV-002',
                    'AdditionalInfo': 'Consider Big O notation'
                }
            ]
        }
    }
    
    # Create Excel files for each role
    for role, info in sample_data.items():
        # Create directory if it doesn't exist
        excel_dir = Path(f"checklists/excel/{role}")
        excel_dir.mkdir(parents=True, exist_ok=True)
        
        # Create DataFrame
        df = pd.DataFrame(info['data'])
        
        # Save to Excel
        excel_path = excel_dir / f"{info['Category'].lower().replace(' ', '_')}.xlsx"
        df.to_excel(excel_path, index=False)
        
        print(f"Created sample Excel file: {excel_path}")
    
    print("Sample Excel files created successfully!")

if __name__ == "__main__":
    create_sample_excel()
