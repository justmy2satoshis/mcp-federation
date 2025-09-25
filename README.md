# MCP Federation Pro 🚀

[![CI/CD Pipeline](https://github.com/justmy2satoshis/mcp-federation-pro/actions/workflows/mcp-ci.yml/badge.svg)](https://github.com/justmy2satoshis/mcp-federation-pro/actions)
[![Security Scan](https://github.com/justmy2satoshis/mcp-federation-pro/actions/workflows/security-scan.yml/badge.svg)](https://github.com/justmy2satoshis/mcp-federation-pro/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Node 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)

## Professional MCP Installer Suite for Claude Desktop

A production-ready, thoroughly tested installer that safely configures 15 essential MCP servers for Claude Desktop without disrupting existing configurations.

### ✅ Key Features

- **Safe Installation**: Never overwrites existing MCPs
- **Clean Uninstall**: Only removes what we installed
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Fully Tested**: Comprehensive CI/CD with 30+ automated checks
- **Manifest Tracking**: Records exactly what was installed
- **Automatic Backups**: Creates timestamped backups before changes
- **Zero Test Contamination**: Complete separation of test and production code

### 📦 Included MCPs (15 Total)

| Category | MCPs | Description |
|----------|------|-------------|
| **Core Tools** | `filesystem`, `memory`, `sequential-thinking` | Essential file and memory operations |
| **Development** | `github-manager`, `git-ops`, `desktop-commander` | GitHub integration and Git operations |
| **Data & Testing** | `sqlite`, `playwright` | Database operations and browser automation |
| **Search & AI** | `web-search`, `perplexity` | Web search and AI assistance |
| **Enhanced** | `expert-role-prompt`, `converse-enhanced` | Advanced AI capabilities |
| **Specialized** | `kimi-k2-code-context`, `kimi-k2-resilient`, `rag-context` | Context-aware code assistance |

### 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/justmy2satoshis/mcp-federation-pro.git
cd mcp-federation-pro

# Run the installer
python install.py

# To uninstall (removes only our MCPs)
python uninstall.py
```

### 🛡️ Safety Features

1. **Pre-Installation Detection**: Identifies existing MCPs before installation
2. **Manifest Tracking**: Records what we install vs what existed
3. **Automatic Backups**: Creates timestamped backups before any modifications
4. **Smart Merging**: Adds new MCPs without disturbing existing ones
5. **Clean Uninstall**: Only removes MCPs from our manifest

### 📊 CI/CD Status

This repository features comprehensive GitHub Actions workflows:

#### Test Matrix
- **Operating Systems**: Ubuntu 22.04, Windows Latest, macOS 14
- **Node.js Versions**: 18.x, 20.x, 22.x
- **Python Versions**: 3.9, 3.10, 3.11, 3.12

#### Quality Assurance
- ✅ **Syntax Validation**: Python AST compilation checks
- ✅ **Contamination Detection**: Ensures no test code in production
- ✅ **Cross-Platform Testing**: Windows path handling verified
- ✅ **Security Scanning**: Automated vulnerability detection
- ✅ **Clean Separation**: Test wrapper completely isolated from installer

### 📁 Repository Structure

```
mcp-federation-pro/
├── install.py              # Production installer (v2.1.0)
├── uninstall.py            # Clean uninstaller
├── tests/                  # Test suite (separate from production)
│   └── test_installer_ci.py    # CI/CD test wrapper
├── .github/workflows/      # CI/CD pipelines
│   ├── mcp-ci.yml         # Main CI pipeline
│   ├── pr-validation.yml  # PR checks
│   └── security-scan.yml  # Security scanning
├── LICENSE                # MIT License
└── README.md              # This file
```

### 🔧 Technical Details

#### Installation Locations

**Installation Manifest**: `~/.mcp-federation/installation_manifest.json`

**Configuration Paths**:
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.claude/claude_desktop_config.json`

#### Manifest Structure

```json
{
  "version": "2.1.0",
  "installation_date": "2024-01-26T10:30:00",
  "installed_by_us": ["filesystem", "memory", ...],
  "already_existed": ["custom-mcp-1", ...],
  "system": "Windows",
  "claude_desktop_mcps": [...]
}
```

### 🔬 Development Philosophy

This project follows strict CI/CD-first development principles:

1. **Test Infrastructure First**: CI/CD was built before the installer
2. **Clean Separation**: Test code never touches production code
3. **No Contamination**: Production installer has zero test flags or modes
4. **Comprehensive Testing**: Every commit triggers 30+ automated checks
5. **Cross-Platform Validation**: Explicit Windows, macOS, and Linux testing

### 🤝 Contributing

We welcome contributions! Please ensure:
- All tests pass (run `python tests/test_installer_ci.py`)
- No test code in production files
- Cross-platform compatibility maintained
- Documentation updated for new features

### 📝 Lessons Learned

This is a complete rebuild after learning from our [deprecated repository](https://github.com/justmy2satoshis/mcp-federation-core). Key improvements:

- **No Test Contamination**: Previous repo failed due to test code in production
- **Clean Architecture**: Complete separation of concerns
- **Professional CI/CD**: Built infrastructure before features
- **Manifest Tracking**: Clean uninstall capability from day one

### 🙏 Acknowledgments

Built with professional engineering practices, clean code separation, and automated testing to ensure reliability across all platforms.

### 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

---

**Note**: This repository represents a complete architectural rebuild with professional engineering standards. The deprecated repository served as a valuable learning experience that informed our current best practices.