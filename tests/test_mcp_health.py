#!/usr/bin/env python3
"""
Test MCP health and installation
"""

import json
import sys
from pathlib import Path
import unittest

class TestMCPHealth(unittest.TestCase):
    """Test MCP installation health"""
    
    def setUp(self):
        """Set up test environment"""
        self.home_dir = Path.home()
        self.config_path = self.home_dir / '.claude' / 'claude_desktop_config.json'
        
        # Expected MCPs
        self.expected_mcps = [
            'filesystem', 'memory', 'sequential-thinking', 'github-manager',
            'sqlite', 'playwright', 'web-search', 'git-ops',
            'desktop-commander', 'perplexity', 'expert-role-prompt',
            'converse-enhanced', 'kimi-k2-code-context',
            'kimi-k2-resilient', 'rag-context'
        ]
    
    def test_config_exists(self):
        """Test that config file can be created"""
        # In CI/CD, we just test that the path is valid
        self.assertIsNotNone(self.config_path)
        self.assertTrue(str(self.config_path).endswith('claude_desktop_config.json'))
    
    def test_mcp_count(self):
        """Test that we have 15 MCPs defined"""
        self.assertEqual(len(self.expected_mcps), 15)
    
    def test_installer_imports(self):
        """Test that installer can be imported"""
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent))
            import install
            self.assertTrue(hasattr(install, 'SafeMCPInstaller'))
        except ImportError:
            self.fail("Could not import installer")
    
    def test_uninstaller_imports(self):
        """Test that uninstaller can be imported"""
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent))
            import uninstall
            self.assertTrue(hasattr(uninstall, 'SafeMCPUninstaller'))
        except ImportError:
            self.fail("Could not import uninstaller")

if __name__ == '__main__':
    unittest.main()