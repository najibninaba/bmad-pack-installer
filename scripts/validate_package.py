#!/usr/bin/env python3
"""Validation script for BMAD Pack Installer package.

This script validates that the package is ready for distribution by checking:
- All imports work correctly
- Entry points are accessible
- Version numbers are consistent
- Build succeeds without errors
"""

import sys
import subprocess
import importlib
from pathlib import Path

# Add src to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


def validate_imports():
    """Validate that all modules can be imported."""
    print("🔍 Validating imports...")
    
    modules_to_test = [
        "bmad_pack_installer.cli",
        "bmad_pack_installer.installer", 
        "bmad_pack_installer.validators",
        "bmad_pack_installer.hash_utils",
        "bmad_pack_installer.manifest",
        "bmad_pack_installer.symlink"
    ]
    
    for module_name in modules_to_test:
        try:
            importlib.import_module(module_name)
            print(f"  ✅ {module_name}")
        except ImportError as e:
            print(f"  ❌ {module_name}: {e}")
            return False
    
    return True


def validate_entry_points():
    """Validate that CLI entry points work."""
    print("🔍 Validating entry points...")
    
    try:
        # Test importing the CLI
        from bmad_pack_installer.cli import cli
        print("  ✅ CLI function imported successfully")
        
        # Test that CLI can be invoked (help command)
        # This is tricky because click CLI will try to exit, so we just check import
        print("  ✅ CLI entry point accessible")
        return True
        
    except Exception as e:
        print(f"  ❌ CLI entry point failed: {e}")
        return False


def validate_version_consistency():
    """Validate that version numbers are consistent across files."""
    print("🔍 Validating version consistency...")
    
    # Get version from __init__.py
    try:
        from bmad_pack_installer import __version__
        init_version = __version__
        print(f"  📦 __init__.py version: {init_version}")
    except ImportError as e:
        print(f"  ❌ Could not import version from __init__.py: {e}")
        return False
    
    # Get version from pyproject.toml
    import toml
    project_root = Path(__file__).parent.parent
    pyproject_path = project_root / "pyproject.toml"
    
    try:
        with open(pyproject_path, 'r') as f:
            pyproject_data = toml.load(f)
        
        toml_version = pyproject_data['project']['version']
        print(f"  📦 pyproject.toml version: {toml_version}")
        
        if init_version == toml_version:
            print("  ✅ Version numbers are consistent")
            return True
        else:
            print(f"  ❌ Version mismatch: {init_version} != {toml_version}")
            return False
            
    except Exception as e:
        print(f"  ❌ Could not read pyproject.toml: {e}")
        return False


def validate_build():
    """Validate that the package can be built."""
    print("🔍 Validating package build...")
    
    project_root = Path(__file__).parent.parent
    
    try:
        # Clean previous builds
        dist_dir = project_root / "dist"
        if dist_dir.exists():
            import shutil
            shutil.rmtree(dist_dir)
            print("  🧹 Cleaned previous builds")
        
        # Run build
        result = subprocess.run(
            [sys.executable, "-m", "build"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("  ✅ Package build succeeded")
            
            # Check that distribution files were created
            dist_files = list(dist_dir.glob("*"))
            if dist_files:
                print(f"  📦 Created {len(dist_files)} distribution files:")
                for file in dist_files:
                    print(f"    - {file.name}")
                return True
            else:
                print("  ❌ No distribution files created")
                return False
        else:
            print(f"  ❌ Build failed with return code {result.returncode}")
            print(f"  stderr: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  ❌ Build validation failed: {e}")
        return False


def validate_tests():
    """Validate that tests can run."""
    print("🔍 Validating tests...")
    
    project_root = Path(__file__).parent.parent
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--tb=short", "-v"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("  ✅ All tests passed")
            return True
        else:
            print(f"  ❌ Tests failed with return code {result.returncode}")
            print("  Test output:")
            print(result.stdout[-1000:])  # Show last 1000 chars
            return False
            
    except Exception as e:
        print(f"  ❌ Test validation failed: {e}")
        return False


def main():
    """Run all validations."""
    print("🚀 BMAD Pack Installer - Package Validation")
    print("=" * 50)
    
    validations = [
        ("Imports", validate_imports),
        ("Entry Points", validate_entry_points), 
        ("Version Consistency", validate_version_consistency),
        ("Tests", validate_tests),
        ("Build", validate_build),
    ]
    
    all_passed = True
    results = []
    
    for name, validation_func in validations:
        print(f"\n{name}:")
        try:
            passed = validation_func()
            results.append((name, passed))
            all_passed = all_passed and passed
        except Exception as e:
            print(f"  ❌ Validation '{name}' crashed: {e}")
            results.append((name, False))
            all_passed = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name:<20} {status}")
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("📦 Package is ready for distribution")
        print("\nNext steps for TestPyPI:")
        print("  1. uv run python -m build")
        print("  2. uv run python -m twine upload --repository testpypi dist/*")
        print("  3. pip install -i https://test.pypi.org/simple/ bmad-pack-installer")
        return 0
    else:
        print("💥 SOME VALIDATIONS FAILED!")
        print("Please fix the issues before proceeding with distribution.")
        return 1


if __name__ == "__main__":
    sys.exit(main())