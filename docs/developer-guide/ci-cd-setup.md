# CI/CD Pipeline Setup

This document provides comprehensive guidance for setting up, using, and maintaining the CI/CD pipeline for PEFT Studio.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Workflows](#workflows)
- [Setup Instructions](#setup-instructions)
- [Usage](#usage)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)
- [Security](#security)
- [Resources](#resources)

## Overview

The CI/CD pipeline is implemented using GitHub Actions and provides automated testing, building, code quality checks, and deployment automation across multiple platforms (Linux, Windows, macOS).

### Key Features

- **Automated Testing** - Unit, integration, property-based, and E2E tests
- **Code Quality** - Linting, formatting, type checking, and security scanning
- **Build Automation** - Multi-platform builds with parallel execution
- **Deployment Automation** - Automated releases with installer generation
- **Dependency Management** - Automated updates with Dependabot

### What Happens Automatically

**On Every Push/PR:**
- ✅ Code linting (ESLint, TypeScript, flake8, black, mypy, pylint)
- ✅ Frontend and backend tests with coverage
- ✅ Build verification on all platforms
- ✅ Security scanning (npm audit, pip audit)

**Daily (2 AM UTC):**
- ✅ Comprehensive test suite with extended timeouts
- ✅ Property-based tests with Hypothesis
- ✅ Nightly builds on all platforms

**Weekly (Monday 9 AM UTC):**
- ✅ Code quality analysis and metrics
- ✅ Dependency updates via Dependabot

**On Git Tags (v*.*.*):**
- ✅ Automated release creation
- ✅ Multi-platform installer generation
- ✅ GitHub release with checksums

## Quick Start

Get started with the CI/CD pipeline in 5 minutes.

### Prerequisites

- GitHub repository with admin access
- Node.js 18+ and Python 3.10+ installed locally
- Git configured on your machine

### Setup Steps

#### 1. Enable GitHub Actions

1. Go to your repository on GitHub
2. Click **Settings** → **Actions** → **General**
3. Select **Allow all actions and reusable workflows**
4. Click **Save**

#### 2. Configure Branch Protection (Recommended)

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

#### 3. Add Secrets (For Releases Only)

Only needed if you plan to create signed releases. See [Secrets Configuration](#secrets-configuration) for details.

#### 4. Test the Pipeline

Push a commit to trigger the CI workflow:

```bash
git add .
git commit -m "test: trigger CI pipeline"
git push origin main
```

#### 5. Monitor Results

1. Go to **Actions** tab in your repository
2. Watch the CI workflow run
3. Check that all jobs pass ✅

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

## Workflows

The CI/CD pipeline consists of multiple workflows that handle different aspects of the development lifecycle.

### 1. CI Workflow (`.github/workflows/ci.yml`)

**Purpose:** Main continuous integration workflow that runs on every push and pull request.

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Manual dispatch

**Jobs:**
- **Lint:** ESLint and TypeScript checks
- **Test Frontend:** Frontend unit tests with coverage
- **Test Backend:** Backend unit tests with coverage
- **Build Check:** Verify builds on all platforms (Linux, Windows, macOS)
- **Security Scan:** npm audit and pip audit
- **All Checks Passed:** Summary job that ensures all checks passed

**Key Features:**
- Parallel execution for faster feedback
- Code coverage upload to Codecov
- Cross-platform build verification
- Security vulnerability scanning

**Typical Execution Time:** 5-10 minutes

### 2. Test Workflow (`.github/workflows/test.yml`)

**Purpose:** Comprehensive testing suite with multiple test types.

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests
- Daily schedule (2 AM UTC)
- Manual dispatch

**Jobs:**
- **Unit Tests:** Cross-platform and cross-version testing (Node 18/20, Python 3.9/3.10/3.11)
- **Property-Based Tests:** Hypothesis-based testing with 30-minute timeout
- **Integration Tests:** API and service integration tests
- **E2E Tests:** End-to-end Playwright tests (when implemented)
- **Performance Tests:** Benchmark and performance tests
- **Test Summary:** Aggregated test results

**Key Features:**
- Matrix testing across multiple OS and language versions
- Property-based testing with Hypothesis
- Performance benchmarking
- Test result artifacts

**Typical Execution Time:** 15-30 minutes

### 3. Build Workflow (`.github/workflows/build.yml`)

**Purpose:** Build artifacts for all platforms.

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests
- Manual dispatch with version input

**Jobs:**
- **Build Frontend:** Compile and bundle frontend
- **Build Backend:** Prepare backend for packaging
- **Build Electron:** Create Electron apps for Linux, Windows, and macOS
- **Verify Builds:** Ensure all builds completed successfully

**Key Features:**
- Parallel builds for all platforms
- Build artifact uploads (7-day retention)
- Build verification checks
- Frontend and backend separation

**Typical Execution Time:** 10-20 minutes

### 4. Deploy Workflow (`.github/workflows/deploy.yml`)

**Purpose:** Automated release and deployment.

**Triggers:**
- Git tags matching `v*.*.*` pattern
- Manual dispatch with environment and version inputs

**Jobs:**
- **Prepare Release:** Create GitHub release with changelog
- **Build and Deploy:** Build and upload installers for all platforms
- **Deploy to Stores:** Deploy to Microsoft Store, Mac App Store, Snap Store (optional)
- **Notify Deployment:** Send deployment notifications

**Key Features:**
- Automatic changelog generation
- Multi-platform installer creation
- Checksum generation
- App store deployment support (configurable)
- Release artifact uploads (90-day retention)

**Typical Execution Time:** 30-45 minutes

### 5. Code Quality Workflow (`.github/workflows/code-quality.yml`)

**Purpose:** Code quality analysis and metrics.

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests
- Weekly schedule (Monday 9 AM UTC)
- Manual dispatch

**Jobs:**
- **Lint Frontend:** ESLint, Prettier, TypeScript checks
- **Lint Backend:** flake8, black, mypy, pylint
- **Code Coverage:** Generate and upload coverage reports
- **Dependency Check:** Check for outdated/vulnerable packages
- **Code Metrics:** Bundle size and lines of code analysis
- **Quality Summary:** Aggregated quality metrics

**Key Features:**
- Multiple linting tools
- Code coverage tracking
- Dependency vulnerability scanning
- Bundle size analysis
- Weekly automated runs

**Typical Execution Time:** 10-15 minutes

### 6. Nightly Build Workflow (`.github/workflows/nightly.yml`)

**Purpose:** Nightly builds and extended testing.

**Triggers:**
- Daily schedule (2 AM UTC)
- Manual dispatch

**Jobs:**
- **Nightly Build:** Build on all platforms
- **Nightly Tests:** Extended property-based tests, stress tests, benchmarks
- **Nightly Report:** Generate and send reports

**Key Features:**
- Extended test timeouts (60 minutes for property tests)
- Stress testing
- Performance benchmarking
- Failure notifications
- 7-day artifact retention

**Typical Execution Time:** 45-60 minutes

### 7. Legacy Workflows

**Release Workflow (`.github/workflows/release.yml`):**
- Legacy release workflow kept for compatibility
- Triggered by git tags
- Creates releases and uploads installers

**Build Installers Workflow (`.github/workflows/build-installers.yml`):**
- Legacy installer build workflow
- Triggered by git tags or manual dispatch
- Creates installers and checksums

## Setup Instructions

### Repository Configuration

#### Enable GitHub Actions

1. Go to repository Settings → Actions → General
2. Enable "Allow all actions and reusable workflows"
3. Click Save

#### Configure Branch Protection

1. Go to Settings → Branches
2. Add rule for `main` branch:
   - Require status checks to pass before merging
   - Require branches to be up to date before merging
   - Select required checks: CI, Test Frontend, Test Backend, Build Check
3. Click Create

### Secrets Configuration

Configure the following secrets in Settings → Secrets and variables → Actions:

#### Required for Code Signing

```
CSC_LINK: Base64-encoded certificate for Windows/macOS code signing
CSC_KEY_PASSWORD: Password for the certificate
APPLE_ID: Apple ID for macOS notarization
APPLE_ID_PASSWORD: App-specific password for Apple ID
```

#### Optional for App Store Deployment

```
MS_STORE_CLIENT_ID: Microsoft Store client ID
MS_STORE_CLIENT_SECRET: Microsoft Store client secret
SNAPCRAFT_STORE_CREDENTIALS: Snap Store credentials
```

#### Optional for Notifications

```
SLACK_WEBHOOK: Slack webhook URL
DISCORD_WEBHOOK: Discord webhook URL
```

#### Optional for Coverage

```
CODECOV_TOKEN: Codecov upload token (for private repos)
```

### Code Signing Setup

#### Windows Code Signing

1. Obtain a code signing certificate from a trusted CA (e.g., DigiCert, Sectigo)
2. Export certificate as PFX file
3. Convert to base64:
   ```bash
   # macOS/Linux
   base64 -i certificate.pfx -o certificate.txt
   
   # Windows PowerShell
   [Convert]::ToBase64String([IO.File]::ReadAllBytes("certificate.pfx")) | Out-File certificate.txt
   ```
4. Add `certificate.txt` content to `CSC_LINK` secret
5. Add certificate password to `CSC_KEY_PASSWORD` secret

#### macOS Code Signing

1. Obtain Apple Developer certificate
2. Export certificate from Keychain as P12 file
3. Convert to base64:
   ```bash
   base64 -i certificate.p12 -o certificate.txt
   ```
4. Add `certificate.txt` content to `CSC_LINK` secret
5. Add certificate password to `CSC_KEY_PASSWORD` secret
6. Create app-specific password at appleid.apple.com
7. Add Apple ID to `APPLE_ID` secret
8. Add app-specific password to `APPLE_ID_PASSWORD` secret

### Codecov Integration (Optional)

1. Sign up at [codecov.io](https://codecov.io)
2. Add repository to Codecov
3. Copy repository upload token
4. Add as `CODECOV_TOKEN` secret (optional for public repos)

### Local Testing with Act

Install [act](https://github.com/nektos/act) for local workflow testing:

```bash
# macOS
brew install act

# Windows
choco install act-cli

# Linux
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
```

Test workflows locally:
```bash
# Test CI workflow
act push

# Test specific job
act -j test-frontend

# Test with secrets
act -s GITHUB_TOKEN=your_token
```

## Usage

### For Developers

#### Before Committing

Run these checks locally before pushing:

```bash
npm run lint
npm run type-check
npm run test:run
npm run build
```

Or run all checks at once:

```bash
npm run ci
```

#### Creating a Pull Request

1. Create feature branch:
   ```bash
   git checkout -b feature/my-feature
   ```

2. Make changes and commit:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

3. Push and create PR:
   ```bash
   git push origin feature/my-feature
   ```

4. On GitHub:
   - Create Pull Request
   - Wait for CI checks to pass ✅
   - Review code coverage reports
   - Address any failing checks
   - Request review

#### Commit Message Format

Follow conventional commits:
```
feat: add new feature
fix: fix bug
docs: update documentation
test: add tests
chore: update dependencies
ci: update CI configuration
refactor: refactor code
perf: improve performance
style: format code
```

### For Maintainers

#### Creating a Release

1. **Update Version:**
   ```bash
   npm version patch  # or minor, or major
   ```

2. **Update Changelog:**
   Edit `CHANGELOG.md` with release notes

3. **Commit and Tag:**
   ```bash
   git add .
   git commit -m "chore: release v1.0.0"
   git tag v1.0.0
   git push origin main --tags
   ```

4. **Monitor Deployment:**
   - Go to Actions tab
   - Watch Deploy workflow
   - Verify installers are uploaded
   - Test installers on each platform

#### Manual Deployment

Trigger deploy workflow manually:

```bash
gh workflow run deploy.yml -f environment=production -f version=1.0.0
```

Or use the GitHub Actions UI:
1. Go to Actions tab
2. Select Deploy workflow
3. Click "Run workflow"
4. Enter environment and version
5. Click "Run workflow"

## Monitoring

### GitHub Actions Dashboard

View all workflow runs:
```
https://github.com/YOUR_ORG/peft-studio/actions
```

### Status Badges

Add to README.md:

```markdown
![CI](https://github.com/YOUR_ORG/peft-studio/workflows/CI/badge.svg)
![Tests](https://github.com/YOUR_ORG/peft-studio/workflows/Comprehensive%20Testing/badge.svg)
![Build](https://github.com/YOUR_ORG/peft-studio/workflows/Build/badge.svg)
![Code Quality](https://github.com/YOUR_ORG/peft-studio/workflows/Code%20Quality/badge.svg)
```

Replace `YOUR_ORG` with your GitHub username or organization.

### Codecov Dashboard

View coverage reports:
```
https://codecov.io/gh/YOUR_ORG/peft-studio
```

### Workflow Notifications

Configure notifications for workflow failures:
1. Go to Settings → Notifications
2. Enable "Actions" notifications
3. Choose notification method (email, web, mobile)

## Troubleshooting

### Common Issues

#### 1. Build Fails on Specific Platform

**Symptoms:** Build succeeds on some platforms but fails on others

**Solutions:**
- Check platform-specific dependencies in package.json
- Verify Node.js and Python versions match CI requirements
- Review platform-specific build scripts
- Test locally on the failing platform
- Check for platform-specific path issues (Windows vs Unix)

#### 2. Tests Timeout

**Symptoms:** Tests exceed time limit and are cancelled

**Solutions:**
- Increase timeout in workflow file
- Optimize slow tests
- Split tests into smaller jobs
- Use `--bail` flag to stop on first failure
- Check for infinite loops or hanging operations

#### 3. Code Signing Fails

**Symptoms:** Installers are not signed or notarization fails

**Solutions:**
- Verify certificate is valid and not expired
- Check CSC_LINK and CSC_KEY_PASSWORD secrets are correct
- Ensure Apple ID credentials are correct
- Review code signing logs in workflow
- Verify certificate matches the platform (Windows/macOS)

#### 4. Coverage Upload Fails

**Symptoms:** Coverage reports don't appear on Codecov

**Solutions:**
- Verify CODECOV_TOKEN is set (required for private repos)
- Check coverage file paths in workflow
- Ensure coverage files are generated before upload
- Review Codecov configuration in codecov.yml
- Check Codecov service status

#### 5. Deployment Fails

**Symptoms:** Release creation or asset upload fails

**Solutions:**
- Verify GITHUB_TOKEN has correct permissions
- Check if release already exists for the tag
- Ensure tag format matches `v*.*.*` pattern
- Review deployment logs for specific errors
- Verify all build artifacts were created successfully

#### 6. CI Fails on First Run

**Symptoms:** CI workflow fails with "command not found" errors

**Solutions:**
- Ensure all dependencies are in package.json
- Run `npm install` and commit package-lock.json
- Verify all required scripts are defined in package.json
- Check that all workflow files reference correct script names

#### 7. Tests Fail Locally But Pass in CI

**Symptoms:** Tests behave differently locally vs CI

**Solutions:**
- Check Node.js and Python versions match CI:
  ```bash
  node --version  # Should be 18.x
  python --version  # Should be 3.10.x
  ```
- Clear local caches and node_modules
- Check for environment-specific code
- Review test isolation and cleanup

### Getting Help

1. Check workflow logs in GitHub Actions
2. Review this documentation
3. Search existing issues on GitHub
4. Open new issue with:
   - Workflow run URL
   - Error messages
   - Steps to reproduce
   - Environment details

## Best Practices

### Development Workflow

1. **Create Feature Branch:**
   ```bash
   git checkout -b feature/feature-name
   ```

2. **Make Small, Focused Commits:**
   - One logical change per commit
   - Use conventional commit messages
   - Write descriptive commit messages

3. **Run Tests Locally:**
   ```bash
   npm run ci
   ```

4. **Push and Create PR:**
   - Push to feature branch
   - Create PR with clear description
   - Link related issues
   - Wait for CI checks

5. **Address Feedback:**
   - Fix any failing checks
   - Respond to review comments
   - Update PR as needed

6. **Merge:**
   - Ensure all checks pass
   - Get required approvals
   - Merge using squash or rebase

### Branch Strategy

- `main`: Production-ready code
- `develop`: Development branch (optional)
- `feature/*`: Feature branches
- `fix/*`: Bug fix branches
- `release/*`: Release preparation branches

### Testing Strategy

1. Write tests before pushing
2. Ensure all tests pass locally
3. Maintain >80% code coverage
4. Add property-based tests for complex logic
5. Write integration tests for APIs
6. Add E2E tests for critical flows

### Release Strategy

1. Use semantic versioning (MAJOR.MINOR.PATCH)
2. Create release notes in CHANGELOG.md
3. Tag releases with `v` prefix (e.g., `v1.0.0`)
4. Test installers before announcing
5. Monitor for issues after release
6. Have rollback plan ready

### Performance Optimization

#### Workflow Optimization

1. **Use Caching:**
   - npm cache for Node.js dependencies
   - pip cache for Python dependencies
   - Build cache for faster rebuilds

2. **Parallel Execution:**
   - Run independent jobs in parallel
   - Use matrix strategy for multi-platform builds
   - Split large test suites

3. **Conditional Execution:**
   - Skip unnecessary jobs on draft PRs
   - Use `if` conditions to skip jobs
   - Use `continue-on-error` for non-critical checks

4. **Artifact Management:**
   - Set appropriate retention periods
   - Compress large artifacts
   - Clean up old artifacts regularly

## Security

### Best Practices

#### 1. Secrets Management

- Never commit secrets to repository
- Use GitHub Secrets for sensitive data
- Rotate secrets regularly
- Use environment-specific secrets
- Limit secret access to necessary workflows

#### 2. Dependency Security

- Run security scans on every PR
- Update dependencies regularly
- Review security advisories
- Use Dependabot for automated updates
- Pin dependency versions for reproducibility

#### 3. Code Signing

- Sign all releases
- Use trusted certificates
- Verify signatures after build
- Store certificates securely
- Rotate certificates before expiration

#### 4. Access Control

- Limit who can trigger workflows
- Require approvals for deployments
- Use branch protection rules
- Review workflow permissions
- Use CODEOWNERS file

#### 5. Workflow Security

- Use specific action versions (not @main)
- Review third-party actions before use
- Limit workflow permissions
- Use environment protection rules
- Audit workflow changes

## Resources

### Documentation

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Electron Builder Documentation](https://www.electron.build/)
- [Code Signing Guide](https://www.electron.build/code-signing)
- [Codecov Documentation](https://docs.codecov.com/)
- [Act - Local Testing](https://github.com/nektos/act)

### Related Documentation

- [Workflow Details](../../.github/workflows/README.md)
- [Testing Guide](testing.md)
- [Build and Installers](build-and-installers.md)
- [Security Best Practices](security.md)

### Useful Commands

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

## Future Improvements

- [ ] Add Playwright E2E tests
- [ ] Implement automatic dependency updates with Dependabot
- [ ] Add performance regression testing
- [ ] Integrate with external monitoring (Sentry, DataDog)
- [ ] Add automatic changelog generation
- [ ] Implement canary deployments
- [ ] Add smoke tests for releases
- [ ] Integrate with issue tracking
- [ ] Add deployment rollback capability
- [ ] Implement blue-green deployments

## Support

For questions or issues with the CI/CD pipeline:

1. Check this documentation
2. Review workflow logs in GitHub Actions
3. Search existing issues on GitHub
4. Open a new issue with:
   - Workflow run URL
   - Error messages
   - Steps to reproduce
   - Environment details
5. Contact maintainers

---

**Last Updated:** December 2024  
**Maintained By:** PEFT Studio Team
