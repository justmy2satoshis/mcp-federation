# MCP Federation 🚀

[![Version](https://img.shields.io/badge/version-3.0.0-brightgreen.svg)](https://github.com/justmy2satoshis/mcp-federation/releases)
[![CI/CD Pipeline](https://github.com/justmy2satoshis/mcp-federation/actions/workflows/ci.yml/badge.svg)](https://github.com/justmy2satoshis/mcp-federation/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Node 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)

## One-Command MCP Installer for Claude Desktop

**It Just Works™** - Automatically installs dependencies, fixes PATH issues, and sets up 15 essential MCP servers for Claude Desktop.

### 🎯 What It Does

Installs and configures 15 MCP servers that supercharge Claude Desktop with:
- File system access and memory management
- GitHub integration and Git operations
- Web search and AI assistance
- Database operations and browser automation
- Advanced context-aware capabilities

### ⚡ Quick Install

```bash
# Clone and run - that's it!
git clone https://github.com/justmy2satoshis/mcp-federation.git
cd mcp-federation
python install.py
```

**Missing Python or Node.js?** No problem! The installer will:
1. Detect what's missing
2. Ask for permission to install
3. Handle everything automatically

### 🔧 Features That Make It Simple

- **Auto-Dependency Installation**: Missing Python/Node.js? We'll install them for you
- **npm PATH Fix**: Automatically fixes the Windows npm PATH issue
- **Safe Installation**: Never overwrites your existing MCPs
- **Clean Uninstall**: Removes only what we installed
- **Zero Configuration**: Works out of the box on Windows, macOS, and Linux

### 📦 What Gets Installed

| Category | MCPs | Purpose |
|----------|------|---------|
| **Core** | `filesystem`, `memory`, `sequential-thinking` | File access, memory, and reasoning |
| **Dev Tools** | `github-manager`, `git-ops`, `desktop-commander` | GitHub and Git integration |
| **Data** | `sqlite`, `playwright` | Databases and browser automation |
| **AI/Search** | `web-search`, `perplexity` | Web search and AI queries |
| **Enhanced** | `expert-role-prompt`, `converse-enhanced` | Advanced AI capabilities |
| **Context** | `kimi-k2-code-context`, `kimi-k2-resilient`, `rag-context` | Code understanding |

### 🛠 Automated Dependency Resolution

The installer automatically handles:

**Windows:**
- Uses winget (built into Windows 10/11)
- Falls back to chocolatey if available
- Fixes npm PATH issues automatically

**macOS:**
- Uses Homebrew if available
- Downloads official installers as fallback

**Linux:**
- Uses apt-get (Ubuntu/Debian)
- Uses yum/dnf (RHEL/Fedora)
- Adapts to your distribution

### 🚀 Advanced Options

```bash
# Fully automated (no prompts)
python install.py --auto

# Just fix npm PATH on Windows
python install.py --fix-npm

# Uninstall (removes only our MCPs)
python uninstall.py
```

### ❓ FAQ

**Q: What if I don't have Python installed?**
A: The installer will offer to install it for you!

**Q: I have Node.js but npm doesn't work**
A: Common Windows issue - we fix it automatically.

**Q: Will it mess up my existing MCPs?**
A: Never! We only add new ones, never overwrite.

**Q: How do I uninstall?**
A: Run `python uninstall.py` - removes only what we added.

**Q: Do I need admin rights?**
A: Only if installing missing dependencies. MCPs install to user space.

### 🔍 Troubleshooting

99% of issues are solved by the installer automatically. If you hit the 1%:

1. **Restart your terminal** after dependency installation
2. **Restart Claude Desktop** after MCP installation
3. **Check the log** for specific error messages

Still stuck? [Open an issue](https://github.com/justmy2satoshis/mcp-federation/issues)

### 📝 Version History

**v3.0.0** - The "It Just Works" Release
- Automatic dependency installation
- npm PATH auto-fix for Windows
- Simplified to single command installation
- Renamed from mcp-federation-pro for simplicity

**v2.x** - Previous iterations with manual steps

### 📄 License

MIT - Use it, modify it, share it!

---

**Philosophy**: Installation should be simple. Dependencies should be automatic. It should just work.

Built with ❤️ for the Claude Desktop community.