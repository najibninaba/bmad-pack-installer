# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-08-14

### Added
- Initial release of bmad-pack-installer to PyPI
- Command-line interface for installing BMAD expansion packs
- Package validation with hash verification
- Symlink management for pack installations
- YAML manifest support for pack definitions
- Comprehensive test suite with pytest
- Type hints and mypy support

### Features
- Install packs from local or remote sources
- Validate pack integrity using SHA256 checksums
- Manage symlinks for pack directories
- Rich CLI output with progress indicators
- Support for Python 3.9+

### Infrastructure
- Restructured package layout for PyPI distribution
- Automated testing with pytest
- Code formatting with Black
- Type checking with mypy
- Build system using hatchling