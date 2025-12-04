# How to Publish PEFT Studio v1.0.1 Release on GitHub

## Quick Start

You have two options to publish the release:

### Option A: Using GitHub Web Interface (Recommended for Manual Release)

1. **Go to the releases page**: https://github.com/Ankesh-007/peft-studio/releases
2. **Click "Draft a new release"**
3. **Fill in the details** (see below for complete content)
4. **Publish the release**

### Option B: Using GitHub CLI (Automated)

```bash
# First, create and push the tag
git tag -a v1.0.1 -m "Release version 1.0.1"
git push origin v1.0.1

# Then create the release using GitHub CLI
gh release create v1.0.1 \
  --title "PEFT Studio v1.0.1" \
  --notes-file .kiro/specs/peft-application-fix/RELEASE_NOTES_v1.0.1.md \
  --latest
```

## Complete Release Information

### Release Tag
```
v1.0.1
```

### Release Title
```
PEFT Studio v1.0.1
```

### Release Description

Copy and paste the following into the release description:

---

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

**Note**: Installers will be available once the release is built. For now, you can build from source:

```bash
git clone https://github.com/Ankesh-007/peft-studio.git
cd peft-studio
git checkout v1.0.1
npm install
npm run build
npm run electron:build
```

### Future Downloads (After Build)

- **Windows**: `PEFT Studio-Setup-1.0.1.exe` (Installer) or `PEFT Studio-Portable-1.0.1.exe` (Portable)
- **macOS**: `PEFT Studio-1.0.1-x64.dmg` (Intel) or `PEFT Studio-1.0.1-arm64.dmg` (Apple Silicon)
- **Linux**: `PEFT Studio-1.0.1-x64.AppImage` (Universal) or `PEFT Studio-1.0.1-x64.deb` (Debian/Ubuntu)

## 🔐 Verifying Downloads

To verify the integrity of your download (once checksums are available):

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

1. Clone the repository or download the installer (when available)
2. Follow the installation instructions for your platform
3. Launch the application
4. Follow the dependency check prompts if needed
5. Start fine-tuning!

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

---

## Step-by-Step Instructions

### Step 1: Create the Git Tag

```bash
# Make sure you're on the main branch
git checkout main
git pull origin main

# Create the tag
git tag -a v1.0.1 -m "Release version 1.0.1 - Backend fixes and PEFT display improvements"

# Push the tag
git push origin v1.0.1
```

### Step 2: Create the Release on GitHub

1. Go to: https://github.com/Ankesh-007/peft-studio/releases
2. Click "Draft a new release"
3. In "Choose a tag", select `v1.0.1` (it should appear after you pushed the tag)
4. Set "Release title" to: `PEFT Studio v1.0.1`
5. Copy the entire release description from above into the description field
6. Check "Set as the latest release"
7. Leave "Set as a pre-release" unchecked
8. Click "Publish release"

### Step 3: Build Installers (Optional)

If you want to provide installers immediately:

**Windows**:
```bash
npm run electron:build -- --win
```

**macOS**:
```bash
npm run electron:build -- --mac
```

**Linux**:
```bash
npm run electron:build -- --linux
```

Then upload the installers to the release by editing it and dragging the files into the assets section.

### Step 4: Generate Checksums (If Installers Built)

```bash
node scripts/generate-checksums.js
```

Upload the `SHA256SUMS.txt` file to the release.

## What Happens After Publishing

1. The release will appear on your releases page
2. Users can download the source code (automatically provided by GitHub)
3. If you uploaded installers, users can download those too
4. The auto-update system will detect the new version (if configured)
5. Users with v1.0.0 will see an update notification

## Important Notes

- **Source Code**: GitHub automatically provides source code downloads (zip and tar.gz) for every release
- **Installers**: You can add installers later by editing the release
- **Checksums**: Generate and upload checksums after building installers
- **Auto-Update**: Will work once installers are available and properly configured

## Troubleshooting

### Tag Already Exists
If the tag already exists:
```bash
git tag -d v1.0.1  # Delete local tag
git push origin :refs/tags/v1.0.1  # Delete remote tag
# Then create it again
```

### Release Already Exists
If a release already exists for v1.0.1:
1. Go to the release page
2. Click "Edit" on the v1.0.1 release
3. Update the description
4. Save changes

### Cannot Push Tag
Make sure you have write access to the repository and are authenticated:
```bash
git remote -v  # Verify remote URL
gh auth status  # Check GitHub CLI authentication
```

## Next Steps After Publishing

1. **Announce the Release**:
   - Post in GitHub Discussions
   - Update project README if needed
   - Share on social media (if applicable)

2. **Monitor for Issues**:
   - Watch for bug reports
   - Check download statistics
   - Respond to user questions

3. **Build Installers** (if not done yet):
   - Set up CI/CD for automated builds
   - Or build manually and upload to release

4. **Test Auto-Update**:
   - Install v1.0.0
   - Verify update notification appears
   - Test update process

## Summary

The release is ready to be published! All code changes are complete, documentation is updated, and the release notes are prepared. Simply follow the steps above to make v1.0.1 available to users.

