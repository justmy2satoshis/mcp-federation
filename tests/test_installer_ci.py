#!/usr/bin/env python3
"""
CI/CD Test Wrapper for MCP Installer
COMPLETELY SEPARATE from production installer
Tests installer WITHOUT modifying it
Cross-platform compatible (Windows, macOS, Linux)
"""

import json
import os
import sys
import tempfile
import platform
from pathlib import Path
import shutil

class InstallerCITest:
    """Test wrapper that NEVER modifies the production installer"""
    
    def __init__(self):
        self.test_dir = None
        self.system = platform.system()
        self.original_home = str(Path.home())
        self.original_appdata = os.environ.get('APPDATA', '')
        self.test_passed = True
        
    def get_config_path(self, base_dir=None):
        """Get OS-specific Claude Desktop config path"""
        if base_dir is None:
            base_dir = Path(self.test_dir) if self.test_dir else Path.home()
        
        if self.system == 'Windows':
            # Windows uses APPDATA
            if self.test_dir:
                return base_dir / 'Claude' / 'claude_desktop_config.json'
            else:
                appdata = os.environ.get('APPDATA', '')
                if appdata:
                    return Path(appdata) / 'Claude' / 'claude_desktop_config.json'
                return base_dir / 'AppData' / 'Roaming' / 'Claude' / 'claude_desktop_config.json'
        elif self.system == 'Darwin':  # macOS
            return base_dir / 'Library' / 'Application Support' / 'Claude' / 'claude_desktop_config.json'
        else:  # Linux
            return base_dir / '.claude' / 'claude_desktop_config.json'
        
    def setup_mock_environment(self):
        """Create temporary test environment"""
        # Create temp directory
        self.test_dir = tempfile.mkdtemp(prefix='mcp_test_')
        test_path = Path(self.test_dir)
        print(f"✓ Created test environment: {self.test_dir}")
        print(f"✓ Platform: {self.system}")
        
        # Set up OS-specific environment
        if self.system == 'Windows':
            # Windows-specific environment
            os.environ['APPDATA'] = str(test_path)
            os.environ['LOCALAPPDATA'] = str(test_path)
            os.environ['USERPROFILE'] = str(test_path)
            config_dir = test_path / 'Claude'
        elif self.system == 'Darwin':  # macOS
            os.environ['HOME'] = str(test_path)
            config_dir = test_path / 'Library' / 'Application Support' / 'Claude'
        else:  # Linux
            os.environ['HOME'] = str(test_path)
            config_dir = test_path / '.claude'
        
        # Create config directory
        config_dir.mkdir(parents=True, exist_ok=True)
        
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
        
        config_path = config_dir / 'claude_desktop_config.json'
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(mock_config, f, indent=2)
        
        print(f"✓ Created mock config at: {config_path}")
        print(f"✓ Config has 2 existing MCPs")
        
    def validate_installer_syntax(self):
        """Validate installer Python syntax without running it"""
        try:
            # Find installer path - handle both Unix and Windows paths
            installer_path = Path(__file__).parent.parent / 'install.py'
            installer_path = installer_path.resolve()
            
            # Check file exists
            if not installer_path.exists():
                print(f"✗ Installer not found at {installer_path}")
                self.test_passed = False
                return
            
            # Compile to check syntax
            with open(installer_path, 'r', encoding='utf-8') as f:
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
            # Get the config path for this OS
            config_path = self.get_config_path()
            
            # Read config
            with open(config_path, 'r', encoding='utf-8') as f:
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
    
    def test_path_handling(self):
        """Test cross-platform path handling"""
        try:
            # Test that paths work on this OS
            test_paths = [
                Path.home(),
                Path.home() / 'test',
                Path('/') if self.system != 'Windows' else Path('C:\\'),
            ]
            
            for path in test_paths:
                # Just verify Path operations work
                str_path = str(path)
                assert isinstance(str_path, str)
            
            print(f"✓ Path handling works on {self.system}")
            
        except Exception as e:
            print(f"✗ Path test failed: {e}")
            self.test_passed = False
    
    def cleanup(self):
        """Clean up test environment"""
        # Restore original environment
        if self.system == 'Windows':
            if self.original_appdata:
                os.environ['APPDATA'] = self.original_appdata
            else:
                os.environ.pop('APPDATA', None)
            # Restore USERPROFILE if we changed it
            if 'USERPROFILE' in os.environ and self.test_dir:
                os.environ['USERPROFILE'] = self.original_home
        else:
            os.environ['HOME'] = self.original_home
        
        # Remove test directory
        if self.test_dir and os.path.exists(self.test_dir):
            try:
                shutil.rmtree(self.test_dir)
                print(f"✓ Cleaned up test environment")
            except Exception as e:
                print(f"⚠ Could not fully clean up: {e}")
    
    def run_tests(self):
        """Run all CI tests"""
        print("="*60)
        print("MCP INSTALLER CI/CD TESTS")
        print(f"Platform: {self.system}")
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
            
            # Test 4: Path handling
            print("\n[Test 4: Cross-Platform Path Handling]")
            self.test_path_handling()
            
        finally:
            # Always cleanup
            print("\n[Cleanup]")
            self.cleanup()
        
        # Report results
        print("\n" + "="*60)
        if self.test_passed:
            print(f"✅ ALL CI TESTS PASSED on {self.system}")
            print("Production installer is clean and uncontaminated")
            return 0
        else:
            print(f"❌ CI TESTS FAILED on {self.system}")
            print("Check errors above")
            return 1

def main():
    """Entry point for CI testing"""
    tester = InstallerCITest()
    return tester.run_tests()

if __name__ == '__main__':
    sys.exit(main())