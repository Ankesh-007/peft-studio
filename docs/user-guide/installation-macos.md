# macOS Installation Guide

This guide provides step-by-step instructions for installing PEFT Studio on macOS.

## System Requirements

**Minimum:**
- macOS 10.13 (High Sierra) or later
- 8 GB RAM
- 10 GB free disk space
- 64-bit Intel or Apple Silicon (M1/M2/M3) processor

**Recommended for Training:**
- macOS 12 (Monterey) or later
- 32 GB RAM or more
- 100+ GB free disk space (SSD)
- Apple Silicon Mac (M1 Pro/Max/Ultra, M2 Pro/Max/Ultra, M3 Pro/Max) for GPU acceleration

## Download

1. Visit the [PEFT Studio Releases page](https://github.com/Ankesh-007/peft-studio/releases/latest)
2. Download the appropriate macOS installer:
   - **PEFT-Studio-{version}-arm64.dmg** - For Apple Silicon Macs (M1/M2/M3)
   - **PEFT-Studio-{version}-x64.dmg** - For Intel Macs
   - **PEFT-Studio-{version}-arm64.zip** - ZIP archive for Apple Silicon
   - **PEFT-Studio-{version}-x64.zip** - ZIP archive for Intel
3. **Important:** Download the `SHA256SUMS.txt` file for checksum verification

**Not sure which one?** Click the Apple menu () → About This Mac:
- If you see "Apple M1", "Apple M2", or "Apple M3" → Download **arm64** version
- If you see "Intel Core" → Download **x64** version

## Verify Download Integrity (Recommended)

Before installing, verify the file hasn't been corrupted or tampered with:

```bash
shasum -a 256 PEFT-Studio-1.0.0-arm64.dmg
```

Compare the output with the checksum in `SHA256SUMS.txt` or the release notes.

**For detailed verification instructions, see the [Checksum Verification Guide](checksum-verification.md).**

**⚠️ Security Warning:** If checksums don't match, DO NOT install the file. Delete it and download again.

## Installation Methods

### Method 1: DMG Installer (Recommended)

The DMG provides the standard macOS installation experience.

#### Step 1: Download the DMG

Download the appropriate `.dmg` file for your Mac (arm64 or x64).

#### Step 2: Open the DMG

1. Double-click the downloaded `.dmg` file
2. A new window will open showing the PEFT Studio icon and an Applications folder shortcut

#### Step 3: Install the Application

1. Drag the **PEFT Studio** icon to the **Applications** folder
2. Wait for the copy to complete (usually a few seconds)
3. Eject the DMG by clicking the eject button in Finder or dragging it to the Trash

#### Step 4: Launch PEFT Studio

1. Open Finder
2. Go to Applications
3. Double-click **PEFT Studio**
4. If you see a security warning, see [Security Warning](#security-warning-app-from-unidentified-developer) below

### Method 2: ZIP Archive

The ZIP archive is useful for automation or if you prefer manual installation.

#### Step 1: Download the ZIP

Download the appropriate `.zip` file for your Mac (arm64 or x64).

#### Step 2: Extract the Archive

1. Double-click the `.zip` file to extract it
2. A folder containing **PEFT Studio.app** will be created

#### Step 3: Move to Applications

1. Open Finder
2. Drag **PEFT Studio.app** to your Applications folder
3. Launch from Applications

## First Launch

When you first launch PEFT Studio:

1. **Security Warning**: You may see a warning about an unidentified developer (see [Troubleshooting](#security-warning-app-from-unidentified-developer))
2. **Welcome Screen**: Read the welcome message and click "Get Started"
3. **Platform Connections**: Add your HuggingFace token (optional but recommended)
   - Go to Settings → Platform Connections
   - Click "Add Connection"
   - Select "HuggingFace"
   - Enter your API token
4. **GPU Detection**: PEFT Studio will automatically detect Apple Silicon GPU if available
5. **Ready to Use**: You're all set! Start by browsing models or uploading a dataset

## Verifying Installation

### Check Version

1. Open PEFT Studio
2. Click **PEFT Studio** in the menu bar → **About PEFT Studio**
3. Verify the version number matches your download

### Test GPU Detection (Apple Silicon Only)

If you have an Apple Silicon Mac:

1. Open PEFT Studio
2. Go to Settings → System
3. Check the "GPU Information" section
4. You should see your Apple GPU cores

**Note:** Intel Macs don't have GPU acceleration for ML training in PEFT Studio.

## Updating PEFT Studio

### Automatic Updates

PEFT Studio automatically checks for updates on startup:

1. When an update is available, you'll see a notification
2. Click "Download Update"
3. The update will download in the background
4. Click "Install and Restart" when ready
5. PEFT Studio will restart with the new version

### Manual Updates

If auto-update fails or you prefer manual updates:

1. Visit the [releases page](https://github.com/Ankesh-007/peft-studio/releases/latest)
2. Download the latest DMG or ZIP for your Mac
3. Follow the installation steps above (it will replace your existing installation)

## Uninstalling PEFT Studio

### Remove the Application

1. Open Finder
2. Go to Applications
3. Find **PEFT Studio**
4. Drag it to the Trash (or right-click → Move to Trash)
5. Empty the Trash

### Remove User Data (Optional)

To completely remove all settings and data:

1. Open Finder
2. Press **Cmd + Shift + G** (Go to Folder)
3. Enter: `~/Library/Application Support/peft-studio`
4. Delete the folder
5. Also delete: `~/Library/Preferences/com.peftstudio.app.plist`

## Troubleshooting

### Security Warning: App from Unidentified Developer

**Issue:** macOS shows "PEFT Studio can't be opened because it is from an unidentified developer"

**Why:** PEFT Studio is not yet notarized by Apple, so macOS Gatekeeper blocks it by default.

**Solution - Method 1 (Recommended):**
1. Open **System Settings** (or System Preferences)
2. Go to **Privacy & Security**
3. Scroll down to the **Security** section
4. You should see a message about PEFT Studio being blocked
5. Click **Open Anyway**
6. Click **Open** in the confirmation dialog
7. PEFT Studio will launch

**Solution - Method 2 (Command Line):**
1. Open Terminal
2. Run:
   ```bash
   xattr -cr /Applications/PEFT\ Studio.app
   ```
3. Try launching PEFT Studio again

**Solution - Method 3 (Right-Click):**
1. Open Finder → Applications
2. **Right-click** (or Control-click) on PEFT Studio
3. Select **Open**
4. Click **Open** in the dialog
5. PEFT Studio will launch

**Note:** You only need to do this once. After the first launch, macOS will remember your choice.

### Application Won't Start

**Issue:** PEFT Studio doesn't launch or crashes immediately

**Solutions:**

1. **Check macOS Version:**
   - Verify you're running macOS 10.13 or later
   - Update macOS if needed

2. **Check Architecture:**
   - Ensure you downloaded the correct version (arm64 for Apple Silicon, x64 for Intel)
   - Download the correct version if needed

3. **Check Logs:**
   - Open Console app (Applications → Utilities → Console)
   - Search for "PEFT Studio"
   - Look for error messages

4. **Reinstall:**
   - Delete PEFT Studio from Applications
   - Download the latest version
   - Install again

### Rosetta 2 Required (Intel Apps on Apple Silicon)

**Issue:** "To open PEFT Studio, you need to install Rosetta"

**Why:** You downloaded the Intel (x64) version on an Apple Silicon Mac.

**Solution - Option 1 (Install Rosetta):**
1. Click **Install** when prompted
2. Enter your password
3. Wait for Rosetta to install
4. Launch PEFT Studio again

**Solution - Option 2 (Download Correct Version):**
1. Delete the Intel version
2. Download the **arm64** version instead
3. Install and launch

**Note:** The arm64 version runs natively on Apple Silicon and is faster.

### Slow Performance

**Issue:** PEFT Studio runs slowly or freezes

**Solutions:**

1. **Close Other Applications:**
   - Close unnecessary programs
   - Free up RAM and CPU resources

2. **Check Activity Monitor:**
   - Open Activity Monitor (Applications → Utilities)
   - Check CPU, Memory, and Disk usage
   - If maxed out, upgrade hardware or reduce workload

3. **Use Apple Silicon Mac:**
   - Training on Intel Macs is slower (CPU only)
   - Apple Silicon Macs have GPU acceleration

4. **Reduce Dataset Size:**
   - Start with smaller datasets for testing
   - Use data sampling for large datasets

### Permission Denied Errors

**Issue:** PEFT Studio can't access files or folders

**Solutions:**

1. **Grant Full Disk Access:**
   - Open System Settings → Privacy & Security
   - Click **Full Disk Access**
   - Click the **+** button
   - Navigate to Applications and select PEFT Studio
   - Enable the checkbox

2. **Grant Specific Permissions:**
   - When PEFT Studio requests access to a folder, click **OK**
   - macOS will remember your choice

### Network Connection Issues

**Issue:** Can't download models or check for updates

**Solutions:**

1. **Check Internet Connection:**
   - Verify you're connected to the internet
   - Try opening a website in Safari

2. **Check Firewall:**
   - Open System Settings → Network → Firewall
   - If enabled, add PEFT Studio to allowed apps

3. **Check VPN:**
   - Some VPNs block certain connections
   - Try disabling VPN temporarily

### Verifying Downloads

To ensure your download isn't corrupted or tampered with:

1. Download the `SHA256SUMS.txt` file from the releases page
2. Open Terminal
3. Navigate to your downloads folder:
   ```bash
   cd ~/Downloads
   ```
4. Calculate the checksum:
   ```bash
   shasum -a 256 PEFT-Studio-*.dmg
   ```
5. Compare the output with the checksum in `SHA256SUMS.txt`
6. They should match exactly

## Apple Silicon Specific Notes

### GPU Acceleration

Apple Silicon Macs (M1/M2/M3) have integrated GPUs that can accelerate ML training:

- **M1**: 7-8 GPU cores
- **M1 Pro**: 14-16 GPU cores
- **M1 Max**: 24-32 GPU cores
- **M1 Ultra**: 48-64 GPU cores
- **M2**: 8-10 GPU cores
- **M2 Pro**: 16-19 GPU cores
- **M2 Max**: 30-38 GPU cores
- **M2 Ultra**: 60-76 GPU cores
- **M3/M3 Pro/M3 Max**: Similar or better

PEFT Studio automatically uses the GPU when available.

### Memory Considerations

Apple Silicon Macs use unified memory (shared between CPU and GPU):

- **8 GB**: Minimum, suitable for small models and datasets
- **16 GB**: Good for most use cases
- **32 GB+**: Recommended for large models and datasets

### Performance Tips

1. **Close Background Apps**: Free up unified memory
2. **Use Native arm64 Version**: Don't use Rosetta 2
3. **Keep macOS Updated**: Apple improves ML performance with each update
4. **Monitor Memory Pressure**: Use Activity Monitor to check memory usage

## Getting Help

If you're still having issues:

1. **Check Documentation:**
   - [Troubleshooting Guide](../reference/troubleshooting.md)
   - [FAQ](../reference/faq.md)

2. **Search Existing Issues:**
   - [GitHub Issues](https://github.com/Ankesh-007/peft-studio/issues)
   - Someone may have already solved your problem

3. **Ask for Help:**
   - [GitHub Discussions](https://github.com/Ankesh-007/peft-studio/discussions)
   - Provide details: macOS version, Mac model, error messages, logs

4. **Report a Bug:**
   - [Open an issue](https://github.com/Ankesh-007/peft-studio/issues/new?template=bug_report.md)
   - Include: macOS version, Mac model (Intel/Apple Silicon), error messages, logs

## Next Steps

Now that PEFT Studio is installed:

1. **[Quick Start Guide](quick-start.md)** - Get started with your first fine-tuning job
2. **[Platform Connections](platform-connections.md)** - Connect to HuggingFace and cloud providers
3. **[Training Configuration](training-configuration.md)** - Learn how to configure training runs

---

**Need more help?** Visit our [support page](../../README.md#-getting-help) for additional resources.
