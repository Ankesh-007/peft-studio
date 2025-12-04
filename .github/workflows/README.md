# GitHub Actions CI/CD Workflows

This directory contains all GitHub Actions workflows for the PEFT Studio project.

## Workflows Overview

### 1. CI Workflow (`ci.yml`)

**Trigger:** Push to main/develop, Pull Requests
**Purpose:** Continuous Integration - runs on every code change

**Jobs:**
- **Lint:** Code style and formatting checks
- **Test Frontend:** Frontend unit tests with coverage
- **Test Backend:** Backend unit tests with coverage
- **Build Check:** Verify builds work on all platforms
- **Security Scan:** npm audit and pip audit

**Usage:**
```bash
# Triggered automatically on push/PR
# Or manually via GitHub Actions UI
```

### 2. Test Workflow (`test.yml`)

**Trigger:** Push, Pull Requests, Daily schedule, Manual
**Purpose:** Comprehensive testing suite

**Jobs:**
- **Unit Tests:** Cross-platform and cross-version testing
- **Property-Based Tests:** Hypothesis-based testing
- **Integration Tests:** API and service integration tests
- **E2E Tests:** End-to-end Playwright tests
- **Performance Tests:** Benchmark and performance tests

**Usage:**
```bash
# Runs automatically on push/PR
# Scheduled daily at 2 AM UTC
# Manual trigger via GitHub Actions UI
```

### 3. Build Workflow (`build.yml`)

**Trigger:** Push, Pull Requests, Manual
**Purpose:** Build artifacts for all platforms

**Jobs:**
- **Build Frontend:** Compile and bundle frontend
- **Build Backend:** Prepare backend for packaging
- **Build Electron:** Create Electron apps for all platforms
- **Verify Builds:** Ensure all builds completed successfully

**Usage:**
```bash
# Triggered automatically on push/PR
# Manual trigger with custom version:
gh workflow run build.yml -f version=1.2.3
```

### 4. Deploy Workflow (`deploy.yml`)

**Trigger:** Git tags (v*.*.*), Manual
**Purpose:** Release and deployment automation

**Jobs:**
- **Prepare Release:** Create GitHub release with changelog
- **Build and Deploy:** Build and upload installers
- **Deploy to Stores:** Deploy to app stores (optional)
- **Notify Deployment:** Send deployment notifications

**Usage:**
```bash
# Create and push a tag to trigger:
git tag v1.0.0
git push origin v1.0.0

# Or manual trigger:
gh workflow run deploy.yml -f environment=production -f version=1.0.0
```

### 5. Code Quality Workflow (`code-quality.yml`)

**Trigger:** Push, Pull Requests, Weekly schedule, Manual
**Purpose:** Code quality and metrics analysis

**Jobs:**
- **Lint Frontend:** ESLint, Prettier, TypeScript checks
- **Lint Backend:** flake8, black, mypy, pylint
- **Code Coverage:** Generate and upload coverage reports
- **Dependency Check:** Check for outdated/vulnerable packages
- **Code Metrics:** Bundle size and LOC analysis

**Usage:**
```bash
# Runs automatically on push/PR
# Scheduled weekly on Monday at 9 AM UTC
```

### 6. Nightly Build Workflow (`nightly.yml`)

**Trigger:** Daily schedule, Manual
**Purpose:** Nightly builds and extended testing

**Jobs:**
- **Nightly Build:** Build on all platforms
- **Nightly Tests:** Extended property-based and stress tests
- **Nightly Report:** Generate and send reports

**Usage:**
```bash
# Runs automatically every night at 2 AM UTC
# Manual trigger via GitHub Actions UI
```

### 7. Release Workflow (`release.yml`)

**Trigger:** Git tags (v*.*.*)
**Purpose:** Legacy release workflow (kept for compatibility)

**Jobs:**
- **Create Release:** Create GitHub release
- **Build and Upload:** Build and upload installers

### 8. Build Installers Workflow (`build-installers.yml`)

**Trigger:** Git tags, Manual
**Purpose:** Build installer packages

**Jobs:**
- **Build:** Create installers for all platforms
- **Create Checksums:** Generate SHA256 checksums

## Secrets Required

Configure these secrets in GitHub repository settings:

