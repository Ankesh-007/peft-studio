# Backend Build System

This directory contains the PyInstaller configuration and build system for creating a standalone executable of the PEFT Studio backend.

## Overview

The build system bundles the Python backend (FastAPI application) and all its dependencies into a single executable that can run without requiring Python to be installed on the target system.

## Key Components

### 1. PyInstaller Spec File (`peft_engine.spec`)

The main configuration file for PyInstaller. It defines:

- **Entry point**: `main.py` - The FastAPI application
- **Output name**: `peft_engine` (with platform-appropriate extension)
- **Hidden imports**: All lazy-loaded modules detected by `build_hooks.py`
- **Data files**: Configuration files (`config.py`, `database.py`) and other resources
- **Exclusions**: Test modules and development tools to reduce size

**Key Features:**
- Automatically detects all service, connector, and plugin modules
- Includes all uvicorn submodules (required for FastAPI)
- Bundles data files with proper directory structure
- Console mode enabled for debugging (Electron hides it in production)

### 2. Dependency Detection (`build_hooks.py`)

Utility module that automatically discovers all Python imports in the codebase.

**Functions:**
- `find_all_imports(directory)` - Recursively scans Python files for imports
- `get_uvicorn_hidden_imports()` - Returns all uvicorn submodules
- `get_service_hidden_imports()` - Returns all service modules
- `get_connector_hidden_imports()` - Returns all connector and plugin modules
- `get_all_hidden_imports()` - Combines all hidden imports into a single list

**Why This Is Needed:**
PyInstaller uses static analysis to detect imports, but it cannot detect:
- Lazy-loaded modules (loaded with `importlib` or in functions)
- Dynamic imports (using `__import__()`)
- Modules loaded by frameworks (like uvicorn's protocol implementations)

The build hooks ensure ALL modules are included, even if they're loaded dynamically.

### 3. Property-Based Tests (`tests/test_pyinstaller_dependency_inclusion.py`)

Comprehensive test suite that validates the build system using property-based testing.

**Tests:**
- **Property 1: Dependency Inclusion Completeness** - Verifies all imports are detected
- Uvicorn imports are comprehensive
- All service modules are included
- All connector modules are included
- No duplicate imports
- Imports are sorted alphabetically
- Critical dependencies are present
- Lazy-loaded services are included

**Test Coverage:**
- 89 tests (81 parametrized + 8 property tests)
- Tests every Python file in the backend
- Uses Hypothesis for property-based testing with 100 iterations
- Validates: Requirements 1.2, 1.5, 7.1, 7.3

### 4. Verification Script (`verify_spec.py`)

Pre-build verification script that checks:
- PyInstaller is installed
- Spec file exists and is valid
- Build hooks are present
- Hidden imports can be generated
- Data files exist
- Entry point (main.py) exists

**Usage:**
```bash
python verify_spec.py
```

### 5. Setup Documentation (`PYINSTALLER_SETUP.md`)

Complete guide for:
- Installing PyInstaller
- Building the executable
- Platform-specific notes
- Verifying the build
- Troubleshooting common issues

## Build Process

### Prerequisites

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Verify setup:
   ```bash
   python verify_spec.py
   ```

### Building

From the `backend` directory:

```bash
pyinstaller peft_engine.spec --clean
```

**Output:**
- Windows: `backend/dist/peft_engine/peft_engine.exe`
- macOS: `backend/dist/peft_engine/peft_engine`
- Linux: `backend/dist/peft_engine/peft_engine`

### Testing the Build

1. Run the executable:
   ```bash
   # Windows
   backend\dist\peft_engine\peft_engine.exe
   
   # macOS/Linux
   ./backend/dist/peft_engine/peft_engine
   ```

2. Test the health endpoint:
   ```bash
   curl http://localhost:8000/api/health
   ```

3. Run the property-based tests:
   ```bash
   pytest backend/tests/test_pyinstaller_dependency_inclusion.py -v
   ```

## Architecture

```
backend/
├── main.py                          # Entry point (FastAPI app)
├── peft_engine.spec                 # PyInstaller configuration
├── build_hooks.py                   # Dependency detection
├── verify_spec.py                   # Pre-build verification
├── PYINSTALLER_SETUP.md            # Setup guide
├── BUILD_SYSTEM_README.md          # This file
├── config.py                        # Configuration (bundled)
├── database.py                      # Database setup (bundled)
├── services/                        # Service modules (all bundled)
├── connectors/                      # Connector modules (all bundled)
├── plugins/                         # Plugin modules (all bundled)
└── tests/
    └── test_pyinstaller_dependency_inclusion.py  # PBT tests
```

## How It Works

1. **Analysis Phase**: PyInstaller analyzes `main.py` and follows imports
2. **Hook Execution**: `build_hooks.py` is imported to get hidden imports
3. **Dependency Collection**: All modules from hidden imports are collected
4. **Binary Collection**: Native libraries (torch, etc.) are collected
5. **Data File Collection**: Config files and resources are collected
6. **Bundling**: Everything is packaged into a single directory
7. **Executable Creation**: A launcher executable is created

## Size Considerations

**Expected Size:** 500MB - 2GB

The executable is large because it includes:
- Python interpreter (~50MB)
- PyTorch (~500MB-1GB)
- Transformers (~200MB)
- Other ML libraries (~200MB)
- Application code (~50MB)

**Size Optimization:**
- Exclude test modules (already done)
- Exclude development tools (already done)
- Consider excluding unused torch backends
- Use UPX compression (enabled in spec)

## Platform-Specific Notes

### Windows
- Output: `.exe` file
- Console window enabled (hidden by Electron)
- Requires Visual C++ Redistributable on target systems
- Antivirus may flag the executable (code signing recommended)

### macOS
- Output: Unix executable (no extension)
- Universal binary requires building on macOS
- Code signing and notarization required for distribution
- Gatekeeper may block unsigned executables

### Linux
- Output: Unix executable (no extension)
- Requires execute permissions: `chmod +x`
- Built on one distro may not work on others (glibc compatibility)
- AppImage recommended for distribution

## Integration with Electron

The bundled executable is designed to work with the Electron main process:

1. **Development Mode** (`app.isPackaged = false`):
   - Electron spawns `python backend/main.py`
   - Uses system Python interpreter
   - Allows hot-reloading and debugging

2. **Production Mode** (`app.isPackaged = true`):
   - Electron spawns the bundled executable from `process.resourcesPath`
   - No Python installation required
   - Faster startup (no import overhead)

## Next Steps

After completing this task:

1. ✓ PyInstaller spec file created
2. ✓ Dependency detection implemented
3. ✓ Property-based tests written and passing
4. ✓ Verification script created
5. ✓ Documentation written

**Remaining Tasks:**
- Add build scripts to `package.json`
- Create backend build verification script for CI
- Update electron-builder configuration
- Enhance BackendServiceManager for production mode
- Integrate into CI/CD pipeline

## Troubleshooting

### Build Fails with "Module not found"

Add the module to `hiddenimports` in `peft_engine.spec` or update `build_hooks.py`.

### Executable Crashes on Startup

Check the console output for import errors. Run with `--debug` flag for more details.

### Executable Too Large

Review the `excludes` list in `peft_engine.spec` and consider excluding optional dependencies.

### Tests Fail

Run `python build_hooks.py` to see all detected imports. Verify all required modules are listed.

## References

- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Hypothesis Testing](https://hypothesis.readthedocs.io/)
- Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 7.1, 7.3
