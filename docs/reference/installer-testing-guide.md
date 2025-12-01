# Installer Testing Guide

This guide provides instructions for testing PEFT Studio installers on different platforms to ensure they work correctly before public release.

## Overview

Before releasing installers to the public, they must be tested on actual target platforms to verify:
- Installation completes successfully
- Application launches without errors
- Core features work as expected
- Uninstallation works correctly

## Prerequisites

### For All Platforms
- Clean test environment (virtual machine or fresh system recommended)
- No previous installation of PEFT Studio
- Internet connection for downloading dependencies
- Sufficient disk space (at least 2GB free)

### Platform-Specific Requirements

**Windows:**
- Windows 10 or later (64-bit)
- Administrator privileges for installation
- .NET Framework 4.5+ (usually pre-installed)

**macOS:**
- macOS 10.13 (High Sierra) or later
- Administrator privileges for installation
- Gatekeeper may require approval for first launch

**Linux:**
- Ubuntu 20.04+ or equivalent distribution
- `libgtk-3-0`, `libnotify4`, `libnss3` packages
- X11 or Wayland display server

## Testing Procedure

### 1. Pre-Installation Testing

Before installing, verify the installer package:

**Windows (.exe or .msi):**
```powershell
# Check file integrity
Get-FileHash -Path "PEFT-Studio-Setup-1.0.0.exe" -Algorithm SHA256

# Verify digital signature (if signed)
Get-AuthenticodeSignature -FilePath "PEFT-Studio-Setup-1.0.0.exe"
```

**macOS (.dmg):**
```bash
# Check file integrity
shasum -a 256 PEFT-Studio-1.0.0.dmg

# Verify code signature (if signed)
codesign -dv --verbose=4 /Applications/PEFT\ Studio.app
```

**Linux (.AppImage or .deb):**
```bash
# Check file integrity
sha256sum PEFT-Studio-1.0.0.AppImage

# For .deb packages
dpkg-deb --info peft-studio_1.0.0_amd64.deb
```

### 2. Installation Testing

#### Windows Installation

1. **Run Installer:**
   - Double-click the installer executable
   - If prompted by Windows Defender SmartScreen, click "More info" → "Run anyway"
   - Follow installation wizard

