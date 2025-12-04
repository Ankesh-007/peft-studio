# Test, Build, and Deploy Guide

This guide explains how to test, build installers, and deploy PEFT Studio to GitHub.

## Quick Start

### Windows

```powershell
# Run all tests, build Windows and Linux installers
.\scripts\test-build-deploy.ps1

# Build only Windows installer
.\scripts\test-build-deploy.ps1 -Platform "windows"

# Skip tests and build directly
.\scripts\test-build-deploy.ps1 -SkipTests

# Build and push to GitHub
.\scripts\test-build-deploy.ps1 -PushToGitHub
```

### Linux/Mac

```bash
# Make script executable
chmod +x scripts/test-build-deploy.sh

# Run all tests, build Windows and Linux installers
./scripts/test-build-deploy.sh

# Build only Linux installer
./scripts/test-build-deploy.sh --platform "linux"

# Skip tests and build directly
./scripts/test-build-deploy.sh --skip-tests

# Build and push to GitHub
./scripts/test-build-deploy.sh --push
```

## What the Script Does

The `test-build-deploy` script performs the following operations:

### 1. Prerequisites Check
- Verifies Node.js, npm, Python, and Git are installed
- Checks for required tools

### 2. Dependency Installation
- Installs Node.js dependencies (`npm ci`)
- Installs Python dependencies (pytest, hypothesis, etc.)

### 3. Code Quality Checks
- Runs ESLint for code linting
- Runs TypeScript type checking

### 4. Testing
- **Frontend Tests**: Runs Vitest unit tests
- **Backend Tests**: Runs pytest with coverage
- Provides detailed error reporting
- Allows continuing even if tests fail (with confirmation)

### 5. Building
- Builds the frontend (React + Vite)
- Creates Electron installers for specified platforms:
  - **Windows**: `.exe` installer and portable version
  - **Linux**: `.AppImage` and `.deb` packages
  - **Mac**: `.dmg` and `.zip` (if on macOS)

### 6. Artifact Display
- Shows all generated installers
- Displays file sizes
- Calculates total build size

### 7. GitHub Deployment (Optional)
- Commits changes
- Pushes to GitHub
- Provides instructions for creating release tags

## Command-Line Options

### Windows PowerShell

| Option | Description | Example |
|--------|-------------|---------|
| `-SkipTests` | Skip all tests | `.\scripts\test-build-deploy.ps1 -SkipTests` |
| `-SkipBuild` | Skip building installers | `.\scripts\test-build-deploy.ps1 -SkipBuild` |
| `-Platform` | Specify platforms to build | `.\scripts\test-build-deploy.ps1 -Platform "windows,linux"` |
| `-PushToGitHub` | Push changes to GitHub | `.\scripts\test-build-deploy.ps1 -PushToGitHub` |
| `-CommitMessage` | Custom commit message | `.\scripts\test-build-deploy.ps1 -PushToGitHub -CommitMessage "Release v1.0.0"` |

### Linux/Mac Bash

| Option | Description | Example |
|--------|-------------|---------|
| `--skip-tests` | Skip all tests | `./scripts/test-build-deploy.sh --skip-tests` |
| `--skip-build` | Skip building installers | `./scripts/test-build-deploy.sh --skip-build` |
| `--platform` | Specify platforms to build | `./scripts/test-build-deploy.sh --platform "linux"` |
| `--push` | Push changes to GitHub | `./scripts/test-build-deploy.sh --push` |
| `--message` | Custom commit message | `./scripts/test-build-deploy.sh --push --message "Release v1.0.0"` |

## Common Workflows

### Development Build
Test and build for your current platform:

```powershell
# Windows
.\scripts\test-build-deploy.ps1 -Platform "windows"

# Linux
./scripts/test-build-deploy.sh --platform "linux"
```

### Quick Build (Skip Tests)
When you need a fast build without running tests:

```powershell
# Windows
.\scripts\test-build-deploy.ps1 -SkipTests -Platform "windows"

# Linux
./scripts/test-build-deploy.sh --skip-tests --platform "linux"
```

