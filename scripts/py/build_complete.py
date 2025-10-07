#!/usr/bin/env python3
"""
Complete Build Script for CodeCritique
Creates a comprehensive distribution package with all files and folders
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
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CompleteBuilder:
    """Builds a complete distribution package for CodeCritique"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        # Change to project root directory
        os.chdir(self.project_root)
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.portable_dir = self.project_root / "portable"
        self.releases_dir = self.project_root / "releases"
        self.config_file = self.project_root / "config" / "build_config.json"
        self.load_config()
        
    def load_config(self):
        """Load build configuration from JSON file"""
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
    
    def create_comprehensive_spec(self):
        """Create comprehensive PyInstaller spec file"""
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # Core application files
        ('config', 'config'),
        ('templates', 'templates'),
        ('static', 'static'),
        ('checklists', 'checklists'),
        ('services', 'services'),
        ('scripts', 'scripts'),
        ('utils', 'utils'),
        ('hooks', 'hooks'),
        
        # Desktop app files
        ('desktop', 'desktop'),
        
        # Documentation and configuration
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
        'datetime',
        'typing',
        'functools',
        'collections',
        'itertools',
        'operator',
        're',
        'io',
        'time',
        'sys',
        'os',
        'platform',
        'argparse',
        'tempfile',
        'glob',
        'fnmatch',
        'stat',
        'hashlib',
        'base64',
        'urllib',
        'urllib.parse',
        'urllib.request',
        'http',
        'http.server',
        'socket',
        'threading',
        'multiprocessing',
        'queue',
        'concurrent',
        'concurrent.futures',
        'asyncio',
        'ssl',
        'certifi',
        'charset_normalizer',
        'idna',
        'requests',
        'urllib3',
        'six',
        'python_dateutil',
        'pytz',
        'tzlocal',
        'backports',
        'backports.zoneinfo',
        'setuptools',
        'pkg_resources',
        'distutils',
        'distutils.util',
        'distutils.version',
        'distutils.sysconfig',
        'distutils.errors',
        'distutils.filelist',
        'distutils.dir_util',
        'distutils.file_util',
        'distutils.archive_util',
        'distutils.dep_util',
        'distutils.spawn',
        'distutils.util',
        'distutils.version',
        'distutils.sysconfig',
        'distutils.errors',
        'distutils.filelist',
        'distutils.dir_util',
        'distutils.file_util',
        'distutils.archive_util',
        'distutils.dep_util',
        'distutils.spawn',
        'distutils.util',
        'distutils.version',
        'distutils.sysconfig',
        'distutils.errors',
        'distutils.filelist',
        'distutils.dir_util',
        'distutils.file_util',
        'distutils.archive_util',
        'distutils.dep_util',
        'distutils.spawn',
        'distutils.util',
        'distutils.version',
        'distutils.sysconfig',
        'distutils.errors',
        'distutils.filelist',
        'distutils.dir_util',
        'distutils.file_util',
        'distutils.archive_util',
        'distutils.dep_util',
        'distutils.spawn',
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
        'IPython',
        'jupyter',
        'notebook',
        'spyder',
        'pycharm',
        'vscode',
        'sublime',
        'atom',
        'vim',
        'emacs',
        'nano',
        'gedit',
        'kate',
        'kwrite',
        'kdevelop',
        'qtcreator',
        'codeblocks',
        'devcpp',
        'turbo',
        'borland',
        'watcom',
        'microsoft',
        'intel',
        'gcc',
        'clang',
        'mingw',
        'cygwin',
        'msys',
        'msys2',
        'git',
        'svn',
        'hg',
        'bzr',
        'cvs',
        'rcs',
        'sccs',
        'clearcase',
        'perforce',
        'tfs',
        'vss',
        'vsts',
        'azure',
        'aws',
        'gcp',
        'heroku',
        'docker',
        'kubernetes',
        'openshift',
        'rancher',
        'mesos',
        'marathon',
        'chronos',
        'aurora',
        'nomad',
        'consul',
        'vault',
        'terraform',
        'ansible',
        'chef',
        'puppet',
        'salt',
        'fabric',
        'capistrano',
        'deploy',
        'ci',
        'cd',
        'jenkins',
        'travis',
        'circle',
        'appveyor',
        'bamboo',
        'teamcity',
        'gitlab',
        'github',
        'bitbucket',
        'azure',
        'aws',
        'gcp',
        'heroku',
        'docker',
        'kubernetes',
        'openshift',
        'rancher',
        'mesos',
        'marathon',
        'chronos',
        'aurora',
        'nomad',
        'consul',
        'vault',
        'terraform',
        'ansible',
        'chef',
        'puppet',
        'salt',
        'fabric',
        'capistrano',
        'deploy',
        'ci',
        'cd',
        'jenkins',
        'travis',
        'circle',
        'appveyor',
        'bamboo',
        'teamcity',
        'gitlab',
        'github',
        'bitbucket',
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
    icon=None,
)
'''
        
        spec_file = self.project_root / f"{self.app_name}_Complete.spec"
        with open(spec_file, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        
        logger.info(f"Created comprehensive PyInstaller spec file: {spec_file}")
        return spec_file
    
    def build_executable(self):
        """Build the executable using PyInstaller"""
        logger.info("Building comprehensive executable with PyInstaller...")
        
        try:
            # Create spec file
            spec_file = self.create_comprehensive_spec()
            
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
    
    def create_complete_package(self):
        """Create complete package with all files"""
        logger.info("Creating complete distribution package...")
        
        # Create releases directory
        self.releases_dir.mkdir(exist_ok=True)
        
        # Create timestamp for versioning
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        package_name = f"{self.app_name}_Complete_v{self.version}_{timestamp}"
        package_dir = self.releases_dir / package_name
        package_dir.mkdir(exist_ok=True)
        
        # Copy executable
        exe_path = self.dist_dir / f"{self.app_name}.exe"
        if exe_path.exists():
            shutil.copy2(exe_path, package_dir / f"{self.app_name}.exe")
            logger.info(f"Copied executable: {exe_path}")
        else:
            logger.error(f"Executable not found: {exe_path}")
            return False
        
        # Copy all project files and directories
        items_to_copy = [
            'config',
            'templates', 
            'static',
            'checklists',
            'services',
            'scripts',
            'utils',
            'hooks',
            'desktop',
            'portable',
            'requirements.txt',
            'README.md',
            'LICENSE',
            'CodeCritique.spec',
            'build.py',
        ]
        
        for item in items_to_copy:
            src_path = self.project_root / item
            if src_path.exists():
                if src_path.is_dir():
                    shutil.copytree(src_path, package_dir / item, dirs_exist_ok=True)
                    logger.info(f"Copied directory: {item}")
                else:
                    shutil.copy2(src_path, package_dir / item)
                    logger.info(f"Copied file: {item}")
        
        # Create startup scripts
        self.create_startup_scripts(package_dir)
        
        # Create comprehensive README
        self.create_comprehensive_readme(package_dir)
        
        # Create installation guide
        self.create_installation_guide(package_dir)
        
        logger.info(f"Complete package created: {package_dir}")
        return package_dir
    
    def create_startup_scripts(self, package_dir):
        """Create startup scripts for different platforms"""
        
        # Windows batch script
        windows_script = package_dir / "start.bat"
        windows_content = '''@echo off
