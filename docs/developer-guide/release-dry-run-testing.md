# Dry-Run Testing Guide

This guide explains how to test the release process using dry-run mode without making any actual changes to your repository or creating real releases.

## Table of Contents

1. [What is Dry-Run Mode?](#what-is-dry-run-mode)
2. [Why Use Dry-Run?](#why-use-dry-run)
3. [Testing Individual Scripts](#testing-individual-scripts)
4. [Testing Complete Release](#testing-complete-release)
5. [Interpreting Dry-Run Output](#interpreting-dry-run-output)
6. [Common Test Scenarios](#common-test-scenarios)
7. [Best Practices](#best-practices)

---

## What is Dry-Run Mode?

Dry-run mode simulates the release process without making any actual changes:

- **No files are deleted** (cleanup)
- **No builds are created** (build)
- **No GitHub releases are created** (release)
- **No git tags are pushed** (release)
- **All validation checks still run** (validate)

It shows you exactly what would happen if you ran the real release.

---

## Why Use Dry-Run?

### Safety

- Test release process without risk
- Verify configuration before real release
- Catch issues early

### Learning

- Understand what each step does
- See expected output
- Learn the release workflow

### Debugging

- Identify problems without consequences
- Test fixes safely
- Verify changes work

### Planning

- Estimate release duration
- Verify all prerequisites
- Check artifact names and sizes

---

## Testing Individual Scripts

### Test Cleanup

Preview what files would be removed:

```bash
node scripts/cleanup-repository.js --dry-run
```

**Expected output:**
```
=============================================================
Repository Cleanup
=============================================================

🔍 DRY RUN MODE - No files will be deleted

📋 Step 1: Identifying unnecessary files...
  Found 45 item(s) to remove:
    - Build artifacts: 12
    - Test caches: 8
    - Python bytecode: 20
    - Temporary files: 5

🗑️  Step 2: Removing unnecessary files...
  [DRY RUN] Would remove: release/old-installer.exe
  [DRY RUN] Would remove: dist/bundle.js
  [DRY RUN] Would remove: .pytest_cache/
  ...

📦 Step 3: Cleaning release directory...
  [DRY RUN] Would remove: release/win-unpacked/

📝 Step 4: Updating .gitignore...
  [DRY RUN] Would add 8 pattern(s) to .gitignore

📊 Step 5: Generating cleanup report...

=============================================================
Cleanup Summary
=============================================================
Files removed: 45
Space freed: 125.43 MB
Duration: 0.52s

💡 Run without --dry-run to actually remove files
```

**What to check:**
- [ ] Files to be removed are correct
- [ ] Essential files are preserved
- [ ] .gitignore patterns are appropriate
- [ ] Space freed is reasonable

---

### Test Validation

Validation always runs real checks (no dry-run mode):

```bash
node scripts/validate-release.js
```

**Expected output:**
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

**What to check:**
- [ ] All validation checks pass
- [ ] Version number is correct
- [ ] CHANGELOG is updated
- [ ] Tests pass
- [ ] Working directory is clean

**Skip tests for faster validation:**
```bash
node scripts/validate-release.js --skip-tests
```

---

### Test Build

Build script doesn't have dry-run mode (builds are local and safe):

```bash
# Test build for single platform
node scripts/build.js windows

# Or test all platforms
node scripts/build.js all
```

**Note:** Builds are created locally in `release/` directory. You can delete them after testing.

**What to check:**
- [ ] Build completes without errors
- [ ] All expected artifacts are created
- [ ] File sizes are reasonable
- [ ] Artifact names are correct

---

### Test Checksum Generation

Checksum generation doesn't have dry-run mode (safe operation):

```bash
node scripts/generate-checksums.js
```

**What to check:**
- [ ] SHA256SUMS.txt is created
- [ ] All installers are included
- [ ] Format is correct (hash  filename)
- [ ] Verification passes

---

### Test GitHub Release

Preview GitHub release creation:

```bash
node scripts/release-to-github.js --dry-run
```

**Expected output:**
```
=============================================================
Creating GitHub Release
=============================================================

🔍 DRY RUN MODE - No release will be created

Reading version from package.json...
  Version: 1.0.0

Extracting release notes from CHANGELOG.md...
  ✓ Release notes extracted:
  
  ### Added
  - New feature description
  
  ### Changed
  - Change description

Creating GitHub release...
  [DRY RUN] Would create release: v1.0.0
  [DRY RUN] Release URL: https://github.com/Ankesh-007/peft-studio/releases/tag/v1.0.0

Uploading assets...
  [DRY RUN] Would upload: PEFT-Studio-Setup-1.0.0.exe (125.5 MB)
  [DRY RUN] Would upload: PEFT-Studio-Portable-1.0.0.exe (120.3 MB)
  [DRY RUN] Would upload: PEFT-Studio-1.0.0-x64.dmg (65.2 MB)
  [DRY RUN] Would upload: PEFT-Studio-1.0.0-arm64.dmg (63.8 MB)
  [DRY RUN] Would upload: PEFT-Studio-1.0.0-x64.zip (60.1 MB)
  [DRY RUN] Would upload: PEFT-Studio-1.0.0-arm64.zip (58.9 MB)
  [DRY RUN] Would upload: PEFT-Studio-1.0.0-x64.AppImage (85.4 MB)
  [DRY RUN] Would upload: peft-studio_1.0.0_amd64.deb (82.1 MB)
  [DRY RUN] Would upload: SHA256SUMS.txt (0.5 KB)

Creating git tag...
  [DRY RUN] Would create tag: v1.0.0
  [DRY RUN] Would push tag to origin

=============================================================
Release Summary
=============================================================

[DRY RUN] Release URL: https://github.com/Ankesh-007/peft-studio/releases/tag/v1.0.0
[DRY RUN] Tag: v1.0.0
[DRY RUN] Assets to upload: 9
[DRY RUN] Total size: 450.23 MB
Duration: 1.23s

💡 Run without --dry-run to create actual release
```

**What to check:**
- [ ] Version number is correct
- [ ] Release notes are formatted properly
- [ ] All expected assets are listed
- [ ] Asset names are correct
- [ ] Total size is reasonable
- [ ] Git tag name is correct

---

## Testing Complete Release

Test the entire release workflow:

```bash
node scripts/complete-release.js --dry-run
```

**Expected output:**
```
======================================================================
PEFT Studio Complete Release Orchestration
======================================================================

🔍 DRY RUN MODE - No changes will be made

[0] Pre-flight Checks
ℹ Checking working directory status...
✓ Working directory is clean

[1/5] Clean unnecessary files
ℹ [DRY RUN] Would execute: node scripts/cleanup-repository.js
✓ Clean unnecessary files completed (skipped)

[2/5] Validate release readiness
> node scripts/validate-release.js
✓ Validate release readiness completed (15.32s)

[3/5] Build installers for all platforms
ℹ [DRY RUN] Would execute: node scripts/build.js all
✓ Build installers for all platforms completed (skipped)

[4/5] Generate SHA256 checksums
ℹ [DRY RUN] Would execute: node scripts/generate-checksums.js
✓ Generate SHA256 checksums completed (skipped)

[5/5] Create GitHub release and upload assets
ℹ [DRY RUN] Would execute: node scripts/release-to-github.js
✓ Create GitHub release and upload assets completed (skipped)

======================================================================
Release Summary
======================================================================

Status: ✓ SUCCESS

Steps Executed: 5
  Successful: 5

Total Duration: 15.45s

Step Details:
  1. ✓ cleanup (skipped)
  2. ✓ validate (15.32s)
  3. ✓ build (skipped)
  4. ✓ checksum (skipped)
  5. ✓ release (skipped)

✨ Dry run completed successfully!
Run without --dry-run to perform the actual release.
```

**What to check:**
- [ ] All steps would execute in correct order
- [ ] Validation passes
- [ ] No errors or warnings
- [ ] Estimated duration is acceptable
- [ ] All prerequisites are met

---

## Interpreting Dry-Run Output

### Success Indicators

Look for these positive signs:

- ✓ Green checkmarks
- "DRY RUN MODE" messages
- "Would execute" or "Would create" messages
- No red error messages
- Final success message

### Warning Signs

Watch for these issues:

- ⚠ Yellow warnings
- Missing files or directories
- Validation failures
- Incorrect versions
- Uncommitted changes

### Error Indicators

Stop and fix these:

- ✗ Red X marks
- "Error:" messages
- "Failed" status
- Missing prerequisites
- Invalid configuration

---

## Common Test Scenarios

### Scenario 1: First-Time Release

Test the complete process before your first release:

```bash
# 1. Prepare repository
git checkout main
git pull origin main

# 2. Update version and CHANGELOG
npm version 1.0.0
# Edit CHANGELOG.md

# 3. Commit changes
git add .
git commit -m "chore: prepare release v1.0.0"

# 4. Test complete release
node scripts/complete-release.js --dry-run

# 5. If successful, run real release
node scripts/complete-release.js
```

---

### Scenario 2: Testing After Changes

Test after modifying release scripts:

```bash
# 1. Make changes to scripts
# Edit scripts/build.js or other scripts

# 2. Test individual script
node scripts/build.js windows

# 3. Test complete workflow
node scripts/complete-release.js --dry-run

# 4. Verify output is correct
# Check for any unexpected behavior

# 5. If good, commit changes
git add scripts/
git commit -m "feat: improve build script"
```

---

### Scenario 3: Testing Different Options

Test various release configurations:

```bash
# Test with cleanup
node scripts/complete-release.js --dry-run

# Test without cleanup
node scripts/complete-release.js --dry-run --skip-cleanup

# Test without tests
node scripts/complete-release.js --dry-run --skip-tests

# Test draft release
node scripts/complete-release.js --dry-run --draft

# Test combination
node scripts/complete-release.js --dry-run --skip-cleanup --skip-tests --draft
```

---

### Scenario 4: Testing Error Handling

Test how scripts handle errors:

```bash
# Test with missing CHANGELOG entry
# (Comment out version in CHANGELOG.md)
node scripts/validate-release.js
# Should fail with clear error

# Test with uncommitted changes
# (Make a change without committing)
node scripts/validate-release.js
# Should warn about uncommitted changes

# Test without GITHUB_TOKEN
unset GITHUB_TOKEN
node scripts/release-to-github.js --dry-run
# Should fail with clear error

# Restore token
export GITHUB_TOKEN="your_token"
```

---

### Scenario 5: Testing Platform-Specific Builds

Test builds for specific platforms:

```bash
# Test Windows build
node scripts/build.js windows
ls -la release/

# Test macOS build
node scripts/build.js mac
ls -la release/

# Test Linux build
node scripts/build.js linux
ls -la release/

# Clean up test builds
rm -rf release/*
```

---

## Best Practices

### Always Dry-Run First

Before any real release:

```bash
# 1. Dry run
node scripts/complete-release.js --dry-run

# 2. Review output carefully

# 3. If everything looks good, run real release
node scripts/complete-release.js
```

### Test Incrementally

Test each step individually before testing complete workflow:

```bash
# 1. Test cleanup
node scripts/cleanup-repository.js --dry-run

# 2. Test validation
node scripts/validate-release.js

# 3. Test build
node scripts/build.js windows

# 4. Test checksums
node scripts/generate-checksums.js

# 5. Test release
node scripts/release-to-github.js --dry-run

# 6. Test complete workflow
node scripts/complete-release.js --dry-run
```

### Document Test Results

Keep a record of dry-run tests:

```bash
# Save dry-run output
node scripts/complete-release.js --dry-run > dry-run-test.log 2>&1

# Review later
cat dry-run-test.log

# Compare with previous tests
diff dry-run-test-old.log dry-run-test.log
```

### Test in Clean Environment

Test in a clean state:

```bash
# 1. Clean build artifacts
rm -rf release/* dist/* build/*

# 2. Clean dependencies
rm -rf node_modules
npm install

# 3. Test
node scripts/complete-release.js --dry-run
```

### Test Edge Cases

Test unusual scenarios:

```bash
# Test with pre-release version
npm version 1.0.0-alpha.1
node scripts/complete-release.js --dry-run

# Test with no previous releases
# (Delete all releases on GitHub)
node scripts/complete-release.js --dry-run

# Test with large files
# (Add large test file to release/)
node scripts/generate-checksums.js
```

### Automate Testing

Add dry-run tests to CI/CD:

```yaml
# .github/workflows/test-release.yml
name: Test Release Process

on:
  pull_request:
    branches: [main]

jobs:
  test-release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: npm install
      - run: node scripts/validate-release.js --skip-tests
      - run: node scripts/complete-release.js --dry-run
```

---

## Troubleshooting Dry-Run Tests

### Dry-Run Passes But Real Release Fails

**Possible causes:**
- Network issues (not tested in dry-run)
- GitHub API issues (not tested in dry-run)
- Insufficient permissions (not tested in dry-run)

**Solution:**
- Test network connectivity
- Verify GitHub token permissions
- Check GitHub API status

### Dry-Run Shows Unexpected Output

**Possible causes:**
- Configuration changes
- Script modifications
- Environment differences

**Solution:**
- Review recent changes
- Compare with previous dry-runs
- Check environment variables

### Dry-Run Takes Too Long

**Possible causes:**
- Validation running all tests
- Large number of files to check

**Solution:**
```bash
# Skip tests for faster dry-run
node scripts/complete-release.js --dry-run --skip-tests

# Or test individual steps
node scripts/validate-release.js --skip-tests
node scripts/release-to-github.js --dry-run
```

---

## Checklist

Use this checklist for dry-run testing:

- [ ] Clean working directory
- [ ] Updated version in package.json
- [ ] Updated CHANGELOG.md
- [ ] GITHUB_TOKEN set
- [ ] Run cleanup dry-run
- [ ] Run validation
- [ ] Run complete release dry-run
- [ ] Review all output
- [ ] Check for warnings or errors
- [ ] Verify artifact names
- [ ] Verify version numbers
- [ ] Verify release notes
- [ ] Document any issues
- [ ] Fix issues if found
- [ ] Re-test after fixes
- [ ] Ready for real release

---

## Related Documentation

- [Complete Release Process](./release-process.md)
- [Step-by-Step Guide](./release-step-by-step.md)
- [Scripts Reference](./release-scripts-reference.md)
- [Troubleshooting Guide](./release-troubleshooting.md)

---

**Last Updated**: 2024-12-04
