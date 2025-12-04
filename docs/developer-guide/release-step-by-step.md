# Step-by-Step Release Guide

This guide provides detailed, step-by-step instructions for creating a PEFT Studio release.

## Table of Contents

1. [Preparation](#preparation)
2. [Pre-Release Checklist](#pre-release-checklist)
3. [Release Steps](#release-steps)
4. [Post-Release Verification](#post-release-verification)
5. [Rollback Procedure](#rollback-procedure)

## Preparation

### 1. Set Up Environment

Ensure your development environment is properly configured:

```bash
# Verify Node.js version (18+ required)
node --version

# Verify npm
npm --version

# Verify Git
git --version

# Set GitHub token
export GITHUB_TOKEN="your_github_personal_access_token"
```

### 2. Update Local Repository

```bash
# Fetch latest changes
git fetch origin

# Ensure you're on main branch
git checkout main

# Pull latest changes
git pull origin main

# Verify clean working directory
git status
```

### 3. Install Dependencies

```bash
# Install/update Node.js dependencies
npm install

# Install/update Python dependencies (if needed)
cd backend
pip install -r requirements.txt
cd ..
```

## Pre-Release Checklist

Before starting the release process, verify:

- [ ] All planned features are merged
- [ ] All tests pass locally
- [ ] CI/CD pipeline is green
- [ ] Documentation is up to date
- [ ] No open critical bugs
- [ ] CHANGELOG.md is ready for update
- [ ] Version number is decided
- [ ] GitHub token is set
- [ ] Working directory is clean

## Release Steps

### Step 1: Version Bump

Update the version number in `package.json`:

```bash
# For patch release (1.0.0 → 1.0.1)
npm version patch

# For minor release (1.0.0 → 1.1.0)
npm version minor

# For major release (1.0.0 → 2.0.0)
npm version major

# For pre-release (1.0.0 → 1.0.1-alpha.1)
npm version prerelease --preid=alpha
```

This command:
- Updates version in `package.json`
- Creates a git commit
- Creates a git tag

**Note**: If you prefer manual control, edit `package.json` directly and commit:

```bash
# Edit package.json manually
# Then commit
git add package.json
git commit -m "chore: bump version to 1.0.0"
```

### Step 2: Update CHANGELOG

Edit `CHANGELOG.md` to document the release:

```markdown
## [1.0.0] - 2024-12-04

### Added
- New feature: Multi-platform installer support
- Added checksum generation for security
- Implemented automated release workflow

### Changed
- Improved build performance by 50%
- Updated UI components for better accessibility

### Fixed
- Fixed memory leak in training monitor
- Resolved crash on macOS when loading large datasets

### Security
- Updated dependencies to patch vulnerabilities
```

**Guidelines:**
- Use present tense ("Add" not "Added")
- Be specific and concise
- Group by category: Added, Changed, Fixed, Removed, Security
- Include issue/PR numbers if applicable
- Add date in YYYY-MM-DD format

Commit the CHANGELOG:

```bash
git add CHANGELOG.md
git commit -m "docs: update CHANGELOG for v1.0.0"
```

### Step 3: Push Changes

Push your commits to GitHub:

```bash
# Push commits
git push origin main

# If you used npm version, push the tag too
git push origin --tags
```

### Step 4: Run Pre-Release Validation

Validate that everything is ready:

```bash
# Run validation script
node scripts/validate-release.js

# Expected output:
# ✓ LICENSE file exists
# ✓ .gitignore contains essential patterns
# ✓ README.md exists and is not empty
# ✓ All required fields present
# ✓ Version follows semantic versioning
# ✓ CHANGELOG contains entry for version 1.0.0
# ✓ All tests passed
# ✓ Working directory is clean
# ✅ Repository is ready for release!
```

If validation fails, fix the issues and re-run.

### Step 5: Test with Dry Run

Test the complete release process without making changes:

```bash
node scripts/complete-release.js --dry-run
```

Review the output carefully:
- Check that all steps would execute
- Verify artifact names are correct
- Ensure no unexpected errors

### Step 6: Execute Release

Run the complete release process:

```bash
node scripts/complete-release.js
```

This will:
1. Clean unnecessary files
2. Validate repository
3. Build installers for all platforms
4. Generate checksums
5. Create GitHub release
6. Upload all assets

**Expected duration**: 10-20 minutes depending on your system

**Monitor the output** for:
- ✓ Success indicators (green)
- ⚠ Warnings (yellow)
- ✗ Errors (red)

### Step 7: Verify Release on GitHub

1. Navigate to your repository's releases page:
   ```
   https://github.com/Ankesh-007/peft-studio/releases
   ```

2. Verify the new release:
   - [ ] Release title is correct
   - [ ] Release notes are formatted properly
   - [ ] All installer assets are present
   - [ ] SHA256SUMS.txt is uploaded
   - [ ] Download counts are visible
   - [ ] Release is not marked as draft (unless intentional)

3. Check asset list:
   - [ ] Windows Setup (NSIS)
   - [ ] Windows Portable
   - [ ] macOS DMG (x64)
   - [ ] macOS DMG (arm64)
   - [ ] macOS ZIP (x64)
   - [ ] macOS ZIP (arm64)
   - [ ] Linux AppImage
   - [ ] Linux DEB
   - [ ] SHA256SUMS.txt

## Post-Release Verification

### 1. Test Downloads

Download and test installers:

```bash
# Create test directory
mkdir -p ~/peft-studio-release-test
cd ~/peft-studio-release-test

# Download release assets
# (Use GitHub release page or curl)

# Verify checksums
curl -LO https://github.com/Ankesh-007/peft-studio/releases/download/v1.0.0/SHA256SUMS.txt

# On Linux/macOS
sha256sum -c SHA256SUMS.txt

# On Windows (PowerShell)
Get-FileHash *.exe -Algorithm SHA256 | Format-List
```

### 2. Test Installation

Test installers on each platform:

**Windows:**
1. Download and run Setup installer
2. Verify installation completes
3. Launch application
4. Test basic functionality
5. Uninstall and test Portable version

**macOS:**
1. Download DMG
2. Mount and drag to Applications
3. Launch application (handle Gatekeeper if needed)
4. Test basic functionality
5. Test ZIP archive version

**Linux:**
1. Download AppImage
2. Make executable: `chmod +x *.AppImage`
3. Run: `./PEFT-Studio-*.AppImage`
4. Test basic functionality
5. Test DEB package: `sudo dpkg -i *.deb`

### 3. Verify Auto-Update

If auto-update is implemented:

1. Install previous version
2. Launch application
3. Verify update notification appears
4. Test update process
5. Verify application updates successfully

### 4. Update Documentation

Update any documentation that references version numbers:

```bash
# Update README badges
# Update installation instructions
# Update screenshots if UI changed
# Update video tutorials if needed
```

### 5. Announce Release

Announce the release through appropriate channels:

- [ ] GitHub Discussions
- [ ] Twitter/Social media
- [ ] Mailing list
- [ ] Discord/Slack community
- [ ] Blog post (if applicable)

**Example announcement:**

```
🎉 PEFT Studio v1.0.0 is now available!

New features:
- Multi-platform installer support
- Automated release workflow
- Enhanced security with checksums

Download: https://github.com/Ankesh-007/peft-studio/releases/tag/v1.0.0

Full changelog: https://github.com/Ankesh-007/peft-studio/blob/main/CHANGELOG.md
```

## Rollback Procedure

If critical issues are discovered after release:

### Option 1: Quick Patch Release

For minor issues:

1. Fix the issue
2. Bump patch version
3. Create new release
4. Mark previous release as "superseded" in description

### Option 2: Delete Release

For critical issues:

```bash
# Delete release from GitHub
gh release delete v1.0.0 --yes

# Delete tag locally
git tag -d v1.0.0

# Delete tag remotely
git push origin :refs/tags/v1.0.0

# Revert commits if needed
git revert <commit-hash>
git push origin main
```

### Option 3: Mark as Pre-release

For issues that need investigation:

1. Edit release on GitHub
2. Check "This is a pre-release"
3. Add warning to release notes
4. Investigate and fix
5. Create new stable release

## Troubleshooting

### Release Script Fails

If `complete-release.js` fails:

1. **Check which step failed**:
   - Review console output
   - Look for red error messages
   - Note the failed step number

2. **Fix the issue**:
   - See [Troubleshooting Guide](./release-troubleshooting.md)
   - Fix the specific problem
   - Re-run from failed step if possible

3. **Resume or restart**:
   ```bash
   # If cleanup failed, skip it
   node scripts/complete-release.js --skip-cleanup
   
   # If tests failed, skip them (not recommended)
   node scripts/complete-release.js --skip-tests
   
   # Or run individual steps
   node scripts/validate-release.js
   node scripts/build.js all
   node scripts/generate-checksums.js
   node scripts/release-to-github.js
   ```

### Build Fails on Specific Platform

If build fails for one platform:

1. **Build other platforms first**:
   ```bash
   node scripts/build.js windows
   node scripts/build.js mac
   node scripts/build.js linux
   ```

2. **Debug the failing platform**:
   - Check build logs
   - Verify platform-specific dependencies
   - Test on that platform if possible

3. **Release without that platform** (temporary):
   - Build available platforms
   - Generate checksums
   - Create release
   - Add note about missing platform
   - Fix and add later

### GitHub API Rate Limit

If you hit GitHub API rate limits:

1. **Wait for reset**:
   ```bash
   # Check rate limit status
   curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/rate_limit
   ```

2. **Use authenticated requests**:
   - Ensure GITHUB_TOKEN is set
   - Authenticated requests have higher limits

3. **Retry later**:
   - Rate limits reset hourly
   - Wait and retry

## Best Practices

### Timing

- **Avoid Fridays**: Don't release on Fridays (less time to fix issues)
- **Avoid holidays**: Users may not be available for testing
- **Business hours**: Release during business hours for quick response
- **Regular schedule**: Establish predictable release cadence

### Communication

- **Announce in advance**: Give users heads-up about upcoming release
- **Document breaking changes**: Clearly communicate any breaking changes
- **Provide migration guides**: Help users upgrade smoothly
- **Be responsive**: Monitor issues and discussions after release

### Quality

- **Test thoroughly**: Don't skip testing steps
- **Use dry runs**: Always test with --dry-run first
- **Verify checksums**: Ensure security verification works
- **Monitor metrics**: Watch download counts and error reports

### Documentation

- **Keep CHANGELOG current**: Update with every change
- **Version documentation**: Tag docs with release version
- **Update examples**: Ensure examples work with new version
- **Screenshot updates**: Update screenshots if UI changed

## Checklist Summary

Use this quick checklist for releases:

- [ ] Version bumped in package.json
- [ ] CHANGELOG.md updated
- [ ] Changes committed and pushed
- [ ] Validation passed
- [ ] Dry run successful
- [ ] Release executed
- [ ] GitHub release verified
- [ ] Assets downloaded and tested
- [ ] Checksums verified
- [ ] Installation tested on all platforms
- [ ] Documentation updated
- [ ] Release announced

## Related Documentation

- [Complete Release Process](./release-process.md)
- [Script Reference](./release-scripts-reference.md)
- [Troubleshooting Guide](./release-troubleshooting.md)
- [Dry-Run Testing](./release-dry-run-testing.md)

---

**Last Updated**: 2024-12-04
