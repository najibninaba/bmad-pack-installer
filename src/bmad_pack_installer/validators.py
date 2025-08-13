"""Validation utilities for BMAD pack installer."""

import re
from pathlib import Path
from typing import Dict, List, Set
import yaml


def format_pack_name(pack_name: str) -> str:
    """Format pack name to ensure 'bmad-' prefix.
    
    Args:
        pack_name: Original pack name
        
    Returns:
        Pack name with 'bmad-' prefix
    """
    if not pack_name.startswith('bmad-'):
        return f'bmad-{pack_name}'
    return pack_name


def format_pack_directory_name(pack_name: str) -> str:
    """Format pack name for directory creation (ensure bmad- prefix and add dot for hidden).
    
    Args:
        pack_name: Original pack name
        
    Returns:
        Directory name with dot prefix for hidden directory
    """
    formatted_name = format_pack_name(pack_name)
    return f'.{formatted_name}'


def validate_pack_name(pack_name: str) -> bool:
    """Validate pack name format.
    
    Args:
        pack_name: Pack name to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Pack names should be lowercase, alphanumeric with hyphens
    pattern = r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$'
    formatted_name = format_pack_name(pack_name)
    return bool(re.match(pattern, formatted_name))


def is_bmad_project(project_path: Path) -> bool:
    """Check if directory is a valid BMAD-enabled project.
    
    Args:
        project_path: Path to project directory
        
    Returns:
        True if valid BMAD project, False otherwise
    """
    if not project_path.exists() or not project_path.is_dir():
        return False
    
    # Check for .bmad-core directory
    bmad_core = project_path / '.bmad-core'
    if not bmad_core.exists() or not bmad_core.is_dir():
        return False
    
    # Check for install-manifest.yaml in .bmad-core
    install_manifest = bmad_core / 'install-manifest.yaml'
    return install_manifest.exists() and install_manifest.is_file()


def is_expansion_pack(source_path: Path) -> bool:
    """Check if directory is a valid BMAD expansion pack.
    
    Args:
        source_path: Path to source directory
        
    Returns:
        True if valid expansion pack, False otherwise
    """
    if not source_path.exists() or not source_path.is_dir():
        return False
    
    # Check for config.yaml
    config_file = source_path / 'config.yaml'
    if not config_file.exists() or not config_file.is_file():
        return False
    
    # Try to load and validate basic structure
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Must have name and version
        if 'name' not in config or 'version' not in config:
            return False
        
        return True
    except (yaml.YAMLError, IOError):
        return False


def load_config(config_path: Path) -> Dict:
    """Load and validate configuration file.
    
    Args:
        config_path: Path to config.yaml file
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML is invalid
        ValueError: If required fields are missing
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in config file: {e}")
    
    # Validate required fields
    required_fields = ['name', 'version']
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required field '{field}' in config.yaml")
    
    return config


def load_exclusion_list(exclusion_file: Path) -> Set[str]:
    """Load exclusion list from file.
    
    Args:
        exclusion_file: Path to exclusion list file
        
    Returns:
        Set of exclusion patterns
    """
    exclusions = set()
    
    if exclusion_file.exists():
        try:
            with open(exclusion_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        exclusions.add(line)
        except IOError:
            # If we can't read exclusion file, continue with defaults
            pass
    
    return exclusions


def get_default_exclusions() -> Set[str]:
    """Get default set of exclusions.
    
    Returns:
        Set of default exclusion patterns
    """
    return {
        'install-expansion-pack-plan.md',
        'exclusion-list.txt',
        'CLAUDE.md',
        '.claude',
        '.taskmaster',
        '.mcp.json',
        '.gitignore',
        '.git',
        'bmad-pack-installer',
        'test-project',  # Exclude test directories
        '__pycache__',   # Python cache
        '.pytest_cache', # Pytest cache
        '.venv',         # Virtual environments
        'venv',
        '.DS_Store',     # macOS files
        'Thumbs.db'      # Windows files
    }


def should_exclude(path: Path, source_base: Path, exclusion_list: Set[str]) -> bool:
    """Check if path should be excluded from installation.
    
    Args:
        path: Path to check
        source_base: Base source directory
        exclusion_list: Set of exclusion patterns
        
    Returns:
        True if should be excluded, False otherwise
    """
    default_exclusions = get_default_exclusions()
    
    # Check if file/directory name is in exclusion list
    if path.name in default_exclusions or path.name in exclusion_list:
        return True
    
    # Check if any part of the path matches exclusion patterns
    relative_path = path.relative_to(source_base)
    for part in relative_path.parts:
        if part in default_exclusions or part in exclusion_list:
            return True
    
    # Check full relative path string
    relative_str = str(relative_path)
    if relative_str in exclusion_list:
        return True
    
    # Check with leading ./
    if f"./{relative_str}" in exclusion_list:
        return True
    
    return False


def validate_command_name(command_name: str) -> bool:
    """Validate Claude command name format.
    
    Args:
        command_name: Command name to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Command names should be alphanumeric, can contain underscores/hyphens
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, command_name)) and len(command_name) > 0