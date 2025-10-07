#!/usr/bin/env python3
"""
CodeCritique - Master Build Script
Handles all build processes: portable, desktop, and distribution
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command(command, cwd=None, check=True):
    """Run a command and return the result"""
    logger.info(f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, check=check, 
                              capture_output=True, text=True)
        if result.stdout:
            logger.info(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        if e.stderr:
            logger.error(f"Error: {e.stderr}")
        raise

def check_prerequisites():
    """Check if all prerequisites are installed"""
    logger.info("Checking prerequisites...")
    
    # Check Python
    try:
        result = subprocess.run([sys.executable, '--version'], capture_output=True, text=True, check=True)
        logger.info(f"Python: {result.stdout.strip()}")
    except:
        logger.error("Python is not available!")
        return False
    
    # Check if we're in the right directory
    if not Path("app.py").exists():
        logger.error("app.py not found! Please run from project root.")
        return False
    
    logger.info("✅ Prerequisites check passed!")
    return True

def setup_desktop():
    """Setup desktop app dependencies"""
    logger.info("Setting up desktop app...")
    
    try:
        # Run desktop setup script
        setup_script = Path("scripts/py/setup_desktop.py")
        if setup_script.exists():
            run_command(f"{sys.executable} {setup_script}")
            logger.info("✅ Desktop setup completed!")
            return True
        else:
            logger.warning("Desktop setup script not found, skipping...")
            return True
    except Exception as e:
        logger.error(f"Desktop setup failed: {e}")
        return False

def build_portable():
    """Build portable executable"""
    logger.info("Building portable executable...")
    
    try:
        # Run portable build script
        build_script = Path("scripts/py/build_portable.py")
        if build_script.exists():
            run_command(f"{sys.executable} {build_script}")
            logger.info("✅ Portable build completed!")
            return True
        else:
            logger.error("Portable build script not found!")
            return False
    except Exception as e:
        logger.error(f"Portable build failed: {e}")
        return False

def build_desktop():
    """Build desktop app"""
    logger.info("Building desktop app...")
    
    try:
        desktop_dir = Path("desktop")
        if not desktop_dir.exists():
            logger.error("Desktop directory not found!")
            return False
        
        # Build desktop app
        run_command("npm run build", cwd=desktop_dir)
        logger.info("✅ Desktop build completed!")
        return True
    except Exception as e:
        logger.error(f"Desktop build failed: {e}")
        return False

def create_distribution():
    """Create distribution packages"""
    logger.info("Creating distribution packages...")
    
    try:
        # Run complete build script
        complete_script = Path("scripts/py/build_complete.py")
        if complete_script.exists():
            run_command(f"{sys.executable} {complete_script}")
            logger.info("✅ Complete distribution packages created!")
            return True
        else:
            # Fallback to original distribution script
            dist_script = Path("scripts/py/build_all.py")
            if dist_script.exists():
                run_command(f"{sys.executable} {dist_script}")
                logger.info("✅ Distribution packages created!")
                return True
            else:
                logger.error("Distribution script not found!")
                return False
    except Exception as e:
        logger.error(f"Distribution creation failed: {e}")
        return False

def clean_build():
    """Clean build directories"""
    logger.info("Cleaning build directories...")
    
    dirs_to_clean = ["build", "dist", "portable", "releases", "desktop/dist", "desktop/node_modules"]
    
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            import shutil
            shutil.rmtree(dir_path)
            logger.info(f"Cleaned {dir_name}")
    
    logger.info("✅ Build directories cleaned!")

def main():
    """Main build function"""
    parser = argparse.ArgumentParser(description='CodeCritique Master Build Script')
    parser.add_argument('--portable-only', action='store_true', help='Build only portable version')
    parser.add_argument('--desktop-only', action='store_true', help='Build only desktop version')
    parser.add_argument('--setup-desktop', action='store_true', help='Setup desktop dependencies only')
    parser.add_argument('--clean', action='store_true', help='Clean build directories only')
    parser.add_argument('--all', action='store_true', help='Build everything (default)')
    
    args = parser.parse_args()
    
    # Default to build all if no specific option is given
    if not any([args.portable_only, args.desktop_only, args.setup_desktop, args.clean]):
        args.all = True
    
    logger.info("🚀 CodeCritique Master Build Script")
    logger.info("=" * 50)
    
    # Check prerequisites
    if not check_prerequisites():
        logger.error("❌ Prerequisites check failed!")
        sys.exit(1)
    
    # Clean if requested
    if args.clean:
        clean_build()
        logger.info("✅ Clean completed!")
        return
    
    success = True
    
    # Setup desktop if requested
    if args.setup_desktop or args.desktop_only or args.all:
        if not setup_desktop():
            logger.error("❌ Desktop setup failed!")
            success = False
    
    # Build portable if requested
    if args.portable_only or args.all:
        if not build_portable():
            logger.error("❌ Portable build failed!")
            success = False
    
    # Build desktop if requested
    if args.desktop_only or args.all:
        if not build_desktop():
            logger.error("❌ Desktop build failed!")
            success = False
    
    # Create distribution if building everything
    if args.all and success:
        if not create_distribution():
            logger.error("❌ Distribution creation failed!")
            success = False
    
    # Show results
    if success:
        logger.info("🎉 Build completed successfully!")
        
        # Show release packages
        releases_dir = Path("releases")
        if releases_dir.exists():
            logger.info("📦 Release packages:")
            for item in releases_dir.iterdir():
                if item.is_file():
                    logger.info(f"  - {item.name}")
        
        logger.info("🚀 You can now distribute the packages!")
    else:
        logger.error("❌ Build failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()

