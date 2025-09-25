#!/usr/bin/env python3
"""
Simple Windows Test Script
Minimal test to diagnose Windows CI issues
"""

import sys
import os
import platform
import subprocess
import json
from pathlib import Path

def main():
    """Run simple Windows diagnostics"""
    print("="*60)
    print("SIMPLE WINDOWS DIAGNOSTIC TEST")
    print("="*60)
    
    # 1. Platform check
    print(f"\n1. Platform: {platform.system()}")
    print(f"   Python: {sys.version}")
    print(f"   Executable: {sys.executable}")
    
    # 2. Environment variables
    print(f"\n2. Environment Variables:")
    print(f"   HOME: {os.environ.get('HOME', 'Not set')}")
    print(f"   USERPROFILE: {os.environ.get('USERPROFILE', 'Not set')}")
    print(f"   APPDATA: {os.environ.get('APPDATA', 'Not set')}")
    print(f"   TEMP: {os.environ.get('TEMP', 'Not set')}")
    
    # 3. Path operations
    print(f"\n3. Path Operations:")
    try:
        home = Path.home()
        print(f"   Path.home(): {home}")
        print(f"   Exists: {home.exists()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 4. Subprocess test
    print(f"\n4. Subprocess Test:")
    try:
        result = subprocess.run(
            [sys.executable, "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        print(f"   Return code: {result.returncode}")
        print(f"   Output: {result.stdout.strip()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 5. JSON test
    print(f"\n5. JSON Test:")
    try:
        test_data = {"test": "value", "number": 123}
        json_str = json.dumps(test_data)
        parsed = json.loads(json_str)
        print(f"   Encode/Decode: OK")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 6. File operations
    print(f"\n6. File Operations:")
    try:
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump({"test": "data"}, f)
            temp_path = f.name
        
        with open(temp_path, 'r') as f:
            data = json.load(f)
        
        os.unlink(temp_path)
        print(f"   Read/Write: OK")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "="*60)
    print("DIAGNOSTIC TEST COMPLETE")
    print("="*60)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())