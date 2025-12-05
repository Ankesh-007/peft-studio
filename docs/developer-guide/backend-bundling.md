# Python Backend Bundling Guide

This guide explains how the Python backend is bundled into a standalone executable within PEFT Studio, eliminating the need for end users to install Python or manage dependencies.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Build Environment Setup](#build-environment-setup)
- [Building the Backend](#building-the-backend)
- [Testing the Bundled Backend](#testing-the-bundled-backend)
- [Troubleshooting](#troubleshooting)
- [Advanced Topics](#advanced-topics)

## Overview

PEFT Studio uses [PyInstaller](https://pyinstaller.org/) to compile the Python backend (FastAPI server) and all its dependencies into platform-specific standalone executables. This approach provides several benefits:

- **No Python Installation Required**: End users don't need to install Python or pip
- **Dependency Management**: All Python packages are bundled automatically
- **Consistent Environment**: Same Python version and dependencies across all installations
- **Simplified Distribution**: Single executable file per platform
- **Better Security**: Code is compiled and harder to modify

### How It Works

1. **Development Mode**: When running from source, the Electron app spawns the Python backend using the system Python interpreter
2. **Production Mode**: When running from an installer, the Electron app spawns the bundled executable
3. **Automatic Detection**: The BackendServiceManager automatically detects which mode to use based on `app.isPackaged`

### Bundled Components

The backend executable includes:

- Python 3.10+ interpreter
- FastAPI application (`backend/main.py`)
- All dependencies from `backend/requirements.txt`
- Service modules (lazy-loaded for performance)
- Configuration files and data files
- Connector plugins

## Architecture

### Build Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                     Build Pipeline                           │
│                                                              │
│  1. Backend Compilation (PyInstaller)                       │
│     ├─ Analyze dependencies                                 │
│     ├─ Bundle Python interpreter                            │
│     ├─ Include all packages from requirements.txt           │
│     ├─ Add data files and configs                           │
│     └─ Generate platform-specific executable                │
│        └─ Output: backend/dist/peft_engine[.exe]            │
│                                                              │
│  2. Frontend Compilation (Vite + TypeScript)                │
│     ├─ Transpile TypeScript                                 │
│     ├─ Bundle React components                              │
│     ├─ Optimize assets                                      │
│     └─ Output: dist/                                        │
│                                                              │
│  3. Electron Packaging (electron-builder)                   │
│     ├─ Copy frontend dist/ to app                           │
│     ├─ Copy backend executable to extraResources            │
│     ├─ Sign executables (Windows/macOS)                     │
│     ├─ Create installer (NSIS/DMG/AppImage)                 │
│     └─ Output: release/PEFT-Studio-Setup-*.exe              │
└─────────────────────────────────────────────────────────────┘
```

### Runtime Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Electron Main Process                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         BackendServiceManager                          │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │  Path Resolution Logic                           │ │ │
│  │  │  - Development: backend/main.py + python         │ │ │
│  │  │  - Production: resources/backend/peft_engine.exe │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │  Process Lifecycle Management                    │ │ │
│  │  │  - Spawn backend process                         │ │ │
│  │  │  - Monitor health                                │ │ │
│  │  │  - Handle crashes/restarts                       │ │ │
│  │  │  - Clean shutdown (SIGTERM → SIGKILL)           │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ spawn
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Python Backend (Bundled Executable)             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  PyInstaller Bundle                                    │ │
│  │  - Python 3.10+ interpreter                           │ │
│  │  - FastAPI application (backend/main.py)              │ │
│  │  - All dependencies (torch, transformers, peft, etc.) │ │
│  │  - Service modules (lazy-loaded)                      │ │
│  │  - Configuration files                                │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Build Environment Setup

### Prerequisites

Before building the backend, ensure you have the following installed:

#### All Platforms

1. **Python 3.10 or higher**
   ```bash
   python --version
   # Should output: Python 3.10.x or higher
   ```

2. **pip** (comes with Python)
   ```bash
   pip --version
   ```

3. **PyInstaller 5.0 or higher**
   ```bash
   pip install pyinstaller
   
   # Verify installation
   pyinstaller --version
   ```

4. **Backend dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

#### Platform-Specific Requirements

**Windows:**
- Windows 10 or later
- Visual C++ Redistributable (usually already installed)
- No additional requirements

**macOS:**
- macOS 10.15 or later
- Xcode Command Line Tools: `xcode-select --install`
- For universal binaries: Build on macOS with both x64 and arm64 support

**Linux:**
- Ubuntu 20.04+ or equivalent
- Build essentials:
  ```bash
  sudo apt-get install -y build-essential libssl-dev
  ```

### Verifying Build Environment

Run the build environment verification script:

```bash
npm run verify:build:env
```

This checks:
- Python version (3.10+)
- PyInstaller installation
- Platform compatibility
- Required dependencies
- Disk space availability

## Building the Backend

### Quick Start

Build the backend for your current platform:

```bash
# Build backend only
npm run build:backend

# Verify the build
npm run build:backend:verify
```

The executable will be created at:
- **Windows**: `backend/dist/peft_engine.exe`
- **macOS**: `backend/dist/peft_engine`
- **Linux**: `backend/dist/peft_engine`

### Platform-Specific Builds

```bash
# Windows
npm run build:backend:win

# macOS
npm run build:backend:mac

# Linux
npm run build:backend:linux
```

### Complete Build Pipeline

To build the entire application with the bundled backend:

```bash
# Build backend + frontend + installer
npm run build:all

# Platform-specific complete builds
npm run build:win      # Windows installer
npm run build:mac      # macOS installer
npm run build:linux    # Linux installer
```

### Build Output

After a successful build, you'll see:

```
✅ Backend executable verified: backend/dist/peft_engine.exe (1.2 GB)
✅ All dependencies included
✅ Data files bundled
✅ Ready for packaging
```

### Build Configuration

The PyInstaller configuration is defined in `backend/peft_engine.spec`:

```python
# Key configuration options
a = Analysis(
    ['main.py'],                    # Entry point
    pathex=['backend'],             # Search path
    hiddenimports=[                 # Lazy-loaded modules
        'uvicorn.logging',
        'uvicorn.loops.auto',
        'services.*',
        'connectors.*',
        # ... more imports
    ],
    datas=[                         # Data files to bundle
        ('config.py', '.'),
        ('database.py', '.'),
        # ... more data files
    ],
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='peft_engine',             # Output name
    console=False,                  # Hide console window
    onefile=True,                   # Single file bundle
)
```

### Customizing the Build

#### Adding Hidden Imports

If you add new lazy-loaded modules, add them to `hiddenimports` in `backend/peft_engine.spec`:

```python
hiddenimports=[
    # Existing imports...
    'your_new_module',
    'your_new_package.*',
]
```

#### Adding Data Files

To bundle additional data files:

```python
datas=[
    # Existing data files...
    ('path/to/your/file.json', 'destination/folder'),
]
```

#### Build Options

Modify the `EXE` section for different build options:

```python
exe = EXE(
    # ...
    console=True,          # Show console for debugging
    onefile=False,         # Create directory bundle instead
    debug=True,            # Enable debug mode
)
```

## Testing the Bundled Backend

### Local Testing

#### Test the Executable Directly

```bash
# Navigate to the backend dist directory
cd backend/dist

# Run the executable
# Windows
.\peft_engine.exe

# macOS/Linux
./peft_engine
```

The backend should start and listen on `http://localhost:8000`. You can test it:

```bash
# In another terminal
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

#### Test with Electron (Development Mode)

```bash
# Run the app in development mode
npm run dev
```

The app should use the Python script, not the bundled executable.

#### Test with Electron (Production Mode)

```bash
# Build the complete application
npm run build:all

# Run the packaged app
# Windows
.\release\win-unpacked\PEFT Studio.exe

# macOS
open release/mac/PEFT\ Studio.app

# Linux
./release/linux-unpacked/peft-studio
```

The app should use the bundled executable.

### Automated Testing

Run the backend integration tests:

```bash
# Unit tests
npm run test:backend

# Integration tests
npm run test:integration

# End-to-end tests
npm run test:e2e
```

### Verification Checklist

After building, verify:

- [ ] Executable exists at `backend/dist/peft_engine[.exe]`
- [ ] File size is reasonable (500MB - 2GB)
- [ ] Executable runs without errors
- [ ] Health endpoint responds correctly
- [ ] All API endpoints work
- [ ] Lazy-loaded modules load correctly
- [ ] Data files are accessible
- [ ] No console window appears (Windows)
- [ ] Process terminates cleanly on shutdown

## Troubleshooting

### Build Issues

#### PyInstaller Not Found

**Error:**
```
'pyinstaller' is not recognized as an internal or external command
```

**Solution:**
```bash
pip install pyinstaller
# Or
python -m pip install pyinstaller
```

#### Python Version Mismatch

**Error:**
```
Python 3.10+ required, found 3.9.x
```

**Solution:**
Install Python 3.10 or higher from [python.org](https://www.python.org/downloads/)

#### Missing Dependencies

**Error:**
```
ModuleNotFoundError: No module named 'torch'
```

**Solution:**
```bash
cd backend
pip install -r requirements.txt
```

#### Build Fails with Import Errors

**Error:**
```
ImportError: cannot import name 'X' from 'Y'
```

**Solution:**
Add the missing module to `hiddenimports` in `backend/peft_engine.spec`:

```python
hiddenimports=[
    # ... existing imports
    'Y.X',  # Add the missing import
]
```

Then rebuild:
```bash
npm run build:backend
```

#### Executable Too Large

**Issue:** The executable is over 3GB

**Solution:**
1. Check for duplicate dependencies
2. Exclude unnecessary packages
3. Use `--exclude-module` for large unused packages:

```python
# In peft_engine.spec
excludes=[
    'matplotlib',  # If not used
    'scipy',       # If not used
]
```

#### Build Fails on Windows with Permission Error

**Error:**
```
PermissionError: [WinError 5] Access is denied
```

**Solution:**
1. Close any running instances of the backend
2. Disable antivirus temporarily
3. Run as administrator
4. Add `backend/dist/` to antivirus exclusions

### Runtime Issues

#### Executable Not Found

**Error:**
```
Backend executable not found: /path/to/peft_engine
Installation may be corrupted. Please reinstall.
```

**Solution:**
1. Verify the executable exists at the expected path
2. Check electron-builder configuration includes `extraResources`
3. Rebuild the application:
   ```bash
   npm run build:all
   ```

#### Permission Denied (Unix)

**Error:**
```
Permission denied: /path/to/peft_engine
```

**Solution:**
```bash
chmod +x /path/to/peft_engine
```

Or the app will attempt to fix permissions automatically.

#### Missing Module at Runtime

**Error:**
```
ModuleNotFoundError: No module named 'X'
```

**Solution:**
Add the module to `hiddenimports` in `backend/peft_engine.spec` and rebuild.

#### Backend Crashes on Startup

**Debugging Steps:**

1. **Check logs:**
   - Windows: `%APPDATA%\PEFT Studio\logs\`
   - macOS: `~/Library/Logs/PEFT Studio/`
   - Linux: `~/.config/PEFT Studio/logs/`

2. **Run executable directly:**
   ```bash
   cd backend/dist
   ./peft_engine
   ```
   Check the console output for errors.

3. **Enable debug mode:**
   Set `console=True` in `peft_engine.spec` and rebuild.

#### Port Already in Use

**Error:**
```
Address already in use: 8000
```

**Solution:**
The app automatically tries ports 8000-8010. If all are in use:

1. Stop other services using these ports
2. Or modify the port range in `electron/main.js`

### Performance Issues

#### Slow Startup

**Issue:** Backend takes more than 5 seconds to start

**Causes:**
- Large ML models being loaded
- Slow disk I/O
- Antivirus scanning

**Solutions:**
1. Ensure lazy loading is working (check `backend/services/lazy_imports.py`)
2. Add backend executable to antivirus exclusions
3. Use SSD instead of HDD
4. Reduce startup dependencies

#### High Memory Usage

**Issue:** Backend uses excessive memory

**Causes:**
- All dependencies loaded in memory
- Large ML models

**Solutions:**
1. Ensure lazy loading is enabled
2. Unload unused models
3. Increase system RAM
4. Use `--onedir` instead of `--onefile` in PyInstaller

## Advanced Topics

### Cross-Platform Builds

You can only build for the platform you're currently on. To build for all platforms:

1. **Use CI/CD**: GitHub Actions builds on all platforms automatically
2. **Use VMs**: Set up virtual machines for each platform
3. **Use Cloud Services**: Use cloud build services

### Optimizing Bundle Size

1. **Exclude Unused Packages:**
   ```python
   excludes=['matplotlib', 'scipy', 'pandas']
   ```

2. **Use Lazy Loading:**
   Ensure heavy imports are lazy-loaded in the code.

3. **Strip Binaries:**
   ```python
   exe = EXE(
       # ...
       strip=True,  # Strip debug symbols
   )
   ```

4. **Compress:**
   ```python
   exe = EXE(
       # ...
       upx=True,  # Use UPX compression
   )
   ```

### Custom Python Version

To use a specific Python version:

1. Install the desired Python version
2. Create a virtual environment:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # Unix
   venv\Scripts\activate     # Windows
   ```
3. Install dependencies and PyInstaller in the venv
4. Build from the venv

### Debugging the Bundle

Enable debug mode for detailed logging:

```python
# In peft_engine.spec
exe = EXE(
    # ...
    console=True,   # Show console
    debug=True,     # Enable debug output
)
```

Then run the executable and check the console output.

### Data File Access

At runtime, bundled data files are accessed via `sys._MEIPASS`:

```python
import sys
import os

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller"""
    if getattr(sys, 'frozen', False):
        # Running as bundled executable
        base_path = sys._MEIPASS
    else:
        # Running as script
        base_path = os.path.dirname(__file__)
    
    return os.path.join(base_path, relative_path)

# Usage
config_path = get_resource_path('config.py')
```

This is implemented in `backend/runtime_paths.py`.

### Code Signing

For production releases, sign the backend executable:

**Windows:**
```bash
# Set environment variables
$env:CSC_LINK = "path\to\certificate.pfx"
$env:CSC_KEY_PASSWORD = "password"

# Build with signing
npm run build:win
```

**macOS:**
```bash
# Sign the executable
codesign --force --sign "Developer ID Application: Your Name" backend/dist/peft_engine

# Verify
codesign -dv --verbose=4 backend/dist/peft_engine
```

### CI/CD Integration

The backend build is integrated into the CI/CD pipeline:

```yaml
# .github/workflows/build.yml
- name: Install PyInstaller
  run: pip install pyinstaller

- name: Build backend
  run: npm run build:backend

- name: Verify backend build
  run: npm run build:backend:verify

- name: Build application
  run: npm run build:win
```

## Related Documentation

- [Build and Installers Guide](build-and-installers.md) - Complete build documentation
- [Release Process](release-process.md) - How to create releases
- [Testing Guide](testing.md) - Testing strategies
- [Troubleshooting](../reference/troubleshooting.md) - General troubleshooting

## Support

For issues or questions:
- Check this guide and troubleshooting section
- Review PyInstaller documentation: https://pyinstaller.org/
- Check GitHub Actions logs for CI failures
- Open an issue on GitHub with:
  - Build logs
  - Error messages
  - Platform and Python version
  - Steps to reproduce

## Summary

The Python backend bundling system:

- **Eliminates Python Installation**: Users don't need Python installed
- **Simplifies Distribution**: Single executable per platform
- **Maintains Performance**: Lazy loading preserves fast startup
- **Supports All Platforms**: Windows, macOS, and Linux
- **Integrates with CI/CD**: Automated builds on all platforms
- **Production Ready**: Comprehensive testing and error handling

The bundling system is transparent to end users and provides a seamless desktop application experience.
