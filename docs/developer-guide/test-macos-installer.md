# macOS Installer Testing Guide

This guide provides detailed instructions for testing PEFT Studio installers on macOS.

## Prerequisites

- macOS 10.13 (High Sierra) or later
- Administrator access
- Terminal access
- Internet connection for checksum verification

## Test Environment Setup

### Option 1: Physical Mac
- Use a dedicated Mac for testing
- Ensure it's a clean environment (no previous PEFT Studio installations)

### Option 2: macOS Virtual Machine
- Use VMware Fusion, Parallels, or UTM
- Create a macOS VM (requires macOS host or specific hardware)
- Take a snapshot before testing for easy rollback

## Testing Procedure

### 1. Download macOS Installer

Navigate to the test release page and download:
- `PEFT-Studio-{version}.dmg` (DMG installer)
- `PEFT-Studio-{version}-mac.zip` (ZIP archive)
- `SHA256SUMS.txt` (Checksums file)

### 2. Verify Checksum

Open Terminal and navigate to the download directory:

```bash
# Calculate SHA256 hash of the DMG
shasum -a 256 PEFT-Studio-1.0.0-test.1.dmg

# Display the expected hash from SHA256SUMS.txt
grep "PEFT-Studio.*\.dmg" SHA256SUMS.txt
```

**Verify**: The calculated hash matches the hash in SHA256SUMS.txt

**Expected Result**: ✅ Hashes match exactly

### 3. Test DMG Installer

#### 3.1 Open the DMG

1. Double-click `PEFT-Studio-{version}.dmg`
2. If Gatekeeper warning appears:
   - For unsigned builds: Right-click → Open → Open
   - Or: System Preferences → Security & Privacy → "Open Anyway"
   - **Note**: This is expected for unsigned builds

**Expected Result**: ✅ DMG mounts successfully

#### 3.2 Verify DMG Contents

**Test**: DMG window displays correctly

1. **Verify**: DMG window opens automatically
2. **Verify**: Window shows:
   - PEFT Studio application icon
   - Applications folder shortcut (arrow or link)
   - Optional: Background image
   - Optional: Instructions text

**Expected Result**: ✅ DMG contains application and Applications folder link

#### 3.3 Install Application

**Test**: Drag-and-drop installation

1. Drag "PEFT Studio" icon to Applications folder
2. **Verify**: Copy progress appears
3. Wait for copy to complete
4. **Verify**: No error messages appear

**Expected Result**: ✅ Application copies to Applications folder successfully

#### 3.4 Eject DMG

1. Right-click DMG in Finder sidebar
2. Click "Eject"
3. **Verify**: DMG unmounts cleanly

**Expected Result**: ✅ DMG ejects without errors

#### 3.5 Verify Installation

**Test**: Application is in Applications folder

1. Open Finder
2. Navigate to Applications folder
3. **Verify**: "PEFT Studio.app" is present
4. **Verify**: Application icon displays correctly

**Expected Result**: ✅ Application is installed in Applications folder

#### 3.6 Launch Application

**Test**: Application launches successfully

1. Double-click "PEFT Studio" in Applications
2. If Gatekeeper warning appears (unsigned builds):
   - Right-click → Open → Open
   - Or: System Preferences → Security & Privacy → "Open Anyway"
3. **Verify**: Application window opens
4. **Verify**: No error dialogs appear
5. **Verify**: Application UI loads correctly

**Expected Result**: ✅ Application launches and displays main window

#### 3.7 Verify Code Signature (If Signed)

**Test**: Application signature verification

```bash
# Check if application is signed
codesign -dv --verbose=4 /Applications/PEFT\ Studio.app

# Verify signature
codesign --verify --deep --strict --verbose=2 /Applications/PEFT\ Studio.app

# Check notarization (macOS 10.15+)
spctl -a -vv /Applications/PEFT\ Studio.app
```

**Expected Results**:
- If signed: ✅ Valid signature and notarization
- If unsigned: ⚠️ "code object is not signed at all" (expected)

### 4. Test ZIP Archive

#### 4.1 Extract ZIP

1. Download `PEFT-Studio-{version}-mac.zip`
2. Verify checksum (same process as DMG)
3. Double-click ZIP to extract
4. **Verify**: "PEFT Studio.app" is extracted

**Expected Result**: ✅ ZIP extracts successfully

#### 4.2 Run from ZIP

**Test**: Application runs from extracted location

1. Double-click extracted "PEFT Studio.app"
2. Handle Gatekeeper warning if present
3. **Verify**: Application launches
4. **Verify**: Application functions correctly

**Expected Result**: ✅ Application runs from any location

#### 4.3 Move to Applications

**Test**: Application can be moved to Applications

1. Drag extracted app to Applications folder
2. **Verify**: Move completes successfully
3. Launch from Applications folder
4. **Verify**: Application runs correctly

**Expected Result**: ✅ Application works after moving

### 5. Test Application Features

#### 5.1 Menu Bar

**Test**: macOS menu bar integration

