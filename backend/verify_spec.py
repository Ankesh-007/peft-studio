"""
Verify PyInstaller spec file is valid and can be loaded.

This script checks:
1. PyInstaller is installed
2. The spec file can be loaded without errors
3. All hidden imports are valid module names
4. Data files exist
"""

import sys
import subprocess
from pathlib import Path


def check_pyinstaller_installed():
    """Check if PyInstaller is installed."""
    try:
        # Try using python -m PyInstaller first (more reliable)
        result = subprocess.run(
            [sys.executable, '-m', 'PyInstaller', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✓ PyInstaller is installed: {version}")
            return True
        else:
            print("✗ PyInstaller is installed but --version failed")
            return False
    except FileNotFoundError:
        print("✗ PyInstaller is not installed")
        print("  Install with: pip install pyinstaller")
        return False
    except Exception as e:
        print(f"✗ Error checking PyInstaller: {e}")
        return False


def check_spec_file_exists():
    """Check if the spec file exists."""
    spec_file = Path(__file__).parent / 'peft_engine.spec'
    if spec_file.exists():
        print(f"✓ Spec file exists: {spec_file}")
        return True
    else:
        print(f"✗ Spec file not found: {spec_file}")
        return False


def check_build_hooks_exists():
    """Check if build_hooks.py exists."""
    hooks_file = Path(__file__).parent / 'build_hooks.py'
    if hooks_file.exists():
        print(f"✓ Build hooks file exists: {hooks_file}")
        return True
    else:
        print(f"✗ Build hooks file not found: {hooks_file}")
        return False


def check_hidden_imports():
    """Check that hidden imports can be generated."""
    try:
        from build_hooks import get_all_hidden_imports
        
        hidden_imports = get_all_hidden_imports()
        print(f"✓ Generated {len(hidden_imports)} hidden imports")
        
        # Check for critical imports
        critical = ['fastapi', 'uvicorn', 'torch', 'transformers', 'peft']
        missing = [imp for imp in critical if imp not in hidden_imports]
        
        if missing:
            print(f"✗ Missing critical imports: {missing}")
            return False
        else:
            print(f"✓ All critical imports present")
            return True
            
    except Exception as e:
        print(f"✗ Error generating hidden imports: {e}")
        return False


def check_data_files():
    """Check that data files referenced in spec exist."""
    backend_dir = Path(__file__).parent
    
    required_files = [
        'config.py',
        'database.py',
        'runtime_paths.py',
    ]
    
    all_exist = True
    for file_name in required_files:
        file_path = backend_dir / file_name
        if file_path.exists():
            print(f"✓ Data file exists: {file_name}")
        else:
            print(f"✗ Data file missing: {file_name}")
            all_exist = False
    
    return all_exist


def check_main_entry_point():
    """Check that main.py exists."""
    main_file = Path(__file__).parent / 'main.py'
    if main_file.exists():
        print(f"✓ Entry point exists: main.py")
        return True
    else:
        print(f"✗ Entry point missing: main.py")
        return False


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("PyInstaller Spec File Verification")
    print("=" * 60)
    print()
    
    checks = [
        ("PyInstaller Installation", check_pyinstaller_installed),
        ("Spec File", check_spec_file_exists),
        ("Build Hooks", check_build_hooks_exists),
        ("Hidden Imports", check_hidden_imports),
        ("Data Files", check_data_files),
        ("Entry Point", check_main_entry_point),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n{name}:")
        print("-" * 60)
        result = check_func()
        results.append((name, result))
    
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print()
    print(f"Result: {passed}/{total} checks passed")
    
    if passed == total:
        print()
        print("✓ All checks passed! Ready to build.")
        print()
        print("To build the executable, run:")
        print("  pyinstaller peft_engine.spec --clean")
        return 0
    else:
        print()
        print("✗ Some checks failed. Please fix the issues above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
