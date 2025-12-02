# PEFT Studio Security and Verification Scripts

This directory contains scripts for security scanning and publish verification before making the repository public.

## Scripts

### 1. Security Scan Scripts

Scans the repository for sensitive data, credentials, and security issues.

#### Windows (PowerShell)
```powershell
.\scripts\security-scan.ps1
```

With verbose output:
```powershell
.\scripts\security-scan.ps1 -Verbose
```

#### Unix/Linux/macOS (Bash)
```bash
bash scripts/security-scan.sh
```

With verbose output:
```bash
bash scripts/security-scan.sh --verbose
```

#### What it checks:
- API keys, tokens, and credentials
- AWS credentials
- Private keys (RSA, DSA, EC, OpenSSH)
- Passwords in code
- Database connection URLs
- Email addresses
- IP addresses
- Sensitive files (.env, .db, .sqlite, .pem, .key)
- .gitignore coverage
- Git commit history for sensitive data
- Large files (>1MB)
- Hardcoded configuration

### 2. Publish Verification Scripts

Runs comprehensive pre-publication checks and generates a verification report.

#### Windows (PowerShell)
```powershell
.\scripts\publish.ps1
```

With options:
```powershell
# Skip tests
.\scripts\publish.ps1 -SkipTests

# Skip build
.\scripts\publish.ps1 -SkipBuild

# Verbose output
.\scripts\publish.ps1 -Verbose

# Combine options
.\scripts\publish.ps1 -SkipTests -SkipBuild -Verbose
```

#### Unix/Linux/macOS (Bash)
```bash
bash scripts/publish.sh
```

With options:
```bash
# Skip tests
bash scripts/publish.sh --skip-tests

# Skip build
bash scripts/publish.sh --skip-build

# Verbose output
bash scripts/publish.sh --verbose

# Combine options
bash scripts/publish.sh --skip-tests --skip-build --verbose
```

#### What it checks:
1. **Security Verification** - Runs security scan
2. **Required Files** - Checks for README, LICENSE, CONTRIBUTING, etc.
3. **GitHub Templates** - Verifies issue templates, PR template, workflows
4. **Package.json Metadata** - Validates repository URL, author, license, keywords
5. **Dependencies Security** - Runs npm audit for vulnerabilities
6. **Code Quality** - Runs linting checks
7. **Test Suite** - Runs frontend and backend tests
8. **Build Verification** - Verifies build completes successfully
9. **Git Repository** - Checks for uncommitted changes and version tags
10. **Documentation** - Validates README links and badges

#### Output

Both scripts generate a report file: `publish-verification-report.txt`

The report includes:
- Timestamp
- Duration
- Summary of checks (passed/failed/warnings)
- Overall status (READY/NOT READY for publication)

## Exit Codes

- `0` - All checks passed (or only warnings)
- `1` - One or more critical checks failed

## Usage in CI/CD

These scripts can be integrated into GitHub Actions workflows:

```yaml
- name: Run Security Scan
  run: |
    if [ "$RUNNER_OS" == "Windows" ]; then
      pwsh scripts/security-scan.ps1
    else
      bash scripts/security-scan.sh
    fi

- name: Run Publish Verification
  run: |
    if [ "$RUNNER_OS" == "Windows" ]; then
      pwsh scripts/publish.ps1
    else
      bash scripts/publish.sh
    fi
```

## Pre-Publication Checklist

Before running these scripts, ensure:

1. All code changes are committed
2. All tests are passing locally
3. Documentation is up-to-date
4. No sensitive data in codebase
5. .gitignore is properly configured
6. Version number is updated in package.json

## Troubleshooting

### Security Scan Issues

**Issue**: False positives for email addresses or IP addresses
- **Solution**: Review the matches. If they're legitimate (e.g., in documentation), they can be ignored. Consider adding them to an exclusion list if needed.

**Issue**: Large files detected
- **Solution**: Remove large files from the repository or add them to .gitignore. Use Git LFS for large binary files if necessary.

### Publish Verification Issues

**Issue**: Tests failing
- **Solution**: Run tests locally first: `npm test -- --run` and `cd backend && pytest`

**Issue**: Build failing
- **Solution**: Run build locally first: `npm run build`

**Issue**: npm audit vulnerabilities
- **Solution**: Update vulnerable packages: `npm audit fix` or `npm audit fix --force`

## Support

For issues or questions about these scripts, please:
1. Check the troubleshooting section above
2. Review the script output for specific error messages
3. Open an issue on GitHub with the error details
