# Installer Build Guide

This guide explains how to build installers for PEFT Studio on Windows, macOS, and Linux.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Building Installers](#building-installers)
- [Platform-Specific Instructions](#platform-specific-instructions)
- [Automated Builds with GitHub Actions](#automated-builds-with-github-actions)
- [Troubleshooting](#troubleshooting)
- [Distribution](#distribution)

## Overview

PEFT Studio uses [electron-builder](https://www.electron.build/) to create installers for all major platforms. The build configuration is defined in `package.json` under the `build` section.

### Supported Formats

- **Windows**: NSIS installer (.exe) and Portable (.exe)
- **macOS**: DMG (.dmg) and ZIP (.zip)
- **Linux**: AppImage (.AppImage) and Debian package (.deb)

## Prerequisites

### All Platforms

- Node.js 18 or higher
- npm or yarn
- Git

### Windows

- Windows 10 or higher
- No additional requirements for building Windows installers

### macOS

- macOS 10.13 or higher
- Xcode Command Line Tools: `xcode-select --install`
- For code signing: Apple Developer account and certificates

### Linux

- Ubuntu 18.04+ or equivalent
- Required packages:
  ```bash
  sudo apt-get install -y build-essential libssl-dev
  ```

## Building Installers

### Step 1: Install Dependencies

```bash
# Clone the repository
git clone https://github.com/Ankesh-007/peft-studio.git
cd peft-studio

# Install Node.js dependencies
npm install
```

### Step 2: Build the Frontend

```bash
# Build with type checking
npm run build

# Or build without type checking (faster)
npm run build:no-check
```

### Step 3: Build Installers

```bash
# Build for your current platform
npm run electron:build

# Or use platform-specific commands
npm run package:win      # Windows
npm run package:mac      # macOS
npm run package:linux    # Linux
```

The installers will be created in the `release/` directory.

## Platform-Specific Instructions

### Windows

#### Building on Windows

```bash
# Build Windows installers
npm run package:win
```

This creates:
- `PEFT Studio Setup 1.0.0.exe` - NSIS installer
- `PEFT Studio 1.0.0.exe` - Portable version

#### Code Signing (Optional)

To sign Windows installers, you need a code signing certificate:

1. Obtain a code signing certificate (e.g., from DigiCert, Sectigo)
2. Set environment variables:
   ```powershell
   $env:CSC_LINK = "path\to\certificate.pfx"
   $env:CSC_KEY_PASSWORD = "certificate-password"
   ```
3. Build with signing:
   ```bash
   npm run package:win
   ```

#### Troubleshooting Windows Builds

**Issue: "A required privilege is not held by the client"**

This error occurs when building without administrator privileges. Solutions:
1. Run PowerShell or Command Prompt as Administrator
2. Or disable code signing in `package.json`:
   ```json
   "win": {
     "sign": null
   }
   ```

### macOS

#### Building on macOS

```bash
# Build macOS installers
npm run package:mac
```

This creates:
- `PEFT Studio-1.0.0.dmg` - DMG installer
- `PEFT Studio-1.0.0-mac.zip` - ZIP archive

#### Code Signing and Notarization (Required for Distribution)

To distribute macOS apps, you must sign and notarize them:

1. **Get Apple Developer certificates:**
   - Join the Apple Developer Program ($99/year)
   - Create certificates in Xcode or Apple Developer portal

2. **Set environment variables:**
   ```bash
   export CSC_LINK="path/to/certificate.p12"
   export CSC_KEY_PASSWORD="certificate-password"
   export APPLE_ID="your-apple-id@email.com"
   export APPLE_ID_PASSWORD="app-specific-password"
   export APPLE_TEAM_ID="your-team-id"
   ```

3. **Build with signing and notarization:**
   ```bash
   npm run package:mac
   ```

#### Creating Entitlements File

Create `build/entitlements.mac.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>com.apple.security.cs.allow-jit</key>
  <true/>
  <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
  <true/>
  <key>com.apple.security.cs.disable-library-validation</key>
  <true/>
</dict>
</plist>
```

### Linux

#### Building on Linux

```bash
# Build Linux installers
npm run package:linux
```

This creates:
- `PEFT Studio-1.0.0.AppImage` - Universal AppImage
- `peft-studio_1.0.0_amd64.deb` - Debian package

#### AppImage

AppImage is the recommended format for Linux as it works on all distributions:

```bash
# Make AppImage executable
chmod +x "PEFT Studio-1.0.0.AppImage"

# Run it
./PEFT\ Studio-1.0.0.AppImage
```

#### Debian Package

For Debian/Ubuntu users:

```bash
# Install the package
sudo dpkg -i peft-studio_1.0.0_amd64.deb

# Fix dependencies if needed
sudo apt-get install -f
```

## Automated Builds with GitHub Actions

The project includes a GitHub Actions workflow (`.github/workflows/build-installers.yml`) that automatically builds installers for all platforms.

### Triggering Automated Builds

#### Method 1: Push a Version Tag

```bash
# Create a new version tag
git tag v1.0.1

# Push the tag
git push origin v1.0.1
```

This will:
1. Build installers for Windows, macOS, and Linux
2. Create a new GitHub Release
3. Upload all installers to the release

#### Method 2: Manual Workflow Dispatch

1. Go to your repository on GitHub
2. Click "Actions" tab
3. Select "Build Installers" workflow
4. Click "Run workflow"
5. Choose the branch and click "Run workflow"

### Workflow Overview

The workflow consists of four jobs:

1. **build-windows**: Builds Windows installers on `windows-latest`
2. **build-macos**: Builds macOS installers on `macos-latest`
3. **build-linux**: Builds Linux installers on `ubuntu-latest`
4. **create-release**: Creates a GitHub Release with all installers

### Secrets Required

For the workflow to work properly, set these secrets in your repository:

- `GITHUB_TOKEN` - Automatically provided by GitHub Actions
- `CSC_LINK` - (Optional) Code signing certificate for Windows/macOS
- `CSC_KEY_PASSWORD` - (Optional) Certificate password
- `APPLE_ID` - (Optional) Apple ID for macOS notarization
- `APPLE_ID_PASSWORD` - (Optional) App-specific password
- `APPLE_TEAM_ID` - (Optional) Apple Team ID

To add secrets:
1. Go to repository Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add each secret

## Troubleshooting

### Common Issues

#### Build Fails with TypeScript Errors

Use the no-check build command:
```bash
npm run build:no-check
```

#### "electron" or "electron-builder" in dependencies

These packages must be in `devDependencies`, not `dependencies`:

```json
{
  "devDependencies": {
    "electron": "^39.2.4",
    "electron-builder": "^25.1.8"
  }
}
```

#### macOS: "Build for macOS is supported only on macOS"

You cannot build macOS installers on Windows or Linux. Use:
- A Mac computer
- GitHub Actions (builds on macOS runner)
- A macOS virtual machine

#### Linux: Permission Denied for AppImage

Make the AppImage executable:
```bash
chmod +x "PEFT Studio-1.0.0.AppImage"
```

#### Windows: SmartScreen Warning

Unsigned Windows applications trigger SmartScreen warnings. To avoid this:
1. Sign your application with a code signing certificate
2. Build reputation by having users click "More info" → "Run anyway"

### Build Configuration

The build configuration is in `package.json`:

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
      "icon": "build/icon.ico"
    },
    "mac": {
      "target": ["dmg", "zip"],
      "icon": "build/icon.icns",
      "category": "public.app-category.developer-tools"
    },
    "linux": {
      "target": ["AppImage", "deb"],
      "icon": "build/icon.png",
      "category": "Development"
    }
  }
}
```

### Icons

Place platform-specific icons in the `build/` directory:

- **Windows**: `build/icon.ico` (256x256 or larger)
- **macOS**: `build/icon.icns` (512x512 or larger)
- **Linux**: `build/icon.png` (512x512 or larger)

You can generate icons from a single PNG using tools like:
- [electron-icon-builder](https://www.npmjs.com/package/electron-icon-builder)
- [icon-gen](https://www.npmjs.com/package/icon-gen)

## Distribution

### GitHub Releases

The recommended way to distribute PEFT Studio is through GitHub Releases:

1. Build installers (manually or via GitHub Actions)
2. Create a new release on GitHub
3. Upload installers as release assets
4. Write release notes
5. Publish the release

### Auto-Updates

PEFT Studio includes auto-update functionality using `electron-updater`. When you publish a new release on GitHub:

1. Users will be notified of the update
2. They can download and install it with one click
3. The app will restart with the new version

Configure auto-updates in `package.json`:

```json
{
  "build": {
    "publish": {
      "provider": "github",
      "owner": "Ankesh-007",
      "repo": "peft-studio"
    }
  }
}
```

### Alternative Distribution Methods

- **Direct Download**: Host installers on your own server
- **Package Managers**: 
  - Windows: Chocolatey, Scoop
  - macOS: Homebrew Cask
  - Linux: Snap, Flatpak
- **App Stores**:
  - Microsoft Store (Windows)
  - Mac App Store (macOS)
  - Snap Store (Linux)

## Next Steps

- [Auto-Update System](auto-update-system.md) - Configure automatic updates
- [CI/CD Setup](ci-cd-setup.md) - Set up continuous integration
- [Build and Installers](build-and-installers.md) - General build documentation

## Resources

- [electron-builder Documentation](https://www.electron.build/)
- [Code Signing Guide](https://www.electron.build/code-signing)
- [macOS Notarization](https://www.electron.build/configuration/mac#notarization)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
