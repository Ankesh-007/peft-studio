# PyInstaller Setup Guide

This document describes how to set up PyInstaller for building the PEFT Studio backend into a standalone executable.

## Prerequisites

- Python 3.10 or higher
- All dependencies from `requirements.txt` installed
- PyInstaller 5.0 or higher

## Installing PyInstaller

```bash
pip install pyinstaller
```

Verify installation:

```bash
pyinstaller --version
```

## Building the Backend Executable

### Quick Build

From the `backend` directory:

```bash
pyinstaller peft_engine.spec --clean
```

The executable will be created in `backend/dist/peft_engine/`

### Build Options

- `--clean`: Remove temporary build files before building (recommended)
- `--noconfirm`: Replace output directory without asking
- `--log-level DEBUG`: Show detailed build information

### Platform-Specific Notes

#### Windows
- Output: `backend/dist/peft_engine/peft_engine.exe`
- Console window is enabled for debugging (hidden by Electron in production)
- Requires Visual C++ Redistributable on target systems

#### macOS
- Output: `backend/dist/peft_engine/peft_engine`
- Universal binary support (x64 + arm64) requires building on macOS
- May require code signing for distribution

#### Linux
- Output: `backend/dist/peft_engine/peft_engine`
- Requires execute permissions: `chmod +x backend/dist/peft_engine/peft_engine`
- Built on one Linux distro may not work on others (glibc compatibility)

## Verifying the Build

### Check Executable Exists

```bash
# Windows
dir backend\dist\peft_engine\peft_engine.exe

# macOS/Linux
ls -lh backend/dist/peft_engine/peft_engine
```

### Check Executable Size

The executable should be between 1MB and 3GB. Typical size is 500MB-2GB due to ML libraries.

```bash
# Windows
Get-Item backend\dist\peft_engine\peft_engine.exe | Select-Object Length

# macOS/Linux
du -h backend/dist/peft_engine/peft_engine
```

### Test the Executable

```bash
# Windows
backend\dist\peft_engine\peft_engine.exe

# macOS/Linux
./backend/dist/peft_engine/peft_engine
```

The backend should start and listen on port 8000. Test with:

```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{"status": "healthy", "timestamp": "..."}
```

## Troubleshooting

### Missing Dependencies

If the executable fails with `ModuleNotFoundError`, the module needs to be added to `hiddenimports` in `peft_engine.spec`.

Run the dependency detection script to verify all imports are included:

```bash
python build_hooks.py
```

### Executable Too Large

If the executable is larger than 3GB:

1. Check if unnecessary packages are included
2. Consider excluding optional dependencies in the spec file
3. Use `--exclude-module` for packages not needed at runtime

### Import Errors at Runtime

If you see import errors when running the bundled executable:

1. Check the module is in `hiddenimports` in the spec file
2. Verify the module is installed: `pip list | grep <module>`
3. Add the module to `build_hooks.py` if it's dynamically imported

### Permission Errors (Unix)

If you get "Permission denied" on Unix systems:

```bash
chmod +x backend/dist/peft_engine/peft_engine
```

## Files Created by This Setup

- `backend/peft_engine.spec` - PyInstaller configuration file
- `backend/build_hooks.py` - Dependency detection utilities
- `backend/tests/test_pyinstaller_dependency_inclusion.py` - Property-based tests for dependency inclusion
- `backend/PYINSTALLER_SETUP.md` - This file

## Next Steps

After verifying the build works locally:

1. Add build scripts to `package.json`
2. Update electron-builder configuration to include the executable
3. Integrate into CI/CD pipeline
4. Test on clean systems without Python installed

## Testing

Run the property-based tests to verify all dependencies are included:

```bash
pytest backend/tests/test_pyinstaller_dependency_inclusion.py -v
```

All tests should pass, confirming that:
- All imports are detected
- All service modules are included
- All connector modules are included
- Critical dependencies are present
- No duplicate imports exist
