"""Symbolic link management for BMAD pack installer."""

import os
import platform
from pathlib import Path
from typing import List, Optional
import shutil

from .validators import format_pack_directory_name


def is_windows() -> bool:
    """Check if running on Windows."""
    return platform.system() == 'Windows'


def can_create_symlinks() -> bool:
    """Check if the system supports symbolic link creation.
    
    Returns:
        True if symlinks can be created, False otherwise
    """
    if not is_windows():
        return True
    
    # On Windows, check if we have the privilege to create symlinks
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except (ImportError, AttributeError):
        return False


def create_symlink(target_path: Path, link_path: Path, fallback_to_copy: bool = True) -> bool:
    """Create a symbolic link.
    
    Args:
        target_path: Path to the target file/directory
        link_path: Path where the symlink should be created
        fallback_to_copy: Whether to copy file if symlink creation fails
        
    Returns:
        True if successful (either symlink or copy), False otherwise
    """
    # Remove existing link/file if it exists
    if link_path.exists() or link_path.is_symlink():
        try:
            if link_path.is_dir() and not link_path.is_symlink():
                shutil.rmtree(link_path)
            else:
                link_path.unlink()
        except (PermissionError, OSError):
            return False
    
    # Calculate relative path from link to target
    try:
        relative_target = os.path.relpath(target_path, link_path.parent)
    except ValueError:
        # Can't create relative path (different drives on Windows)
        relative_target = str(target_path)
    
    # Try to create symbolic link
    try:
        link_path.symlink_to(relative_target)
        return True
    except (OSError, PermissionError, NotImplementedError):
        # Symlink creation failed
        if fallback_to_copy and target_path.exists():
            try:
                if target_path.is_file():
                    shutil.copy2(target_path, link_path)
                else:
                    shutil.copytree(target_path, link_path)
                return True
            except (PermissionError, OSError):
                pass
        return False


def create_claude_symlinks(
    project_path: Path, 
    pack_name: str, 
    command_name: str,
    fallback_to_copy: bool = True
) -> tuple[List[str], List[str]]:
    """Create symbolic links for Claude Code integration.
    
    Args:
        project_path: Path to the target project
        pack_name: Name of the expansion pack
        command_name: Claude command name
        fallback_to_copy: Whether to copy files if symlinks fail
        
    Returns:
        Tuple of (successful_links, failed_links)
    """
    successful_links = []
    failed_links = []
    
    # Get pack directory (hidden with dot prefix)
    pack_dir = project_path / format_pack_directory_name(pack_name)
    
    # Create Claude commands directory structure
    claude_base = project_path / '.claude' / 'commands' / command_name
    
    for file_type in ['agents', 'tasks']:
        source_dir = pack_dir / file_type
        target_dir = claude_base / file_type
        
        # Skip if source directory doesn't exist
        if not source_dir.exists():
            continue
        
        # Create target directory
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Create symlinks for all markdown files
        for md_file in source_dir.glob('*.md'):
            link_path = target_dir / md_file.name
            
            if create_symlink(md_file, link_path, fallback_to_copy):
                successful_links.append(f'{file_type}/{md_file.name}')
            else:
                failed_links.append(f'{file_type}/{md_file.name}')
    
    return successful_links, failed_links


def remove_claude_symlinks(project_path: Path, command_name: str) -> bool:
    """Remove Claude Code symbolic links for a command.
    
    Args:
        project_path: Path to the target project
        command_name: Claude command name
        
    Returns:
        True if successful, False if errors occurred
    """
    claude_dir = project_path / '.claude' / 'commands' / command_name
    
    if not claude_dir.exists():
        return True
    
    try:
        shutil.rmtree(claude_dir)
        return True
    except (PermissionError, OSError):
        return False


def verify_symlinks(
    project_path: Path, 
    pack_name: str, 
    command_name: str
) -> tuple[List[str], List[str]]:
    """Verify that symbolic links are working correctly.
    
    Args:
        project_path: Path to the target project
        pack_name: Name of the expansion pack
        command_name: Claude command name
        
    Returns:
        Tuple of (working_links, broken_links)
    """
    working_links = []
    broken_links = []
    
    claude_base = project_path / '.claude' / 'commands' / command_name
    
    for file_type in ['agents', 'tasks']:
        target_dir = claude_base / file_type
        
        if not target_dir.exists():
            continue
        
        for link_file in target_dir.glob('*.md'):
            if link_file.exists():
                # Check if it's a symlink and target exists
                if link_file.is_symlink():
                    try:
                        # Try to resolve the symlink
                        target = link_file.resolve()
                        if target.exists():
                            working_links.append(f'{file_type}/{link_file.name}')
                        else:
                            broken_links.append(f'{file_type}/{link_file.name}')
                    except (OSError, RuntimeError):
                        broken_links.append(f'{file_type}/{link_file.name}')
                elif link_file.is_file():
                    # It's a copied file (fallback), consider it working
                    working_links.append(f'{file_type}/{link_file.name} (copy)')
                else:
                    broken_links.append(f'{file_type}/{link_file.name}')
    
    return working_links, broken_links


def get_existing_claude_commands(project_path: Path) -> List[str]:
    """Get list of existing Claude command directories.
    
    Args:
        project_path: Path to the target project
        
    Returns:
        List of existing command names
    """
    claude_commands_dir = project_path / '.claude' / 'commands'
    
    if not claude_commands_dir.exists():
        return []
    
    try:
        return [
            item.name for item in claude_commands_dir.iterdir() 
            if item.is_dir() and not item.name.startswith('.')
        ]
    except (PermissionError, OSError):
        return []


def cleanup_broken_symlinks(project_path: Path, command_name: str) -> int:
    """Clean up broken symbolic links in Claude commands directory.
    
    Args:
        project_path: Path to the target project
        command_name: Claude command name
        
    Returns:
        Number of broken links removed
    """
    claude_dir = project_path / '.claude' / 'commands' / command_name
    
    if not claude_dir.exists():
        return 0
    
    removed_count = 0
    
    for file_type in ['agents', 'tasks']:
        target_dir = claude_dir / file_type
        
        if not target_dir.exists():
            continue
        
        for link_file in target_dir.glob('*'):
            if link_file.is_symlink():
                try:
                    # Check if symlink target exists
                    target = link_file.resolve()
                    if not target.exists():
                        link_file.unlink()
                        removed_count += 1
                except (OSError, RuntimeError):
                    # Broken symlink, remove it
                    try:
                        link_file.unlink()
                        removed_count += 1
                    except (PermissionError, OSError):
                        pass
    
    return removed_count