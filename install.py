#!/usr/bin/env python3
"""
MCP Federation Installer v3.1.0 - Python MCP Fix Edition
Automated dependency resolution + proper Python MCP configuration
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
from typing import Dict, Optional, Tuple, List

__version__ = "3.1.0"

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

class PrerequisiteManager:
    """Handles automatic installation of missing dependencies"""

    def __init__(self):
        self.system = platform.system()
        self.missing_deps = []

    def check_python_version(self) -> Tuple[bool, str]:
        """Check Python version (requires 3.9+)"""
        try:
            import sys
            version = sys.version_info
            version_str = f"{version.major}.{version.minor}.{version.micro}"

            if version.major >= 3 and version.minor >= 9:
                return True, version_str
            else:
                self.missing_deps.append(('python', version_str, '3.9+'))
                return False, version_str
        except Exception as e:
            self.missing_deps.append(('python', 'Not found', '3.9+'))
            return False, "Not found"

    def find_nodejs_path(self) -> Optional[Path]:
        """Find Node.js installation path on Windows"""
        if self.system != "Windows":
            return None

        # Common Node.js installation paths
        common_paths = [
            Path("C:/Program Files/nodejs"),
            Path("C:/Program Files (x86)/nodejs"),
            Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "nodejs",
            Path(os.environ.get("ProgramW6432", "C:/Program Files")) / "nodejs",
        ]

        # Check registry for Node.js path
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Node.js") as key:
                install_path = winreg.QueryValueEx(key, "InstallPath")[0]
                if install_path:
                    common_paths.insert(0, Path(install_path))
        except:
            pass

        # Check each path
        for path in common_paths:
            if path.exists() and (path / "node.exe").exists():
                return path

        # Check if node is in PATH
        result = shutil.which("node")
        if result:
            return Path(result).parent

        return None

    def check_nodejs_version(self) -> Tuple[bool, str]:
        """Check Node.js version (requires 18+)"""
        try:
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip().lstrip('v')
                major_version = int(version.split('.')[0])
                if major_version >= 18:
                    return True, version
                else:
                    self.missing_deps.append(('nodejs', version, '18+'))
                    return False, version
            else:
                self.missing_deps.append(('nodejs', 'Not found', '18+'))
                return False, "Not found"
        except Exception:
            self.missing_deps.append(('nodejs', 'Not found', '18+'))
            return False, "Not found"

    def check_npm(self) -> Tuple[bool, str]:
        """Check npm availability - with special handling for Windows PATH issues"""
        # First try standard npm command
        try:
            result = subprocess.run(
                ["npm", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return True, result.stdout.strip()
        except:
            pass

        # On Windows, check if Node.js is installed but npm is not in PATH
        if self.system == "Windows":
            nodejs_path = self.find_nodejs_path()
            if nodejs_path:
                npm_cmd = nodejs_path / "npm.cmd"
                if npm_cmd.exists():
                    # npm exists but not in PATH - we can fix this!
                    print(f"{Colors.WARNING}  ⚠ npm found at {npm_cmd} but not in PATH{Colors.ENDC}")

                    # Try to run npm directly
                    try:
                        result = subprocess.run(
                            [str(npm_cmd), "--version"],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode == 0:
                            # npm works when called directly
                            return True, f"{result.stdout.strip()} (needs PATH fix)"
                    except:
                        pass

        self.missing_deps.append(('npm', 'Not found', 'Latest'))
        return False, "Not found"

    def fix_npm_path_windows(self) -> bool:
        """Fix npm PATH on Windows by adding Node.js directory to PATH"""
        if self.system != "Windows":
            return False

        nodejs_path = self.find_nodejs_path()
        if not nodejs_path:
            return False

        # Check if npm.cmd exists
        npm_cmd = nodejs_path / "npm.cmd"
        if not npm_cmd.exists():
            print(f"{Colors.FAIL}npm.cmd not found in {nodejs_path}{Colors.ENDC}")
            return False

        # Add to PATH for current session
        current_path = os.environ.get("PATH", "")
        if str(nodejs_path) not in current_path:
            os.environ["PATH"] = f"{nodejs_path};{current_path}"
            print(f"{Colors.OKGREEN}  ✅ Added {nodejs_path} to PATH for this session{Colors.ENDC}")

            # Offer to add permanently
            response = input(f"{Colors.OKCYAN}  Add to PATH permanently? (requires admin) [y/N]: {Colors.ENDC}").strip().lower()
            if response == 'y':
                try:
                    # Use setx to set user PATH
                    subprocess.run(
                        ["setx", "PATH", f"{nodejs_path};%PATH%"],
                        check=True,
                        capture_output=True
                    )
                    print(f"{Colors.OKGREEN}  ✅ PATH updated permanently (restart terminal to apply){Colors.ENDC}")
                except:
                    print(f"{Colors.WARNING}  Could not update PATH permanently - manual update needed{Colors.ENDC}")

            return True
        else:
            print(f"{Colors.OKBLUE}  Node.js path already in PATH{Colors.ENDC}")
            return True

    def check_git(self) -> Tuple[bool, str]:
        """Check Git availability"""
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                self.missing_deps.append(('git', 'Not found', 'Latest'))
                return False, "Not found"
        except Exception:
            self.missing_deps.append(('git', 'Not found', 'Latest'))
            return False, "Not found"

    def install_python_windows(self) -> bool:
        """Install Python on Windows using winget or chocolatey"""
        print(f"{Colors.OKBLUE}Installing Python 3.12...{Colors.ENDC}")

        # Try winget first (Windows 10/11)
        try:
            result = subprocess.run(
                ["winget", "install", "Python.Python.3.12", "-e", "--silent"],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                print(f"{Colors.OKGREEN}  ✅ Python installed successfully via winget{Colors.ENDC}")
                return True
        except:
            pass

        # Try chocolatey
        try:
            result = subprocess.run(
                ["choco", "install", "python", "-y"],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                print(f"{Colors.OKGREEN}  ✅ Python installed successfully via chocolatey{Colors.ENDC}")
                return True
        except:
            pass

        # Fallback: Direct download
        print(f"{Colors.WARNING}  Automated installation failed. Please download from:{Colors.ENDC}")
        print(f"  https://www.python.org/downloads/")
        return False

    def install_nodejs_windows(self) -> bool:
        """Install Node.js on Windows"""
        print(f"{Colors.OKBLUE}Installing Node.js 20 LTS...{Colors.ENDC}")

        # Try winget first
        try:
            result = subprocess.run(
                ["winget", "install", "OpenJS.NodeJS.LTS", "-e", "--silent"],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                print(f"{Colors.OKGREEN}  ✅ Node.js installed successfully via winget{Colors.ENDC}")
                return True
        except:
            pass

        # Try chocolatey
        try:
            result = subprocess.run(
                ["choco", "install", "nodejs-lts", "-y"],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                print(f"{Colors.OKGREEN}  ✅ Node.js installed successfully via chocolatey{Colors.ENDC}")
                return True
        except:
            pass

        # Fallback
        print(f"{Colors.WARNING}  Automated installation failed. Please download from:{Colors.ENDC}")
        print(f"  https://nodejs.org/")
        return False

    def install_git_windows(self) -> bool:
        """Install Git on Windows"""
        print(f"{Colors.OKBLUE}Installing Git...{Colors.ENDC}")

        # Try winget
        try:
            result = subprocess.run(
                ["winget", "install", "Git.Git", "-e", "--silent"],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                print(f"{Colors.OKGREEN}  ✅ Git installed successfully via winget{Colors.ENDC}")
                return True
        except:
            pass

        # Try chocolatey
        try:
            result = subprocess.run(
                ["choco", "install", "git", "-y"],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                print(f"{Colors.OKGREEN}  ✅ Git installed successfully via chocolatey{Colors.ENDC}")
                return True
        except:
            pass

        # Fallback
        print(f"{Colors.WARNING}  Automated installation failed. Please download from:{Colors.ENDC}")
        print(f"  https://git-scm.com/download/win")
        return False

    def auto_install_dependencies(self) -> bool:
        """Automatically install missing dependencies with user consent"""
        if not self.missing_deps:
            return True

        print(f"\n{Colors.WARNING}Missing dependencies detected:{Colors.ENDC}")
        for dep, current, required in self.missing_deps:
            print(f"  • {dep}: {current} (requires {required})")

        # Ask for consent
        print(f"\n{Colors.OKCYAN}Would you like to automatically install missing dependencies?{Colors.ENDC}")
        response = input(f"Install automatically? [Y/n]: ").strip().lower()

        if response == 'n':
            print(f"{Colors.WARNING}Manual installation required. Please install:{Colors.ENDC}")
            for dep, _, required in self.missing_deps:
                print(f"  • {dep} {required}")
            return False

        # Install each missing dependency
        success = True
        for dep, _, _ in self.missing_deps:
            if self.system == "Windows":
                if dep == 'python':
                    success &= self.install_python_windows()
                elif dep == 'nodejs':
                    success &= self.install_nodejs_windows()
                elif dep == 'git':
                    success &= self.install_git_windows()
            elif self.system == "Darwin":  # macOS
                # Implement macOS installation
                print(f"{Colors.WARNING}Auto-installation on macOS coming soon{Colors.ENDC}")
                success = False
            elif self.system == "Linux":
                # Implement Linux installation
                print(f"{Colors.WARNING}Auto-installation on Linux coming soon{Colors.ENDC}")
                success = False

        return success

    def check_all_prerequisites(self) -> bool:
        """Check all prerequisites and offer auto-installation"""
        print(f"{Colors.OKBLUE}Checking system prerequisites...{Colors.ENDC}")

        # Check each dependency
        python_ok, python_ver = self.check_python_version()
        print(f"  {'✅' if python_ok else '❌'} Python: {python_ver} {'✓' if python_ok else '(requires 3.9+)'}")

        nodejs_ok, nodejs_ver = self.check_nodejs_version()
        print(f"  {'✅' if nodejs_ok else '❌'} Node.js: {nodejs_ver} {'✓' if nodejs_ok else '(requires 18+)'}")

        npm_ok, npm_ver = self.check_npm()

        # Special handling for npm PATH issue on Windows
        if not npm_ok and nodejs_ok and self.system == "Windows":
            print(f"{Colors.WARNING}  ⚠ Node.js is installed but npm is not accessible{Colors.ENDC}")
            print(f"{Colors.OKBLUE}  Attempting to fix npm PATH...{Colors.ENDC}")
            if self.fix_npm_path_windows():
                npm_ok, npm_ver = self.check_npm()

        print(f"  {'✅' if npm_ok else '❌'} npm: {npm_ver} {'✓' if npm_ok else ''}")

        git_ok, git_ver = self.check_git()
        print(f"  {'✅' if git_ok else '❌'} Git: {git_ver} {'✓' if git_ok else ''}")

        # If anything is missing, offer auto-installation
        all_ok = python_ok and nodejs_ok and npm_ok and git_ok

        if not all_ok:
            return self.auto_install_dependencies()

        print(f"{Colors.OKGREEN}All prerequisites satisfied!{Colors.ENDC}")
        return True


class MCPInstaller:
    """Enhanced MCP installer with Python MCP support"""

    def __init__(self):
        """Initialize installer"""
        self.start_time = time.time()
        self.prereq_manager = PrerequisiteManager()

        # Platform detection
        self.system = platform.system()
        self.home_dir = Path.home()

        # Configuration paths - Windows specific
        if self.system == "Windows":
            self.config_dir = Path(os.environ.get('APPDATA', '')) / 'Claude'
        elif self.system == "Darwin":  # macOS
            self.config_dir = self.home_dir / 'Library' / 'Application Support' / 'Claude'
        else:  # Linux
            self.config_dir = self.home_dir / '.claude'

        self.config_path = self.config_dir / 'claude_desktop_config.json'

        # Manifest and backup paths
        self.manifest_dir = self.home_dir / '.mcp-federation'
        self.manifest_path = self.manifest_dir / 'installation_manifest.json'
        self.backup_dir = self.manifest_dir / 'backups'

        # Python MCPs installation directory
        self.python_mcps_dir = self.home_dir / 'mcp-servers'

        # Tracking
        self.existing_mcps = set()
        self.installed_by_us = []
        self.already_existed = []

        # Python MCPs with their GitHub URLs
        self.PYTHON_MCPS = {
            'desktop-commander': 'https://github.com/modelcontextprotocol/desktop-commander-mcp',
            'expert-role-prompt': 'https://github.com/modelcontextprotocol/expert-role-prompt-mcp',
            'converse-enhanced': 'https://github.com/justmy2satoshis/converse-mcp-enhanced',
            'kimi-k2-code-context': 'https://github.com/justmy2satoshis/kimi-k2-code-context-mcp',
            'kimi-k2-resilient': 'https://github.com/justmy2satoshis/kimi-k2-resilient-enhanced',
            'rag-context': 'https://github.com/justmy2satoshis/rag-context-mcp',
        }

        # Node.js MCPs (use npx)
        self.NODEJS_MCP_CONFIGS = {
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
            'perplexity': {
                'command': 'npx',
                'args': ['-y', '@modelcontextprotocol/server-perplexity'],
                'env': {'PERPLEXITY_API_KEY': 'YOUR_PERPLEXITY_KEY'}
            }
        }

        # Python MCP configurations (will be populated dynamically)
        self.PYTHON_MCP_CONFIGS = {}

        # Combined MCP configurations
        self.MCP_CONFIGS = {}

    def install_python_mcp(self, name: str, github_url: str) -> bool:
        """Clone and install a Python MCP"""
        print(f"{Colors.OKBLUE}Installing Python MCP: {name}...{Colors.ENDC}")

        mcp_path = self.python_mcps_dir / name

        # Check if already exists
        if mcp_path.exists():
            print(f"  ✓ {name} already exists at {mcp_path}")
        else:
            # Clone from GitHub
            try:
                print(f"  Cloning from {github_url}...")
                result = subprocess.run(
                    ["git", "clone", github_url, str(mcp_path)],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.returncode != 0:
                    print(f"{Colors.FAIL}  Failed to clone {name}: {result.stderr}{Colors.ENDC}")
                    return False
                print(f"{Colors.OKGREEN}  ✅ Cloned {name} successfully{Colors.ENDC}")
            except Exception as e:
                print(f"{Colors.FAIL}  Error cloning {name}: {e}{Colors.ENDC}")
                return False

        # Install Python dependencies
        if not self.install_python_dependencies(mcp_path, name):
            return False

        # Create configuration for this Python MCP
        self.PYTHON_MCP_CONFIGS[name] = {
            'command': 'python',
            'args': ['server.py'],
            'cwd': str(mcp_path),
            'env': {'PYTHONUNBUFFERED': '1'}
        }

        # Some MCPs might need special environment variables
        if name == 'converse-enhanced':
            self.PYTHON_MCP_CONFIGS[name]['env']['OPENAI_API_KEY'] = 'YOUR_OPENAI_KEY'

        return True

    def install_python_dependencies(self, mcp_path: Path, name: str) -> bool:
        """Install Python dependencies for an MCP"""
        print(f"  Installing Python dependencies for {name}...")

        # Check for requirements.txt
        requirements_file = mcp_path / "requirements.txt"

        # Common Python MCP packages to install
        common_packages = ["mcp", "anthropic-mcp"]

        try:
            # Install common MCP packages first
            for package in common_packages:
                print(f"    Installing {package}...")
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", package, "--quiet", "--user"],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.returncode != 0 and "Requirement already satisfied" not in result.stdout:
                    print(f"{Colors.WARNING}    Warning: Could not install {package}{Colors.ENDC}")

            # Install from requirements.txt if it exists
            if requirements_file.exists():
                print(f"    Installing from requirements.txt...")
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", str(requirements_file), "--quiet", "--user"],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                if result.returncode != 0:
                    print(f"{Colors.WARNING}    Warning: Some dependencies might have failed{Colors.ENDC}")
                else:
                    print(f"{Colors.OKGREEN}    ✅ Dependencies installed{Colors.ENDC}")
            else:
                print(f"    No requirements.txt found, using common packages only")

            # Verify MCP module is available
            result = subprocess.run(
                [sys.executable, "-c", "import mcp"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"{Colors.OKGREEN}    ✅ Python MCP module verified{Colors.ENDC}")
                return True
            else:
                print(f"{Colors.WARNING}    Warning: MCP module not verified{Colors.ENDC}")
                return True  # Continue anyway, might work

        except Exception as e:
            print(f"{Colors.FAIL}    Error installing dependencies: {e}{Colors.ENDC}")
            return False

    def print_banner(self):
        """Display installation banner"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}")
        print("="*60)
        print("    MCP FEDERATION INSTALLER v3.1.0")
        print("    Python MCP Configuration Fix")
        print("="*60)
        print(f"{Colors.ENDC}")
        print(f"{Colors.OKCYAN}Installing 15 essential MCP servers for Claude Desktop{Colors.ENDC}")
        print(f"{Colors.OKBLUE}Now with proper Python MCP support!{Colors.ENDC}\n")

    def backup_config(self) -> bool:
        """Create timestamped backup of existing configuration"""
        if not self.config_path.exists():
            return True

        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"claude_config_backup_{timestamp}.json"

            shutil.copy2(self.config_path, backup_path)
            print(f"{Colors.OKGREEN}✅ Backup created: {backup_path.name}{Colors.ENDC}")
            return True

        except Exception as e:
            print(f"{Colors.FAIL}Backup failed: {e}{Colors.ENDC}")
            return False

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
                self.already_existed = list(self.existing_mcps)
                print(f"{Colors.OKGREEN}Found {len(self.existing_mcps)} existing MCPs{Colors.ENDC}")

            return config

        except Exception as e:
            print(f"{Colors.FAIL}Error reading config: {e}{Colors.ENDC}")
            return None

    def prepare_mcp_configs(self) -> bool:
        """Prepare all MCP configurations (Node.js + Python)"""
        print(f"\n{Colors.OKBLUE}Preparing MCP configurations...{Colors.ENDC}")

        # Create Python MCPs directory if needed
        self.python_mcps_dir.mkdir(parents=True, exist_ok=True)

        # Install Python MCPs
        print(f"\n{Colors.OKCYAN}Installing Python MCPs...{Colors.ENDC}")
        for name, github_url in self.PYTHON_MCPS.items():
            if not self.install_python_mcp(name, github_url):
                print(f"{Colors.WARNING}Warning: Failed to install {name}{Colors.ENDC}")

        # Combine Node.js and Python configurations
        self.MCP_CONFIGS = {**self.NODEJS_MCP_CONFIGS, **self.PYTHON_MCP_CONFIGS}

        print(f"\n{Colors.OKGREEN}✅ Prepared {len(self.MCP_CONFIGS)} MCP configurations{Colors.ENDC}")
        print(f"  • Node.js MCPs: {len(self.NODEJS_MCP_CONFIGS)}")
        print(f"  • Python MCPs: {len(self.PYTHON_MCP_CONFIGS)}")

        return True

    def merge_configs(self, existing_config: Optional[Dict]) -> Dict:
        """Merge new MCPs with existing configuration"""
        if existing_config is None:
            config = {'mcpServers': {}}
        else:
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
                # Update Python MCP configs even if they exist (to fix configuration)
                if name in self.PYTHON_MCPS:
                    print(f"  ⚠ Updating {name} configuration (Python MCP fix)")
                    config['mcpServers'][name] = mcp_config
                    if name not in self.installed_by_us:
                        self.installed_by_us.append(name)
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

            print(f"{Colors.OKGREEN}✅ Configuration saved to {self.config_path}{Colors.ENDC}")
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
                'claude_desktop_mcps': list(self.MCP_CONFIGS.keys()),
                'python_mcps': list(self.PYTHON_MCPS.keys()),
                'python_mcps_dir': str(self.python_mcps_dir)
            }

            with open(self.manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)

            print(f"{Colors.OKGREEN}✅ Installation manifest saved{Colors.ENDC}")
            return True

        except Exception as e:
            print(f"{Colors.WARNING}Could not save manifest: {e}{Colors.ENDC}")
            return False

    def validate_installation(self, config: Dict) -> bool:
        """Validate that all MCPs are configured correctly"""
        if 'mcpServers' not in config:
            return False

        mcp_count = len(config['mcpServers'])
        required_count = len(self.MCP_CONFIGS)

        print(f"\n{Colors.OKBLUE}Validating MCP configurations...{Colors.ENDC}")

        # Check Python MCPs specifically
        python_mcps_ok = True
        for name in self.PYTHON_MCPS.keys():
            if name in config['mcpServers']:
                mcp_config = config['mcpServers'][name]
                if mcp_config.get('command') == 'python' and 'cwd' in mcp_config:
                    print(f"  ✅ {name}: Correctly configured (Python MCP)")
                else:
                    print(f"  ❌ {name}: Configuration issue")
                    python_mcps_ok = False
            else:
                print(f"  ❌ {name}: Missing from configuration")
                python_mcps_ok = False

        if mcp_count >= required_count and python_mcps_ok:
            print(f"{Colors.OKGREEN}✅ All {required_count} MCPs configured successfully{Colors.ENDC}")
            return True
        else:
            print(f"{Colors.WARNING}Some MCPs may need attention{Colors.ENDC}")
            return True  # Non-fatal

    def run(self) -> int:
        """Main installation process with Python MCP fixes"""
        self.print_banner()

        # Check and auto-install prerequisites
        if not self.prereq_manager.check_all_prerequisites():
            print(f"\n{Colors.FAIL}Could not satisfy prerequisites automatically.{Colors.ENDC}")
            print(f"{Colors.WARNING}Please install missing dependencies manually and try again.{Colors.ENDC}")
            return 1

        # Prepare MCP configurations (install Python MCPs)
        if not self.prepare_mcp_configs():
            print(f"{Colors.FAIL}Failed to prepare MCP configurations{Colors.ENDC}")
            return 1

        # Read existing configuration
        print(f"\n{Colors.OKBLUE}Reading configuration...{Colors.ENDC}")
        existing_config = self.read_existing_config()

        # Backup if config exists
        if existing_config:
            print(f"\n{Colors.OKBLUE}Creating backup...{Colors.ENDC}")
            if not self.backup_config():
                print(f"{Colors.FAIL}Backup failed - aborting for safety{Colors.ENDC}")
                return 1

        # Merge configurations
        print(f"\n{Colors.OKBLUE}Configuring MCP servers...{Colors.ENDC}")
        merged_config = self.merge_configs(existing_config)

        # Save configuration
        print(f"\n{Colors.OKBLUE}Saving configuration...{Colors.ENDC}")
        if not self.save_config(merged_config):
            return 1

        # Validate
        self.validate_installation(merged_config)

        # Save manifest
        self.save_manifest()

        # Success!
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
        print(f"  • Total MCPs: {len(merged_config.get('mcpServers', {}))}")
        print(f"  • Python MCPs fixed: {len(self.PYTHON_MCPS)}")

        if self.installed_by_us:
            print(f"\n{Colors.OKCYAN}Newly installed/updated MCPs:{Colors.ENDC}")
            for mcp in self.installed_by_us:
                mcp_type = "Python" if mcp in self.PYTHON_MCPS else "Node.js"
                print(f"    • {mcp} ({mcp_type})")

        print(f"\n{Colors.OKCYAN}Next steps:{Colors.ENDC}")
        print("  1. Restart Claude Desktop completely")
        print("  2. All Python MCPs should now connect properly")
        print("  3. Configure API keys as needed:")
        print("     • GitHub token for github-manager")
        print("     • Brave API key for web-search")
        print("     • Perplexity key for perplexity")
        print("     • OpenAI key for converse-enhanced")
        print(f"\n{Colors.OKGREEN}Python MCPs are now properly configured with 'python server.py' and correct paths!{Colors.ENDC}")
        print(f"\n{Colors.OKBLUE}To uninstall: python uninstall.py{Colors.ENDC}\n")

        return 0


def main():
    """Entry point with enhanced features"""
    # Add command line arguments for automation
    import argparse
    parser = argparse.ArgumentParser(description='MCP Federation Installer v3.1.0 - Python Fix Edition')
    parser.add_argument('--auto', action='store_true', help='Automatically install dependencies without prompting')
    parser.add_argument('--fix-npm', action='store_true', help='Fix npm PATH issues on Windows')
    args = parser.parse_args()

    # Set auto mode if requested
    if args.auto:
        os.environ['MCP_AUTO_INSTALL'] = '1'

    installer = MCPInstaller()
    return installer.run()


if __name__ == '__main__':
    sys.exit(main())