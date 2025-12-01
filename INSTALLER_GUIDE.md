# PEFT Studio Installer Guide

This guide explains how to build installers for PEFT Studio on Windows, macOS, and Linux.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Platform-Specific Builds](#platform-specific-builds)
- [Code Signing](#code-signing)
- [Portable Versions](#portable-versions)
- [Troubleshooting](#troubleshooting)

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

## Quick Start

### Build All Platforms

```bash
# Using npm scripts
npm run package:all

# Or using build scripts
node scripts/build.js all
```

This will create installers for Windows, macOS, and Linux in the `release/` directory.

### Build Single Platform

```bash
# Windows
npm run package:win

# macOS
npm run package:mac

# Linux
npm run package:linux
```

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

**Build Command:**
```bash
npm run package:win
```

**Output Location:**
```
release/
├── PEFT-Studio-Setup-1.0.0.exe
└── PEFT-Studio-1.0.0-portable.exe
```

**Configuration:**
The NSIS installer is configured in `package.json`:
```json
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

**Build Command:**
```bash
npm run package:mac
```

**Output Location:**
```
release/
├── PEFT-Studio-1.0.0.dmg
└── PEFT-Studio-1.0.0-mac.zip
```

**Requirements:**
- Must be built on macOS
- Requires Xcode Command Line Tools
- Code signing recommended for distribution

### Linux Installer (AppImage)

The Linux build creates:

1. **AppImage** (`PEFT-Studio-1.0.0.AppImage`)
   - Universal Linux package
   - Works on most distributions
   - No installation required

2. **DEB Package** (`peft-studio_1.0.0_amd64.deb`)
   - For Debian/Ubuntu-based systems
   - Integrates with system package manager

**Build Command:**
```bash
npm run package:linux
```

**Output Location:**
```
release/
├── PEFT-Studio-1.0.0.AppImage
└── peft-studio_1.0.0_amd64.deb
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

### macOS Portable

The macOS `.app` bundle is inherently portable:

```bash
# Extract from DMG or ZIP
unzip release/PEFT-Studio-1.0.0-mac.zip
# Copy PEFT Studio.app anywhere
```

### Linux Portable

The AppImage is inherently portable:

```bash
chmod +x release/PEFT-Studio-1.0.0.AppImage
./PEFT-Studio-1.0.0.AppImage
```

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

## Icon Requirements

Place the following icons in the `build/` directory:

- **Windows:** `icon.ico` (256x256 or multi-resolution)
- **macOS:** `icon.icns` (512x512 or multi-resolution)
- **Linux:** `icon.png` (512x512 PNG)

See `build/README.md` for icon generation instructions.

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

### macOS: "Code signing failed"

**Solution:**
- Verify certificate is installed in Keychain
- Check certificate hasn't expired
- Ensure CSC_LINK and CSC_KEY_PASSWORD are set correctly

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

### Slow Build Times

**Solution:**
- Use platform-specific builds instead of building all platforms
- Enable build caching
- Use faster disk (SSD)
- Increase Node.js memory: `NODE_OPTIONS=--max-old-space-size=4096`

## CI/CD Integration

### GitHub Actions

Create `.github/workflows/build.yml`:

```yaml
name: Build Installers

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: npm install
      
      - name: Build
        run: npm run package
        env:
          CSC_LINK: ${{ secrets.CSC_LINK }}
          CSC_KEY_PASSWORD: ${{ secrets.CSC_KEY_PASSWORD }}
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: installers-${{ matrix.os }}
          path: release/*
```

## Distribution

### GitHub Releases

1. Create a new release on GitHub
2. Upload installers from `release/` directory
3. Add release notes

### Auto-Update

The app includes auto-update functionality using `electron-updater`:

1. Configure `publish` in `package.json`:
   ```json
   "publish": {
     "provider": "github",
     "owner": "your-username",
     "repo": "peft-studio"
   }
   ```

2. Build and publish:
   ```bash
   npm run package
   # Upload to GitHub Releases
   ```

3. Users will be notified of updates automatically

## Support

For issues or questions:
- GitHub Issues: https://github.com/your-username/peft-studio/issues
- Documentation: https://github.com/your-username/peft-studio/docs

## License

See LICENSE file for details.
