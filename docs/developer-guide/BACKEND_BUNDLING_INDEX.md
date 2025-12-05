# Backend Bundling Documentation Index

This index provides a comprehensive overview of all documentation related to the Python backend bundling feature in PEFT Studio.

## Overview

PEFT Studio uses PyInstaller to bundle the Python backend (FastAPI server) and all its dependencies into platform-specific standalone executables. This eliminates the need for end users to install Python or manage dependencies manually.

## Documentation Structure

### For Developers

#### Getting Started
1. **[Backend Bundling Guide](backend-bundling.md)** - Start here
   - Overview of backend bundling
   - Architecture and design
   - Build environment setup
   - Building the backend
   - Configuration and customization

#### Building and Testing
2. **[Testing Bundled Backend](testing-bundled-backend.md)**
   - Testing workflow
   - Unit testing
   - Integration testing
   - Manual testing procedures
   - Performance testing
   - Platform-specific testing

3. **[Build and Installers Guide](build-and-installers.md)**
   - Complete build process
   - Platform-specific builds
   - Code signing
   - CI/CD integration

#### Releasing
4. **[Release with Bundled Backend](release-with-bundled-backend.md)**
   - Release process overview
   - Pre-release checklist
   - Step-by-step release guide
   - Platform-specific considerations
   - Verification procedures

#### Troubleshooting
5. **[Backend Bundling Troubleshooting](backend-bundling-troubleshooting.md)**
   - Build-time issues
   - Runtime issues
   - Performance issues
   - Platform-specific issues
   - Debugging techniques

### For Users

6. **[Installation Guide](../user-guide/installation.md)**
   - Installation instructions for all platforms
   - System requirements (updated for bundled backend)
   - Troubleshooting installation issues
   - What's included in the installer

## Quick Links

### Common Tasks

