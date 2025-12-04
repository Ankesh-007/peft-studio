# Complete Release Process Guide

This comprehensive guide documents the complete release process for PEFT Studio, including all scripts, workflows, and best practices.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Release Workflow](#release-workflow)
4. [Script Reference](#script-reference)
5. [Troubleshooting](#troubleshooting)
6. [Best Practices](#best-practices)

## Overview

The PEFT Studio release process is fully automated through a series of scripts that handle:

- Repository cleanup
- Release validation
- Multi-platform builds
- Checksum generation
- GitHub release creation
- Asset upload and verification

The entire process can be executed with a single command or run step-by-step for more control.

## Prerequisites

### Required Tools

- **Node.js 18+**: JavaScript runtime
- **npm**: Package manager (comes with Node.js)
- **Git**: Version control
- **GitHub CLI (optional)**: For advanced GitHub operations

### Required Environment Variables

```bash
# Required for GitHub release creation
export GITHUB_TOKEN="your_github_personal_access_token"

# Optional: For code signing (see Code Signing section)
export CSC_LINK="/path/to/certificate"
export CSC_KEY_PASSWORD="certificate_password"
```

### GitHub Token Setup

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select scopes:
   - `repo` (Full control of private repositories)
   - `write:packages` (Upload packages to GitHub Package Registry)
4. Copy token and set as environment variable

### Repository Requirements

- Clean working directory (no uncommitted changes)
- Updated CHANGELOG.md with current version
- Valid semantic version in package.json
- All tests passing
- Complete documentation (README, CONTRIBUTING, LICENSE)

## Release Workflow

### Quick Release (Recommended)

Execute the complete release process with a single command:

```bash
# Full release
node scripts/complete-release.js

# Dry run (test without making changes)
node scripts/complete-release.js --dry-run

# Create draft release
node scripts/complete-release.js --draft
```

The orchestration script executes these steps in sequence:

1. **Cleanup**: Remove unnecessary files
2. **Validate**: Verify repository readiness
3. **Build**: Create installers for all platforms
4. **Checksum**: Generate SHA256 checksums
5. **Release**: Create GitHub release and upload assets

### Step-by-Step Release

For more control, execute each step individually:

#### Step 1: Clean Repository

Remove build artifacts, test caches, and temporary files:

```bash
# Preview what will be removed
node scripts/cleanup-repository.js --dry-run

# Perform cleanup
node scripts/cleanup-repository.js
```

**What it does:**
- Removes `dist/`, `build/`, `release/` directories
- Cleans test caches (`.pytest_cache/`, `.hypothesis/`)
- Removes Python bytecode (`__pycache__/`, `*.pyc`)
- Deletes temporary files (`*.tmp`, `*.log`, `*_SUMMARY.md`)
- Updates `.gitignore` to prevent re-addition

#### Step 2: Validate Release Readiness

Verify the repository is ready for release:

```bash
# Full validation
node scripts/validate-release.js

# Skip test execution
node scripts/validate-release.js --skip-tests
```

**Validation checks:**
- Repository structure (LICENSE, README, CONTRIBUTING)
- package.json metadata completeness
- Semantic versioning compliance
- CHANGELOG version entry
- Test execution (optional)
- Working directory cleanliness

#### Step 3: Build Installers

Build installers for all platforms:

```bash
# Build all platforms
node scripts/build.js all

# Build specific platform
node scripts/build.js windows
node scripts/build.js mac
node scripts/build.js linux
```

**Generated artifacts:**

**Windows:**
- `PEFT-Studio-Setup-{version}.exe` (NSIS installer)
- `PEFT-Studio-Portable-{version}.exe` (Portable executable)

**macOS:**
- `PEFT-Studio-{version}-x64.dmg` (Intel DMG)
- `PEFT-Studio-{version}-arm64.dmg` (Apple Silicon DMG)
- `PEFT-Studio-{version}-x64.zip` (Intel ZIP)
- `PEFT-Studio-{version}-arm64.zip` (Apple Silicon ZIP)

**Linux:**
- `PEFT-Studio-{version}-x64.AppImage` (Universal AppImage)
- `peft-studio_{version}_amd64.deb` (Debian package)

All artifacts are placed in the `release/` directory.

#### Step 4: Generate Checksums

Create SHA256 checksums for all installers:

```bash
node scripts/generate-checksums.js
```

**What it does:**
- Calculates SHA256 hash for each installer
- Creates `SHA256SUMS.txt` in release directory
- Verifies checksums by recalculation
- Uses standard format: `HASH  FILENAME`

**Checksum file format:**
```
a1b2c3d4...  PEFT-Studio-Setup-1.0.0.exe
e5f6g7h8...  PEFT-Studio-Portable-1.0.0.exe
...
```

#### Step 5: Create GitHub Release

Create GitHub release and upload all assets:

```bash
# Create release
node scripts/release-to-github.js

# Create draft release
node scripts/release-to-github.js --draft

# Dry run
node scripts/release-to-github.js --dry-run
```

**What it does:**
- Extracts release notes from CHANGELOG.md
- Creates GitHub release with version tag
- Uploads all installer artifacts
- Uploads SHA256SUMS.txt
- Creates and pushes git tag
- Generates release summary

## Script Reference

### cleanup-repository.js

**Purpose**: Remove unnecessary files from repository

**Usage:**
```bash
node scripts/cleanup-repository.js [--dry-run]
```

**Options:**
- `--dry-run`: Preview changes without deleting files

**What it removes:**
- Build artifacts: `release/*`, `dist/`, `build/`
- Test caches: `.pytest_cache/`, `.hypothesis/`
- Python bytecode: `__pycache__/`, `*.pyc`, `*.pyo`
- Temporary files: `*.tmp`, `*.log`, `*_SUMMARY.md`, `*_STATUS.md`

**What it preserves:**
- Source code: `src/`, `backend/`
- Documentation: `docs/`, `*.md`
- Configuration files: `*.config.js`, `package.json`, etc.
- Git repository: `.git/`

**Exit codes:**
- `0`: Success
- `1`: Error occurred

### validate-release.js

**Purpose**: Validate repository readiness for release

**Usage:**
```bash
node scripts/validate-release.js [--skip-tests]
```

**Options:**
- `--skip-tests`: Skip test execution

**Validation checks:**
1. **Structure**: LICENSE, README, CONTRIBUTING, .gitignore
2. **Metadata**: package.json completeness and validity
3. **Versioning**: Semantic version format
4. **CHANGELOG**: Current version entry exists
5. **Tests**: All tests pass (optional)
6. **Working Directory**: No uncommitted changes

**Exit codes:**
- `0`: Repository is ready
- `1`: Validation failed

### build.js

**Purpose**: Build installers for all platforms

**Usage:**
```bash
node scripts/build.js [platform]
```

**Arguments:**
- `platform`: `windows`, `mac`, `linux`, or `all` (default: `all`)

**Build process:**
1. Check prerequisites (Node.js, npm, node_modules)
2. Build frontend (TypeScript + Vite)
3. Run electron-builder for target platform(s)
4. Collect and verify artifacts
5. Display build summary

**Exit codes:**
- `0`: Build successful
- `1`: Build failed

### generate-checksums.js

**Purpose**: Generate SHA256 checksums for installers

**Usage:**
```bash
node scripts/generate-checksums.js
```

**Process:**
1. Find all installer files in `release/` directory
2. Calculate SHA256 hash for each file
3. Write `SHA256SUMS.txt` with standard format
4. Verify checksums by recalculation

**Exit codes:**
- `0`: Checksums generated successfully
- `1`: Error occurred

### release-to-github.js

**Purpose**: Create GitHub release and upload assets

**Usage:**
```bash
node scripts/release-to-github.js [options]
```

**Options:**
- `--draft`: Create draft release (not published)
- `--dry-run`: Simulate without creating release

**Environment variables:**
- `GITHUB_TOKEN`: Required for authentication

**Process:**
1. Read version from package.json
2. Extract release notes from CHANGELOG.md
3. Create GitHub release via API
4. Upload all installer artifacts
5. Upload SHA256SUMS.txt
6. Create and push git tag
7. Generate release summary

**Exit codes:**
- `0`: Release created successfully
- `1`: Release failed

### complete-release.js

**Purpose**: Orchestrate complete release process

**Usage:**
```bash
node scripts/complete-release.js [options]
```

**Options:**
- `--dry-run`: Simulate without making changes
- `--skip-cleanup`: Skip cleanup step
- `--skip-tests`: Skip test execution
- `--draft`: Create draft release
- `--help`: Display help message

**Execution sequence:**
1. Pre-flight checks (working directory status)
2. Cleanup (optional)
3. Validate
4. Build
5. Checksum
6. Release

**Halt behavior:**
- Stops on first failure
- Reports which step failed
- Provides error details

**Exit codes:**
- `0`: All steps successful
- `1`: One or more steps failed

## Troubleshooting

### Common Issues

#### 1. "GITHUB_TOKEN not set"

**Problem**: GitHub token environment variable not configured

**Solution:**
```bash
export GITHUB_TOKEN="your_token_here"
```

Or add to your shell profile (`~/.bashrc`, `~/.zshrc`):
```bash
echo 'export GITHUB_TOKEN="your_token_here"' >> ~/.bashrc
source ~/.bashrc
```

#### 2. "Working directory has uncommitted changes"

**Problem**: Git working directory is not clean

**Solution:**
```bash
# Commit changes
git add .
git commit -m "Prepare for release"

# Or stash changes
git stash

# Or force release (not recommended)
node scripts/complete-release.js --skip-cleanup
```

#### 3. "CHANGELOG does not contain entry for version X.Y.Z"

**Problem**: CHANGELOG.md missing current version

**Solution:**
1. Open `CHANGELOG.md`
2. Add section for current version:
```markdown
## [1.0.0] - 2024-01-15

### Added
- New feature description

### Changed
- Changed feature description

### Fixed
- Bug fix description
```

#### 4. "Build failed for platform X"

**Problem**: Platform-specific build error

**Solution:**
1. Check build logs for specific error
2. Verify dependencies: `npm install`
3. Test build locally: `node scripts/build.js windows`
4. Check electron-builder configuration in `package.json`

#### 5. "Asset upload failed"

**Problem**: GitHub API upload error

**Solution:**
1. Check internet connection
2. Verify GITHUB_TOKEN has correct permissions
3. Check GitHub API status: https://www.githubstatus.com/
4. Retry: Script has automatic retry logic

#### 6. "Tests failed"

**Problem**: Test suite has failures

**Solution:**
```bash
# Run tests to see failures
npm run test:run

# Fix failing tests
# Then re-run validation
node scripts/validate-release.js
```

#### 7. "Permission denied" (Unix/Linux/macOS)

**Problem**: Script not executable

**Solution:**
```bash
chmod +x scripts/*.sh
```

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
# Set debug environment variable
export DEBUG=*

# Run script
node scripts/complete-release.js
```

### Dry Run Testing

Always test with dry run first:

```bash
# Test complete process
node scripts/complete-release.js --dry-run

# Test individual steps
node scripts/cleanup-repository.js --dry-run
node scripts/release-to-github.js --dry-run
```

## Best Practices

### Before Release

1. **Update version**: Bump version in `package.json`
   ```bash
   npm version patch  # 1.0.0 → 1.0.1
   npm version minor  # 1.0.0 → 1.1.0
   npm version major  # 1.0.0 → 2.0.0
   ```

2. **Update CHANGELOG**: Add entry for new version
   - Document all changes
   - Categorize: Added, Changed, Fixed, Removed
   - Include dates

3. **Run tests**: Ensure all tests pass
   ```bash
   npm run test:run
   ```

4. **Commit changes**: Clean working directory
   ```bash
   git add .
   git commit -m "chore: prepare release v1.0.0"
   ```

5. **Dry run**: Test release process
   ```bash
   node scripts/complete-release.js --dry-run
   ```

### During Release

1. **Use orchestration script**: Prefer `complete-release.js` over manual steps
2. **Monitor output**: Watch for warnings or errors
3. **Verify artifacts**: Check that all expected files are generated
4. **Test checksums**: Verify SHA256SUMS.txt is correct

### After Release

1. **Verify GitHub release**: Check release page on GitHub
2. **Test downloads**: Download and verify installers
3. **Validate checksums**: Users should be able to verify
   ```bash
   sha256sum -c SHA256SUMS.txt
   ```

4. **Update documentation**: If needed
5. **Announce release**: Social media, mailing list, etc.

### Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.0.0): Breaking changes
- **MINOR** (0.X.0): New features (backward compatible)
- **PATCH** (0.0.X): Bug fixes (backward compatible)

Examples:
- `1.0.0` → `1.0.1`: Bug fix
- `1.0.0` → `1.1.0`: New feature
- `1.0.0` → `2.0.0`: Breaking change

### Pre-release Versions

For testing:
- `1.0.0-alpha.1`: Alpha release
- `1.0.0-beta.1`: Beta release
- `1.0.0-rc.1`: Release candidate

### Release Frequency

- **Patch releases**: As needed for critical bugs
- **Minor releases**: Monthly or when features are ready
- **Major releases**: Quarterly or when breaking changes accumulate

### Security

1. **Never commit tokens**: Use environment variables
2. **Rotate tokens**: Periodically update GitHub tokens
3. **Verify checksums**: Always generate and publish
4. **Sign releases**: Enable code signing when possible
5. **Audit dependencies**: Run security scans before release

### Documentation

1. **Keep CHANGELOG current**: Update with every change
2. **Document breaking changes**: Clearly in CHANGELOG
3. **Update README**: Version badges, screenshots
4. **Migration guides**: For major versions

## Related Documentation

- [Step-by-Step Release Guide](./release-step-by-step.md)
- [Script Usage Reference](./release-scripts-reference.md)
- [Troubleshooting Guide](./release-troubleshooting.md)
- [Dry-Run Testing Guide](./release-dry-run-testing.md)
- [Build and Installers](./build-and-installers.md)
- [Test Release Process](./test-release-process.md)

## Support

For issues or questions:
- Check [Troubleshooting Guide](./release-troubleshooting.md)
- Review script output for error messages
- Check GitHub Actions logs for CI failures
- Open an issue on GitHub

---

**Last Updated**: 2024-12-04
