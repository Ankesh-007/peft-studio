# CI/CD Pipeline Setup

This document describes the complete CI/CD pipeline setup for PEFT Studio.

## Overview

The CI/CD pipeline is implemented using GitHub Actions and consists of multiple workflows that handle:

- Continuous Integration (testing, linting, building)
- Automated Testing (unit, integration, property-based, E2E)
- Code Quality Analysis
- Automated Builds (multi-platform)
- Release Automation
- Deployment to App Stores

## Workflows

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
- App store deployment (configurable)
- Release artifact uploads (90-day retention)

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

### 1. Repository Configuration

1. **Enable GitHub Actions:**
   - Go to repository Settings → Actions → General
   - Enable "Allow all actions and reusable workflows"

2. **Configure Branch Protection:**
   - Go to Settings → Branches
   - Add rule for `main` branch:
     - Require status checks to pass before merging
     - Require branches to be up to date before merging
     - Select required checks: CI, Test Frontend, Test Backend, Build Check

### 2. Secrets Configuration

Configure the following secrets in Settings → Secrets and variables → Actions:

#### Required for Code Signing:
```
CSC_LINK: Base64-encoded certificate for Windows/macOS code signing
CSC_KEY_PASSWORD: Password for the certificate
APPLE_ID: Apple ID for macOS notarization
APPLE_ID_PASSWORD: App-specific password for Apple ID
```

#### Optional for App Store Deployment:
```
MS_STORE_CLIENT_ID: Microsoft Store client ID
MS_STORE_CLIENT_SECRET: Microsoft Store client secret
SNAPCRAFT_STORE_CREDENTIALS: Snap Store credentials
```

#### Optional for Notifications:
```
SLACK_WEBHOOK: Slack webhook URL
DISCORD_WEBHOOK: Discord webhook URL
```

### 3. Code Signing Setup

#### Windows Code Signing:
1. Obtain a code signing certificate from a trusted CA
2. Export certificate as PFX file
3. Convert to base64: `base64 -i certificate.pfx -o certificate.txt`
4. Add to `CSC_LINK` secret
5. Add password to `CSC_KEY_PASSWORD` secret

#### macOS Code Signing:
1. Obtain Apple Developer certificate
2. Export certificate from Keychain as P12 file
3. Convert to base64: `base64 -i certificate.p12 -o certificate.txt`
4. Add to `CSC_LINK` secret
5. Add password to `CSC_KEY_PASSWORD` secret
6. Create app-specific password for Apple ID
7. Add Apple ID to `APPLE_ID` secret
8. Add app-specific password to `APPLE_ID_PASSWORD` secret

### 4. Codecov Integration (Optional)

1. Sign up at [codecov.io](https://codecov.io)
2. Add repository to Codecov
3. Copy repository upload token
4. Add as `CODECOV_TOKEN` secret (optional, public repos don't need it)

### 5. Local Testing

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

#### Before Committing:
```bash
npm run lint
npm run type-check
npm run test:run
npm run build
```

#### Creating a Pull Request:
1. Push your branch
2. Create PR on GitHub
3. Wait for CI checks to pass
4. Review code coverage reports
5. Address any failing checks

### For Maintainers

#### Creating a Release:

1. **Update Version:**
   ```bash
   npm version patch  # or minor, or major
   ```

2. **Update Changelog:**
   Edit `CHANGELOG.md` with release notes

3. **Commit and Tag:**
   ```bash
   git add .
   git commit -m "Release v1.0.0"
   git tag v1.0.0
   git push origin main --tags
   ```

4. **Monitor Deployment:**
   - Go to Actions tab
   - Watch Deploy workflow
   - Verify installers are uploaded
   - Test installers on each platform

#### Manual Deployment:

```bash
# Trigger deploy workflow manually
gh workflow run deploy.yml -f environment=production -f version=1.0.0
```

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

### Codecov Dashboard

View coverage reports:
```
https://codecov.io/gh/YOUR_ORG/peft-studio
```

## Troubleshooting

### Common Issues

#### 1. Build Fails on Specific Platform

**Symptoms:** Build succeeds on some platforms but fails on others

**Solutions:**
- Check platform-specific dependencies in package.json
- Verify Node.js and Python versions
- Review platform-specific build scripts
- Test locally on the failing platform

#### 2. Tests Timeout

**Symptoms:** Tests exceed time limit and are cancelled

**Solutions:**
- Increase timeout in workflow file
- Optimize slow tests
- Split tests into smaller jobs
- Use `--bail` flag to stop on first failure

#### 3. Code Signing Fails

**Symptoms:** Installers are not signed or notarization fails

**Solutions:**
- Verify certificate is valid and not expired
- Check CSC_LINK and CSC_KEY_PASSWORD secrets
- Ensure Apple ID credentials are correct
- Review code signing logs in workflow

#### 4. Coverage Upload Fails

**Symptoms:** Coverage reports don't appear on Codecov

**Solutions:**
- Verify CODECOV_TOKEN is set (if private repo)
- Check coverage file paths in workflow
- Ensure coverage files are generated
- Review Codecov configuration

#### 5. Deployment Fails

**Symptoms:** Release creation or asset upload fails

**Solutions:**
- Verify GITHUB_TOKEN has correct permissions
- Check if release already exists
- Ensure tag format matches `v*.*.*`
- Review deployment logs

### Getting Help

1. Check workflow logs in GitHub Actions
2. Review this documentation
3. Search existing issues
4. Open new issue with:
   - Workflow run URL
   - Error messages
   - Steps to reproduce

## Best Practices

### Commit Messages

Follow conventional commits:
```
feat: add new feature
fix: fix bug
docs: update documentation
test: add tests
chore: update dependencies
ci: update CI configuration
```

### Branch Strategy

- `main`: Production-ready code
- `develop`: Development branch
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

## Performance Optimization

### Workflow Optimization

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
   - Clean up old artifacts

## Security

### Best Practices

1. **Secrets Management:**
   - Never commit secrets to repository
   - Use GitHub Secrets for sensitive data
   - Rotate secrets regularly
   - Use environment-specific secrets

2. **Dependency Security:**
   - Run security scans on every PR
   - Update dependencies regularly
   - Review security advisories
   - Use dependabot for automated updates

3. **Code Signing:**
   - Sign all releases
   - Use trusted certificates
   - Verify signatures after build
   - Store certificates securely

4. **Access Control:**
   - Limit who can trigger workflows
   - Require approvals for deployments
   - Use branch protection rules
   - Review workflow permissions

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

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Electron Builder Documentation](https://www.electron.build/)
- [Code Signing Guide](https://www.electron.build/code-signing)
- [Codecov Documentation](https://docs.codecov.com/)
- [Act - Local Testing](https://github.com/nektos/act)

## Support

For questions or issues with the CI/CD pipeline:

1. Check this documentation
2. Review workflow logs
3. Search existing issues
4. Open a new issue with details
5. Contact maintainers

---

**Last Updated:** December 2024
**Maintained By:** PEFT Studio Team
