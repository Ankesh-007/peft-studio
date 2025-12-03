"""
Tests for Settings Service and API

Verifies settings management including theme selection, notifications,
default providers, and data retention policies.
"""

import pytest
import json
from pathlib import Path
from services.settings_service import SettingsService, DEFAULT_SETTINGS


@pytest.fixture
def temp_settings_file(tmp_path):
    """Create a temporary settings file"""
    settings_file = tmp_path / "settings.json"
    return settings_file


@pytest.fixture
def settings_service(temp_settings_file):
    """Create a settings service with temporary file"""
    service = SettingsService()
    service.settings_file = temp_settings_file
    service._ensure_settings_file()
    return service


def test_default_settings_creation(settings_service):
    """Test that default settings are created"""
    settings = settings_service.get_all_settings()
    
    assert settings is not None
    assert 'appearance' in settings
    assert 'notifications' in settings
    assert 'providers' in settings
    assert 'dataRetention' in settings


def test_theme_selection(settings_service):
    """Test theme selection (dark/light/auto)"""
    # Test dark theme
    settings_service.update_setting('appearance', 'theme', 'dark')
    theme = settings_service.get_setting('appearance', 'theme')
    assert theme == 'dark'
    
    # Test light theme
    settings_service.update_setting('appearance', 'theme', 'light')
    theme = settings_service.get_setting('appearance', 'theme')
    assert theme == 'light'
    
    # Test auto theme
    settings_service.update_setting('appearance', 'theme', 'auto')
    theme = settings_service.get_setting('appearance', 'theme')
    assert theme == 'auto'


def test_notification_preferences(settings_service):
    """Test notification preferences"""
    # Enable all notifications
    settings_service.update_setting('notifications', 'enabled', True)
    settings_service.update_setting('notifications', 'trainingComplete', True)
    settings_service.update_setting('notifications', 'soundEnabled', True)
    
    notifications = settings_service.get_setting('notifications')
    assert notifications['enabled'] is True
    assert notifications['trainingComplete'] is True
    assert notifications['soundEnabled'] is True
    
    # Disable notifications
    settings_service.update_setting('notifications', 'enabled', False)
    enabled = settings_service.get_setting('notifications', 'enabled')
    assert enabled is False


def test_default_provider_settings(settings_service):
    """Test default provider settings"""
    # Set default compute provider
    settings_service.update_setting('providers', 'defaultCompute', 'runpod')
    compute = settings_service.get_setting('providers', 'defaultCompute')
    assert compute == 'runpod'
    
    # Set default registry
    settings_service.update_setting('providers', 'defaultRegistry', 'huggingface')
    registry = settings_service.get_setting('providers', 'defaultRegistry')
    assert registry == 'huggingface'
    
    # Set default tracker
    settings_service.update_setting('providers', 'defaultTracker', 'wandb')
    tracker = settings_service.get_setting('providers', 'defaultTracker')
    assert tracker == 'wandb'


def test_data_retention_policies(settings_service):
    """Test data retention policies"""
    # Set retention periods
    settings_service.update_setting('dataRetention', 'keepLogs', 30)
    settings_service.update_setting('dataRetention', 'keepCheckpoints', 90)
    settings_service.update_setting('dataRetention', 'keepFailedRuns', 7)
    settings_service.update_setting('dataRetention', 'autoCleanup', True)
    
    retention = settings_service.get_setting('dataRetention')
    assert retention['keepLogs'] == 30
    assert retention['keepCheckpoints'] == 90
    assert retention['keepFailedRuns'] == 7
    assert retention['autoCleanup'] is True


def test_update_category(settings_service):
    """Test updating an entire category"""
    new_appearance = {
        'theme': 'light',
        'accentColor': 'purple',
        'fontSize': 'large',
        'compactMode': True
    }
    
    settings_service.update_category('appearance', new_appearance)
    appearance = settings_service.get_setting('appearance')
    
    assert appearance['theme'] == 'light'
    assert appearance['accentColor'] == 'purple'
    assert appearance['fontSize'] == 'large'
    assert appearance['compactMode'] is True


def test_reset_to_defaults(settings_service):
    """Test resetting settings to defaults"""
    # Modify settings
    settings_service.update_setting('appearance', 'theme', 'light')
    settings_service.update_setting('notifications', 'enabled', False)
    
    # Reset appearance category
    settings_service.reset_to_defaults('appearance')
    appearance = settings_service.get_setting('appearance')
    assert appearance['theme'] == DEFAULT_SETTINGS['appearance']['theme']
    
    # Reset all settings
    settings_service.reset_to_defaults()
    settings = settings_service.get_all_settings()
    assert settings['appearance'] == DEFAULT_SETTINGS['appearance']
    assert settings['notifications'] == DEFAULT_SETTINGS['notifications']


def test_export_import_settings(settings_service):
    """Test exporting and importing settings"""
    # Modify settings
    settings_service.update_setting('appearance', 'theme', 'light')
    settings_service.update_setting('notifications', 'soundEnabled', False)
    
    # Export settings
    exported = settings_service.export_settings()
    assert exported is not None
    
    # Parse exported JSON
    exported_data = json.loads(exported)
    assert exported_data['appearance']['theme'] == 'light'
    assert exported_data['notifications']['soundEnabled'] is False
    
    # Reset settings
    settings_service.reset_to_defaults()
    
    # Import settings
    imported = settings_service.import_settings(exported)
    assert imported['appearance']['theme'] == 'light'
    assert imported['notifications']['soundEnabled'] is False


def test_settings_validation(settings_service):
    """Test settings validation"""
    # Valid settings
    valid_settings = {
        'appearance': {'theme': 'dark'},
        'dataRetention': {'keepLogs': 30, 'maxCacheSize': 5000}
    }
    is_valid, error = settings_service.validate_settings(valid_settings)
    assert is_valid is True
    assert error is None
    
    # Invalid theme
    invalid_theme = {
        'appearance': {'theme': 'invalid'}
    }
    is_valid, error = settings_service.validate_settings(invalid_theme)
    assert is_valid is False
    assert 'theme' in error.lower()
    
    # Invalid retention value
    invalid_retention = {
        'dataRetention': {'keepLogs': -5}
    }
    is_valid, error = settings_service.validate_settings(invalid_retention)
    assert is_valid is False


def test_cleanup_candidates(settings_service):
    """Test getting cleanup candidates based on retention policies"""
    settings_service.update_setting('dataRetention', 'keepLogs', 30)
    settings_service.update_setting('dataRetention', 'keepCheckpoints', 90)
    settings_service.update_setting('dataRetention', 'autoCleanup', True)
    
    candidates = settings_service.get_cleanup_candidates()
    
    assert 'logs_before' in candidates
    assert 'checkpoints_before' in candidates
    assert 'failed_runs_before' in candidates
    assert candidates['auto_cleanup_enabled'] is True


def test_settings_caching(settings_service):
    """Test that settings are cached properly"""
    # First read
    settings1 = settings_service.get_all_settings()
    
    # Second read (should use cache)
    settings2 = settings_service.get_all_settings()
    
    assert settings1 == settings2
    
    # Modify settings (should invalidate cache)
    settings_service.update_setting('appearance', 'theme', 'light')
    
    # Read again (should get updated value)
    settings3 = settings_service.get_all_settings()
    assert settings3['appearance']['theme'] == 'light'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
