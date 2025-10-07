#!/usr/bin/env python3
"""
Portable Build Script for CodeCritique
Creates a standalone executable with all dependencies bundled
"""

import os
import sys
import shutil
import subprocess
import zipfile
import json
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PortableBuilder:
    """Builds a portable version of CodeCritique"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        # Change to project root directory
        os.chdir(self.project_root)
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.portable_dir = self.project_root / "portable"
        self.config_file = self.project_root / "config" / "build_config.json"
        self.load_config()
    
    def load_config(self):
        """Load build configuration from JSON file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            self.app_name = self.config['build']['app_name']
            logger.info(f"Loaded build configuration for {self.app_name}")
        except Exception as e:
            logger.warning(f"Could not load config file, using defaults: {e}")
            self.config = {
                'build': {'app_name': 'CodeCritique'},
                'pyinstaller': {},
                'portable': {}
            }
            self.app_name = 'CodeCritique'
        
    def clean_build_dirs(self):
        """Clean previous build directories"""
        logger.info("Cleaning previous build directories...")
        
        dirs_to_clean = [self.build_dir, self.dist_dir, self.portable_dir]
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                logger.info(f"Cleaned {dir_path}")
    
    def create_pyinstaller_spec(self):
        """Create PyInstaller spec file for the build"""
        # Skip icon for now to avoid conversion issues
        icon_line = "icon=None,"
        
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('config', 'config'),
        ('templates', 'templates'),
        ('static', 'static'),
        ('checklists', 'checklists'),
        ('services', 'services'),
        ('scripts', 'scripts'),
        ('utils', 'utils'),
        ('hooks', 'hooks'),
        ('desktop', 'desktop'),
        ('portable', 'portable'),
        ('dist', 'dist'),
        ('build', 'build'),
        ('requirements.txt', '.'),
        ('README.md', '.'),
        ('LICENSE', '.'),
        ('CodeCritique.spec', '.'),
        ('build.py', '.'),
    ],
    hiddenimports=[
        'flask',
        'pandas',
        'numpy',
        'numpy.core',
        'numpy.core._methods',
        'numpy.lib.format',
        'reportlab',
        'openpyxl',
        'jinja2',
        'werkzeug',
        'markupsafe',
        'itsdangerous',
        'click',
        'blinker',
        'email_validator',
        'importlib_metadata',
        'zipp',
        'subprocess',
        'json',
        'pathlib',
        'logging',
        'zipfile',
        'shutil',
    ],
    hookspath=['hooks'],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'pandas.tests',
        'pytest',
        'unittest',
        'test',
        'tests',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{self.app_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    {icon_line}
)
'''
        
        spec_file = self.project_root / f"{self.app_name}.spec"
        with open(spec_file, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        
        logger.info(f"Created PyInstaller spec file: {spec_file}")
        return spec_file
    
    def build_executable(self):
        """Build the executable using PyInstaller"""
        logger.info("Building executable with PyInstaller...")
        
        try:
            # Create spec file
            spec_file = self.create_pyinstaller_spec()
            
            # Run PyInstaller
            cmd = [
                sys.executable, '-m', 'PyInstaller',
                '--clean',
                '--noconfirm',
                str(spec_file)
            ]
            
            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"PyInstaller failed: {result.stderr}")
                return False
            
            logger.info("Executable built successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error building executable: {e}")
            return False
    
    def create_portable_package(self):
        """Create portable package with all necessary files"""
        logger.info("Creating portable package...")
        
        # Create portable directory
        self.portable_dir.mkdir(exist_ok=True)
        
        # Copy executable
        exe_path = self.dist_dir / f"{self.app_name}.exe"
        if exe_path.exists():
            shutil.copy2(exe_path, self.portable_dir / f"{self.app_name}.exe")
            logger.info(f"Copied executable: {exe_path}")
        else:
            logger.error(f"Executable not found: {exe_path}")
            return False
        
        # Copy additional files
        files_to_copy = [
            'README.md',
            'LICENSE',
            'requirements.txt',
        ]
        
        for file_name in files_to_copy:
            src_file = self.project_root / file_name
            if src_file.exists():
                shutil.copy2(src_file, self.portable_dir / file_name)
                logger.info(f"Copied {file_name}")
        
        # Create startup script
        self.create_startup_script()
        
        # Create README for portable version
        self.create_portable_readme()
        
        logger.info("Portable package created successfully!")
        return True
    
    def create_startup_script(self):
        """Create startup script for the portable version"""
        startup_script = self.portable_dir / "start.bat"
        startup_content = '''@echo off
