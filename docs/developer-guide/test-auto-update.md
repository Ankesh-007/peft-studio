# Auto-Update Testing Guide

This guide provides detailed instructions for testing the auto-update mechanism in PEFT Studio.

## Prerequisites

- Two test releases created (e.g., v1.0.0-test.1 and v1.0.0-test.2)
- Application installed from first test release
- Internet connection
- Access to application logs

## Overview

The auto-update system uses electron-updater to:
1. Check for updates on application startup
2. Download updates in the background
3. Verify update integrity using checksums
4. Install updates with user confirmation
5. Restart application to apply updates

## Testing Procedure

### 1. Install Initial Version

#### 1.1 Install from First Test Release

1. Create and publish first test release: `v1.0.0-test.1`
2. Download and install the application
3. Launch the application
4. Verify it's running version 1.0.0-test.1

**Expected Result**: ✅ Application installed and running

### 2. Create Newer Test Release

#### 2.1 Prepare Second Test Release

1. Update version in `package.json`:
   ```json
   {
     "version": "1.0.0-test.2"
   }
   ```

2. Commit changes:
   ```bash
   git add package.json
   git commit -m "Bump version to 1.0.0-test.2 for update testing"
   ```

3. Create and push tag:
   ```bash
   git tag -a v1.0.0-test.2 -m "Second test release for auto-update testing"
   git push origin v1.0.0-test.2
   ```

4. Wait for release workflow to complete
5. Verify new release is published on GitHub

**Expected Result**: ✅ Second test release is available

### 3. Test Update Check on Startup

#### 3.1 Launch Application

1. Close application if running
2. Launch application
3. Observe startup behavior

**Test**: Update check occurs automatically

**Verify**:
- Application checks for updates within 3 seconds of startup
- No errors appear during update check
- Application remains responsive during check

**Expected Result**: ✅ Update check occurs on startup

#### 3.2 Check Application Logs

**Windows**:
```powershell
# View logs in PowerShell
Get-Content "$env:APPDATA\peft-studio\logs\main.log" -Tail 50
```

**macOS**:
```bash
# View logs in Terminal
tail -f ~/Library/Logs/peft-studio/main.log

# Or use Console.app
open -a Console
# Filter for "peft-studio"
```

**Linux**:
```bash
# View logs in Terminal
tail -f ~/.config/peft-studio/logs/main.log
```

**Verify log entries**:
- "Checking for updates..."
- "Update available: 1.0.0-test.2"
- Update info logged (version, release date, files)

**Expected Result**: ✅ Update check logged correctly

### 4. Test Update Notification

#### 4.1 Verify Notification Appears

**Test**: Update notification is displayed to user

**Verify**:
1. Notification component appears in UI
2. Notification shows:
   - New version number (1.0.0-test.2)
   - Release notes (if available)
   - "Download Update" button
   - "Dismiss" or "Later" button

**Expected Result**: ✅ Update notification displays correctly

#### 4.2 Test Notification Interaction

**Test**: User can interact with notification

1. **Test "Dismiss" button**:
   - Click "Dismiss" or "Later"
   - Verify notification closes
   - Verify application continues normally

2. **Test "Download Update" button**:
   - Relaunch application to see notification again
   - Click "Download Update"
   - Verify download starts

**Expected Result**: ✅ Notification buttons work correctly

### 5. Test Update Download

#### 5.1 Initiate Download

1. Click "Download Update" in notification
2. Observe download progress

**Test**: Update downloads in background

**Verify**:
- Download progress indicator appears
- Progress percentage updates
- Download speed shown (optional)
- Application remains usable during download

**Expected Result**: ✅ Update downloads in background

#### 5.2 Monitor Download Progress

**Check logs for download progress**:
- "Download progress: X%" messages
- Bytes transferred and total size
- Download speed

**Expected Result**: ✅ Download progress logged correctly

#### 5.3 Test Download Interruption

**Test**: Download handles interruptions gracefully

1. Start download
2. Disconnect internet
3. **Verify**: Error message appears
4. Reconnect internet
5. **Verify**: Download can be retried

**Expected Result**: ✅ Download handles network errors

### 6. Test Integrity Verification