### Code Signing
- `CSC_LINK`: Certificate for Windows/macOS code signing
- `CSC_KEY_PASSWORD`: Password for certificate
- `APPLE_ID`: Apple ID for macOS notarization
- `APPLE_ID_PASSWORD`: App-specific password for Apple ID

### App Store Deployment (Optional)
- `MS_STORE_CLIENT_ID`: Microsoft Store client ID
- `MS_STORE_CLIENT_SECRET`: Microsoft Store client secret
- `SNAPCRAFT_STORE_CREDENTIALS`: Snap Store credentials

### Notifications (Optional)
- `SLACK_WEBHOOK`: Slack webhook URL for notifications
- `DISCORD_WEBHOOK`: Discord webhook URL for notifications

## Environment Variables

### Build Configuration
- `NODE_ENV`: Set to 'production' for production builds
- `VERSION`: Version number for builds
- `PLATFORM`: Target platform (linux, windows, mac)

### Testing Configuration
- `CI`: Set to 'true' in CI environment
- `HYPOTHESIS_PROFILE`: Hypothesis testing profile (ci, dev)

## Workflow Dependencies

```
ci.yml
├── Runs on every push/PR
└── Required for merge

test.yml
├── Comprehensive testing
└── Runs daily + on push/PR

build.yml
├── Depends on: ci.yml passing
└── Creates build artifacts

deploy.yml
├── Depends on: test.yml passing
├── Depends on: build.yml passing
└── Creates releases

code-quality.yml
├── Independent quality checks
└── Runs weekly + on push/PR

nightly.yml
├── Independent nightly builds
└── Runs daily at 2 AM UTC
```

## Best Practices

### For Contributors

1. **Before Pushing:**
   ```bash
   npm run lint
   npm run test -- --run
   npm run build
   ```

2. **For Pull Requests:**
   - Ensure CI workflow passes
   - Check code coverage reports
   - Review build artifacts

3. **For Releases:**
   - Update version in package.json
   - Update CHANGELOG.md
   - Create and push tag
   - Monitor deploy workflow

### For Maintainers

1. **Regular Maintenance:**
   - Review nightly build reports
   - Update dependencies weekly
   - Monitor code quality metrics
   - Review security scan results

2. **Release Process:**
   - Verify all tests pass
   - Update documentation
   - Create release tag
   - Monitor deployment
   - Verify installers work

3. **Troubleshooting:**
   - Check workflow logs in Actions tab
   - Review artifact uploads
   - Verify secrets are configured
   - Test locally before pushing

## Local Testing

Test workflows locally using [act](https://github.com/nektos/act):

```bash
# Install act
brew install act  # macOS
# or
choco install act-cli  # Windows

# Run CI workflow
act push

# Run specific job
act -j test-frontend

# Run with secrets
act -s GITHUB_TOKEN=your_token
```

## Monitoring

### GitHub Actions Dashboard
- View all workflow runs: `https://github.com/Ankesh-007/peft-studio/actions`
- Monitor build status
- Download artifacts
- Review logs

### Status Badges

Add to README.md:

```markdown
![CI](https://github.com/Ankesh-007/peft-studio/workflows/CI/badge.svg)
![Tests](https://github.com/Ankesh-007/peft-studio/workflows/Comprehensive%20Testing/badge.svg)
![Build](https://github.com/Ankesh-007/peft-studio/workflows/Build/badge.svg)
```

## Troubleshooting

### Common Issues

1. **Build Fails on Specific Platform:**
   - Check platform-specific dependencies
   - Verify Node/Python versions
   - Review platform-specific scripts

2. **Tests Timeout:**
   - Increase timeout in workflow
   - Optimize slow tests
   - Split into smaller jobs

3. **Deployment Fails:**
   - Verify secrets are configured
   - Check certificate validity
   - Review deployment logs

4. **Coverage Upload Fails:**
   - Verify Codecov token
   - Check coverage file paths
   - Review Codecov configuration

### Getting Help

- Check workflow logs in GitHub Actions
- Review this documentation
- Open an issue with workflow run URL
- Contact maintainers

## Future Improvements

- [ ] Add Playwright E2E tests
- [ ] Implement automatic dependency updates
- [ ] Add performance regression testing
- [ ] Integrate with external monitoring
- [ ] Add automatic changelog generation
- [ ] Implement canary deployments
- [ ] Add smoke tests for releases
- [ ] Integrate with issue tracking
