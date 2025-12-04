# Windows Installation Guide

This guide provides step-by-step instructions for installing PEFT Studio on Windows.

## System Requirements

**Minimum:**
- Windows 10 (64-bit) or later
- 8 GB RAM
- 10 GB free disk space
- 64-bit processor with 4+ cores

**Recommended for Training:**
- Windows 10/11 (64-bit)
- 32 GB RAM or more
- 100+ GB free disk space (SSD recommended)
- NVIDIA GPU with 16+ GB VRAM and CUDA support

## Download

1. Visit the [PEFT Studio Releases page](https://github.com/Ankesh-007/peft-studioreleases/latest)
2. Download one of the Windows installers:
   - **PEFT-Studio-Setup-{version}.exe** - Standard installer (recommended)
   - **PEFT-Studio-Portable-{version}.exe** - Portable version (no installation)
3. **Important:** Download the `SHA256SUMS.txt` file for checksum verification

## Verify Download Integrity (Recommended)

Before installing, verify the file hasn't been corrupted or tampered with:

```powershell
Get-FileHash "PEFT-Studio-Setup-1.0.0.exe" -Algorithm SHA256
```

Compare the output with the checksum in `SHA256SUMS.txt` or the release notes.

**For detailed verification instructions, see the [Checksum Verification Guide](checksum-verification.md).**

**⚠️ Security Warning:** If checksums don't match, DO NOT install the file. Delete it and download again.

## Installation Methods

### Method 1: Standard Installer (Recommended)

The standard installer provides the best experience with auto-updates and proper system integration.

#### Step 1: Download the Installer

Download `PEFT-Studio-Setup-{version}.exe` from the releases page.

#### Step 2: Run the Installer

1. Double-click the downloaded `.exe` file
2. If Windows SmartScreen appears (see [Troubleshooting](#windows-smartscreen-warning) below), click "More info" → "Run anyway"
3. The installation wizard will open

#### Step 3: Choose Installation Location

1. Click "Next" on the welcome screen
2. Choose your installation directory (default: `C:\Users\{YourName}\AppData\Local\Programs\peft-studio`)
3. Click "Next"

#### Step 4: Select Additional Options

Choose your preferences:
- ✅ Create a desktop shortcut (recommended)
- ✅ Create a Start Menu shortcut (recommended)
- ✅ Add to PATH (optional - allows running from command line)

Click "Next"

#### Step 5: Complete Installation

1. Review your choices
2. Click "Install"
3. Wait for the installation to complete (usually 1-2 minutes)
4. Click "Finish" to launch PEFT Studio

### Method 2: Portable Version

The portable version doesn't require installation and can run from any location (USB drive, external drive, etc.).

#### Step 1: Download Portable Version

Download `PEFT-Studio-Portable-{version}.exe` from the releases page.

#### Step 2: Choose Location

1. Create a folder where you want to run PEFT Studio (e.g., `C:\PortableApps\PEFT-Studio`)
2. Move the downloaded `.exe` file to this folder

#### Step 3: Run the Application

1. Double-click `PEFT-Studio-Portable-{version}.exe`
2. If Windows SmartScreen appears, click "More info" → "Run anyway"
3. PEFT Studio will launch without installation

**Note:** The portable version stores all settings and data in the same folder as the executable.

## First Launch

When you first launch PEFT Studio:

1. **Welcome Screen**: Read the welcome message and click "Get Started"
2. **Platform Connections**: Add your HuggingFace token (optional but recommended)
   - Go to Settings → Platform Connections
   - Click "Add Connection"
   - Select "HuggingFace"
   - Enter your API token
3. **GPU Detection**: PEFT Studio will automatically detect your NVIDIA GPU if available
4. **Ready to Use**: You're all set! Start by browsing models or uploading a dataset

## Verifying Installation

### Check Version

1. Open PEFT Studio
2. Click the menu icon (☰) in the top-left
3. Go to Settings → About
4. Verify the version number matches your download

### Test GPU Detection

If you have an NVIDIA GPU:

1. Open PEFT Studio
2. Go to Settings → System
3. Check the "GPU Information" section
4. You should see your GPU model and VRAM

If your GPU isn't detected, see [GPU Not Detected](#gpu-not-detected) in Troubleshooting.

## Updating PEFT Studio

### Automatic Updates (Standard Installer Only)

PEFT Studio automatically checks for updates on startup:

1. When an update is available, you'll see a notification
2. Click "Download Update"
3. The update will download in the background
4. Click "Install and Restart" when ready
5. PEFT Studio will restart with the new version

### Manual Updates

For portable version or if auto-update fails:

1. Visit the [releases page](https://github.com/Ankesh-007/peft-studioreleases/latest)
2. Download the latest installer
3. Run the new installer (it will update your existing installation)

## Uninstalling PEFT Studio

### Standard Installation

**Method 1: Windows Settings**
1. Open Windows Settings (Win + I)
2. Go to Apps → Apps & features
3. Search for "PEFT Studio"
4. Click "Uninstall"
5. Follow the uninstallation wizard

**Method 2: Control Panel**
1. Open Control Panel
2. Go to Programs → Programs and Features
3. Find "PEFT Studio"
4. Right-click and select "Uninstall"
5. Follow the uninstallation wizard

### Portable Version

Simply delete the folder containing the portable executable.

### Removing User Data

The uninstaller keeps your settings and data by default. To remove everything:

1. Uninstall PEFT Studio (see above)
2. Delete the data folder:
   - Standard: `C:\Users\{YourName}\AppData\Roaming\peft-studio`
   - Portable: Same folder as the executable

## Troubleshooting

### Windows SmartScreen Warning

**Issue:** Windows shows "Windows protected your PC" warning

**Why:** PEFT Studio is not yet code-signed, so Windows doesn't recognize the publisher.

**Solution:**
1. Click "More info" on the SmartScreen dialog
2. Click "Run anyway"
3. The application will launch normally

This is safe - the warning appears for all unsigned applications. We're working on code signing for future releases.

### Installation Fails

**Issue:** Installer shows an error or fails to complete

**Solutions:**

1. **Run as Administrator:**
   - Right-click the installer
   - Select "Run as administrator"
   - Try installing again

2. **Check Disk Space:**
   - Ensure you have at least 10 GB free space
   - Try installing to a different drive

3. **Disable Antivirus Temporarily:**
   - Some antivirus software blocks installers
   - Temporarily disable it during installation
   - Re-enable after installation completes

4. **Download Again:**
   - The download may be corrupted
   - Delete the installer and download again
   - Verify the checksum (see [Verifying Downloads](#verifying-downloads))

### Application Won't Start

**Issue:** PEFT Studio doesn't launch after installation

**Solutions:**

1. **Check System Requirements:**
   - Verify you're running Windows 10 64-bit or later
   - Ensure you have at least 8 GB RAM

2. **Run as Administrator:**
   - Right-click the PEFT Studio shortcut
   - Select "Run as administrator"

3. **Check Logs:**
   - Open File Explorer
   - Navigate to `%APPDATA%\peft-studio\logs`
   - Open the latest log file
   - Look for error messages

4. **Reinstall:**
   - Uninstall PEFT Studio
   - Download the latest version
   - Install again

### GPU Not Detected

**Issue:** PEFT Studio doesn't detect your NVIDIA GPU

**Solutions:**

1. **Update NVIDIA Drivers:**
   - Visit [NVIDIA Driver Downloads](https://www.nvidia.com/Download/index.aspx)
   - Download and install the latest drivers for your GPU
   - Restart your computer

2. **Install CUDA Toolkit:**
   - Download [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads)
   - Install version 11.8 or later
   - Restart your computer

3. **Check GPU in Device Manager:**
   - Open Device Manager (Win + X → Device Manager)
   - Expand "Display adapters"
   - Verify your NVIDIA GPU is listed and enabled

4. **Verify CUDA Installation:**
   - Open Command Prompt
   - Run: `nvidia-smi`
   - You should see your GPU information
   - If not, reinstall NVIDIA drivers

### Slow Performance

**Issue:** PEFT Studio runs slowly or freezes

**Solutions:**

1. **Close Other Applications:**
   - Close unnecessary programs
   - Free up RAM and CPU resources

2. **Check System Resources:**
   - Open Task Manager (Ctrl + Shift + Esc)
   - Check CPU, RAM, and disk usage
   - If maxed out, upgrade hardware or reduce workload

3. **Use GPU for Training:**
   - Ensure GPU is detected (see above)
   - Training on CPU is much slower

4. **Reduce Dataset Size:**
   - Start with smaller datasets for testing
   - Use data sampling for large datasets

### Firewall or Antivirus Blocking

**Issue:** Firewall or antivirus blocks PEFT Studio

**Solutions:**

1. **Add Exception:**
   - Open your antivirus/firewall settings
   - Add PEFT Studio to the allowed applications list
   - Path: `C:\Users\{YourName}\AppData\Local\Programs\peft-studio`

2. **Allow Network Access:**
   - PEFT Studio needs internet access for:
     - Downloading models from HuggingFace
     - Checking for updates
     - Connecting to cloud platforms
   - Allow both inbound and outbound connections

### Verifying Downloads

To ensure your download isn't corrupted or tampered with:

1. Download the `SHA256SUMS.txt` file from the releases page
2. Open PowerShell in your downloads folder
3. Run:
   ```powershell
   Get-FileHash "PEFT-Studio-Setup-{version}.exe" -Algorithm SHA256
   ```
4. Compare the output with the checksum in `SHA256SUMS.txt`
5. They should match exactly

## Getting Help

If you're still having issues:

1. **Check Documentation:**
   - [Troubleshooting Guide](../reference/troubleshooting.md)
   - [FAQ](../reference/faq.md)

2. **Search Existing Issues:**
   - [GitHub Issues](https://github.com/Ankesh-007/peft-studioissues)
   - Someone may have already solved your problem

3. **Ask for Help:**
   - [GitHub Discussions](https://github.com/Ankesh-007/peft-studiodiscussions)
   - Provide details: Windows version, error messages, logs

4. **Report a Bug:**
   - [Open an issue](https://github.com/Ankesh-007/peft-studioissues/new?template=bug_report.md)
   - Include: Windows version, installation method, error messages, logs

## Next Steps

Now that PEFT Studio is installed:

1. **[Quick Start Guide](quick-start.md)** - Get started with your first fine-tuning job
2. **[Platform Connections](platform-connections.md)** - Connect to HuggingFace and cloud providers
3. **[Training Configuration](training-configuration.md)** - Learn how to configure training runs

---

**Need more help?** Visit our [support page](../../README.md#-getting-help) for additional resources.
