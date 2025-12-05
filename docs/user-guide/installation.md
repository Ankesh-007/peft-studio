# Installation Guide

Choose your platform and follow the installation steps below.

> **Note:** PEFT Studio now includes a bundled Python backend. You no longer need to install Python or any Python dependencies manually. Everything you need is included in the installer.

## Windows

1. **Download** PEFT-Studio-Setup.exe from [releases](https://github.com/Ankesh-007/peft-studio/releases/latest)
2. **Run the installer**
3. **Follow the installation wizard**
4. **Launch PEFT Studio** from the Start Menu

### System Requirements
- Windows 10 or later (64-bit)
- 8GB RAM minimum (16GB recommended for ML workloads)
- 5GB disk space for installation
- Additional space for models and datasets (varies by usage)
- No Python installation required

---

## macOS

1. **Download** PEFT-Studio.dmg from [releases](https://github.com/Ankesh-007/peft-studio/releases/latest)
2. **Open the DMG file**
3. **Drag PEFT Studio to Applications**
4. **Launch** from Applications folder

### System Requirements
- macOS 10.15 (Catalina) or later
- Apple Silicon (M1/M2/M3) or Intel processor
- 8GB RAM minimum (16GB recommended for ML workloads)
- 5GB disk space for installation
- Additional space for models and datasets (varies by usage)
- No Python installation required

---

## Linux

1. **Download** PEFT-Studio.AppImage from [releases](https://github.com/Ankesh-007/peft-studio/releases/latest)
2. **Make it executable:**
   ```bash
   chmod +x PEFT-Studio.AppImage
   ```
3. **Run:**
   ```bash
   ./PEFT-Studio.AppImage
   ```

### System Requirements
- Ubuntu 20.04+ or equivalent (64-bit)
- GLIBC 2.31 or higher
- 8GB RAM minimum (16GB recommended for ML workloads)
- 5GB disk space for installation
- Additional space for models and datasets (varies by usage)
- No Python installation required
- FUSE library (for AppImage): `sudo apt install libfuse2`

---

---

## What's Included

PEFT Studio now includes everything you need in a single installer:

- **Electron Application**: The desktop interface
- **Python Backend**: Bundled FastAPI server with all dependencies
- **ML Libraries**: PyTorch, Transformers, PEFT, and more
- **No Setup Required**: Just install and run

You don't need to:
- Install Python separately
- Manage pip or virtual environments
- Install ML libraries manually
- Configure environment variables

Everything is pre-configured and ready to use.

---

## Troubleshooting

### Windows

**Windows Defender blocks the installer:**
- Click "More info" and then "Run anyway"
- This is normal for new applications without established reputation

**Installation requires administrator privileges:**
- Right-click the installer and select "Run as administrator"
- Or choose a user directory during installation

**Antivirus software blocks the application:**
- Add PEFT Studio to your antivirus exclusions
- The bundled Python backend may trigger false positives

### macOS

**"App can't be opened because it is from an unidentified developer":**
- Right-click the app and select "Open"
- Click "Open" in the dialog
- This only needs to be done once

**"App is damaged and can't be opened":**
- Remove the quarantine attribute:
  ```bash
  xattr -cr /Applications/PEFT\ Studio.app
  ```

**Gatekeeper blocks execution:**
- Go to System Preferences → Security & Privacy
- Click "Open Anyway" for PEFT Studio

### Linux

**AppImage doesn't run:**
- Install FUSE library:
  ```bash
  sudo apt install libfuse2
  ```

**Permission denied:**
- Make sure the AppImage is executable:
  ```bash
  chmod +x PEFT-Studio.AppImage
  ```

**GLIBC version error:**
- Your Linux distribution is too old
- Upgrade to Ubuntu 20.04+ or equivalent

### General Issues

**Application won't start:**
1. Check system requirements are met
2. Ensure you have enough disk space (5GB+)
3. Check application logs:
   - Windows: `%APPDATA%\PEFT Studio\logs\`
   - macOS: `~/Library/Logs/PEFT Studio/`
   - Linux: `~/.config/PEFT Studio/logs/`

**Backend fails to start:**
- The application will show an error message
- Check logs for details
- Try reinstalling the application

**Slow startup:**
- First launch may take 10-15 seconds
- Subsequent launches should be faster
- Add PEFT Studio to antivirus exclusions

For more help, see the [Troubleshooting Guide](../reference/troubleshooting.md).

---

## Disk Space Requirements

PEFT Studio requires significant disk space due to the bundled ML libraries:

- **Installation**: ~2-3GB (includes Python backend and ML libraries)
- **Application Data**: ~500MB (settings, cache, logs)
- **Models**: Varies by model size (500MB - 10GB+ per model)
- **Datasets**: Varies by dataset size

**Recommended:** 10GB+ free disk space for comfortable usage

---

## Uninstallation

### Windows
1. Go to Settings → Apps → Apps & features
2. Find "PEFT Studio" and click Uninstall
3. Or use the uninstaller in the installation directory

### macOS
1. Drag PEFT Studio from Applications to Trash
2. Empty Trash
3. Optionally remove application data:
   ```bash
   rm -rf ~/Library/Application\ Support/PEFT\ Studio
   rm -rf ~/Library/Logs/PEFT\ Studio
   ```

### Linux
1. Delete the AppImage file
2. Optionally remove application data:
   ```bash
   rm -rf ~/.config/PEFT\ Studio
   ```

---

## Next Steps

After installation, check out the [Quick Start Guide](quick-start.md) to get started with PEFT Studio.

## Related Documentation

- [Quick Start Guide](quick-start.md) - Get started with PEFT Studio
- [Troubleshooting](../reference/troubleshooting.md) - Common issues and solutions
- [FAQ](../reference/faq.md) - Frequently asked questions
