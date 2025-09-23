#!/usr/bin/env python3
"""
Advanced proxy setup script for CodeCritique
Automatically detects and configures proxy settings for pip installation
"""

import os
import sys
import subprocess
import urllib.request
import urllib.error
import json
import platform
from typing import List, Dict, Optional

def get_system_proxy() -> Optional[str]:
    """Get system proxy settings from environment variables and registry (Windows)"""
    proxy = None
    
    # Check environment variables
    for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
        if var in os.environ:
            proxy = os.environ[var]
            break
    
    # Windows: Check registry for proxy settings
    if platform.system() == "Windows" and not proxy:
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                              r"Software\Microsoft\Windows\CurrentVersion\Internet Settings") as key:
                proxy_enabled = winreg.QueryValueEx(key, "ProxyEnable")[0]
                if proxy_enabled:
                    proxy_server = winreg.QueryValueEx(key, "ProxyServer")[0]
                    if proxy_server:
                        proxy = f"http://{proxy_server}"
        except:
            pass
    
    return proxy

def test_connection(url: str = "https://pypi.org", timeout: int = 10) -> bool:
    """Test if we can connect to a URL"""
    try:
        urllib.request.urlopen(url, timeout=timeout)
        return True
    except:
        return False

def test_proxy(proxy: str, url: str = "https://pypi.org", timeout: int = 10) -> bool:
    """Test if a proxy works"""
    try:
        proxy_handler = urllib.request.ProxyHandler({'http': proxy, 'https': proxy})
        opener = urllib.request.build_opener(proxy_handler)
        urllib.request.install_opener(opener)
        urllib.request.urlopen(url, timeout=timeout)
        return True
    except:
        return False

def get_common_proxies() -> List[str]:
    """Get list of common proxy configurations to try"""
    return [
        None,  # No proxy
        "http://proxy:8080",
        "http://127.0.0.1:8080",
        "http://localhost:8080",
        "http://proxy.company.com:8080",
        "http://proxy.corp:8080",
        "http://10.0.0.1:8080",
        "http://192.168.1.1:8080",
    ]

def install_with_pip(proxy: Optional[str] = None, trusted_hosts: bool = True) -> bool:
    """Install requirements.txt using pip with optional proxy"""
    cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
    
    if proxy:
        cmd.extend(["--proxy", proxy])
    
    if trusted_hosts:
        cmd.extend([
            "--trusted-host", "pypi.org",
            "--trusted-host", "pypi.python.org", 
            "--trusted-host", "files.pythonhosted.org"
        ])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("❌ Installation timed out")
        return False
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return False

def get_user_proxy() -> Optional[str]:
    """Get proxy settings from user input"""
    print("\n🔧 Manual Proxy Configuration")
    print("-" * 30)
    print("If automatic proxy detection failed, you can enter your proxy settings manually.")
    print("Leave blank to skip proxy configuration.")
    print()
    
    # Get proxy URL
    proxy_url = input("Enter proxy URL (e.g., http://proxy.company.com:8080): ").strip()
    if not proxy_url:
        return None
    
    # Validate proxy format
    if not proxy_url.startswith(('http://', 'https://')):
        proxy_url = 'http://' + proxy_url
    
    # Test the proxy
    print(f"\nTesting proxy: {proxy_url}")
    if test_proxy(proxy_url):
        print("✅ Proxy test successful!")
        return proxy_url
    else:
        print("❌ Proxy test failed!")
        
        # Ask for username/password if needed
        use_auth = input("Does your proxy require authentication? (y/n): ").strip().lower()
        if use_auth in ['y', 'yes']:
            username = input("Enter proxy username: ").strip()
            password = input("Enter proxy password: ").strip()
            if username and password:
                # Format proxy with authentication
                auth_proxy = f"http://{username}:{password}@{proxy_url.replace('http://', '')}"
                print(f"Testing authenticated proxy...")
                if test_proxy(auth_proxy):
                    print("✅ Authenticated proxy test successful!")
                    return auth_proxy
                else:
                    print("❌ Authenticated proxy test failed!")
        
        return None

def main():
    """Main function to handle proxy detection and pip installation"""
    print("🔍 CodeCritique Proxy Setup")
    print("=" * 50)
    
    # Test direct connection first
    print("Testing direct connection to PyPI...")
    if test_connection():
        print("✅ Direct connection works!")
        if install_with_pip():
            print("✅ Dependencies installed successfully!")
            return True
        else:
            print("❌ Direct installation failed, trying proxy configurations...")
    else:
        print("❌ Direct connection failed, trying proxy configurations...")
    
    # Get system proxy
    system_proxy = get_system_proxy()
    if system_proxy:
        print(f"🔍 Found system proxy: {system_proxy}")
        if test_proxy(system_proxy):
            print(f"✅ System proxy works: {system_proxy}")
            if install_with_pip(system_proxy):
                print("✅ Dependencies installed with system proxy!")
                return True
        else:
            print(f"❌ System proxy doesn't work: {system_proxy}")
    
    # Try common proxy configurations
    print("\n🔍 Trying common proxy configurations...")
    proxies = get_common_proxies()
    
    for i, proxy in enumerate(proxies, 1):
        if proxy is None:
            print(f"{i}. Trying without proxy...")
        else:
            print(f"{i}. Trying proxy: {proxy}")
            if not test_proxy(proxy):
                print(f"   ❌ Proxy test failed: {proxy}")
                continue
        
        if install_with_pip(proxy):
            print(f"✅ Dependencies installed successfully!")
            if proxy:
                print(f"   Using proxy: {proxy}")
            return True
        else:
            print(f"   ❌ Installation failed")
    
    # Ask user for manual proxy input
    print("\n❌ All automatic proxy configurations failed!")
    user_proxy = get_user_proxy()
    
    if user_proxy:
        print(f"\n🔧 Trying user-provided proxy: {user_proxy}")
        if install_with_pip(user_proxy):
            print("✅ Dependencies installed with user proxy!")
            return True
        else:
            print("❌ User proxy installation failed!")
    
    print("\n❌ All proxy configurations failed!")
    print("\nTroubleshooting tips:")
    print("1. Check your internet connection")
    print("2. Verify proxy settings with your IT department")
    print("3. Try running as administrator")
    print("4. Check firewall settings")
    print("5. Try manual installation: pip install -r requirements.txt")
    print("6. Contact your IT support for correct proxy settings")
    
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
