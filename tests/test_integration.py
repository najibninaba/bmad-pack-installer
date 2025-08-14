"""Integration tests for BMAD pack installer."""

import pytest
import tempfile
import yaml
from pathlib import Path

import sys
from pathlib import Path

# Add src to path for importing modules
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from bmad_pack_installer.installer import ExpansionPackInstaller, install_expansion_pack


class TestExpansionPackInstallerIntegration:
    """Integration tests for the complete installation process."""
    
    def create_test_expansion_pack(self, pack_dir: Path):
        """Create a test expansion pack structure."""
        # Create config.yaml
        config = {
            "name": "test-pack",
            "version": "1.0.0",
            "description": "Test expansion pack",
            "slashPrefix": "testCmd"
        }
        
        config_file = pack_dir / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        # Create agents directory with test files
        agents_dir = pack_dir / "agents"
        agents_dir.mkdir()
        (agents_dir / "test-agent.md").write_text("# Test Agent\n\nTest agent content")
        
        # Create tasks directory with test files
        tasks_dir = pack_dir / "tasks"
        tasks_dir.mkdir()
        (tasks_dir / "test-task.md").write_text("# Test Task\n\nTest task content")
        
        # Create templates directory
        templates_dir = pack_dir / "templates"
        templates_dir.mkdir()
        (templates_dir / "test-template.yaml").write_text("name: test-template\n")
        
        # Create some additional files
        (pack_dir / "README.md").write_text("# Test Pack\n\nTest expansion pack")
        
        # Create exclusion list
        exclusion_file = pack_dir / "exclusion-list.txt"
        exclusion_file.write_text("temp.txt\n*.tmp\n")
        
        # Create file that should be excluded
        (pack_dir / "temp.txt").write_text("This should be excluded")
        
        return config
    
    def create_test_bmad_project(self, project_dir: Path):
        """Create a test BMAD project structure."""
        # Create .bmad-core directory
        bmad_core = project_dir / ".bmad-core"
        bmad_core.mkdir()
        
        # Create install-manifest.yaml
        core_manifest = {
            "expansion_packs": [],
            "files": []
        }
        
        manifest_file = bmad_core / "install-manifest.yaml"
        with open(manifest_file, 'w') as f:
            yaml.dump(core_manifest, f)
        
        # Create .claude/commands directory
        claude_commands = project_dir / ".claude" / "commands"
        claude_commands.mkdir(parents=True)
    
    def test_complete_installation_workflow(self):
        """Test the complete installation workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            
            # Create test expansion pack
            pack_dir = base_dir / "test-expansion-pack"
            pack_dir.mkdir()
            config = self.create_test_expansion_pack(pack_dir)
            
            # Create test BMAD project
            project_dir = base_dir / "test-project"
            project_dir.mkdir()
            self.create_test_bmad_project(project_dir)
            
            # Run installation
            result = install_expansion_pack(
                source_path=str(pack_dir),
                target_path=str(project_dir),
                dry_run=False
            )
            
            # Verify installation success
            assert result.success is True
            assert result.pack_name == "bmad-test-pack"
            assert result.files_installed > 0
            
            # Verify pack directory was created
            pack_install_dir = project_dir / ".bmad-test-pack"
            assert pack_install_dir.exists()
            assert (pack_install_dir / "config.yaml").exists()
            assert (pack_install_dir / "agents" / "test-agent.md").exists()
            assert (pack_install_dir / "tasks" / "test-task.md").exists()
            
            # Verify exclusions were respected
            assert not (pack_install_dir / "temp.txt").exists()
            
            # Verify install manifest was created
            pack_manifest = pack_install_dir / "install-manifest.yaml"
            assert pack_manifest.exists()
            
            with open(pack_manifest, 'r') as f:
                manifest_data = yaml.safe_load(f)
            
            assert manifest_data["expansion_pack_id"] == "bmad-test-pack"
            assert manifest_data["version"] == "1.0.0"
            assert len(manifest_data["files"]) > 0
            
            # Verify core manifest was updated
            core_manifest_path = project_dir / ".bmad-core" / "install-manifest.yaml"
            with open(core_manifest_path, 'r') as f:
                core_data = yaml.safe_load(f)
            
            assert "bmad-test-pack" in core_data["expansion_packs"]
            
            # Verify Claude symlinks were created
            claude_command_dir = project_dir / ".claude" / "commands" / "testCmd"
            assert claude_command_dir.exists()
            
            agents_link_dir = claude_command_dir / "agents"
            tasks_link_dir = claude_command_dir / "tasks"
            
            assert agents_link_dir.exists()
            assert tasks_link_dir.exists()
            assert (agents_link_dir / "test-agent.md").exists()
            assert (tasks_link_dir / "test-task.md").exists()
    
    def test_dry_run_installation(self):
        """Test dry run installation doesn't make changes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            
            # Create test expansion pack
            pack_dir = base_dir / "test-expansion-pack"
            pack_dir.mkdir()
            config = self.create_test_expansion_pack(pack_dir)
            
            # Create test BMAD project
            project_dir = base_dir / "test-project"
            project_dir.mkdir()
            self.create_test_bmad_project(project_dir)
            
            # Run dry run installation
            result = install_expansion_pack(
                source_path=str(pack_dir),
                target_path=str(project_dir),
                dry_run=True
            )
            
            # Verify dry run success
            assert result.success is True
            assert result.pack_name == "bmad-test-pack"
            assert result.files_installed > 0
            assert "DRY RUN" in result.message
            
            # Verify no actual changes were made
            pack_install_dir = project_dir / ".bmad-test-pack"
            assert not pack_install_dir.exists()
            
            # Verify core manifest wasn't changed
            core_manifest_path = project_dir / ".bmad-core" / "install-manifest.yaml"
            with open(core_manifest_path, 'r') as f:
                core_data = yaml.safe_load(f)
            
            assert core_data["expansion_packs"] == []
    
    def test_force_reinstallation(self):
        """Test force reinstallation over existing pack."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            
            # Create test expansion pack
            pack_dir = base_dir / "test-expansion-pack"
            pack_dir.mkdir()
            config = self.create_test_expansion_pack(pack_dir)
            
            # Create test BMAD project
            project_dir = base_dir / "test-project"
            project_dir.mkdir()
            self.create_test_bmad_project(project_dir)
            
            # First installation
            result1 = install_expansion_pack(
                source_path=str(pack_dir),
                target_path=str(project_dir)
            )
            assert result1.success is True
            
            # Second installation without force should fail
            result2 = install_expansion_pack(
                source_path=str(pack_dir),
                target_path=str(project_dir)
            )
            assert result2.success is False
            assert "already installed" in result2.message
            
            # Second installation with force should succeed
            result3 = install_expansion_pack(
                source_path=str(pack_dir),
                target_path=str(project_dir),
                force=True
            )
            assert result3.success is True
    
    def test_custom_pack_and_command_names(self):
        """Test installation with custom pack and command names."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            
            # Create test expansion pack
            pack_dir = base_dir / "test-expansion-pack"
            pack_dir.mkdir()
            config = self.create_test_expansion_pack(pack_dir)
            
            # Create test BMAD project
            project_dir = base_dir / "test-project"
            project_dir.mkdir()
            self.create_test_bmad_project(project_dir)
            
            # Run installation with custom names
            result = install_expansion_pack(
                source_path=str(pack_dir),
                target_path=str(project_dir),
                pack_name="custom-pack-name",
                command_name="customCmd"
            )
            
            # Verify installation success with custom names
            assert result.success is True
            assert result.pack_name == "bmad-custom-pack-name"
            
            # Verify custom pack directory was created
            pack_install_dir = project_dir / ".bmad-custom-pack-name"
            assert pack_install_dir.exists()
            
            # Verify custom command directory was created
            claude_command_dir = project_dir / ".claude" / "commands" / "customCmd"
            assert claude_command_dir.exists()
    
    def test_skip_options(self):
        """Test installation with skip options."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            
            # Create test expansion pack
            pack_dir = base_dir / "test-expansion-pack"
            pack_dir.mkdir()
            config = self.create_test_expansion_pack(pack_dir)
            
            # Create test BMAD project
            project_dir = base_dir / "test-project"
            project_dir.mkdir()
            self.create_test_bmad_project(project_dir)
            
            # Run installation with skip options
            result = install_expansion_pack(
                source_path=str(pack_dir),
                target_path=str(project_dir),
                skip_core_update=True,
                skip_symlinks=True
            )
            
            # Verify installation success
            assert result.success is True
            
            # Verify core manifest wasn't updated
            core_manifest_path = project_dir / ".bmad-core" / "install-manifest.yaml"
            with open(core_manifest_path, 'r') as f:
                core_data = yaml.safe_load(f)
            
            assert core_data["expansion_packs"] == []
            
            # Verify no Claude symlinks were created
            claude_command_dir = project_dir / ".claude" / "commands" / "testCmd"
            assert not claude_command_dir.exists()
    
    def test_invalid_source_pack(self):
        """Test installation with invalid source pack."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            
            # Create invalid expansion pack (no config.yaml)
            pack_dir = base_dir / "invalid-pack"
            pack_dir.mkdir()
            (pack_dir / "README.md").write_text("No config file")
            
            # Create test BMAD project
            project_dir = base_dir / "test-project"
            project_dir.mkdir()
            self.create_test_bmad_project(project_dir)
            
            # Run installation
            result = install_expansion_pack(
                source_path=str(pack_dir),
                target_path=str(project_dir)
            )
            
            # Verify installation failure
            assert result.success is False
            assert "not a valid BMAD expansion pack" in result.message
    
    def test_invalid_target_project(self):
        """Test installation with invalid target project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            
            # Create test expansion pack
            pack_dir = base_dir / "test-expansion-pack"
            pack_dir.mkdir()
            config = self.create_test_expansion_pack(pack_dir)
            
            # Create invalid BMAD project (no .bmad-core)
            project_dir = base_dir / "invalid-project"
            project_dir.mkdir()
            (project_dir / "README.md").write_text("Not a BMAD project")
            
            # Run installation
            result = install_expansion_pack(
                source_path=str(pack_dir),
                target_path=str(project_dir)
            )
            
            # Verify installation failure
            assert result.success is False
            assert "not a BMAD-enabled project" in result.message