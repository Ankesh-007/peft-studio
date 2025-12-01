"""
Settings and Preferences Service

Manages user settings including theme, notifications, default providers, and data retention.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Settings file path
SETTINGS_DIR = Path.home() / ".peft-studio" / "config"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"

# Default settings
DEFAULT_SETTINGS = {
    "appearance": {
        "theme": "dark",  # dark, light, auto
        "accentColor": "blue",  # blue, purple, green, orange
        "fontSize": "medium",  # small, medium, large
        "compactMode": False
    },
    "notifications": {
        "enabled": True,
        "trainingComplete": True,
        "trainingFailed": True,
        "deploymentReady": True,
        "systemUpdates": True,
        "soundEnabled": True,
        "desktopNotifications": True
    },
    "providers": {
        "defaultCompute": "local",  # local, runpod, lambda, vastai
        "defaultRegistry": "huggingface",  # huggingface, civitai, ollama
        "defaultTracker": None,  # wandb, cometml, phoenix, None
        "autoSelectCheapest": False,
        "preferredRegion": "us-east"
    },
    "dataRetention": {
        "keepLogs": 30,  # days
        "keepCheckpoints": 90,  # days
        "keepFailedRuns": 7,  # days
        "autoCleanup": True,
        "maxCacheSize": 10240  # MB (10GB)
    },
    "training": {
        "autoSaveCheckpoints": True,
        "checkpointInterval": 500,  # steps
        "enableTelemetry": False,
        "autoResume": True
    },
    "advanced": {
        "enableDebugMode": False,
        "logLevel": "INFO",  # DEBUG, INFO, WARNING, ERROR
        "maxConcurrentRuns": 3,
        "enableExperimentalFeatures": False
    }
}


class SettingsService:
    """Service for managing user settings and preferences"""
    
    def __init__(self):
        self.settings_file = SETTINGS_FILE
        self._ensure_settings_file()
        self._settings_cache = None
        self._last_modified = None
    
    def _ensure_settings_file(self):
        """Ensure settings directory and file exist"""
        SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        
        if not self.settings_file.exists():
            self._write_settings(DEFAULT_SETTINGS)
            logger.info("Created default settings file")
    
    def _read_settings(self) -> Dict[str, Any]:
        """Read settings from file with caching"""
        try:
            # Check if file was modified
            current_mtime = self.settings_file.stat().st_mtime
            
            if self._settings_cache is not None and self._last_modified == current_mtime:
                return self._settings_cache
            
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
            
            # Update cache
            self._settings_cache = settings
            self._last_modified = current_mtime
            
            return settings
        except Exception as e:
            logger.error(f"Error reading settings: {e}")
            return DEFAULT_SETTINGS.copy()
    
    def _write_settings(self, settings: Dict[str, Any]):
        """Write settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            
            # Invalidate cache
            self._settings_cache = None
            self._last_modified = None
            
            logger.info("Settings saved successfully")
        except Exception as e:
            logger.error(f"Error writing settings: {e}")
            raise
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings"""
        return self._read_settings()
    
    def get_setting(self, category: str, key: Optional[str] = None) -> Any:
        """
        Get a specific setting
        
        Args:
            category: Settings category (e.g., 'appearance', 'notifications')
            key: Optional specific key within category
        
        Returns:
            Setting value or entire category if key is None
        """
        settings = self._read_settings()
        
        if category not in settings:
            return None
        
        if key is None:
            return settings[category]
        
        return settings[category].get(key)
    
    def update_setting(self, category: str, key: str, value: Any) -> Dict[str, Any]:
        """
        Update a specific setting
        
        Args:
            category: Settings category
            key: Setting key
            value: New value
        
        Returns:
            Updated settings
        """
        settings = self._read_settings()
        
        if category not in settings:
            settings[category] = {}
        
        settings[category][key] = value
        self._write_settings(settings)
        
        return settings
    
    def update_category(self, category: str, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an entire category of settings
        
        Args:
            category: Settings category
            values: Dictionary of key-value pairs to update
        
        Returns:
            Updated settings
        """
        settings = self._read_settings()
        
        if category not in settings:
            settings[category] = {}
        
        settings[category].update(values)
        self._write_settings(settings)
        
        return settings
    
    def reset_to_defaults(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Reset settings to defaults
        
        Args:
            category: Optional category to reset. If None, resets all settings.
        
        Returns:
            Updated settings
        """
        if category is None:
            # Reset all settings
            self._write_settings(DEFAULT_SETTINGS.copy())
            return DEFAULT_SETTINGS.copy()
        else:
            # Reset specific category
            settings = self._read_settings()
            if category in DEFAULT_SETTINGS:
                settings[category] = DEFAULT_SETTINGS[category].copy()
                self._write_settings(settings)
            return settings
    
    def export_settings(self) -> str:
        """Export settings as JSON string"""
        settings = self._read_settings()
        return json.dumps(settings, indent=2)
    
    def import_settings(self, settings_json: str) -> Dict[str, Any]:
        """
        Import settings from JSON string
        
        Args:
            settings_json: JSON string containing settings
        
        Returns:
            Imported settings
        """
        try:
            settings = json.loads(settings_json)
            
            # Validate settings structure
            if not isinstance(settings, dict):
                raise ValueError("Settings must be a dictionary")
            
            # Merge with defaults to ensure all keys exist
            merged_settings = DEFAULT_SETTINGS.copy()
            for category, values in settings.items():
                if category in merged_settings:
                    merged_settings[category].update(values)
            
            self._write_settings(merged_settings)
            return merged_settings
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in settings import: {e}")
            raise ValueError("Invalid JSON format")
        except Exception as e:
            logger.error(f"Error importing settings: {e}")
            raise
    
    def get_cleanup_candidates(self) -> Dict[str, Any]:
        """
        Get files that can be cleaned up based on retention policies
        
        Returns:
            Dictionary with cleanup candidates
        """
        settings = self._read_settings()
        retention = settings.get("dataRetention", {})
        
        keep_logs = retention.get("keepLogs", 30)
        keep_checkpoints = retention.get("keepCheckpoints", 90)
        keep_failed = retention.get("keepFailedRuns", 7)
        
        cutoff_logs = datetime.now() - timedelta(days=keep_logs)
        cutoff_checkpoints = datetime.now() - timedelta(days=keep_checkpoints)
        cutoff_failed = datetime.now() - timedelta(days=keep_failed)
        
        return {
            "logs_before": cutoff_logs.isoformat(),
            "checkpoints_before": cutoff_checkpoints.isoformat(),
            "failed_runs_before": cutoff_failed.isoformat(),
            "auto_cleanup_enabled": retention.get("autoCleanup", True)
        }
    
    def validate_settings(self, settings: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate settings structure and values
        
        Args:
            settings: Settings dictionary to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check theme
            if "appearance" in settings:
                theme = settings["appearance"].get("theme")
                if theme and theme not in ["dark", "light", "auto"]:
                    return False, "Invalid theme value"
            
            # Check data retention values
            if "dataRetention" in settings:
                retention = settings["dataRetention"]
                for key in ["keepLogs", "keepCheckpoints", "keepFailedRuns"]:
                    if key in retention:
                        value = retention[key]
                        if not isinstance(value, int) or value < 0:
                            return False, f"Invalid {key} value: must be non-negative integer"
                
                if "maxCacheSize" in retention:
                    if not isinstance(retention["maxCacheSize"], int) or retention["maxCacheSize"] < 0:
                        return False, "Invalid maxCacheSize: must be non-negative integer"
            
            # Check advanced settings
            if "advanced" in settings:
                advanced = settings["advanced"]
                if "logLevel" in advanced:
                    if advanced["logLevel"] not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
                        return False, "Invalid log level"
                
                if "maxConcurrentRuns" in advanced:
                    if not isinstance(advanced["maxConcurrentRuns"], int) or advanced["maxConcurrentRuns"] < 1:
                        return False, "maxConcurrentRuns must be at least 1"
            
            return True, None
        except Exception as e:
            return False, str(e)


# Global instance
_settings_service = None


def get_settings_service() -> SettingsService:
    """Get or create settings service instance"""
    global _settings_service
    if _settings_service is None:
        _settings_service = SettingsService()
    return _settings_service
