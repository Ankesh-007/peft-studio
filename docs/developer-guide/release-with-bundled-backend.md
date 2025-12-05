# Release Process with Bundled Backend

This guide explains the release process for PEFT Studio with the bundled Python backend, including additional steps and considerations specific to backend bundling.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Pre-Release Checklist](#pre-release-checklist)
- [Release Steps](#release-steps)
- [Platform-Specific Considerations](#platform-specific-considerations)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Post-Release](#post-release)

## Overview

With the bundled Python backend, the release process includes additional steps to ensure:

- Backend executable is correctly built for each platform
- All Python dependencies are included
- Data files are bundled properly
- Backend integrates correctly with Electron
- Auto-updater includes backend executable
- Platform-specific requirements are met

### What's Different

Compared to releases without bundled backend:

- **Larger Installers**: 1-3GB instead of 100-200MB
- **Backend Build Step**: PyInstaller compilation before Electron build
- **Platform-Specific Builds**: Must build on each target platform
- **Additional Testing**: Backend-specific integration tests
- **Longer Build Times**: 10-20 minutes per platform

## Prerequisites

### Development Environment

#### All Platforms

1. **Node.js 18+**
   ```bash
   node --version
   ```

2. **Python 3.10+**
   ```bash
   python --version
   ```

3. **PyInstaller 5.0+**
   ```bash
   pip install pyinstaller
   pyinstaller --version
   ```

4. **Backend Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

5. **Verify Build Environment**
   ```bash
   npm run verify:build:env
   ```

#### Platform-Specific

**Windows:**
- Windows 10+ (64-bit)
- Visual C++ Redistributable
- Code signing certificate (optional)

**macOS:**
- macOS 10.15+
- Xcode Command Line Tools: `xcode-select --install`
- Apple Developer account (for signing/notarization)

**Linux:**
- Ubuntu 20.04+ or equivalent
- Build essentials: `sudo apt-get install build-essential`

### Environment Variables

```bash
# Required for GitHub release
export GITHUB_TOKEN="your_github_token"

# Optional: Code signing (Windows/macOS)
export CSC_LINK="/path/to/certificate"
export CSC_KEY_PASSWORD="certificate_password"

# Optional: macOS notarization
export APPLE_ID="your@email.com"
export APPLE_ID_PASSWORD="app-specific-password"
export APPLE_TEAM_ID="your_team_id"
```

## Pre-Release Checklist

### Code and Documentation

- [ ] All code changes committed and pushed
- [ ] Version updated in `package.json`
- [ ] CHANGELOG.md updated with release notes
- [ ] README.md updated if needed
- [ ] Documentation updated for new features
- [ ] All tests passing: `npm test`

### Backend-Specific Checks

- [ ] Backend dependencies up to date: `pip list --outdated`
- [ ] PyInstaller spec file updated if needed
- [ ] Hidden imports list complete
- [ ] Data files list complete
- [ ] Runtime path resolution tested
- [ ] Backend unit tests passing: `cd backend && pytest`

### Build Environment

- [ ] Build environment verified: `npm run verify:build:env`
- [ ] PyInstaller installed: `pyinstaller --version`
- [ ] Sufficient disk space (10GB+ per platform)
- [ ] Clean working directory: `git status`
- [ ] No uncommitted changes

### Testing

- [ ] Backend builds successfully: `npm run build:backend`
- [ ] Backend executable runs: `./backend/dist/peft_engine`
- [ ] Integration tests pass: `npm run test:integration`
- [ ] Manual testing completed (see [Testing Guide](testing-bundled-backend.md))

## Release Steps

### Step 1: Prepare Release

```bash
# Update version
npm version patch  # or minor, or major

# Update CHANGELOG.md
# Add release notes for this version

# Commit changes
git add package.json CHANGELOG.md
git commit -m "chore: prepare release v1.0.0"
git push
```

### Step 2: Build Backend (All Platforms)

The backend must be built on each target platform. You can either:

**Option A: Build Locally (if you have all platforms)**

```bash
# On Windows
npm run build:backend:win

# On macOS
npm run build:backend:mac

# On Linux
npm run build:backend:linux
```

**Option B: Use CI/CD (Recommended)**

Push a version tag to trigger automated builds:

```bash
git tag v1.0.0
git push origin v1.0.0
```

The CI/CD workflow will build on all platforms automatically.

### Step 3: Verify Backend Builds

```bash
# Verify backend executable exists
npm run build:backend:verify

# Test backend executable
cd backend/dist
./peft_engine  # Should start without errors

# Test health endpoint
curl http://localhost:8000/api/health
```

### Step 4: Build Complete Application

```bash
# Build for current platform
npm run build:all

# Or build for specific platform
npm run build:win    # Windows
npm run build:mac    # macOS
npm run build:linux  # Linux
```

This will:
1. Build the backend (if not already built)
2. Verify backend build
3. Build the frontend
4. Package with electron-builder
5. Create installer

### Step 5: Test Installers

Test the installer on a clean system (or VM):

**Windows:**
```bash
# Install
.\release\PEFT-Studio-Setup-1.0.0.exe

# Launch and test
# - Backend starts automatically
# - No console window appears
# - All features work
# - Clean shutdown (no zombie processes)

# Uninstall
# Control Panel → Programs → Uninstall
```

**macOS:**
```bash
# Install
open release/PEFT-Studio-1.0.0.dmg
# Drag to Applications

# Launch and test
open /Applications/PEFT\ Studio.app

# Uninstall
rm -rf /Applications/PEFT\ Studio.app
```

**Linux:**
```bash
# Make executable
chmod +x release/PEFT-Studio-1.0.0.AppImage

# Run
./release/PEFT-Studio-1.0.0.AppImage

# Test all features
```

### Step 6: Generate Checksums

```bash
# Generate SHA256 checksums for all installers
node scripts/generate-checksums.js

# Verify checksums file created
cat release/checksums.txt
```

### Step 7: Create GitHub Release

```bash
# Create release and upload assets
node scripts/release-to-github.js

# Or create draft release
node scripts/release-to-github.js --draft

# Or use complete release script
node scripts/complete-release.js
```

This will:
1. Create GitHub release
2. Upload all installers
3. Upload checksums file
4. Add release notes from CHANGELOG.md

### Step 8: Verify Release

1. Go to GitHub Releases page
2. Verify all assets are uploaded:
   - Windows installer (.exe)
   - Windows portable (.exe)
   - macOS DMG (.dmg)
   - macOS ZIP (.zip)
   - Linux AppImage (.AppImage)
   - Linux DEB (.deb)
   - Checksums file (checksums.txt)
3. Verify file sizes are reasonable (1-3GB per installer)
4. Download and test one installer from each platform

### Step 9: Publish Release

If you created a draft release:

1. Review release notes
2. Test download links
3. Click "Publish release"

The auto-updater will now distribute the update to users.

## Platform-Specific Considerations

### Windows

**Installer Size:**
- Expect 1.5-2.5GB installer
- Includes Python backend (~1-2GB)
- NSIS compression reduces size

**Code Signing:**
- Highly recommended to avoid SmartScreen warnings
- Requires code signing certificate
- Sign both application and installer

**Testing:**
- Test on Windows 10 and Windows 11
- Test with Windows Defender enabled
- Verify no console window appears
- Test auto-update functionality

**Common Issues:**
- Antivirus false positives (add to exclusions)
- SmartScreen warnings (sign the installer)
- Permission errors (run as administrator)

### macOS

**Installer Size:**
- Expect 1.5-2.5GB DMG
- Universal binary (x64 + arm64) is larger
- DMG compression reduces size

**Code Signing and Notarization:**
- Required for distribution
- Requires Apple Developer account ($99/year)
- Must notarize with Apple
- Process takes 5-15 minutes

**Testing:**
- Test on Intel and Apple Silicon Macs
- Test on macOS 10.15, 11, 12, 13, 14
- Verify Gatekeeper doesn't block
- Test auto-update functionality

**Common Issues:**
- "App is damaged" (notarization failed)
- "Cannot verify developer" (not signed)
- Gatekeeper blocks (not notarized)

### Linux

**Installer Size:**
- Expect 1.5-2.5GB AppImage
- Self-contained, includes all dependencies
- No compression (already compressed)

**Distribution Compatibility:**
- Build on Ubuntu 20.04 for maximum compatibility
- Test on Ubuntu, Fedora, Debian, Arch
- Requires GLIBC 2.31+

**Testing:**
- Test on multiple distributions
- Test with and without FUSE
- Verify executable permissions
- Test auto-update functionality

**Common Issues:**
- GLIBC version mismatch (build on older system)
- FUSE not installed (install libfuse2)
- Permission denied (chmod +x)

## Verification

### Automated Verification

```bash
# Verify build outputs
node scripts/verify-build-outputs.js

# Verify backend build
npm run build:backend:verify

# Run integration tests
npm run test:integration

# Run end-to-end tests
npm run test:e2e
```

### Manual Verification

#### Backend Verification

- [ ] Executable exists at correct path
- [ ] File size is reasonable (500MB - 2GB)
- [ ] Executable runs without errors
- [ ] Health endpoint responds
- [ ] All API endpoints work
- [ ] Data files are accessible
- [ ] No console window (Windows)
- [ ] Clean shutdown

#### Application Verification

- [ ] Installer installs successfully
- [ ] Application launches
- [ ] Backend starts automatically
- [ ] Frontend connects to backend
- [ ] All features work
- [ ] No errors in logs
- [ ] Clean uninstall

#### Auto-Update Verification

- [ ] Update notification appears (on older version)
- [ ] Update downloads successfully
- [ ] Update installs correctly
- [ ] New backend executable is used
- [ ] Application works after update

### Checksum Verification

Users can verify downloads:

```bash
# Windows (PowerShell)
Get-FileHash PEFT-Studio-Setup-1.0.0.exe -Algorithm SHA256

# macOS/Linux
shasum -a 256 PEFT-Studio-1.0.0.dmg

# Compare with checksums.txt
```

## Troubleshooting

### Backend Build Fails

**Issue:** PyInstaller fails to build backend

**Solutions:**
1. Check PyInstaller is installed: `pyinstaller --version`
2. Verify Python version: `python --version` (3.10+)
3. Install dependencies: `pip install -r backend/requirements.txt`
4. Check for errors in build log
5. See [Troubleshooting Guide](backend-bundling-troubleshooting.md)

### Backend Not Included in Installer

**Issue:** Installer doesn't include backend executable

**Solutions:**
1. Verify backend was built: `ls backend/dist/peft_engine*`
2. Check electron-builder config has `extraResources`
3. Rebuild: `npm run build:all`
4. Check build logs for errors

### Installer Too Large

**Issue:** Installer is over 3GB

**Solutions:**
1. This is expected for ML applications
2. Verify size is reasonable (1-3GB)
3. Check for duplicate dependencies
4. Consider excluding unused packages
5. Use compression (already enabled)

### Auto-Update Fails

**Issue:** Users can't update to new version

**Solutions:**
1. Verify backend executable is in update package
2. Check electron-updater configuration
3. Verify GitHub release is published (not draft)
4. Check update server is accessible
5. Review auto-updater logs

### Platform-Specific Build Fails

**Issue:** Build fails on specific platform

**Solutions:**
1. Verify platform-specific prerequisites
2. Check platform-specific build logs
3. Test on clean VM
4. See platform-specific sections above
5. Use CI/CD for consistent builds

## Post-Release

### Announce Release

1. **GitHub Release Notes**: Already created
2. **Social Media**: Announce on Twitter, LinkedIn, etc.
3. **Documentation**: Update docs site if applicable
4. **Changelog**: Ensure CHANGELOG.md is up to date

### Monitor Release

1. **Download Stats**: Check GitHub release downloads
2. **Error Reports**: Monitor for crash reports
3. **User Feedback**: Check issues and discussions
4. **Auto-Update**: Verify users are updating successfully

### Hotfix Process

If critical issues are found:

1. **Create Hotfix Branch**
   ```bash
   git checkout -b hotfix/v1.0.1
   ```

2. **Fix Issue**
   ```bash
   # Make fixes
   git commit -m "fix: critical issue"
   ```

3. **Test Thoroughly**
   ```bash
   npm test
   npm run test:integration
   ```

4. **Release Hotfix**
   ```bash
   npm version patch
   git push origin hotfix/v1.0.1
   git tag v1.0.1
   git push origin v1.0.1
   ```

5. **Merge to Main**
   ```bash
   git checkout main
   git merge hotfix/v1.0.1
   git push
   ```

### Rollback Process

If a release has critical issues:

1. **Mark Release as Pre-release** on GitHub
2. **Create Hotfix** (see above)
3. **Notify Users** via GitHub discussions
4. **Provide Rollback Instructions**:
   - Download previous version
   - Uninstall current version
   - Install previous version

## Best Practices

### Before Release

- Test on clean systems (VMs)
- Test all platforms
- Verify backend integration
- Check auto-update works
- Review all documentation

### During Release

- Use CI/CD for consistency
- Build on clean environments
- Verify checksums
- Test installers before publishing
- Create draft releases first

### After Release

- Monitor for issues
- Respond to user feedback
- Update documentation
- Plan next release
- Archive build artifacts

## Related Documentation

- [Backend Bundling Guide](backend-bundling.md) - Backend bundling details
- [Testing Bundled Backend](testing-bundled-backend.md) - Testing procedures
- [Troubleshooting](backend-bundling-troubleshooting.md) - Common issues
- [Build and Installers](build-and-installers.md) - Build process
- [Release Process](release-process.md) - General release process

## Summary

Releasing PEFT Studio with bundled backend requires:

1. **Preparation**: Verify environment and dependencies
2. **Backend Build**: Build on each platform
3. **Testing**: Comprehensive testing of backend and integration
4. **Packaging**: Create installers with bundled backend
5. **Verification**: Test installers on clean systems
6. **Release**: Create GitHub release and upload assets
7. **Monitoring**: Watch for issues and user feedback

The bundled backend adds complexity but provides a better user experience by eliminating Python installation requirements.

## Quick Reference

```bash
# Complete release process
npm run verify:build:env          # Verify environment
npm run build:backend             # Build backend
npm run build:backend:verify      # Verify backend
npm run test:integration          # Test integration
npm run build:all                 # Build application
node scripts/generate-checksums.js # Generate checksums
node scripts/release-to-github.js  # Create release

# Or use orchestration script
node scripts/complete-release.js   # Complete release
```

For detailed information on each step, see the sections above.
