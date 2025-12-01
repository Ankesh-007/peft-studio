# CI/CD Quick Start Guide

Get started with the PEFT Studio CI/CD pipeline in 5 minutes.

## Prerequisites

- GitHub repository with admin access
- Node.js 18+ and Python 3.10+ installed locally
- Git configured on your machine

## Quick Setup (5 Steps)

### 1. Enable GitHub Actions

1. Go to your repository on GitHub
2. Click **Settings** → **Actions** → **General**
3. Select **Allow all actions and reusable workflows**
4. Click **Save**

### 2. Configure Branch Protection (Optional but Recommended)

1. Go to **Settings** → **Branches**
2. Click **Add rule** for `main` branch
3. Enable:
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
4. Select required checks:
   - `lint`
   - `test-frontend`
   - `test-backend`
   - `build-check`
5. Click **Create**

### 3. Add Secrets (For Releases Only)

Only needed if you plan to create signed releases:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add these secrets (see [Code Signing Setup](#code-signing-setup) for details):
   - `CSC_LINK` (optional)
   - `CSC_KEY_PASSWORD` (optional)
   - `APPLE_ID` (optional)
   - `APPLE_ID_PASSWORD` (optional)

### 4. Test the Pipeline

Push a commit to trigger the CI workflow:

```bash
git add .
git commit -m "test: trigger CI pipeline"
git push origin main
```

### 5. Monitor Results

1. Go to **Actions** tab in your repository
2. Watch the CI workflow run
3. Check that all jobs pass ✅

## What Happens Automatically

### On Every Push/PR
- ✅ Code linting (ESLint, TypeScript)
- ✅ Frontend tests with coverage
- ✅ Backend tests with coverage
- ✅ Build verification on all platforms
- ✅ Security scanning

### Daily (2 AM UTC)
- ✅ Comprehensive test suite
- ✅ Extended property-based tests
- ✅ Nightly builds

### Weekly (Monday 9 AM UTC)
- ✅ Code quality analysis
- ✅ Dependency updates (Dependabot)

### On Git Tags (v*.*.*)
- ✅ Automated release creation
- ✅ Multi-platform installers
- ✅ GitHub release with assets

## Common Workflows

### Creating a Pull Request

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes and commit
git add .
git commit -m "feat: add new feature"

# Push and create PR
git push origin feature/my-feature
```

Then:
1. Go to GitHub and create Pull Request
2. Wait for CI checks to pass ✅
3. Request review
4. Merge when approved

### Creating a Release

```bash
# Update version
npm version patch  # or minor, or major

# Commit and tag
git add .
git commit -m "chore: release v1.0.1"
git tag v1.0.1

# Push with tags
git push origin main --tags
```

The deploy workflow will automatically:
1. Create GitHub release
2. Build installers for all platforms
3. Upload installers to release
4. Generate checksums

### Running Tests Locally

Before pushing, run tests locally:

```bash
# Run all CI checks
npm run ci

# Or run individually
npm run lint
npm run type-check
npm run test:run
npm run build
```

## Troubleshooting

### CI Fails on First Run

**Problem:** CI workflow fails with "command not found" errors

**Solution:** Ensure all dependencies are in package.json:
```bash
npm install
git add package-lock.json
git commit -m "chore: update dependencies"
git push
```

### Tests Fail Locally But Pass in CI

**Problem:** Tests behave differently locally vs CI

**Solution:** Check Node.js and Python versions match CI:
```bash
node --version  # Should be 18.x
python --version  # Should be 3.10.x
```

### Build Fails on Specific Platform

**Problem:** Build succeeds on Linux but fails on Windows/macOS

**Solution:** Check platform-specific code and dependencies. Test locally on that platform if possible.

### Coverage Upload Fails

**Problem:** Codecov upload fails in CI

**Solution:** For private repos, add `CODECOV_TOKEN` secret. For public repos, this is optional.

## Code Signing Setup

### Windows Code Signing

1. Obtain code signing certificate from trusted CA (e.g., DigiCert, Sectigo)
2. Export as PFX file
3. Convert to base64:
   ```bash
   # macOS/Linux
   base64 -i certificate.pfx -o certificate.txt
   
   # Windows PowerShell
   [Convert]::ToBase64String([IO.File]::ReadAllBytes("certificate.pfx")) | Out-File certificate.txt
   ```
4. Add `certificate.txt` content to `CSC_LINK` secret
5. Add certificate password to `CSC_KEY_PASSWORD` secret

### macOS Code Signing

1. Obtain Apple Developer certificate
2. Export from Keychain as P12 file
3. Convert to base64:
   ```bash
   base64 -i certificate.p12 -o certificate.txt
   ```
4. Add `certificate.txt` content to `CSC_LINK` secret
5. Add certificate password to `CSC_KEY_PASSWORD` secret
6. Create app-specific password at appleid.apple.com
7. Add Apple ID to `APPLE_ID` secret
8. Add app-specific password to `APPLE_ID_PASSWORD` secret

## Status Badges

Add these to your README.md:

```markdown
![CI](https://github.com/YOUR_ORG/peft-studio/workflows/CI/badge.svg)
![Tests](https://github.com/YOUR_ORG/peft-studio/workflows/Comprehensive%20Testing/badge.svg)
![Build](https://github.com/YOUR_ORG/peft-studio/workflows/Build/badge.svg)
![Code Quality](https://github.com/YOUR_ORG/peft-studio/workflows/Code%20Quality/badge.svg)
```

Replace `YOUR_ORG` with your GitHub username or organization.

## Next Steps

1. ✅ **Test the pipeline** - Push a commit and verify CI passes
2. ✅ **Add status badges** - Update README.md with badges
3. ✅ **Configure branch protection** - Require CI checks before merge
4. ✅ **Set up code signing** - Add secrets for signed releases
5. ✅ **Create first release** - Tag and push to test deployment

## Getting Help

- 📖 **Full Documentation:** See `CI_CD_SETUP.md`
- 🔧 **Workflow Details:** See `.github/workflows/README.md`
- 🐛 **Issues:** Check workflow logs in Actions tab
- 💬 **Questions:** Open an issue or discussion

## Useful Commands

```bash
# Run CI checks locally
npm run ci

# Run tests with coverage
npm run test:coverage

# Check code formatting
npm run format:check

# Fix code formatting
npm run format

# Build for production
npm run build

# Package for all platforms
npm run package:all

# Verify build configuration
npm run verify:build
```

## Workflow Files

All workflow files are in `.github/workflows/`:

- `ci.yml` - Main CI workflow (runs on every push/PR)
- `test.yml` - Comprehensive testing
- `build.yml` - Build automation
- `deploy.yml` - Release automation
- `code-quality.yml` - Code quality checks
- `nightly.yml` - Nightly builds

## Resources

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Electron Builder Docs](https://www.electron.build/)
- [Code Signing Guide](https://www.electron.build/code-signing)

---

**Need more details?** See the complete [CI/CD Setup Guide](CI_CD_SETUP.md)