echo Starting CodeCritique...
echo.
echo The application will start in your default web browser.
echo.
echo To stop the application, close this window or press Ctrl+C
echo.
CodeCritique.exe
pause
'''
        
        with open(startup_script, 'w', encoding='utf-8') as f:
            f.write(startup_content)
        
        logger.info(f"Created startup script: {startup_script}")
    
    def create_portable_readme(self):
        """Create README for portable version"""
        readme_content = '''# CodeCritique - Portable Version

## 🚀 Quick Start

1. **Double-click `start.bat`** to start the application
2. **Open your browser** and go to http://localhost:5000
3. **Start using CodeCritique** immediately!

## 📋 Features

- ✅ **No Installation Required** - Runs directly from this folder
- ✅ **No Dependencies** - Everything is bundled
- ✅ **Portable** - Copy to any Windows computer and run
- ✅ **Self-Contained** - No Python or other software needed

## 🔧 Usage

### Starting the Application
- **Double-click `start.bat`** - Easiest way to start
- **Or run `CodeCritique.exe`** directly from command line

### Stopping the Application
- **Close the command window** - Stops the application
- **Or press Ctrl+C** in the command window

### Accessing the Application
- **Open your web browser**
- **Go to http://localhost:5000**
- **Start your code reviews!**

## 📁 What's Included

- `CodeCritique.exe` - Main application executable
- `start.bat` - Easy startup script
- `README.md` - This file
- `LICENSE` - Apache 2.0 License
- All necessary data files and configurations

## 🎯 System Requirements

- **Windows 7/8/10/11** (64-bit)
- **No Python installation required**
- **No additional dependencies needed**
- **Internet connection** (for initial setup only)

## 🚀 Distribution

This portable version can be:
- **Copied to any Windows computer**
- **Run from USB drive**
- **Distributed as a ZIP file**
- **No installation required**

## 📞 Support

For issues or questions:
- Check the main README.md for detailed documentation
- Review the LICENSE file for usage terms
- The application includes built-in help and documentation

---
**CodeCritique** - Professional code review tool
Licensed under Apache 2.0 License
'''
        
        readme_file = self.portable_dir / "README_Portable.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        logger.info(f"Created portable README: {readme_file}")
    
    def create_distribution_zip(self):
        """Create ZIP file for distribution"""
        logger.info("Creating distribution ZIP file...")
        
        zip_path = self.project_root / f"{self.app_name}_Portable.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.portable_dir):
                for file in files:
                    file_path = Path(root) / file
                    arc_path = file_path.relative_to(self.portable_dir)
                    zipf.write(file_path, arc_path)
        
        logger.info(f"Created distribution ZIP: {zip_path}")
        return zip_path
    
    def build(self):
        """Main build process"""
        logger.info("Starting portable build process...")
        
        try:
            # Step 1: Clean previous builds
            self.clean_build_dirs()
            
            # Step 2: Build executable
            if not self.build_executable():
                logger.error("❌ Failed to build executable")
                return False
            
            # Step 3: Create portable package
            if not self.create_portable_package():
                logger.error("❌ Failed to create portable package")
                return False
            
            # Step 4: Create distribution ZIP
            zip_path = self.create_distribution_zip()
            
            logger.info("Portable build completed successfully!")
            logger.info(f"Distribution package: {zip_path}")
            logger.info(f"Portable directory: {self.portable_dir}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Build failed: {e}")
            return False

def main():
    """Main function"""
    builder = PortableBuilder()
    success = builder.build()
    
    if success:
        print("\nBuild completed successfully!")
        print(f"Distribution ZIP: {builder.project_root / f'{builder.app_name}_Portable.zip'}")
        print(f"Portable directory: {builder.portable_dir}")
        print("\nYou can now distribute the ZIP file or the portable directory!")
    else:
        print("\nBuild failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
