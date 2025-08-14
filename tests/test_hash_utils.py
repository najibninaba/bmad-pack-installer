"""Tests for hash_utils module."""

import pytest
import tempfile
from pathlib import Path

import sys
from pathlib import Path

# Add src to path for importing modules
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from bmad_pack_installer.hash_utils import (
    generate_file_hash,
    generate_files_manifest,
    verify_file_integrity
)


class TestFileHashing:
    """Test file hashing functionality."""
    
    def test_generate_file_hash(self):
        """Test file hash generation."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            f.flush()
            
            file_path = Path(f.name)
            hash_value = generate_file_hash(file_path)
            
            # Hash should be 16 characters (truncated SHA-256)
            assert len(hash_value) == 16
            assert hash_value.isalnum()
            
            # Same content should produce same hash
            hash_value2 = generate_file_hash(file_path)
            assert hash_value == hash_value2
            
            file_path.unlink()  # Clean up
            
    def test_generate_file_hash_nonexistent_file(self):
        """Test hash generation for non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            generate_file_hash(Path("/nonexistent/file.txt"))
            
    def test_generate_file_hash_different_content(self):
        """Test that different content produces different hashes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file1 = Path(temp_dir) / "file1.txt"
            file2 = Path(temp_dir) / "file2.txt"
            
            file1.write_text("content 1")
            file2.write_text("content 2")
            
            hash1 = generate_file_hash(file1)
            hash2 = generate_file_hash(file2)
            
            assert hash1 != hash2


class TestFilesManifest:
    """Test files manifest generation."""
    
    def test_generate_files_manifest(self):
        """Test manifest generation for multiple files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            
            # Create test files
            file1 = base_path / "file1.txt"
            file2 = base_path / "subdir" / "file2.txt"
            file2.parent.mkdir(parents=True)
            
            file1.write_text("content 1")
            file2.write_text("content 2")
            
            files = [file1, file2]
            manifest = generate_files_manifest(files, base_path)
            
            assert len(manifest) == 2
            
            # Check first file entry
            entry1 = manifest[0]
            assert entry1['path'] == 'file1.txt'
            assert len(entry1['hash']) == 16
            assert entry1['modified'] is False
            
            # Check second file entry
            entry2 = manifest[1]
            assert entry2['path'] == str(Path('subdir') / 'file2.txt')
            assert len(entry2['hash']) == 16
            assert entry2['modified'] is False
            
    def test_generate_files_manifest_empty_list(self):
        """Test manifest generation for empty file list."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            manifest = generate_files_manifest([], base_path)
            assert manifest == []
            
    def test_generate_files_manifest_with_nonexistent_file(self):
        """Test manifest generation handles non-existent files gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            
            # Create one valid file
            valid_file = base_path / "valid.txt"
            valid_file.write_text("valid content")
            
            # Include one non-existent file
            nonexistent_file = base_path / "nonexistent.txt"
            
            files = [valid_file, nonexistent_file]
            manifest = generate_files_manifest(files, base_path)
            
            # Should only include the valid file
            assert len(manifest) == 1
            assert manifest[0]['path'] == 'valid.txt'


class TestFileIntegrityVerification:
    """Test file integrity verification."""
    
    def test_verify_file_integrity_valid(self):
        """Test verification of valid file hash."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            f.flush()
            
            file_path = Path(f.name)
            expected_hash = generate_file_hash(file_path)
            
            # Verification should succeed
            assert verify_file_integrity(file_path, expected_hash) is True
            
            file_path.unlink()  # Clean up
            
    def test_verify_file_integrity_invalid(self):
        """Test verification with wrong hash fails."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            f.flush()
            
            file_path = Path(f.name)
            wrong_hash = "0000000000000000"  # Wrong hash
            
            # Verification should fail
            assert verify_file_integrity(file_path, wrong_hash) is False
            
            file_path.unlink()  # Clean up
            
    def test_verify_file_integrity_nonexistent_file(self):
        """Test verification of non-existent file returns False."""
        nonexistent_file = Path("/nonexistent/file.txt")
        fake_hash = "1234567890123456"
        
        assert verify_file_integrity(nonexistent_file, fake_hash) is False