# Release Troubleshooting Guide

Comprehensive troubleshooting guide for common issues encountered during the PEFT Studio release process.

## Table of Contents

1. [Environment Issues](#environment-issues)
2. [Validation Failures](#validation-failures)
3. [Build Failures](#build-failures)
4. [Checksum Issues](#checksum-issues)
5. [GitHub Release Issues](#github-release-issues)
6. [Platform-Specific Issues](#platform-specific-issues)
7. [Network Issues](#network-issues)
8. [Recovery Procedures](#recovery-procedures)

---

## Environment Issues

### Issue: GITHUB_TOKEN not set

**Symptoms:**
```
Error: GITHUB_TOKEN environment variable is not set
```

**Cause:** GitHub token not configured

**Solution:**
```bash
# Set token for current session
export GITHUB_TOKEN="your_github_token_here"

# Or add to shell profile for persistence
echo 'export GITHUB_TOKEN="your_token"' >> ~/.bashrc
source ~/.bashrc

# Verify it's set
echo $GITHUB_TOKEN
```

**Prevention:**
- Add token to shell profile
- Use environment file (`.env`)
- Document in team onboarding

---

### Issue: Node.js version mismatch

**Symptoms:**
```
Error: Node.js version 16.x is not supported
Required: Node.js 18.x or higher
```

**Cause:** Outdated Node.js version

**Solution:**
```bash
# Check current version
node --version

# Update Node.js
# Using nvm (recommended)
nvm install 18
nvm use 18

# Or download from nodejs.org
# https://nodejs.org/

# Verify
node --version  # Should show v18.x.x or higher
```

**Prevention:**
- Use nvm for version management
- Document required version in README
- Add version check to scripts

---

### Issue: Missing dependencies

**Symptoms:**
```
Error: Cannot find module 'electron-builder'
```

**Cause:** Dependencies not installed

**Solution:**
```bash
# Remove existing installations
rm -rf node_modules package-lock.json

# Reinstall dependencies
npm install

# Verify installation
npm list electron-builder
```

**Prevention:**
- Run `npm install` before release
- Keep package-lock.json in version control
- Document dependency installation

---

## Validation Failures

### Issue: Working directory has uncommitted changes

**Symptoms:**
```
✗ Working directory has uncommitted changes:
  M package.json
  M CHANGELOG.md
```

**Cause:** Uncommitted files in repository

**Solution:**

**Option 1: Commit changes**
```bash
git add .
git commit -m "chore: prepare release v1.0.0"
git push origin main
```

**Option 2: Stash changes**
```bash
git stash
# Run release
git stash pop
```

**Option 3: Force release (not recommended)**
```bash
# Skip validation
node scripts/complete-release.js --skip-tests
```

**Prevention:**
- Commit changes before release
- Use pre-release checklist
- Automate version bumps

---

### Issue: CHANGELOG missing version entry

**Symptoms:**
```
✗ CHANGELOG does not contain entry for version 1.0.0
```

**Cause:** CHANGELOG.md not updated

**Solution:**

1. Open `CHANGELOG.md`
2. Add entry for current version:

```markdown
## [1.0.0] - 2024-12-04

### Added
- Feature description

### Changed
- Change description

### Fixed
- Bug fix description
```

3. Commit and retry:
```bash
git add CHANGELOG.md
git commit -m "docs: update CHANGELOG for v1.0.0"
node scripts/validate-release.js
```

**Prevention:**
- Update CHANGELOG with each PR
- Use automated CHANGELOG generation
- Include in release checklist

---

### Issue: Tests failing

**Symptoms:**
```
✗ Tests failed
npm ERR! Test failed. See above for more details.
```

**Cause:** Test suite has failures

**Solution:**

1. **Run tests locally:**
```bash
npm run test:run
```

2. **Identify failing tests:**
```
FAIL src/components/Button.test.tsx
  ● Button › should render correctly
    Expected: "Click me"
    Received: "Click"
```

3. **Fix failing tests:**
- Review test output
- Fix code or update tests
- Re-run tests

4. **Retry validation:**
```bash
node scripts/validate-release.js
```

**Temporary workaround (not recommended):**
```bash
node scripts/validate-release.js --skip-tests
```

**Prevention:**
- Run tests before committing
- Use pre-commit hooks
- Monitor CI/CD pipeline

---

### Issue: Invalid semantic version

**Symptoms:**
```
✗ Version does not follow semantic versioning: 1.0
```

**Cause:** Version in package.json not valid semver

**Solution:**

1. Open `package.json`
2. Fix version format:
```json
{
  "version": "1.0.0"  // Must be MAJOR.MINOR.PATCH
}
```

3. Commit and retry:
```bash
git add package.json
git commit -m "fix: correct version format"
node scripts/validate-release.js
```

**Valid formats:**
- `1.0.0` (release)
- `1.0.0-alpha.1` (pre-release)
- `1.0.0-beta.2` (beta)
- `1.0.0-rc.1` (release candidate)

**Prevention:**
- Use `npm version` command
- Validate version format in CI
- Document versioning scheme

---

## Build Failures

### Issue: Build fails with "Cannot find module"

**Symptoms:**
```
Error: Cannot find module '@/components/Button'
```

**Cause:** Missing dependencies or incorrect imports

**Solution:**

1. **Reinstall dependencies:**
```bash
rm -rf node_modules package-lock.json
npm install
```

2. **Check import paths:**
```typescript
// Incorrect
import Button from '@/components/Button'

// Correct (verify path alias in tsconfig.json)
import Button from '../components/Button'
```

3. **Verify tsconfig.json:**
```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

4. **Retry build:**
```bash
node scripts/build.js all
```

**Prevention:**
- Use consistent import paths
- Validate imports before committing
- Configure path aliases properly

---

### Issue: Out of memory during build

**Symptoms:**
```
FATAL ERROR: Reached heap limit Allocation failed
JavaScript heap out of memory
```

**Cause:** Insufficient memory for build process

**Solution:**

1. **Increase Node.js memory:**
```bash
# Linux/macOS
export NODE_OPTIONS="--max-old-space-size=4096"

# Windows (PowerShell)
$env:NODE_OPTIONS="--max-old-space-size=4096"

# Retry build
node scripts/build.js all
```

2. **Build platforms separately:**
```bash
node scripts/build.js windows
node scripts/build.js mac
node scripts/build.js linux
```

3. **Close other applications:**
- Free up system memory
- Close browser tabs
- Stop other processes

**Prevention:**
- Set NODE_OPTIONS in environment
- Build on machine with adequate RAM (8GB+)
- Use CI/CD with sufficient resources

---

### Issue: Platform-specific build fails

**Symptoms:**
```
✗ macOS build failed
Error: Cannot find entitlements file
```

**Cause:** Missing platform-specific configuration

**Solution:**

**For macOS:**
```bash
# Check entitlements file exists
ls build/entitlements.mac.plist

# If missing, create it
# See docs/developer-guide/build-and-installers.md
```

**For Windows:**
```bash
# Check icon exists
ls build/icon.ico

# If missing, add icon file
```

**For Linux:**
```bash
# Check icon exists
ls build/icon.png

# If missing, add icon file
```

**Workaround - Build other platforms:**
```bash
# Skip failing platform
node scripts/build.js windows
node scripts/build.js linux
# Fix macOS issue later
```

**Prevention:**
- Verify build assets exist
- Test builds on each platform
- Document platform requirements

---

### Issue: Code signing fails

**Symptoms:**
```
⚠ Code signing failed
Warning: Installers are not signed
```

**Cause:** Missing or invalid signing certificates

**Solution:**

**Option 1: Skip signing (development)**
```bash
# Unset signing variables
unset CSC_LINK
unset CSC_KEY_PASSWORD

# Build without signing
node scripts/build.js all
```

**Option 2: Configure signing (production)**
```bash
# Set certificate path and password
export CSC_LINK="/path/to/certificate.p12"
export CSC_KEY_PASSWORD="your_password"

# Retry build
node scripts/build.js all
```

**Note:** Unsigned builds work but may show security warnings to users.

**Prevention:**
- Document signing setup
- Use separate dev/prod configurations
- Store certificates securely

---

## Checksum Issues

### Issue: No installer files found

**Symptoms:**
```
Error: No installer files found in release/ directory
```

**Cause:** Build step not completed or failed

**Solution:**

1. **Verify build completed:**
```bash
ls -la release/
```

2. **Run build if needed:**
```bash
node scripts/build.js all
```

3. **Retry checksum generation:**
```bash
node scripts/generate-checksums.js
```

**Prevention:**
- Run build before checksums
- Use orchestration script
- Verify build output

---

### Issue: Checksum verification fails

**Symptoms:**
```
✗ Checksum verification failed for PEFT-Studio-Setup-1.0.0.exe
Expected: a1b2c3d4...
Got: e5f6g7h8...
```

**Cause:** File modified after checksum calculation

**Solution:**

1. **Regenerate checksums:**
```bash
node scripts/generate-checksums.js
```

2. **Verify files not corrupted:**
```bash
# Check file sizes
ls -lh release/

# Rebuild if necessary
node scripts/build.js all
node scripts/generate-checksums.js
```

**Prevention:**
- Don't modify files after build
- Generate checksums immediately after build
- Use orchestration script

---

## GitHub Release Issues

### Issue: GitHub API authentication failed

**Symptoms:**
```
Error: Bad credentials
GitHub API returned 401
```

**Cause:** Invalid or expired GitHub token

**Solution:**

1. **Verify token is set:**
```bash
echo $GITHUB_TOKEN
```

2. **Generate new token:**
- Go to GitHub Settings → Developer settings → Personal access tokens
- Generate new token (classic)
- Select `repo` scope
- Copy token

3. **Set new token:**
```bash
export GITHUB_TOKEN="new_token_here"
```

4. **Retry release:**
```bash
node scripts/release-to-github.js
```

**Prevention:**
- Use tokens that don't expire
- Document token generation process
- Store tokens securely

---

### Issue: Release already exists

**Symptoms:**
```
Error: Release v1.0.0 already exists
```

**Cause:** Attempting to create duplicate release

**Solution:**

**Option 1: Delete existing release**
```bash
# Using GitHub CLI
gh release delete v1.0.0 --yes

# Delete tag
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0

# Retry
node scripts/release-to-github.js
```

**Option 2: Bump version**
```bash
# Increment version
npm version patch

# Update CHANGELOG
# Commit changes
git push origin main

# Retry
node scripts/release-to-github.js
```

**Prevention:**
- Check existing releases before creating
- Use unique version numbers
- Follow semantic versioning

---

### Issue: Asset upload fails

**Symptoms:**
```
✗ Failed to upload PEFT-Studio-Setup-1.0.0.exe
Error: Request timeout
```

**Cause:** Network issues or large file size

**Solution:**

1. **Check internet connection:**
```bash
ping github.com
```

2. **Retry (script has automatic retry):**
- Script retries up to 3 times
- Wait for completion

3. **Manual upload if needed:**
- Go to GitHub release page
- Click "Edit release"
- Upload missing assets manually

4. **Check file size:**
```bash
ls -lh release/PEFT-Studio-Setup-1.0.0.exe
```

**Prevention:**
- Use stable internet connection
- Compress installers if too large
- Use CI/CD with reliable network

---

### Issue: GitHub API rate limit exceeded

**Symptoms:**
```
Error: API rate limit exceeded
Limit resets at: 2024-12-04T11:00:00Z
```

**Cause:** Too many API requests

**Solution:**

1. **Check rate limit status:**
```bash
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/rate_limit
```

2. **Wait for reset:**
- Rate limits reset hourly
- Wait until reset time
- Retry release

3. **Use authenticated requests:**
- Ensure GITHUB_TOKEN is set
- Authenticated requests have higher limits (5000/hour)

**Prevention:**
- Use authenticated requests
- Avoid unnecessary API calls
- Space out releases

---

## Platform-Specific Issues

### Windows Issues

#### Issue: PowerShell execution policy error

**Symptoms:**
```
.\scripts\build.ps1 : File cannot be loaded because running scripts is disabled
```

**Solution:**
```powershell
# Set execution policy for current user
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Retry
.\scripts\build.ps1
```

#### Issue: Path too long

**Symptoms:**
```
Error: ENAMETOOLONG: name too long
```

**Solution:**
```powershell
# Enable long paths in Windows
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
  -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force

# Or move project to shorter path
# C:\peft-studio instead of C:\Users\...\very\long\path\peft-studio
```

---

### macOS Issues

#### Issue: Gatekeeper blocks unsigned app

**Symptoms:**
```
"PEFT Studio" cannot be opened because the developer cannot be verified
```

**Solution:**

**For developers:**
```bash
# Remove quarantine attribute
xattr -cr "/Applications/PEFT Studio.app"
```

**For users:**
- Right-click app → Open
- Click "Open" in dialog

**Prevention:**
- Sign app with Apple Developer certificate
- Notarize app with Apple

#### Issue: Missing Xcode Command Line Tools

**Symptoms:**
```
Error: xcode-select: error: tool 'xcodebuild' requires Xcode
```

**Solution:**
```bash
# Install Command Line Tools
xcode-select --install

# Verify installation
xcode-select -p
```

---

### Linux Issues

#### Issue: AppImage not executable

**Symptoms:**
```
bash: ./PEFT-Studio-1.0.0-x64.AppImage: Permission denied
```

**Solution:**
```bash
# Make executable
chmod +x PEFT-Studio-1.0.0-x64.AppImage

# Run
./PEFT-Studio-1.0.0-x64.AppImage
```

#### Issue: Missing FUSE for AppImage

**Symptoms:**
```
dlopen(): error loading libfuse.so.2
AppImages require FUSE to run
```

**Solution:**
```bash
# Ubuntu/Debian
sudo apt install fuse libfuse2

# Fedora
sudo dnf install fuse fuse-libs

# Arch
sudo pacman -S fuse2
```

---

## Network Issues

### Issue: Slow upload speeds

**Symptoms:**
- Asset uploads taking very long
- Timeouts during upload

**Solution:**

1. **Check internet speed:**
```bash
# Test upload speed
speedtest-cli
```

2. **Use wired connection:**
- Ethernet instead of WiFi
- More stable and faster

3. **Upload during off-peak hours:**
- Less network congestion
- Better speeds

4. **Use CI/CD:**
- GitHub Actions has fast network
- More reliable than local

**Prevention:**
- Use CI/CD for releases
- Ensure stable internet connection
- Compress assets if possible

---

### Issue: Connection timeout

**Symptoms:**
```
Error: ETIMEDOUT
Connection timed out
```

**Solution:**

1. **Check firewall:**
```bash
# Ensure GitHub is not blocked
ping github.com
curl https://api.github.com
```

2. **Check proxy settings:**
```bash
# If behind proxy
export HTTP_PROXY="http://proxy.example.com:8080"
export HTTPS_PROXY="http://proxy.example.com:8080"
```

3. **Retry:**
- Script has automatic retry
- Wait and retry manually if needed

**Prevention:**
- Configure proxy if needed
- Whitelist GitHub in firewall
- Use stable network

---

## Recovery Procedures

### Partial Release Failure

If release process fails partway through:

1. **Identify what completed:**
```bash
# Check what exists
ls -la release/
git tag -l
gh release list
```

2. **Resume from failed step:**
```bash
# If build completed but release failed
node scripts/generate-checksums.js
node scripts/release-to-github.js

# If only upload failed
# Edit release on GitHub and upload manually
```

3. **Or start over:**
```bash
# Delete partial release
gh release delete v1.0.0 --yes
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0

# Clean and retry
node scripts/cleanup-repository.js
node scripts/complete-release.js
```

---

### Corrupted Build Artifacts

If build artifacts are corrupted:

1. **Clean build directory:**
```bash
rm -rf release/* dist/* build/*
```

2. **Rebuild:**
```bash
node scripts/build.js all
```

3. **Verify artifacts:**
```bash
# Check file sizes are reasonable
ls -lh release/

# Test installers if possible
```

4. **Regenerate checksums:**
```bash
node scripts/generate-checksums.js
```

---

### Wrong Version Released

If wrong version was released:

1. **Delete release:**
```bash
gh release delete v1.0.0 --yes
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0
```

2. **Fix version:**
```bash
# Edit package.json
# Update CHANGELOG
git add package.json CHANGELOG.md
git commit -m "fix: correct version"
git push origin main
```

3. **Retry release:**
```bash
node scripts/complete-release.js
```

---

## Getting Help

If you're still stuck:

1. **Check documentation:**
   - [Release Process Guide](./release-process.md)
   - [Step-by-Step Guide](./release-step-by-step.md)
   - [Scripts Reference](./release-scripts-reference.md)

2. **Review logs:**
   - Script output
   - GitHub Actions logs
   - Build logs

3. **Search issues:**
   - Check GitHub issues
   - Search for similar problems

4. **Ask for help:**
   - Open GitHub issue
   - Ask in discussions
   - Contact maintainers

---

**Last Updated**: 2024-12-04
