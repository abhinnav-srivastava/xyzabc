#!/usr/bin/env python3
"""
Comprehensive Build Script for CodeCritique
Creates both portable executable and desktop app distributions
"""

import os
import sys
import shutil
import subprocess
import zipfile
import json
import platform
from pathlib import Path
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CodeCritiqueBuilder:
    """Builds CodeCritique in multiple formats"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.portable_dir = self.project_root / "portable"
        self.desktop_dir = self.project_root / "desktop"
        self.releases_dir = self.project_root / "releases"
        self.config_file = self.project_root / "config" / "build_config.json"
        self.load_config()
        
    def load_config(self):
        """Load build configuration"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            self.app_name = self.config['build']['app_name']
            self.version = self.config['build']['version']
            logger.info(f"Loaded build configuration for {self.app_name} v{self.version}")
        except Exception as e:
            logger.warning(f"Could not load config file, using defaults: {e}")
            self.config = {
                'build': {'app_name': 'CodeCritique', 'version': '1.0.0'},
                'pyinstaller': {},
                'portable': {}
            }
            self.app_name = 'CodeCritique'
            self.version = '1.0.0'
    
    def clean_build_dirs(self):
        """Clean previous build directories"""
        logger.info("Cleaning previous build directories...")
        
        dirs_to_clean = [self.build_dir, self.dist_dir, self.portable_dir, self.releases_dir]
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                logger.info(f"Cleaned {dir_path}")
    
    def build_portable(self):
        """Build portable executable"""
        logger.info("Building portable executable...")
        
        try:
            # Import and run the portable builder
            sys.path.append(str(self.project_root / "scripts" / "py"))
            from build_portable import PortableBuilder
            
            builder = PortableBuilder()
            success = builder.build()
            
            if success:
                logger.info("✅ Portable build completed successfully!")
                return True
            else:
                logger.error("❌ Portable build failed!")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error building portable: {e}")
            return False
    
    def build_desktop(self):
        """Build desktop app using Electron"""
        logger.info("Building desktop app...")
        
        try:
            # Check if Node.js is available
            try:
                subprocess.run(['node', '--version'], capture_output=True, check=True)
                subprocess.run(['npm', '--version'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.error("❌ Node.js and npm are required for desktop app build")
                logger.info("Please install Node.js from https://nodejs.org/")
                return False
            
            # Install Electron dependencies
            logger.info("Installing Electron dependencies...")
            os.chdir(self.desktop_dir)
            
            # Install dependencies
            subprocess.run(['npm', 'install'], check=True)
            
            # Build desktop app
            logger.info("Building desktop app with Electron Builder...")
            
            # Copy the portable executable to desktop assets
            portable_exe = self.dist_dir / f"{self.app_name}.exe"
            if portable_exe.exists():
                desktop_dist = self.desktop_dir / "dist"
                desktop_dist.mkdir(exist_ok=True)
                shutil.copy2(portable_exe, desktop_dist / f"{self.app_name}.exe")
                logger.info("Copied portable executable to desktop build")
            else:
                logger.error("Portable executable not found. Please build portable first.")
                return False
            
            # Build for current platform
            if platform.system() == "Windows":
                subprocess.run(['npm', 'run', 'build-win'], check=True)
            elif platform.system() == "Darwin":
                subprocess.run(['npm', 'run', 'build-mac'], check=True)
            else:
                subprocess.run(['npm', 'run', 'build-linux'], check=True)
            
            logger.info("✅ Desktop app build completed successfully!")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Desktop build failed: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error building desktop app: {e}")
            return False
        finally:
            os.chdir(self.project_root)
    
    def create_release_packages(self):
        """Create release packages for distribution"""
        logger.info("Creating release packages...")
        
        self.releases_dir.mkdir(exist_ok=True)
        
        # Create portable release
        if self.portable_dir.exists():
            portable_zip = self.releases_dir / f"{self.app_name}_Portable_v{self.version}.zip"
            self.create_zip(self.portable_dir, portable_zip)
            logger.info(f"Created portable release: {portable_zip}")
        
        # Create desktop release
        desktop_dist = self.desktop_dir / "dist"
        if desktop_dist.exists():
            desktop_zip = self.releases_dir / f"{self.app_name}_Desktop_v{self.version}.zip"
            self.create_zip(desktop_dist, desktop_zip)
            logger.info(f"Created desktop release: {desktop_zip}")
        
        # Create combined release
        combined_dir = self.releases_dir / f"{self.app_name}_Combined_v{self.version}"
        combined_dir.mkdir(exist_ok=True)
        
        if self.portable_dir.exists():
            shutil.copytree(self.portable_dir, combined_dir / "Portable", dirs_exist_ok=True)
        
        if desktop_dist.exists():
            shutil.copytree(desktop_dist, combined_dir / "Desktop", dirs_exist_ok=True)
        
        # Create combined README
        self.create_combined_readme(combined_dir)
        
        # Create combined ZIP
        combined_zip = self.releases_dir / f"{self.app_name}_Combined_v{self.version}.zip"
        self.create_zip(combined_dir, combined_zip)
        logger.info(f"Created combined release: {combined_zip}")
    
    def create_zip(self, source_dir, zip_path):
        """Create ZIP file from directory"""
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = Path(root) / file
                    arc_path = file_path.relative_to(source_dir)
                    zipf.write(file_path, arc_path)
    
    def create_combined_readme(self, combined_dir):
        """Create README for combined release"""
        readme_content = f'''# CodeCritique v{self.version} - Combined Release

## 🚀 What's Included

This release contains both portable and desktop versions of CodeCritique:

### 📦 Portable Version (`Portable/` folder)
- **No Installation Required** - Runs directly from the folder
- **No Dependencies** - Everything is bundled
- **Cross-Platform** - Works on Windows, macOS, Linux
- **USB Portable** - Copy to any computer and run

### 🖥️ Desktop Version (`Desktop/` folder)
- **Native Desktop App** - Built with Electron
- **System Integration** - Menu bar, keyboard shortcuts
- **Professional UI** - Enhanced desktop experience
- **Auto-Updates** - Built-in update mechanism

## 🎯 Quick Start

### Portable Version
1. Navigate to the `Portable/` folder
2. Double-click `start.bat` (Windows) or `start.sh` (macOS/Linux)
3. Open your browser to http://localhost:5000

### Desktop Version
1. Navigate to the `Desktop/` folder
2. Run the installer for your platform:
   - **Windows**: `CodeCritique Setup.exe`
   - **macOS**: `CodeCritique.dmg`
   - **Linux**: `CodeCritique.AppImage` or `CodeCritique.deb`

## 📋 Features

- ✅ **Role-Based Reviews** - Architect, Developer, Tech Lead, etc.
- ✅ **Category-Driven Checklists** - Organized by review categories
- ✅ **Excel Integration** - Import/export Excel checklists
- ✅ **PWA Support** - Progressive Web App capabilities
- ✅ **Offline Mode** - Works without internet connection
- ✅ **Responsive Design** - Works on desktop, tablet, mobile
- ✅ **Professional UI** - Clean, modern interface

## 🔧 System Requirements

### Portable Version
- **Windows**: 7/8/10/11 (64-bit)
- **macOS**: 10.14+ (64-bit)
- **Linux**: Ubuntu 18.04+, CentOS 7+, etc.
- **No Python installation required**

### Desktop Version
- **Windows**: 10/11 (64-bit)
- **macOS**: 10.15+ (64-bit/ARM64)
- **Linux**: Ubuntu 18.04+, CentOS 7+, etc.

## 📞 Support

For issues or questions:
- Check the main README.md for detailed documentation
- Review the LICENSE file for usage terms
- The application includes built-in help and documentation

## 📄 License

Licensed under Apache 2.0 License - see LICENSE file for details.

---
**CodeCritique** - Professional code review tool
Version {self.version}
'''
        
        readme_file = combined_dir / "README.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
    
    def build_all(self, portable_only=False, desktop_only=False):
        """Build all distributions"""
        logger.info("Starting comprehensive build process...")
        
        try:
            # Step 1: Clean previous builds
            self.clean_build_dirs()
            
            success = True
            
            # Step 2: Build portable (if requested)
            if not desktop_only:
                if not self.build_portable():
                    success = False
            
            # Step 3: Build desktop (if requested)
            if not portable_only:
                if not self.build_desktop():
                    success = False
            
            # Step 4: Create release packages
            if success:
                self.create_release_packages()
                logger.info("✅ All builds completed successfully!")
                
                # Show results
                logger.info(f"📦 Release packages created in: {self.releases_dir}")
                for item in self.releases_dir.iterdir():
                    if item.is_file():
                        logger.info(f"  - {item.name}")
                
                return True
            else:
                logger.error("❌ Some builds failed!")
                return False
                
        except Exception as e:
            logger.error(f"❌ Build process failed: {e}")
            return False

def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(description='Build CodeCritique distributions')
    parser.add_argument('--portable-only', action='store_true', 
                        help='Build only portable version')
    parser.add_argument('--desktop-only', action='store_true', 
                        help='Build only desktop version')
    parser.add_argument('--clean', action='store_true', 
                        help='Clean build directories only')
    
    args = parser.parse_args()
    
    builder = CodeCritiqueBuilder()
    
    if args.clean:
        builder.clean_build_dirs()
        print("✅ Build directories cleaned!")
        return
    
    if args.portable_only and args.desktop_only:
        print("❌ Cannot specify both --portable-only and --desktop-only")
        sys.exit(1)
    
    success = builder.build_all(
        portable_only=args.portable_only,
        desktop_only=args.desktop_only
    )
    
    if success:
        print("\n🎉 All builds completed successfully!")
        print(f"📦 Release packages: {builder.releases_dir}")
        print("\n🚀 You can now distribute the release packages!")
    else:
        print("\n❌ Build failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()

