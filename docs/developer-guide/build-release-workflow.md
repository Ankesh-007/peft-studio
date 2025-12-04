# Build and Release Workflow

This document visualizes the complete build and release workflow for PEFT Studio.

## Overview

```
Developer → Git Tag → GitHub Actions → Installers → GitHub Release → Users
```

## Detailed Workflow

### 1. Development Phase

```
┌─────────────────────────────────────────────────────────────┐
│                     Development Phase                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Write code                                               │
│  2. Run tests: npm test                                      │
│  3. Lint code: npm run lint                                  │
│  4. Type check: npm run type-check                           │
│  5. Update CHANGELOG.md                                      │
│  6. Update version in package.json                           │
│  7. Commit changes                                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
```

### 2. Release Trigger

```
┌─────────────────────────────────────────────────────────────┐
│                      Release Trigger                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Developer creates and pushes version tag:                   │
│                                                              │
│  $ git tag v1.0.1                                            │
│  $ git push origin v1.0.1                                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
```

### 3. GitHub Actions Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                   GitHub Actions Workflow                    │
│              (.github/workflows/build-installers.yml)        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Windows    │  │    macOS     │  │    Linux     │      │
│  │   Runner     │  │   Runner     │  │   Runner     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                 │                 │               │
│         ▼                 ▼                 ▼               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Checkout     │  │ Checkout     │  │ Checkout     │      │
│  │ Install deps │  │ Install deps │  │ Install deps │      │
│  │ Build frontend│ │ Build frontend│ │ Build frontend│     │
│  │ Build Windows│  │ Build macOS  │  │ Build Linux  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                 │                 │               │
│         ▼                 ▼                 ▼               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Upload       │  │ Upload       │  │ Upload       │      │
│  │ Artifacts    │  │ Artifacts    │  │ Artifacts    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                 │                 │               │
│         └─────────────────┴─────────────────┘               │
│                           │                                 │
│                           ▼                                 │
│                  ┌──────────────────┐                       │
│                  │ Create Release   │                       │
│                  │ Upload Installers│                       │
│                  └──────────────────┘                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
```

### 4. GitHub Release

```
┌─────────────────────────────────────────────────────────────┐
│                      GitHub Release                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Release: PEFT Studio v1.0.1                                 │
│                                                              │
│  📦 Assets:                                                  │
│  ├─ PEFT Studio Setup 1.0.1.exe (Windows Installer)         │
│  ├─ PEFT Studio 1.0.1.exe (Windows Portable)                │
│  ├─ PEFT Studio-1.0.1.dmg (macOS DMG)                       │
│  ├─ PEFT Studio-1.0.1-mac.zip (macOS ZIP)                   │
│  ├─ PEFT Studio-1.0.1.AppImage (Linux AppImage)             │
│  └─ peft-studio_1.0.1_amd64.deb (Linux DEB)                 │
│                                                              │
│  📝 Release Notes                                            │
│  🔗 Download Links                                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
```

### 5. User Installation

```
┌─────────────────────────────────────────────────────────────┐
│                     User Installation                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Windows User:                                               │
│  1. Download PEFT Studio Setup 1.0.1.exe                     │
│  2. Run installer                                            │
│  3. Launch from Start Menu                                   │
│                                                              │
│  macOS User:                                                 │
│  1. Download PEFT Studio-1.0.1.dmg                           │
│  2. Open DMG and drag to Applications                        │
│  3. Launch from Applications                                 │
│                                                              │
│  Linux User:                                                 │
│  1. Download PEFT Studio-1.0.1.AppImage                      │
│  2. chmod +x PEFT-Studio-1.0.1.AppImage                      │
│  3. Run ./PEFT-Studio-1.0.1.AppImage                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
```

### 6. Auto-Update Cycle

```
┌─────────────────────────────────────────────────────────────┐
│                      Auto-Update Cycle                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  User's Installed App (v1.0.0)                               │
│         │                                                    │
│         ▼                                                    │
│  Check for updates (on startup)                              │
│         │                                                    │
│         ▼                                                    │
│  New version available? (v1.0.1)                             │
│         │                                                    │
│         ▼                                                    │
│  Show notification to user                                   │
│         │                                                    │
│         ▼                                                    │
│  User clicks "Update"                                        │
│         │                                                    │
│         ▼                                                    │
│  Download update from GitHub                                 │
│         │                                                    │
│         ▼                                                    │
│  Install update                                              │
│         │                                                    │
│         ▼                                                    │
│  Restart app with v1.0.1                                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Build Process Details

### Local Build