### Release Build
Build for all platforms and prepare for release:

```powershell
# Windows
.\scripts\test-build-deploy.ps1 -Platform "windows,linux"

# Linux (can build Windows from Linux using Wine)
./scripts/test-build-deploy.sh --platform "windows,linux"
```

### Deploy to GitHub
Build and push to GitHub:

```powershell
# Windows
.\scripts\test-build-deploy.ps1 -PushToGitHub -CommitMessage "Release v1.0.0"

# Linux
./scripts/test-build-deploy.sh --push --message "Release v1.0.0"
```

## Creating a GitHub Release

After building installers, create a release on GitHub:

### 1. Tag the Release

```bash
# Create and push a version tag
git tag v1.0.0
git push origin v1.0.0
```

### 2. Automated Build
The GitHub Actions workflow (`.github/workflows/build-installers.yml`) will automatically:
- Build installers for Windows, macOS, and Linux
- Create a GitHub release
- Upload all installers as release assets

### 3. Manual Release
Alternatively, create a release manually:

1. Go to your GitHub repository
2. Click "Releases" → "Create a new release"
3. Choose the tag you created
4. Upload installers from the `release/` directory
5. Write release notes
6. Publish the release

## Build Output

After a successful build, you'll find installers in the `release/` directory:

### Windows
- `PEFT Studio Setup 1.0.0.exe` - Full installer
- `PEFT Studio 1.0.0.exe` - Portable version

### Linux
- `PEFT-Studio-1.0.0.AppImage` - Universal Linux package
- `peft-studio_1.0.0_amd64.deb` - Debian/Ubuntu package

### macOS (if built on Mac)
- `PEFT Studio 1.0.0.dmg` - Disk image installer
- `PEFT Studio 1.0.0-mac.zip` - Archive

## Troubleshooting

### Tests Failing

If tests fail, the script will ask if you want to continue. You can:
- Fix the failing tests and run again
- Continue anyway (not recommended for releases)
- Use `-SkipTests` to bypass testing

### Build Errors

Common build issues:

1. **Missing dependencies**: Run `npm ci` and `pip install -r backend/requirements.txt`
2. **Out of memory**: Close other applications or increase Node memory: `export NODE_OPTIONS="--max-old-space-size=4096"`
3. **Permission errors**: Run with appropriate permissions or use `sudo` (Linux/Mac)

### Platform-Specific Issues

**Windows:**
- Ensure you're running PowerShell (not CMD)
- You may need to enable script execution: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

**Linux:**
- Install build dependencies: `sudo apt-get install build-essential`
- For AppImage: `sudo apt-get install fuse libfuse2`

**macOS:**
- Install Xcode Command Line Tools: `xcode-select --install`
- For code signing, set up certificates in Keychain

## CI/CD Integration

The project includes GitHub Actions workflows for automated testing and building:

- **`.github/workflows/ci.yml`**: Runs on every push/PR
- **`.github/workflows/test.yml`**: Comprehensive test suite
- **`.github/workflows/build-installers.yml`**: Builds installers on tag push
- **`.github/workflows/release.yml`**: Creates GitHub releases

## Environment Variables

For automated builds, you may need to set:

```bash
# GitHub token for releases
export GH_TOKEN="your_github_token"

# Code signing (optional)
export CSC_LINK="path_to_certificate"
export CSC_KEY_PASSWORD="certificate_password"

# macOS notarization (optional)
export APPLE_ID="your_apple_id"
export APPLE_ID_PASSWORD="app_specific_password"
```

## Best Practices

1. **Always run tests** before building release installers
2. **Test installers** on clean systems before publishing
3. **Use semantic versioning** for tags (v1.0.0, v1.0.1, etc.)
4. **Write release notes** describing changes
5. **Keep dependencies updated** for security
6. **Sign installers** for production releases (Windows/macOS)

## Support

For issues or questions:
- Check the [main README](../README.md)
- Review [troubleshooting docs](../docs/reference/troubleshooting.md)
- Open an issue on GitHub
