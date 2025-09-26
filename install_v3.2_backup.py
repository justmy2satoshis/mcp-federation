#!/usr/bin/env python3
"""
MCP Federation Installer v3.2.1 - Windows npm.cmd Fix
Fixes Windows npm execution with proper command resolution
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

__version__ = "3.2.1"

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

# CORRECT MCP Classifications - v3.2.0
# These are verified and mirror the working development device exactly# NPX-based MCPs - Run directly with npx
MCP_NPX_PACKAGES = {
    "sequential-thinking": "@modelcontextprotocol/server-sequential-thinking",
    "github": "@modelcontextprotocol/server-github",
    "sqlite": "@modelcontextprotocol/server-sqlite",
    "playwright": "@modelcontextprotocol/server-playwright", 
    "git-ops": "@joshuakarp/mcp-git-ingest",
    "desktop-commander": "@desktopcommanderai/mcp-server-desktop-commander",
    "perplexity": "mcp-server-perplexity"
}

# NPM-based MCPs - Need npm install first
MCP_NPM_PACKAGES = {
    "filesystem": "@modelcontextprotocol/server-filesystem",
    "memory": "@modelcontextprotocol/server-memory",
    "web-search": "@modelcontextprotocol/server-brave-search",
    "expert-role-prompt": "mcp-expert-role-prompt"
}

# Python-based MCPs - Need git clone and Python setup
MCP_PYTHON_REPOS = {
    "converse-enhanced": {
        "repo": "https://github.com/justmy2satoshis/converse-mcp-enhanced",
        "command": "python",
        "args": ["server.py"]
    },
    "kimi-k2-code-context": {
        "repo": "https://github.com/zhaoyinglia/kimi-k2-code-context-enhanced",
        "command": "python",
        "args": ["server.py"]
    },
    "kimi-k2-resilient": {
        "repo": "https://github.com/zhaoyinglia/kimi-k2-resilient-enhanced",
        "command": "python",
        "args": ["server.py"]
    },
    "rag-context": {
        "repo": "https://github.com/valentin-marquez/mcp-rag-context",
        "command": "python",
        "args": ["src/mcp_rag_context/server.py"]
    }
}


class MCPFederationInstaller:
    """Main installer class with correct MCP classifications"""
    
    def __init__(self):
        self.system = platform.system()
        self.home = Path.home()
        self.username = os.environ.get('USERNAME' if self.system == 'Windows' else 'USER', 'User')
        self.mcp_base_dir = self.home / "mcp-servers"
        self.claude_config_path = self._get_claude_config_path()
        self.errors = []
        self.warnings = []
        # Store command paths for Windows compatibility
        self.npm_cmd = None
        self.npx_cmd = None
        self.node_cmd = None
        
    def _get_claude_config_path(self) -> Path:
        """Get Claude Desktop configuration path"""
        if self.system == "Windows":
            return self.home / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
        elif self.system == "Darwin":
            return self.home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
        else:
            return self.home / ".config" / "claude" / "claude_desktop_config.json"
    
    def get_npm_cmd(self) -> str:
        """Get the correct npm command for the platform"""
        if self.npm_cmd:
            return self.npm_cmd
        # On Windows, npm is actually npm.cmd
        if self.system == "Windows" or os.name == 'nt':
            # Try to find npm.cmd
            npm_cmd = shutil.which("npm.cmd")
            if npm_cmd:
                return npm_cmd
            # Fallback to common location
            nodejs_path = Path("C:/Program Files/nodejs/npm.cmd")
            if nodejs_path.exists():
                return str(nodejs_path)
            return "npm.cmd"  # Last resort
        return "npm"
    
    def get_npx_cmd(self) -> str:
        """Get the correct npx command for the platform"""
        if self.npx_cmd:
            return self.npx_cmd
        # On Windows, npx is actually npx.cmd
        if self.system == "Windows" or os.name == 'nt':
            # Try to find npx.cmd
            npx_cmd = shutil.which("npx.cmd")
            if npx_cmd:
                return npx_cmd
            # Fallback to common location
            nodejs_path = Path("C:/Program Files/nodejs/npx.cmd")
            if nodejs_path.exists():
                return str(nodejs_path)
            return "npx.cmd"  # Last resort
        return "npx"
    
    def check_prerequisites(self) -> bool:
        """Check for Node.js and npm"""
        print(f"{Colors.OKBLUE}Checking prerequisites...{Colors.ENDC}")
        
        # Check Node.js
        if self.system == "Windows":
            node_check = shutil.which("node.exe") or shutil.which("node")
        else:
            node_check = shutil.which("node")
        
        if not node_check:
            print(f"{Colors.FAIL}[X] Node.js not found{Colors.ENDC}")
            return False
        self.node_cmd = node_check
        
        # Check npm - on Windows it's npm.cmd
        if self.system == "Windows":
            npm_check = shutil.which("npm.cmd") or shutil.which("npm")
            npx_check = shutil.which("npx.cmd") or shutil.which("npx")
        else:
            npm_check = shutil.which("npm")
            npx_check = shutil.which("npx")
        
        if not npm_check:
            print(f"{Colors.FAIL}[X] npm not found{Colors.ENDC}")
            return False
        
        # Store the found commands
        self.npm_cmd = npm_check
        self.npx_cmd = npx_check or self.get_npx_cmd()
            
        # Check Python
        if sys.version_info < (3, 9):
            print(f"{Colors.FAIL}[X] Python 3.9+ required{Colors.ENDC}")
            return False
            
        print(f"{Colors.OKGREEN}[OK] All prerequisites met{Colors.ENDC}")
        return True
    
    def create_mcp_directories(self):
        """Create necessary directories"""
        self.mcp_base_dir.mkdir(exist_ok=True)
        print(f"{Colors.OKGREEN}[OK] Created MCP directory: {self.mcp_base_dir}{Colors.ENDC}")
    
    def configure_npx_mcp(self, name: str, package: str, config: Dict) -> Dict:
        """Configure an NPX-based MCP"""
        print(f"  Configuring NPX MCP: {name}")
        
        mcp_config = {
            "command": self.get_npx_cmd(),
            "args": ["-y", package]
        }
        
        # Add environment variables if needed
        if name == "github":
            mcp_config["env"] = {"GITHUB_PERSONAL_ACCESS_TOKEN": "YOUR_TOKEN_HERE"}
        elif name == "perplexity":
            mcp_config["env"] = {"PERPLEXITY_API_KEY": "YOUR_KEY_HERE"}
        elif name == "sqlite":
            db_path = str(self.mcp_base_dir / "sqlite" / "test.db")
            os.makedirs(self.mcp_base_dir / "sqlite", exist_ok=True)
            mcp_config["args"].extend(["--db-path", db_path])
        
        config["mcpServers"][name] = mcp_config
        return config
    
    def install_npm_mcp(self, name: str, package: str, config: Dict) -> Dict:
        """Install and configure an NPM-based MCP"""
        print(f"  Installing NPM MCP: {name}")
        
        # Create directory for NPM MCP
        mcp_dir = self.mcp_base_dir / name
        mcp_dir.mkdir(parents=True, exist_ok=True)
        
        # Create package.json
        package_json = {
            "name": f"mcp-{name}",
            "version": "1.0.0",
            "private": True,
            "scripts": {
                "serve": f"node node_modules/{package}/dist/index.js"
            },
            "dependencies": {
                package: "latest"
            }
        }
        
        package_json_path = mcp_dir / "package.json"
        with open(package_json_path, 'w') as f:
            json.dump(package_json, f, indent=2)
        
        # Install dependencies
        try:
            subprocess.run(
                [self.get_npm_cmd(), "install"],
                cwd=str(mcp_dir),
                check=True,
                capture_output=True,
                text=True
            )
            print(f"    [OK] Installed {package}")
        except subprocess.CalledProcessError as e:
            self.errors.append(f"Failed to install {name}: {e}")
            return config        
        # Configure MCP
        mcp_config = {
            "command": self.get_npm_cmd(),
            "args": ["run", "serve"],
            "cwd": str(mcp_dir)
        }
        
        # Add environment variables if needed
        if name == "filesystem":
            mcp_config["env"] = {
                "ALLOWED_DIRECTORIES": str(self.home)
            }
        elif name == "web-search":
            mcp_config["env"] = {
                "BRAVE_SEARCH_API_KEY": "YOUR_KEY_HERE"
            }
        
        config["mcpServers"][name] = mcp_config
        return config
    
    def install_python_mcp(self, name: str, repo_info: Dict, config: Dict) -> Dict:
        """Clone and configure a Python-based MCP"""
        print(f"  Installing Python MCP: {name}")
        
        mcp_dir = self.mcp_base_dir / name
        
        # Clone repository if not exists
        if not mcp_dir.exists():
            try:
                subprocess.run(                    ["git", "clone", repo_info["repo"], str(mcp_dir)],
                    check=True,
                    capture_output=True,
                    text=True
                )
                print(f"    [OK] Cloned repository")
            except subprocess.CalledProcessError as e:
                self.errors.append(f"Failed to clone {name}: {e}")
                return config
        
        # Install Python dependencies if requirements.txt exists
        req_file = mcp_dir / "requirements.txt"
        if req_file.exists():
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
                    check=True,
                    capture_output=True,
                    text=True
                )
                print(f"    [OK] Installed Python dependencies")
            except subprocess.CalledProcessError:
                self.warnings.append(f"Could not install deps for {name}")
        
        # Configure MCP
        mcp_config = {
            "command": repo_info.get("command", "python"),
            "args": repo_info.get("args", ["server.py"]),
            "cwd": str(mcp_dir),
            "env": {
                "PYTHONUNBUFFERED": "1"            }
        }
        
        # Add specific environment variables
        if name == "converse-enhanced":
            mcp_config["env"]["ANTHROPIC_API_KEY"] = "YOUR_KEY_HERE"
        
        config["mcpServers"][name] = mcp_config
        return config
    
    def install_all_mcps(self):
        """Install all MCPs with correct classifications"""
        print(f"\n{Colors.HEADER}Installing MCP Federation (15 MCPs){Colors.ENDC}\n")
        
        # Load or create config
        if self.claude_config_path.exists():
            with open(self.claude_config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {"mcpServers": {}}
        
        # Ensure mcpServers key exists
        if "mcpServers" not in config:
            config["mcpServers"] = {}
        
        # 1. Configure NPX MCPs (7)
        print(f"{Colors.OKBLUE}Configuring NPX-based MCPs...{Colors.ENDC}")
        for name, package in MCP_NPX_PACKAGES.items():
            config = self.configure_npx_mcp(name, package, config)
        print(f"{Colors.OKGREEN}[OK] Configured {len(MCP_NPX_PACKAGES)} NPX MCPs{Colors.ENDC}\n")        
        # 2. Install NPM MCPs (4)
        print(f"{Colors.OKBLUE}Installing NPM-based MCPs...{Colors.ENDC}")
        for name, package in MCP_NPM_PACKAGES.items():
            config = self.install_npm_mcp(name, package, config)
        print(f"{Colors.OKGREEN}[OK] Installed {len(MCP_NPM_PACKAGES)} NPM MCPs{Colors.ENDC}\n")
        
        # 3. Install Python MCPs (4)
        print(f"{Colors.OKBLUE}Installing Python-based MCPs...{Colors.ENDC}")
        for name, repo_info in MCP_PYTHON_REPOS.items():
            config = self.install_python_mcp(name, repo_info, config)
        print(f"{Colors.OKGREEN}[OK] Installed {len(MCP_PYTHON_REPOS)} Python MCPs{Colors.ENDC}\n")
        
        # Save configuration
        self.claude_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.claude_config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"{Colors.OKGREEN}{Colors.BOLD}[OK] Configuration saved to:{Colors.ENDC}")
        print(f"  {self.claude_config_path}\n")
        
        # Report summary
        total_mcps = len(MCP_NPX_PACKAGES) + len(MCP_NPM_PACKAGES) + len(MCP_PYTHON_REPOS)
        print(f"{Colors.HEADER}{Colors.BOLD}Installation Complete!{Colors.ENDC}")
        print(f"Total MCPs configured: {total_mcps}")
        print(f"  • NPX-based: {len(MCP_NPX_PACKAGES)}")
        print(f"  • NPM-based: {len(MCP_NPM_PACKAGES)}")
        print(f"  • Python-based: {len(MCP_PYTHON_REPOS)}")
                # Show any errors or warnings
        if self.errors:
            print(f"\n{Colors.FAIL}Errors encountered:{Colors.ENDC}")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.warnings:
            print(f"\n{Colors.WARNING}Warnings:{Colors.ENDC}")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        print(f"\n{Colors.OKCYAN}Next steps:{Colors.ENDC}")
        print("1. Add your API keys to the configuration")
        print("2. Restart Claude Desktop")
        print("3. All 15 MCPs should be available!")
    
    def run(self):
        """Main installation process"""
        print(f"{Colors.HEADER}{Colors.BOLD}")
        print("="*60)
        print("    MCP FEDERATION INSTALLER v3.2.0")
        print("    Correct Classification Edition")
        print("="*60)
        print(f"{Colors.ENDC}\n")
        
        # Check prerequisites
        if not self.check_prerequisites():
            print(f"\n{Colors.FAIL}Please install missing prerequisites first.{Colors.ENDC}")
            return 1
        
        # Create directories        self.create_mcp_directories()
        
        # Install all MCPs
        self.install_all_mcps()
        
        return 0


def main():
    """Entry point"""
    installer = MCPFederationInstaller()
    return installer.run()


if __name__ == '__main__':
    sys.exit(main())