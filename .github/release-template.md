# PEFT Studio {{VERSION}}

Released on {{RELEASE_DATE}}

## 📥 Downloads

Choose the installer for your platform:

### Windows
- **[PEFT Studio Setup {{VERSION}}.exe]({{WINDOWS_INSTALLER_URL}})** - Recommended for most users
  - Full installer with setup wizard
  - Creates desktop and start menu shortcuts
  - Automatic updates enabled
- **[PEFT Studio {{VERSION}} Portable.exe]({{WINDOWS_PORTABLE_URL}})** - No installation required
  - Runs without admin rights
  - Portable version for USB drives

### macOS
- **[PEFT Studio {{VERSION}}.dmg]({{MACOS_DMG_URL}})** - Recommended for most users
  - Standard macOS disk image
  - Drag and drop installation
- **[PEFT Studio {{VERSION}}.zip]({{MACOS_ZIP_URL}})** - Alternative format
  - ZIP archive with application bundle

### Linux
- **[PEFT Studio {{VERSION}}.AppImage]({{LINUX_APPIMAGE_URL}})** - Recommended for most users
  - Universal Linux application
  - No installation required
  - Works on most distributions
- **[PEFT Studio {{VERSION}}.deb]({{LINUX_DEB_URL}})** - For Debian/Ubuntu
  - Native package for Debian-based systems
  - Automatic dependency management

---

## 📋 Installation Instructions

### Windows Installation

1. **Download** the installer from the links above
2. **Run** the downloaded `.exe` file
3. **Follow** the installation wizard:
   - Choose installation directory (default: `C:\Program Files\PEFT Studio`)
   - Select components to install
   - Choose whether to create desktop shortcut
4. **Launch** PEFT Studio from the Start Menu or desktop shortcut

**Note for Portable Version:**
- Simply download and run the portable `.exe` file
- No installation required
- All settings stored in the same folder

**Security Warning:** If you see a Windows SmartScreen warning, click "More info" and then "Run anyway". This occurs because the application is not yet code-signed.

### macOS Installation

1. **Download** the `.dmg` file from the links above
2. **Open** the downloaded DMG file
3. **Drag** the PEFT Studio icon to the Applications folder
4. **Launch** PEFT Studio from Applications or Spotlight

**Security Note:** On first launch, you may see a security warning. To bypass:
- Right-click (or Control-click) the application
- Select "Open" from the context menu
- Click "Open" in the dialog

**Alternative (ZIP):**
- Download and extract the `.zip` file
- Move the extracted app to Applications folder
- Follow the same security steps above

**System Requirements:** macOS 10.15 (Catalina) or later

### Linux Installation

#### AppImage (Recommended)

1. **Download** the `.AppImage` file from the links above
2. **Make it executable:**
   ```bash
   chmod +x PEFT-Studio-{{VERSION}}.AppImage
   ```
3. **Run** the AppImage:
   ```bash
   ./PEFT-Studio-{{VERSION}}.AppImage
   ```

**Desktop Integration:** On first run, the AppImage will offer to integrate with your desktop environment (adds menu entries and file associations).

#### Debian/Ubuntu Package

1. **Download** the `.deb` file from the links above
2. **Install** using dpkg:
   ```bash
   sudo dpkg -i PEFT-Studio-{{VERSION}}.deb
   sudo apt-get install -f  # Install dependencies if needed
   ```
3. **Launch** from your application menu or run `peft-studio` in terminal

**System Requirements:** Ubuntu 20.04+ or Debian 11+

---

## ✨ What's New

{{CHANGELOG}}

---

## 🔒 Checksum Verification

To verify the integrity of your download, compare the SHA256 checksum of the downloaded file with the values below:

### SHA256 Checksums

```
{{CHECKSUMS}}
```

### How to Verify Checksums

#### Windows (PowerShell)

```powershell
Get-FileHash "PEFT-Studio-Setup-{{VERSION}}.exe" -Algorithm SHA256
```

Compare the output hash with the checksum listed above.

#### Windows (Command Prompt with certutil)

```cmd
certutil -hashfile "PEFT-Studio-Setup-{{VERSION}}.exe" SHA256
```

#### macOS / Linux

```bash
shasum -a 256 PEFT-Studio-{{VERSION}}.dmg
# or
sha256sum PEFT-Studio-{{VERSION}}.AppImage
```

Compare the output with the checksum listed above.

#### GUI Tools

- **Windows:** [HashTab](http://implbits.com/products/hashtab/) - Adds checksum tab to file properties
- **macOS:** [HashTab for Mac](https://hashtab.en.softonic.com/mac) or built-in terminal
- **Linux:** Most file managers have checksum plugins, or use terminal

**⚠️ Security Warning:** If the checksums do not match, **do not install the file**. The file may have been corrupted or tampered with. Please report this issue immediately.

---

## 💻 System Requirements

### Minimum Requirements

- **Windows:** Windows 10 (64-bit) or later
- **macOS:** macOS 10.15 (Catalina) or later
- **Linux:** Ubuntu 20.04+, Debian 11+, or equivalent
- **RAM:** 4 GB minimum, 8 GB recommended
- **Disk Space:** 500 MB for application, additional space for models and datasets
- **GPU:** Optional but recommended for training (CUDA-compatible NVIDIA GPU)

### Recommended Requirements

- **RAM:** 16 GB or more
- **GPU:** NVIDIA GPU with 8GB+ VRAM
- **Disk Space:** 10 GB+ for models and datasets

---

## 🆘 Support & Troubleshooting

### Common Issues

**Installation fails on Windows:**
- Ensure you have administrator privileges
- Temporarily disable antivirus software
- Check that you have enough disk space

**macOS security warning:**
- Follow the security bypass instructions above
- The app is not yet notarized by Apple

**Linux AppImage won't run:**
- Ensure FUSE is installed: `sudo apt install fuse libfuse2`
- Make sure the file is executable: `chmod +x *.AppImage`

### Getting Help

- **Documentation:** [https://github.com/YOUR_USERNAME/peft-studio/tree/main/docs](https://github.com/YOUR_USERNAME/peft-studio/tree/main/docs)
- **Issues:** [Report a bug](https://github.com/YOUR_USERNAME/peft-studio/issues/new?template=bug_report.md)
- **Discussions:** [Ask questions](https://github.com/YOUR_USERNAME/peft-studio/discussions)
- **Troubleshooting Guide:** [View detailed troubleshooting](https://github.com/YOUR_USERNAME/peft-studio/blob/main/docs/reference/troubleshooting.md)

---

## 🔄 Automatic Updates

PEFT Studio includes an automatic update system. When a new version is available:

1. You'll see a notification in the application
2. Click "Update" to download and install automatically
3. The application will restart with the new version

You can check for updates manually in **Settings → About → Check for Updates**.

---

## 📝 Release Notes

For detailed release notes and changelog, see [CHANGELOG.md](https://github.com/YOUR_USERNAME/peft-studio/blob/main/CHANGELOG.md).

---

## 🙏 Acknowledgments

Thank you to all contributors and users who helped make this release possible!

---

**Full Changelog:** [{{PREVIOUS_TAG}}...{{TAG_NAME}}](https://github.com/YOUR_USERNAME/peft-studio/compare/{{PREVIOUS_TAG}}...{{TAG_NAME}})