title CodeCritique - Professional Code Review Tool
echo.
echo ========================================
echo   CodeCritique - Professional Code Review Tool
echo ========================================
echo.
echo Starting the application...
echo.
echo The application will start in your default web browser.
echo.
echo To stop the application, close this window or press Ctrl+C
echo.
echo ========================================
echo.
CodeCritique.exe
echo.
echo Application stopped.
pause
'''
        
        with open(windows_script, 'w', encoding='utf-8') as f:
            f.write(windows_content)
        
        # Linux/Mac shell script
        unix_script = package_dir / "start.sh"
        unix_content = '''#!/bin/bash

echo "========================================"
echo "  CodeCritique - Professional Code Review Tool"
echo "========================================"
echo ""
echo "Starting the application..."
echo ""
echo "The application will start in your default web browser."
echo ""
echo "To stop the application, close this terminal or press Ctrl+C"
echo ""
echo "========================================"
echo ""

./CodeCritique

echo ""
echo "Application stopped."
'''
        
        with open(unix_script, 'w', encoding='utf-8') as f:
            f.write(unix_content)
        
        # Make unix script executable
        os.chmod(unix_script, 0o755)
        
        logger.info("Created startup scripts for all platforms")
    
    def create_comprehensive_readme(self, package_dir):
        """Create comprehensive README for the complete package"""
        readme_content = f'''# CodeCritique v{self.version} - Complete Distribution