2. **Verify Installation:**
   - Check installation directory: `C:\Program Files\PEFT Studio\`
   - Verify Start Menu shortcut exists
   - Verify Desktop shortcut exists (if selected)

3. **Check Registry Entries:**
   ```powershell
   # Check if application is registered
   Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* | 
       Where-Object { $_.DisplayName -like "*PEFT Studio*" }
   ```

#### macOS Installation

1. **Mount DMG:**
   - Double-click the .dmg file
   - Drag PEFT Studio to Applications folder

2. **First Launch:**
   - Open Applications folder
   - Right-click PEFT Studio → Open (first time only)
   - Click "Open" when Gatekeeper warning appears

3. **Verify Installation:**
   ```bash
   # Check if app bundle is valid
   ls -la /Applications/PEFT\ Studio.app/Contents/MacOS/
   
   # Verify permissions
   xattr -l /Applications/PEFT\ Studio.app
   ```

#### Linux Installation

**For AppImage:**
1. **Make Executable:**
   ```bash
   chmod +x PEFT-Studio-1.0.0.AppImage
   ```

2. **Run:**
   ```bash
   ./PEFT-Studio-1.0.0.AppImage
   ```

**For .deb Package:**
1. **Install:**
   ```bash
   sudo dpkg -i peft-studio_1.0.0_amd64.deb
   sudo apt-get install -f  # Fix dependencies if needed
   ```

2. **Verify:**
   ```bash
   dpkg -l | grep peft-studio
   which peft-studio
   ```

### 3. Application Launch Testing

After installation, test the application launch:

1. **Launch Application:**
   - Windows: Start Menu → PEFT Studio
   - macOS: Applications → PEFT Studio
   - Linux: Application menu or command line

2. **Verify Startup:**
   - Application window opens within 10 seconds
   - No error dialogs appear
   - Splash screen displays (if implemented)
   - Main window loads completely

3. **Check Console Output:**
   - Windows: Check Event Viewer for errors
   - macOS: Check Console.app for crash reports
   - Linux: Check `~/.config/PEFT Studio/logs/`

### 4. Core Feature Testing

Test essential features to ensure the application works:

#### Basic Functionality
- [ ] Dashboard loads and displays correctly
- [ ] Navigation between sections works
- [ ] Settings can be opened and modified
- [ ] Application can be minimized/maximized
- [ ] Application can be closed properly

#### Platform Connections
- [ ] Can open Platform Connections settings
- [ ] Can add a test API key (use dummy value)
- [ ] Connection validation works
- [ ] Can remove API key

#### Model Browser
- [ ] Model Browser opens
- [ ] Search functionality works
- [ ] Filters can be applied
- [ ] Model details can be viewed

#### Training Configuration
- [ ] Configuration wizard opens
- [ ] Can navigate through wizard steps
- [ ] Form validation works
- [ ] Can save configuration

#### File Operations
- [ ] Can open file dialogs
- [ ] Can select files
- [ ] File paths display correctly

### 5. Performance Testing

Verify the application performs acceptably:

1. **Startup Time:**
   - Measure time from launch to fully loaded UI
   - Should be < 10 seconds on modern hardware

2. **Memory Usage:**
   - Check initial memory footprint
   - Should be < 500MB at startup

3. **CPU Usage:**
   - Monitor CPU usage during idle
   - Should be < 5% when idle

4. **Responsiveness:**
   - UI should remain responsive during operations
   - No freezing or hanging

### 6. Uninstallation Testing

Test that the application can be cleanly removed:

#### Windows
1. **Uninstall:**
   - Settings → Apps → PEFT Studio → Uninstall
   - Or: Control Panel → Programs → Uninstall

2. **Verify Removal:**
   ```powershell
   # Check if files removed
   Test-Path "C:\Program Files\PEFT Studio"
   
   # Check if registry entries removed
   Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* | 
       Where-Object { $_.DisplayName -like "*PEFT Studio*" }
   ```

#### macOS
1. **Uninstall:**
   - Drag PEFT Studio from Applications to Trash
   - Empty Trash

2. **Verify Removal:**
   ```bash
   # Check if app removed
   ls /Applications/ | grep "PEFT Studio"
   
   # Check for leftover files
   ls ~/Library/Application\ Support/ | grep "PEFT Studio"
   ```

#### Linux
**For AppImage:**
- Simply delete the .AppImage file

**For .deb:**
```bash
sudo apt-get remove peft-studio
sudo apt-get purge peft-studio  # Remove config files too
```

### 7. Edge Case Testing

Test uncommon scenarios:

- [ ] Install with non-admin user (should prompt for elevation)
- [ ] Install to custom directory
- [ ] Install over existing installation (upgrade scenario)
- [ ] Install with limited disk space
- [ ] Launch with no internet connection
- [ ] Launch with firewall blocking network access

## Test Report Template

Use this template to document test results:

```markdown
# PEFT Studio Installer Test Report

**Version:** 1.0.0
**Platform:** [Windows/macOS/Linux]
**Tester:** [Name]
**Date:** [YYYY-MM-DD]

## Environment
- OS Version: 
- Hardware: 
- Disk Space: 
- Internet: [Yes/No]

## Installation
- [ ] Installer downloaded successfully
- [ ] File integrity verified
- [ ] Installation completed without errors
- [ ] Shortcuts created correctly
- [ ] Installation time: [X seconds]

## Application Launch
- [ ] Application launched successfully
- [ ] No error dialogs
- [ ] UI loaded completely
- [ ] Launch time: [X seconds]

## Core Features
- [ ] Dashboard works
- [ ] Navigation works
- [ ] Settings accessible
- [ ] Platform connections work
- [ ] Model browser works
- [ ] Training configuration works

## Performance
- Startup time: [X seconds]
- Memory usage: [X MB]
- CPU usage (idle): [X%]
- Responsiveness: [Good/Fair/Poor]

## Uninstallation
- [ ] Uninstall completed successfully
- [ ] Files removed
- [ ] Registry/config cleaned
- [ ] No leftover files

