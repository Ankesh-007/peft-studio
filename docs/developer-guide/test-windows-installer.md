# Windows Installer Testing Guide

This guide provides detailed instructions for testing PEFT Studio installers on Windows.

## Prerequisites

- Windows 10 or later (64-bit)
- Administrator access (for installer testing)
- PowerShell or Command Prompt
- Internet connection for checksum verification

## Test Environment Setup

### Option 1: Physical Windows Machine
- Use a dedicated Windows machine for testing
- Ensure it's a clean environment (no previous PEFT Studio installations)

### Option 2: Windows Virtual Machine
- Use VirtualBox, VMware, or Hyper-V
- Create a Windows 10/11 VM
- Take a snapshot before testing for easy rollback

## Testing Procedure

### 1. Download Windows Installer

Navigate to the test release page and download:
- `PEFT-Studio-Setup-{version}.exe` (NSIS installer)
- `PEFT-Studio-{version}-portable.exe` (Portable version)
- `SHA256SUMS.txt` (Checksums file)

### 2. Verify Checksum

Open PowerShell and navigate to the download directory:

```powershell
# Calculate SHA256 hash of the installer
$hash = Get-FileHash -Path "PEFT-Studio-Setup-1.0.0-test.1.exe" -Algorithm SHA256
Write-Host "Calculated: $($hash.Hash)"

# Display the expected hash from SHA256SUMS.txt
Get-Content SHA256SUMS.txt | Select-String "PEFT-Studio-Setup"
```

**Verify**: The calculated hash matches the hash in SHA256SUMS.txt

**Expected Result**: ✅ Hashes match exactly

### 3. Test NSIS Installer

#### 3.1 Run the Installer

1. Double-click `PEFT-Studio-Setup-{version}.exe`
2. If SmartScreen warning appears:
   - Click "More info"
   - Click "Run anyway"
   - **Note**: This is expected for unsigned builds

#### 3.2 Installation Wizard

**Test**: Installation directory selection

1. Installer should display welcome screen
2. Click "Next"
3. **Verify**: Option to choose installation directory is present
4. **Test**: Change installation directory to a custom location
5. Click "Next"

**Expected Result**: ✅ User can select custom installation directory

#### 3.3 Installation Options

**Test**: Installation options

1. **Verify**: Option to create desktop shortcut is present
2. **Verify**: Option to create start menu shortcut is present
3. Select both options
4. Click "Install"

**Expected Result**: ✅ Installation proceeds with selected options

#### 3.4 Installation Progress

**Test**: Installation completes successfully

1. **Verify**: Progress bar shows installation progress
2. Wait for installation to complete
3. **Verify**: No error messages appear

**Expected Result**: ✅ Installation completes without errors

#### 3.5 Post-Installation Verification

**Test**: Shortcuts created

1. **Verify**: Desktop shortcut exists
   - Check desktop for "PEFT Studio" icon
2. **Verify**: Start menu shortcut exists
   - Open Start menu
   - Search for "PEFT Studio"
   - Verify shortcut appears

**Expected Result**: ✅ Both shortcuts are created

**Test**: Installation directory

1. Navigate to installation directory (default: `C:\Users\{username}\AppData\Local\Programs\peft-studio`)
2. **Verify**: Application files are present:
   - `PEFT Studio.exe`
   - `resources` folder
   - `locales` folder
   - Other Electron files

**Expected Result**: ✅ All application files are present

#### 3.6 Launch Application

**Test**: Application launches successfully

1. Double-click desktop shortcut or start menu shortcut
2. **Verify**: Application window opens
3. **Verify**: No error dialogs appear
4. **Verify**: Application UI loads correctly

**Expected Result**: ✅ Application launches and displays main window

#### 3.7 Auto-Update Registration

**Test**: Auto-update system is registered

1. Open application
2. Check application logs (if accessible)
3. **Verify**: Update check occurs on startup
4. **Verify**: No update errors in logs

**Expected Result**: ✅ Auto-update system is functional

### 4. Test Portable Version

#### 4.1 Extract and Run

1. Download `PEFT-Studio-{version}-portable.exe`
2. Verify checksum (same process as installer)
3. Place portable exe in a test folder
4. Double-click to run

**Test**: Portable version runs without installation

1. **Verify**: Application launches directly
2. **Verify**: No installation wizard appears
3. **Verify**: Application runs from current directory

**Expected Result**: ✅ Portable version runs without installation

#### 4.2 Portable Behavior

**Test**: No system modifications

1. Run portable version
2. **Verify**: No shortcuts created
3. **Verify**: No registry entries created
4. **Verify**: Application data stored in portable directory

**Expected Result**: ✅ Portable version doesn't modify system

### 5. Uninstallation Testing

#### 5.1 Uninstall via Control Panel

1. Open "Add or Remove Programs"
2. Find "PEFT Studio"
3. Click "Uninstall"
4. Follow uninstallation wizard

**Test**: Clean uninstallation

1. **Verify**: Uninstaller removes application files
2. **Verify**: Desktop shortcut is removed
3. **Verify**: Start menu shortcut is removed
4. **Verify**: Installation directory is removed

**Expected Result**: ✅ Application is completely uninstalled

#### 5.2 Verify Cleanup

**Test**: No leftover files

1. Check installation directory
2. **Verify**: Directory is removed or empty
3. Check `%APPDATA%\peft-studio`
4. **Note**: User data may be preserved (expected behavior)

**Expected Result**: ✅ Application files are removed

## Test Results Template

```markdown
## Windows Installer Test Results

**Test Date**: YYYY-MM-DD
**Tester**: [Your Name]
**Version**: v1.0.0-test.1
**Windows Version**: Windows 10/11 [Build Number]

### Checksum Verification
- [ ] NSIS Installer checksum matches
- [ ] Portable version checksum matches

### NSIS Installer
- [ ] Installation wizard displays correctly
- [ ] Directory selection works
- [ ] Desktop shortcut created
- [ ] Start menu shortcut created
- [ ] Application launches successfully
- [ ] Auto-update registration works

### Portable Version
- [ ] Runs without installation
- [ ] No system modifications
- [ ] Application functions correctly

### Uninstallation
- [ ] Uninstaller runs successfully
- [ ] Application files removed
- [ ] Shortcuts removed

### Issues Found
[List any issues discovered during testing]

### Notes
[Any additional observations]
```

## Common Issues and Solutions

### SmartScreen Warning

**Issue**: Windows SmartScreen blocks installer

**Solution**: 
- Click "More info" → "Run anyway"
- This is expected for unsigned builds
- Document in release notes

### Installation Fails

**Issue**: Installer fails with error

**Solutions**:
- Check if previous version is running (close it)
- Run installer as administrator
- Check antivirus isn't blocking
- Review installer logs in `%TEMP%`

### Application Won't Launch

**Issue**: Application fails to start

**Solutions**:
- Check Windows Event Viewer for errors
- Verify all dependencies are installed
- Try running as administrator
- Check antivirus logs

### Shortcuts Not Created

**Issue**: Desktop/Start menu shortcuts missing

**Solutions**:
- Verify options were selected during installation
- Check if installer completed successfully
- Manually create shortcuts if needed

## Next Steps

After completing Windows testing:
1. Document all test results
2. Report any bugs found
3. Proceed to [macOS Installer Testing](./test-macos-installer.md)
4. Update test checklist in [Test Release Process](./test-release-process.md)
