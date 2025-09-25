#!/usr/bin/env python3
"""
MCP Federation Pro Installer v2.1.0
PRODUCTION INSTALLER - NO TEST CODE
Safe installer that preserves existing MCPs and tracks what it installs
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

__version__ = "2.1.0"

# ANSI color codes
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class MCPInstaller:
    """Production MCP installer - NO TEST CODE"""
    
    def __init__(self):
        """Initialize installer - NO TEST PARAMETERS"""
        self.start_time = time.time()
        
        # Platform detection
        self.system = platform.system()
        self.home_dir = Path.home()
        
        # Configuration paths
        self.config_dir = self.home_dir / '.claude'
        self.config_path = self.config_dir / 'claude_desktop_config.json'
        
        # Manifest and backup paths
        self.manifest_dir = self.home_dir / '.mcp-federation'
        self.manifest_path = self.manifest_dir / 'installation_manifest.json'
        self.backup_dir = self.manifest_dir / 'backups'
        
        # Tracking
        self.existing_mcps = set()
        self.installed_by_us = []
        self.already_existed = []
        
        # EXACT working MCP configurations from production
        self.MCP_CONFIGS = {
            'filesystem': {
                'command': 'npx',
                'args': ['-y', '@modelcontextprotocol/server-filesystem', str(self.home_dir)],
                'env': {'NODE_NO_WARNINGS': '1'}
            },
            'memory': {
                'command': 'npx',
                'args': ['-y', '@modelcontextprotocol/server-memory'],
                'env': {'NODE_NO_WARNINGS': '1'}
            },
            'sequential-thinking': {
                'command': 'npx',
                'args': ['-y', '@modelcontextprotocol/server-sequential-thinking'],
                'env': {'NODE_NO_WARNINGS': '1'}
            },
            'github-manager': {
                'command': 'npx',
                'args': ['-y', '@modelcontextprotocol/server-github'],
                'env': {'GITHUB_PERSONAL_ACCESS_TOKEN': 'YOUR_GITHUB_TOKEN'}
            },
            'sqlite': {
                'command': 'npx',
                'args': ['-y', 'mcp-sqlite', str(self.home_dir / 'mcp-servers' / 'databases' / 'dev.db')],
                'env': {'NODE_NO_WARNINGS': '1'}
            },
            'playwright': {
                'command': 'npx',
                'args': ['-y', '@playwright/mcp@0.0.37', '--browser', 'chromium'],
                'env': {'NODE_NO_WARNINGS': '1'}
            },
            'web-search': {
                'command': 'npx',
                'args': ['-y', '@modelcontextprotocol/server-brave-search'],
                'env': {'BRAVE_API_KEY': 'YOUR_BRAVE_KEY'}
            },
            'git-ops': {
                'command': 'npx',
                'args': ['-y', '@cyanheads/git-mcp-server'],
                'env': {
                    'NODE_NO_WARNINGS': '1',
                    'GIT_REPO_PATH': str(self.home_dir / 'mcp-project')
                }
            },
            'desktop-commander': {
                'command': 'npx',
                'args': ['-y', '@wonderwhy-er/desktop-commander@latest'],
                'env': {'NODE_NO_WARNINGS': '1'}
            },
            'perplexity': {
                'command': 'npx',
                'args': ['-y', 'server-perplexity-ask'],
                'env': {'PERPLEXITY_API_KEY': 'YOUR_PERPLEXITY_KEY'}
            },
            'expert-role-prompt': {
                'command': 'node',
                'args': [str(self.home_dir / 'mcp-servers' / 'expert-role-prompt' / 'server.js')],
                'env': {'NODE_NO_WARNINGS': '1'}
            },
            'converse-enhanced': {
                'command': 'python',
                'args': [str(self.home_dir / 'mcp-servers' / 'converse-mcp-enhanced' / 'src' / 'mcp_server.py')],
                'env': {
                    'OPENAI_API_KEY': 'YOUR_OPENAI_KEY',
                    'GEMINI_API_KEY': 'YOUR_GEMINI_KEY'
                }
            },
            'kimi-k2-code-context': {
                'command': 'python',
                'args': [str(self.home_dir / 'mcp-servers' / 'kimi-k2-code-context-enhanced' / 'server.py')],
                'env': {}
            },
            'kimi-k2-resilient': {
                'command': 'python',
                'args': [str(self.home_dir / 'mcp-servers' / 'kimi-k2-resilient-enhanced' / 'server.py')],
                'env': {}
            },
            'rag-context': {
                'command': 'python',
                'args': [str(self.home_dir / 'mcp-servers' / 'rag-context-fixed' / 'server.py')],
                'env': {}
            }
        }
    
    def print_banner(self):
        """Print installer banner"""
        print(f"{Colors.HEADER}{Colors.BOLD}")
        print("="*60)
        print(f"    MCP FEDERATION PRO INSTALLER v{__version__}")
        print("    Production Installer - Safe Installation")
        print("    Preserves Existing MCPs | Clean Uninstall")
        print("="*60)
        print(f"{Colors.ENDC}")
        print(f"\n{Colors.OKCYAN}System: {self.system}")
        print(f"Config: {self.config_path}{Colors.ENDC}\n")
    
    def check_prerequisites(self) -> bool:
        """Check system prerequisites"""
        print(f"{Colors.OKBLUE}Checking prerequisites...{Colors.ENDC}")
        
        checks = [
            ('Python', 'python --version'),
            ('Node.js', 'node --version'),
            ('npm', 'npm --version'),
            ('Git', 'git --version')
        ]
        
        all_good = True
        for name, cmd in checks:
            try:
                result = subprocess.run(
                    cmd.split(),
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    print(f"  ✅ {name}: {result.stdout.strip()}")
                else:
                    print(f"  ❌ {name}: Not found")
                    all_good = False
            except Exception as e:
                print(f"  ❌ {name}: {e}")
                all_good = False
        
        return all_good
    
    def read_existing_config(self) -> Optional[Dict]:
        """Read existing Claude Desktop configuration"""
        if not self.config_path.exists():
            print(f"{Colors.OKBLUE}No existing config found - fresh installation{Colors.ENDC}")
            return None
        
        try:
            with open(self.config_path) as f:
                config = json.load(f)
            
            # Track existing MCPs
            if 'mcpServers' in config:
                self.existing_mcps = set(config['mcpServers'].keys())
                print(f"{Colors.OKCYAN}Found {len(self.existing_mcps)} existing MCPs{Colors.ENDC}")
                
                # Categorize MCPs
                for mcp in self.MCP_CONFIGS.keys():
                    if mcp in self.existing_mcps:
                        self.already_existed.append(mcp)
                
            return config
            
        except Exception as e:
            print(f"{Colors.WARNING}Error reading existing config: {e}{Colors.ENDC}")
            return None
    
    def backup_config(self) -> bool:
        """Backup existing configuration"""
        if not self.config_path.exists():
            return True
        
        try:
            # Create backup directory
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Create timestamped backup
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.backup_dir / f'claude_desktop_config_{timestamp}.json'
            
            shutil.copy2(self.config_path, backup_path)
            print(f"{Colors.OKGREEN}✅ Config backed up to {backup_path}{Colors.ENDC}")
            return True
            
        except Exception as e:
            print(f"{Colors.FAIL}Failed to backup config: {e}{Colors.ENDC}")
            return False
    
    def merge_configs(self, existing_config: Optional[Dict]) -> Dict:
        """Safely merge new MCPs with existing configuration"""
        if existing_config is None:
            # Fresh installation
            config = {'mcpServers': {}}
        else:
            # Preserve existing config
            config = existing_config.copy()
            if 'mcpServers' not in config:
                config['mcpServers'] = {}
        
        # Add our MCPs without overwriting existing ones
        for name, mcp_config in self.MCP_CONFIGS.items():
            if name not in config['mcpServers']:
                config['mcpServers'][name] = mcp_config
                self.installed_by_us.append(name)
                print(f"  + Adding {name}")
            else:
                print(f"  ✓ {name} already exists - skipping")
        
        return config
    
    def save_config(self, config: Dict) -> bool:
        """Save configuration to file"""
        try:
            # Ensure directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Save config
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"{Colors.OKGREEN}✅ Configuration saved{Colors.ENDC}")
            return True
            
        except Exception as e:
            print(f"{Colors.FAIL}Failed to save config: {e}{Colors.ENDC}")
            return False
    
    def save_manifest(self) -> bool:
        """Save installation manifest for clean uninstall"""
        try:
            self.manifest_dir.mkdir(parents=True, exist_ok=True)
            
            manifest = {
                'version': __version__,
                'installation_date': datetime.now().isoformat(),
                'installed_by_us': self.installed_by_us,
                'already_existed': self.already_existed,
                'system': self.system,
                'claude_desktop_mcps': list(self.MCP_CONFIGS.keys())
            }
            
            with open(self.manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            print(f"{Colors.OKGREEN}✅ Installation manifest saved{Colors.ENDC}")
            return True
            
        except Exception as e:
            print(f"{Colors.WARNING}Could not save manifest: {e}{Colors.ENDC}")
            return False
    
    def validate_installation(self, config: Dict) -> bool:
        """Validate that all 15 MCPs are in config"""
        if 'mcpServers' not in config:
            return False
        
        mcp_count = len(config['mcpServers'])
        required_count = len(self.MCP_CONFIGS)
        
        if mcp_count >= required_count:
            print(f"{Colors.OKGREEN}✅ All {required_count} MCPs configured successfully{Colors.ENDC}")
            
            # Check each required MCP
            missing = []
            for name in self.MCP_CONFIGS.keys():
                if name not in config['mcpServers']:
                    missing.append(name)
            
            if missing:
                print(f"{Colors.WARNING}Missing MCPs: {', '.join(missing)}{Colors.ENDC}")
                return False
            
            return True
        else:
            print(f"{Colors.WARNING}Expected {required_count} MCPs, found {mcp_count}{Colors.ENDC}")
            return False
    
    def run(self) -> int:
        """Main installation process - PRODUCTION ONLY"""
        self.print_banner()
        
        # Check prerequisites
        if not self.check_prerequisites():
            print(f"\n{Colors.FAIL}Prerequisites not met. Please install required tools:{Colors.ENDC}")
            print("  • Python 3.9+")
            print("  • Node.js 18+")
            print("  • npm 8+")
            print("  • Git")
            return 1
        
        # Read existing configuration
        print(f"\n{Colors.OKBLUE}Checking existing configuration...{Colors.ENDC}")
        existing_config = self.read_existing_config()
        
        # Backup existing config
        if existing_config:
            print(f"\n{Colors.OKBLUE}Creating backup...{Colors.ENDC}")
            if not self.backup_config():
                print(f"{Colors.FAIL}Backup failed - aborting for safety{Colors.ENDC}")
                return 1
        
        # Merge configurations
        print(f"\n{Colors.OKBLUE}Merging MCP configurations...{Colors.ENDC}")
        merged_config = self.merge_configs(existing_config)
        
        # Save merged configuration
        print(f"\n{Colors.OKBLUE}Saving configuration...{Colors.ENDC}")
        if not self.save_config(merged_config):
            return 1
        
        # Validate installation
        print(f"\n{Colors.OKBLUE}Validating installation...{Colors.ENDC}")
        if not self.validate_installation(merged_config):
            print(f"{Colors.WARNING}Validation warnings (non-fatal){Colors.ENDC}")
        
        # Save installation manifest
        print(f"\n{Colors.OKBLUE}Saving installation manifest...{Colors.ENDC}")
        self.save_manifest()
        
        # Success report
        elapsed = time.time() - self.start_time
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}")
        print("="*60)
        print(f"🎉 SUCCESS! Installation completed in {elapsed:.1f} seconds")
        print("="*60)
        print(f"{Colors.ENDC}")
        
        # Summary
        print(f"\n{Colors.OKCYAN}Installation Summary:{Colors.ENDC}")
        print(f"  • Newly installed: {len(self.installed_by_us)} MCPs")
        print(f"  • Already existed: {len(self.already_existed)} MCPs")
        print(f"  • Total MCPs now: {len(merged_config.get('mcpServers', {}))} ")
        
        if self.installed_by_us:
            print(f"\n{Colors.OKCYAN}Newly installed MCPs:{Colors.ENDC}")
            for mcp in self.installed_by_us:
                print(f"    • {mcp}")
        
        print(f"\n{Colors.OKCYAN}Next steps:{Colors.ENDC}")
        print("  1. Restart Claude Desktop")
        print("  2. Configure API keys as needed")
        print("  3. To uninstall: python uninstall.py\n")
        
        return 0

def main():
    """Entry point - PRODUCTION ONLY, NO TEST FLAGS"""
    # NO ARGPARSE - NO FLAGS - PRODUCTION ONLY
    installer = MCPInstaller()
    return installer.run()

if __name__ == '__main__':
    sys.exit(main())