## Issues Found
[List any issues, bugs, or unexpected behavior]

## Overall Result
- [ ] PASS - Ready for release
- [ ] FAIL - Issues must be fixed
- [ ] CONDITIONAL - Minor issues, can release with notes

## Notes
[Any additional observations or comments]
```

## Automated Testing

For CI/CD environments, use these automated tests:

### Windows (PowerShell)
```powershell
# Install silently
Start-Process -FilePath "PEFT-Studio-Setup.exe" -ArgumentList "/S" -Wait

# Verify installation
$installed = Test-Path "C:\Program Files\PEFT Studio\PEFT Studio.exe"
if ($installed) {
    Write-Host "Installation successful"
} else {
    Write-Host "Installation failed"
    exit 1
}

# Launch and check process
Start-Process "C:\Program Files\PEFT Studio\PEFT Studio.exe"
Start-Sleep -Seconds 10
$process = Get-Process -Name "PEFT Studio" -ErrorAction SilentlyContinue
if ($process) {
    Write-Host "Application launched successfully"
    Stop-Process -Name "PEFT Studio" -Force
} else {
    Write-Host "Application failed to launch"
    exit 1
}
```

### macOS (Bash)
```bash
#!/bin/bash

# Mount DMG
hdiutil attach PEFT-Studio-1.0.0.dmg

# Copy to Applications
cp -R "/Volumes/PEFT Studio/PEFT Studio.app" /Applications/

# Unmount DMG
hdiutil detach "/Volumes/PEFT Studio"

# Verify installation
if [ -d "/Applications/PEFT Studio.app" ]; then
    echo "Installation successful"
else
    echo "Installation failed"
    exit 1
fi

# Launch and check
open "/Applications/PEFT Studio.app"
sleep 10
if pgrep -f "PEFT Studio" > /dev/null; then
    echo "Application launched successfully"
    pkill -f "PEFT Studio"
else
    echo "Application failed to launch"
    exit 1
fi
```

### Linux (Bash)
```bash
#!/bin/bash

# For AppImage
chmod +x PEFT-Studio-1.0.0.AppImage

# Launch in background
./PEFT-Studio-1.0.0.AppImage &
APP_PID=$!

# Wait and check
sleep 10
if ps -p $APP_PID > /dev/null; then
    echo "Application launched successfully"
    kill $APP_PID
else
    echo "Application failed to launch"
    exit 1
fi
```

## Common Issues and Solutions

### Windows

**Issue:** "Windows protected your PC" message
**Solution:** Click "More info" → "Run anyway" or sign the installer

**Issue:** Installation fails with permission error
**Solution:** Run installer as Administrator

**Issue:** Application doesn't start
**Solution:** Check Windows Event Viewer for errors, verify .NET Framework installed

### macOS

**Issue:** "App is damaged and can't be opened"
**Solution:** Remove quarantine attribute: `xattr -cr /Applications/PEFT\ Studio.app`

**Issue:** Gatekeeper blocks application
**Solution:** Right-click → Open (first time only)

**Issue:** Application crashes on launch
**Solution:** Check Console.app for crash reports, verify macOS version compatibility

### Linux

**Issue:** AppImage won't run
**Solution:** Install FUSE: `sudo apt-get install fuse libfuse2`

**Issue:** Missing dependencies
**Solution:** Install required libraries: `sudo apt-get install libgtk-3-0 libnotify4 libnss3`

**Issue:** Permission denied
**Solution:** Make executable: `chmod +x PEFT-Studio.AppImage`

## Checklist for Release

Before releasing installers publicly:

- [ ] All platforms tested on clean systems
- [ ] Installation works without errors
- [ ] Application launches successfully
- [ ] Core features verified working
- [ ] Performance is acceptable
- [ ] Uninstallation works cleanly
- [ ] No critical bugs found
- [ ] Test reports documented
- [ ] Known issues documented
- [ ] Release notes prepared

## Contact

If you encounter issues during testing:
- Open an issue on GitHub
- Include test report
- Attach relevant logs
- Describe steps to reproduce