## 🚀 Professional Code Review Tool

CodeCritique is a comprehensive code review tool designed for professional development teams. It provides role-based checklists, category-driven reviews, and seamless integration with your existing workflow.

## 📦 What's Included

This complete distribution includes:

### 🖥️ **Executable Application**
- `CodeCritique.exe` - Main application executable (Windows)
- `CodeCritique` - Main application executable (Linux/Mac)
- No Python installation required
- All dependencies bundled

### 📁 **Complete Source Code**
- `config/` - Configuration files and settings
- `templates/` - HTML templates for the web interface
- `static/` - CSS, JavaScript, and static assets
- `checklists/` - Excel and Markdown checklist files
- `services/` - Backend service modules
- `scripts/` - Build and utility scripts
- `utils/` - Utility functions and helpers
- `hooks/` - PyInstaller hooks
- `desktop/` - Desktop application files
- `portable/` - Portable version files

### 📋 **Documentation**
- `README.md` - This comprehensive guide
- `LICENSE` - Apache 2.0 License
- `requirements.txt` - Python dependencies
- `CodeCritique.spec` - PyInstaller specification
- `build.py` - Build script

## 🎯 Quick Start

### Windows
1. **Double-click `start.bat`** to start the application
2. **Open your browser** and go to http://localhost:5000
3. **Start using CodeCritique** immediately!

### Linux/Mac
1. **Run `./start.sh`** in terminal to start the application
2. **Open your browser** and go to http://localhost:5000
3. **Start using CodeCritique** immediately!

## 🔧 Features

### ✅ **Role-Based Reviews**
- **Architect** - System architecture and design reviews
- **Developer** - Code quality and implementation reviews
- **Tech Lead** - Technical leadership and mentoring reviews
- **Peer** - Peer review and collaboration
- **Self** - Self-assessment and improvement

### ✅ **Category-Driven Checklists**
- **Architecture** - System design and structure
- **Design** - Software design patterns and principles
- **Correctness** - Bug prevention and code accuracy
- **Readability** - Code clarity and maintainability
- **Tests** - Testing strategies and coverage
- **Functionality** - Feature implementation and logic
- **Style** - Coding standards and conventions
- **Operations** - Deployment and maintenance

### ✅ **Advanced Features**
- **Excel Integration** - Import/export Excel checklists
- **PWA Support** - Progressive Web App capabilities
- **Offline Mode** - Works without internet connection
- **Responsive Design** - Works on desktop, tablet, mobile
- **Professional UI** - Clean, modern interface
- **Export Reports** - HTML and PDF report generation
- **Dynamic Categories** - Auto-updating checklist categories

## 🎨 User Interface

### **Modern Design**
- Clean, professional interface
- Responsive layout for all devices
- Intuitive navigation and workflow
- Color-coded status indicators
- Progress tracking and statistics

### **Review Process**
1. **Select Role** - Choose your review role
2. **Start Review** - Begin the review process
3. **Complete Checklists** - Work through category-based checklists
4. **Add Comments** - Provide detailed feedback
5. **Generate Report** - Export comprehensive reports

## 🔧 System Requirements

### **Minimum Requirements**
- **Windows**: 7/8/10/11 (64-bit)
- **macOS**: 10.14+ (64-bit)
- **Linux**: Ubuntu 18.04+, CentOS 7+, etc.
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 500MB free space
- **Network**: Internet connection for initial setup

