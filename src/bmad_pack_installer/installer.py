"""Main installation logic for BMAD expansion pack installer."""

import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass

from .validators import (
    is_bmad_project, 
    is_expansion_pack, 
    load_config, 
    load_exclusion_list,
    should_exclude,
    format_pack_name,
    format_pack_directory_name,
    validate_command_name
)
from .hash_utils import generate_files_manifest
from .manifest import (
    create_install_manifest,
    write_install_manifest,
    update_core_manifest,
    is_pack_installed,
    get_pack_manifest_path,
    select_key_files
)
from .symlink import create_claude_symlinks, can_create_symlinks


@dataclass
class InstallationResult:
    """Result of expansion pack installation."""
    success: bool
    pack_name: str
    pack_directory: str
    files_installed: int
    symlinks_created: List[str]
    symlinks_failed: List[str]
    message: str
    warnings: List[str]


class ExpansionPackInstaller:
    """Main installer class for BMAD expansion packs."""
    
    def __init__(self, source_path: Path, target_path: Path):
        """Initialize installer.
        
        Args:
            source_path: Path to expansion pack source directory
            target_path: Path to target BMAD project
        """
        self.source_path = source_path.resolve()
        self.target_path = target_path.resolve()
        self.warnings: List[str] = []
    
    def validate_installation(self, force: bool = False) -> Tuple[bool, str]:
        """Validate that installation can proceed.
        
        Args:
            force: Whether to force installation over existing pack
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check source directory
        if not self.source_path.exists():
            return False, f"Source directory does not exist: {self.source_path}"
        
        if not is_expansion_pack(self.source_path):
            return False, f"Source directory is not a valid BMAD expansion pack: {self.source_path}"
        
        # Check target directory
        if not self.target_path.exists():
            return False, f"Target directory does not exist: {self.target_path}"
        
        if not is_bmad_project(self.target_path):
            return False, f"Target directory is not a BMAD-enabled project: {self.target_path}"
        
        # Load config to get pack name
        try:
            config = load_config(self.source_path / 'config.yaml')
            pack_name = config['name']
            
            # Check if pack is already installed
            core_manifest_path = self.target_path / '.bmad-core' / 'install-manifest.yaml'
            if is_pack_installed(core_manifest_path, pack_name) and not force:
                formatted_name = format_pack_name(pack_name)
                return False, f"Expansion pack '{formatted_name}' is already installed. Use --force to reinstall."
        
        except Exception as e:
            return False, f"Failed to load pack configuration: {e}"
        
        return True, ""
    
    def copy_files(
        self, 
        pack_name: str, 
        exclusion_list: Set[str],
        dry_run: bool = False
    ) -> Tuple[Path, List[Dict[str, Any]]]:
        """Copy expansion pack files to target directory.
        
        Args:
            pack_name: Name of the pack
            exclusion_list: Set of exclusion patterns
            dry_run: Whether this is a dry run (don't actually copy)
            
        Returns:
            Tuple of (target_directory, files_data)
        """
        # Create hidden target directory
        target_dir = self.target_path / format_pack_directory_name(pack_name)
        
        if not dry_run:
            target_dir.mkdir(parents=True, exist_ok=True)
        
        files_data = []
        
        for source_file in self.source_path.rglob('*'):
            # Skip directories
            if source_file.is_dir():
                continue
            
            # Check exclusions
            if should_exclude(source_file, self.source_path, exclusion_list):
                continue
            
            # Calculate paths
            relative_path = source_file.relative_to(self.source_path)
            target_file = target_dir / relative_path
            
            if not dry_run:
                # Ensure target directory exists
                target_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                try:
                    shutil.copy2(source_file, target_file)
                except (PermissionError, OSError) as e:
                    self.warnings.append(f"Failed to copy {relative_path}: {e}")
                    continue
            
            # Add to files data with pack directory prefix
            pack_dir_name = format_pack_directory_name(pack_name)
            full_path = f"{pack_dir_name}/{relative_path}"
            
            files_data.append({
                'path': str(full_path),
                'hash': 'pending' if dry_run else 'will_calculate',
                'modified': False
            })
        
        # Calculate hashes for real installation
        if not dry_run and files_data:
            from .hash_utils import generate_file_hash
            for i, file_entry in enumerate(files_data):
                try:
                    file_path = self.target_path / file_entry['path']
                    file_hash = generate_file_hash(file_path)
                    files_data[i]['hash'] = file_hash
                except Exception as e:
                    self.warnings.append(f"Failed to hash {file_entry['path']}: {e}")
                    files_data[i]['hash'] = 'error'
        
        return target_dir, files_data
    
    def install(
        self,
        pack_name: Optional[str] = None,
        command_name: Optional[str] = None,
        ide: str = 'claude-code',
        skip_core_update: bool = False,
        skip_symlinks: bool = False,
        force: bool = False,
        dry_run: bool = False
    ) -> InstallationResult:
        """Install the expansion pack.
        
        Args:
            pack_name: Override pack name (uses config if None)
            command_name: Claude command name (uses config if None)
            ide: IDE to configure for (default: claude-code)
            skip_core_update: Skip updating core manifest
            skip_symlinks: Skip creating symbolic links
            force: Force installation over existing pack
            dry_run: Show what would be installed without doing it
            
        Returns:
            InstallationResult with installation details
        """
        try:
            # Validate installation
            is_valid, error_msg = self.validate_installation(force)
            if not is_valid:
                return InstallationResult(
                    success=False,
                    pack_name="",
                    pack_directory="",
                    files_installed=0,
                    symlinks_created=[],
                    symlinks_failed=[],
                    message=error_msg,
                    warnings=[]
                )
            
            # Load configuration
            config = load_config(self.source_path / 'config.yaml')
            
            # Determine pack name and command name
            final_pack_name = pack_name or config['name']
            final_command_name = command_name or config.get('slashPrefix', final_pack_name)
            
            # Validate command name
            if not validate_command_name(final_command_name):
                return InstallationResult(
                    success=False,
                    pack_name=final_pack_name,
                    pack_directory="",
                    files_installed=0,
                    symlinks_created=[],
                    symlinks_failed=[],
                    message=f"Invalid command name: {final_command_name}",
                    warnings=[]
                )
            
            # Load exclusion list
            exclusion_file = self.source_path / 'exclusion-list.txt'
            exclusion_list = load_exclusion_list(exclusion_file)
            
            if dry_run:
                return self._dry_run_install(
                    final_pack_name, 
                    final_command_name, 
                    config, 
                    exclusion_list
                )
            
            # Remove existing installation if force is enabled
            if force:
                self._remove_existing_installation(final_pack_name, final_command_name)
            
            # Phase 1: Copy files
            target_dir, files_data = self.copy_files(final_pack_name, exclusion_list)
            
            # Phase 2: Create pack install manifest
            pack_manifest_data = create_install_manifest(
                final_pack_name, 
                config, 
                files_data,
                [ide] if ide else ['claude-code']
            )
            
            pack_manifest_path = target_dir / 'install-manifest.yaml'
            write_install_manifest(pack_manifest_path, pack_manifest_data)
            
            # Phase 3: Update core manifest
            symlinks_created = []
            symlinks_failed = []
            
            if not skip_core_update:
                core_manifest_path = self.target_path / '.bmad-core' / 'install-manifest.yaml'
                key_files = select_key_files(files_data)
                update_core_manifest(core_manifest_path, final_pack_name, key_files)
            
            # Phase 4: Create symbolic links
            if not skip_symlinks and ide == 'claude-code':
                if can_create_symlinks():
                    symlinks_created, symlinks_failed = create_claude_symlinks(
                        self.target_path, 
                        final_pack_name, 
                        final_command_name
                    )
                else:
                    self.warnings.append("Cannot create symlinks on this system. Files were copied instead.")
                    symlinks_created, symlinks_failed = create_claude_symlinks(
                        self.target_path, 
                        final_pack_name, 
                        final_command_name,
                        fallback_to_copy=True
                    )
            
            formatted_pack_name = format_pack_name(final_pack_name)
            pack_dir_name = format_pack_directory_name(final_pack_name)
            
            return InstallationResult(
                success=True,
                pack_name=formatted_pack_name,
                pack_directory=str(pack_dir_name),
                files_installed=len(files_data),
                symlinks_created=symlinks_created,
                symlinks_failed=symlinks_failed,
                message=f"Successfully installed expansion pack '{formatted_pack_name}'",
                warnings=self.warnings
            )
            
        except Exception as e:
            return InstallationResult(
                success=False,
                pack_name=pack_name or "unknown",
                pack_directory="",
                files_installed=0,
                symlinks_created=[],
                symlinks_failed=[],
                message=f"Installation failed: {e}",
                warnings=self.warnings
            )
    
    def _dry_run_install(
        self, 
        pack_name: str, 
        command_name: str, 
        config: Dict[str, Any],
        exclusion_list: Set[str]
    ) -> InstallationResult:
        """Perform a dry run installation (show what would be done).
        
        Args:
            pack_name: Name of the pack
            command_name: Claude command name
            config: Pack configuration
            exclusion_list: Set of exclusion patterns
            
        Returns:
            InstallationResult with dry run details
        """
        target_dir, files_data = self.copy_files(pack_name, exclusion_list, dry_run=True)
        
        # Count potential symlinks
        agents_dir = self.source_path / 'agents'
        tasks_dir = self.source_path / 'tasks'
        
        potential_symlinks = []
        if agents_dir.exists():
            potential_symlinks.extend([f"agents/{f.name}" for f in agents_dir.glob('*.md')])
        if tasks_dir.exists():
            potential_symlinks.extend([f"tasks/{f.name}" for f in tasks_dir.glob('*.md')])
        
        formatted_pack_name = format_pack_name(pack_name)
        pack_dir_name = format_pack_directory_name(pack_name)
        
        message = (
            f"DRY RUN: Would install expansion pack '{formatted_pack_name}'\n"
            f"Target directory: {pack_dir_name}\n"
            f"Files to install: {len(files_data)}\n"
            f"Potential symlinks: {len(potential_symlinks)}\n"
            f"Command name: {command_name}"
        )
        
        return InstallationResult(
            success=True,
            pack_name=formatted_pack_name,
            pack_directory=str(pack_dir_name),
            files_installed=len(files_data),
            symlinks_created=potential_symlinks,
            symlinks_failed=[],
            message=message,
            warnings=self.warnings
        )
    
    def _remove_existing_installation(self, pack_name: str, command_name: str) -> None:
        """Remove existing installation if it exists.
        
        Args:
            pack_name: Name of the pack to remove
            command_name: Claude command name
        """
        # Remove pack directory
        pack_dir = self.target_path / format_pack_directory_name(pack_name)
        if pack_dir.exists():
            try:
                shutil.rmtree(pack_dir)
            except (PermissionError, OSError) as e:
                self.warnings.append(f"Failed to remove existing pack directory: {e}")
        
        # Remove Claude symlinks
        from .symlink import remove_claude_symlinks
        if not remove_claude_symlinks(self.target_path, command_name):
            self.warnings.append(f"Failed to remove existing Claude symlinks for '{command_name}'")
        
        # Note: We don't remove entries from core manifest as update_core_manifest
        # will handle duplicates gracefully


def install_expansion_pack(
    source_path: str,
    target_path: str,
    **kwargs
) -> InstallationResult:
    """Convenience function to install an expansion pack.
    
    Args:
        source_path: Path to expansion pack source
        target_path: Path to target BMAD project
        **kwargs: Additional arguments for installer
        
    Returns:
        InstallationResult
    """
    installer = ExpansionPackInstaller(
        Path(source_path),
        Path(target_path)
    )
    
    return installer.install(**kwargs)