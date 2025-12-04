# Checksum Verification Guide

## Overview

Checksum verification is a critical security practice that ensures the integrity of downloaded files. By verifying checksums, you can confirm that:

1. The file was not corrupted during download
2. The file has not been tampered with or modified
3. You have the exact file that was published by the PEFT Studio team

**⚠️ Important:** Always verify checksums before installing software, especially when downloading from the internet.

## What is a Checksum?

A checksum (or hash) is a unique fingerprint of a file. PEFT Studio uses SHA256, a cryptographic hash function that produces a 64-character hexadecimal string. Even the smallest change to a file will produce a completely different checksum.

## Finding Official Checksums

Official checksums for PEFT Studio releases are published in two places:

1. **GitHub Releases Page:** Download the `SHA256SUMS.txt` file from the release assets
2. **Release Notes:** Checksums are listed in the release notes on GitHub

## Verification Methods

### Windows

#### Method 1: PowerShell (Recommended)

1. Open PowerShell (press `Win + X`, then select "Windows PowerShell")
2. Navigate to your downloads folder:
   ```powershell
   cd $HOME\Downloads
   ```
3. Calculate the checksum:
   ```powershell
   Get-FileHash "PEFT-Studio-Setup-1.0.0.exe" -Algorithm SHA256
   ```
4. Compare the output with the official checksum

**Example Output:**
```
Algorithm       Hash                                                                   Path
---------       ----                                                                   ----
SHA256          A1B2C3D4E5F6...                                                       C:\Users\...\PEFT-Studio-Setup-1.0.0.exe
```

#### Method 2: Command Prompt with certutil

1. Open Command Prompt (press `Win + R`, type `cmd`, press Enter)
2. Navigate to your downloads folder:
   ```cmd
   cd %USERPROFILE%\Downloads
   ```
3. Calculate the checksum:
   ```cmd
   certutil -hashfile "PEFT-Studio-Setup-1.0.0.exe" SHA256
   ```
4. Compare the output with the official checksum

#### Method 3: GUI Tool - HashTab

