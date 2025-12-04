# Linux Installation Guide

This guide provides step-by-step instructions for installing PEFT Studio on Linux.

## System Requirements

**Minimum:**
- Linux distribution: Ubuntu 18.04+, Fedora 28+, Debian 10+, or equivalent
- 8 GB RAM
- 10 GB free disk space
- 64-bit x86_64 processor

**Recommended for Training:**
- Ubuntu 22.04 LTS or later
- 32 GB RAM or more
- 100+ GB free disk space (SSD recommended)
- NVIDIA GPU with 16+ GB VRAM and CUDA support

## Download

1. Visit the [PEFT Studio Releases page](https://github.com/Ankesh-007/peft-studio/releases/latest)
2. Download the appropriate Linux installer:
   - **PEFT-Studio-{version}-x64.AppImage** - Universal format (recommended)
   - **PEFT-Studio-{version}-amd64.deb** - For Debian/Ubuntu
3. **Important:** Download the `SHA256SUMS.txt` file for checksum verification

## Verify Download Integrity (Recommended)

Before installing, verify the file hasn't been corrupted or tampered with:

```bash
sha256sum PEFT-Studio-1.0.0-x64.AppImage
```

Or verify all files at once:

```bash
sha256sum -c SHA256SUMS.txt
```

Compare the output with the checksum in `SHA256SUMS.txt` or the release notes.

**For detailed verification instructions, see the [Checksum Verification Guide](checksum-verification.md).**

**⚠️ Security Warning:** If checksums don't match, DO NOT install the file. Delete it and download again.

## Installation Methods

### Method 1: AppImage (Recommended)

AppImage is a universal format that works on all Linux distributions without installation.

#### Step 1: Download the AppImage

Download `PEFT-Studio-{version}-x64.AppImage` from the releases page.

#### Step 2: Make it Executable

Open a terminal in your downloads folder and run:

```bash
chmod +x PEFT-Studio-*.AppImage
```

Or using the GUI:
1. Right-click the AppImage file
2. Select **Properties**
3. Go to the **Permissions** tab
4. Check **Allow executing file as program**
5. Click **OK**

#### Step 3: Run the AppImage

Double-click the AppImage file, or run from terminal:

```bash
./PEFT-Studio-*.AppImage
```

#### Step 4: (Optional) Integrate with Desktop

To add PEFT Studio to your application menu:

1. Run the AppImage once
2. It will ask if you want to integrate with your system
3. Click **Yes** to add it to your application menu
4. You can now launch it like any other application

**Manual Integration:**

```bash
# Move AppImage to a permanent location
mkdir -p ~/.local/bin
mv PEFT-Studio-*.AppImage ~/.local/bin/peft-studio

# Create desktop entry
cat > ~/.local/share/applications/peft-studio.desktop << EOF
[Desktop Entry]
Name=PEFT Studio
Comment=Parameter-Efficient Fine-Tuning Studio
Exec=$HOME/.local/bin/peft-studio
Icon=peft-studio
Terminal=false
Type=Application
Categories=Development;Science;
EOF

# Update desktop database
update-desktop-database ~/.local/share/applications
```

### Method 2: Debian Package (Ubuntu/Debian)

For Debian-based distributions (Ubuntu, Debian, Linux Mint, Pop!_OS, etc.).

#### Step 1: Download the DEB Package

Download `PEFT-Studio-{version}-amd64.deb` from the releases page.

#### Step 2: Install the Package

**Using GUI:**
1. Double-click the `.deb` file
2. Click **Install** in the Software Center
3. Enter your password when prompted

**Using Terminal:**

```bash
# Install the package
sudo dpkg -i PEFT-Studio-*.deb

# Fix dependencies if needed
sudo apt-get install -f
```

#### Step 3: Launch PEFT Studio

- Search for "PEFT Studio" in your application menu
- Or run from terminal: `peft-studio`

### Method 3: Build from Source

For advanced users or unsupported distributions.

#### Prerequisites

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y git nodejs npm python3 python3-pip build-essential

# Fedora
sudo dnf install -y git nodejs npm python3 python3-pip gcc-c++ make

# Arch Linux
sudo pacman -S git nodejs npm python python-pip base-devel
```

#### Build Steps

```bash
# Clone the repository
git clone https://github.com/Ankesh-007/peft-studio.git
cd peft-studio

# Install Node.js dependencies
npm install

# Build the frontend
npm run build

# Build the AppImage
npm run package:linux
```

The AppImage will be created in the `release/` directory.

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

### AppImage

1. Download the latest AppImage from the [releases page](https://github.com/Ankesh-007/peft-studio/releases/latest)
2. Replace your old AppImage with the new one
3. Make it executable: `chmod +x PEFT-Studio-*.AppImage`
4. Run the new version

### Debian Package

```bash
# Download the latest .deb package
wget https://github.com/Ankesh-007/peft-studio/releases/latest/download/PEFT-Studio-{version}-amd64.deb

# Install the update
sudo dpkg -i PEFT-Studio-*.deb
```

## Uninstalling PEFT Studio

### AppImage

Simply delete the AppImage file:

```bash
rm ~/.local/bin/peft-studio
rm ~/.local/share/applications/peft-studio.desktop
```

### Debian Package

```bash
sudo apt-get remove peft-studio
```

### Remove User Data (Optional)

To completely remove all settings and data:

```bash
rm -rf ~/.config/peft-studio
rm -rf ~/.local/share/peft-studio
```

## Troubleshooting

### AppImage Won't Run

**Issue:** Double-clicking the AppImage does nothing

**Solutions:**

1. **Make it Executable:**
   ```bash
   chmod +x PEFT-Studio-*.AppImage
   ```

2. **Install FUSE:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install fuse libfuse2
   
   # Fedora
   sudo dnf install fuse fuse-libs
   
   # Arch Linux
   sudo pacman -S fuse2
   ```

3. **Run from Terminal:**
   ```bash
   ./PEFT-Studio-*.AppImage
   ```
   Check for error messages

4. **Extract and Run:**
   ```bash
   ./PEFT-Studio-*.AppImage --appimage-extract
   cd squashfs-root
   ./peft-studio
   ```

### Permission Denied

**Issue:** "Permission denied" when trying to run AppImage

**Solution:**

```bash
chmod +x PEFT-Studio-*.AppImage
```

### Missing Dependencies (DEB Package)

**Issue:** "Dependency is not satisfiable" error

**Solution:**

```bash
# Update package lists
sudo apt-get update

# Install dependencies
sudo apt-get install -f

# Try installing again
sudo dpkg -i PEFT-Studio-*.deb
```

### GPU Not Detected

**Issue:** PEFT Studio doesn't detect your NVIDIA GPU

**Solutions:**

1. **Install NVIDIA Drivers:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install nvidia-driver-535
   
   # Fedora
   sudo dnf install akmod-nvidia
   
   # Arch Linux
   sudo pacman -S nvidia nvidia-utils
   ```

2. **Install CUDA Toolkit:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install nvidia-cuda-toolkit
   
   # Fedora
   sudo dnf install cuda
   
   # Arch Linux
   sudo pacman -S cuda
   ```

3. **Verify NVIDIA Driver:**
   ```bash
   nvidia-smi
   ```
   You should see your GPU information. If not, reboot and try again.

4. **Check CUDA Version:**
   ```bash
   nvcc --version
   ```
   PEFT Studio requires CUDA 11.8 or later.

### Application Won't Start

**Issue:** PEFT Studio doesn't launch or crashes immediately

**Solutions:**

1. **Run from Terminal:**
   ```bash
   ./PEFT-Studio-*.AppImage
   ```
   Or for DEB package:
   ```bash
   peft-studio
   ```
   Check for error messages

2. **Check Logs:**
   ```bash
   cat ~/.config/peft-studio/logs/main.log
   ```

3. **Install Missing Libraries:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install libgtk-3-0 libnotify4 libnss3 libxss1 libxtst6 xdg-utils libatspi2.0-0 libdrm2 libgbm1 libxcb-dri3-0
   
   # Fedora
   sudo dnf install gtk3 libnotify nss libXScrnSaver libXtst xdg-utils at-spi2-core libdrm mesa-libgbm libxcb
   
   # Arch Linux
   sudo pacman -S gtk3 libnotify nss libxss libxtst xdg-utils at-spi2-core libdrm mesa libxcb
   ```

4. **Update System:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update && sudo apt-get upgrade
   
   # Fedora
   sudo dnf update
   
   # Arch Linux
   sudo pacman -Syu
   ```

### Slow Performance

**Issue:** PEFT Studio runs slowly or freezes

**Solutions:**

1. **Close Other Applications:**
   - Close unnecessary programs
   - Free up RAM and CPU resources

2. **Check System Resources:**
   ```bash
   htop
   ```
   Check CPU, RAM, and disk usage

3. **Use GPU for Training:**
   - Ensure GPU is detected (see above)
   - Training on CPU is much slower

4. **Reduce Dataset Size:**
   - Start with smaller datasets for testing
   - Use data sampling for large datasets

### Wayland Issues

**Issue:** Application doesn't work properly on Wayland

**Solution:**

Force X11 mode:

```bash
# For AppImage
GDK_BACKEND=x11 ./PEFT-Studio-*.AppImage

# For DEB package
GDK_BACKEND=x11 peft-studio
```

Or create a desktop entry with X11:

```bash
cat > ~/.local/share/applications/peft-studio.desktop << EOF
[Desktop Entry]
Name=PEFT Studio
Comment=Parameter-Efficient Fine-Tuning Studio
Exec=env GDK_BACKEND=x11 $HOME/.local/bin/peft-studio
Icon=peft-studio
Terminal=false
Type=Application
Categories=Development;Science;
EOF
```

### Verifying Downloads

To ensure your download isn't corrupted or tampered with:

```bash
# Download the checksums file
wget https://github.com/Ankesh-007/peft-studio/releases/latest/download/SHA256SUMS.txt

# Verify the AppImage
sha256sum -c SHA256SUMS.txt --ignore-missing

# Or manually
sha256sum PEFT-Studio-*.AppImage
# Compare with SHA256SUMS.txt
```

## Distribution-Specific Notes

### Ubuntu/Debian

```bash
# Install all recommended dependencies
sudo apt-get install -y \
  libgtk-3-0 libnotify4 libnss3 libxss1 libxtst6 \
  xdg-utils libatspi2.0-0 libdrm2 libgbm1 libxcb-dri3-0 \
  nvidia-driver-535 nvidia-cuda-toolkit
```

### Fedora

```bash
# Install all recommended dependencies
sudo dnf install -y \
  gtk3 libnotify nss libXScrnSaver libXtst xdg-utils \
  at-spi2-core libdrm mesa-libgbm libxcb \
  akmod-nvidia cuda
```

### Arch Linux

```bash
# Install all recommended dependencies
sudo pacman -S \
  gtk3 libnotify nss libxss libxtst xdg-utils \
  at-spi2-core libdrm mesa libxcb \
  nvidia nvidia-utils cuda
```

### Pop!_OS

Pop!_OS comes with NVIDIA drivers pre-installed. Just install CUDA:

```bash
sudo apt-get install nvidia-cuda-toolkit
```

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
   - Provide details: Distribution, version, error messages, logs

4. **Report a Bug:**
   - [Open an issue](https://github.com/Ankesh-007/peft-studio/issues/new?template=bug_report.md)
   - Include: Distribution, version, installation method, error messages, logs

## Next Steps

Now that PEFT Studio is installed:

1. **[Quick Start Guide](quick-start.md)** - Get started with your first fine-tuning job
2. **[Platform Connections](platform-connections.md)** - Connect to HuggingFace and cloud providers
3. **[Training Configuration](training-configuration.md)** - Learn how to configure training runs

---

**Need more help?** Visit our [support page](../../README.md#-getting-help) for additional resources.
