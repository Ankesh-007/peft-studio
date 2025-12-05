"""
Property-based tests for data file bundling in PyInstaller executable.

Feature: python-backend-bundling, Property 7: Data File Bundling Completeness
Validates: Requirements 1.4

Tests that all data files and configuration files required by the backend at runtime
are included in the bundled executable and accessible.
"""

import sys
import os
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume
import pytest

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


# Test data: files that must be bundled
REQUIRED_DATA_FILES = [
    'config.py',
    'database.py',
    'runtime_paths.py',
]

# Test data: modules that use data files
DATA_FILE_MODULES = [
    'config',
    'database',
    'runtime_paths',
]


class TestDataFileBundling:
    """Test data file bundling completeness."""
    
    def test_required_data_files_exist_in_spec(self):
        """
        Test that all required data files are listed in the PyInstaller spec file.
        
        This ensures that the spec file is configured to bundle all necessary files.
        """
        spec_file = backend_path / 'peft_engine.spec'
        assert spec_file.exists(), "PyInstaller spec file not found"
        
        with open(spec_file, 'r') as f:
            spec_content = f.read()
        
        for data_file in REQUIRED_DATA_FILES:
            # Check if file is mentioned in datas list
            assert data_file in spec_content, \
                f"Required data file '{data_file}' not found in spec file"
    
    def test_runtime_paths_module_importable(self):
        """
        Test that the runtime_paths module can be imported.
        
        This is a critical module for path resolution in bundled executables.
        """
        try:
            import runtime_paths
            assert hasattr(runtime_paths, 'get_base_path')
            assert hasattr(runtime_paths, 'resolve_data_path')
            assert hasattr(runtime_paths, 'get_data_dir')
            assert hasattr(runtime_paths, 'is_bundled')
        except ImportError as e:
            pytest.fail(f"Failed to import runtime_paths: {e}")
    
    def test_config_uses_runtime_paths(self):
        """
        Test that config.py uses runtime_paths for path resolution.
        
        This ensures config.py will work correctly in bundled mode.
        """
        config_file = backend_path / 'config.py'
        assert config_file.exists(), "config.py not found"
        
        with open(config_file, 'r') as f:
            config_content = f.read()
        
        # Check that config imports runtime_paths
        assert 'from runtime_paths import' in config_content or 'import runtime_paths' in config_content, \
            "config.py does not import runtime_paths"
        
        # Check that config uses runtime path functions
        assert 'get_base_path' in config_content or 'get_data_dir' in config_content, \
            "config.py does not use runtime path resolution functions"
    
    def test_data_directories_created(self):
        """
        Test that data directories are created when modules are imported.
        
        This ensures the application can write data even in bundled mode.
        """
        import config
        
        # Check that directories are defined
        assert hasattr(config, 'DATA_DIR')
        assert hasattr(config, 'MODELS_DIR')
        assert hasattr(config, 'DATASETS_DIR')
        assert hasattr(config, 'CHECKPOINTS_DIR')
        assert hasattr(config, 'CACHE_DIR')
        
        # Check that directories are Path objects
        assert isinstance(config.DATA_DIR, Path)
        assert isinstance(config.MODELS_DIR, Path)
        assert isinstance(config.DATASETS_DIR, Path)
        assert isinstance(config.CHECKPOINTS_DIR, Path)
        assert isinstance(config.CACHE_DIR, Path)
    
    def test_database_url_uses_data_dir(self):
        """
        Test that DATABASE_URL uses the data directory.
        
        This ensures the database is stored in a writable location.
        """
        import config
        
        assert hasattr(config, 'DATABASE_URL')
        assert 'sqlite:///' in config.DATABASE_URL
        
        # Extract path from DATABASE_URL
        db_path_str = config.DATABASE_URL.replace('sqlite:///', '')
        db_path = Path(db_path_str)
        
        # Check that database path is within data directory
        assert str(config.DATA_DIR) in str(db_path), \
            f"Database path {db_path} is not within DATA_DIR {config.DATA_DIR}"
    
    # Feature: python-backend-bundling, Property 7: Data File Bundling Completeness
    # Validates: Requirements 1.4
    @given(
        data_file=st.sampled_from(REQUIRED_DATA_FILES)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_data_file_accessibility(self, data_file):
        """
        Property: For any required data file, when the backend is running,
        the file should be accessible via runtime path resolution.
        
        This property ensures that all data files are correctly bundled and
        accessible at runtime, regardless of whether running from source or
        as a bundled executable.
        """
        from runtime_paths import resolve_data_path, get_base_path
        
        # Resolve the data file path
        resolved_path = resolve_data_path(data_file)
        
        # The file should exist at the resolved path
        assert resolved_path.exists(), \
            f"Data file '{data_file}' not found at resolved path: {resolved_path}"
        
        # The file should be readable
        assert os.access(resolved_path, os.R_OK), \
            f"Data file '{data_file}' is not readable at: {resolved_path}"
        
        # For Python files, verify they can be imported
        if data_file.endswith('.py'):
            module_name = data_file[:-3]  # Remove .py extension
            try:
                __import__(module_name)
            except ImportError as e:
                pytest.fail(f"Failed to import module '{module_name}': {e}")
    
    # Feature: python-backend-bundling, Property 7: Data File Bundling Completeness
    # Validates: Requirements 1.4
    @given(
        module_name=st.sampled_from(DATA_FILE_MODULES)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_module_imports_successfully(self, module_name):
        """
        Property: For any module that uses data files, when imported,
        the module should load successfully without path errors.
        
        This property ensures that all modules can access their required
        data files correctly in both source and bundled modes.
        """
        try:
            # Import the module
            module = __import__(module_name)
            
            # Module should have been imported successfully
            assert module is not None
            
            # For config module, verify key attributes exist
            if module_name == 'config':
                assert hasattr(module, 'BASE_DIR')
                assert hasattr(module, 'DATA_DIR')
                assert hasattr(module, 'DATABASE_URL')
            
            # For database module, verify key classes exist
            elif module_name == 'database':
                assert hasattr(module, 'Base')
                assert hasattr(module, 'Model')
                assert hasattr(module, 'Dataset')
                assert hasattr(module, 'TrainingRun')
            
            # For runtime_paths module, verify key functions exist
            elif module_name == 'runtime_paths':
                assert hasattr(module, 'get_base_path')
                assert hasattr(module, 'resolve_data_path')
                assert hasattr(module, 'get_data_dir')
                assert hasattr(module, 'is_bundled')
                
        except ImportError as e:
            pytest.fail(f"Failed to import module '{module_name}': {e}")
        except Exception as e:
            pytest.fail(f"Error while testing module '{module_name}': {e}")
    
    # Feature: python-backend-bundling, Property 7: Data File Bundling Completeness
    # Validates: Requirements 1.4
    @given(
        dir_name=st.sampled_from(['data', 'models', 'datasets', 'checkpoints', 'cache'])
    )
    @settings(max_examples=100, deadline=None)
    def test_property_data_directories_writable(self, dir_name):
        """
        Property: For any data directory, when accessed via runtime_paths,
        the directory should exist and be writable.
        
        This property ensures that the application can write data files
        in both source and bundled modes.
        """
        from runtime_paths import get_data_dir, get_models_dir, get_datasets_dir, get_checkpoints_dir, get_cache_dir
        
        # Map directory names to getter functions
        dir_getters = {
            'data': get_data_dir,
            'models': get_models_dir,
            'datasets': get_datasets_dir,
            'checkpoints': get_checkpoints_dir,
            'cache': get_cache_dir,
        }
        
        # Get the directory path
        dir_path = dir_getters[dir_name]()
        
        # Directory should exist
        assert dir_path.exists(), \
            f"Directory '{dir_name}' does not exist at: {dir_path}"
        
        # Directory should be a directory
        assert dir_path.is_dir(), \
            f"Path '{dir_path}' is not a directory"
        
        # Directory should be writable
        assert os.access(dir_path, os.W_OK), \
            f"Directory '{dir_name}' is not writable at: {dir_path}"
        
        # Test that we can create a file in the directory
        test_file = dir_path / f'.test_write_{dir_name}.tmp'
        try:
            test_file.write_text('test')
            assert test_file.exists()
            test_file.unlink()  # Clean up
        except Exception as e:
            pytest.fail(f"Failed to write to directory '{dir_name}' at {dir_path}: {e}")
    
    def test_runtime_paths_bundled_detection(self):
        """
        Test that runtime_paths correctly detects bundled vs source mode.
        
        This is critical for correct path resolution.
        """
        from runtime_paths import is_bundled
        
        # When running tests from source, should return False
        bundled = is_bundled()
        assert isinstance(bundled, bool)
        
        # In test environment, we're running from source
        assert bundled is False, \
            "is_bundled() should return False when running from source"
    
    def test_runtime_paths_base_path_resolution(self):
        """
        Test that get_base_path returns a valid path.
        """
        from runtime_paths import get_base_path, is_bundled
        
        base_path = get_base_path()
        
        # Should return a Path object
        assert isinstance(base_path, Path)
        
        # Should exist
        assert base_path.exists(), f"Base path does not exist: {base_path}"
        
        # Should be a directory
        assert base_path.is_dir(), f"Base path is not a directory: {base_path}"
        
        # When running from source, should be the backend directory
        if not is_bundled():
            assert base_path == backend_path, \
                f"Base path {base_path} does not match backend path {backend_path}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
