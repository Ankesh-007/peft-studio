# Implementation Plan: Python Backend Bundling

## Overview

This implementation plan breaks down the Python backend bundling feature into discrete, manageable tasks. Each task builds incrementally on previous work, ensuring the system remains functional throughout development.

**Current State Analysis:**
- ✅ Backend service manager exists in `electron/main.js` with comprehensive process lifecycle management
- ✅ Python backend exists with FastAPI and all dependencies in `backend/`
- ✅ CI/CD workflows exist for testing and building (`.github/workflows/ci.yml`)
- ✅ Electron-builder configuration exists in `package.json`
- ✅ Build script exists (`scripts/build.js`) with artifact collection and verification
- ✅ Backend has lazy loading optimization for startup performance
- ✅ BackendServiceManager has health checks, crash recovery, and port management
- ✅ BackendServiceManager already has `findPythonExecutable()` method for development mode
- ✅ BackendServiceManager already has proper SIGTERM → SIGKILL shutdown sequence
- ✅ BackendServiceManager already has crash recovery with restart attempts
- ✅ BackendServiceManager already has port conflict handling (8000-8010)
- ✅ BackendServiceManager already has comprehensive error handling for missing modules, port conflicts, etc.
- ❌ No PyInstaller configuration or spec file
- ❌ No backend bundling scripts or build:backend npm scripts
- ❌ No path resolution for bundled executables in BackendServiceManager (only supports development mode)
- ❌ Backend not included in electron-builder extraResources
- ❌ No backend build verification script
- ❌ No build environment verification for PyInstaller
- ❌ No data file bundling configuration for PyInstaller
- ❌ No `.github/workflows/build.yml` workflow exists yet

---

## Tasks

- [x] 1. Set up PyInstaller configuration and dependency detection





  - Create PyInstaller spec file (`backend/peft_engine.spec`) for the backend
  - Configure entry point as `backend/main.py`
  - Set output name to `peft_engine` with platform-appropriate extension
  - Configure console mode as hidden (`--noconsole` for Windows)
  - Implement dependency detection module (`backend/build_hooks.py`) to find all imports
  - Configure hidden imports for lazy-loaded modules (uvicorn.*, services.*, connectors.*, plugins.*)
  - Add data files to bundle: config.py, database.py, and any other runtime configuration files
  - Configure PyInstaller to handle FastAPI and Uvicorn properly
  - Test spec file generates executable on current platform
  - Verify executable size is reasonable (>1MB, <3GB)
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 7.1, 7.3_

- [x] 1.1 Write property test for dependency inclusion


  - **Property 1: Dependency Inclusion Completeness**
  - **Validates: Requirements 1.2, 1.5, 7.1, 7.3**

- [x] 2. Create platform-specific build scripts and verification









  - Add `build:backend` script to package.json for PyInstaller execution
  - Add platform-specific build scripts (build:backend:win, build:backend:mac, build:backend:linux)
  - Create backend build verification script (`scripts/verify-backend-build.js`)
  - Verify executable exists at `backend/dist/peft_engine[.exe]`
  - Check executable size is reasonable (>1MB minimum, <3GB maximum)
  - Verify critical dependencies are present in bundle (test imports)
  - Add error handling for build failures with clear messages
  - Ensure build scripts work on Windows (PowerShell/CMD), macOS, and Linux
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 6.1, 6.2, 6.3, 6.4, 6.5, 7.4_

- [x] 2.1 Write property test for build order enforcement


  - **Property 4: Build Order Enforcement**
  - **Validates: Requirements 6.1, 6.4**

- [x] 2.2 Write property test for platform-specific naming


  - **Property 5: Platform-Specific Naming Consistency**
  - **Validates: Requirements 2.4, 2.5**

- [x] 3. Enhance BackendServiceManager for path resolution





  - Implement `getBackendPath()` method in `electron/main.js` with dev/production mode detection
  - Use `app.isPackaged` to distinguish between development and production modes
  - In development mode: return existing path to `backend/main.py` and use existing `findPythonExecutable()` method
  - In production mode: return path to bundled executable via `process.resourcesPath`
  - Update `start()` method to use resolved paths from `getBackendPath()`
  - Add logging for resolved backend paths (include mode, path, platform)
  - Handle both Python script (dev) and executable (prod) execution in spawn
  - Ensure stdout/stderr capture works for bundled executable (should already work)
  - Test path resolution in both modes
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3.1 Write property test for path resolution consistency


  - **Property 2: Path Resolution Consistency**
  - **Validates: Requirements 3.1, 3.2, 3.3**