- **First Time Setup**: [Backend Bundling Guide → Build Environment Setup](backend-bundling.md#build-environment-setup)
- **Build Backend**: [Backend Bundling Guide → Building the Backend](backend-bundling.md#building-the-backend)
- **Test Backend**: [Testing Bundled Backend → Testing Workflow](testing-bundled-backend.md#testing-workflow)
- **Create Release**: [Release with Bundled Backend → Release Steps](release-with-bundled-backend.md#release-steps)
- **Fix Build Issues**: [Troubleshooting → Build Issues](backend-bundling-troubleshooting.md#build-time-issues)
- **Fix Runtime Issues**: [Troubleshooting → Runtime Issues](backend-bundling-troubleshooting.md#runtime-issues)

### Reference

- **PyInstaller Spec File**: `backend/peft_engine.spec`
- **Build Scripts**: `package.json` (scripts section)
- **Verification Script**: `scripts/verify-backend-build.js`
- **Environment Verification**: `scripts/verify-build-environment.js`
- **Runtime Paths**: `backend/runtime_paths.py`
- **Build Hooks**: `backend/build_hooks.py`

## Key Concepts

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Electron Main Process                     │
│                  (BackendServiceManager)                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ spawns
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Python Backend (Bundled Executable)             │
│  - Python 3.10+ interpreter                                 │
│  - FastAPI application                                      │
│  - All dependencies (torch, transformers, peft, etc.)       │
│  - Service modules (lazy-loaded)                            │
│  - Configuration files                                      │
└─────────────────────────────────────────────────────────────┘
```

### Build Pipeline

```
1. Backend Compilation (PyInstaller)
   ├─ Analyze dependencies
   ├─ Bundle Python interpreter
   ├─ Include all packages
   ├─ Add data files
   └─ Generate executable
       └─ Output: backend/dist/peft_engine[.exe]

2. Frontend Compilation (Vite + TypeScript)
   └─ Output: dist/

3. Electron Packaging (electron-builder)
   ├─ Copy frontend dist/
   ├─ Copy backend executable to extraResources
   ├─ Sign executables
   └─ Create installer
       └─ Output: release/PEFT-Studio-Setup-*.exe
```

### Development vs Production

| Aspect | Development Mode | Production Mode |
|--------|-----------------|-----------------|
| Backend | Python script | Bundled executable |
| Python | System Python | Bundled interpreter |
| Dependencies | pip install | Bundled in executable |
| Path | `backend/main.py` | `resources/backend/peft_engine` |
| Detection | `app.isPackaged = false` | `app.isPackaged = true` |

## Prerequisites

### Required Software

- **Node.js 18+**: JavaScript runtime
- **Python 3.10+**: Python interpreter
- **PyInstaller 5.0+**: Python bundling tool
- **pip**: Python package manager

### Platform-Specific

**Windows:**
- Windows 10+ (64-bit)
- Visual C++ Redistributable

**macOS:**
- macOS 10.15+
- Xcode Command Line Tools

**Linux:**
- Ubuntu 20.04+ or equivalent
- Build essentials

### Verification

```bash
# Verify all prerequisites
npm run verify:build:env

# Expected output:
# ✅ Node.js version: 18.x.x
# ✅ Python version: 3.10.x
# ✅ PyInstaller version: 5.x.x
# ✅ Platform: win32/darwin/linux
# ✅ Disk space: 10GB+ available
```

## Common Workflows

### Workflow 1: First Time Setup

```bash
# 1. Install PyInstaller
pip install pyinstaller

# 2. Install backend dependencies
cd backend
pip install -r requirements.txt

# 3. Verify environment
npm run verify:build:env

# 4. Build backend
npm run build:backend

# 5. Verify build
npm run build:backend:verify

# 6. Test backend
cd backend/dist
./peft_engine
```

### Workflow 2: Development Build

```bash
# 1. Make code changes
# ... edit files ...

# 2. Build backend
npm run build:backend

# 3. Test changes
npm run test:integration

# 4. Run application
npm run dev
```

### Workflow 3: Release Build

```bash
# 1. Verify environment
npm run verify:build:env

# 2. Run tests
npm test
npm run test:integration

# 3. Build backend
npm run build:backend

# 4. Build application
npm run build:all

# 5. Test installer
# ... test on clean system ...

# 6. Create release
node scripts/complete-release.js
```

### Workflow 4: Troubleshooting

```bash
# 1. Check logs
# Windows: %APPDATA%\PEFT Studio\logs\
# macOS: ~/Library/Logs/PEFT Studio/
# Linux: ~/.config/PEFT Studio/logs/

# 2. Test backend independently
cd backend/dist
./peft_engine

# 3. Enable debug mode
# Edit backend/peft_engine.spec:
# console=True, debug=True

# 4. Rebuild with debug
npm run build:backend

# 5. Check for missing imports
python backend/build_hooks.py
```

## File Structure

```
peft-studio/
├── backend/
│   ├── main.py                    # Backend entry point
│   ├── peft_engine.spec          # PyInstaller configuration
│   ├── build_hooks.py            # Dependency detection
│   ├── runtime_paths.py          # Path resolution helper
│   ├── requirements.txt          # Python dependencies
│   ├── dist/                     # Build output
│   │   └── peft_engine[.exe]    # Bundled executable
│   └── tests/                    # Backend tests
│       ├── test_data_file_bundling.py
│       └── test_runtime_path_integration.py
├── electron/
│   └── main.js                   # BackendServiceManager
├── scripts/
│   ├── build.js                  # Build orchestration
│   ├── verify-backend-build.js   # Backend verification
│   ├── verify-build-environment.js # Environment check
│   └── complete-release.js       # Release orchestration
├── src/test/
│   ├── integration/              # Integration tests
│   │   ├── backend-lifecycle-verification.test.ts
│   │   ├── backend-performance-verification.test.ts
│   │   ├── platform-windows.test.ts
│   │   ├── platform-macos.test.ts
│   │   └── platform-linux.test.ts
│   └── pbt/                      # Property-based tests
│       ├── backend-path-resolution.pbt.test.ts
│       ├── backend-process-cleanup.pbt.test.ts
│       └── resource-path-accessibility.pbt.test.ts
├── docs/
│   ├── developer-guide/
│   │   ├── backend-bundling.md
│   │   ├── backend-bundling-troubleshooting.md
│   │   ├── testing-bundled-backend.md
│   │   ├── release-with-bundled-backend.md
│   │   └── BACKEND_BUNDLING_INDEX.md (this file)
│   └── user-guide/
│       └── installation.md       # Updated with new requirements
└── package.json                  # Build scripts
```

## Configuration Files

### PyInstaller Spec File

**Location**: `backend/peft_engine.spec`

**Key Sections**:
- `Analysis`: Dependency detection and hidden imports
- `PYZ`: Python bytecode archive
- `EXE`: Executable configuration
- `hiddenimports`: Lazy-loaded modules
- `datas`: Data files to bundle

### Electron-Builder Config

**Location**: `package.json` → `build` section

**Key Settings**:
- `extraResources`: Include backend executable
- `files`: Exclude backend source from asar
- Platform-specific settings (win, mac, linux)

### Build Scripts

**Location**: `package.json` → `scripts` section

**Key Scripts**:
- `build:backend`: Build backend executable
- `build:backend:verify`: Verify backend build
- `build:all`: Build backend + frontend + installer
- `verify:build:env`: Verify build environment

## Testing

### Test Types

1. **Unit Tests** (Python)
   - Location: `backend/tests/`
   - Run: `cd backend && pytest`
   - Coverage: Backend functionality

2. **Integration Tests** (TypeScript)
   - Location: `src/test/integration/`
   - Run: `npm run test:integration`
   - Coverage: Electron-backend integration

3. **Property-Based Tests** (TypeScript)
   - Location: `src/test/pbt/`
   - Run: `npm run test:pbt`
   - Coverage: Correctness properties

4. **End-to-End Tests** (TypeScript)
   - Location: `src/test/e2e/`
   - Run: `npm run test:e2e`
   - Coverage: Complete workflows

### Test Coverage

- Backend unit tests: 80%+
- Integration tests: All critical paths
- Property-based tests: All correctness properties
- Manual testing: All platforms

## Troubleshooting Quick Reference

| Issue | Solution | Documentation |
|-------|----------|---------------|
| PyInstaller not found | `pip install pyinstaller` | [Troubleshooting → Build Issues](backend-bundling-troubleshooting.md#pyinstaller-not-found) |
| Python version mismatch | Install Python 3.10+ | [Troubleshooting → Build Issues](backend-bundling-troubleshooting.md#python-version-mismatch) |
| Missing dependencies | `pip install -r requirements.txt` | [Troubleshooting → Build Issues](backend-bundling-troubleshooting.md#missing-dependencies) |
| Hidden import errors | Add to `hiddenimports` in spec | [Troubleshooting → Build Issues](backend-bundling-troubleshooting.md#hidden-import-errors) |
| Executable not found | Check `extraResources` config | [Troubleshooting → Runtime Issues](backend-bundling-troubleshooting.md#executable-not-found) |
| Permission denied | `chmod +x peft_engine` | [Troubleshooting → Runtime Issues](backend-bundling-troubleshooting.md#permission-denied-unix) |
| Backend crashes | Check logs, enable debug mode | [Troubleshooting → Runtime Issues](backend-bundling-troubleshooting.md#backend-crashes-on-startup) |
| Slow startup | Check lazy loading, antivirus | [Troubleshooting → Performance Issues](backend-bundling-troubleshooting.md#slow-startup-time) |

## Best Practices

### Development

1. **Test Early**: Build and test backend frequently
2. **Use Virtual Environments**: Isolate dependencies
3. **Keep Spec Updated**: Update `hiddenimports` and `datas`
4. **Monitor Size**: Keep executable size reasonable
5. **Check Logs**: Review build and runtime logs

### Building

1. **Clean Builds**: Remove `dist/` and `build/` before building
2. **Verify Environment**: Run `verify:build:env` before building
3. **Test Independently**: Test backend executable standalone
4. **Platform-Specific**: Build on each target platform
5. **Use CI/CD**: Automate builds for consistency

### Testing

1. **Comprehensive**: Test all platforms and scenarios
2. **Automated**: Use CI/CD for continuous testing
3. **Manual**: Test installers on clean systems
4. **Performance**: Monitor startup time and memory
5. **Integration**: Test Electron-backend integration

### Releasing

1. **Pre-Release Checklist**: Complete all checks
2. **Test Installers**: Test on clean systems
3. **Verify Checksums**: Generate and verify checksums
4. **Draft First**: Create draft releases for review
5. **Monitor**: Watch for issues after release

## Support and Resources

### Internal Resources

- **Specification**: `.kiro/specs/python-backend-bundling/`
- **Design Document**: `.kiro/specs/python-backend-bundling/design.md`
- **Requirements**: `.kiro/specs/python-backend-bundling/requirements.md`
- **Tasks**: `.kiro/specs/python-backend-bundling/tasks.md`

### External Resources

- **PyInstaller Documentation**: https://pyinstaller.org/
- **Electron Builder**: https://www.electron.build/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Python Packaging**: https://packaging.python.org/

### Getting Help

1. **Check Documentation**: Start with this index
2. **Search Issues**: Look for similar problems on GitHub
3. **Check Logs**: Review application and build logs
4. **Ask for Help**: Open an issue with:
   - Platform and versions
   - Error messages
   - Steps to reproduce
   - Relevant logs

## Changelog

### Version 1.0.0 (Current)

- Initial implementation of backend bundling
- PyInstaller integration
- Platform-specific builds (Windows, macOS, Linux)
- Comprehensive testing suite
- Complete documentation

### Future Enhancements

- Incremental updates for backend
- Multiple backend versions support
- Backend plugins system
- Size optimization
- Cloud backend option

## Summary

The backend bundling system provides:

- **Zero Setup**: No Python installation required
- **Consistent Environment**: Same dependencies everywhere
- **Better UX**: Seamless desktop application
- **Cross-Platform**: Windows, macOS, Linux support
- **Production Ready**: Comprehensive testing and documentation

This documentation index serves as your starting point for understanding, building, testing, and releasing PEFT Studio with the bundled Python backend.

## Navigation

- **Previous**: [Build and Installers Guide](build-and-installers.md)
- **Next**: [Backend Bundling Guide](backend-bundling.md)
- **Up**: [Developer Guide Index](README.md)
