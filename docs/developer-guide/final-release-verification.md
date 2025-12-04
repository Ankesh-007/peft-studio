# Final Release Verification Guide

This guide explains how to perform comprehensive verification of a completed GitHub release to ensure everything is working correctly and the repository looks professional.

## Overview

The final release verification process checks:

1. **GitHub Release Completeness** - Verify the release exists with all expected assets
2. **Download Link Accessibility** - Test that all installer downloads work
3. **Checksum Validation** - Verify SHA256SUMS.txt is properly formatted and complete
4. **Repository Professionalism** - Ensure documentation and structure meet standards

## Quick Start

### Verify Current Release

```bash
npm run verify:release
```

This will verify the release for the version specified in `package.json`.

### Verify Specific Version

```bash
node scripts/verify-final-release.js --version 1.0.1
```

### Skip Download Tests (Faster)

```bash
npm run verify:release:skip-downloads
```

Or:

```bash
node scripts/verify-final-release.js --skip-downloads
```

## Verification Steps

### 1. GitHub Release Verification

The script checks:

- ✅ Release exists on GitHub
- ✅ Release has the correct version tag
- ✅ Release contains expected asset types:
  - Windows installer (Setup.exe)
  - Windows portable (Portable.exe)
  - macOS DMG files
  - Linux AppImage
  - SHA256SUMS.txt

**Example Output:**

```
=== Verifying GitHub Release ===
ℹ Checking release for Ankesh-007/peft-studio version 1.0.1...
✓ Release found: v1.0.1
  URL: https://github.com/Ankesh-007/peft-studio/releases/tag/v1.0.1
  Published: 2024-01-15T10:30:00Z
  Draft: false
  Prerelease: false

  Assets (8):
    - PEFT Studio-Setup-1.0.1.exe (45.23 MB)
    - PEFT Studio-Portable-1.0.1.exe (45.10 MB)
    - PEFT Studio-1.0.1-x64.dmg (48.50 MB)
    - PEFT Studio-1.0.1-arm64.dmg (47.80 MB)
    - PEFT Studio-1.0.1-x64.AppImage (52.30 MB)
    - PEFT Studio-1.0.1-amd64.deb (45.60 MB)
    - SHA256SUMS.txt (0.00 MB)
    - latest.yml (0.00 MB)

✓ All expected asset types present
```

### 2. Download Link Testing

The script tests each download link to ensure it's accessible:

- ✅ HTTP HEAD request succeeds (200 OK)
- ✅ File size is reported correctly
- ✅ No broken links

**Example Output:**

```
=== Testing Download Links ===
ℹ Testing 8 download links...
✓ PEFT Studio-Setup-1.0.1.exe (45.23 MB)
✓ PEFT Studio-Portable-1.0.1.exe (45.10 MB)
✓ PEFT Studio-1.0.1-x64.dmg (48.50 MB)
✓ PEFT Studio-1.0.1-arm64.dmg (47.80 MB)
✓ PEFT Studio-1.0.1-x64.AppImage (52.30 MB)
✓ PEFT Studio-1.0.1-amd64.deb (45.60 MB)
✓ SHA256SUMS.txt (0.00 MB)
✓ latest.yml (0.00 MB)

✓ All 8 download links are accessible
```

### 3. Checksum Verification

The script verifies the SHA256SUMS.txt file:

- ✅ File exists in release assets
- ✅ Format is correct (64-char hex hash, two spaces, filename)
- ✅ All installers have corresponding checksums
- ✅ No missing or extra entries

**Example Output:**

```
=== Verifying Checksums ===
✓ SHA256SUMS.txt found in release
ℹ Downloading checksum file...

Checksum file contains 6 entries:
  ✓ PEFT Studio-Setup-1.0.1.exe
  ✓ PEFT Studio-Portable-1.0.1.exe
  ✓ PEFT Studio-1.0.1-x64.dmg
  ✓ PEFT Studio-1.0.1-arm64.dmg
  ✓ PEFT Studio-1.0.1-x64.AppImage
  ✓ PEFT Studio-1.0.1-amd64.deb

✓ All 6 checksum entries are properly formatted
✓ All installers have checksums
```

### 4. Repository Professionalism

The script checks repository documentation and structure:

**README.md:**
- ✅ Title/header present
- ✅ Description (at least 50 characters)
- ✅ Installation section
- ✅ Usage section
- ✅ License section
- ✅ Badges present

**LICENSE:**
- ✅ File exists
- ✅ Substantial content (>100 characters)

**CONTRIBUTING.md:**
- ✅ File exists

**CHANGELOG.md:**
- ✅ File exists
- ✅ Contains current version entry

**.gitignore:**
- ✅ File exists
- ✅ Contains essential patterns (node_modules, dist, *.log, release)

**package.json:**
- ✅ All required metadata fields present
- ✅ Keywords specified for discoverability

**Example Output:**

