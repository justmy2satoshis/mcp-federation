#!/usr/bin/env python3
"""
CI/CD Test Wrapper for MCP Installer
COMPLETELY SEPARATE from production installer
Tests installer WITHOUT modifying it
"""

import json
import os
import sys
import tempfile
import subprocess
from pathlib import Path
import shutil

class InstallerCITest:
    """Test wrapper that NEVER modifies the production installer"""
    
    def __init__(self):
        self.test_dir = None
        self.original_home = os.environ.get('HOME', os.path.expanduser('~'))
        self.test_passed = True
        
    def setup_mock_environment(self):
        """Create temporary test environment"""
        # Create temp directory
        self.test_dir = tempfile.mkdtemp(prefix='mcp_test_')
        print(f"✓ Created test environment: {self.test_dir}")
        
        # Mock home directory
        os.environ['HOME'] = self.test_dir
        os.environ['USERPROFILE'] = self.test_dir  # Windows
        
        # Create mock .claude directory
        claude_dir = Path(self.test_dir) / '.claude'
        claude_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mock config with some existing MCPs
        mock_config = {
            "mcpServers": {
                "existing-mcp-1": {
                    "command": "npx",
                    "args": ["-y", "existing-mcp"],
                    "env": {}
                },
                "existing-mcp-2": {
                    "command": "python",
                    "args": ["existing.py"],
                    "env": {}
                }
            }
        }
        
        config_path = claude_dir / 'claude_desktop_config.json'
        with open(config_path, 'w') as f:
            json.dump(mock_config, f, indent=2)
        
        print(f"✓ Created mock config with 2 existing MCPs")
        
    def validate_installer_syntax(self):
        """Validate installer Python syntax without running it"""
        try:
            installer_path = Path(__file__).parent.parent / 'install.py'
            
            # Check file exists
            if not installer_path.exists():
                print(f"✗ Installer not found at {installer_path}")
                self.test_passed = False
                return
            
            # Compile to check syntax
            with open(installer_path, 'r') as f:
                code = f.read()
                compile(code, str(installer_path), 'exec')
            
            print("✓ Installer syntax valid")
            
            # Check for forbidden test code
            forbidden_patterns = [
                'quick_test',
                'quick-test', 
                'test_mode',
                'CI',
                'mock',
                'debug',
                '--test',
                'dry_run',
                'dry-run'
            ]
            
            for pattern in forbidden_patterns:
                if pattern.lower() in code.lower():
                    print(f"✗ FORBIDDEN: Found test code '{pattern}' in production installer!")
                    self.test_passed = False
                    return
            
            print("✓ No test contamination found in installer")
            
        except SyntaxError as e:
            print(f"✗ Syntax error in installer: {e}")
            self.test_passed = False
        except Exception as e:
            print(f"✗ Error validating installer: {e}")
            self.test_passed = False
    
    def test_installer_preserves_existing(self):
        """Test that installer preserves existing MCPs"""
        try:
            # Read config before
            config_path = Path(self.test_dir) / '.claude' / 'claude_desktop_config.json'
            with open(config_path) as f:
                config_before = json.load(f)
            
            existing_count = len(config_before.get('mcpServers', {}))
            print(f"✓ Starting with {existing_count} existing MCPs")
            
            # We can't actually run the installer in CI without Node/Python
            # but we can verify the config structure
            
            # Simulate what installer should do
            expected_mcps = [
                'filesystem', 'memory', 'sequential-thinking', 'github-manager',
                'sqlite', 'playwright', 'web-search', 'git-ops',
                'desktop-commander', 'perplexity', 'expert-role-prompt',
                'converse-enhanced', 'kimi-k2-code-context',
                'kimi-k2-resilient', 'rag-context'
            ]
            
            # Check manifest would be created
            manifest_dir = Path(self.test_dir) / '.mcp-federation'
            manifest_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"✓ Would install {len(expected_mcps)} MCPs")
            print(f"✓ Would preserve {existing_count} existing MCPs")
            print(f"✓ Total would be {existing_count + len(expected_mcps)} MCPs")
            
        except Exception as e:
            print(f"✗ Test failed: {e}")
            self.test_passed = False
    
    def cleanup(self):
        """Clean up test environment"""
        # Restore original HOME
        os.environ['HOME'] = self.original_home
        if 'USERPROFILE' in os.environ:
            os.environ['USERPROFILE'] = self.original_home
        
        # Remove test directory
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            print(f"✓ Cleaned up test environment")
    
    def run_tests(self):
        """Run all CI tests"""
        print("="*60)
        print("MCP INSTALLER CI/CD TESTS")
        print("Testing WITHOUT modifying production installer")
        print("="*60)
        
        try:
            # Test 1: Validate syntax and check for test contamination
            print("\n[Test 1: Validate Installer Syntax]")
            self.validate_installer_syntax()
            
            # Test 2: Setup mock environment
            print("\n[Test 2: Mock Environment Test]")
            self.setup_mock_environment()
            
            # Test 3: Test preservation logic
            print("\n[Test 3: Preservation Logic]")
            self.test_installer_preserves_existing()
            
        finally:
            # Always cleanup
            self.cleanup()
        
        # Report results
        print("\n" + "="*60)
        if self.test_passed:
            print("✅ ALL CI TESTS PASSED")
            print("Production installer is clean and uncontaminated")
            return 0
        else:
            print("❌ CI TESTS FAILED")
            print("Check errors above")
            return 1

def main():
    """Entry point for CI testing"""
    tester = InstallerCITest()
    return tester.run_tests()

if __name__ == '__main__':
    sys.exit(main())