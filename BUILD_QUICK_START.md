# Build Quick Start Guide

Quick reference for building PEFT Studio installers.

## Prerequisites

```bash
# Check Node.js version (requires v18+)
node --version

# Install dependencies
npm install
```

## Build Commands

### Build All Platforms

```bash
npm run package:all
```

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

## Output Location

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

## Code Signing (Optional)

### Windows

```bash
# PowerShell
$env:CSC_LINK = "C:\path\to\certificate.pfx"
$env:CSC_KEY_PASSWORD = "your_password"

# Then build
npm run package:win
```

### macOS

```bash
export CSC_LINK=/path/to/certificate.p12
export CSC_KEY_PASSWORD=your_password
export APPLE_ID=your@email.com
export APPLE_ID_PASSWORD=app-specific-password

# Then build
npm run package:mac
```

## Testing Installers

### Windows

```bash
# Test installer
release\PEFT-Studio-Setup-1.0.0.exe

# Test portable
release\PEFT-Studio-1.0.0-portable.exe
```

### macOS

```bash
# Test DMG
open release/PEFT-Studio-1.0.0.dmg

# Test ZIP
unzip release/PEFT-Studio-1.0.0-mac.zip
open "PEFT Studio.app"
```

### Linux

```bash
# Test AppImage
chmod +x release/PEFT-Studio-1.0.0.AppImage
./release/PEFT-Studio-1.0.0.AppImage

# Test DEB
sudo dpkg -i release/peft-studio_1.0.0_amd64.deb
peft-studio
```

## Creating a Release

```bash
# 1. Tag version
git tag -a v1.0.0 -m "Release v1.0.0"

# 2. Push tag (triggers CI build)
git push origin v1.0.0

# 3. CI automatically builds and uploads to GitHub Releases
```

## Troubleshooting

### Build fails

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run package
```

### Missing icons

Add icon files to `build/` directory:
- `icon.ico` (Windows)
- `icon.icns` (macOS)
- `icon.png` (Linux)

See `build/README.md` for icon generation instructions.

## Full Documentation

For detailed instructions, see:
- `INSTALLER_GUIDE.md` - Complete build and distribution guide
- `INSTALLER_PACKAGES_IMPLEMENTATION.md` - Implementation details
- `build/README.md` - Icon requirements and generation

## Support

- Documentation: `docs/`
- Issues: GitHub Issues
- CI Logs: GitHub Actions tab
