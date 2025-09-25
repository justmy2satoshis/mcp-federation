#!/usr/bin/env python3
"""
MCP Federation Pro Uninstaller
Clean uninstaller that ONLY removes MCPs we installed
Preserves all other user MCPs
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import shutil

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

class SafeMCPUninstaller:
    """Safe uninstaller that only removes what we installed"""
    
    def __init__(self, force=False):
        self.force = force
        self.home_dir = Path.home()
        
        # Paths
        self.config_path = self.home_dir / '.claude' / 'claude_desktop_config.json'
        self.manifest_dir = self.home_dir / '.mcp-federation'
        self.manifest_path = self.manifest_dir / 'installation_manifest.json'
        self.backup_dir = self.manifest_dir / 'backups'
        
        self.manifest = None
        self.removed_count = 0
    
    def print_banner(self):
        """Print uninstaller banner"""
        print(f"{Colors.HEADER}{Colors.BOLD}")
        print("="*60)
        print("    MCP FEDERATION PRO UNINSTALLER")
        print("    Safe Removal - Preserves Other MCPs")
        print("="*60)
        print(f"{Colors.ENDC}\n")
    
    def load_manifest(self) -> bool:
        """Load installation manifest"""
        if not self.manifest_path.exists():
            print(f"{Colors.WARNING}No installation manifest found.{Colors.ENDC}")
            print("This means either:")
            print("  1. MCP Federation was never installed")
            print("  2. Installation was done with an older version")
            print("\nUse --force to remove all 15 standard MCPs anyway.")
            return False
        
        try:
            with open(self.manifest_path) as f:
                self.manifest = json.load(f)
            
            print(f"{Colors.OKCYAN}Found installation manifest:{Colors.ENDC}")
            print(f"  • Version: {self.manifest.get('version', 'unknown')}")
            print(f"  • Installed on: {self.manifest.get('installation_date', 'unknown')}")
            print(f"  • MCPs installed by us: {len(self.manifest.get('installed_by_us', []))}")
            print(f"  • MCPs that already existed: {len(self.manifest.get('already_existed', []))}")
            
            return True
            
        except Exception as e:
            print(f"{Colors.FAIL}Error reading manifest: {e}{Colors.ENDC}")
            return False
    
    def backup_current_config(self) -> bool:
        """Backup current configuration before uninstalling"""
        if not self.config_path.exists():
            return True
        
        try:
            # Create backup directory
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Create timestamped backup
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.backup_dir / f'pre_uninstall_{timestamp}.json'
            
            shutil.copy2(self.config_path, backup_path)
            print(f"{Colors.OKGREEN}✅ Config backed up to {backup_path}{Colors.ENDC}")
            return True
            
        except Exception as e:
            print(f"{Colors.FAIL}Failed to backup config: {e}{Colors.ENDC}")
            return False
    
    def remove_our_mcps(self) -> bool:
        """Remove only the MCPs we installed"""
        if not self.config_path.exists():
            print(f"{Colors.WARNING}No config file found - nothing to uninstall{Colors.ENDC}")
            return True
        
        try:
            # Load current config
            with open(self.config_path) as f:
                config = json.load(f)
            
            if 'mcpServers' not in config:
                print(f"{Colors.WARNING}No MCPs found in config{Colors.ENDC}")
                return True
            
            # Determine which MCPs to remove
            if self.manifest:
                # Use manifest to determine what to remove
                to_remove = self.manifest.get('installed_by_us', [])
                print(f"\n{Colors.OKBLUE}Removing MCPs installed by us:{Colors.ENDC}")
            elif self.force:
                # Force mode - remove all 15 standard MCPs
                to_remove = [
                    'filesystem', 'memory', 'sequential-thinking', 'github-manager',
                    'sqlite', 'playwright', 'web-search', 'git-ops',
                    'desktop-commander', 'perplexity', 'expert-role-prompt',
                    'converse-enhanced', 'kimi-k2-code-context',
                    'kimi-k2-resilient', 'rag-context'
                ]
                print(f"\n{Colors.WARNING}Force mode - removing all 15 standard MCPs{Colors.ENDC}")
            else:
                print(f"{Colors.WARNING}No manifest and no --force flag{Colors.ENDC}")
                return False
            
            # Remove MCPs
            original_count = len(config['mcpServers'])
            for mcp in to_remove:
                if mcp in config['mcpServers']:
                    del config['mcpServers'][mcp]
                    self.removed_count += 1
                    print(f"  - Removed {mcp}")
                else:
                    print(f"  • {mcp} not found (already removed?)")
            
            # Save updated config
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            remaining_count = len(config['mcpServers'])
            print(f"\n{Colors.OKGREEN}✅ Removed {self.removed_count} MCPs{Colors.ENDC}")
            print(f"   Remaining MCPs: {remaining_count} (preserved)")
            
            return True
            
        except Exception as e:
            print(f"{Colors.FAIL}Error removing MCPs: {e}{Colors.ENDC}")
            return False
    
    def cleanup_manifest(self):
        """Remove manifest and cleanup directory"""
        try:
            if self.manifest_path.exists():
                self.manifest_path.unlink()
                print(f"{Colors.OKGREEN}✅ Removed installation manifest{Colors.ENDC}")
            
            # Keep backup directory but remove manifest dir if empty
            if self.manifest_dir.exists():
                # Check if only backups remain
                remaining = list(self.manifest_dir.glob('*'))
                if len(remaining) == 1 and remaining[0].name == 'backups':
                    print(f"{Colors.OKCYAN}Keeping backup directory for safety{Colors.ENDC}")
                elif len(remaining) == 0:
                    self.manifest_dir.rmdir()
                    print(f"{Colors.OKGREEN}✅ Removed manifest directory{Colors.ENDC}")
            
        except Exception as e:
            print(f"{Colors.WARNING}Could not cleanup manifest: {e}{Colors.ENDC}")
    
    def run(self) -> int:
        """Main uninstall process"""
        self.print_banner()
        
        # Load manifest
        print(f"{Colors.OKBLUE}Loading installation manifest...{Colors.ENDC}")
        has_manifest = self.load_manifest()
        
        if not has_manifest and not self.force:
            print(f"\n{Colors.FAIL}Cannot uninstall without manifest.{Colors.ENDC}")
            print("Use --force to remove all 15 standard MCPs anyway.")
            return 1
        
        # Confirm uninstallation
        print(f"\n{Colors.WARNING}This will remove the following:{Colors.ENDC}")
        if self.manifest:
            mcps = self.manifest.get('installed_by_us', [])
            print(f"  • {len(mcps)} MCPs that we installed")
            for mcp in mcps[:5]:  # Show first 5
                print(f"    - {mcp}")
            if len(mcps) > 5:
                print(f"    ... and {len(mcps)-5} more")
        else:
            print("  • All 15 standard Federation MCPs")
        
        print(f"\n{Colors.OKCYAN}MCPs NOT installed by us will be preserved.{Colors.ENDC}")
        
        response = input(f"\n{Colors.WARNING}Proceed with uninstall? (yes/no): {Colors.ENDC}")
        if response.lower() not in ['yes', 'y']:
            print("Uninstall cancelled.")
            return 0
        
        # Backup current config
        print(f"\n{Colors.OKBLUE}Creating backup...{Colors.ENDC}")
        if not self.backup_current_config():
            print(f"{Colors.FAIL}Backup failed - aborting for safety{Colors.ENDC}")
            return 1
        
        # Remove our MCPs
        print(f"\n{Colors.OKBLUE}Removing MCPs...{Colors.ENDC}")
        if not self.remove_our_mcps():
            print(f"{Colors.FAIL}Failed to remove MCPs{Colors.ENDC}")
            return 1
        
        # Cleanup manifest
        if self.manifest:
            print(f"\n{Colors.OKBLUE}Cleaning up manifest...{Colors.ENDC}")
            self.cleanup_manifest()
        
        # Success
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}")
        print("="*60)
        print("    UNINSTALL COMPLETE")
        print(f"    Removed {self.removed_count} MCPs")
        print(f"    Other MCPs preserved")
        print("="*60)
        print(f"{Colors.ENDC}")
        
        print(f"\n{Colors.OKCYAN}Notes:{Colors.ENDC}")
        print("  • Your other MCPs were preserved")
        print("  • Backups saved in ~/.mcp-federation/backups/")
        print("  • Restart Claude Desktop to apply changes\n")
        
        return 0

def main():
    """Entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='MCP Federation Pro Uninstaller - Safe removal'
    )
    parser.add_argument('--force', action='store_true',
                        help='Force removal of all 15 MCPs even without manifest')
    
    args = parser.parse_args()
    
    uninstaller = SafeMCPUninstaller(force=args.force)
    return uninstaller.run()

if __name__ == '__main__':
    sys.exit(main())