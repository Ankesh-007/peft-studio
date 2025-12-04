# Building PEFT Studio

This guide covers building PEFT Studio from source and creating installers for distribution.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Development Build](#development-build)
- [Production Build](#production-build)
- [Platform-Specific Instructions](#platform-specific-instructions)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

1. **Node.js** (v18 or later)
   - Download from [nodejs.org](https://nodejs.org/)
   - Verify: `node --version`

2. **Python** (v3.9 or later)
   - Download from [python.org](https://www.python.org/)
   - Verify: `python --version` or `python3 --version`

3. **Git**
   - Download from [git-scm.com](https://git-scm.com/)
   - Verify: `git --version`

### Platform-Specific Requirements

**Windows:**
- Windows 10 or later
- PowerShell 5.1 or later
- Visual Studio Build Tools (optional, for native modules)

**Linux:**
- Ubuntu 18.04+ or equivalent
- Build essentials: `sudo apt-get install build-essential`
- For AppImage: `sudo apt-get install fuse libfuse2`

**macOS:**
- macOS 10.13 or later
- Xcode Command Line Tools: `xcode-select --install`

## Quick Start

### Interactive Build (Easiest)

**Windows:**
```powershell
.\build-and-test.ps1
```

This launches an interactive menu where you can choose what to build.

### Command-Line Build

**Windows:**
```powershell
# Build Windows and Linux installers with tests
.\scripts\test-build-deploy.ps1

# Build only Windows installer
.\scripts\test-build-deploy.ps1 -Platform "windows"

# Quick build without tests
.\scripts\test-build-deploy.ps1 -SkipTests
```

**Linux/Mac:**
```bash
# Build Windows and Linux installers with tests
./scripts/test-build-deploy.sh

# Build only Linux installer
./scripts/test-build-deploy.sh --platform "linux"

# Quick build without tests
./scripts/test-build-deploy.sh --skip-tests
```

## Development Build

For development, you don't need to create installers. Use the development server:

### Frontend Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# In another terminal, start the backend
cd backend
python -m uvicorn main:app --reload
```

The app will be available at `http://localhost:5173`

### Electron Development

```bash
# Build frontend
npm run build

# Run Electron app
npm run electron:dev
```

## Production Build

### Step 1: Install Dependencies

```bash
# Install Node.js dependencies
npm ci

# Install Python dependencies
cd backend
pip install -r requirements.txt
cd ..
```

### Step 2: Run Tests

```bash
# Frontend tests
npm run test:run

# Backend tests
cd backend
pytest tests/ -v
cd ..
```

### Step 3: Build Frontend

```bash
npm run build
```

This creates optimized production files in the `dist/` directory.

### Step 4: Create Installers

**Windows:**
```powershell
# Windows installer
npm run package:win

# Or use electron-builder directly
npx electron-builder --win
```

**Linux:**
```bash
# Linux packages
npm run package:linux

# Or use electron-builder directly
npx electron-builder --linux
```

**macOS:**
```bash
# macOS installer
npm run package:mac

# Or use electron-builder directly
npx electron-builder --mac
```

**All Platforms:**
```bash
npm run package:all
```

### Step 5: Find Your Installers

Installers are created in the `release/` directory:

- **Windows**: `PEFT Studio Setup 1.0.0.exe`
- **Linux**: `PEFT-Studio-1.0.0.AppImage`, `peft-studio_1.0.0_amd64.deb`
- **macOS**: `PEFT Studio 1.0.0.dmg`

## Platform-Specific Instructions

### Building on Windows

```powershell
# Enable script execution (if needed)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run the build script
.\scripts\test-build-deploy.ps1 -Platform "windows"
```

**Common Issues:**
- If you get "script execution disabled", run the Set-ExecutionPolicy command above
- For native module compilation, install Visual Studio Build Tools

### Building on Linux

```bash
# Install build dependencies
sudo apt-get update
sudo apt-get install build-essential fuse libfuse2

# Make script executable
chmod +x scripts/test-build-deploy.sh

# Run the build script
./scripts/test-build-deploy.sh --platform "linux"
```

**Common Issues:**
- Missing FUSE: Install with `sudo apt-get install fuse libfuse2`
- Permission errors: Use `sudo` or fix file permissions

### Building on macOS

```bash
# Install Xcode Command Line Tools
xcode-select --install

# Make script executable
chmod +x scripts/test-build-deploy.sh

# Run the build script
./scripts/test-build-deploy.sh --platform "mac"
```

**Common Issues:**
- Code signing: For distribution, you need an Apple Developer account
- Notarization: Required for macOS 10.15+

### Cross-Platform Building

You can build for multiple platforms from a single machine:

**From Linux (using Wine):**
```bash
# Install Wine
sudo apt-get install wine64

# Build for Windows and Linux
./scripts/test-build-deploy.sh --platform "windows,linux"
```

**From macOS:**
```bash
# Build for all platforms
./scripts/test-build-deploy.sh --platform "windows,linux,mac"
```

## Testing

### Run All Tests

```bash
# Frontend tests
npm run test:run

# Backend tests
cd backend
pytest tests/ -v
cd ..

# Or use the build script
.\scripts\test-build-deploy.ps1 -SkipBuild  # Windows
./scripts/test-build-deploy.sh --skip-build  # Linux/Mac
```

### Test Types

1. **Unit Tests**: Test individual components
   ```bash
   npm run test:run
   ```

2. **Integration Tests**: Test component interactions
   ```bash
   cd backend
   pytest tests/ -k "integration"
   cd ..
   ```

3. **Property-Based Tests**: Test with generated inputs
   ```bash
   cd backend
   pytest tests/ -k "property"
   cd ..
   ```

4. **E2E Tests**: Test full user workflows
   ```bash
   npm run test:e2e
   ```

### Test Coverage

```bash
# Frontend coverage
npm run test:coverage

# Backend coverage
cd backend
pytest --cov=. --cov-report=html
cd ..
```

## Build Configuration

### Electron Builder Configuration

The build configuration is in `package.json` under the `build` key:

```json
{
  "build": {
    "appId": "com.peftstudio.app",
    "productName": "PEFT Studio",
    "directories": {
      "output": "release"
    },
    "win": {
      "target": ["nsis", "portable"]
    },
    "linux": {
      "target": ["AppImage", "deb"]
    },
    "mac": {
      "target": ["dmg", "zip"]
    }
  }
}
```

### Customizing the Build

Edit `package.json` to customize:
- App name and ID
- Output directory
- Target formats
- Icons and assets
- Code signing settings

## Troubleshooting

### Build Fails

**Problem**: Build fails with "out of memory"
```bash
# Increase Node memory
export NODE_OPTIONS="--max-old-space-size=4096"
npm run build
```

**Problem**: Missing dependencies
```bash
# Clean install
rm -rf node_modules package-lock.json
npm install
```

**Problem**: Python tests fail
```bash
# Reinstall Python dependencies
cd backend
pip install --upgrade -r requirements.txt
cd ..
```

### Installer Issues

**Problem**: Windows installer not signed
- For development, this is normal
- For production, get a code signing certificate

**Problem**: macOS app won't open (security warning)
- Right-click → Open (first time only)
- For distribution, sign and notarize the app

**Problem**: Linux AppImage won't run
```bash
# Make executable
chmod +x PEFT-Studio-1.0.0.AppImage

# Install FUSE if needed
sudo apt-get install fuse libfuse2
```

### Performance Issues

**Problem**: Build is slow
- Use `npm run build:no-check` to skip TypeScript checking
- Close other applications
- Use SSD for faster I/O

**Problem**: Tests are slow
- Run specific test suites: `npm run test -- --run src/test/specific.test.ts`
- Use `--maxfail=1` to stop on first failure

## Advanced Topics

### Code Signing

**Windows:**
1. Get a code signing certificate
2. Set environment variables:
   ```powershell
   $env:CSC_LINK = "path\to\certificate.pfx"
   $env:CSC_KEY_PASSWORD = "certificate_password"
   ```

**macOS:**
1. Join Apple Developer Program
2. Create certificates in Xcode
3. Set environment variables:
   ```bash
   export APPLE_ID="your@email.com"
   export APPLE_ID_PASSWORD="app-specific-password"
   ```

### Auto-Updates

The app includes auto-update functionality using `electron-updater`. Configure in `electron/main.js`:

```javascript
const { autoUpdater } = require('electron-updater');

autoUpdater.checkForUpdatesAndNotify();
```

### CI/CD

GitHub Actions workflows are configured in `.github/workflows/`:
- `ci.yml`: Runs on every push
- `test.yml`: Comprehensive testing
- `build-installers.yml`: Builds installers on tag push
- `release.yml`: Creates GitHub releases

## Resources

- [Electron Builder Documentation](https://www.electron.build/)
- [Vite Build Documentation](https://vitejs.dev/guide/build.html)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Project README](README.md)
- [Contributing Guide](CONTRIBUTING.md)

## Getting Help

If you encounter issues:

1. Check this guide and [troubleshooting docs](docs/reference/troubleshooting.md)
2. Search [existing issues](https://github.com/Ankesh-007/peft-studio/issues)
3. Ask in [discussions](https://github.com/Ankesh-007/peft-studio/discussions)
4. Open a [new issue](https://github.com/Ankesh-007/peft-studio/issues/new)
