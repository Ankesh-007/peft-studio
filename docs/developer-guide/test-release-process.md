# Test Release Process

This guide walks through the end-to-end testing of the GitHub release process for PEFT Studio.

## Prerequisites

- Git repository with push access
- GitHub account with repository access
- Access to Windows, macOS, and Linux test environments (VMs or physical machines)
- Node.js 18+ installed on build machine

## Step 1: Create Test Release

### 1.1 Prepare for Test Release

Before creating a test release, ensure all previous tasks are complete:

```bash
# Verify build configuration
npm run verify:build

# Run all tests
npm run test:run

# Build the application locally
npm run build
```

### 1.2 Create Test Version Tag

Create a test version tag following semantic versioning with a pre-release identifier:

```bash
# Example: v1.0.0-test.1
git tag -a v1.0.0-test.1 -m "Test release for end-to-end validation"

# Push the tag to trigger the release workflow
git push origin v1.0.0-test.1
```

**Note**: Use the `-test` suffix to clearly identify this as a test release.

### 1.3 Monitor Workflow Execution

1. Navigate to GitHub Actions: `https://github.com/Ankesh-007/peft-studio/actions`
2. Find the "Release" workflow triggered by your tag
3. Monitor each job:
   - `create-release`: Creates the GitHub release (draft)
   - `build-windows`: Builds Windows installers
   - `build-macos`: Builds macOS installers
   - `build-linux`: Builds Linux installers
   - `upload-assets`: Uploads all installers to the release
   - `generate-checksums`: Generates SHA256SUMS.txt

### 1.4 Verify Job Completion

Check that all jobs complete successfully:

- ✅ All jobs show green checkmarks
- ✅ No failed steps in any job
- ✅ Build artifacts are uploaded
- ✅ Release is created (in draft state)

### 1.5 Review Release Page

Navigate to the releases page: `https://github.com/Ankesh-007/peft-studio/releases`

Verify the test release contains:

- **Release title**: "PEFT Studio v1.0.0-test.1"
- **Draft status**: Release should be marked as draft
- **Assets**:
  - Windows: `PEFT-Studio-Setup-1.0.0-test.1.exe`
  - Windows Portable: `PEFT-Studio-1.0.0-test.1-portable.exe`
  - macOS DMG: `PEFT-Studio-1.0.0-test.1.dmg`
  - macOS ZIP: `PEFT-Studio-1.0.0-test.1-mac.zip`
  - Linux AppImage: `PEFT-Studio-1.0.0-test.1.AppImage`
  - Linux DEB: `peft-studio_1.0.0-test.1_amd64.deb`
  - Checksums: `SHA256SUMS.txt`
- **Release notes**: Formatted with installation instructions
- **Checksums section**: Present in release notes

## Step 2: Test Windows Installer

See [Windows Installer Testing](./test-windows-installer.md)

## Step 3: Test macOS Installer

See [macOS Installer Testing](./test-macos-installer.md)

## Step 4: Test Linux Installer

See [Linux Installer Testing](./test-linux-installer.md)

## Step 5: Test Auto-Update Mechanism

See [Auto-Update Testing](./test-auto-update.md)

## Troubleshooting

### Workflow Fails to Trigger

**Problem**: Tag is pushed but workflow doesn't start

**Solutions**:
- Verify tag format matches `v*.*.*` pattern
- Check GitHub Actions is enabled for the repository
- Ensure workflow file is in `.github/workflows/release.yml`
- Check repository permissions

### Build Job Fails

**Problem**: Platform-specific build fails

**Solutions**:
- Check build logs for specific errors
- Verify `package.json` build configuration
- Ensure all dependencies are in `package.json`
- Test build locally: `npm run package:win` (or `:mac`, `:linux`)

### Asset Upload Fails

**Problem**: Built installers don't appear in release

**Solutions**:
- Check artifact names match expected patterns
- Verify file paths in workflow
- Check GitHub token permissions
- Review upload-assets job logs

### Checksum Generation Fails

**Problem**: SHA256SUMS.txt is missing

**Solutions**:
- Verify `scripts/generate-checksums.js` exists
- Check that artifacts were downloaded successfully
- Review generate-checksums job logs
- Test locally: `npm run generate:checksums`

### Code Signing Issues

**Problem**: Installers are unsigned or signing fails

**Solutions**:
- Check if code signing secrets are configured (optional)
- Review signing status files in artifacts
- Unsigned builds are expected if secrets aren't configured
- See [Code Signing Documentation](./code-signing.md)

## Cleanup

After testing is complete:

### Delete Test Release

```bash
# Delete the release from GitHub UI or via API
gh release delete v1.0.0-test.1 --yes

# Delete the tag locally
git tag -d v1.0.0-test.1

# Delete the tag remotely
git push origin :refs/tags/v1.0.0-test.1
```

### Keep Test Release (Optional)

If you want to keep the test release for reference:
- Edit the release on GitHub
- Update the title to clearly mark it as a test
- Add a note explaining it's for testing purposes

## Next Steps

Once all tests pass:
1. Document any issues found
2. Fix any bugs discovered
3. Update documentation as needed
4. Prepare for official v1.0.0 release

## Checklist

Use this checklist to track testing progress:

- [ ] Test release tag created and pushed
- [ ] Release workflow triggered successfully
- [ ] All build jobs completed successfully
- [ ] Release created with all assets
- [ ] SHA256SUMS.txt generated
- [ ] Windows installer tested
- [ ] macOS installer tested
- [ ] Linux installer tested
- [ ] Auto-update mechanism tested
- [ ] All issues documented
- [ ] Test release cleaned up (or marked as test)

