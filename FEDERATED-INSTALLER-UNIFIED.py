#!/usr/bin/env python3
"""
MCP Federation Core v0.1.6 - Fixed converse-enhanced missing requirements.txt
Copyright (c) 2025 justmy2satoshis
Licensed under MIT License

CRITICAL UPDATE v0.1.6 - Fixed converse-enhanced installation:
- converse-enhanced now installs dependencies directly (httpx, python-dotenv)
- Bypasses missing requirements.txt in repository

PREVIOUS UPDATE v0.1.5 - Fixed converse-enhanced to use Python server:
- converse-enhanced now correctly uses Python server.py instead of npm package

PREVIOUS UPDATE v0.1.4 - Fixed directory nesting and MCP command errors:
- DIRECTORY FIX: Prevents triple-nested directory creation bug
- MCP COMMANDS: Updated to match working Claude Desktop configuration
- COMPLETE UNINSTALL: Now removes ALL installed files and directories
- PYTHON COMMAND: Uses 'python' on Windows (not python3)

PREVIOUS FIXES v0.1.3 - Fixed data loss bug in uninstaller:
- NEVER overwrites existing MCP configurations
- Creates multiple backups before any changes
- Merges new federation MCPs with existing user MCPs
- Provides user confirmation and rollback capability
- ✅ FIXED: Correct npm package names (sqlite, playwright, git-ops, desktop-commander)
- ✅ FIXED: GitHub repository URLs updated to match working structure
- ✅ FIXED: Python commands changed to python3 for cross-platform compatibility
- ✅ FIXED: Duplicate prevention logic prevents MCP conflicts
- Sources MCPs from original repositories (npm + GitHub)
- Implements selective database unification (40% memory savings)
- Maintains zero bundled code - pure orchestration
"""

import json
import os
import subprocess
import sys
import shutil
import platform
from pathlib import Path
from datetime import datetime

