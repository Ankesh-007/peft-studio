# Python Backend Bundling Spec

## Overview

This spec defines the implementation of bundling the Python backend into a self-contained executable within the PEFT Studio Electron application. The goal is to create a true "one-click run" desktop application where end users don't need to manually install Python, pip, or any Python dependencies.

## Problem Statement

Currently, PEFT Studio requires users to:
1. Install Python 3.10+
2. Install pip and manage Python dependencies
3. Ensure the correct Python version is in their PATH
4. Troubleshoot Python environment issues

This creates a significant barrier to entry and leads to support issues when users have incompatible Python versions or missing dependencies.

## Solution

Use PyInstaller to compile the FastAPI backend and all its dependencies into platform-specific standalone executables. The Electron app will automatically use the bundled executable in production mode while maintaining the development workflow for contributors.

## Key Benefits

- **Zero Python Installation Required:** Users can install and run PEFT Studio without installing Python
- **Consistent Environment:** All users run the same Python version and dependency versions
- **Reduced Support Burden:** Eliminates Python environment-related issues
- **Professional User Experience:** True desktop application feel with one-click installation
- **Simplified Updates:** Backend updates are distributed through the existing auto-updater

## Documents

- **[requirements.md](./requirements.md):** Detailed requirements following EARS pattern
- **[design.md](./design.md):** Architecture, components, and implementation design
- **[tasks.md](./tasks.md):** Step-by-step implementation plan with 17 tasks

## Implementation Status

🔴 **Not Started** - This spec is ready for implementation

## Getting Started

To begin implementing this feature:

1. Review the requirements document to understand what needs to be built
2. Study the design document to understand the architecture
3. Open tasks.md and click "Start task" on task 1 to begin implementation

## Technical Approach

### Build Pipeline

```
Python Backend (source) 
    ↓ PyInstaller
Standalone Executable (peft_engine.exe)
    ↓ electron-builder
Windows Installer (PEFT-Studio-Setup.exe)
```

### Runtime Architecture

```
Electron Main Process
    ↓ spawns
Bundled Python Executable (peft_engine.exe)
    ↓ HTTP/WebSocket
React Frontend
```

### Key Technologies

- **PyInstaller:** Bundles Python applications into standalone executables
- **Electron:** Desktop application framework
- **electron-builder:** Creates installers for Windows, macOS, and Linux
- **FastAPI:** Python backend framework (already in use)

## Platform Support

- ✅ **Windows:** .exe executable, NSIS installer
- ✅ **macOS:** Universal binary (x64 + arm64), DMG installer
- ✅ **Linux:** Executable, AppImage and .deb packages

## Testing Strategy

The spec includes comprehensive testing:
- **10 Property-Based Tests:** Verify universal properties across many inputs
- **Unit Tests:** Test specific components and edge cases
- **Integration Tests:** Test end-to-end workflows
- **Platform-Specific Tests:** Verify behavior on each OS

## Dependencies

### Build-Time
- PyInstaller (>=5.0)
- Python (>=3.10)
- Node.js (>=18)
- electron-builder (>=25.0) - already installed

### Runtime
- None for end users (everything is bundled)

## Estimated Impact

### File Sizes
- Backend executable: ~500MB-2GB (includes PyTorch and ML libraries)
- Installer: ~1-3GB (compressed)

### Performance
- Startup time: <5 seconds (with lazy loading)
- Memory overhead: +200-500MB (Python interpreter + libraries)

### Development Time
- Estimated: 2-3 weeks for full implementation
- 17 tasks covering all aspects of bundling, testing, and documentation

## Related Issues

This spec addresses the need for a self-contained desktop application as mentioned in the user's request for "One-Click Run" functionality.

## Questions or Feedback?

If you have questions about this spec or suggestions for improvements, please discuss them before beginning implementation to ensure alignment.
