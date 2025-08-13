"""Hash generation utilities for BMAD pack installer."""

import hashlib
from pathlib import Path
from typing import Dict, List


def generate_file_hash(file_path: Path) -> str:
    """Generate truncated SHA-256 hash (first 16 chars) for a file.
    
    Args:
        file_path: Path to the file to hash
        
    Returns:
        First 16 characters of SHA-256 hash
        
    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file can't be read
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256 = hashlib.sha256()
    
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
    except PermissionError as e:
        raise PermissionError(f"Cannot read file {file_path}: {e}")
    
    return sha256.hexdigest()[:16]


def generate_files_manifest(files: List[Path], base_path: Path) -> List[Dict[str, str]]:
    """Generate manifest entries for a list of files.
    
    Args:
        files: List of file paths to process
        base_path: Base path to calculate relative paths from
        
    Returns:
        List of manifest entries with path, hash, and modified status
    """
    manifest_entries = []
    
    for file_path in files:
        try:
            file_hash = generate_file_hash(file_path)
            relative_path = file_path.relative_to(base_path)
            
            manifest_entries.append({
                'path': str(relative_path),
                'hash': file_hash,
                'modified': False
            })
        except (FileNotFoundError, PermissionError) as e:
            # Log warning but continue processing other files
            print(f"Warning: Skipping file {file_path}: {e}")
            continue
    
    return manifest_entries


def verify_file_integrity(file_path: Path, expected_hash: str) -> bool:
    """Verify file integrity against expected hash.
    
    Args:
        file_path: Path to file to verify
        expected_hash: Expected hash (first 16 chars of SHA-256)
        
    Returns:
        True if hash matches, False otherwise
    """
    try:
        current_hash = generate_file_hash(file_path)
        return current_hash == expected_hash
    except (FileNotFoundError, PermissionError):
        return False