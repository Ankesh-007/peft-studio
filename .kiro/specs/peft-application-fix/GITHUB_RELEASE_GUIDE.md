# GitHub Release Guide for v1.0.1

## Overview

This guide provides step-by-step instructions for creating and publishing the PEFT Studio v1.0.1 release on GitHub.

## Prerequisites

Before creating the release:

- ✅ Version bumped to 1.0.1 in `package.json`
- ✅ CHANGELOG.md updated with release notes
- ✅ All code changes committed and pushed to main branch
- ⏳ Installers built for all platforms (via GitHub Actions)
- ⏳ Checksums generated (`SHA256SUMS.txt`)
- ⏳ Installers tested on clean systems

## Release Process

### Step 1: Create and Push Git Tag

```bash
# Ensure you're on the main branch with latest changes
git checkout main
git pull origin main

# Create annotated tag
git tag -a v1.0.1 -m "Release version 1.0.1 - Backend fixes and PEFT display improvements"

# Push tag to GitHub
git push origin v1.0.1
```

**Note**: Pushing the tag will trigger the GitHub Actions release workflow if configured.

### Step 2: Wait for GitHub Actions Build

If you have GitHub Actions configured (`.github/workflows/release.yml`):

1. Go to: `https://github.com/Ankesh-007/peft-studio/actions`
2. Find the workflow run triggered by the v1.0.1 tag
3. Wait for all builds to complete:
   - Windows installer build
   - macOS installer build (Intel + Apple Silicon)
   - Linux installer build (AppImage + DEB)
   - Checksum generation
4. Verify all jobs succeeded (green checkmarks)

### Step 3: Create GitHub Release

#### Option A: Automated (if GitHub Actions is configured)

The release workflow should automatically:
- Create a draft release
- Upload all installers
- Upload checksums file
- Add release notes from CHANGELOG.md

Review the draft release and publish it.

#### Option B: Manual Release Creation

1. **Navigate to Releases**:
   - Go to: `https://github.com/Ankesh-007/peft-studio/releases`
   - Click "Draft a new release"

2. **Configure Release**:
   - **Tag**: Select `v1.0.1` from dropdown
   - **Release title**: `PEFT Studio v1.0.1`
   - **Description**: Copy from CHANGELOG.md (see template below)

3. **Upload Assets**:
   Upload all installer files and checksums:
   
   **Windows**:
   - `PEFT Studio-Setup-1.0.1.exe`
   - `PEFT Studio-Portable-1.0.1.exe`
   
   **macOS**:
   - `PEFT Studio-1.0.1-x64.dmg`
   - `PEFT Studio-1.0.1-arm64.dmg`
   - `PEFT Studio-1.0.1-x64.zip`
   - `PEFT Studio-1.0.1-arm64.zip`
   
   **Linux**:
   - `PEFT Studio-1.0.1-x64.AppImage`
   - `PEFT Studio-1.0.1-x64.deb`
   
   **Checksums**:
   - `SHA256SUMS.txt`

4. **Set as Latest Release**:
   - Check "Set as the latest release"
   - Uncheck "Set as a pre-release" (unless this is a beta)

5. **Publish**:
   - Click "Publish release"

## Release Notes Template

Use this template for the GitHub release description:

