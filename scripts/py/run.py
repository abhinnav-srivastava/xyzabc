#!/usr/bin/env python3
"""
CodeCritique Script Runner
Main entry point for running CodeCritique scripts and utilities.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_setup():
    """Run the setup script."""
    print("Running CodeCritique setup...")
    
    # Determine the appropriate setup script based on OS
    if os.name == 'nt':  # Windows
        if os.path.exists('scripts/powershell/setup.ps1'):
            subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-File', 'scripts/powershell/setup.ps1'])
        elif os.path.exists('scripts/batch/setup.bat'):
            subprocess.run(['scripts/batch/setup.bat'])
    else:  # Unix-like
        if os.path.exists('scripts/shell/setup.sh'):
            subprocess.run(['bash', 'scripts/shell/setup.sh'])
    
    print("Setup completed!")

def run_start():
    """Run the start script."""
    print("Starting CodeCritique...")
    
    # Determine the appropriate start script based on OS
    if os.name == 'nt':  # Windows
        if os.path.exists('scripts/powershell/start.ps1'):
            subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-File', 'scripts/powershell/start.ps1'])
        elif os.path.exists('scripts/batch/start.bat'):
            subprocess.run(['scripts/batch/start.bat'])
    else:  # Unix-like
        if os.path.exists('scripts/shell/start.sh'):
            subprocess.run(['bash', 'scripts/shell/start.sh'])
    
    print("CodeCritique started!")

def convert_excel():
    """Run Excel to Markdown conversion."""
    print("Converting Excel files to Markdown...")
    
    # Run the conversion script
    conversion_script = Path(__file__).parent / 'convert_excel_to_markdown.py'
    if conversion_script.exists():
        subprocess.run([sys.executable, str(conversion_script)])
    else:
        print("Conversion script not found!")
    
    print("Conversion completed!")

def refresh_checklists():
    """Refresh checklists."""
    print("Refreshing checklists...")
    
    # Run the auto-update script
    auto_update_script = Path(__file__).parent / 'auto_update_checklists.py'
    if auto_update_script.exists():
        subprocess.run([sys.executable, str(auto_update_script)])
    else:
        print("Auto-update script not found!")
    
    print("Checklists refreshed!")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='CodeCritique Script Runner')
    parser.add_argument('command', choices=['setup', 'start', 'convert', 'refresh'], 
                       help='Command to run')
    
    args = parser.parse_args()
    
    if args.command == 'setup':
        run_setup()
    elif args.command == 'start':
        run_start()
    elif args.command == 'convert':
        convert_excel()
    elif args.command == 'refresh':
        refresh_checklists()

if __name__ == '__main__':
    main()
