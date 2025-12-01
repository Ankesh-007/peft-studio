"""
Lazy Import Module for Heavy ML Libraries

This module provides lazy loading of heavy ML libraries (torch, transformers, peft)
to reduce startup memory usage. Libraries are only imported when actually needed.

This helps meet the memory usage constraint in Requirements 14.1 and 14.4:
- Idle memory usage should be under 200MB
- Libraries like PyTorch can consume 200-300MB just by being imported
"""

import sys
from typing import Any, Optional
import importlib


class LazyModule:
    """
    A lazy module loader that defers import until first access.
    
    This allows us to declare imports at the top of files without
    actually loading the heavy libraries until they're needed.
    """
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self._module: Optional[Any] = None
    
    def _load(self):
        """Load the module if not already loaded"""
        if self._module is None:
            self._module = importlib.import_module(self.module_name)
        return self._module
    
    def __getattr__(self, name: str):
        """Lazy load the module and return the requested attribute"""
        module = self._load()
        return getattr(module, name)
    
    def __dir__(self):
        """Return the module's attributes"""
        module = self._load()
        return dir(module)


class LazyImporter:
    """
    Manages lazy imports for heavy ML libraries.
    
    Usage:
        from services.lazy_imports import lazy_torch, lazy_transformers
        
        # These don't actually import anything yet
        torch = lazy_torch()
        transformers = lazy_transformers()
        
        # Import happens here on first use
        device = torch.device('cuda')
        model = transformers.AutoModelForCausalLM.from_pretrained(...)
    """
    
    _instances = {}
    
    @classmethod
    def get_lazy_module(cls, module_name: str) -> LazyModule:
        """Get or create a lazy module instance"""
        if module_name not in cls._instances:
            cls._instances[module_name] = LazyModule(module_name)
        return cls._instances[module_name]
    
    @classmethod
    def is_loaded(cls, module_name: str) -> bool:
        """Check if a module has been loaded"""
        if module_name not in cls._instances:
            return False
        return cls._instances[module_name]._module is not None
    
    @classmethod
    def unload_all(cls):
        """Unload all lazy modules (for testing)"""
        for instance in cls._instances.values():
            if instance._module is not None:
                # Remove from sys.modules to force reimport
                if instance.module_name in sys.modules:
                    del sys.modules[instance.module_name]
                instance._module = None


# Convenience functions for common heavy libraries
def lazy_torch():
    """Get lazy torch module"""
    return LazyImporter.get_lazy_module('torch')


def lazy_transformers():
    """Get lazy transformers module"""
    return LazyImporter.get_lazy_module('transformers')


def lazy_peft():
    """Get lazy peft module"""
    return LazyImporter.get_lazy_module('peft')


def lazy_datasets():
    """Get lazy datasets module"""
    return LazyImporter.get_lazy_module('datasets')


def lazy_trl():
    """Get lazy trl module"""
    return LazyImporter.get_lazy_module('trl')


# Check if heavy libraries are loaded
def are_ml_libraries_loaded() -> dict:
    """
    Check which ML libraries are currently loaded.
    
    Returns:
        dict: Status of each library (loaded/not loaded)
    """
    return {
        'torch': LazyImporter.is_loaded('torch'),
        'transformers': LazyImporter.is_loaded('transformers'),
        'peft': LazyImporter.is_loaded('peft'),
        'datasets': LazyImporter.is_loaded('datasets'),
        'trl': LazyImporter.is_loaded('trl'),
    }


def get_memory_usage_mb() -> float:
    """
    Get current process memory usage in MB.
    
    Returns:
        float: Memory usage in megabytes
    """
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


if __name__ == "__main__":
    # Demo: Show memory usage before and after loading libraries
    import time
    
    print("=== Lazy Import Demo ===\n")
    
    print(f"Initial memory: {get_memory_usage_mb():.1f}MB")
    print(f"Libraries loaded: {are_ml_libraries_loaded()}\n")
    
    # Create lazy imports (doesn't load anything)
    print("Creating lazy imports...")
    torch = lazy_torch()
    transformers = lazy_transformers()
    print(f"Memory after lazy import: {get_memory_usage_mb():.1f}MB")
    print(f"Libraries loaded: {are_ml_libraries_loaded()}\n")
    
    # Actually use torch (triggers import)
    print("Using torch.cuda.is_available()...")
    is_cuda = torch.cuda.is_available()
    print(f"CUDA available: {is_cuda}")
    print(f"Memory after torch import: {get_memory_usage_mb():.1f}MB")
    print(f"Libraries loaded: {are_ml_libraries_loaded()}\n")
    
    # Use transformers (triggers import)
    print("Accessing transformers.AutoModel...")
    _ = transformers.AutoModel
    print(f"Memory after transformers import: {get_memory_usage_mb():.1f}MB")
    print(f"Libraries loaded: {are_ml_libraries_loaded()}\n")
