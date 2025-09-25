# MCP Federation Pro 🚀

[![CI/CD Pipeline](https://github.com/justmy2satoshis/mcp-federation-pro/workflows/MCP%20Federation%20CI%2FCD%20Pipeline/badge.svg)](https://github.com/justmy2satoshis/mcp-federation-pro/actions)
[![Security Scan](https://github.com/justmy2satoshis/mcp-federation-pro/workflows/Security%20%26%20Vulnerability%20Scanning/badge.svg)](https://github.com/justmy2satoshis/mcp-federation-pro/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![Node 18+](https://img.shields.io/badge/node-18%2B-green)](https://nodejs.org/)
[![Version](https://img.shields.io/badge/version-2.0.0-orange)](https://github.com/justmy2satoshis/mcp-federation-pro/releases)

**Professional MCP installer with safe installation, manifest tracking, and clean uninstall.**

## 🎯 What's New in v2.0.0

- ✅ **Safe Installation**: Preserves existing user MCPs
- ✅ **Manifest Tracking**: Tracks what we install vs what existed  
- ✅ **Clean Uninstall**: Only removes MCPs we installed
- ✅ **Exact Production Config**: Mirrors working setup exactly
- ✅ **Backup System**: Creates backups before modifications
- ✅ **CI/CD Validated**: All changes tested automatically

## 🏗️ Architecture

This installer follows **safety-first principles**:
1. Never disrupts existing user MCPs
2. Tracks everything it installs in a manifest
3. Creates backups before any modifications
4. Only uninstalls what it installed
5. Validates all configurations before saving

## 📦 All 15 MCP Servers

| Type | MCP | Description |
|------|-----|-------------|
| **NPX** | filesystem | File system access |
| **NPX** | memory | Memory storage (fixed EEXIST issue) |
| **NPX** | sequential-thinking | Chain of thought reasoning |
| **NPX** | github-manager | GitHub operations |
| **NPX** | sqlite | SQLite database |
| **NPX** | playwright | Browser automation |
| **NPX** | web-search | Brave search integration |
| **NPX** | git-ops | Git operations |
| **NPX** | desktop-commander | Desktop control |
| **NPX** | perplexity | Perplexity AI search |
| **Node** | expert-role-prompt | Expert role prompts |
| **Python** | converse-enhanced | Enhanced conversations |
| **Python** | kimi-k2-code-context | Code context analysis |
| **Python** | kimi-k2-resilient | Resilient processing |
| **Python** | rag-context | RAG context management |

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/justmy2satoshis/mcp-federation-pro.git
cd mcp-federation-pro

# Run the safe installer
python install.py

# Result: All 15 MCPs installed safely
```

## 🛡️ Safe Installation Features

### Installation Process
1. **Detects existing MCPs** before installing
2. **Creates backup** of current configuration
3. **Merges new MCPs** without overwriting existing ones
4. **Saves manifest** tracking what was installed
5. **Validates** all MCPs are configured correctly

### Installation Manifest
The installer creates `~/.mcp-federation/installation_manifest.json` containing:
```json
{
  "version": "2.0.0",
  "installation_date": "2025-09-25T15:30:00",
  "installed_by_us": ["memory", "sqlite", ...],
  "already_existed": ["filesystem", ...],
  "system": "Windows"
}
```

## 🧹 Clean Uninstall

Remove ONLY the MCPs we installed, preserving all others:

```bash
# Safe uninstall (uses manifest)
python uninstall.py

# Force uninstall (removes all 15 standard MCPs)
python uninstall.py --force
```

### Uninstall Safety
- ✅ Reads installation manifest
- ✅ Only removes MCPs in "installed_by_us" list
- ✅ Preserves all other user MCPs
- ✅ Creates backup before removal
- ✅ Cleans up manifest after uninstall

## 🔧 Configuration Details

### Memory MCP Fix
Previously had EEXIST errors with npm install. Now uses npx:
```json
"memory": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-memory"],
  "env": {"NODE_NO_WARNINGS": "1"}
}
```

### Expert-Role-Prompt
Bundled from local installation (not on npm):
```json
"expert-role-prompt": {
  "command": "node",
  "args": ["~/mcp-servers/expert-role-prompt/server.js"],
  "env": {"NODE_NO_WARNINGS": "1"}
}
```

## 📊 Installation Summary

After installation, you'll see:
```
Installation Summary:
  • Newly installed: 8 MCPs
  • Already existed: 7 MCPs  
  • Total MCPs now: 15

Newly installed MCPs:
  • memory
  • sqlite
  • playwright
  • web-search
  • git-ops
  • desktop-commander
  • perplexity
  • rag-context
```

## 🏭 CI/CD Pipeline

Every commit is tested across:
- **Operating Systems**: Ubuntu, Windows, macOS
- **Node.js Versions**: 18.x, 20.x, 22.x
- **Python Versions**: 3.9, 3.10, 3.11
- **Total Configurations**: 27 parallel test runs

## 🔒 Security Features

- Daily vulnerability scanning
- Secret detection
- License compliance checking
- Dependency auditing
- SAST with Semgrep

## 🤝 Contributing

We welcome contributions! The codebase is:
- ✅ Fully tested with CI/CD
- ✅ Type-hinted and documented
- ✅ Following safety-first principles
- ✅ Clean uninstall capability

### Running Tests Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Test installer in dry-run mode
python install.py --dry-run

# Quick test for CI/CD
python install.py --quick-test
```

## 📜 License

MIT License - see [LICENSE](LICENSE) file

## 🙏 Key Improvements Over Legacy

| Feature | Legacy | This Repository |
|---------|--------|-----------------|
| Preserves User MCPs | ❌ Overwrites | ✅ Safe merge |
| Tracks Installations | ❌ No tracking | ✅ Manifest system |
| Clean Uninstall | ❌ Removes all | ✅ Only ours |
| Backup System | ❌ None | ✅ Automatic |
| Memory MCP | ❌ EEXIST error | ✅ Fixed |
| CI/CD | ❌ None | ✅ 27 configs |

## ⚠️ Migration from Old Repository

If you used the old `mcp-federation-core` repository:
1. That repo had 10+ conflicting installer versions
2. This is a clean rebuild with proper practices
3. Safe to install over existing MCPs
4. Will preserve your customizations

---

**Built with safety-first principles and professional CI/CD**