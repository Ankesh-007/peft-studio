# PEFT Studio v{{VERSION}}

## Downloads

### Windows
- **Installer:** `PEFT-Studio-Setup-{{VERSION}}.exe` (Recommended)
- **Portable:** `PEFT-Studio-Portable-{{VERSION}}.exe`

### macOS
- **DMG:** `PEFT-Studio-{{VERSION}}-x64.dmg` (Intel)
- **DMG:** `PEFT-Studio-{{VERSION}}-arm64.dmg` (Apple Silicon)
- **ZIP:** `PEFT-Studio-{{VERSION}}-mac.zip`

### Linux
- **AppImage:** `PEFT-Studio-{{VERSION}}-x64.AppImage` (Universal)
- **DEB:** `peft-studio_{{VERSION}}_amd64.deb` (Debian/Ubuntu)

## Installation Instructions

### Windows
1. Download `PEFT-Studio-Setup-{{VERSION}}.exe`
2. Run the installer
3. Follow the installation wizard
4. Launch PEFT Studio from the Start Menu

**Note:** Windows may show a security warning for unsigned applications. Click "More info" and "Run anyway" to proceed.

### macOS
1. Download the appropriate DMG file for your Mac:
   - Intel Macs: `PEFT-Studio-{{VERSION}}-x64.dmg`
   - Apple Silicon (M1/M2/M3): `PEFT-Studio-{{VERSION}}-arm64.dmg`
2. Open the DMG file
3. Drag PEFT Studio to your Applications folder
4. Right-click the app and select "Open" (first time only)

**Note:** macOS may show a security warning for unsigned applications. Go to System Preferences > Security & Privacy and click "Open Anyway".

### Linux
#### AppImage (Universal)
1. Download `PEFT-Studio-{{VERSION}}-x64.AppImage`
2. Make it executable: `chmod +x PEFT-Studio-{{VERSION}}-x64.AppImage`
3. Run: `./PEFT-Studio-{{VERSION}}-x64.AppImage`

#### Debian/Ubuntu (DEB)
1. Download `peft-studio_{{VERSION}}_amd64.deb`
2. Install: `sudo dpkg -i peft-studio_{{VERSION}}_amd64.deb`
3. Fix dependencies if needed: `sudo apt-get install -f`
4. Launch from applications menu or run: `peft-studio`

## What's New

{{RELEASE_NOTES}}

## System Requirements

- **Windows:** Windows 10 or later (64-bit)
- **macOS:** macOS 10.13 (High Sierra) or later
- **Linux:** Ubuntu 18.04 or later (or equivalent)
- **RAM:** 4GB minimum, 8GB recommended
- **Disk Space:** 500MB for application, additional space for models and datasets

## Checksums

See `SHA256SUMS.txt` for file integrity verification.

To verify a download:
```bash
# Linux/macOS
sha256sum -c SHA256SUMS.txt

# Windows (PowerShell)
Get-FileHash -Algorithm SHA256 <filename>
```

## Support

- **Documentation:** [https://github.com/Ankesh-007/peft-studio/tree/main/docs](https://github.com/Ankesh-007/peft-studio/tree/main/docs)
- **Report Issues:** [https://github.com/Ankesh-007/peft-studio/issues](https://github.com/Ankesh-007/peft-studio/issues)
- **Discussions:** [https://github.com/Ankesh-007/peft-studio/discussions](https://github.com/Ankesh-007/peft-studio/discussions)

## Known Issues

- Code signing certificates are not yet configured. Users will see security warnings on first launch.
- Auto-update functionality requires manual configuration of update server.

## Contributing

We welcome contributions! See [CONTRIBUTING.md](https://github.com/Ankesh-007/peft-studio/blob/main/CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](https://github.com/Ankesh-007/peft-studio/blob/main/LICENSE) for details.