- [x] 4. Verify and test process lifecycle management with bundled executable





  - Verify existing `stop()` method works with bundled executable (SIGTERM → SIGKILL already implemented)
  - Test zombie process cleanup on app quit with bundled executable
  - Test crash recovery logic works with bundled executable (restart attempts already implemented)
  - Verify health checks work with bundled executable (existing health check should work)
  - Test port conflict handling with bundled executable (8000-8010 range already implemented)
  - Add any necessary adjustments for bundled executable process management
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 4.1 Write property test for process cleanup


  - **Property 3: Process Cleanup Guarantee**
  - **Validates: Requirements 4.2, 4.3, 4.4**

- [x] 5. Update electron-builder configuration





  - Add extraResources configuration in package.json to include backend executable
  - Update files configuration to exclude backend source files from asar
  - Verify platform-specific settings (NSIS, DMG, AppImage) are correct
  - Ensure requestedExecutionLevel is set to asInvoker for Windows
  - Test that backend executable is copied to correct location in packaged app
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 5.1 Write property test for resource path accessibility


  - **Property 6: Resource Path Accessibility**
  - **Validates: Requirements 5.1, 5.3**

- [x] 6. Implement comprehensive error handling





  - Add build-time error detection in build scripts (PyInstaller not found, Python version mismatch)
  - Enhance runtime error handling in BackendServiceManager for bundled executable scenarios
  - Add specific error for executable not found: "Installation may be corrupted. Please reinstall."
  - Add specific error for permission issues on Unix: attempt chmod +x, provide manual instructions
  - Extend existing error messages for bundled executable context
  - Add structured error logging with platform, mode, paths, timestamps (extend existing logging)
  - Test existing error recovery strategies work with bundled executable (port conflicts, module errors, etc.)
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 6.1 Write property test for error message specificity


  - **Property 10: Error Message Specificity**
  - **Validates: Requirements 8.1, 8.2, 8.4**

- [x] 7. Add build environment verification





  - Create pre-build verification script (`scripts/verify-build-environment.js`)
  - Check for PyInstaller installation (run `pyinstaller --version`)
  - Add Python version verification (3.10+ required)
  - Implement platform-specific path handling (Windows vs Unix)
  - Add installation instructions for missing dependencies
  - Integrate verification into build pipeline (run before backend build)
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 8. Implement data file bundling and runtime path resolution





  - Identify all configuration files and data files used by backend (config.py, database.py, etc.)
  - Add data files to PyInstaller spec file using `datas` parameter
  - Implement runtime path resolution helper in backend for bundled data files using sys._MEIPASS
  - Update backend code to use resolved paths when running as bundled executable (if needed)
  - Test data files are accessible in bundled executable
  - Verify database.py and config.py work correctly in bundled mode
  - _Requirements: 1.4_

- [x] 8.1 Write property test for data file bundling


  - **Property 7: Data File Bundling Completeness**
  - **Validates: Requirements 1.4**

- [x] 9. Integrate backend build into existing build pipeline





  - Update `scripts/build.js` to run backend build before frontend build
  - Add backend build step (create buildBackend() function similar to buildFrontend())
  - Ensure backend executable is verified before proceeding to electron-builder
  - Update platform-specific build functions to include backend build
  - Add backend artifacts to existing artifact collection and reporting
  - Update build report to include backend executable information
  - Test complete build pipeline with backend bundling on all platforms
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 10. Integrate with auto-updater





  - Verify backend executable is included in electron-builder output (via extraResources)
  - Test that auto-updater includes backend executable in update packages
  - Add version logging for backend executable in BackendServiceManager startup
  - Verify new backend executable is used after update restart
  - Test update integrity verification includes backend executable (electron-updater handles this)
  - Verify existing checksum verification in auto-updater works with backend executable
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [x] 10.1 Write property test for update package integrity


  - **Property 9: Update Package Integrity**
  - **Validates: Requirements 12.1, 12.3**