### **Recommended Requirements**
- **RAM**: 8GB or more
- **Storage**: 1GB free space
- **Network**: Stable internet connection
- **Browser**: Chrome, Firefox, Safari, or Edge (latest versions)

## 🚀 Distribution

### **Portable Distribution**
- **Copy to any computer** - No installation required
- **Run from USB drive** - Fully portable
- **No dependencies** - Everything bundled
- **Cross-platform** - Works on Windows, Mac, Linux

### **Enterprise Deployment**
- **Network deployment** - Deploy across your organization
- **Custom configuration** - Tailor to your needs
- **Integration ready** - Works with existing tools
- **Scalable** - Handles large teams and projects

## 📞 Support and Documentation

### **Built-in Help**
- **Interactive tutorials** - Learn as you go
- **Context-sensitive help** - Get help when you need it
- **Best practices guide** - Professional review techniques
- **FAQ section** - Common questions and answers

### **External Resources**
- **GitHub Repository** - Source code and issues
- **Documentation** - Comprehensive guides and tutorials
- **Community** - User forums and discussions
- **Professional Support** - Enterprise support available

## 📄 License and Legal

### **Open Source License**
- **Apache 2.0 License** - Permissive open source license
- **Commercial use allowed** - Use in commercial projects
- **Modification allowed** - Customize to your needs
- **Distribution allowed** - Share with your team

### **Compliance**
- **GDPR Compliant** - Privacy and data protection
- **Enterprise Ready** - Meets enterprise security standards
- **Audit Trail** - Complete review history and tracking
- **Data Export** - Export all data in standard formats

## 🎯 Use Cases

### **Software Development**
- **Code Reviews** - Comprehensive code quality reviews
- **Architecture Reviews** - System design and structure
- **Security Audits** - Security vulnerability assessments
- **Performance Reviews** - Optimization and efficiency

### **Quality Assurance**
- **Process Improvement** - Streamline review processes
- **Team Training** - Educate team members on best practices
- **Compliance** - Meet regulatory and industry standards
- **Documentation** - Maintain comprehensive review records

### **Project Management**
- **Progress Tracking** - Monitor review completion
- **Resource Planning** - Allocate review resources
- **Timeline Management** - Schedule and track reviews
- **Reporting** - Generate management reports

## 🔮 Future Roadmap

### **Planned Features**
- **AI-Powered Reviews** - Automated code analysis
- **Integration APIs** - Connect with development tools
- **Advanced Analytics** - Detailed metrics and insights
- **Mobile Apps** - Native mobile applications

### **Community Contributions**
- **Open Source** - Community-driven development
- **Plugin System** - Extensible architecture
- **Custom Checklists** - User-defined review criteria
- **Theme Support** - Customizable user interface

---

**CodeCritique** - Professional Code Review Tool  
Version {self.version}  
Licensed under Apache 2.0 License  

For support, documentation, and updates, visit our GitHub repository.
'''
        
        readme_file = package_dir / "README.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        logger.info(f"Created comprehensive README: {readme_file}")
    
    def create_installation_guide(self, package_dir):
        """Create installation and setup guide"""
        install_guide = package_dir / "INSTALLATION.md"
        install_content = f'''# CodeCritique Installation Guide

## 🚀 Quick Installation

### Windows
1. **Extract the ZIP file** to your desired location
2. **Double-click `start.bat`** to start the application
3. **Open your browser** and go to http://localhost:5000

### Linux/Mac
1. **Extract the ZIP file** to your desired location
2. **Run `./start.sh`** in terminal to start the application
3. **Open your browser** and go to http://localhost:5000

## 🔧 Advanced Setup

### **Custom Configuration**
- Edit files in `config/` directory to customize settings
- Modify `config/app_config.json` for application settings
- Update `config/roles.json` for role definitions
- Customize `config/checklist_columns.json` for checklist structure

### **Network Deployment**
- Configure `config/network_security.json` for network settings
- Set up proxy settings if needed
- Configure firewall rules for port 5000
- Set up SSL certificates for HTTPS