```markdown
# PEFT Studio v1.0.1

This release fixes critical issues with backend service initialization and adds complete PEFT algorithm display.

## 🐛 Fixed

- **Backend Service Not Starting**: Fixed critical issue where Python backend service was not initializing properly, causing blank window on application startup
- **Backend Health Monitoring**: Added automatic health check polling and restart mechanism for crashed backend services
- **Port Conflict Resolution**: Implemented automatic alternative port selection when default port is in use
- **Dependency Verification**: Added comprehensive dependency checking on startup with clear error messages and fix instructions

## ✨ Added

- **PEFT Algorithm Display**: All five PEFT algorithms now visible in UI (LoRA, QLoRA, DoRA, PiSSA, RSLoRA) with descriptions and parameter controls
- **Algorithm Metadata**: Added detailed descriptions, recommended use cases, and parameter definitions for each PEFT algorithm
- **Dependency Status UI**: New component displays Python version, CUDA availability, and package installation status on startup
- **Startup Error Screen**: Clear error messages with diagnostic information and actionable recovery steps
- **Enhanced Splash Screen**: Progress indicators showing current initialization step during startup
- **Health Check Endpoints**: New `/api/health`, `/api/dependencies`, and `/api/startup/status` endpoints for monitoring

## 🔧 Improved

- **Error Handling**: Comprehensive error recovery mechanisms with automatic restart and manual recovery options
- **User Feedback**: Real-time status updates during application startup with progress indicators
- **Error Messages**: All errors now include what went wrong, why it happened, and how to fix it
- **Backend Process Management**: Robust Python process lifecycle management with proper cleanup on exit
- **Startup Flow**: Streamlined initialization sequence with better error detection and reporting

## 🧹 Cleaned

- **Repository Size**: Removed build artifacts, test caches, and redundant documentation files
- **Build Artifacts**: Cleaned `release/`, `dist/`, and `build/` directories (except essential files)
- **Test Artifacts**: Removed `.hypothesis/` and `.pytest_cache/` directories
- **Documentation**: Consolidated redundant completion status files into CHANGELOG

## 📦 Downloads

### Windows
- **Installer**: `PEFT Studio-Setup-1.0.1.exe` (Recommended)
- **Portable**: `PEFT Studio-Portable-1.0.1.exe`

### macOS
- **Intel**: `PEFT Studio-1.0.1-x64.dmg`
- **Apple Silicon**: `PEFT Studio-1.0.1-arm64.dmg`

### Linux
- **AppImage**: `PEFT Studio-1.0.1-x64.AppImage` (Universal)
- **Debian/Ubuntu**: `PEFT Studio-1.0.1-x64.deb`

### Checksums
- **SHA256**: `SHA256SUMS.txt`

## 🔐 Verifying Downloads

To verify the integrity of your download:

**Windows (PowerShell)**:
```powershell
$hash = (Get-FileHash -Algorithm SHA256 "PEFT Studio-Setup-1.0.1.exe").Hash.ToLower()
# Compare with SHA256SUMS.txt
```

**macOS/Linux**:
```bash
shasum -a 256 -c SHA256SUMS.txt
```

See [Checksum Verification Guide](https://github.com/Ankesh-007/peft-studio/blob/main/docs/user-guide/checksum-verification.md) for detailed instructions.

## 📋 System Requirements

**Minimum**:
- OS: Windows 10, macOS 11, or Ubuntu 20.04
- RAM: 8GB
- Storage: 10GB free space
- CPU: 4-core processor

**Recommended**:
- OS: Windows 11, macOS 13, or Ubuntu 22.04
- RAM: 16GB or more
- Storage: 50GB+ free space
- GPU: NVIDIA GPU with 8GB+ VRAM and CUDA support
- CPU: 8-core processor or better

## 🚀 Getting Started

1. Download the installer for your platform
2. Verify the checksum (recommended)
3. Install PEFT Studio
4. Launch the application
5. Follow the dependency check prompts if needed
6. Start fine-tuning!

For detailed instructions, see the [Quick Start Guide](https://github.com/Ankesh-007/peft-studio/blob/main/docs/user-guide/quick-start.md).

## 📚 Documentation

- [Installation Guide](https://github.com/Ankesh-007/peft-studio/blob/main/docs/user-guide/installation.md)
- [Troubleshooting](https://github.com/Ankesh-007/peft-studio/blob/main/docs/reference/troubleshooting.md)
- [Full Documentation](https://github.com/Ankesh-007/peft-studio/tree/main/docs)

## 🐛 Known Issues

- GPU training requires CUDA-compatible NVIDIA GPU
- Some cloud providers require manual credential setup
- Large model downloads may take significant time depending on connection speed

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/Ankesh-007/peft-studio/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Ankesh-007/peft-studio/discussions)
- **Security**: See [SECURITY.md](https://github.com/Ankesh-007/peft-studio/blob/main/SECURITY.md)

## 🔄 Upgrading from v1.0.0

This release includes automatic update support. If you have v1.0.0 installed:

1. Launch PEFT Studio
2. You should see an update notification
3. Click "Download Update" to install v1.0.1
4. Restart the application

Alternatively, download and install manually from this release page.

## 📝 Full Changelog

See [CHANGELOG.md](https://github.com/Ankesh-007/peft-studio/blob/main/CHANGELOG.md) for complete details.

---

**Full Changelog**: https://github.com/Ankesh-007/peft-studio/compare/v1.0.0...v1.0.1
```

## Post-Release Tasks

### 1. Verify Release

After publishing:

1. **Check release page**: Verify all assets uploaded correctly
2. **Test download links**: Download one installer and verify it works
3. **Verify checksums**: Ensure SHA256SUMS.txt is correct
4. **Check auto-update**: Verify update notification appears in v1.0.0

### 2. Update Documentation

If needed, update:

- README.md (update version badges)
- Installation guides (if process changed)
- Troubleshooting docs (add new known issues)

### 3. Announce Release

Consider announcing on:

- GitHub Discussions
- Project website (if applicable)
- Social media (if applicable)
- User mailing list (if applicable)

### 4. Monitor for Issues

After release:

- Watch GitHub Issues for bug reports
- Monitor Discussions for user questions
- Check download statistics
- Gather user feedback

## Rollback Procedure

If critical issues are discovered:

1. **Mark release as pre-release**:
   - Edit the release
   - Check "Set as a pre-release"
   - Add warning to description

2. **Create hotfix**:
   - Fix critical issues
   - Release v1.0.2 immediately

3. **Communicate**:
   - Post issue on GitHub
   - Notify users via available channels
   - Provide workaround if possible

## Release Checklist

Before marking release as complete:

- [ ] Git tag created and pushed
- [ ] GitHub Actions build completed successfully
- [ ] All installers built and tested
- [ ] Checksums generated and verified
- [ ] GitHub release created
- [ ] All assets uploaded
- [ ] Release notes complete and accurate
- [ ] Release marked as latest
- [ ] Release published (not draft)
- [ ] Download links tested
- [ ] Auto-update tested (if applicable)
- [ ] Documentation updated
- [ ] Release announced

## Related Files

- `CHANGELOG.md` - Source for release notes
- `package.json` - Version number
- `.github/workflows/release.yml` - Automated release workflow
- `scripts/generate-checksums.js` - Checksum generation
- `docs/user-guide/checksum-verification.md` - User verification guide

## GitHub Actions Configuration

If using automated releases, ensure `.github/workflows/release.yml` includes:

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    # Build installers for all platforms
    
  release:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            release/*.exe
            release/*.dmg
            release/*.zip
            release/*.AppImage
            release/*.deb
            release/SHA256SUMS.txt
          body_path: .github/release-notes.md
          draft: false
          prerelease: false
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Conclusion

Following this guide ensures a smooth, professional release process for PEFT Studio v1.0.1. The release will be properly documented, verified, and accessible to users across all platforms.
