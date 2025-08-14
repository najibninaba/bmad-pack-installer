# BMAD Expansion Pack Installer

A modern Python tool for installing BMAD (Breakthrough Method for Agile Ai Driven Development) expansion packs with proper directory structure, symbolic links, and manifest management.

## Features

- Installs BMAD expansion packs with proper directory structure
- Creates symbolic links for Claude Code integration
- Generates hidden directories using `.bmad-pack-name` format
- Provides SHA-256 hash generation and verification
- Creates and updates installation manifests
- Excludes development files and directories automatically
- Supports Windows, macOS, and Linux
- Displays progress indicators during installation
- Validates source packs and target projects

## Installation

### Recommended: Install as Tool

```bash
# Install once (recommended for regular use)
uv tool install bmad-pack-installer

# Use anywhere - command available globally
bmad-pack-installer --version
bmad-pack-installer deploy ./expansion-pack-source ./target-project
```

### Quick Use Without Installation

```bash
# Run directly with uvx (no installation needed)
uvx --from bmad-pack-installer bmad-pack-installer deploy ./expansion-pack-source ./target-project
```

### Install in Project

```bash
# Add to current project dependencies
uv add bmad-pack-installer

# Or install with pip
pip install bmad-pack-installer

# Use in project context
uv run bmad-pack-installer deploy ./expansion-pack-source ./target-project
```

### Install from Source (Development)

```bash
# Clone the repository
git clone https://github.com/najibninaba/bmad-pack-installer.git
cd bmad-pack-installer

# Install in virtual environment with uv
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .

# Install in virtual environment with pip
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

## Updating

To upgrade to the latest version:

```bash
# If installed as a tool (recommended)
uv tool upgrade bmad-pack-installer

# If installed with pip
pip install --upgrade bmad-pack-installer

# If installed in a project with uv
uv add --upgrade bmad-pack-installer

# Check current version
bmad-pack-installer --version
```

## Usage

### Basic Deployment

```bash
# Deploy expansion pack to BMAD project (assumes tool installation)
bmad-pack-installer deploy ./bmad-aisg-aiml /path/to/project
```

### Advanced Options

```bash
# Custom pack and command names
bmad-pack-installer deploy ./source /target \
  --pack-name=ai-ml-engineering \
  --command-name=bmadAISG

# Dry run to preview changes
bmad-pack-installer deploy ./source /target --dry-run

# Force reinstall over existing pack
bmad-pack-installer deploy ./source /target --force

# Skip certain installation steps
bmad-pack-installer deploy ./source /target \
  --skip-core-update \
  --skip-symlinks

# Configure for different IDE
bmad-pack-installer deploy ./source /target --ide=cursor
```

### Validation Commands

```bash
# Check if directory is a valid BMAD project
bmad-pack-installer check /path/to/project

# Validate expansion pack structure
bmad-pack-installer validate ./expansion-pack
```

> **Note:** If you haven't installed as a tool, prefix commands with `uvx --from bmad-pack-installer` or use `uv run bmad-pack-installer` if installed in a project.

## Command Line Options

| Option | Description |
|--------|-------------|
| `--pack-name` | Override pack name (auto-prepends 'bmad-' if missing) |
| `--command-name` | Claude command name (default: from config.yaml) |
| `--ide` | IDE to configure: claude-code, cursor, windsurf |
| `--skip-core-update` | Skip updating .bmad-core/install-manifest.yaml |
| `--skip-symlinks` | Skip creating symbolic links |
| `--force` | Overwrite existing installation |
| `--dry-run` | Show what would be installed without changes |
| `--verbose` | Enable detailed logging |

## Expansion Pack Requirements

Your expansion pack must have this structure:

```
bmad-expansion-pack/
├── config.yaml                 # Required: Pack metadata
├── agents/                     # AI agent definitions
│   └── *.md
├── tasks/                      # Task definitions  
│   └── *.md
├── templates/                  # Document templates
│   └── *.yaml
├── checklists/                 # Validation checklists
│   └── *.md
├── workflows/                  # Multi-step workflows
│   └── *.yaml
├── agent-teams/               # Agent team configurations
│   └── *.yaml
├── data/                      # Reference data
│   └── *.md
└── web-bundles/              # Pre-built UI bundles
    └── *.txt
```

### Required config.yaml

```yaml
name: expansion-pack-name        # Will get 'bmad-' prefix
version: 1.0.0                   # Semantic version
description: Pack description    # Human-readable description
slashPrefix: commandName         # Claude command name (optional)
```

## Deployment Process

The installer performs these steps:

1. Validates source pack and target project
2. Copies files to hidden `.bmad-pack-name/` directory
3. Generates SHA-256 hashes for integrity checking
4. Creates installation manifests
5. Updates `.bmad-core/install-manifest.yaml`
6. Creates symbolic links in `.claude/commands/`


## Examples

### Deploying the AI/ML Engineering Pack

```bash
# Basic deployment
bmad-pack-installer deploy ./bmad-aisg-aiml ./my-project

# Results in:
# - Hidden directory: ./my-project/.bmad-aisg-aiml/
# - Claude commands: ./my-project/.claude/commands/bmadAISG/
# - Updated manifests and symlinks
```

### Dry Run Preview

```bash
bmad-pack-installer deploy ./pack ./project --dry-run

# Output:
# DRY RUN: Would deploy expansion pack 'bmad-pack-name'
# Target directory: .bmad-pack-name
# Files to deploy: 47
# Potential symlinks: 12
# Command name: packCommand
```

## Target Project Requirements

The target project must be BMAD-enabled with:

- `.bmad-core/` directory
- `.bmad-core/install-manifest.yaml` file

## Development

To develop or contribute to this tool:

```bash
# Clone and setup
git clone <repository>
cd bmad-pack-installer

# Install in development mode
uv pip install -e .

# Run tests
uv run pytest

# Format code
uv run black src/
uv run flake8 src/
```

## Troubleshooting

### Pack Not Recognized

- Ensure `config.yaml` exists in source directory
- Verify required fields: `name`, `version`

### Target Not Valid BMAD Project

- Check for `.bmad-core/` directory
- Verify `.bmad-core/install-manifest.yaml` exists

### Symlink Creation Failed

- On Windows: Run as Administrator or enable Developer Mode
- Fallback: Files are copied instead of symlinked

### Permission Errors

- Check write permissions to target directory
- Ensure `.bmad-core/install-manifest.yaml` is writable

## License

MIT License - see LICENSE file for details.

## Support

For issues and feature requests, please visit the [GitHub repository](https://github.com/najibninaba/bmad-pack-installer).
