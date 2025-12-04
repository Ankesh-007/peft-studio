# Release Testing Summary

This document provides an overview of the end-to-end release testing process for PEFT Studio.

## Overview

The release testing process validates that:
1. GitHub Actions workflow builds installers correctly
2. All platform-specific installers work as expected
3. Checksums are generated and can be verified
4. Auto-update mechanism functions properly
5. Documentation is accurate and complete

## Quick Start

### Automated Testing

Use the provided scripts to automate parts of the testing process:

**PowerShell (Windows)**:
```powershell
# Test latest test release
.\scripts\test-release.ps1 -All

# Test specific version
.\scripts\test-release.ps1 -Version v1.0.0-test.1 -All

# Run individual checks
.\scripts\test-release.ps1 -CheckWorkflow
.\scripts\test-release.ps1 -VerifyAssets
.\scripts\test-release.ps1 -VerifyChecksums
```

**Bash (Linux/macOS)**:
```bash
# Make script executable (first time only)
chmod +x scripts/test-release.sh

# Test latest test release
./scripts/test-release.sh --all

# Test specific version
./scripts/test-release.sh --version v1.0.0-test.1 --all

# Run individual checks
./scripts/test-release.sh --check-workflow
./scripts/test-release.sh --verify-assets
./scripts/test-release.sh --verify-checksums
```

### Manual Testing

Follow the detailed guides for each platform:

1. **[Test Release Process](./test-release-process.md)** - Overall process and workflow
2. **[Windows Installer Testing](./test-windows-installer.md)** - Windows-specific testing
3. **[macOS Installer Testing](./test-macos-installer.md)** - macOS-specific testing
4. **[Linux Installer Testing](./test-linux-installer.md)** - Linux-specific testing
5. **[Auto-Update Testing](./test-auto-update.md)** - Update mechanism testing

## Testing Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Create Test Release                                      │
│    - Create version tag (v1.0.0-test.1)                    │
│    - Push tag to trigger workflow                          │
│    - Monitor workflow execution                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Verify Release Assets                                    │
│    - Check all platform installers present                  │
│    - Verify SHA256SUMS.txt exists                          │
│    - Review release notes                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Test Platform Installers                                 │
│    ├─ Windows: NSIS installer + portable                   │
│    ├─ macOS: DMG + ZIP archive                             │
│    └─ Linux: AppImage + DEB package                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Test Auto-Update                                         │
│    - Install from test.1                                    │
│    - Create test.2 release                                  │
│    - Verify update detection                                │
│    - Test update installation                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Document Results                                         │
│    - Record test results                                    │
│    - Report any issues found                                │
│    - Update documentation if needed                         │
└─────────────────────────────────────────────────────────────┘
```

## Test Checklist

### Pre-Release Checks

- [ ] All previous tasks completed
- [ ] Code is committed and pushed
- [ ] Version number updated in package.json
- [ ] CHANGELOG.md updated
- [ ] Documentation reviewed

### Release Creation

- [ ] Test tag created (v1.0.0-test.X)
- [ ] Tag pushed to GitHub
- [ ] Workflow triggered successfully
- [ ] All build jobs completed
- [ ] Release created (draft)

### Asset Verification

- [ ] Windows NSIS installer present
- [ ] Windows portable version present
- [ ] macOS DMG present
- [ ] macOS ZIP present
- [ ] Linux AppImage present
- [ ] Linux DEB package present
- [ ] SHA256SUMS.txt present
- [ ] Release notes formatted correctly

### Windows Testing

- [ ] Installer checksum verified
- [ ] Installation wizard works
- [ ] Custom directory selection works
- [ ] Desktop shortcut created
- [ ] Start menu shortcut created
- [ ] Application launches
- [ ] Portable version works
- [ ] Uninstallation works

### macOS Testing

- [ ] DMG checksum verified
- [ ] DMG mounts successfully
- [ ] Drag-and-drop installation works
- [ ] Application launches
- [ ] Code signature valid (if signed)
- [ ] ZIP archive works
- [ ] Menu bar integration works
- [ ] Dock integration works

### Linux Testing

- [ ] AppImage checksum verified
- [ ] AppImage is executable
- [ ] AppImage runs without installation
- [ ] Desktop integration works
- [ ] DEB package installs
- [ ] Application appears in menu
- [ ] Application launches from terminal
- [ ] Uninstallation works

### Auto-Update Testing

- [ ] Update check occurs on startup
- [ ] Update notification appears
- [ ] Update download works
- [ ] Download progress shown
- [ ] Checksum verification works
- [ ] Update installation works
- [ ] Application restarts with new version
- [ ] Network errors handled gracefully

### Documentation

- [ ] README links to releases
- [ ] Installation guides accurate
- [ ] Troubleshooting guide complete
- [ ] Code signing documentation accurate
- [ ] Checksum verification instructions clear

## Common Issues

### Workflow Failures

**Symptom**: Build jobs fail or don't complete

**Troubleshooting**:
1. Check workflow logs in GitHub Actions
2. Verify package.json configuration
3. Test builds locally: `npm run package:win`
4. Check for missing dependencies
5. Verify secrets are configured (for code signing)

### Missing Assets

**Symptom**: Some installers not in release

**Troubleshooting**:
1. Check if build job completed successfully
2. Verify artifact upload step succeeded
3. Check file naming matches expected patterns
4. Review upload-assets job logs

### Checksum Verification Fails

**Symptom**: Downloaded file checksum doesn't match

**Troubleshooting**:
1. Re-download the file (may be corrupted)
2. Verify SHA256SUMS.txt is correct
3. Check if file was modified after upload
4. Use correct checksum algorithm (SHA256)

### Installer Won't Run

**Symptom**: Installer fails to launch or install

**Troubleshooting**:
1. Check OS version compatibility
2. Verify file isn't corrupted (checksum)
3. Check antivirus isn't blocking
4. For unsigned builds, bypass security warnings
5. Run as administrator (Windows)

### Auto-Update Doesn't Work

**Symptom**: Application doesn't check for updates

**Troubleshooting**:
1. Verify not running in development mode
2. Check internet connection
3. Review application logs
4. Verify electron-updater configuration
5. Check GitHub releases are public

## Test Results Template

Use this template to document your test results:

```markdown
# Release Test Results