#### 6.1 Verify Checksum Validation

**Test**: Downloaded update is verified

**Check logs for verification**:
- "Update downloaded successfully"
- "✅ Update integrity verified via SHA512 checksum"
- Checksum verification details logged

**Expected Result**: ✅ Update integrity verified automatically

#### 6.2 Test Checksum Mismatch (Simulated)

**Note**: This test requires modifying the update file, which is difficult in practice. Instead, verify the error handling exists in code.

**Verify in code** (`electron/main.js`):
```javascript
autoUpdater.on('error', (err) => {
  if (err.message.includes('sha512') || 
      err.message.includes('checksum') || 
      err.message.includes('integrity')) {
    // Checksum verification failure handling
    errorMessage = '⚠️ Update integrity verification failed...';
    errorType = 'checksum-mismatch';
  }
});
```

**Expected Result**: ✅ Checksum mismatch handling exists

### 7. Test Update Installation

#### 7.1 Install Downloaded Update

**Test**: Update can be installed

1. Wait for download to complete
2. **Verify**: "Update Ready" notification appears
3. **Verify**: "Install and Restart" button is shown
4. Click "Install and Restart"

**Expected Result**: ✅ Installation prompt appears

#### 7.2 Verify Installation Process

**Test**: Application restarts and applies update

1. Click "Install and Restart"
2. **Verify**: Application closes
3. **Verify**: Update is installed
4. **Verify**: Application restarts automatically
5. **Verify**: New version is running (1.0.0-test.2)

**Expected Result**: ✅ Application updates and restarts

#### 7.3 Verify Version After Update

**Check application version**:

1. Open application
2. Go to About dialog or Settings
3. **Verify**: Version shows 1.0.0-test.2
4. Check logs for version confirmation

**Expected Result**: ✅ Application is running new version

### 8. Test Update Scenarios

#### 8.1 Test "No Update Available"

**Test**: Application handles no updates correctly

1. Ensure application is on latest version
2. Restart application
3. **Verify**: Update check occurs
4. **Verify**: No notification appears
5. **Check logs**: "Update not available" message

**Expected Result**: ✅ No update scenario handled correctly

#### 8.2 Test Update Declined

**Test**: User can decline update

1. Trigger update notification
2. Click "Later" or "Dismiss"
3. **Verify**: Application continues normally
4. **Verify**: Update check occurs on next startup

**Expected Result**: ✅ User can postpone updates

#### 8.3 Test Multiple Updates

**Test**: Application can update through multiple versions

1. Install v1.0.0-test.1
2. Create v1.0.0-test.2 and v1.0.0-test.3
3. Update from test.1 to test.2
4. Verify update to test.3 is detected
5. Update to test.3

**Expected Result**: ✅ Multiple updates work correctly

### 9. Test Error Handling

#### 9.1 Test Network Errors

**Test**: Network errors are handled gracefully

1. Disconnect internet
2. Launch application
3. **Verify**: Update check fails silently
4. **Verify**: Application remains usable
5. **Check logs**: Network error logged
6. Reconnect internet
7. **Verify**: Next startup checks for updates

**Expected Result**: ✅ Network errors handled gracefully

#### 9.2 Test Server Errors

**Test**: Server errors are handled

1. Temporarily make releases private (or simulate 404)
2. Launch application
3. **Verify**: Update check fails gracefully
4. **Verify**: Error logged but app continues

**Expected Result**: ✅ Server errors handled gracefully

#### 9.3 Test Corrupted Download

**Test**: Corrupted downloads are rejected

**Note**: electron-updater automatically handles this via checksum verification

**Verify in logs**:
- If download is corrupted, checksum verification fails
- Error message indicates integrity failure
- Update is not installed

**Expected Result**: ✅ Corrupted downloads are rejected

### 10. Platform-Specific Testing

#### 10.1 Windows

**Test**: Windows-specific update behavior

1. Verify update downloads to temp directory
2. Verify installer runs with elevated privileges (if needed)
3. Verify application restarts correctly
4. Check Windows Event Viewer for errors

**Expected Result**: ✅ Windows updates work correctly

#### 10.2 macOS

