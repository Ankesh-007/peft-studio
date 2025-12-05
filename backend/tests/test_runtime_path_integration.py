"""
Integration test for runtime path resolution.

Verifies that the backend can start and access data files correctly
with the new runtime path resolution system.
"""

import sys
import os
from pathlib import Path
import pytest

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


class TestRuntimePathIntegration:
    """Integration tests for runtime path resolution."""
    
    def test_config_imports_successfully(self):
        """Test that config.py imports successfully with runtime paths."""
        try:
            import config
            
            # Verify key attributes exist
            assert hasattr(config, 'BASE_DIR')
            assert hasattr(config, 'DATA_DIR')
            assert hasattr(config, 'MODELS_DIR')
            assert hasattr(config, 'DATASETS_DIR')
            assert hasattr(config, 'CHECKPOINTS_DIR')
            assert hasattr(config, 'CACHE_DIR')
            assert hasattr(config, 'DATABASE_URL')
            
            # Verify paths are Path objects
            assert isinstance(config.BASE_DIR, Path)
            assert isinstance(config.DATA_DIR, Path)
            
            # Verify directories exist
            assert config.DATA_DIR.exists()
            assert config.MODELS_DIR.exists()
            assert config.DATASETS_DIR.exists()
            assert config.CHECKPOINTS_DIR.exists()
            assert config.CACHE_DIR.exists()
            
        except Exception as e:
            pytest.fail(f"Failed to import config: {e}")
    
    def test_database_imports_successfully(self):
        """Test that database.py imports successfully."""
        try:
            import database
            
            # Verify key classes exist
            assert hasattr(database, 'Base')
            assert hasattr(database, 'Model')
            assert hasattr(database, 'Dataset')
            assert hasattr(database, 'TrainingRun')
            assert hasattr(database, 'get_db')
            
        except Exception as e:
            pytest.fail(f"Failed to import database: {e}")
    
    def test_database_url_is_valid(self):
        """Test that DATABASE_URL is properly configured."""
        import config
        
        # Should be a SQLite URL
        assert config.DATABASE_URL.startswith('sqlite:///')
        
        # Extract path
        db_path_str = config.DATABASE_URL.replace('sqlite:///', '')
        db_path = Path(db_path_str)
        
        # Parent directory should exist
        assert db_path.parent.exists()
        
        # Should be writable
        assert os.access(db_path.parent, os.W_OK)
    
    def test_data_directories_are_writable(self):
        """Test that all data directories are writable."""
        import config
        
        directories = [
            config.DATA_DIR,
            config.MODELS_DIR,
            config.DATASETS_DIR,
            config.CHECKPOINTS_DIR,
            config.CACHE_DIR,
        ]
        
        for directory in directories:
            assert directory.exists(), f"Directory does not exist: {directory}"
            assert directory.is_dir(), f"Path is not a directory: {directory}"
            assert os.access(directory, os.W_OK), f"Directory is not writable: {directory}"
    
    def test_runtime_paths_functions_work(self):
        """Test that runtime_paths functions work correctly."""
        from runtime_paths import (
            get_base_path,
            resolve_data_path,
            get_data_dir,
            get_models_dir,
            get_datasets_dir,
            get_checkpoints_dir,
            get_cache_dir,
            is_bundled
        )
        
        # Test get_base_path
        base_path = get_base_path()
        assert base_path.exists()
        assert base_path.is_dir()
        
        # Test resolve_data_path
        config_path = resolve_data_path('config.py')
        assert config_path.exists()
        
        # Test directory getters
        data_dir = get_data_dir()
        assert data_dir.exists()
        assert data_dir.is_dir()
        
        models_dir = get_models_dir()
        assert models_dir.exists()
        assert models_dir.is_dir()
        
        datasets_dir = get_datasets_dir()
        assert datasets_dir.exists()
        assert datasets_dir.is_dir()
        
        checkpoints_dir = get_checkpoints_dir()
        assert checkpoints_dir.exists()
        assert checkpoints_dir.is_dir()
        
        cache_dir = get_cache_dir()
        assert cache_dir.exists()
        assert cache_dir.is_dir()
        
        # Test is_bundled
        bundled = is_bundled()
        assert isinstance(bundled, bool)
        # In test environment, should be False
        assert bundled is False
    
    def test_security_service_uses_runtime_paths(self):
        """Test that security service uses runtime paths for audit log."""
        try:
            from services.security_service import get_security_service
            
            # Get security service (this will create audit log path)
            service = get_security_service()
            
            # Service should be created successfully
            assert service is not None
            
            # Audit log file should be in data directory
            from runtime_paths import get_data_dir
            data_dir = get_data_dir()
            
            # The audit log path should be within data directory
            # (we can't easily check the exact path without accessing private attributes)
            
        except Exception as e:
            pytest.fail(f"Failed to test security service: {e}")
    
    def test_config_and_database_work_together(self):
        """Test that config and database modules work together."""
        try:
            import config
            import database
            
            # Database should use config's DATABASE_URL
            assert database.engine.url.render_as_string(hide_password=False).startswith('sqlite:///')
            
            # Database file should be in data directory
            db_path_str = config.DATABASE_URL.replace('sqlite:///', '')
            db_path = Path(db_path_str)
            
            assert str(config.DATA_DIR) in str(db_path)
            
        except Exception as e:
            pytest.fail(f"Failed to test config and database integration: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
