# PEFT Studio Release Guide

This guide explains how to prepare and release a new version of PEFT Studio to GitHub.

## Quick Release (Automated)

### Windows
```powershell
# Dry run first to see what will happen
.\scripts\release-to-github.ps1 -DryRun

# Actual release
.\scripts\release-to-github.ps1 -Version "1.0.1"

# Skip tests/build if already done
.\scripts\release-to-github.ps1 -Version "1.0.1" -SkipTests -SkipBuild
```

### Linux/macOS
```bash
# Make scripts executable (first time only)
chmod +x scripts/*.sh

# Dry run first to see what will happen
./scripts/release-to-github.sh --dry-run

# Actual release
./scripts/release-to-github.sh --version "1.0.1"

# Skip tests/build if already done
./scripts/release-to-github.sh --version "1.0.1" --skip-tests --skip-build
```

## Manual Release Process

If you prefer to do it step-by-step:

### 1. Clean Up Unnecessary Files

**Windows:**
```powershell
.\scripts\prepare-release.ps1
```

**Linux/macOS:**
```bash
./scripts/prepare-release.sh
```

### 2. Run Tests
```bash
npm run test:run
```

### 3. Build Application
```bash
npm run build
```

### 4. Package Installers
```bash
npm run package:all
```

This creates installers for all platforms in the `release/` directory:
- Windows: `PEFT-Studio-Setup-1.0.1.exe`, `PEFT-Studio-Portable-1.0.1.exe`
- macOS: `PEFT-Studio-1.0.1-x64.dmg`, `PEFT-Studio-1.0.1-arm64.dmg`
- Linux: `PEFT-Studio-1.0.1-x64.AppImage`, `PEFT-Studio-1.0.1-x64.deb`

### 5. Generate Checksums
```bash
npm run generate:checksums
```

This creates `checksums.txt` in the `release/` directory.

### 6. Commit Changes
```bash
git add .
git commit -m "chore: prepare v1.0.1 release"
```

### 7. Create and Push Tag
```bash
git tag -a v1.0.1 -m "Release v1.0.1"
git push origin main --tags
```

### 8. Create GitHub Release

1. Go to https://github.com/Ankesh-007/peft-studio/releases
2. Click "Draft a new release"
3. Select the tag you just created (v1.0.1)
4. Fill in the release title: "PEFT Studio v1.0.1"
5. Copy release notes from `CHANGELOG.md`
6. Upload installers from `release/` directory:
   - All `.exe`, `.dmg`, `.AppImage`, and `.deb` files
   - The `checksums.txt` file
7. Click "Publish release"

## What Gets Cleaned Up

The cleanup script removes:

### Build Artifacts
- `release/win-unpacked/` - Temporary Windows build files
- `release/builder-debug.yml` - Debug configuration
- `release/builder-effective-config.yaml` - Build configuration
- `dist/assets/`, `dist/samples/`, `dist/*.html` - Old build outputs

### Backend Cache
- `backend/.hypothesis/` - Property test cache
- `backend/.pytest_cache/` - Pytest cache
- `backend/__pycache__/` - Python bytecode
- `backend/data/cache/` - Application cache
- `backend/data/peft_studio.db` - Development database
- `backend/data/security_audit.log` - Audit logs

### Temporary Documentation
- Release preparation documents in `.kiro/specs/peft-application-fix/`

## What Gets Kept

Critical files that are preserved:
- `package.json` - Package configuration
- `README.md` - Main documentation
- `LICENSE` - License file
- `CHANGELOG.md` - Version history
- `electron/main.js` - Electron entry point
- `backend/main.py` - Backend entry point
- `backend/requirements.txt` - Python dependencies
- `build/.gitkeep` - Keeps build directory
- `build/README.md` - Build documentation

## Verification

After cleanup, the script verifies all critical files still exist. If any are missing, the script will fail with an error.

## Troubleshooting

### "Tests failed"
Run tests individually to identify the issue:
```bash
npm run test:run
```

### "Build failed"
Check for TypeScript errors:
```bash
npm run type-check
```

### "Packaging failed"
Ensure all dependencies are installed:
```bash
npm install
```

### "Push failed"
Check your Git credentials and network connection:
```bash
git remote -v
git status
```

### "Tag already exists"
Delete the existing tag first:
```bash
git tag -d v1.0.1
git push origin :refs/tags/v1.0.1
```

## Platform-Specific Notes

### Windows
- Requires PowerShell 5.1 or later
- May need to run as Administrator for some operations
- Code signing requires valid certificate

### macOS
- Requires Xcode Command Line Tools
- Code signing requires Apple Developer account
- Notarization requires Apple ID credentials

### Linux
- Requires standard build tools (gcc, make, etc.)
- AppImage requires FUSE
- Debian package requires dpkg-deb

## Release Checklist

Before releasing:
- [ ] Update version in `package.json`
- [ ] Update `CHANGELOG.md` with release notes
- [ ] Run all tests and ensure they pass
- [ ] Test installers on target platforms
- [ ] Verify checksums match
- [ ] Update documentation if needed
- [ ] Review security audit logs

After releasing:
- [ ] Verify GitHub release is published
- [ ] Test auto-update functionality
- [ ] Announce release (if applicable)
- [ ] Monitor for issues

## Support

For issues or questions:
- GitHub Issues: https://github.com/Ankesh-007/peft-studio/issues
- Documentation: https://github.com/Ankesh-007/peft-studio/tree/main/docs

## License

PEFT Studio is released under the MIT License. See LICENSE file for details.