### **Enterprise Integration**
- Configure GitLab integration in `config/gitlab_config.py`
- Set up authentication and authorization
- Configure database connections if needed
- Set up monitoring and logging

## 📋 System Requirements

### **Minimum Requirements**
- **OS**: Windows 7+, macOS 10.14+, Ubuntu 18.04+
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 500MB free space
- **Network**: Internet connection for initial setup

### **Recommended Requirements**
- **OS**: Windows 10+, macOS 11+, Ubuntu 20.04+
- **RAM**: 8GB or more
- **Storage**: 1GB free space
- **Network**: Stable internet connection
- **Browser**: Chrome, Firefox, Safari, or Edge (latest versions)

## 🛠️ Troubleshooting

### **Common Issues**

#### **Application Won't Start**
- Check if port 5000 is available
- Ensure firewall allows the application
- Check system requirements
- Try running as administrator (Windows)

#### **Browser Issues**
- Clear browser cache and cookies
- Try a different browser
- Check if JavaScript is enabled
- Ensure popup blockers are disabled

#### **Performance Issues**
- Close other applications to free up memory
- Check available disk space
- Restart the application
- Check system resource usage

### **Getting Help**
- Check the main README.md for detailed documentation
- Review the LICENSE file for usage terms
- The application includes built-in help and documentation
- Visit our GitHub repository for community support

## 🔒 Security Considerations

### **Network Security**
- Configure firewall rules appropriately
- Use HTTPS in production environments
- Set up proper authentication and authorization
- Monitor network traffic and access logs

### **Data Protection**
- Regular backups of configuration and data
- Secure storage of sensitive information
- Access control and user permissions
- Audit trails and logging

## 📞 Support

For technical support and questions:
- **GitHub Issues**: Report bugs and request features
- **Documentation**: Comprehensive guides and tutorials
- **Community**: User forums and discussions
- **Professional Support**: Enterprise support available

---

**CodeCritique** - Professional Code Review Tool  
Version {self.version}  
Licensed under Apache 2.0 License
'''
        
        with open(install_guide, 'w', encoding='utf-8') as f:
            f.write(install_content)
        
        logger.info(f"Created installation guide: {install_guide}")
    
    def create_distribution_zip(self, package_dir):
        """Create ZIP file for distribution"""
        logger.info("Creating distribution ZIP file...")
        
        zip_path = self.releases_dir / f"{package_dir.name}.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(package_dir):
                for file in files:
                    file_path = Path(root) / file
                    arc_path = file_path.relative_to(package_dir)
                    zipf.write(file_path, arc_path)
        
        logger.info(f"Created distribution ZIP: {zip_path}")
        return zip_path
    
    def build_complete(self):
        """Main build process"""
        logger.info("Starting complete build process...")
        
        try:
            # Step 1: Clean previous builds
            self.clean_build_dirs()
            
            # Step 2: Build executable
            if not self.build_executable():
                logger.error("❌ Failed to build executable")
                return False
            
            # Step 3: Create complete package
            package_dir = self.create_complete_package()
            if not package_dir:
                logger.error("❌ Failed to create complete package")
                return False
            
            # Step 4: Create distribution ZIP
            zip_path = self.create_distribution_zip(package_dir)
            
            logger.info("Complete build finished successfully!")
            logger.info(f"Package directory: {package_dir}")
            logger.info(f"Distribution ZIP: {zip_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Build failed: {e}")
            return False

def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(description='Build complete CodeCritique distribution')
    parser.add_argument('--clean', action='store_true', 
                        help='Clean build directories only')
    
    args = parser.parse_args()
    
    builder = CompleteBuilder()
    
    if args.clean:
        builder.clean_build_dirs()
        print("✅ Build directories cleaned!")
        return
    
    success = builder.build_complete()
    
    if success:
        print("\n🎉 Complete build finished successfully!")
        print(f"📦 Package directory: {builder.releases_dir}")
        print("\n🚀 You can now distribute the complete package!")
    else:
        print("\n❌ Build failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
