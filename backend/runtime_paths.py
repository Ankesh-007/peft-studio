"""
Runtime path resolution for PyInstaller bundled executables.

This module provides utilities to resolve paths to data files and configuration
files when running as a bundled executable vs. running from source.

When PyInstaller bundles an application, it extracts files to a temporary directory
(sys._MEIPASS) at runtime. This module handles the path resolution transparently.
"""

import sys
import os
from pathlib import Path
from typing import Union


def get_base_path() -> Path:
    """
    Get the base path for the application.
    
    Returns:
        Path: The base directory path. When running as a bundled executable,
              this returns sys._MEIPASS. When running from source, this returns
              the directory containing this file.
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running as bundled executable
        return Path(sys._MEIPASS)
    else:
        # Running from source
        return Path(__file__).parent


def resolve_data_path(relative_path: Union[str, Path]) -> Path:
    """
    Resolve a relative path to a data file or configuration file.
    
    Args:
        relative_path: Path relative to the backend directory
        
    Returns:
        Path: Absolute path to the file, correctly resolved for both
              bundled and source execution modes
              
    Example:
        >>> config_path = resolve_data_path('config.py')
        >>> db_path = resolve_data_path('data/peft_studio.db')
    """
    base = get_base_path()
    return base / relative_path


def get_data_dir() -> Path:
    """
    Get the data directory path.
    
    For bundled executables, this returns a writable directory in the user's
    home directory. For source execution, this returns backend/data.
    
    Returns:
        Path: The data directory path
    """
    if getattr(sys, 'frozen', False):
        # Running as bundled executable - use user's home directory
        # This ensures we have write permissions
        app_data_dir = Path.home() / '.peft_studio' / 'data'
        app_data_dir.mkdir(parents=True, exist_ok=True)
        return app_data_dir
    else:
        # Running from source - use backend/data
        data_dir = Path(__file__).parent / 'data'
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir


def get_models_dir() -> Path:
    """Get the models directory path."""
    models_dir = get_data_dir() / 'models'
    models_dir.mkdir(parents=True, exist_ok=True)
    return models_dir


def get_datasets_dir() -> Path:
    """Get the datasets directory path."""
    datasets_dir = get_data_dir() / 'datasets'
    datasets_dir.mkdir(parents=True, exist_ok=True)
    return datasets_dir


def get_checkpoints_dir() -> Path:
    """Get the checkpoints directory path."""
    checkpoints_dir = get_data_dir() / 'checkpoints'
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    return checkpoints_dir


def get_cache_dir() -> Path:
    """Get the cache directory path."""
    cache_dir = get_data_dir() / 'cache'
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def is_bundled() -> bool:
    """
    Check if the application is running as a bundled executable.
    
    Returns:
        bool: True if running as bundled executable, False if running from source
    """
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