1. Download and install [HashTab](http://implbits.com/products/hashtab/)
2. Right-click the downloaded file
3. Select "Properties"
4. Click the "File Hashes" tab
5. Compare the SHA256 hash with the official checksum

### macOS

#### Method 1: Terminal with shasum (Recommended)

1. Open Terminal (press `Cmd + Space`, type "Terminal", press Enter)
2. Navigate to your downloads folder:
   ```bash
   cd ~/Downloads
   ```
3. Calculate the checksum:
   ```bash
   shasum -a 256 PEFT-Studio-1.0.0.dmg
   ```
4. Compare the output with the official checksum

**Example Output:**
```
a1b2c3d4e5f6...  PEFT-Studio-1.0.0.dmg
```

#### Method 2: Terminal with openssl

```bash
openssl dgst -sha256 PEFT-Studio-1.0.0.dmg
```

#### Method 3: Automated Verification Script

Create a verification script:

```bash
#!/bin/bash
# Save this as verify-checksum.sh

EXPECTED_CHECKSUM="paste_official_checksum_here"
FILE="PEFT-Studio-1.0.0.dmg"

ACTUAL_CHECKSUM=$(shasum -a 256 "$FILE" | awk '{print $1}')

if [ "$EXPECTED_CHECKSUM" = "$ACTUAL_CHECKSUM" ]; then
    echo "✅ Checksum verified! File is authentic."
else
    echo "❌ Checksum mismatch! DO NOT install this file."
    echo "Expected: $EXPECTED_CHECKSUM"
    echo "Actual:   $ACTUAL_CHECKSUM"
fi
```

Make it executable and run:
```bash
chmod +x verify-checksum.sh
./verify-checksum.sh
```

### Linux

#### Method 1: sha256sum (Recommended)

1. Open Terminal
2. Navigate to your downloads folder:
   ```bash
   cd ~/Downloads
   ```
3. Calculate the checksum:
   ```bash
   sha256sum PEFT-Studio-1.0.0.AppImage
   ```
4. Compare the output with the official checksum

**Example Output:**
```
a1b2c3d4e5f6...  PEFT-Studio-1.0.0.AppImage
```

#### Method 2: Verify Against SHA256SUMS.txt

If you've downloaded the `SHA256SUMS.txt` file:

```bash
sha256sum -c SHA256SUMS.txt
```

This will automatically verify all files listed in the checksums file.

**Example Output:**
```
PEFT-Studio-1.0.0.AppImage: OK
```

#### Method 3: GUI Tools

Most Linux file managers have checksum verification built-in or available via plugins:

- **Nautilus (GNOME):** Install `nautilus-gtkhash` extension
- **Dolphin (KDE):** Built-in checksum calculator in file properties
- **Thunar (XFCE):** Install `thunar-gtkhash` plugin

## Automated Verification

### Using the SHA256SUMS.txt File

1. Download both the installer and `SHA256SUMS.txt` from the release page
2. Place them in the same directory
3. Run the verification command for your platform:

**Windows (PowerShell):**
```powershell
$checksums = Get-Content SHA256SUMS.txt
$file = "PEFT-Studio-Setup-1.0.0.exe"
$expected = ($checksums | Select-String $file).ToString().Split()[0]
$actual = (Get-FileHash $file -Algorithm SHA256).Hash.ToLower()

if ($expected -eq $actual) {
    Write-Host "✅ Checksum verified! File is authentic." -ForegroundColor Green
} else {
    Write-Host "❌ Checksum mismatch! DO NOT install this file." -ForegroundColor Red
}
```

**macOS/Linux:**
```bash
sha256sum -c SHA256SUMS.txt 2>&1 | grep "$(basename PEFT-Studio-1.0.0.dmg)"
```

## Understanding Results

### ✅ Checksum Match

If the checksums match, you'll see output like:
- `OK` (Linux)
- Matching hash values (Windows/macOS)

**This means:**
- The file is authentic and unmodified
- It's safe to proceed with installation
- The download completed successfully

### ❌ Checksum Mismatch

If the checksums don't match, you'll see:
- `FAILED` (Linux)
- Different hash values (Windows/macOS)

**This means:**
- The file may be corrupted
- The file may have been tampered with
- The download may have been incomplete

**What to do:**
1. **DO NOT install the file**
2. Delete the downloaded file
3. Clear your browser cache
4. Download the file again from the official GitHub releases page
5. Verify the checksum again
6. If it still fails, report the issue on GitHub

## Security Best Practices

### 1. Always Verify Before Installing

Make checksum verification a habit for all software downloads, not just PEFT Studio.

### 2. Use Official Sources Only

Only download PEFT Studio from:
- Official GitHub releases: `https://github.com/Ankesh-007/peft-studio/releases`
- Official website (if available)

Never download from third-party sites or file-sharing services.

### 3. Verify the Checksums Source

Ensure you're comparing against checksums from the official GitHub release page. Don't trust checksums from:
- Email attachments
- Third-party websites
- Unofficial mirrors

### 4. Check HTTPS Connection

When downloading from GitHub, ensure you see the padlock icon in your browser's address bar, indicating a secure HTTPS connection.

### 5. Keep Records

Save the `SHA256SUMS.txt` file for your records. This can be useful for:
- Future verification
- Compliance requirements
- Audit trails

## Troubleshooting

### "File not found" Error

**Problem:** The verification command can't find the file.

**Solution:**
- Ensure you're in the correct directory
- Check the filename matches exactly (including version number)
- Use quotes around filenames with spaces

### Checksums Don't Match After Re-download

**Problem:** Downloaded the file again, but checksum still doesn't match.

**Possible causes:**
1. Network issues causing corruption
2. Antivirus software modifying the file
3. Browser extensions interfering with download

**Solutions:**
- Try a different browser
- Temporarily disable antivirus during download
- Use a download manager
- Try downloading from a different network

### Can't Find SHA256SUMS.txt

**Problem:** The checksums file isn't in the release assets.

**Solution:**
- Check the release notes for inline checksums
- Contact the maintainers via GitHub Issues
- Wait for the release to be fully published (checksums are generated last)

## Why Checksum Verification Matters

### Real-World Scenarios

1. **Corrupted Downloads:** Network issues can cause incomplete or corrupted downloads. Checksum verification catches these before installation.

2. **Man-in-the-Middle Attacks:** If an attacker intercepts your download and replaces it with malicious software, the checksum won't match.

3. **Compromised Mirrors:** If downloading from a mirror site, verification ensures you got the authentic file.

4. **Storage Corruption:** Files can become corrupted on disk. Verification before installation prevents issues.

### The Cost of Not Verifying

Installing unverified software can lead to:
- Malware infections
- Data theft
- System instability
- Security vulnerabilities
- Loss of trust in the software

**Verification takes 30 seconds. Recovery from a compromised system takes hours or days.**

## Automatic Verification in PEFT Studio

PEFT Studio's auto-update system automatically verifies checksums when downloading updates. This happens transparently in the background using electron-updater's built-in verification.

When you see "Update downloaded and verified," it means:
1. The update was downloaded successfully
2. The checksum was verified against the published value
3. The update is safe to install

If verification fails, you'll see an error message and the update won't be installed.

## Additional Resources

### Tools

- **Windows:** [HashTab](http://implbits.com/products/hashtab/), [7-Zip](https://www.7-zip.org/) (has checksum feature)
- **macOS:** Built-in Terminal commands, [HashTab for Mac](https://hashtab.en.softonic.com/mac)
- **Linux:** Built-in `sha256sum`, file manager plugins

### Further Reading

- [SHA-256 on Wikipedia](https://en.wikipedia.org/wiki/SHA-2)
- [NIST Guidelines on Cryptographic Hash Functions](https://csrc.nist.gov/projects/hash-functions)
- [How to Verify File Integrity](https://www.howtogeek.com/67241/htg-explains-what-are-md5-sha-1-hashes-and-how-do-i-check-them/)

## Support

If you encounter issues with checksum verification:

1. **Check this guide** for troubleshooting steps
2. **Search existing issues** on GitHub
3. **Create a new issue** with:
   - Your operating system and version
   - The file you're trying to verify
   - The expected and actual checksums
   - Steps you've already tried

**Security Issues:** If you believe you've found a security issue related to checksums or file integrity, please report it privately to the maintainers via GitHub Security Advisories.

---

**Remember:** A few seconds of verification can save hours of recovery. Always verify checksums before installing software!