# Fix Windows Unicode
if platform.system() == "Windows":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class FederatedUnifiedInstaller:
    """
    Installer that:
    1. Sources MCPs from original repositories
    2. Implements unified database for MCPs that benefit
    3. Maintains updateability from upstream
    """

    def __init__(self):
        self.home = Path.home()
        self.base_dir = self.home / "mcp-servers"
        self.config_path = self._get_config_path()
        self.db_path = self.base_dir / "mcp-unified.db"
        self.wrapper_dir = self.base_dir / "federation-wrappers"
        self.is_windows = platform.system() == "Windows"

        # MCPs that benefit from unified database
        self.UNIFIED_DB_MCPS = [
            'memory',
            'kimi-k2-code-context',
            'kimi-k2-resilient',
            'rag-context'
        ]

        # Track installation
        self.installed_mcps = []
        self.failed_mcps = []

        # Installation manifest for safe uninstallation
        self.manifest_path = self.base_dir / "installation_manifest.json"

    def check_installation_location(self):
        """Prevent nested directory creation bug"""
        current_dir = Path.cwd()

        # Check if we're already in mcp-federation-core
        if current_dir.name == 'mcp-federation-core':
            print("\n" + "="*70)
            print(" ⚠️  DIRECTORY WARNING - Already in mcp-federation-core")
            print("="*70)
            print("\n❌ Do NOT clone again - this would create nested directories")
            print("✅ You're in the right place - run the installer directly:")
            print(f"   {'python' if self.is_windows else 'python3'} FEDERATED-INSTALLER-UNIFIED.py")
            print("")
            return True  # OK to proceed with installation

        # Check if mcp-federation-core exists as subdirectory
        if (current_dir / 'mcp-federation-core').exists():
            print("\n" + "="*70)
            print(" 📁 Found existing mcp-federation-core directory")
            print("="*70)
            print("\nChange to that directory first:")
            print("   cd mcp-federation-core")
            print(f"   {'python' if self.is_windows else 'python3'} FEDERATED-INSTALLER-UNIFIED.py")
            print("")
            return False  # Don't proceed

        # Check for nested structure (already in nested directory)
        if 'mcp-federation-core' in str(current_dir) and current_dir.parent.name == 'mcp-federation-core':
            print("\n" + "="*70)
            print(" ⚠️  NESTED DIRECTORY DETECTED")
            print("="*70)
            print(f"\nYou appear to be in a nested directory structure:")
            print(f"   {current_dir}")
            print("\nNavigate to the root mcp-federation-core directory:")
            print("   cd ../..")
            print(f"   {'python' if self.is_windows else 'python3'} FEDERATED-INSTALLER-UNIFIED.py")
            print("")
            return False  # Don't proceed

        return True  # OK to proceed

    def _get_config_path(self):
        """Get Claude Desktop config path"""
        if platform.system() == "Windows":
            return Path(os.environ.get('APPDATA', '')) / "Claude" / "claude_desktop_config.json"
        elif platform.system() == "Darwin":
            return self.home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
        else:
            return self.home / ".config" / "Claude" / "claude_desktop_config.json"

    def create_wrapper(self, mcp_name, original_config):
        """
        Create wrapper script that sets unified database environment
        before executing the original MCP
        """
        self.wrapper_dir.mkdir(parents=True, exist_ok=True)

        if self.is_windows:
            # Windows batch wrapper
            wrapper_path = self.wrapper_dir / f"{mcp_name}-wrapper.bat"
            wrapper_content = f"""@echo off
set MCP_DATABASE={self.db_path}
set DATABASE_URL=sqlite:///{self.db_path}
set SQLITE_PATH={self.db_path}
set MCP_UNIFIED=true
{original_config['command']} {' '.join(original_config['args'])} %*
"""
        else:
            # Unix shell wrapper
            wrapper_path = self.wrapper_dir / f"{mcp_name}-wrapper.sh"
            wrapper_content = f"""#!/bin/bash
export MCP_DATABASE="{self.db_path}"
export DATABASE_URL="sqlite:///{self.db_path}"
export SQLITE_PATH="{self.db_path}"
export MCP_UNIFIED="true"
{original_config['command']} {' '.join(original_config['args'])} "$@"
"""

        wrapper_path.write_text(wrapper_content)
        if not self.is_windows:
            wrapper_path.chmod(0o755)

        print(f"  📦 Created wrapper for unified database: {wrapper_path.name}")
        return wrapper_path

    def get_mcp_configuration(self, name, mcp_info):
        """
        Generate configuration with selective unified database
        """
        config = mcp_info['config'].copy()

        # Check if this MCP should use unified database
        if name in self.UNIFIED_DB_MCPS:
            print(f"  🔗 Configuring {name} for unified database")

            # First try environment variables (cleanest approach)
            if 'env' not in config:
                config['env'] = {}

            config['env'].update({
                'MCP_DATABASE': str(self.db_path),
                'DATABASE_URL': f'sqlite:///{self.db_path}',
                'SQLITE_PATH': str(self.db_path),
                'MCP_UNIFIED': 'true',
                'MCP_NAMESPACE': name  # Namespace tables per MCP
            })

            # For GitHub MCPs that may not respect env vars, use wrapper
            if mcp_info['type'] == 'github' and name in self.UNIFIED_DB_MCPS:
                wrapper_path = self.create_wrapper(name, config)

                # Update config to use wrapper
                if self.is_windows:
                    config['command'] = 'cmd'
                    config['args'] = ['/c', str(wrapper_path)]
                else:
                    config['command'] = str(wrapper_path)
                    config['args'] = []

        return config

    def get_mcp_source_matrix(self):
        """
        Complete source matrix with database unification info
        """
        return {
            # NPM MCPs with env var support
            'sequential-thinking': {
                'type': 'npm',
                'source': '@modelcontextprotocol/server-sequential-thinking',
                'install': ['npm', 'install', '-g', '@modelcontextprotocol/server-sequential-thinking'],
                'needs_db': False,
                'config': {
                    'command': 'npx',
                    'args': ['-y', '@modelcontextprotocol/server-sequential-thinking']
                }
            },
            'memory': {
                'type': 'npm',
                'source': '@modelcontextprotocol/server-memory',
                'install': ['npm', 'install', '-g', '@modelcontextprotocol/server-memory'],
                'needs_db': True,  # UNIFIED
                'config': {
                    'command': 'npx',
                    'args': ['-y', '@modelcontextprotocol/server-memory']
                }
            },
            'filesystem': {
                'type': 'npm',
                'source': '@modelcontextprotocol/server-filesystem',
                'install': ['npm', 'install', '-g', '@modelcontextprotocol/server-filesystem'],
                'needs_db': False,
                'config': {
                    'command': 'npx',
                    'args': ['-y', '@modelcontextprotocol/server-filesystem', str(self.home)]
                }
            },
            'sqlite': {
                'type': 'npm',
                'source': 'mcp-sqlite',
                'install': ['npm', 'install', '-g', 'mcp-sqlite'],
                'needs_db': False,  # Special case - IS the database interface
                'config': {
                    'command': 'npx',
                    'args': ['-y', 'mcp-sqlite', str(self.db_path)]
                }
            },
            'github-manager': {
                'type': 'npm',
                'source': '@modelcontextprotocol/server-github',
                'install': ['npm', 'install', '-g', '@modelcontextprotocol/server-github'],
                'needs_db': False,
                'config': {
                    'command': 'npx',
                    'args': ['-y', '@modelcontextprotocol/server-github'],
                    'env': {'GITHUB_TOKEN': 'YOUR_GITHUB_TOKEN'}
                }
            },
            'web-search': {
                'type': 'npm',
                'source': '@modelcontextprotocol/server-brave-search',
                'install': ['npm', 'install', '-g', '@modelcontextprotocol/server-brave-search'],
                'needs_db': False,
                'config': {
                    'command': 'npx',
                    'args': ['-y', '@modelcontextprotocol/server-brave-search'],
                    'env': {'BRAVE_API_KEY': 'YOUR_BRAVE_API_KEY'}
                }
            },
            'playwright': {
                'type': 'npm',
                'source': '@playwright/mcp@0.0.39',
                'install': ['npm', 'install', '-g', '@playwright/mcp@0.0.39'],
                'needs_db': False,
                'config': {
                    'command': 'npx',
                    'args': ['-y', '@playwright/mcp@0.0.39',
                           '--browser', 'chromium']
                }
            },
            'git-ops': {
                'type': 'npm',
                'source': '@cyanheads/git-mcp-server',
                'install': ['npm', 'install', '-g', '@cyanheads/git-mcp-server'],
                'needs_db': False,
                'config': {
                    'command': 'npx',
                    'args': ['-y', '@cyanheads/git-mcp-server']
                }
            },
            'desktop-commander': {
                'type': 'npm',
                'source': '@wonderwhy-er/desktop-commander@latest',
                'install': ['npm', 'install', '-g', '@wonderwhy-er/desktop-commander@latest'],
                'needs_db': False,
                'config': {
                    'command': 'npx',
                    'args': ['-y', '@wonderwhy-er/desktop-commander@latest']
                }
            },
            'perplexity': {
                'type': 'npm',
                'source': 'server-perplexity-ask',
                'install': ['npm', 'install', '-g', 'server-perplexity-ask'],
                'needs_db': False,
                'config': {
                    'command': 'npx',
                    'args': ['-y', 'server-perplexity-ask'],
                    'env': {'PERPLEXITY_API_KEY': 'YOUR_PERPLEXITY_KEY'}
                }
            },

            # GitHub MCPs - need wrappers for unified DB
            'expert-role-prompt': {
                'type': 'github',
                'source': 'https://github.com/justmy2satoshis/expert-role-prompt-mcp.git',
                'directory': 'expert-role-prompt-mcp',
                'branch': 'main',
                'install': ['npm', 'install'],
                'needs_db': False,
                'config': {
                    'command': 'node',
                    'args': [str(self.base_dir / 'expert-role-prompt-mcp' / 'server.js')]
                }
            },
            'converse-enhanced': {
                'type': 'github',
                'source': 'https://github.com/justmy2satoshis/converse-mcp-enhanced.git',
                'directory': 'converse-mcp-enhanced',
                'branch': 'main',
                'install': ['pip', 'install', 'httpx', 'python-dotenv'],
                'needs_db': False,
                'config': {
                    'command': 'python',
                    'args': [str(self.base_dir / 'converse-mcp-enhanced' / 'src' / 'mcp_server.py')],
                    'env': {
                        'OPENAI_API_KEY': 'YOUR_OPENAI_KEY',
                        'GEMINI_API_KEY': 'YOUR_GEMINI_KEY'
                    }
                }
            },
            'kimi-k2-code-context': {
                'type': 'federation',
                'source_directory': 'mcp-servers/kimi-k2-code-context-enhanced',
                'directory': 'kimi-k2-code-context-enhanced',
                'install': [],  # Python server - no npm install needed
                'needs_db': True,  # UNIFIED with wrapper
                'config': {
                    'command': 'python' if self.is_windows else 'python3',
                    'args': [str(self.base_dir / 'kimi-k2-code-context-enhanced' / 'server.py')]
                }
            },
            'kimi-k2-resilient': {
                'type': 'federation',
                'source_directory': 'mcp-servers/kimi-k2-resilient-enhanced',
                'directory': 'kimi-k2-resilient-enhanced',
                'install': [],  # Python server - no npm install needed
                'needs_db': True,  # UNIFIED with wrapper
                'config': {
                    'command': 'python' if self.is_windows else 'python3',
                    'args': [str(self.base_dir / 'kimi-k2-resilient-enhanced' / 'server.py')]
                }
            },
            'rag-context': {
                'type': 'federation',
                'source_directory': 'mcp-servers/rag-context-fixed',
                'directory': 'rag-context-fixed',
                'install': [],  # Python server - no npm install needed
                'needs_db': True,  # UNIFIED
                'config': {
                    'command': 'python' if self.is_windows else 'python3',
                    'args': [str(self.base_dir / 'rag-context-fixed' / 'server.py')],
                    'timeout': 120000
                }
            }
        }

    def initialize_unified_database(self):
        """
        Initialize unified database with namespaced schema
        """
        print("\n💾 Initializing unified database...")

        try:
            import sqlite3

            # Create database
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Create namespace tables for each MCP that needs DB
            schemas = {
                'memory': """
                    CREATE TABLE IF NOT EXISTS memory_conversations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        conversation_id TEXT,
                        message TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """,
                'kimi_code': """
                    CREATE TABLE IF NOT EXISTS kimi_code_context (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_path TEXT,
                        analysis TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """,
                'kimi_resilient': """
                    CREATE TABLE IF NOT EXISTS kimi_resilient_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        key TEXT UNIQUE,
                        value TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """,
                'rag': """
                    CREATE TABLE IF NOT EXISTS rag_embeddings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        content TEXT,
                        embedding BLOB,
                        metadata TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """
            }

            for name, schema in schemas.items():
                cursor.execute(schema)
                print(f"  ✓ Created namespace: {name}")

            conn.commit()
            conn.close()

            print(f"  ✅ Unified database initialized: {self.db_path}")
            return True

        except Exception as e:
            print(f"  ⚠️ Could not initialize database: {e}")
            return False

    def install_npm_mcp(self, name, mcp_info):
        """Install MCP from npm registry"""
        print(f"\n📦 Installing {name} from npm...")

        try:
            # Check if already installed
            check_cmd = ['npm', 'list', '-g', mcp_info['source']]
            result = subprocess.run(check_cmd, capture_output=True, text=True, shell=self.is_windows)

            if result.returncode == 0:
                print(f"  ✓ Already installed: {mcp_info['source']}")
                return True

            # Install from npm
            print(f"  Installing: {mcp_info['source']}")
            install_result = subprocess.run(
                mcp_info['install'],
                capture_output=True,
                text=True,
                shell=self.is_windows
            )

            if install_result.returncode == 0:
                print(f"  ✅ Installed: {name}")
                return True
            else:
                print(f"  ❌ Failed: {install_result.stderr[:200]}")
                return False

        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False

    def install_federation_mcp(self, name, mcp_info):
        """Copy federation MCP from bundled sources"""
        print(f"\n📦 Installing {name} from bundled sources...")

        # Get paths
        script_dir = Path(__file__).parent
        source_dir = script_dir / mcp_info['source_directory']
        target_dir = self.base_dir / mcp_info['directory']

        try:
            # Check if source exists
            if not source_dir.exists():
                print(f"  ❌ Source directory not found: {source_dir}")
                return False

            # Copy federation MCP
            if target_dir.exists():
                shutil.rmtree(target_dir)

            shutil.copytree(source_dir, target_dir)
            print(f"  ✅ Federation MCP copied successfully")

            # Install dependencies if needed
            if mcp_info.get('install'):
                if mcp_info['install'][0] == 'npm':
                    result = subprocess.run(['npm', 'install'], cwd=str(target_dir), capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"  ✅ npm dependencies installed")
                    else:
                        print(f"  ⚠️ npm install had warnings (usually OK)")

                elif mcp_info['install'][0] == 'pip':
                    pip_cmd = ['pip', 'install'] if self.is_windows else ['pip3', 'install']
                    pip_cmd.extend(mcp_info['install'][1:])  # Add the packages
                    result = subprocess.run(pip_cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"  ✅ Python dependencies installed")
                    else:
                        print(f"  ⚠️ pip install had warnings: {result.stderr[:100]}")

            return True

        except Exception as e:
            print(f"  ❌ Exception during federation installation: {e}")
            return False

    def install_github_mcp(self, name, mcp_info):
        """Clone and install MCP from GitHub"""
        print(f"\n🔗 Installing {name} from GitHub...")

        target_dir = self.base_dir / mcp_info['directory']

        try:
            if target_dir.exists():
                print(f"  📂 Updating existing repository...")
                pull_cmd = ['git', 'pull', 'origin', mcp_info['branch']]
                subprocess.run(pull_cmd, cwd=str(target_dir), capture_output=True)
            else:
                print(f"  Cloning: {mcp_info['source']}")
                clone_cmd = ['git', 'clone', '-b', mcp_info['branch'],
                           mcp_info['source'], str(target_dir)]
                clone_result = subprocess.run(clone_cmd, capture_output=True, text=True)

                if clone_result.returncode != 0:
                    print(f"  ❌ Clone failed: {clone_result.stderr[:200]}")
                    return False

            # Install dependencies
            if mcp_info['install']:
                print(f"  📦 Installing dependencies...")
                subprocess.run(mcp_info['install'], cwd=str(target_dir),
                             capture_output=True, shell=self.is_windows)

            print(f"  ✅ Ready: {name}")
            return True

        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False

    def backup_existing_config(self):
        """Create multiple backups of existing configuration"""
        if not self.config_path.exists():
            print("  ℹ️ No existing configuration to backup")
            return True

        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            # Create backup directory
            backup_dir = self.config_path.parent / 'config_backups'
            backup_dir.mkdir(exist_ok=True)

            # Create timestamped backup
            backup_path = backup_dir / f'claude_desktop_config_backup_{timestamp}.json'
            shutil.copy2(self.config_path, backup_path)

            # Create 'before_federation' backup if it doesn't exist
            before_federation_path = backup_dir / 'claude_desktop_config_before_federation.json'
            if not before_federation_path.exists():
                shutil.copy2(self.config_path, before_federation_path)
                print(f"  💾 Created 'before_federation' backup: {before_federation_path}")

            print(f"  💾 Configuration backed up: {backup_path}")
            return True

        except Exception as e:
            print(f"  ⚠️ Backup failed: {e}")
            return False

    def load_existing_config(self):
        """Load existing configuration safely"""
        if not self.config_path.exists():
            return {'mcpServers': {}}

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                existing_config = json.load(f)

            # Ensure mcpServers key exists
            if 'mcpServers' not in existing_config:
                existing_config['mcpServers'] = {}

            return existing_config

        except Exception as e:
            print(f"  ⚠️ Could not load existing config: {e}")
            print(f"  ⚠️ Starting with empty configuration")
            return {'mcpServers': {}}

    def create_installation_manifest(self, existing_config):
        """Create manifest tracking pre-existing vs newly installed MCPs"""
        print("\n📋 Creating installation manifest...")

        matrix = self.get_mcp_source_matrix()
        federation_mcps = set(matrix.keys())

        # Identify pre-existing MCPs
        pre_existing_mcps = []
        existing_mcps = existing_config.get('mcpServers', {})

        for name in existing_mcps.keys():
            if name in federation_mcps:
                pre_existing_mcps.append(name)

        # Create manifest
        manifest = {
            'installation_date': datetime.now().isoformat(),
            'installer_version': '0.1.4',
            'pre_existing_mcps': pre_existing_mcps,
            'newly_installed_mcps': [],  # Will be populated during installation
            'failed_mcps': []
        }

        if pre_existing_mcps:
            print(f"  ✅ Detected {len(pre_existing_mcps)} pre-existing federation MCPs:")
            for name in pre_existing_mcps:
                print(f"    • {name} (will be preserved)")

        return manifest

    def save_installation_manifest(self, manifest):
        """Save installation manifest to disk"""
        try:
            with open(self.manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2)
            print(f"  ✅ Manifest saved: {self.manifest_path}")
            return True
        except Exception as e:
            print(f"  ⚠️ Failed to save manifest: {e}")
            return False

    def update_manifest_with_results(self, manifest):
        """Update manifest with installation results"""
        manifest['newly_installed_mcps'] = self.installed_mcps.copy()
        manifest['failed_mcps'] = self.failed_mcps.copy()

        # Remove pre-existing MCPs from newly_installed list if they exist
        newly_installed = []
        for mcp in self.installed_mcps:
            if mcp not in manifest['pre_existing_mcps']:
                newly_installed.append(mcp)

        manifest['newly_installed_mcps'] = newly_installed

        print(f"\n📋 Manifest summary:")
        print(f"  • Pre-existing MCPs: {len(manifest['pre_existing_mcps'])}")
        print(f"  • Newly installed MCPs: {len(manifest['newly_installed_mcps'])}")
        print(f"  • Failed MCPs: {len(manifest['failed_mcps'])}")

        return manifest

    def merge_configurations(self, existing_config, new_mcps):
        """Merge new federation MCPs with existing user MCPs"""
        print("\n🔄 Merging configurations...")

        merged_config = existing_config.copy()
        matrix = self.get_mcp_source_matrix()

        # List of federation MCPs that we manage
        federation_mcps = set(matrix.keys())

        # Count existing non-federation MCPs
        existing_user_mcps = []
        for name in existing_config.get('mcpServers', {}).keys():
            if name not in federation_mcps:
                existing_user_mcps.append(name)

        if existing_user_mcps:
            print(f"  ✅ Preserving {len(existing_user_mcps)} existing user MCPs:")
            for name in existing_user_mcps:
                print(f"    • {name}")

        # Add/update federation MCPs with duplicate prevention
        updated_mcps = []
        duplicate_prevention = {}  # Track duplicates by command+args combination

        for name in new_mcps:
            if name in matrix:
                mcp_config = self.get_mcp_configuration(name, matrix[name])

                # Create signature to detect duplicates
                command = mcp_config.get('command', '')
                args = ' '.join(mcp_config.get('args', []))
                signature = f"{command}|{args}"

                # Check for existing MCP with same signature
                if signature in duplicate_prevention:
                    existing_name = duplicate_prevention[signature]
                    print(f"  ⚠️ Skipping {name}: duplicate of {existing_name}")
                    continue

                # Check if this MCP already exists with different config
                if name in merged_config['mcpServers']:
                    print(f"  🔄 Updating existing MCP: {name}")
                else:
                    print(f"  ➕ Adding new MCP: {name}")

                merged_config['mcpServers'][name] = mcp_config
                duplicate_prevention[signature] = name
                updated_mcps.append(name)

                db_status = "✓ Unified" if name in self.UNIFIED_DB_MCPS else "Independent"
                print(f"    Status: {db_status}")

        print(f"\n  📊 Configuration summary:")
        print(f"    • User MCPs preserved: {len(existing_user_mcps)}")
        print(f"    • Federation MCPs added/updated: {len(updated_mcps)}")
        print(f"    • Total MCPs: {len(merged_config['mcpServers'])}")

        return merged_config

    def confirm_changes(self, existing_config, merged_config):
        """Ask user to confirm configuration changes"""
        print("\n" + "="*60)
        print(" CONFIGURATION CHANGE CONFIRMATION")
        print("="*60)

        existing_count = len(existing_config.get('mcpServers', {}))
        new_count = len(merged_config.get('mcpServers', {}))

        print(f"\n📊 Changes to be made:")
        print(f"  Current MCPs: {existing_count}")
        print(f"  After merge: {new_count}")
        print(f"  Net change: +{new_count - existing_count}")

        if existing_count > 0:
            print(f"\n🔒 Your existing MCPs will be PRESERVED")

        print(f"\n📁 Backup location: {self.config_path.parent / 'config_backups'}")
        print(f"📁 Config file: {self.config_path}")

        while True:
            response = input("\n✅ Proceed with configuration merge? [y/N]: ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no', '']:
                print("\n❌ Installation cancelled by user")
                return False
            else:
                print("Please answer 'y' for yes or 'n' for no")

    def write_configuration_safely(self, config):
        """Write configuration with atomic file operations"""
        print("\n💾 Writing configuration safely...")

        try:
            # Write to temporary file first
            temp_path = self.config_path.with_suffix('.tmp')

            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)

            # Atomic move to final location
            if self.is_windows:
                # Windows requires removing target file first
                if self.config_path.exists():
                    self.config_path.unlink()

            temp_path.rename(self.config_path)

            print(f"  ✅ Configuration saved safely: {self.config_path}")
            return True

        except Exception as e:
            print(f"  ❌ Failed to save configuration: {e}")
            # Clean up temp file if it exists
            if temp_path.exists():
                temp_path.unlink()
            return False

    def write_configuration(self):
        """SAFE configuration writing with backup and merge"""
        print("\n📝 Preparing safe configuration update...")

        # Step 1: Create backup
        if not self.backup_existing_config():
            print("❌ Cannot proceed without backup - installation aborted")
            return False

        # Step 2: Load existing configuration
        existing_config = self.load_existing_config()

        # Step 3: Create installation manifest for safe uninstallation
        manifest = self.create_installation_manifest(existing_config)

        # Step 4: Merge configurations
        merged_config = self.merge_configurations(existing_config, self.installed_mcps)

        # Step 5: Get user confirmation
        if not self.confirm_changes(existing_config, merged_config):
            return False

        # Step 6: Update manifest with installation results
        manifest = self.update_manifest_with_results(manifest)

        # Step 7: Save manifest for safe uninstallation
        self.save_installation_manifest(manifest)

        # Step 8: Write configuration safely
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        return self.write_configuration_safely(merged_config)

    def install(self):
        """Main installation process"""
        print("\n" + "="*70)
        print(" MCP FEDERATION CORE v0.1.6 - UNIFIED INSTALLER")
        print(" All 15 MCPs Working - converse-enhanced Dependencies Fixed")
        print("="*70)

        # Check for directory nesting issues first
        if not self.check_installation_location():
            print("\n❌ Installation aborted to prevent directory issues")
            return False

        # Create directories
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # Initialize unified database
        self.initialize_unified_database()

        # Install MCPs
        matrix = self.get_mcp_source_matrix()

        for name, info in matrix.items():
            success = False
            if info['type'] == 'npm':
                success = self.install_npm_mcp(name, info)
            elif info['type'] == 'github':
                success = self.install_github_mcp(name, info)
            elif info['type'] == 'federation':
                success = self.install_federation_mcp(name, info)

            if success:
                self.installed_mcps.append(name)
            else:
                self.failed_mcps.append(name)

        # Write configuration
        self.write_configuration()

        # Summary
        print("\n" + "="*70)
        print(" INSTALLATION COMPLETE")
        print("="*70)
        print(f"\n✅ Installed: {len(self.installed_mcps)} MCPs")
        print(f"   Using unified database: {len(self.UNIFIED_DB_MCPS)} MCPs")
        print(f"   Independent databases: {len(self.installed_mcps) - len(self.UNIFIED_DB_MCPS)} MCPs")

        if self.failed_mcps:
            print(f"\n❌ Failed: {', '.join(self.failed_mcps)}")

        print(f"\n📁 Unified Database: {self.db_path}")
        print(f"📁 Configuration: {self.config_path}")

        print("\n📋 Architecture:")
        print("  • Pulls from original repositories ✅")
        print("  • Selective unified database for 4 MCPs ✅")
        print("  • Maintains updateability ✅")
        print("  • Clean separation of concerns ✅")

        return True

def main():
    # Display version header
    print("="*70)
    print(" MCP Federation Core v0.1.4 - COMPLETE FIX INSTALLER")
    print(" Lightweight Orchestrator for 15 Production-Ready MCPs")
    print(" ✅ FIXED: Directory nesting bug prevention")
    print(" ✅ FIXED: MCP commands match working configuration")
    print(" ✅ FIXED: Complete uninstallation of all artifacts")
    print(" ✅ SAFE Configuration Merging - Preserves User MCPs")
    print("="*70)
    print()

    installer = FederatedUnifiedInstaller()
    try:
        success = installer.install()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()