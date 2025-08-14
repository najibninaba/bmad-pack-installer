"""Tests for manifest module."""

import pytest
import tempfile
import yaml
from pathlib import Path
from datetime import datetime

import sys
from pathlib import Path

# Add src to path for importing modules
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from bmad_pack_installer.manifest import (
    create_install_manifest,
    write_install_manifest,
    load_core_manifest,
    update_core_manifest,
    is_pack_installed,
    get_pack_manifest_path,
    select_key_files
)


class TestInstallManifestCreation:
    """Test install manifest creation."""
    
    def test_create_install_manifest_basic(self):
        """Test basic install manifest creation."""
        pack_name = "test-pack"
        config = {
            "name": "test-pack",
            "version": "1.2.3",
            "description": "Test pack"
        }
        files_data = [
            {"path": "config.yaml", "hash": "abc123", "modified": False},
            {"path": "agents/test.md", "hash": "def456", "modified": False}
        ]
        
        manifest = create_install_manifest(pack_name, config, files_data)
        
        assert manifest["version"] == "1.2.3"
        assert manifest["expansion_pack_id"] == "bmad-test-pack"
        assert manifest["expansion_pack_name"] == "bmad-test-pack"
        assert manifest["install_type"] == "expansion-pack"
        assert manifest["ides_setup"] == ["claude-code"]
        assert manifest["files"] == files_data
        assert "installed_at" in manifest
        
    def test_create_install_manifest_with_custom_ide(self):
        """Test manifest creation with custom IDE."""
        pack_name = "test-pack"
        config = {"name": "test-pack", "version": "1.0.0"}
        files_data = []
        ides_setup = ["cursor"]
        
        manifest = create_install_manifest(pack_name, config, files_data, ides_setup)
        
        assert manifest["ides_setup"] == ["cursor"]
        
    def test_create_install_manifest_adds_bmad_prefix(self):
        """Test that pack name gets bmad- prefix."""
        pack_name = "simple-pack"  # No bmad- prefix
        config = {"name": "simple-pack", "version": "1.0.0"}
        files_data = []
        
        manifest = create_install_manifest(pack_name, config, files_data)
        
        assert manifest["expansion_pack_id"] == "bmad-simple-pack"
        assert manifest["expansion_pack_name"] == "bmad-simple-pack"


class TestManifestFileOperations:
    """Test manifest file read/write operations."""
    
    def test_write_install_manifest(self):
        """Test writing install manifest to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "install-manifest.yaml"
            manifest_data = {
                "version": "1.0.0",
                "expansion_pack_id": "bmad-test-pack",
                "files": []
            }
            
            write_install_manifest(manifest_path, manifest_data)
            
            assert manifest_path.exists()
            
            # Verify content
            with open(manifest_path, 'r') as f:
                loaded_data = yaml.safe_load(f)
            
            assert loaded_data["version"] == "1.0.0"
            assert loaded_data["expansion_pack_id"] == "bmad-test-pack"
            
    def test_write_install_manifest_creates_directory(self):
        """Test that manifest writing creates parent directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "subdir" / "install-manifest.yaml"
            manifest_data = {"version": "1.0.0"}
            
            write_install_manifest(manifest_path, manifest_data)
            
            assert manifest_path.exists()
            assert manifest_path.parent.exists()
            
    def test_load_core_manifest_valid(self):
        """Test loading valid core manifest."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "install-manifest.yaml"
            
            manifest_data = {
                "expansion_packs": ["bmad-pack1", "bmad-pack2"],
                "files": []
            }
            
            with open(manifest_path, 'w') as f:
                yaml.dump(manifest_data, f)
                
            loaded_manifest = load_core_manifest(manifest_path)
            
            assert loaded_manifest["expansion_packs"] == ["bmad-pack1", "bmad-pack2"]
            assert loaded_manifest["files"] == []
            
    def test_load_core_manifest_nonexistent(self):
        """Test loading non-existent manifest raises FileNotFoundError."""
        nonexistent_path = Path("/nonexistent/manifest.yaml")
        
        with pytest.raises(FileNotFoundError):
            load_core_manifest(nonexistent_path)
            
    def test_load_core_manifest_empty_file(self):
        """Test loading empty manifest file returns empty dict."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")  # Empty file
            f.flush()
            
            manifest_path = Path(f.name)
            loaded_manifest = load_core_manifest(manifest_path)
            
            assert loaded_manifest == {}
            
            manifest_path.unlink()  # Clean up


