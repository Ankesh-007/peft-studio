# Linux Installer Testing Guide

This guide provides detailed instructions for testing PEFT Studio installers on Linux.

## Prerequisites

- Ubuntu 18.04 or later (or equivalent distribution)
- Terminal access
- Internet connection for checksum verification
- `sha256sum` utility (usually pre-installed)

## Test Environment Setup

### Option 1: Physical Linux Machine
- Use a dedicated Linux machine for testing
- Ensure it's a clean environment (no previous PEFT Studio installations)

### Option 2: Linux Virtual Machine
- Use VirtualBox, VMware, or KVM
- Create an Ubuntu VM (recommended for testing)
- Take a snapshot before testing for easy rollback

### Recommended Test Distributions
- Ubuntu 20.04 LTS (primary target)
- Ubuntu 22.04 LTS
- Debian 11/12
- Fedora (latest)
- Arch Linux (for AppImage compatibility)

## Testing Procedure

### 1. Download Linux Installer

Navigate to the test release page and download:
- `PEFT-Studio-{version}.AppImage` (Universal Linux package)
- `peft-studio_{version}_amd64.deb` (Debian/Ubuntu package)
- `SHA256SUMS.txt` (Checksums file)

### 2. Verify Checksum

Open Terminal and navigate to the download directory:

```bash
# Calculate SHA256 hash of the AppImage
sha256sum PEFT-Studio-1.0.0-test.1.AppImage

# Display the expected hash from SHA256SUMS.txt
grep "PEFT-Studio.*\.AppImage" SHA256SUMS.txt

# Verify they match
sha256sum -c SHA256SUMS.txt 2>&1 | grep AppImage
```

**Verify**: The calculated hash matches the hash in SHA256SUMS.txt

**Expected Result**: ✅ Hashes match exactly

### 3. Test AppImage

#### 3.1 Make AppImage Executable

```bash
# Make the AppImage executable
chmod +x PEFT-Studio-1.0.0-test.1.AppImage

# Verify permissions
ls -lh PEFT-Studio-1.0.0-test.1.AppImage
```

**Expected Result**: ✅ File has execute permissions (-rwxr-xr-x)

#### 3.2 Run AppImage

**Test**: AppImage runs without installation

```bash
# Run the AppImage
./PEFT-Studio-1.0.0-test.1.AppImage
```

**Verify**:
1. Application window opens
2. No error messages in terminal
3. Application UI loads correctly
4. No missing library errors

**Expected Result**: ✅ Application launches successfully

#### 3.3 Test Desktop Integration

**Test**: AppImage integrates with desktop environment

1. Run AppImage for the first time
2. **Verify**: Desktop integration prompt may appear
3. If prompted, accept desktop integration
4. **Verify**: Application icon appears in application menu
5. **Verify**: .desktop file created in `~/.local/share/applications/`

```bash
# Check for desktop file
ls ~/.local/share/applications/ | grep -i peft

# View desktop file contents
cat ~/.local/share/applications/appimagekit_*-PEFT_Studio.desktop
```

**Expected Result**: ✅ Desktop integration works (if supported by AppImage)

#### 3.4 Test File Associations

**Test**: .peft file association (if configured)

```bash
# Check MIME type registration
xdg-mime query default application/x-peft-config

# Or check desktop file associations
grep -r "peft" ~/.local/share/applications/
```

**Expected Result**: ✅ File associations registered (if configured)

#### 3.5 Test AppImage Portability

**Test**: AppImage runs from any location

```bash
# Move AppImage to different location
mkdir ~/test-location
mv PEFT-Studio-*.AppImage ~/test-location/
cd ~/test-location

# Run from new location
./PEFT-Studio-*.AppImage
```

**Expected Result**: ✅ Application runs from any directory

#### 3.6 Test AppImage Cleanup

**Test**: AppImage doesn't leave system modifications

1. Run AppImage
2. Close application
3. Delete AppImage file
4. **Verify**: No system-wide changes (except optional desktop integration)

```bash
# Check for leftover files
ls ~/.config/peft-studio
ls ~/.local/share/peft-studio
```

**Expected Result**: ✅ Minimal system modifications

