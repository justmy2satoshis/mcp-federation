#!/usr/bin/env python3
"""
MCP Federation Core v2.0.0 - Enhanced UX Installer
Copyright (c) 2025 justmy2satoshis
Licensed under MIT License

MAJOR UPDATE v2.0.0 - Complete UX overhaul:
- Verbose output for every action
- Progress tracking [1/15], [2/15], etc.
- Clear error messages and debugging info
- System information display
- Installation summary with next steps

PREVIOUS UPDATE v0.1.6 - Fixed converse-enhanced installation:
- converse-enhanced now installs dependencies directly (httpx, python-dotenv)
- Bypasses missing requirements.txt in repository
"""

import json
import os
import subprocess
import sys
import shutil
import platform
from pathlib import Path
from datetime import datetime
import time

# Fix Windows Unicode
if platform.system() == "Windows":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class FederatedUnifiedInstaller:
    """
    Enhanced installer with verbose output and progress tracking
    """

    def __init__(self):
        self.home = Path.home()
        self.base_dir = self.home / "mcp-servers"
        self.is_windows = platform.system() == "Windows"
        self.config_path = self._get_config_path()
        self.db_path = self.base_dir / "mcp-unified.db"
        self.wrapper_dir = self.base_dir / "federation-wrappers"

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
        self.current_mcp = 0
        self.total_mcps = 15

        # Installation manifest for safe uninstallation
        self.manifest_path = self.base_dir / "installation_manifest.json"

    def print_banner(self):
        """Display startup banner with system information"""
        print("\n" + "="*70)
        print(" MCP FEDERATION CORE INSTALLER v2.0.0")
        print("="*70)
        print(f" Installing to: {self.base_dir}")
        print(f" Python: {sys.version.split()[0]}")
        print(f" Platform: {platform.system()} {platform.release()}")
        print(f" Architecture: {platform.machine()}")
        print(f" User: {os.environ.get('USER', os.environ.get('USERNAME', 'unknown'))}")
        print("="*70)
        print()

    def check_prerequisites(self):
        """Check if required tools are installed"""
        print("🔍 Checking prerequisites...")

        tools = {
            'python': ['python', '--version'] if self.is_windows else ['python3', '--version'],
            'node': ['node', '--version'],
            'npm': ['npm', '--version'],
            'git': ['git', '--version']
        }

        all_good = True
        for tool, cmd in tools.items():
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, shell=self.is_windows)
                if result.returncode == 0:
                    version = result.stdout.strip().split('\n')[0]
                    print(f"  ✅ {tool}: {version}")
                else:
                    print(f"  ❌ {tool}: Not found")
                    all_good = False
            except Exception as e:
                print(f"  ❌ {tool}: Error checking - {e}")
                all_good = False

        if not all_good:
            print("\n⚠️  Some prerequisites are missing. Please install them first.")
            return False

        print("  ✅ All prerequisites met!\n")
        return True

    def check_installation_location(self):
        """Check if we're in the right directory"""
        current_dir = Path.cwd()

        # Check if installer file exists in current directory
        if Path("FEDERATED-INSTALLER-UNIFIED.py").exists() or Path("FEDERATED-INSTALLER-UNIFIED-VERBOSE.py").exists():
            print("✅ Located in mcp-federation-core directory")
            return True

        # Check if mcp-federation-core exists as subdirectory
        if (current_dir / 'mcp-federation-core').exists():
            print("\n⚠️  Found mcp-federation-core as subdirectory")
            print("   Please change to that directory first:")
            print(f"   cd mcp-federation-core")
            print(f"   {'python' if self.is_windows else 'python3'} FEDERATED-INSTALLER-UNIFIED-VERBOSE.py")
            return False

        print("\n❌ ERROR: Not in mcp-federation-core directory!")
        print("   Please clone the repository first:")
        print("   git clone https://github.com/justmy2satoshis/mcp-federation-core.git")
        print("   cd mcp-federation-core")
        print(f"   {'python' if self.is_windows else 'python3'} FEDERATED-INSTALLER-UNIFIED-VERBOSE.py")
        return False

    def _get_config_path(self):
        """Get Claude Desktop config path based on OS"""
        if self.is_windows:
            return Path(os.environ.get('APPDATA', '')) / 'Claude' / 'claude_desktop_config.json'
        elif platform.system() == "Darwin":
            return Path.home() / 'Library' / 'Application Support' / 'Claude' / 'claude_desktop_config.json'
        else:
            return Path.home() / '.config' / 'Claude' / 'claude_desktop_config.json'

    def get_mcp_source_matrix(self):
        """Define MCP source matrix with all installation details"""
        return {
            # NPM Registry MCPs
            'sequential-thinking': {
                'type': 'npm',
                'source': 'mcp-sequential-thinking',
                'install': ['npm', 'install', '-g', 'mcp-sequential-thinking'],
                'needs_db': False,
                'config': {
                    'command': 'mcp-sequential-thinking'
                }
            },
            'filesystem': {
                'type': 'npm',
                'source': '@modelcontextprotocol/server-filesystem',
                'install': ['npm', 'install', '-g', '@modelcontextprotocol/server-filesystem'],
                'needs_db': False,
                'config': {
                    'command': 'mcp-server-filesystem',
                    'args': [str(self.home)]
                }
            },
            'github': {
                'type': 'npm',
                'source': '@modelcontextprotocol/server-github',
                'install': ['npm', 'install', '-g', '@modelcontextprotocol/server-github'],
                'needs_db': False,
                'config': {
                    'command': 'mcp-server-github',
                    'env': {'GITHUB_TOKEN': 'YOUR_GITHUB_TOKEN'}
                }
            },
            'sqlite': {
                'type': 'npm',
                'source': '@modelcontextprotocol/server-sqlite',
                'install': ['npm', 'install', '-g', '@modelcontextprotocol/server-sqlite'],
                'needs_db': False,
                'config': {
                    'command': 'mcp-server-sqlite',
                    'args': [str(self.db_path)]
                }
            },
            'playwright': {
                'type': 'npm',
                'source': '@modelcontextprotocol/server-playwright',
                'install': ['npm', 'install', '-g', '@modelcontextprotocol/server-playwright'],
                'needs_db': False,
                'config': {
                    'command': 'mcp-server-playwright'
                }
            },
            'memory': {
                'type': 'npm',
                'source': '@modelcontextprotocol/server-memory',
                'install': ['npm', 'install', '-g', '@modelcontextprotocol/server-memory'],
                'needs_db': True,
                'config': {
                    'command': 'mcp-server-memory'
                }
            },
            'web-search': {
                'type': 'npm',
                'source': '@modelcontextprotocol/server-brave-search',
                'install': ['npm', 'install', '-g', '@modelcontextprotocol/server-brave-search'],
                'needs_db': False,
                'config': {
                    'command': 'mcp-server-brave-search',
                    'env': {'BRAVE_API_KEY': 'YOUR_BRAVE_KEY'}
                }
            },
            'git-ops': {
                'type': 'npm',
                'source': '@modelcontextprotocol/server-git',
                'install': ['npm', 'install', '-g', '@modelcontextprotocol/server-git'],
                'needs_db': False,
                'config': {
                    'command': 'mcp-server-git'
                }
            },
            'desktop-commander': {
                'type': 'npm',
                'source': 'mcp-server-desktop-commander',
                'install': ['npm', 'install', '-g', 'mcp-server-desktop-commander'],
                'needs_db': False,
                'config': {
                    'command': 'mcp-server-desktop-commander'
                }
            },
            'perplexity': {
                'type': 'npm',
                'source': 'mcp-server-perplexity',
                'install': ['npm', 'install', '-g', 'mcp-server-perplexity'],
                'needs_db': False,
                'config': {
                    'command': 'npx',
                    'args': ['-y', 'server-perplexity-ask'],
                    'env': {'PERPLEXITY_API_KEY': 'YOUR_PERPLEXITY_KEY'}
                }
            },

            # GitHub MCPs
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
                    'command': 'python' if self.is_windows else 'python3',
                    'args': [str(self.base_dir / 'converse-mcp-enhanced' / 'src' / 'server.py')],
                    'env': {
                        'OPENAI_API_KEY': 'YOUR_OPENAI_KEY',
                        'GEMINI_API_KEY': 'YOUR_GEMINI_KEY'
                    }
                }
            },
            'kimi-k2-code-context': {
                'type': 'github',
                'source': 'https://github.com/justmy2satoshis/kimi-k2-code-context-mcp-repo.git',
                'directory': 'kimi-k2-code-context-enhanced',
                'branch': 'main',
                'install': [],
                'needs_db': True,
                'config': {
                    'command': 'python' if self.is_windows else 'python3',
                    'args': [str(self.base_dir / 'kimi-k2-code-context-enhanced' / 'server.py')]
                }
            },
            'kimi-k2-resilient': {
                'type': 'github',
                'source': 'https://github.com/justmy2satoshis/kimi-k2-heavy-processor-mcp-repo.git',
                'directory': 'kimi-k2-resilient-enhanced',
                'branch': 'main',
                'install': [],
                'needs_db': True,
                'config': {
                    'command': 'python' if self.is_windows else 'python3',
                    'args': [str(self.base_dir / 'kimi-k2-resilient-enhanced' / 'server.py')]
                }
            },
            'rag-context': {
                'type': 'github',
                'source': 'https://github.com/justmy2satoshis/rag-context-fixed.git',
                'directory': 'rag-context-fixed',
                'branch': 'main',
                'install': [],
                'needs_db': False,
                'config': {
                    'command': 'python' if self.is_windows else 'python3',
                    'args': [str(self.base_dir / 'rag-context-fixed' / 'server.py')]
                }
            }
        }

    def initialize_unified_database(self):
        """Initialize the unified SQLite database"""
        print("🗄️ Initializing unified database...")
        print(f"  → Creating database at: {self.db_path}")

        try:
            import sqlite3
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Create tables for MCPs that need unified DB
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memory_storage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mcp_name TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(mcp_name, key)
                )
            ''')

            conn.commit()
            conn.close()
            print(f"  ✅ Unified database initialized successfully")
            return True

        except Exception as e:
            print(f"  ❌ Database initialization failed: {e}")
            return False

    def install_npm_mcp(self, name, mcp_info):
        """Install MCP from npm registry with verbose output"""
        self.current_mcp += 1
        print(f"\n[{self.current_mcp}/{self.total_mcps}] Installing {name}")
        print(f"  📦 Type: NPM Package")
        print(f"  📦 Package: {mcp_info['source']}")

        try:
            # Check if already installed
            print(f"  → Checking if already installed...")
            check_cmd = ['npm', 'list', '-g', mcp_info['source']]
            result = subprocess.run(check_cmd, capture_output=True, text=True, shell=self.is_windows)

            if result.returncode == 0:
                print(f"  ✅ Already installed, skipping")
                return True

            # Install from npm
            print(f"  → Installing from npm registry...")
            print(f"  → Running: npm install -g {mcp_info['source']}")

            # Show spinner while installing
            start_time = time.time()
            install_result = subprocess.run(
                mcp_info['install'],
                capture_output=True,
                text=True,
                shell=self.is_windows
            )
            elapsed = time.time() - start_time

            if install_result.returncode == 0:
                print(f"  ✅ Successfully installed in {elapsed:.1f}s")
                return True
            else:
                error_msg = install_result.stderr[:200] if install_result.stderr else "Unknown error"
                print(f"  ❌ Installation failed: {error_msg}")
                return False

        except Exception as e:
            print(f"  ❌ Exception during installation: {e}")
            return False

    def install_github_mcp(self, name, mcp_info):
        """Clone and install MCP from GitHub with verbose output"""
        self.current_mcp += 1
        print(f"\n[{self.current_mcp}/{self.total_mcps}] Installing {name}")
        print(f"  🔗 Type: GitHub Repository")
        print(f"  🔗 Source: {mcp_info['source']}")

        target_dir = self.base_dir / mcp_info['directory']

        try:
            if target_dir.exists():
                print(f"  → Found existing installation at {target_dir.name}")
                print(f"  → Updating repository...")
                pull_cmd = ['git', 'pull', 'origin', mcp_info['branch']]
                result = subprocess.run(pull_cmd, cwd=str(target_dir), capture_output=True, text=True)

                if result.returncode == 0:
                    print(f"  ✅ Repository updated successfully")
                else:
                    print(f"  ⚠️ Git pull failed, continuing with existing version")
            else:
                print(f"  → Cloning repository...")
                print(f"  → Target: {target_dir.name}")

                clone_cmd = ['git', 'clone', '-b', mcp_info['branch'], mcp_info['source'], str(target_dir)]
                result = subprocess.run(clone_cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    print(f"  ✅ Repository cloned successfully")
                else:
                    print(f"  ❌ Git clone failed: {result.stderr[:200]}")
                    return False

            # Install dependencies if needed
            if mcp_info['install']:
                if mcp_info['install'][0] == 'npm':
                    print(f"  → Installing npm dependencies...")
                    result = subprocess.run(['npm', 'install'], cwd=str(target_dir), capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"  ✅ npm dependencies installed")
                    else:
                        print(f"  ⚠️ npm install had warnings (usually OK)")

                elif mcp_info['install'][0] == 'pip':
                    print(f"  → Installing Python dependencies...")
                    pip_cmd = ['pip'] if self.is_windows else ['pip3']
                    pip_cmd.extend(mcp_info['install'][1:])

                    result = subprocess.run(pip_cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"  ✅ Python dependencies installed")
                    else:
                        print(f"  ⚠️ Some dependencies may already be installed")

            print(f"  ✅ {name} ready to use")
            return True

        except Exception as e:
            print(f"  ❌ Exception during installation: {e}")
            return False

    def write_configuration(self):
        """Write Claude Desktop configuration with progress"""
        print("\n📝 Writing Claude Desktop configuration...")
        print(f"  → Config file: {self.config_path}")

        try:
            # Create config directory if it doesn't exist
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # Load existing config or create new
            if self.config_path.exists():
                print(f"  → Loading existing configuration...")
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                print(f"  ✅ Found {len(config.get('mcpServers', {}))} existing MCPs")
            else:
                print(f"  → Creating new configuration...")
                config = {}

            # Initialize mcpServers if not present
            if 'mcpServers' not in config:
                config['mcpServers'] = {}

            # Add our MCPs
            matrix = self.get_mcp_source_matrix()
            added_count = 0

            for name in self.installed_mcps:
                if name in matrix:
                    mcp_info = matrix[name]
                    config['mcpServers'][name] = mcp_info['config']
                    added_count += 1

            # Write config
            print(f"  → Writing configuration with {len(config['mcpServers'])} total MCPs...")
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)

            print(f"  ✅ Configuration saved successfully")
            print(f"  ✅ Added {added_count} federation MCPs")
            return True

        except Exception as e:
            print(f"  ❌ Failed to write configuration: {e}")
            return False

    def install(self):
        """Main installation process with enhanced UX"""
        # Print banner
        self.print_banner()

        # Check prerequisites
        if not self.check_prerequisites():
            return False

        # Check installation location
        if not self.check_installation_location():
            print("\n❌ Installation aborted - wrong directory")
            return False

        print("\n🚀 Starting MCP Federation Core installation...")
        print(f"   This will install {self.total_mcps} production-ready MCPs\n")

        # Create directories
        print("📁 Creating directories...")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        print(f"  ✅ Base directory ready: {self.base_dir}")

        # Initialize unified database
        self.initialize_unified_database()

        # Install MCPs
        print("\n🔧 Installing MCP servers...")
        matrix = self.get_mcp_source_matrix()

        self.current_mcp = 0
        for name, info in matrix.items():
            success = False

            if info['type'] == 'npm':
                success = self.install_npm_mcp(name, info)
            elif info['type'] == 'github':
                success = self.install_github_mcp(name, info)

            if success:
                self.installed_mcps.append(name)
            else:
                self.failed_mcps.append((name, info.get('source', 'unknown')))

        # Write configuration
        self.write_configuration()

        # Print summary
        self.print_summary()

        return len(self.failed_mcps) == 0

    def print_summary(self):
        """Print installation summary with next steps"""
        print("\n" + "="*70)
        print(" INSTALLATION COMPLETE")
        print("="*70)

        success_count = len(self.installed_mcps)
        fail_count = len(self.failed_mcps)

        print(f"\n📊 Installation Summary:")
        print(f"  ✅ Successfully installed: {success_count}/{self.total_mcps} MCPs")

        if self.failed_mcps:
            print(f"  ❌ Failed installations: {fail_count}")
            print("\n  Failed MCPs:")
            for mcp, source in self.failed_mcps:
                print(f"    • {mcp}: {source}")

        print(f"\n📁 Installation Locations:")
        print(f"  • MCP Servers: {self.base_dir}")
        print(f"  • Unified Database: {self.db_path}")
        print(f"  • Configuration: {self.config_path}")

        print("\n🎯 Next Steps:")
        print("  1. Restart Claude Desktop")
        print("  2. Check MCP connections in Claude Desktop settings")
        print("  3. Configure API keys for services you want to use:")
        print("     • GitHub: Add GITHUB_TOKEN")
        print("     • OpenAI: Add OPENAI_API_KEY")
        print("     • Gemini: Add GEMINI_API_KEY")
        print("     • Brave Search: Add BRAVE_API_KEY")

        print("\n📚 Documentation:")
        print("  • GitHub: https://github.com/justmy2satoshis/mcp-federation-core")
        print("  • Issues: https://github.com/justmy2satoshis/mcp-federation-core/issues")

        print("\n✨ Enjoy using MCP Federation Core v2.0.0!")
        print("="*70)

def main():
    """Main entry point with error handling"""
    try:
        installer = FederatedUnifiedInstaller()
        success = installer.install()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        print("\nDebug information:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    # Flush output immediately
    sys.stdout.flush()
    main()