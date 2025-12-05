"""
Build hooks for PyInstaller to detect all dependencies.

This module provides utilities to find all imports in the backend codebase,
including lazy-loaded modules, to ensure they are included in the PyInstaller bundle.
"""

import ast
import os
from pathlib import Path
from typing import Set, List


def find_all_imports(directory: str) -> Set[str]:
    """
    Recursively find all import statements in Python files.
    
    Args:
        directory: Root directory to search for Python files
        
    Returns:
        Set of module names that are imported
    """
    imports = set()
    
    for py_file in Path(directory).rglob('*.py'):
        # Skip this file itself
        if py_file.name == 'build_hooks.py':
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(py_file))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            # Get the top-level module name
                            module_name = alias.name.split('.')[0]
                            imports.add(module_name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            # Get the top-level module name
                            module_name = node.module.split('.')[0]
                            imports.add(module_name)
        except (SyntaxError, UnicodeDecodeError) as e:
            print(f"Warning: Could not parse {py_file}: {e}")
    
    return imports


def generate_hidden_imports() -> List[str]:
    """
    Generate list of hidden imports for PyInstaller.
    
    Filters out standard library modules and returns only third-party
    and local modules that need to be explicitly included.
    
    Returns:
        Sorted list of module names to include as hidden imports
    """
    backend_dir = Path(__file__).parent
    all_imports = find_all_imports(str(backend_dir))
    
    # Standard library modules to exclude (Python 3.10+)
    stdlib_modules = {
        'os', 'sys', 'json', 'logging', 'asyncio', 'typing', 'datetime',
        'pathlib', 'collections', 'functools', 'itertools', 'operator',
        'time', 'math', 're', 'random', 'string', 'io', 'tempfile',
        'shutil', 'subprocess', 'threading', 'multiprocessing', 'queue',
        'socket', 'ssl', 'http', 'urllib', 'email', 'base64', 'hashlib',
        'hmac', 'secrets', 'uuid', 'copy', 'pickle', 'shelve', 'dbm',
        'sqlite3', 'csv', 'configparser', 'argparse', 'getopt', 'warnings',
        'traceback', 'inspect', 'dis', 'ast', 'importlib', 'pkgutil',
        'zipfile', 'tarfile', 'gzip', 'bz2', 'lzma', 'zlib', 'enum',
        'dataclasses', 'abc', 'contextlib', 'weakref', 'gc', 'atexit',
        'signal', 'errno', 'ctypes', 'struct', 'array', 'heapq', 'bisect',
        'decimal', 'fractions', 'statistics', 'platform', 'glob', 'fnmatch',
        'linecache', 'tokenize', 'keyword', 'token', 'pydoc', 'doctest',
        'unittest', 'test', 'pdb', 'profile', 'pstats', 'timeit', 'trace',
        'cProfile', 'encodings', 'codecs', 'unicodedata', 'stringprep',
        'textwrap', 'difflib', 'calendar', 'locale', 'gettext'
    }
    
    # Filter out standard library modules
    hidden_imports = sorted([imp for imp in all_imports if imp not in stdlib_modules])
    
    return hidden_imports


def get_uvicorn_hidden_imports() -> List[str]:
    """
    Get all uvicorn-related hidden imports.
    
    Uvicorn uses dynamic imports that PyInstaller cannot detect automatically.
    
    Returns:
        List of uvicorn module names
    """
    return [
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.loops.asyncio',
        'uvicorn.loops.uvloop',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.http.httptools_impl',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.websockets.websockets_impl',
        'uvicorn.protocols.websockets.wsproto_impl',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        'uvicorn.middleware',
        'uvicorn.middleware.proxy_headers',
        'uvicorn.middleware.wsgi',
    ]


def get_service_hidden_imports() -> List[str]:
    """
    Get all service module hidden imports.
    
    Services are lazy-loaded in main.py, so PyInstaller won't detect them.
    
    Returns:
        List of service module names
    """
    services_dir = Path(__file__).parent / 'services'
    service_modules = []
    
    if services_dir.exists():
        for py_file in services_dir.glob('*.py'):
            if py_file.name != '__init__.py':
                module_name = f'services.{py_file.stem}'
                service_modules.append(module_name)
    
    return sorted(service_modules)


def get_connector_hidden_imports() -> List[str]:
    """
    Get all connector module hidden imports.
    
    Connectors may be dynamically loaded.
    
    Returns:
        List of connector module names
    """
    connector_modules = []
    
    # Core connectors
    connectors_dir = Path(__file__).parent / 'connectors'
    if connectors_dir.exists():
        for py_file in connectors_dir.glob('*.py'):
            if py_file.name != '__init__.py':
                module_name = f'connectors.{py_file.stem}'
                connector_modules.append(module_name)
    
    # Plugin connectors
    plugins_dir = Path(__file__).parent / 'plugins' / 'connectors'
    if plugins_dir.exists():
        for py_file in plugins_dir.glob('*.py'):
            if py_file.name != '__init__.py' and not py_file.name.startswith('.'):
                module_name = f'plugins.connectors.{py_file.stem}'
                connector_modules.append(module_name)
    
    return sorted(connector_modules)


def get_all_hidden_imports() -> List[str]:
    """
    Get complete list of all hidden imports needed for PyInstaller.
    
    Returns:
        Comprehensive list of all module names to include
    """
    hidden_imports = []
    
    # Add uvicorn imports
    hidden_imports.extend(get_uvicorn_hidden_imports())
    
    # Add service imports
    hidden_imports.extend(get_service_hidden_imports())
    
    # Add connector imports
    hidden_imports.extend(get_connector_hidden_imports())
    
    # Add other detected imports
    hidden_imports.extend(generate_hidden_imports())
    
    # Remove duplicates and sort
    return sorted(list(set(hidden_imports)))


if __name__ == '__main__':
    """Print all hidden imports for verification."""
    print("Detected hidden imports:")
    print("-" * 60)
    
    all_imports = get_all_hidden_imports()
    for imp in all_imports:
        print(f"  - {imp}")
    
    print("-" * 60)
    print(f"Total: {len(all_imports)} modules")