class TestCoreManifestUpdates:
    """Test core manifest update functionality."""
    
    def test_update_core_manifest_new_pack(self):
        """Test updating core manifest with new pack."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "install-manifest.yaml"
            
            # Create initial manifest
            initial_data = {
                "expansion_packs": ["bmad-existing-pack"],
                "files": []
            }
            
            with open(manifest_path, 'w') as f:
                yaml.dump(initial_data, f)
            
            # Update with new pack
            pack_name = "new-pack"
            key_files = [
                {"path": ".bmad-new-pack/config.yaml", "hash": "abc123", "modified": False}
            ]
            
            update_core_manifest(manifest_path, pack_name, key_files, create_backup=False)
            
            # Verify update
            updated_manifest = load_core_manifest(manifest_path)
            
            assert "bmad-new-pack" in updated_manifest["expansion_packs"]
            assert "bmad-existing-pack" in updated_manifest["expansion_packs"]
            assert len(updated_manifest["files"]) == 1
            
    def test_update_core_manifest_duplicate_pack(self):
        """Test updating with pack that's already installed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "install-manifest.yaml"
            
            # Create manifest with existing pack
            initial_data = {
                "expansion_packs": ["bmad-test-pack"],
                "files": []
            }
            
            with open(manifest_path, 'w') as f:
                yaml.dump(initial_data, f)
            
            # Update with same pack (should not duplicate)
            pack_name = "test-pack"
            key_files = []
            
            update_core_manifest(manifest_path, pack_name, key_files, create_backup=False)
            
            # Verify no duplication
            updated_manifest = load_core_manifest(manifest_path)
            expansion_packs = updated_manifest["expansion_packs"]
            
            assert expansion_packs.count("bmad-test-pack") == 1
            
    def test_is_pack_installed_true(self):
        """Test detection of installed pack."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "install-manifest.yaml"
            
            manifest_data = {
                "expansion_packs": ["bmad-test-pack", "bmad-other-pack"]
            }
            
            with open(manifest_path, 'w') as f:
                yaml.dump(manifest_data, f)
                
            assert is_pack_installed(manifest_path, "test-pack") is True
            assert is_pack_installed(manifest_path, "bmad-test-pack") is True
            
    def test_is_pack_installed_false(self):
        """Test detection of non-installed pack."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "install-manifest.yaml"
            
            manifest_data = {
                "expansion_packs": ["bmad-other-pack"]
            }
            
            with open(manifest_path, 'w') as f:
                yaml.dump(manifest_data, f)
                
            assert is_pack_installed(manifest_path, "test-pack") is False
            
    def test_is_pack_installed_nonexistent_manifest(self):
        """Test pack detection with non-existent manifest returns False."""
        nonexistent_path = Path("/nonexistent/manifest.yaml")
        assert is_pack_installed(nonexistent_path, "any-pack") is False


class TestKeyFilesSelection:
    """Test key files selection for core manifest."""
    
    def test_select_key_files_prioritizes_important_files(self):
        """Test that important files are prioritized."""
        files_data = [
            {"path": "random.txt", "hash": "hash1", "modified": False},
            {"path": "config.yaml", "hash": "hash2", "modified": False},
            {"path": "agents/agent1.md", "hash": "hash3", "modified": False},
            {"path": "templates/template1.yaml", "hash": "hash4", "modified": False},
            {"path": "another.txt", "hash": "hash5", "modified": False}
        ]
        
        key_files = select_key_files(files_data, max_files=3)
        
        assert len(key_files) == 3
        
        # Config.yaml should be first
        assert key_files[0]["path"] == "config.yaml"
        
        # Agents and templates should be included
        paths = [f["path"] for f in key_files]
        assert "agents/agent1.md" in paths
        assert "templates/template1.yaml" in paths
        
    def test_select_key_files_respects_max_limit(self):
        """Test that max files limit is respected."""
        files_data = [
            {"path": f"file{i}.txt", "hash": f"hash{i}", "modified": False}
            for i in range(20)
        ]
        
        key_files = select_key_files(files_data, max_files=5)
        
        assert len(key_files) == 5
        
    def test_select_key_files_empty_list(self):
        """Test key files selection with empty input."""
        key_files = select_key_files([])
        assert key_files == []


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_get_pack_manifest_path(self):
        """Test pack manifest path generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            pack_name = "test-pack"
            
            manifest_path = get_pack_manifest_path(project_path, pack_name)
            
            expected_path = project_path / ".bmad-test-pack" / "install-manifest.yaml"
            assert manifest_path == expected_path