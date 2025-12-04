# Release Scripts Reference

Complete reference documentation for all release-related scripts in PEFT Studio.

## Table of Contents

1. [cleanup-repository.js](#cleanup-repositoryjs)
2. [validate-release.js](#validate-releasejs)
3. [build.js](#buildjs)
4. [generate-checksums.js](#generate-checksumsjs)
5. [release-to-github.js](#release-to-githubjs)
6. [complete-release.js](#complete-releasejs)
7. [Environment Variables](#environment-variables)
8. [Exit Codes](#exit-codes)

---

## cleanup-repository.js

### Purpose

Removes unnecessary files from the repository including build artifacts, test caches, temporary files, and Python bytecode while preserving essential source code and documentation.

### Usage

```bash
node scripts/cleanup-repository.js [options]
```

### Options

| Option | Description |
|--------|-------------|
| `--dry-run` | Preview changes without deleting files |

### What It Removes

**Build Artifacts:**
- `release/*` (except latest release files)
- `dist/`
- `build/`

**Test Caches:**
- `.pytest_cache/`
- `.hypothesis/`

**Python Bytecode:**
- `__pycache__/`
- `*.pyc`
- `*.pyo`

**Temporary Files:**
- `*.tmp`
- `*.log`
- `*_SUMMARY.md`
- `*_STATUS.md`
- `*_COMPLETE.md`

### What It Preserves

- Source code (`src/`, `backend/`)
- Documentation (`docs/`, `*.md`)
- Configuration files (`*.config.js`, `package.json`, etc.)
- Git repository (`.git/`)
- Essential release files (`SHA256SUMS.txt`, `latest.yml`, `.gitkeep`)

### Process

1. Identifies unnecessary files based on patterns
2. Categorizes files (build artifacts, test caches, etc.)
3. Removes identified files
4. Cleans release directory selectively
5. Updates `.gitignore` with cleanup patterns
6. Generates cleanup report

### Output

```
=============================================================
Repository Cleanup
=============================================================

📋 Step 1: Identifying unnecessary files...
  Found 45 item(s) to remove:
    - Build artifacts: 12
    - Test caches: 8
    - Python bytecode: 20
    - Temporary files: 5

🗑️  Step 2: Removing unnecessary files...

📦 Step 3: Cleaning release directory...

📝 Step 4: Updating .gitignore...
  ✓ Added 8 pattern(s) to .gitignore

📊 Step 5: Generating cleanup report...

=============================================================
Cleanup Summary
=============================================================
Files removed: 45
Space freed: 125.43 MB
Duration: 2.15s
Timestamp: 2024-12-04T10:30:00.000Z

✨ Cleanup complete!
```

### Exit Codes

- `0`: Cleanup successful
- `1`: Error occurred during cleanup

### Examples

```bash
# Preview cleanup
node scripts/cleanup-repository.js --dry-run

# Perform cleanup
node scripts/cleanup-repository.js
```

### Notes

- Safe to run multiple times (idempotent)
- Always preserves essential files
- Updates `.gitignore` to prevent re-addition
- Provides detailed report of actions taken

---

## validate-release.js

### Purpose

Validates that the repository is ready for release by checking structure, metadata, versioning, tests, and working directory status.

### Usage

```bash
node scripts/validate-release.js [options]
```

### Options

| Option | Description |
|--------|-------------|
| `--skip-tests` | Skip test execution (faster validation) |

### Validation Checks

**1. Repository Structure:**
- LICENSE file exists
- .gitignore contains essential patterns
- README.md exists and is not empty
- CONTRIBUTING.md exists
- CHANGELOG.md exists

**2. Package Metadata:**
- package.json has all required fields (name, version, description, author, license)
- Version follows semantic versioning
- Repository URL is valid
- Keywords are specified

**3. CHANGELOG Version:**
- CHANGELOG.md contains entry for current version
- Version format matches package.json

**4. Tests:**
- All tests pass (optional with `--skip-tests`)

**5. Working Directory:**
- No uncommitted changes
- Git repository is clean

### Output

```
=============================================================
Release Readiness Validation
=============================================================

=== Validating Repository Structure ===
  ✓ LICENSE file exists
  ✓ .gitignore contains essential patterns
  ✓ README.md exists and is not empty
  ✓ CONTRIBUTING.md exists and is not empty
  ✓ CHANGELOG.md exists and is not empty

=== Validating package.json Metadata ===
  ✓ All required fields present
  ✓ Version follows semantic versioning: 1.0.0
  ✓ Repository URL is valid
  ✓ Keywords specified: 5

=== Verifying CHANGELOG Version ===
  ✓ CHANGELOG contains entry for version 1.0.0

=== Executing Tests ===
  Running tests...
  ✓ All tests passed

=== Checking Working Directory ===
  ✓ Working directory is clean

=============================================================
Validation Summary
=============================================================

Structure:        ✓ PASS
Metadata:         ✓ PASS
CHANGELOG:        ✓ PASS
Tests:            ✓ PASS
Working Dir:      ✓ PASS

Duration:         15.32s

✅ Repository is ready for release!
```

### Exit Codes

- `0`: Repository is ready for release
- `1`: Validation failed (issues found)

### Examples

```bash
# Full validation
node scripts/validate-release.js

# Skip tests (faster)
node scripts/validate-release.js --skip-tests
```

### Notes

- Comprehensive pre-release check
- Catches common issues before release
- Provides specific remediation guidance
- Can be integrated into CI/CD pipeline

---

## build.js

### Purpose

Builds installers for all platforms (Windows, macOS, Linux) using electron-builder.

### Usage

```bash
node scripts/build.js [platform]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `windows` | Build Windows installers only |
| `mac` | Build macOS installers only |
| `linux` | Build Linux installers only |
| `all` | Build all platforms (default) |

### Build Targets

**Windows (x64):**
- NSIS installer: `PEFT-Studio-Setup-{version}.exe`
- Portable: `PEFT-Studio-Portable-{version}.exe`

**macOS:**
- Intel DMG: `PEFT-Studio-{version}-x64.dmg`
- Apple Silicon DMG: `PEFT-Studio-{version}-arm64.dmg`
- Intel ZIP: `PEFT-Studio-{version}-x64.zip`
- Apple Silicon ZIP: `PEFT-Studio-{version}-arm64.zip`

**Linux (x64):**
- AppImage: `PEFT-Studio-{version}-x64.AppImage`
- DEB: `peft-studio_{version}_amd64.deb`

### Process

1. Checks prerequisites (Node.js, npm, node_modules)
2. Verifies build configuration
3. Builds frontend (TypeScript + Vite)
4. Runs electron-builder for target platform(s)
5. Collects and catalogs artifacts
6. Verifies all expected outputs exist
7. Displays build summary

### Output

```
=============================================================
Building PEFT Studio Installers
=============================================================

Platform: all

Checking prerequisites...
  ✓ Node.js: v18.17.0
  ✓ npm: 9.6.7
  ✓ node_modules exists

Building frontend...
  > npm run build
  ✓ Frontend built successfully

Building Windows installers...
  > electron-builder --win
  ✓ Windows build complete

Building macOS installers...
  > electron-builder --mac
  ✓ macOS build complete

Building Linux installers...
  > electron-builder --linux
  ✓ Linux build complete

=============================================================
Build Summary
=============================================================

Total artifacts: 8
Total size: 450.23 MB
Duration: 8.45min

Artifacts:
  Windows:
    - PEFT-Studio-Setup-1.0.0.exe (125.5 MB)
    - PEFT-Studio-Portable-1.0.0.exe (120.3 MB)
  
  macOS:
    - PEFT-Studio-1.0.0-x64.dmg (65.2 MB)
    - PEFT-Studio-1.0.0-arm64.dmg (63.8 MB)
    - PEFT-Studio-1.0.0-x64.zip (60.1 MB)
    - PEFT-Studio-1.0.0-arm64.zip (58.9 MB)
  
  Linux:
    - PEFT-Studio-1.0.0-x64.AppImage (85.4 MB)
    - peft-studio_1.0.0_amd64.deb (82.1 MB)

Output directory: release/

✨ Build complete!
```

### Exit Codes

- `0`: Build successful
- `1`: Build failed

### Examples

```bash
# Build all platforms
node scripts/build.js all
node scripts/build.js  # 'all' is default

# Build specific platform
node scripts/build.js windows
node scripts/build.js mac
node scripts/build.js linux
```

### Notes

- Requires all dependencies installed
- Can take 5-15 minutes depending on system
- Builds are placed in `release/` directory
- Supports code signing if certificates configured

---

## generate-checksums.js

### Purpose

Generates SHA256 checksums for all installer artifacts to enable security verification by users.

### Usage

```bash
node scripts/generate-checksums.js
```

### Options

None

### Process

1. Finds all installer files in `release/` directory
2. Calculates SHA256 hash for each file
3. Writes `SHA256SUMS.txt` with standard format
4. Verifies checksums by recalculation
5. Reports results

### Output Format

The generated `SHA256SUMS.txt` file uses the standard format:

```
a1b2c3d4e5f6...  PEFT-Studio-Setup-1.0.0.exe
f6e5d4c3b2a1...  PEFT-Studio-Portable-1.0.0.exe
1a2b3c4d5e6f...  PEFT-Studio-1.0.0-x64.dmg
...
```

Format: `HASH  FILENAME` (64-character hex hash, two spaces, filename)

### Console Output

```
=============================================================
Generating SHA256 Checksums
=============================================================

Finding installer files...
  Found 8 installer(s)

Calculating checksums...
  ✓ PEFT-Studio-Setup-1.0.0.exe
  ✓ PEFT-Studio-Portable-1.0.0.exe
  ✓ PEFT-Studio-1.0.0-x64.dmg
  ✓ PEFT-Studio-1.0.0-arm64.dmg
  ✓ PEFT-Studio-1.0.0-x64.zip
  ✓ PEFT-Studio-1.0.0-arm64.zip
  ✓ PEFT-Studio-1.0.0-x64.AppImage
  ✓ peft-studio_1.0.0_amd64.deb

Writing checksums file...
  ✓ SHA256SUMS.txt created

Verifying checksums...
  ✓ All checksums verified

=============================================================
Checksum Summary
=============================================================

Files processed: 8
Checksum file: release/SHA256SUMS.txt
Duration: 3.21s

✨ Checksums generated successfully!
```

### Exit Codes

- `0`: Checksums generated and verified
- `1`: Error occurred

### Examples

```bash
# Generate checksums
node scripts/generate-checksums.js

# Verify checksums manually (Linux/macOS)
cd release
sha256sum -c SHA256SUMS.txt

# Verify checksums manually (Windows PowerShell)
cd release
Get-FileHash * -Algorithm SHA256 | Format-List
```

### Notes

- Must be run after build step
- Uses SHA256 (secure hash algorithm)
- Verifies checksums after generation
- Standard format compatible with `sha256sum` tool

---

## release-to-github.js

### Purpose

Creates a GitHub release, uploads all installer artifacts and checksums, and creates a git tag.

### Usage

```bash
node scripts/release-to-github.js [options]
```

### Options

| Option | Description |
|--------|-------------|
| `--draft` | Create draft release (not published) |
| `--dry-run` | Simulate without creating release |

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | Yes | GitHub personal access token with `repo` scope |

### Process

1. Reads version from package.json
2. Extracts release notes from CHANGELOG.md
3. Creates GitHub release via API
4. Uploads all installer artifacts with retry logic
5. Uploads SHA256SUMS.txt
6. Verifies all uploads successful
7. Creates and pushes git tag
8. Generates release summary

### Output

```
=============================================================
Creating GitHub Release
=============================================================

Reading version from package.json...
  Version: 1.0.0

Extracting release notes from CHANGELOG.md...
  ✓ Release notes extracted

Creating GitHub release...
  ✓ Release created: v1.0.0

Uploading assets...
  ✓ PEFT-Studio-Setup-1.0.0.exe (1/9)
  ✓ PEFT-Studio-Portable-1.0.0.exe (2/9)
  ✓ PEFT-Studio-1.0.0-x64.dmg (3/9)
  ✓ PEFT-Studio-1.0.0-arm64.dmg (4/9)
  ✓ PEFT-Studio-1.0.0-x64.zip (5/9)
  ✓ PEFT-Studio-1.0.0-arm64.zip (6/9)
  ✓ PEFT-Studio-1.0.0-x64.AppImage (7/9)
  ✓ peft-studio_1.0.0_amd64.deb (8/9)
  ✓ SHA256SUMS.txt (9/9)

Verifying uploads...
  ✓ All assets uploaded successfully

Creating git tag...
  ✓ Tag v1.0.0 created and pushed

=============================================================
Release Summary
=============================================================

Release URL: https://github.com/Ankesh-007/peft-studio/releases/tag/v1.0.0
Tag: v1.0.0
Assets uploaded: 9
Total size: 450.23 MB
Duration: 5.32min

✨ Release created successfully!
```

### Exit Codes

- `0`: Release created successfully
- `1`: Release failed

### Examples

```bash
# Create release
export GITHUB_TOKEN="your_token"
node scripts/release-to-github.js

# Create draft release
node scripts/release-to-github.js --draft

# Dry run (test without creating)
node scripts/release-to-github.js --dry-run
```

### Notes

- Requires GITHUB_TOKEN environment variable
- Automatically retries failed uploads (up to 3 times)
- Creates git tag matching release version
- Extracts release notes from CHANGELOG.md
- Supports draft releases for testing

---

## complete-release.js

### Purpose

Master orchestration script that executes the complete release process in sequence with comprehensive error handling.

### Usage

```bash
node scripts/complete-release.js [options]
```

### Options

| Option | Description |
|--------|-------------|
| `--dry-run` | Simulate without making changes |
| `--skip-cleanup` | Skip repository cleanup step |
| `--skip-tests` | Skip test execution in validation |
| `--draft` | Create draft GitHub release |
| `--help` | Display help message |

### Execution Sequence

1. **Pre-flight Checks**: Verify working directory status
2. **Cleanup** (optional): Remove unnecessary files
3. **Validate**: Verify repository readiness
4. **Build**: Create installers for all platforms
5. **Checksum**: Generate SHA256 checksums
6. **Release**: Create GitHub release and upload assets

### Halt Behavior

- Stops on first failure of required step
- Reports which step failed
- Provides error details
- Allows skipping optional steps

### Output

```
======================================================================
PEFT Studio Complete Release Orchestration
======================================================================

[0] Pre-flight Checks
ℹ Checking working directory status...
✓ Working directory is clean

[1/5] Clean unnecessary files
> node scripts/cleanup-repository.js
✓ Clean unnecessary files completed (2.15s)

[2/5] Validate release readiness
> node scripts/validate-release.js
✓ Validate release readiness completed (15.32s)

[3/5] Build installers for all platforms
> node scripts/build.js all
✓ Build installers for all platforms completed (8.45min)

[4/5] Generate SHA256 checksums
> node scripts/generate-checksums.js
✓ Generate SHA256 checksums completed (3.21s)

[5/5] Create GitHub release and upload assets
> node scripts/release-to-github.js
✓ Create GitHub release and upload assets completed (5.32min)

======================================================================
Release Summary
======================================================================

Status: ✓ SUCCESS

Steps Executed: 5
  Successful: 5

Total Duration: 14.15min

Step Details:
  1. ✓ cleanup (2.15s)
  2. ✓ validate (15.32s)
  3. ✓ build (8.45min)
  4. ✓ checksum (3.21s)
  5. ✓ release (5.32min)

Release URL:
  https://github.com/Ankesh-007/peft-studio/releases/tag/v1.0.0

Release Assets:
  - PEFT-Studio-Setup-1.0.0.exe (125.50 MB)
  - PEFT-Studio-Portable-1.0.0.exe (120.30 MB)
  - PEFT-Studio-1.0.0-x64.dmg (65.20 MB)
  - PEFT-Studio-1.0.0-arm64.dmg (63.80 MB)
  - PEFT-Studio-1.0.0-x64.zip (60.10 MB)
  - PEFT-Studio-1.0.0-arm64.zip (58.90 MB)
  - PEFT-Studio-1.0.0-x64.AppImage (85.40 MB)
  - peft-studio_1.0.0_amd64.deb (82.10 MB)
  - SHA256SUMS.txt (0.00 MB)

======================================================================

🎉 Release completed successfully!
```

### Exit Codes

- `0`: All steps successful
- `1`: One or more steps failed

### Examples

```bash
# Full release
node scripts/complete-release.js

# Dry run (test without changes)
node scripts/complete-release.js --dry-run

# Skip cleanup
node scripts/complete-release.js --skip-cleanup

# Skip tests (faster)
node scripts/complete-release.js --skip-tests

# Create draft release
node scripts/complete-release.js --draft

# Combine options
node scripts/complete-release.js --skip-cleanup --skip-tests --draft

# Display help
node scripts/complete-release.js --help
```

### Notes

- Recommended for production releases
- Provides comprehensive error handling
- Generates detailed summary
- Supports dry-run for testing
- Can skip optional steps
- Halts on first failure

---

## Environment Variables

### GITHUB_TOKEN

**Required for**: `release-to-github.js`, `complete-release.js`

**Description**: GitHub personal access token for API authentication

**Scopes required**:
- `repo`: Full control of private repositories
- `write:packages`: Upload packages to GitHub Package Registry

**Setup**:
```bash
# Linux/macOS
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"

# Windows (PowerShell)
$env:GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"

# Windows (CMD)
set GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# Permanent (add to shell profile)
echo 'export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"' >> ~/.bashrc
source ~/.bashrc
```

### CSC_LINK (Optional)

**Required for**: Code signing

**Description**: Path to code signing certificate

**Example**:
```bash
export CSC_LINK="/path/to/certificate.p12"
```

### CSC_KEY_PASSWORD (Optional)

**Required for**: Code signing

**Description**: Password for code signing certificate

**Example**:
```bash
export CSC_KEY_PASSWORD="certificate_password"
```

---

## Exit Codes

All scripts follow standard Unix exit code conventions:

| Code | Meaning |
|------|---------|
| `0` | Success - operation completed without errors |
| `1` | Failure - operation failed or validation errors found |

### Usage in Scripts

```bash
# Check exit code
node scripts/validate-release.js
if [ $? -eq 0 ]; then
  echo "Validation passed"
else
  echo "Validation failed"
  exit 1
fi

# Or use && for chaining
node scripts/validate-release.js && \
node scripts/build.js all && \
node scripts/generate-checksums.js
```

---

## Related Documentation

- [Complete Release Process](./release-process.md)
- [Step-by-Step Guide](./release-step-by-step.md)
- [Troubleshooting Guide](./release-troubleshooting.md)
- [Dry-Run Testing](./release-dry-run-testing.md)

---

**Last Updated**: 2024-12-04
