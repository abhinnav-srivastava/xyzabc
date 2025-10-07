#!/usr/bin/env python3
"""
Setup Desktop App Dependencies
Installs Node.js dependencies and creates desktop app assets
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_node_js():
    """Check if Node.js is installed"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True, check=True)
        logger.info(f"Node.js version: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("Node.js is not installed!")
        logger.info("Please install Node.js from https://nodejs.org/")
        return False

def check_npm():
    """Check if npm is available"""
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True, check=True)
        logger.info(f"npm version: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("npm is not available!")
        return False

def install_desktop_dependencies():
    """Install desktop app dependencies"""
    project_root = Path(__file__).parent.parent.parent
    desktop_dir = project_root / "desktop"
    
    if not desktop_dir.exists():
        logger.error("Desktop directory not found!")
        return False
    
    logger.info("Installing desktop app dependencies...")
    
    try:
        # Change to desktop directory
        os.chdir(desktop_dir)
        
        # Install dependencies
        logger.info("Running npm install...")
        subprocess.run(['npm', 'install'], check=True)
        
        logger.info("✅ Desktop dependencies installed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False
    except Exception as e:
        logger.error(f"Error installing dependencies: {e}")
        return False
    finally:
        # Return to project root
        os.chdir(project_root)

def create_desktop_assets():
    """Create desktop app assets"""
    project_root = Path(__file__).parent.parent.parent
    
    try:
        # Run the asset creation script
        asset_script = project_root / "scripts" / "py" / "create_desktop_assets.py"
        
        if asset_script.exists():
            logger.info("Creating desktop assets...")
            subprocess.run([sys.executable, str(asset_script)], check=True)
            logger.info("✅ Desktop assets created successfully!")
            return True
        else:
            logger.warning("Asset creation script not found, skipping...")
            return True
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create assets: {e}")
        return False
    except Exception as e:
        logger.error(f"Error creating assets: {e}")
        return False

def setup_desktop():
    """Main setup function"""
    logger.info("Setting up desktop app...")
    
    # Check prerequisites
    if not check_node_js():
        return False
    
    if not check_npm():
        return False
    
    # Install dependencies
    if not install_desktop_dependencies():
        return False
    
    # Create assets
    if not create_desktop_assets():
        return False
    
    logger.info("🎉 Desktop app setup completed successfully!")
    logger.info("You can now build the desktop app using:")
    logger.info("  python scripts/py/build_all.py --desktop-only")
    logger.info("  or")
    logger.info("  cd desktop && npm run build")
    
    return True

def main():
    """Main function"""
    success = setup_desktop()
    
    if success:
        print("\n🎉 Desktop app setup completed successfully!")
        print("🚀 You can now build the desktop app!")
    else:
        print("\n❌ Desktop app setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()

