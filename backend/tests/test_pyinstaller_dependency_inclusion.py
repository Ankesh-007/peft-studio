"""
Property-based tests for PyInstaller dependency inclusion.

Feature: python-backend-bundling, Property 1: Dependency Inclusion Completeness

This test validates that all Python modules imported in the backend code
(including lazy-loaded modules) are correctly detected and included in the
PyInstaller hidden imports list.

Validates: Requirements 1.2, 1.5, 7.1, 7.3
"""

import ast
import sys
from pathlib import Path
from typing import Set, List
import pytest
from hypothesis import given, strategies as st, settings, assume

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from build_hooks import (
    find_all_imports,
    get_all_hidden_imports,
    get_uvicorn_hidden_imports,
    get_service_hidden_imports,
    get_connector_hidden_imports,
)


def get_all_python_files(directory: Path) -> List[Path]:
    """Get all Python files in the backend directory."""
    python_files = []
    for py_file in directory.rglob('*.py'):
        # Skip test files and build hooks itself
        if 'tests' not in py_file.parts and py_file.name != 'build_hooks.py':
            python_files.append(py_file)
    return python_files


def extract_imports_from_file(file_path: Path) -> Set[str]:
    """Extract all import statements from a Python file."""
    imports = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)
    except (SyntaxError, UnicodeDecodeError):
        pass
    
    return imports


def is_third_party_or_local(module_name: str) -> bool:
    """
    Check if a module is third-party or local (not stdlib).
    
    This is a heuristic check - we consider modules that are:
    - In our local packages (services, connectors, plugins)
    - Common third-party packages
    """
    # Local modules
    if module_name.startswith(('services', 'connectors', 'plugins', 'backend')):
        return True
    
    # Known third-party packages used in the project
    third_party = {
        'fastapi', 'uvicorn', 'pydantic', 'torch', 'transformers', 'peft',
        'accelerate', 'bitsandbytes', 'datasets', 'evaluate', 'pandas',
        'numpy', 'sklearn', 'aiofiles', 'aiohttp', 'sqlalchemy',
        'huggingface_hub', 'psutil', 'pynvml', 'GPUtil', 'pytest',
        'hypothesis', 'unsloth', 'trl', 'semver', 'wandb', 'keyring',
        'cryptography', 'paramiko', 'scp', 'starlette', 'requests',
    }
    
    module_root = module_name.split('.')[0]
    return module_root in third_party


# Feature: python-backend-bundling, Property 1: Dependency Inclusion Completeness
@pytest.mark.parametrize("python_file", get_all_python_files(backend_dir))
def test_all_imports_included_in_hidden_imports(python_file):
    """
    Property: For any Python module imported in the backend code,
    the module should be included in the PyInstaller hidden imports list.
    
    This ensures that all dependencies, including lazy-loaded ones,
    are bundled with the executable.
    """
    # Get all hidden imports from build_hooks
    hidden_imports = set(get_all_hidden_imports())
    
    # Extract imports from the file
    file_imports = extract_imports_from_file(python_file)
    
    # Check each import
    for imported_module in file_imports:
        # Skip stdlib modules (they're automatically included)
        if not is_third_party_or_local(imported_module):
            continue
        
        # Check if the module or its root is in hidden imports
        module_root = imported_module.split('.')[0]
        full_module_in_hidden = imported_module in hidden_imports
        root_module_in_hidden = module_root in hidden_imports
        
        # At least the root module should be in hidden imports
        assert full_module_in_hidden or root_module_in_hidden, (
            f"Module '{imported_module}' from {python_file.relative_to(backend_dir)} "
            f"is not in hidden imports. Neither '{imported_module}' nor '{module_root}' found."
        )


def test_uvicorn_imports_are_comprehensive():
    """
    Test that all critical uvicorn submodules are included.
    
    Uvicorn uses dynamic imports that PyInstaller cannot detect,
    so we must explicitly include them.
    """
    uvicorn_imports = get_uvicorn_hidden_imports()
    
    # Critical uvicorn modules that must be present
    critical_modules = [
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops.auto',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan.on',
    ]
    
    for module in critical_modules:
        assert module in uvicorn_imports, (
            f"Critical uvicorn module '{module}' not in hidden imports"
        )