### 4. Test DEB Package

#### 4.1 Verify DEB Package

```bash
# Verify checksum
sha256sum peft-studio_1.0.0-test.1_amd64.deb
grep "peft-studio.*\.deb" SHA256SUMS.txt

# Inspect DEB package contents
dpkg-deb --info peft-studio_1.0.0-test.1_amd64.deb
dpkg-deb --contents peft-studio_1.0.0-test.1_amd64.deb
```

**Expected Result**: ✅ DEB package is valid and contains expected files

#### 4.2 Install DEB Package

**Test**: DEB package installs successfully

```bash
# Install using dpkg
sudo dpkg -i peft-studio_1.0.0-test.1_amd64.deb

# If dependency errors occur, fix them
sudo apt-get install -f
```

**Verify**:
1. Installation completes without errors
2. Dependencies are resolved automatically
3. No conflict messages

**Expected Result**: ✅ Package installs successfully

#### 4.3 Verify Installation

**Test**: Application is installed correctly

```bash
# Check if application is installed
dpkg -l | grep peft-studio

# Find installation location
dpkg -L peft-studio | grep -E "bin|opt|usr"

# Check desktop file
ls /usr/share/applications/ | grep -i peft
```

**Expected Result**: ✅ Application files are installed in correct locations

#### 4.4 Launch from Application Menu

**Test**: Application appears in application menu

1. Open application menu (GNOME Activities, KDE Menu, etc.)
2. Search for "PEFT Studio"
3. **Verify**: Application icon appears
4. Click to launch
5. **Verify**: Application opens

**Expected Result**: ✅ Application launches from menu

#### 4.5 Launch from Terminal

**Test**: Application can be launched from terminal

```bash
# Try to run application
peft-studio

# Or find the executable
which peft-studio

# Or check /opt or /usr/local
ls /opt/PEFT\ Studio/
ls /usr/local/bin/ | grep peft
```

**Expected Result**: ✅ Application can be launched from terminal

#### 4.6 Test Dependencies

**Test**: All dependencies are satisfied

```bash
# Check for missing dependencies
ldd /opt/PEFT\ Studio/peft-studio | grep "not found"

# Or check package dependencies
apt-cache depends peft-studio
```

**Expected Result**: ✅ No missing dependencies

### 5. Test Desktop Environment Integration

#### 5.1 GNOME

**Test**: GNOME integration

1. Launch application
2. **Verify**: Application appears in top bar
3. **Verify**: Application icon in dock/dash
4. **Verify**: Notifications work (if applicable)
5. **Verify**: Window controls work correctly

#### 5.2 KDE Plasma

**Test**: KDE integration

1. Launch application
2. **Verify**: Application appears in taskbar
3. **Verify**: System tray integration (if applicable)
4. **Verify**: Window decorations work
5. **Verify**: Notifications work (if applicable)

#### 5.3 XFCE

**Test**: XFCE integration

1. Launch application
2. **Verify**: Application appears in panel
3. **Verify**: Application menu entry exists
4. **Verify**: Basic functionality works

### 6. Test Auto-Update System

**Test**: Update check on startup

```bash
# Run application from terminal to see logs
./PEFT-Studio-*.AppImage 2>&1 | tee app.log

# Or for DEB installation
peft-studio 2>&1 | tee app.log

# Check logs for update check
grep -i "update" app.log
```

**Expected Result**: ✅ Update check occurs on startup

### 7. Uninstallation Testing

#### 7.1 Uninstall AppImage

**Test**: AppImage removal

```bash
# Simply delete the AppImage file
rm PEFT-Studio-*.AppImage

# Remove desktop integration (if present)
rm ~/.local/share/applications/appimagekit_*-PEFT_Studio.desktop

# Remove user data (optional)
rm -rf ~/.config/peft-studio
```

**Expected Result**: ✅ AppImage is removed cleanly

#### 7.2 Uninstall DEB Package

**Test**: DEB package uninstallation

```bash
# Remove package
sudo apt-get remove peft-studio

# Or completely remove including config files
sudo apt-get purge peft-studio

# Verify removal
dpkg -l | grep peft-studio
```

**Expected Result**: ✅ Package is uninstalled cleanly