```
┌─────────────────────────────────────────────────────────────┐
│                       Local Build                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  $ npm install                                               │
│         │                                                    │
│         ▼                                                    │
│  Install Node.js dependencies                                │
│         │                                                    │
│         ▼                                                    │
│  $ npm run build:no-check                                    │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────────────────────────────┐                   │
│  │ Vite Build Process                   │                   │
│  ├──────────────────────────────────────┤                   │
│  │ 1. Compile TypeScript → JavaScript   │                   │
│  │ 2. Bundle React components           │                   │
│  │ 3. Optimize assets                   │                   │
│  │ 4. Generate dist/ folder             │                   │
│  └──────────────────────────────────────┘                   │
│         │                                                    │
│         ▼                                                    │
│  $ npm run electron:build                                    │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────────────────────────────┐                   │
│  │ electron-builder Process             │                   │
│  ├──────────────────────────────────────┤                   │
│  │ 1. Package Electron app              │                   │
│  │ 2. Include dist/ and backend/        │                   │
│  │ 3. Create platform-specific installer│                   │
│  │ 4. Output to release/ folder         │                   │
│  └──────────────────────────────────────┘                   │
│         │                                                    │
│         ▼                                                    │
│  Installer ready in release/                                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Platform-Specific Outputs

```
┌─────────────────────────────────────────────────────────────┐
│                  Platform-Specific Outputs                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Windows (npm run package:win)                               │
│  ├─ NSIS Installer (.exe)                                    │
│  │  ├─ Installation wizard                                   │
│  │  ├─ Desktop shortcut                                      │
│  │  ├─ Start menu entry                                      │
│  │  └─ Uninstaller                                           │
│  └─ Portable (.exe)                                          │
│     └─ Single executable, no installation                    │
│                                                              │
│  macOS (npm run package:mac)                                 │
│  ├─ DMG (.dmg)                                               │
│  │  ├─ Drag-to-Applications installer                        │
│  │  └─ Background image                                      │
│  └─ ZIP (.zip)                                               │
│     └─ Compressed app bundle                                 │
│                                                              │
│  Linux (npm run package:linux)                               │
│  ├─ AppImage (.AppImage)                                     │
│  │  ├─ Self-contained executable                             │
│  │  └─ Works on all distributions                            │
│  └─ DEB (.deb)                                               │
│     ├─ Debian/Ubuntu package                                 │
│     └─ System integration                                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Release Timeline

```
Day 1: Development
├─ Write code
├─ Run tests
├─ Fix bugs
└─ Update docs

Day 2: Pre-Release
├─ Update version
├─ Update CHANGELOG
├─ Test locally
└─ Review checklist

Day 3: Release
├─ 09:00 - Create and push tag
├─ 09:05 - GitHub Actions starts
├─ 09:15 - Windows build complete
├─ 09:20 - macOS build complete
├─ 09:25 - Linux build complete
├─ 09:30 - Release created
├─ 09:35 - Verify installers
├─ 10:00 - Announce release
└─ 10:30 - Monitor feedback

Day 4+: Post-Release
├─ Monitor issues
├─ Respond to feedback
├─ Plan next release
└─ Start new development
```

## File Flow

```
Source Code
    │
    ├─ src/              → Frontend React code
    ├─ electron/         → Electron main process
    ├─ backend/          → Python backend
    └─ package.json      → Build configuration
    │
    ▼
Build Process (npm run build)
    │
    ├─ TypeScript → JavaScript
    ├─ React → Bundled components
    ├─ Assets → Optimized files
    └─ Output → dist/
    │
    ▼
Package Process (electron-builder)
    │
    ├─ dist/             → Frontend build
    ├─ electron/         → Main process
    ├─ backend/          → Python services
    └─ package.json      → App metadata
    │
    ▼
Platform Installers
    │
    ├─ Windows → .exe files
    ├─ macOS   → .dmg and .zip
    └─ Linux   → .AppImage and .deb
    │
    ▼
GitHub Release
    │
    └─ All installers uploaded
    │
    ▼
User Downloads
    │
    └─ Install and run
```

## Decision Tree

```
Need to release?
    │
    ├─ Yes → Ready to release?
    │   │
    │   ├─ Yes → Push version tag
    │   │   │
    │   │   └─ GitHub Actions builds automatically
    │   │
    │   └─ No → Complete pre-release checklist
    │       │
    │       └─ Then push version tag
    │
    └─ No → Continue development
        │
        └─ Test locally with: npm run electron:build
```

## Troubleshooting Flow

```
Build Failed?
    │
    ├─ TypeScript errors?
    │   └─ Use: npm run build:no-check
    │
    ├─ Permission errors?
    │   └─ Run as Administrator (Windows)
    │
    ├─ Missing dependencies?
    │   └─ Run: npm install
    │
    ├─ Platform mismatch?
    │   └─ Use GitHub Actions for cross-platform
    │
    └─ Other error?
        └─ Check: docs/developer-guide/installer-build-guide.md
```

## Summary

This workflow provides:

✅ **Automated builds** - Push a tag, get installers
✅ **Cross-platform** - Windows, macOS, Linux
✅ **Auto-updates** - Users get updates automatically
✅ **Quality control** - Tests run before build
✅ **Easy distribution** - GitHub Releases
✅ **User-friendly** - Simple installation process

## Testing

After building installers, comprehensive testing is required:

- **[Release Testing Summary](./release-testing-summary.md)** - Overview of testing process
- **[Test Release Process](./test-release-process.md)** - Step-by-step testing guide
- **[Windows Testing](./test-windows-installer.md)** - Windows installer testing
- **[macOS Testing](./test-macos-installer.md)** - macOS installer testing
- **[Linux Testing](./test-linux-installer.md)** - Linux installer testing
- **[Auto-Update Testing](./test-auto-update.md)** - Update mechanism testing

### Quick Test

```bash
# PowerShell (Windows)
.\scripts\test-release.ps1 -All

# Bash (Linux/macOS)
./scripts/test-release.sh --all
```

## Resources

- [Installer Build Guide](installer-build-guide.md)
- [BUILD_INSTALLERS.md](../../BUILD_INSTALLERS.md)
- [RELEASE_CHECKLIST.md](../../RELEASE_CHECKLIST.md)
- [GitHub Actions Workflow](../../.github/workflows/build-installers.yml)

---

*Last updated: December 2024*
