"""Manifest file handling for BMAD pack installer."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any
import yaml
import shutil

from .validators import format_pack_name


def create_install_manifest(
    pack_name: str, 
    config: Dict[str, Any], 
    files_data: List[Dict[str, Any]],
    ides_setup: List[str] = None
) -> Dict[str, Any]:
    """Create install-manifest.yaml for the expansion pack.
    
    Args:
        pack_name: Name of the pack (will ensure bmad- prefix)
        config: Configuration dictionary from config.yaml
        files_data: List of file entries with path, hash, modified
        ides_setup: List of IDEs configured during installation
        
    Returns:
        Dictionary containing install manifest data
    """
    if ides_setup is None:
        ides_setup = ['claude-code']
    
    # Ensure pack name has proper format (no dot prefix for manifest)
    formatted_pack_name = format_pack_name(pack_name)
    
    return {
        'version': config.get('version', '1.0.0'),
        'installed_at': datetime.now(timezone.utc).isoformat(),
        'install_type': 'expansion-pack',
        'expansion_pack_id': formatted_pack_name,
        'expansion_pack_name': formatted_pack_name,
        'ides_setup': ides_setup,
        'files': files_data
    }


def write_install_manifest(manifest_path: Path, manifest_data: Dict[str, Any]) -> None:
    """Write install manifest to file.
    
    Args:
        manifest_path: Path where to write the manifest
        manifest_data: Manifest data dictionary
        
    Raises:
        PermissionError: If cannot write to file
        IOError: If file write fails
    """
    # Ensure directory exists
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(manifest_path, 'w', encoding='utf-8') as f:
            yaml.dump(manifest_data, f, default_flow_style=False, sort_keys=False)
    except (PermissionError, IOError) as e:
        raise IOError(f"Failed to write install manifest to {manifest_path}: {e}")


def load_core_manifest(core_manifest_path: Path) -> Dict[str, Any]:
    """Load the core BMAD install manifest.
    
    Args:
        core_manifest_path: Path to .bmad-core/install-manifest.yaml
        
    Returns:
        Core manifest dictionary
        
    Raises:
        FileNotFoundError: If manifest file doesn't exist
        yaml.YAMLError: If YAML is invalid
    """
    if not core_manifest_path.exists():
        raise FileNotFoundError(f"Core manifest not found: {core_manifest_path}")
    
    try:
        with open(core_manifest_path, 'r', encoding='utf-8') as f:
            manifest = yaml.safe_load(f)
        
        if manifest is None:
            manifest = {}
        
        return manifest
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in core manifest: {e}")


def backup_core_manifest(core_manifest_path: Path) -> Path:
    """Create a backup of the core manifest file.
    
    Args:
        core_manifest_path: Path to core manifest file
        
    Returns:
        Path to backup file
        
    Raises:
        IOError: If backup fails
    """
    if not core_manifest_path.exists():
        raise FileNotFoundError(f"Cannot backup non-existent file: {core_manifest_path}")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = core_manifest_path.with_suffix(f'.backup_{timestamp}.yaml')
    
    try:
        shutil.copy2(core_manifest_path, backup_path)
        return backup_path
    except (PermissionError, IOError) as e:
        raise IOError(f"Failed to create backup: {e}")


def update_core_manifest(
    core_manifest_path: Path, 
    pack_name: str, 
    key_files: List[Dict[str, Any]],
    create_backup: bool = True
) -> None:
    """Update the core BMAD install manifest with expansion pack info.
    
    Args:
        core_manifest_path: Path to .bmad-core/install-manifest.yaml
        pack_name: Name of the expansion pack
        key_files: List of key files to add to manifest
        create_backup: Whether to create a backup before modifying
        
    Raises:
        FileNotFoundError: If core manifest doesn't exist
        IOError: If cannot write to manifest
    """
    # Create backup if requested
    if create_backup and core_manifest_path.exists():
        backup_core_manifest(core_manifest_path)
    
    # Load existing manifest
    manifest = load_core_manifest(core_manifest_path)
    
    # Ensure required sections exist
    if 'expansion_packs' not in manifest:
        manifest['expansion_packs'] = []
    if 'files' not in manifest:
        manifest['files'] = []
    
    # Format pack name (no dot prefix for manifest)
    formatted_pack_name = format_pack_name(pack_name)
    
    # Add pack to expansion_packs list if not already present
    if formatted_pack_name not in manifest['expansion_packs']:
        manifest['expansion_packs'].append(formatted_pack_name)
        manifest['expansion_packs'].sort()  # Keep list sorted
    
    # Add key files to files section
    existing_paths = {file_entry.get('path', '') for file_entry in manifest['files']}
    
    for file_info in key_files:
        file_path = file_info.get('path', '')
        if file_path and file_path not in existing_paths:
            manifest['files'].append(file_info)
    
    # Write updated manifest
    try:
        with open(core_manifest_path, 'w', encoding='utf-8') as f:
            yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)
    except (PermissionError, IOError) as e:
        raise IOError(f"Failed to update core manifest: {e}")


def is_pack_installed(core_manifest_path: Path, pack_name: str) -> bool:
    """Check if expansion pack is already installed.
    
    Args:
        core_manifest_path: Path to core manifest file
        pack_name: Name of pack to check
        
    Returns:
        True if pack is installed, False otherwise
    """
    try:
        manifest = load_core_manifest(core_manifest_path)
        formatted_pack_name = format_pack_name(pack_name)
        expansion_packs = manifest.get('expansion_packs', [])
        return formatted_pack_name in expansion_packs
    except (FileNotFoundError, yaml.YAMLError):
        return False


def get_pack_manifest_path(project_path: Path, pack_name: str) -> Path:
    """Get path to expansion pack's install manifest.
    
    Args:
        project_path: Path to target project
        pack_name: Name of the expansion pack
        
    Returns:
        Path to pack's install-manifest.yaml
    """
    from .validators import format_pack_directory_name
    
    pack_dir = project_path / format_pack_directory_name(pack_name)
    return pack_dir / 'install-manifest.yaml'


def select_key_files(files_data: List[Dict[str, Any]], max_files: int = 10) -> List[Dict[str, Any]]:
    """Select key files to include in core manifest.
    
    Prioritizes important files like config.yaml, agents, templates, etc.
    
    Args:
        files_data: List of all file entries
        max_files: Maximum number of files to select
        
    Returns:
        List of key file entries to include in core manifest
    """
    # Priority order for file types
    priority_patterns = [
        'config.yaml',
        'README.md',
        'agents/',
        'templates/',
        'tasks/',
        'workflows/',
        'agent-teams/',
        'checklists/',
        'data/'
    ]
    
    key_files = []
    added_paths = set()
    
    # Add files in priority order
    for pattern in priority_patterns:
        if len(key_files) >= max_files:
            break
            
        for file_entry in files_data:
            if len(key_files) >= max_files:
                break
                
            file_path = file_entry.get('path', '')
            if file_path in added_paths:
                continue
                
            if pattern in file_path:
                key_files.append(file_entry)
                added_paths.add(file_path)
    
    # Fill remaining slots with other files if needed
    for file_entry in files_data:
        if len(key_files) >= max_files:
            break
            
        file_path = file_entry.get('path', '')
        if file_path not in added_paths:
            key_files.append(file_entry)
            added_paths.add(file_path)
    
    return key_files[:max_files]