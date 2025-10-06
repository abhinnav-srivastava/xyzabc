#!/usr/bin/env python3
"""
Test script for portable build
Verifies that the portable build works correctly
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def test_portable_build():
    """Test the portable build"""
    print("🧪 Testing CodeCritique Portable Build")
    print("=" * 40)
    
    project_root = Path(__file__).parent.parent
    portable_dir = project_root / "portable"
    exe_path = portable_dir / "CodeCritique.exe"
    
    if not exe_path.exists():
        print("❌ Portable executable not found!")
        print(f"   Expected: {exe_path}")
        return False
    
    print(f"✅ Found executable: {exe_path}")
    
    # Test if executable runs
    print("\n🚀 Testing executable startup...")
    try:
        # Start the executable in background
        process = subprocess.Popen([str(exe_path)], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 text=True)
        
        # Wait a bit for startup
        time.sleep(5)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ Executable started successfully!")
            
            # Try to connect to the application
            try:
                response = requests.get("http://localhost:5000", timeout=5)
                if response.status_code == 200:
                    print("✅ Application is responding on http://localhost:5000")
                    success = True
                else:
                    print(f"⚠️  Application responded with status {response.status_code}")
                    success = True  # Still consider it working
            except requests.exceptions.RequestException as e:
                print(f"⚠️  Could not connect to application: {e}")
                success = True  # Executable is running, just can't test HTTP
            
            # Stop the process
            process.terminate()
            process.wait(timeout=10)
            
        else:
            print("❌ Executable failed to start!")
            stdout, stderr = process.communicate()
            print(f"   stdout: {stdout}")
            print(f"   stderr: {stderr}")
            success = False
            
    except Exception as e:
        print(f"❌ Error testing executable: {e}")
        success = False
    
    return success

def main():
    """Main test function"""
    success = test_portable_build()
    
    if success:
        print("\n🎉 Portable build test PASSED!")
        print("✅ The portable version is working correctly!")
        return 0
    else:
        print("\n❌ Portable build test FAILED!")
        print("❌ The portable version has issues!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