1. Launch application
2. **Verify**: Application menu appears in menu bar
3. **Verify**: Standard menus present:
   - PEFT Studio menu (with About, Preferences, Quit)
   - File menu
   - Edit menu
   - View menu
   - Window menu
   - Help menu

**Expected Result**: ✅ Menu bar integration works correctly

#### 5.2 Dock Integration

**Test**: Dock icon and behavior

1. **Verify**: Application icon appears in Dock
2. **Verify**: Icon displays correctly
3. Right-click Dock icon
4. **Verify**: Context menu appears with options

**Expected Result**: ✅ Dock integration works correctly

#### 5.3 File Associations

**Test**: .peft file association (if configured)

1. Create a test .peft file
2. Double-click the file
3. **Verify**: PEFT Studio opens the file
4. Or: Right-click → Open With → PEFT Studio

**Expected Result**: ✅ File associations work (if configured)

### 6. Test Auto-Update System

**Test**: Update check on startup

1. Launch application
2. Check Console.app for PEFT Studio logs
3. **Verify**: Update check occurs
4. **Verify**: No update errors in logs

**Expected Result**: ✅ Auto-update system is functional

### 7. Uninstallation Testing

#### 7.1 Remove Application

**Test**: Manual uninstallation

1. Quit PEFT Studio
2. Open Applications folder
3. Drag "PEFT Studio.app" to Trash
4. Empty Trash
5. **Verify**: Application is removed

**Expected Result**: ✅ Application is deleted

#### 7.2 Verify Cleanup

**Test**: Check for leftover files

```bash
# Check application support directory
ls ~/Library/Application\ Support/peft-studio

# Check preferences
ls ~/Library/Preferences/com.peftstudio.app.*

# Check caches
ls ~/Library/Caches/com.peftstudio.app

# Check logs
ls ~/Library/Logs/peft-studio
```

**Note**: User data may be preserved (expected behavior)

**Expected Result**: ✅ Application files are removed, user data may remain

## Test Results Template

```markdown
## macOS Installer Test Results

**Test Date**: YYYY-MM-DD
**Tester**: [Your Name]
**Version**: v1.0.0-test.1
**macOS Version**: macOS [Version] ([Build])
**Architecture**: Intel / Apple Silicon

### Checksum Verification
- [ ] DMG checksum matches
- [ ] ZIP checksum matches

### DMG Installer
- [ ] DMG mounts successfully
- [ ] DMG window displays correctly
- [ ] Drag-and-drop installation works
- [ ] Application launches successfully
- [ ] Code signature valid (if signed)

### ZIP Archive
- [ ] ZIP extracts successfully
- [ ] Application runs from extracted location
- [ ] Application can be moved to Applications

### macOS Integration
- [ ] Menu bar integration works
- [ ] Dock integration works
- [ ] File associations work (if configured)

### Auto-Update
- [ ] Update check occurs on startup
- [ ] No update errors

### Uninstallation
- [ ] Application can be deleted
- [ ] Application files removed

### Issues Found
[List any issues discovered during testing]

### Notes
[Any additional observations]
```

## Common Issues and Solutions

### Gatekeeper Blocks Application

**Issue**: "App can't be opened because it is from an unidentified developer"

**Solution**:
- Right-click app → Open → Open
- Or: System Preferences → Security & Privacy → "Open Anyway"
- This is expected for unsigned builds
- Document in release notes

### DMG Won't Mount

**Issue**: DMG fails to mount

**Solutions**:
- Verify DMG isn't corrupted (check checksum)
- Try mounting from Terminal: `hdiutil attach PEFT-Studio-*.dmg`
- Check Disk Utility for errors
- Re-download DMG

### Application Crashes on Launch

**Issue**: Application crashes immediately

**Solutions**:
- Check Console.app for crash logs
- Verify macOS version compatibility
- Check for missing dependencies
- Try running from Terminal to see errors

### Code Signature Invalid

**Issue**: Signature verification fails

**Solutions**:
- Check if app was modified after signing
- Verify signing certificate is valid
- Re-download installer
- Check for quarantine attribute: `xattr -d com.apple.quarantine /Applications/PEFT\ Studio.app`

### Notarization Issues

**Issue**: Notarization check fails

**Solutions**:
- Verify app was notarized (check workflow logs)
- Check Apple Developer account status
- Notarization is optional for testing
- Document in release notes

## Architecture-Specific Testing

### Intel Macs

**Test**: Application runs on Intel architecture

1. Verify DMG contains x64 build
2. Launch application
3. Check Activity Monitor → Architecture shows "Intel"

### Apple Silicon Macs

**Test**: Application runs on Apple Silicon

1. Verify DMG contains arm64 build or universal binary
2. Launch application
3. Check Activity Monitor → Architecture shows "Apple" (native) or "Intel" (Rosetta)

**Test**: Rosetta 2 compatibility (if Intel-only build)

1. Verify Rosetta 2 is installed
2. Application should run via Rosetta
3. Performance may be slightly reduced

## Next Steps

After completing macOS testing:
1. Document all test results
2. Report any bugs found
3. Proceed to [Linux Installer Testing](./test-linux-installer.md)
4. Update test checklist in [Test Release Process](./test-release-process.md)