def test_all_service_modules_included():
    """
    Test that all service modules are included in hidden imports.
    
    Services are lazy-loaded in main.py, so PyInstaller won't detect them
    automatically. We must explicitly include all service modules.
    """
    service_imports = get_service_hidden_imports()
    services_dir = backend_dir / 'services'
    
    # Get all Python files in services directory
    service_files = [
        f for f in services_dir.glob('*.py')
        if f.name != '__init__.py'
    ]
    
    for service_file in service_files:
        expected_module = f'services.{service_file.stem}'
        assert expected_module in service_imports, (
            f"Service module '{expected_module}' not in hidden imports"
        )


def test_all_connector_modules_included():
    """
    Test that all connector modules are included in hidden imports.
    
    Connectors may be dynamically loaded, so we must explicitly include them.
    """
    connector_imports = get_connector_hidden_imports()
    
    # Check core connectors
    connectors_dir = backend_dir / 'connectors'
    if connectors_dir.exists():
        connector_files = [
            f for f in connectors_dir.glob('*.py')
            if f.name != '__init__.py'
        ]
        
        for connector_file in connector_files:
            expected_module = f'connectors.{connector_file.stem}'
            assert expected_module in connector_imports, (
                f"Connector module '{expected_module}' not in hidden imports"
            )
    
    # Check plugin connectors
    plugins_dir = backend_dir / 'plugins' / 'connectors'
    if plugins_dir.exists():
        plugin_files = [
            f for f in plugins_dir.glob('*.py')
            if f.name != '__init__.py' and not f.name.startswith('.')
        ]
        
        for plugin_file in plugin_files:
            expected_module = f'plugins.connectors.{plugin_file.stem}'
            assert expected_module in connector_imports, (
                f"Plugin connector module '{expected_module}' not in hidden imports"
            )


def test_no_duplicate_hidden_imports():
    """
    Test that there are no duplicate entries in hidden imports.
    
    Duplicates waste space and can cause confusion.
    """
    hidden_imports = get_all_hidden_imports()
    
    # Check for duplicates
    seen = set()
    duplicates = []
    
    for module in hidden_imports:
        if module in seen:
            duplicates.append(module)
        seen.add(module)
    
    assert len(duplicates) == 0, (
        f"Found duplicate hidden imports: {duplicates}"
    )


def test_hidden_imports_are_sorted():
    """
    Test that hidden imports are sorted alphabetically.
    
    This makes the list easier to review and maintain.
    """
    hidden_imports = get_all_hidden_imports()
    
    assert hidden_imports == sorted(hidden_imports), (
        "Hidden imports are not sorted alphabetically"
    )


# Feature: python-backend-bundling, Property 1: Dependency Inclusion Completeness
@given(st.sampled_from(get_all_python_files(backend_dir)))
@settings(max_examples=100, deadline=None)
def test_property_all_imports_detected(python_file):
    """
    Property-based test: For any Python file in the backend,
    all its third-party and local imports should be detectable
    by the build_hooks module.
    
    This is a generative test that samples random Python files
    and verifies the import detection works correctly.
    """
    # Get all imports from the file
    file_imports = extract_imports_from_file(python_file)
    
    # Get all detected imports
    all_detected = set(find_all_imports(str(backend_dir)))
    
    # Check each third-party/local import
    for imported_module in file_imports:
        if not is_third_party_or_local(imported_module):
            continue
        
        module_root = imported_module.split('.')[0]
        
        # The root module should be detected
        assert module_root in all_detected, (
            f"Import '{imported_module}' from {python_file.name} "
            f"not detected by find_all_imports()"
        )


def test_critical_dependencies_included():
    """
    Test that critical dependencies are explicitly included.
    
    These are the core packages that the application cannot run without.
    """
    hidden_imports = set(get_all_hidden_imports())
    
    critical_deps = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'sqlalchemy',
        'torch',
        'transformers',
        'peft',
    ]
    
    for dep in critical_deps:
        assert dep in hidden_imports, (
            f"Critical dependency '{dep}' not in hidden imports"
        )


def test_lazy_loaded_services_included():
    """
    Test that lazy-loaded services from main.py are included.
    
    The main.py file uses lazy loading for heavy services,
    which PyInstaller cannot detect automatically.
    """
    hidden_imports = set(get_all_hidden_imports())
    
    # Services that are lazy-loaded in main.py
    lazy_loaded = [
        'services.peft_service',
        'services.hardware_service',
        'services.model_registry_service',
        'services.smart_config_service',
        'services.profile_service',
        'services.monitoring_service',
        'services.inference_service',
        'services.offline_queue_service',
        'services.network_service',
        'services.sync_engine',
    ]
    
    for service in lazy_loaded:
        assert service in hidden_imports, (
            f"Lazy-loaded service '{service}' not in hidden imports"
        )
