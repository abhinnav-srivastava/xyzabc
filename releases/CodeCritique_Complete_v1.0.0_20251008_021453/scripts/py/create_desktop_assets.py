#!/usr/bin/env python3
"""
Create Desktop App Assets
Converts existing icons and creates desktop app assets
"""

import os
import shutil
from pathlib import Path
from PIL import Image
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_desktop_assets():
    """Create desktop app assets from existing icons"""
    
    project_root = Path(__file__).parent.parent.parent
    static_icons = project_root / "static" / "icons"
    desktop_assets = project_root / "desktop" / "assets"
    
    # Create assets directory
    desktop_assets.mkdir(exist_ok=True)
    
    # Find the best source icon
    source_icon = None
    icon_sizes = [512, 256, 128, 64, 32, 16]
    
    for size in icon_sizes:
        icon_path = static_icons / f"icon-{size}x{size}.png"
        if icon_path.exists():
            source_icon = icon_path
            break
    
    if not source_icon:
        logger.error("No source icon found!")
        return False
    
    logger.info(f"Using source icon: {source_icon}")
    
    try:
        # Open the source image
        img = Image.open(source_icon)
        
        # Create Windows ICO file
        ico_path = desktop_assets / "icon.ico"
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        img.save(ico_path, format='ICO', sizes=sizes)
        logger.info(f"Created Windows icon: {ico_path}")
        
        # Create macOS ICNS file (simplified - just copy PNG)
        icns_path = desktop_assets / "icon.icns"
        # For now, just copy the 512x512 PNG as ICNS
        shutil.copy2(source_icon, icns_path)
        logger.info(f"Created macOS icon: {icns_path}")
        
        # Create Linux PNG icon
        png_path = desktop_assets / "icon.png"
        # Resize to 512x512 if needed
        if img.size != (512, 512):
            img_resized = img.resize((512, 512), Image.Resampling.LANCZOS)
            img_resized.save(png_path, format='PNG')
        else:
            shutil.copy2(source_icon, png_path)
        logger.info(f"Created Linux icon: {png_path}")
        
        # Create favicon
        favicon_path = desktop_assets / "favicon.ico"
        favicon_img = img.resize((32, 32), Image.Resampling.LANCZOS)
        favicon_img.save(favicon_path, format='ICO')
        logger.info(f"Created favicon: {favicon_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating desktop assets: {e}")
        return False

def create_desktop_readme():
    """Create README for desktop app"""
    
    project_root = Path(__file__).parent.parent.parent
    readme_path = project_root / "desktop" / "README.md"
    
    readme_content = '''# CodeCritique Desktop App

## 🖥️ Desktop Application

This directory contains the Electron-based desktop application for CodeCritique.

## 📋 Prerequisites

- Node.js 16+ (https://nodejs.org/)
- npm (comes with Node.js)
- Python 3.8+ (for building the Flask backend)

## 🚀 Development

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start development server:**
   ```bash
   npm start
   ```

## 🔧 Building

### Build for current platform:
```bash
npm run build
```

### Build for specific platforms:
```bash
npm run build-win    # Windows
npm run build-mac    # macOS
npm run build-linux  # Linux
```

## 📦 Distribution

The build process creates installers and portable packages:

- **Windows**: NSIS installer + Portable ZIP
- **macOS**: DMG installer
- **Linux**: AppImage + DEB package

## 🎯 Features

- **Native Desktop Experience** - Menu bar, keyboard shortcuts
- **System Integration** - Proper window management
- **Auto-Updates** - Built-in update mechanism
- **Professional UI** - Enhanced desktop experience
- **Offline Support** - Works without internet connection

## 📁 Structure

- `main.js` - Main Electron process
- `preload.js` - Secure preload script
- `renderer.js` - Desktop-specific enhancements
- `styles.css` - Desktop-specific styles
- `package.json` - Node.js dependencies and build config
- `assets/` - Icons and other assets

## 🔧 Configuration

The desktop app automatically:
- Starts the Flask backend server
- Opens the web interface in a native window
- Handles external links properly
- Provides native menu and shortcuts

## 📞 Support

For desktop app specific issues:
- Check the main project README
- Review Electron documentation
- Check the console for error messages
'''
    
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    logger.info(f"Created desktop README: {readme_path}")

def main():
    """Main function"""
    logger.info("Creating desktop app assets...")
    
    # Create assets
    if create_desktop_assets():
        logger.info("✅ Desktop assets created successfully!")
    else:
        logger.error("❌ Failed to create desktop assets!")
        return False
    
    # Create README
    create_desktop_readme()
    logger.info("✅ Desktop README created!")
    
    logger.info("🎉 Desktop app setup completed!")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)