#### 7.3 Verify Cleanup

**Test**: Check for leftover files

```bash
# Check for application files
ls /opt/ | grep -i peft
ls /usr/local/bin/ | grep -i peft

# Check for user data
ls ~/.config/ | grep -i peft
ls ~/.local/share/ | grep -i peft

# Check for desktop files
ls /usr/share/applications/ | grep -i peft
ls ~/.local/share/applications/ | grep -i peft
```

**Expected Result**: ✅ Application files removed, user data may remain

## Test Results Template

```markdown
## Linux Installer Test Results

**Test Date**: YYYY-MM-DD
**Tester**: [Your Name]
**Version**: v1.0.0-test.1
**Distribution**: Ubuntu 22.04 LTS (or other)
**Desktop Environment**: GNOME / KDE / XFCE / Other
**Architecture**: x86_64

### Checksum Verification
- [ ] AppImage checksum matches
- [ ] DEB package checksum matches

### AppImage
- [ ] AppImage is executable
- [ ] Application launches successfully
- [ ] Desktop integration works
- [ ] File associations work (if configured)
- [ ] Runs from any location
- [ ] Minimal system modifications

### DEB Package
- [ ] Package installs successfully
- [ ] Dependencies resolved automatically
- [ ] Application appears in menu
- [ ] Application launches from terminal
- [ ] No missing dependencies

### Desktop Integration
- [ ] Application menu entry exists
- [ ] Application icon displays correctly
- [ ] Window management works
- [ ] Notifications work (if applicable)

### Auto-Update
- [ ] Update check occurs on startup
- [ ] No update errors

### Uninstallation
- [ ] AppImage can be deleted
- [ ] DEB package uninstalls cleanly
- [ ] Application files removed

### Issues Found
[List any issues discovered during testing]

### Notes
[Any additional observations]
```

## Common Issues and Solutions

### AppImage Won't Run

**Issue**: "Permission denied" or "cannot execute binary file"

**Solutions**:
- Make executable: `chmod +x PEFT-Studio-*.AppImage`
- Check if FUSE is installed: `sudo apt-get install fuse libfuse2`
- Try extracting: `./PEFT-Studio-*.AppImage --appimage-extract`
- Run extracted: `./squashfs-root/AppRun`

### Missing Libraries

**Issue**: "error while loading shared libraries"

**Solutions**:
- Install missing libraries: `sudo apt-get install <library-name>`
- For AppImage, this shouldn't happen (self-contained)
- For DEB, run: `sudo apt-get install -f`

### DEB Installation Fails

**Issue**: Dependency conflicts or errors

**Solutions**:
- Update package lists: `sudo apt-get update`
- Fix broken dependencies: `sudo apt-get install -f`
- Check for conflicting packages: `dpkg -l | grep peft`
- Try force install: `sudo dpkg -i --force-all peft-studio_*.deb`

### Desktop Integration Doesn't Work

**Issue**: Application doesn't appear in menu

**Solutions**:
- Update desktop database: `update-desktop-database ~/.local/share/applications/`
- Manually create .desktop file
- Restart desktop environment
- Check .desktop file syntax

### Application Crashes on Launch

**Issue**: Application crashes immediately

**Solutions**:
- Run from terminal to see error messages
- Check for missing dependencies: `ldd /path/to/executable`
- Check system logs: `journalctl -xe`
- Verify graphics drivers are installed

## Distribution-Specific Notes

### Ubuntu/Debian
- DEB package is the recommended format
- AppImage works as fallback
- Use `apt` or `dpkg` for installation

### Fedora/RHEL
- AppImage is recommended (no RPM provided)
- May need to install FUSE: `sudo dnf install fuse fuse-libs`

### Arch Linux
- AppImage is recommended
- Can create AUR package for community
- May need `fuse2` package

### Other Distributions
- AppImage should work universally
- May need to install FUSE support
- Check distribution-specific requirements

## Next Steps

After completing Linux testing:
1. Document all test results
2. Report any bugs found
3. Proceed to [Auto-Update Testing](./test-auto-update.md)
4. Update test checklist in [Test Release Process](./test-release-process.md)
