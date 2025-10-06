#!/usr/bin/env python3
"""
Generate PWA icons from SVG
This script creates various sized PNG icons for PWA support
"""

import os
import sys
from pathlib import Path

def create_icon_placeholder(size, filename):
    """Create a placeholder icon file"""
    icon_dir = Path("static/icons")
    icon_dir.mkdir(exist_ok=True)
    
    # Create a simple placeholder file
    placeholder_content = f"""<!-- Placeholder icon {size}x{size} -->
<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#0d6efd;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#6f42c1;stop-opacity:1" />
    </linearGradient>
  </defs>
  
  <!-- Background -->
  <rect width="{size}" height="{size}" fill="url(#bg)" rx="{size//8}"/>
  
  <!-- Code brackets -->
  <g fill="white" stroke="white" stroke-width="{max(1, size//64)}" stroke-linecap="round" stroke-linejoin="round">
    <!-- Left bracket -->
    <path d="M {size//4} {size//3} L {size//4} {size//2} L {size//3} {size//2} L {size//3} {size*2//3} L {size//4} {size*2//3} L {size//4} {size*3//4} L {size//2} {size*3//4} L {size//2} {size//3} Z"/>
    
    <!-- Right bracket -->
    <path d="M {size*3//4} {size//3} L {size*3//4} {size//2} L {size*2//3} {size//2} L {size*2//3} {size*2//3} L {size*3//4} {size*2//3} L {size*3//4} {size*3//4} L {size//2} {size*3//4} L {size//2} {size//3} Z"/>
  </g>
  
  <!-- Checkmark in center -->
  <g fill="white" stroke="white" stroke-width="{max(1, size//42)}" stroke-linecap="round" stroke-linejoin="round">
    <path d="M {size//2.5} {size//2.2} L {size//2.1} {size//1.9} L {size*3//5} {size//2.5}"/>
  </g>
  
  <!-- Text -->
  <text x="{size//2}" y="{size*3//4}" font-family="Arial, sans-serif" font-size="{size//10}" font-weight="bold" text-anchor="middle" fill="white">CC</text>
</svg>"""
    
    with open(icon_dir / filename, 'w') as f:
        f.write(placeholder_content)
    
    print(f"Created placeholder icon: {filename}")

def main():
    """Generate all required PWA icons"""
    print("Generating PWA icons...")
    
    # Icon sizes and filenames
    icons = [
        (16, "icon-16x16.png"),
        (32, "icon-32x32.png"),
        (72, "icon-72x72.png"),
        (96, "icon-96x96.png"),
        (128, "icon-128x128.png"),
        (144, "icon-144x144.png"),
        (152, "icon-152x152.png"),
        (192, "icon-192x192.png"),
        (384, "icon-384x384.png"),
        (512, "icon-512x512.png")
    ]
    
    for size, filename in icons:
        create_icon_placeholder(size, filename)
    
    print(f"Generated {len(icons)} PWA icons")
    print("Note: These are placeholder SVG files. In production, convert them to PNG format.")

if __name__ == "__main__":
    main()