```
=== Verifying Repository Professionalism ===
Checking README.md...
  ✓ Title/Header section present
  ✓ Description section present
  ✓ Installation section present
  ✓ Usage section present
  ✓ License section present
  ✓ Badges present

Checking LICENSE...
  ✓ LICENSE file present and substantial

Checking CONTRIBUTING.md...
  ✓ CONTRIBUTING.md present

Checking CHANGELOG.md...
  ✓ CHANGELOG.md includes version 1.0.1

Checking .gitignore...
  ✓ .gitignore contains essential patterns

Checking package.json metadata...
  ✓ All required metadata fields present
  ✓ Keywords present (13)
```

## Verification Report

After running, the script generates a detailed report saved to `VERIFICATION_REPORT.md`:

```markdown
# Final Release Verification Report

Generated: 2024-01-15T10:45:00.000Z
Version: 1.0.1

## GitHub Release

- ✓ Release exists: https://github.com/Ankesh-007/peft-studio/releases/tag/v1.0.1
- Assets: 8
- Draft: false
- Prerelease: false

## Download Links

- Tested: 8
- Accessible: 8
- Failed: 0

## Checksums

- File exists: ✓
- Format valid: ✓
- Entries: 6

## Repository Professionalism

- ✓ license
- ✓ contributing
- ✓ changelog
- ✓ gitignore
- ✓ packageMetadata
- ✓ keywords

## Summary

✅ **All verifications passed!**
```

## Command-Line Options

### `--version <version>`

Specify which version to verify (default: from package.json):

```bash
node scripts/verify-final-release.js --version 1.0.1
```

### `--skip-downloads`

Skip testing actual downloads (faster, useful for quick checks):

```bash
node scripts/verify-final-release.js --skip-downloads
```

### `--help`

Display help message:

```bash
node scripts/verify-final-release.js --help
```

## Environment Variables

### `GITHUB_TOKEN` (Optional)

GitHub personal access token. Recommended to avoid API rate limits:

```bash
export GITHUB_TOKEN=ghp_your_token_here
node scripts/verify-final-release.js
```

Without a token, you're limited to 60 API requests per hour. With a token, you get 5,000 requests per hour.

## Exit Codes

- `0` - All verifications passed
- `1` - One or more verifications failed

## Troubleshooting

### "Release not found"

**Cause:** The release doesn't exist on GitHub or the version tag is incorrect.

**Solution:**
1. Check that the release was created successfully
2. Verify the version in package.json matches the release tag
3. Ensure the release is published (not a draft)

### "Download link not accessible"

**Cause:** The asset URL is broken or the file wasn't uploaded correctly.

**Solution:**
1. Check the GitHub release page manually
2. Try downloading the file in a browser
3. Re-upload the asset if necessary

### "Checksum file not found"

**Cause:** SHA256SUMS.txt wasn't uploaded to the release.

**Solution:**
1. Run `npm run generate:checksums` to create the file
2. Upload it to the release manually or re-run the release script

### "Invalid checksum format"

**Cause:** SHA256SUMS.txt has incorrect formatting.

**Solution:**
1. Ensure the format is: `<64-char-hex-hash>  <filename>` (two spaces)
2. Regenerate checksums with `npm run generate:checksums`

### "README missing sections"

**Cause:** README.md doesn't contain required sections.

**Solution:**
1. Add missing sections (Installation, Usage, License, etc.)
2. Run `node scripts/enhance-documentation.js` to auto-enhance

### "LICENSE is missing"

**Cause:** No LICENSE file in repository root.

**Solution:**
1. Add a LICENSE file with your chosen license
2. Update package.json to specify the license type

### "CHANGELOG doesn't include current version"

**Cause:** CHANGELOG.md hasn't been updated for the current release.

**Solution:**
1. Add an entry for the current version in CHANGELOG.md
2. Follow the format: `## [1.0.1] - 2024-01-15`

## Integration with Release Workflow

The verification script is designed to be run after a release is complete:

```bash
# 1. Complete the release
npm run release

# 2. Verify the release
npm run verify:release

# 3. Review the verification report
cat VERIFICATION_REPORT.md
```

You can also integrate it into your CI/CD pipeline:

```yaml
# .github/workflows/verify-release.yml
name: Verify Release

on:
  release:
    types: [published]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run verify:release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Best Practices

1. **Always verify after releasing** - Catch issues before users do
2. **Use --skip-downloads for quick checks** - Save time during development
3. **Review the verification report** - Keep it for your records
4. **Fix issues immediately** - Don't let broken releases linger
5. **Automate in CI/CD** - Catch problems automatically

## Related Documentation

- [Release Process](./release-process.md) - Complete release workflow
- [Release Step-by-Step](./release-step-by-step.md) - Detailed release instructions
- [Release Troubleshooting](./release-troubleshooting.md) - Common issues and solutions
- [Release Scripts Reference](./release-scripts-reference.md) - All release scripts

## Support

If you encounter issues not covered in this guide:

1. Check the [Release Troubleshooting Guide](./release-troubleshooting.md)
2. Review the verification report for specific errors
3. Open an issue on GitHub with the verification report attached