**Date**: YYYY-MM-DD
**Tester**: [Your Name]
**Version Tested**: v1.0.0-test.X
**Test Environment**: [OS and versions used]

## Summary

- **Overall Status**: ✅ Pass / ❌ Fail
- **Issues Found**: [Number]
- **Blockers**: [Number]

## Automated Tests

- [ ] Workflow status check: ✅ Pass / ❌ Fail
- [ ] Asset verification: ✅ Pass / ❌ Fail
- [ ] Checksum verification: ✅ Pass / ❌ Fail

## Platform Tests

### Windows
- [ ] Installer: ✅ Pass / ❌ Fail
- [ ] Portable: ✅ Pass / ❌ Fail
- **Notes**: [Any observations]

### macOS
- [ ] DMG: ✅ Pass / ❌ Fail
- [ ] ZIP: ✅ Pass / ❌ Fail
- **Notes**: [Any observations]

### Linux
- [ ] AppImage: ✅ Pass / ❌ Fail
- [ ] DEB: ✅ Pass / ❌ Fail
- **Notes**: [Any observations]

## Auto-Update
- [ ] Update check: ✅ Pass / ❌ Fail
- [ ] Update download: ✅ Pass / ❌ Fail
- [ ] Update installation: ✅ Pass / ❌ Fail
- **Notes**: [Any observations]

## Issues Found

### Issue 1: [Title]
- **Severity**: Critical / High / Medium / Low
- **Platform**: Windows / macOS / Linux / All
- **Description**: [Detailed description]
- **Steps to Reproduce**: [Steps]
- **Expected**: [Expected behavior]
- **Actual**: [Actual behavior]

[Add more issues as needed]

## Recommendations

[Any recommendations for improvements or fixes]

## Sign-off

- [ ] All critical issues resolved
- [ ] All tests passed
- [ ] Ready for production release

**Tester Signature**: [Your Name]
**Date**: YYYY-MM-DD
```

## Next Steps

After completing all tests:

1. **If all tests pass**:
   - Document test results
   - Clean up test releases (or mark as test)
   - Prepare for official v1.0.0 release
   - Update version to 1.0.0 (remove -test suffix)
   - Create official release

2. **If tests fail**:
   - Document all issues found
   - Create GitHub issues for bugs
   - Fix critical issues
   - Re-test after fixes
   - Repeat testing cycle

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [electron-builder Documentation](https://www.electron.build/)
- [electron-updater Documentation](https://www.electron.build/auto-update)
- [Code Signing Guide](./code-signing.md)
- [Build and Release Workflow](./build-release-workflow.md)

## Support

If you encounter issues during testing:

1. Check the troubleshooting sections in each guide
2. Review GitHub Actions logs
3. Check application logs
4. Search existing GitHub issues
5. Create a new issue with detailed information

## Continuous Improvement

After each release cycle:

- Review test results
- Update testing documentation
- Improve automation scripts
- Add new test cases as needed
- Document lessons learned
