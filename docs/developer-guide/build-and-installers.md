# Build and Installer Guide

This comprehensive guide covers building, packaging, and distributing PEFT Studio installers across Windows, macOS, and Linux platforms.

## Table of Contents

- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Build Commands](#build-commands)
- [Platform-Specific Builds](#platform-specific-builds)
- [Code Signing](#code-signing)
- [Portable Versions](#portable-versions)
- [Build Configuration](#build-configuration)
- [Build Scripts](#build-scripts)
- [CI/CD Integration](#cicd-integration)
- [Distribution](#distribution)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Build All Platforms

```bash
npm run package:all
```

This creates installers for Windows, macOS, and Linux in the `release/` directory.

### Build Single Platform

```bash
# Windows
npm run package:win

# macOS
npm run package:mac

# Linux
npm run package:linux
```

### Using Build Scripts

```bash
# Cross-platform (Node.js)
node scripts/build.js [windows|mac|linux|all]

# Unix/Linux/macOS
chmod +x scripts/build.sh
./scripts/build.sh [windows|mac|linux|all]

# Windows (PowerShell)
.\scripts\build.ps1 [windows|mac|linux|all]
```

### Output Location

All installers are created in the `release/` directory:

```
release/
├── PEFT-Studio-Setup-1.0.0.exe          # Windows installer
├── PEFT-Studio-1.0.0-portable.exe       # Windows portable
├── PEFT-Studio-1.0.0.dmg                # macOS installer
├── PEFT-Studio-1.0.0-mac.zip            # macOS archive
├── PEFT-Studio-1.0.0.AppImage           # Linux universal
└── peft-studio_1.0.0_amd64.deb          # Linux Debian/Ubuntu
```

## Prerequisites

### All Platforms

1. **Node.js** (v18 or higher)
   ```bash
   node --version
   ```

2. **npm** (comes with Node.js)
   ```bash
   npm --version
   ```

3. **Install dependencies**
   ```bash
   npm install
   ```

### Platform-Specific Requirements

#### Windows

- **Windows 10/11** (for building Windows installers)
- **NSIS** (automatically installed by electron-builder)
- Optional: Code signing certificate (.pfx file)

#### macOS

- **macOS 10.13+** (for building macOS installers)
- **Xcode Command Line Tools**
  ```bash
  xcode-select --install
  ```
- Optional: Apple Developer account for code signing

#### Linux

- **Linux** (Ubuntu 18.04+ recommended)
- **Required packages**
  ```bash
  sudo apt-get install -y rpm
  ```

## Build Commands

### NPM Scripts

The following scripts are available in `package.json`:

```json
{
  "package": "npm run build && electron-builder",
  "package:win": "npm run build && electron-builder --win",
  "package:mac": "npm run build && electron-builder --mac",
  "package:linux": "npm run build && electron-builder --linux",
  "package:all": "npm run build && electron-builder --win --mac --linux",
  "dist": "node scripts/build.js",
  "dist:win": "node scripts/build.js windows",
  "dist:mac": "node scripts/build.js mac",
  "dist:linux": "node scripts/build.js linux",
  "verify:build": "node scripts/verify-build-config.js"
}
```

### Verify Configuration

Before building, verify your configuration:

```bash
npm run verify:build
```

This checks:
- Build configuration in package.json
- Platform targets
- Build scripts presence
- Build assets directory
- macOS entitlements
- CI/CD workflows
- Dependencies

## Platform-Specific Builds

### Windows Installer (NSIS)

The Windows build creates two installers:

1. **Setup Installer** (`PEFT-Studio-Setup-1.0.0.exe`)
   - Traditional installer with installation wizard
   - Allows user to choose installation directory
   - Creates desktop and start menu shortcuts
   - Supports uninstallation

2. **Portable Version** (`PEFT-Studio-1.0.0-portable.exe`)
   - No installation required
   - Can run from USB drive
   - All data stored in application directory
   - No registry modifications
   - No admin rights required

**Build Command:**
```bash
npm run package:win
```

**Configuration:**
The NSIS installer is configured in `package.json`:
```json
"win": {
  "target": ["nsis", "portable"],
  "icon": "build/icon.ico",
  "publisherName": "PEFT Studio"
},
"nsis": {
  "oneClick": false,
  "allowToChangeInstallationDirectory": true,
  "createDesktopShortcut": true,
  "createStartMenuShortcut": true
}
```

### macOS Installer (DMG)

The macOS build creates:

1. **DMG Image** (`PEFT-Studio-1.0.0.dmg`)
   - Drag-and-drop installer
   - Standard macOS installation experience

2. **ZIP Archive** (`PEFT-Studio-1.0.0-mac.zip`)
   - Compressed application bundle
   - For direct distribution
   - Inherently portable

**Build Command:**
```bash
npm run package:mac
```

**Configuration:**
```json
"mac": {
  "target": ["dmg", "zip"],
  "icon": "build/icon.icns",
  "category": "public.app-category.developer-tools",
  "hardenedRuntime": true,
  "entitlements": "build/entitlements.mac.plist"
}
```

**Requirements:**
- Must be built on macOS
- Requires Xcode Command Line Tools
- Code signing recommended for distribution

**Entitlements:**
The macOS build includes entitlements for:
- Network access (client and server)
- File system access (user-selected, downloads)
- Keychain access for credentials
- JIT compilation for Python runtime

### Linux Installer (AppImage)

The Linux build creates:

1. **AppImage** (`PEFT-Studio-1.0.0.AppImage`)
   - Universal Linux package
   - Works on most distributions
   - No installation required
   - Inherently portable

2. **DEB Package** (`peft-studio_1.0.0_amd64.deb`)
   - For Debian/Ubuntu-based systems
   - Integrates with system package manager
   - System-wide installation

**Build Command:**
```bash
npm run package:linux
```

**Configuration:**
```json
"linux": {
  "target": ["AppImage", "deb"],
  "icon": "build/icon.png",
  "category": "Development"
}
```

**Running AppImage:**
```bash
chmod +x PEFT-Studio-1.0.0.AppImage
./PEFT-Studio-1.0.0.AppImage
```

## Code Signing

Code signing ensures users that the application comes from a trusted source and hasn't been tampered with.

### Windows Code Signing

1. **Obtain a Code Signing Certificate**
   - Purchase from: DigiCert, Sectigo, GlobalSign
   - Format: `.pfx` or `.p12` file

2. **Set Environment Variables**
   ```bash
   # Windows (PowerShell)
   $env:CSC_LINK = "C:\path\to\certificate.pfx"
   $env:CSC_KEY_PASSWORD = "your_password"
   
   # Windows (Command Prompt)
   set CSC_LINK=C:\path\to\certificate.pfx
   set CSC_KEY_PASSWORD=your_password
   ```

3. **Build with Signing**
   ```bash
   npm run package:win
   ```

**Verification:**
- Right-click the installer → Properties → Digital Signatures
- Should show your certificate information

### macOS Code Signing

1. **Obtain Apple Developer Account**
   - Sign up at https://developer.apple.com
   - Cost: $99/year

2. **Create Developer ID Certificate**
   - Open Xcode → Preferences → Accounts
   - Add your Apple ID
   - Manage Certificates → Create "Developer ID Application"

3. **Set Environment Variables**
   ```bash
   export CSC_LINK=/path/to/certificate.p12
   export CSC_KEY_PASSWORD=your_password
   export APPLE_ID=your@email.com
   export APPLE_ID_PASSWORD=app-specific-password
   ```

4. **Build with Signing**
   ```bash
   npm run package:mac
   ```

**Notarization (Required for macOS 10.15+):**
```bash
# electron-builder handles notarization automatically if credentials are set
export APPLE_ID=your@email.com
export APPLE_ID_PASSWORD=app-specific-password
npm run package:mac
```

**Verification:**
```bash
codesign -dv --verbose=4 release/mac/PEFT\ Studio.app
spctl -a -vv release/mac/PEFT\ Studio.app
```

### Linux Code Signing (Optional)

Linux doesn't require code signing, but you can sign with GPG:

```bash
# Sign AppImage
gpg --detach-sign --armor release/PEFT-Studio-1.0.0.AppImage

# Verify signature
gpg --verify release/PEFT-Studio-1.0.0.AppImage.asc release/PEFT-Studio-1.0.0.AppImage
```

## Portable Versions

### Windows Portable

The Windows portable version is automatically created during the build:

```bash
npm run package:win
```

Output: `release/PEFT-Studio-1.0.0-portable.exe`

**Features:**
- No installation required
- Can run from USB drive
- Settings stored in application directory
- No registry modifications
- No admin rights required

**Usage:**
1. Download portable executable
2. Run directly - no installation
3. All data stored in application folder

### macOS Portable

The macOS `.app` bundle is inherently portable:

```bash
# Extract from DMG or ZIP
unzip release/PEFT-Studio-1.0.0-mac.zip
# Copy PEFT Studio.app anywhere
```

**Features:**
- Can be copied anywhere
- No installation required
- Self-contained application

### Linux Portable

The AppImage is inherently portable:

```bash
chmod +x release/PEFT-Studio-1.0.0.AppImage
./PEFT-Studio-1.0.0.AppImage
```

**Features:**
- No installation required
- Works on most distributions
- Can run from any location

## Build Configuration

The build configuration is in `package.json` under the `build` key:

```json
{
  "build": {
    "appId": "com.peftstudio.app",
    "productName": "PEFT Studio",
    "directories": {
      "output": "release"
    },
    "files": [
      "dist/**/*",
      "electron/**/*",
      "backend/**/*",
      "package.json"
    ],
    "win": {
      "target": ["nsis", "portable"],
      "icon": "build/icon.ico",
      "publisherName": "PEFT Studio"
    },
    "nsis": {
      "oneClick": false,
      "allowToChangeInstallationDirectory": true,
      "createDesktopShortcut": true,
      "createStartMenuShortcut": true
    },
    "mac": {
      "target": ["dmg", "zip"],
      "icon": "build/icon.icns",
      "category": "public.app-category.developer-tools",
      "hardenedRuntime": true,
      "entitlements": "build/entitlements.mac.plist"
    },
    "linux": {
      "target": ["AppImage", "deb"],
      "icon": "build/icon.png",
      "category": "Development"
    },
    "publish": {
      "provider": "github",
      "owner": "your-github-username",
      "repo": "peft-studio"
    }
  }
}
```

### Icon Requirements

Place the following icons in the `build/` directory:

- **Windows:** `icon.ico` (256x256 or multi-resolution)
- **macOS:** `icon.icns` (512x512 or multi-resolution)
- **Linux:** `icon.png` (512x512 PNG)

See `build/README.md` for icon generation instructions.

## Build Scripts

### Cross-Platform Node.js Script

**Location:** `scripts/build.js`

**Features:**
- Platform detection
- Prerequisite checking
- Frontend build automation
- Installer generation
- Output summary with file sizes
- Color-coded console output

**Usage:**
```bash
node scripts/build.js [windows|mac|linux|all]
```

### Unix/Linux/macOS Shell Script

**Location:** `scripts/build.sh`

**Features:**
- Bash-based automation
- Dependency verification
- Build orchestration
- Error handling

**Usage:**
```bash
chmod +x scripts/build.sh
./scripts/build.sh [windows|mac|linux|all]
```

### Windows PowerShell Script

**Location:** `scripts/build.ps1`

**Features:**
- PowerShell-native
- Windows-optimized
- Color-coded output
- Error handling

**Usage:**
```powershell
.\scripts\build.ps1 [windows|mac|linux|all]
```

### Configuration Verification Script

**Location:** `scripts/verify-build-config.js`

**Features:**
- Validates build configuration
- Checks for required files
- Verifies dependencies
- Reports configuration status

**Usage:**
```bash
npm run verify:build
```

## CI/CD Integration

### GitHub Actions Workflows

#### Build Workflow

**Location:** `.github/workflows/build-installers.yml`

**Features:**
- Triggers on version tags (`v*`)
- Builds on all platforms (Ubuntu, Windows, macOS)
- Uploads artifacts with 30-day retention
- Generates SHA256 checksums
- Uploads to GitHub Releases

**Trigger:**
```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

#### Release Workflow

**Location:** `.github/workflows/release.yml`

**Features:**
- Triggers on semantic version tags (`v*.*.*`)
- Creates draft release with template
- Builds and uploads all installers
- Includes installation instructions
- Provides checksums for verification

### Required Secrets

Configure these secrets in your GitHub repository (Settings → Secrets and variables → Actions):

- `CSC_LINK` - Code signing certificate (base64 encoded)
- `CSC_KEY_PASSWORD` - Certificate password
- `APPLE_ID` - Apple ID for notarization (macOS)
- `APPLE_ID_PASSWORD` - App-specific password (macOS)
- `GITHUB_TOKEN` - Automatically provided by GitHub

### Encoding Certificate for GitHub Secrets

```bash
# macOS/Linux
base64 -i certificate.p12 | pbcopy

# Windows (PowerShell)
[Convert]::ToBase64String([IO.File]::ReadAllBytes("certificate.pfx")) | Set-Clipboard
```

### CI Build Process

1. **Tag Version:**
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   ```

2. **Automated Build:**
   - CI builds all platforms simultaneously
   - Uploads to GitHub Releases
   - Generates checksums

3. **Manual Steps:**
   - Review draft release
   - Add release notes
   - Publish release

## Distribution

### GitHub Releases

1. **Create Tag:**
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   ```

2. **Automated Build:**
   - CI builds all platforms
   - Uploads to GitHub Releases
   - Generates checksums

3. **Manual Steps:**
   - Review draft release
   - Add release notes
   - Publish release

### Auto-Update

The application includes auto-update functionality using `electron-updater`:

**Configuration:**
```json
"publish": {
  "provider": "github",
  "owner": "your-github-username",
  "repo": "peft-studio"
}
```

**Features:**
- Checks for updates on startup
- Downloads in background
- Notifies user when ready
- Installs on app quit

**How it Works:**
1. App checks GitHub Releases for newer versions
2. Downloads update in background
3. Shows notification when ready
4. Installs on next app restart

## Troubleshooting

### Build Fails with "Cannot find module"

**Solution:**
```bash
rm -rf node_modules package-lock.json
npm install
npm run package
```

### Windows: "NSIS Error"

**Solution:**
- Ensure you have write permissions to the output directory
- Try running as administrator
- Check antivirus isn't blocking the build
- Verify disk space is available

### macOS: "Code signing failed"

**Solution:**
- Verify certificate is installed in Keychain
- Check certificate hasn't expired
- Ensure CSC_LINK and CSC_KEY_PASSWORD are set correctly
- Verify certificate is for "Developer ID Application"

### Linux: "AppImage build failed"

**Solution:**
```bash
# Install required dependencies
sudo apt-get install -y rpm fakeroot dpkg
npm run package:linux
```

### Large Bundle Size

**Solution:**
- Run bundle analyzer: `npm run build:analyze`
- Check for duplicate dependencies
- Ensure tree shaking is working
- Consider lazy loading heavy components
- Review included files in build configuration

### Slow Build Times

**Solution:**
- Use platform-specific builds instead of building all platforms
- Enable build caching
- Use faster disk (SSD)
- Increase Node.js memory: `NODE_OPTIONS=--max-old-space-size=4096`
- Close unnecessary applications

### Missing Icons

**Solution:**
- Add icon files to `build/` directory
- See `build/README.md` for icon generation instructions
- Verify icon file names match configuration

### Code Signing Certificate Issues

**Windows:**
- Verify certificate is in `.pfx` or `.p12` format
- Check certificate is valid and not expired
- Ensure password is correct

**macOS:**
- Verify certificate is in Keychain Access
- Check certificate type is "Developer ID Application"
- Ensure app-specific password is generated for notarization

## Testing Installers

### Local Testing

**Windows:**
```bash
npm run package:win
# Test installer
release\PEFT-Studio-Setup-1.0.0.exe
# Test portable
release\PEFT-Studio-1.0.0-portable.exe
```

**macOS:**
```bash
npm run package:mac
# Test DMG
open release/PEFT-Studio-1.0.0.dmg
# Test ZIP
unzip release/PEFT-Studio-1.0.0-mac.zip
open "PEFT Studio.app"
```

**Linux:**
```bash
npm run package:linux
# Test AppImage
chmod +x release/PEFT-Studio-1.0.0.AppImage
./release/PEFT-Studio-1.0.0.AppImage
# Test DEB
sudo dpkg -i release/peft-studio_1.0.0_amd64.deb
peft-studio
```

### CI Testing

Automated builds run on:
- Ubuntu Latest
- Windows Latest
- macOS Latest

Artifacts are uploaded for manual testing and can be downloaded from the GitHub Actions tab.

## Best Practices

### Version Management

- Use semantic versioning (e.g., v1.0.0)
- Tag releases in git
- Update version in package.json before building
- Keep changelog updated

### Security

- Always sign installers for production releases
- Use strong passwords for certificates
- Store certificates securely
- Never commit certificates to version control
- Use GitHub Secrets for CI/CD

### Build Process

- Test builds locally before pushing tags
- Verify all platforms build successfully
- Test installers on target platforms
- Check file sizes are reasonable
- Verify auto-update functionality

### Documentation

- Keep release notes updated
- Document breaking changes
- Provide installation instructions
- Include checksums for verification

## Support

For issues or questions:
- Review this guide for detailed instructions
- Check troubleshooting section
- Review GitHub Actions logs for CI failures
- Consult electron-builder documentation: https://www.electron.build/
- Open an issue on GitHub

## Related Documentation

- `build/README.md` - Icon requirements and generation
- `.github/workflows/` - CI/CD workflow configurations
- `scripts/` - Build script implementations
- `docs/developer-guide/ci-cd-setup.md` - CI/CD setup guide

## Summary

This guide covers the complete build and distribution process for PEFT Studio:

- **Build Commands:** Simple npm scripts for all platforms
- **Code Signing:** Support for Windows, macOS, and Linux
- **Portable Versions:** Available for all platforms
- **CI/CD:** Automated builds with GitHub Actions
- **Distribution:** GitHub Releases with auto-update
- **Troubleshooting:** Common issues and solutions

The build system is production-ready and supports all major platforms with comprehensive automation and documentation.