- [x] 11. Verify performance and startup time




  - Test bundled executable startup time (should be under 5 seconds on modern hardware)
  - Verify lazy loading is preserved in bundled executable (backend already has lazy loading)
  - Ensure production mode skips unnecessary dependency checks
  - Verify existing backend-status event notification works with bundled executable
  - Add performance metrics logging for slow startups (extend existing logging)
  - Test that /api/health endpoint responds quickly with bundled executable
  - Compare startup time between development and production modes
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 12. Verify code signing integration





  - Test existing sign-windows.js works with bundled executable (if signing is configured)
  - Verify macOS entitlements apply to backend executable (if configured)
  - Test that both application and installer are signed (if signing is configured)
  - Ensure error handling allows unsigned dev builds (already implemented)
  - Test antivirus compatibility (Windows Defender) with bundled executable
  - Document code signing requirements for backend executable
  - _Requirements: 11.1, 11.2, 11.3, 11.5_

- [x] 13. Create platform-specific test suites





  - Write Windows-specific tests (.exe extension, no console, NSIS installer)
  - Write macOS-specific tests (universal binary, DMG installer, notarization)
  - Write Linux-specific tests (AppImage, .deb package, permissions)
  - Verify each platform's installer works on clean systems
  - Test backend executable launches correctly on each platform
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 14. Update CI/CD workflows





  - Add PyInstaller installation to `.github/workflows/ci.yml` (in build-check job)
  - Create `.github/workflows/build.yml` workflow for building installers
  - Add build-backend job in build.yml to run PyInstaller build
  - Add backend build verification step after backend build
  - Ensure platform-specific builds work in CI (Windows, macOS, Linux)
  - Update artifact upload to include backend executables
  - Test CI pipeline end-to-end with backend bundling
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 15. Create end-to-end integration tests





  - Test fresh installation on system without Python
  - Test backend startup and health check with bundled executable
  - Test frontend-backend communication with bundled executable
  - Test crash recovery and automatic restart with bundled executable
  - Test clean shutdown without zombie processes
  - Test all existing backend functionality works with bundled executable
  - _Requirements: 4.1, 4.4, 4.5_


- [x] 16. Write comprehensive documentation




  - Document build environment setup (PyInstaller installation) in `docs/developer-guide/`
  - Create developer guide for building with bundled backend
  - Document troubleshooting steps for common build issues
  - Update user documentation with new system requirements (disk space)
  - Document release process with bundled backend
  - Add documentation for testing bundled executable locally
  - _Requirements: 9.1_

- [x] 17. Final verification and testing









  - Test complete build pipeline on all platforms (Windows, macOS, Linux)
  - Verify all bundled executables work correctly
  - Test installation on clean systems without Python
  - Verify all existing functionality works with bundled backend
  - Ensure all tests pass, ask the user if questions arise

---

## Notes

- All tasks are now required (tests and documentation included for comprehensive implementation)
- Core implementation tasks focus on PyInstaller configuration, build scripts, and path resolution
- Each task includes references to the specific requirements it addresses
- Property-based tests should run a minimum of 100 iterations
- All property tests must include the comment tag: `Feature: python-backend-bundling, Property {number}: {property_text}`
- The implementation follows an incremental approach where each task builds on previous work
- Backend already has hypothesis installed for property-based testing
- Frontend uses fast-check for property-based testing

**Key Existing Infrastructure to Leverage:**
- BackendServiceManager already has comprehensive process lifecycle management (SIGTERM → SIGKILL, crash recovery, health checks)
- BackendServiceManager already has error handling for missing modules, port conflicts, and Python detection
- Build pipeline in `scripts/build.js` already has artifact collection, verification, and reporting
- CI/CD workflows already exist for testing and building
- Auto-updater already has checksum verification and integrity checking

**Main Implementation Focus:**
1. Create PyInstaller spec file with proper configuration for FastAPI/Uvicorn
2. Add build scripts and verification
3. Enhance BackendServiceManager to support production mode (bundled executable)
4. Update electron-builder configuration to include backend executable
5. Integrate backend build into existing build pipeline
6. Update CI/CD workflows to build backend executables
