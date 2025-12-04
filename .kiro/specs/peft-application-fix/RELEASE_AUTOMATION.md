# Release Automation Implementation

## Overview

This document describes the automated release process implemented for PEFT Studio v1.0.1.

## New Scripts Created

### 1. `scripts/prepare-release.ps1` / `scripts/prepare-release.sh`

**Purpose:** Clean up unnecessary files before release

**What it does:**
- Removes build artifacts (release/win-unpacked, dist/*, etc.)
- Cleans backend cache (.hypothesis, .pytest_cache, __pycache__)
- Removes temporary databases and logs
- Deletes temporary documentation files
- Verifies critical files still exist

**Usage:**
```powershell
# Windows - Dry run
.\scripts\prepare-release.ps1 -DryRun

# Windows - Actual cleanup
.\scripts\prepare-release.ps1

# Linux/macOS - Dry run
./scripts/prepare-release.sh --dry-run

# Linux/macOS - Actual cleanup
./scripts/prepare-release.sh
```

### 2. `scripts/release-to-github.ps1` / `scripts/release-to-github.sh`

**Purpose:** Complete automated release process

**What it does:**
1. Runs cleanup script
2. Executes tests (optional)
3. Builds application (optional)
4. Packages installers for all platforms
5. Generates checksums
6. Commits changes
7. Creates and pushes Git tag
8. Provides instructions for GitHub release

**Usage:**
```powershell
# Windows - Full release
.\scripts\release-to-github.ps1 -Version "1.0.1"

# Windows - Dry run
.\scripts\release-to-github.ps1 -DryRun

# Windows - Skip tests and build
.\scripts\release-to-github.ps1 -Version "1.0.1" -SkipTests -SkipBuild

# Linux/macOS - Full release
./scripts/release-to-github.sh --version "1.0.1"

# Linux/macOS - Dry run
./scripts/release-to-github.sh --dry-run
```

## Files Cleaned Up

### Build Artifacts (Safe to Remove)
- `release/win-unpacked/` - Temporary Windows build directory
- `release/builder-debug.yml` - Electron builder debug config
- `release/builder-effective-config.yaml` - Electron builder effective config
- `dist/assets/` - Old frontend build assets
- `dist/samples/` - Sample files from build
- `dist/index.html` - Old build HTML
- `dist/stats.html` - Build statistics
- `build/signing-status-macos.txt` - Temporary signing status
- `build/signing-status.txt` - Temporary signing status

### Backend Cache (Safe to Remove)
- `backend/.hypothesis/` - Property-based testing cache (4000+ files)
- `backend/.pytest_cache/` - Pytest cache
- `backend/__pycache__/` - Python bytecode cache
- `backend/data/cache/` - Application cache
- `backend/data/peft_studio.db` - Development database
- `backend/data/security_audit.log` - Security audit logs
- `backend/artifacts/` - Training artifacts
- `backend/checkpoints/` - Model checkpoints

### Temporary Documentation (Safe to Remove)
- `.kiro/specs/peft-application-fix/RELEASE_PUBLICATION_GUIDE.md`
- `.kiro/specs/peft-application-fix/RELEASE_NOTES_v1.0.1.md`
- `.kiro/specs/peft-application-fix/FINAL_CHECKPOINT_VERIFICATION.md`
- `.kiro/specs/peft-application-fix/RELEASE_1.0.1_SUMMARY.md`
- `.kiro/specs/peft-application-fix/GITHUB_RELEASE_GUIDE.md`
- `.kiro/specs/peft-application-fix/INSTALLER_TESTING_GUIDE.md`

### Other
- `.vite/` - Vite cache

## Files Preserved

Critical files that must remain:
- `package.json` - Package configuration
- `README.md` - Main documentation
- `LICENSE` - License file
- `CHANGELOG.md` - Version history
- `electron/main.js` - Electron entry point
- `backend/main.py` - Backend entry point
- `backend/requirements.txt` - Python dependencies
- `build/.gitkeep` - Keeps build directory in Git
- `build/README.md` - Build documentation

## NPM Scripts Added

```json
{
  "prepare:release": "pwsh -File scripts/prepare-release.ps1",
  "prepare:release:dry": "pwsh -File scripts/prepare-release.ps1 -DryRun",
  "release": "pwsh -File scripts/release-to-github.ps1",
  "release:dry": "pwsh -File scripts/release-to-github.ps1 -DryRun"
}
```

## Release Workflow

### Automated (Recommended)

```bash
# 1. Dry run to see what will happen
npm run release:dry

# 2. Actual release
npm run release
```

### Manual (Step-by-Step)

```bash
# 1. Clean up
npm run prepare:release

# 2. Test
npm run test:run

# 3. Build
npm run build

# 4. Package
npm run package:all

# 5. Generate checksums
npm run generate:checksums

# 6. Commit
git add .
git commit -m "chore: prepare v1.0.1 release"

# 7. Tag and push
git tag -a v1.0.1 -m "Release v1.0.1"
git push origin main --tags
```

## Safety Features

### Dry Run Mode
Both scripts support dry run mode to preview changes without making them:
- Shows what files would be removed
- Shows what commands would be executed
- No actual changes made to filesystem or Git

### Critical File Verification
After cleanup, scripts verify that all critical files still exist:
- If any critical file is missing, script fails with error
- Prevents accidental deletion of important files

### Error Handling
- Scripts stop on first error
- Clear error messages
- Exit codes indicate success/failure

## Documentation

Created comprehensive documentation:
- `RELEASE_GUIDE.md` - Complete release guide for users
- This file - Technical implementation details

## Benefits

1. **Consistency:** Same process every time
2. **Speed:** Automated steps save time
3. **Safety:** Dry run and verification prevent mistakes
4. **Clarity:** Clear output shows what's happening
5. **Flexibility:** Can skip steps or run individually

## Testing

Before using in production:

```bash
# Test cleanup (dry run)
npm run prepare:release:dry

# Test full release (dry run)
npm run release:dry

# Verify no critical files would be removed
# Verify Git commands are correct
```

## Next Steps

1. Test scripts in dry run mode
2. Review files to be removed
3. Run actual cleanup
4. Build and package installers
5. Push to GitHub
6. Create GitHub release
7. Upload installers and checksums

## Rollback

If something goes wrong:

```bash
# Undo last commit
git reset --soft HEAD~1

# Delete tag locally
git tag -d v1.0.1

# Delete tag remotely (if pushed)
git push origin :refs/tags/v1.0.1

# Restore files from Git
git checkout .
```

## Maintenance

Scripts should be updated when:
- New build artifacts are created
- New cache directories are added
- Critical files change
- Release process changes

## Support

For issues with release scripts:
1. Check script output for errors
2. Run in dry run mode first
3. Verify Git status is clean
4. Check file permissions
5. Review RELEASE_GUIDE.md

## License

These scripts are part of PEFT Studio and released under the MIT License.