**Test**: macOS-specific update behavior

1. Verify DMG is downloaded
2. Verify application is replaced in Applications folder
3. Verify code signature is maintained (if signed)
4. Check Console.app for errors

**Expected Result**: ✅ macOS updates work correctly

#### 10.3 Linux

**Test**: Linux-specific update behavior

1. For AppImage: Verify AppImage is replaced
2. For DEB: Verify package manager handles update
3. Verify permissions are maintained
4. Check system logs for errors

**Expected Result**: ✅ Linux updates work correctly

## Test Results Template

```markdown
## Auto-Update Test Results

**Test Date**: YYYY-MM-DD
**Tester**: [Your Name]
**Initial Version**: v1.0.0-test.1
**Update Version**: v1.0.0-test.2
**Platform**: Windows / macOS / Linux
**Platform Version**: [OS Version]

### Update Check
- [ ] Update check occurs on startup
- [ ] Update check logged correctly
- [ ] No errors during check

### Update Notification
- [ ] Notification appears when update available
- [ ] Notification shows version and release notes
- [ ] "Download" button works
- [ ] "Dismiss" button works

### Update Download
- [ ] Download starts successfully
- [ ] Progress indicator works
- [ ] Application remains usable during download
- [ ] Network errors handled gracefully

### Integrity Verification
- [ ] Checksum verification occurs automatically
- [ ] Verification logged correctly
- [ ] Corrupted downloads rejected (if tested)

### Update Installation
- [ ] "Install and Restart" prompt appears
- [ ] Application closes and restarts
- [ ] Update applied successfully
- [ ] New version running after restart

### Error Handling
- [ ] Network errors handled gracefully
- [ ] Server errors handled gracefully
- [ ] Application remains stable during errors

### Platform-Specific
- [ ] Platform-specific update mechanism works
- [ ] No platform-specific errors

### Issues Found
[List any issues discovered during testing]

### Notes
[Any additional observations]
```

## Common Issues and Solutions

### Update Check Doesn't Occur

**Issue**: No update check on startup

**Solutions**:
- Check if running in development mode (updates disabled)
- Verify internet connection
- Check application logs for errors
- Verify `electron-updater` is configured correctly
- Check GitHub releases API is accessible

### Update Notification Doesn't Appear

**Issue**: Update available but no notification

**Solutions**:
- Check if notification component is implemented
- Verify IPC communication between main and renderer
- Check browser console for errors
- Verify update event handlers are registered

### Download Fails

**Issue**: Update download fails or hangs

**Solutions**:
- Check internet connection
- Verify GitHub releases are public
- Check firewall/proxy settings
- Verify download URL is correct
- Check available disk space

### Checksum Verification Fails

**Issue**: Update rejected due to checksum mismatch

**Solutions**:
- Re-download update (may be corrupted)
- Verify release assets are correct
- Check if assets were modified after upload
- Verify electron-updater version is up-to-date

### Installation Fails

**Issue**: Update downloads but won't install

**Solutions**:
- Check if application has write permissions
- Verify no other instances are running
- Check if antivirus is blocking
- Review installation logs
- Try running as administrator (Windows)

### Application Won't Restart

**Issue**: Application closes but doesn't restart

**Solutions**:
- Check if `quitAndInstall()` is called correctly
- Verify no errors in installation process
- Manually restart application
- Check system logs for errors

## Automated Testing

### Unit Tests

Create unit tests for update logic:

```typescript
// src/test/unit/auto-update.test.ts
describe('Auto-Update System', () => {
  it('should check for updates on startup', async () => {
    // Test update check logic
  });

  it('should handle update available event', async () => {
    // Test update notification
  });

  it('should verify update integrity', async () => {
    // Test checksum verification
  });
});
```

### Integration Tests

Create integration tests for update flow:

```typescript
// src/test/integration/update-flow.test.ts
describe('Update Flow', () => {
  it('should complete full update cycle', async () => {
    // Test: check → download → verify → install
  });
});
```

## Next Steps

After completing auto-update testing:
1. Document all test results
2. Report any bugs found
3. Complete [Test Release Process](./test-release-process.md) checklist
4. Prepare for official release if all tests pass
