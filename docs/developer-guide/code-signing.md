# Code Signing Guide

## Overview

Code signing is the process of digitally signing executables and scripts to confirm the software author and guarantee that the code has not been altered or corrupted since it was signed. This guide explains how to configure code signing for PEFT Studio releases.

## Why Code Signing?

- **Trust**: Users can verify the software comes from a legitimate source
- **Security**: Operating systems trust signed applications and show fewer warnings
- **Integrity**: Ensures the installer hasn't been tampered with
- **Auto-updates**: Signed applications can update more seamlessly

## Platform Requirements

### Windows Code Signing

**Required Certificate**: Code Signing Certificate from a trusted Certificate Authority (CA)

**Supported Certificate Types**:
- Standard Code Signing Certificate
- EV (Extended Validation) Code Signing Certificate (recommended)

**Where to Obtain**:
- DigiCert
- Sectigo (formerly Comodo)
- GlobalSign
- SSL.com

**Cost**: $100-$500/year depending on provider and certificate type

### macOS Code Signing

**Required Credentials**:
- Apple Developer Account ($99/year)
- Developer ID Application Certificate
- App-specific password for notarization

**Where to Obtain**:
- [Apple Developer Program](https://developer.apple.com/programs/)

### Linux

Linux distributions generally don't require code signing for desktop applications. However, some package repositories may have their own signing requirements.

## Configuration

### GitHub Secrets Setup

To enable code signing in the release workflow, configure the following GitHub Secrets:

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add the following secrets:

#### Windows Secrets

| Secret Name | Description | How to Obtain |
|------------|-------------|---------------|
| `CSC_LINK` | Base64-encoded certificate file (.pfx or .p12) | Export your certificate and encode it: `base64 -i certificate.pfx` |
| `CSC_KEY_PASSWORD` | Certificate password | The password you set when creating the certificate |

**Example: Encoding Certificate**
```bash
# On macOS/Linux
base64 -i your-certificate.pfx -o certificate-base64.txt

# On Windows (PowerShell)
[Convert]::ToBase64String([IO.File]::ReadAllBytes("your-certificate.pfx")) | Out-File certificate-base64.txt
```

#### macOS Secrets

| Secret Name | Description | How to Obtain |
|------------|-------------|---------------|
| `CSC_LINK` | Base64-encoded certificate file (.p12) | Export from Keychain Access and encode |
| `CSC_KEY_PASSWORD` | Certificate password | The password you set when exporting |
| `APPLE_ID` | Your Apple ID email | Your Apple Developer account email |
| `APPLE_ID_PASSWORD` | App-specific password | Generate at [appleid.apple.com](https://appleid.apple.com) |
| `APPLE_TEAM_ID` | Your Apple Team ID | Find in Apple Developer account |

**Example: Exporting macOS Certificate**
1. Open **Keychain Access**
2. Find your "Developer ID Application" certificate
3. Right-click → **Export**
4. Save as `.p12` file with a password
5. Encode: `base64 -i certificate.p12 -o certificate-base64.txt`

**Example: Creating App-Specific Password**
1. Go to [appleid.apple.com](https://appleid.apple.com)
2. Sign in with your Apple ID
3. Navigate to **Security** → **App-Specific Passwords**
4. Click **Generate Password**
5. Enter a label (e.g., "PEFT Studio Notarization")
6. Copy the generated password

### Local Development Setup

For local testing of signed builds:

**Windows**:
```bash
# Set environment variables
set CSC_LINK=C:\path\to\certificate.pfx
set CSC_KEY_PASSWORD=your-password

# Build
npm run package:win
```

**macOS**:
```bash
# Set environment variables
export CSC_LINK=/path/to/certificate.p12
export CSC_KEY_PASSWORD=your-password
export APPLE_ID=your@email.com
export APPLE_ID_PASSWORD=your-app-specific-password
export APPLE_TEAM_ID=YOUR_TEAM_ID

# Build
npm run package:mac
```

## Unsigned Builds

### When Signing is Not Available

If code signing credentials are not configured, the build process will:
1. Create unsigned installers
2. Log a warning message
3. Continue with the build process
4. Add a note to the release about unsigned status

### Security Implications

**Unsigned Windows Installers**:
- Windows SmartScreen will show a warning
- Users must click "More info" → "Run anyway"
- Some antivirus software may flag the installer
- Corporate environments may block installation

**Unsigned macOS Applications**:
- Gatekeeper will block the application by default
- Users must right-click → "Open" to bypass
- macOS 10.15+ shows stronger warnings
- Cannot be distributed through Mac App Store

### User Instructions for Unsigned Builds

Include these instructions in your release notes when distributing unsigned builds:

**Windows**:
```
If you see a "Windows protected your PC" warning:
1. Click "More info"
2. Click "Run anyway"
3. Proceed with installation
```

**macOS**:
```
If you see a "cannot be opened because the developer cannot be verified" warning:
1. Right-click (or Control-click) the application
2. Select "Open" from the menu
3. Click "Open" in the dialog
4. The application will now run
```

**Linux**:
```
Make the AppImage executable:
chmod +x PEFT-Studio-*.AppImage
./PEFT-Studio-*.AppImage
```

## Verification

### Verifying Signed Windows Executables

```powershell
# Check signature
Get-AuthenticodeSignature "PEFT-Studio-Setup-1.0.0.exe"

# Should show:
# Status: Valid
# SignerCertificate: CN=Your Company Name
```

### Verifying Signed macOS Applications

```bash
# Check code signature
codesign -dv --verbose=4 "PEFT Studio.app"

# Check notarization
spctl -a -vv "PEFT Studio.app"

# Should show:
# accepted
# source=Notarized Developer ID
```

## Troubleshooting

### Windows Signing Issues

**Problem**: "Certificate not found"
- **Solution**: Ensure `CSC_LINK` points to a valid .pfx or .p12 file
- **Solution**: Check that the certificate is not expired

**Problem**: "Invalid password"
- **Solution**: Verify `CSC_KEY_PASSWORD` is correct
- **Solution**: Try re-exporting the certificate with a new password

**Problem**: "Timestamp server unavailable"
- **Solution**: This is usually temporary; retry the build
- **Solution**: Check your internet connection

### macOS Signing Issues

**Problem**: "No identity found"
- **Solution**: Ensure the certificate is installed in Keychain
- **Solution**: Check that it's a "Developer ID Application" certificate

**Problem**: "Notarization failed"
- **Solution**: Verify `APPLE_ID` and `APPLE_ID_PASSWORD` are correct
- **Solution**: Ensure you're using an app-specific password, not your main password
- **Solution**: Check that `APPLE_TEAM_ID` matches your developer account

**Problem**: "Hardened runtime error"
- **Solution**: Ensure `entitlements.mac.plist` is properly configured
- **Solution**: Check that all required entitlements are included

### General Issues

**Problem**: Build succeeds but application won't run
- **Solution**: Verify the certificate is for code signing (not SSL/TLS)
- **Solution**: Check that the certificate hasn't expired
- **Solution**: Ensure the certificate chain is complete

## Best Practices

1. **Secure Storage**: Never commit certificates or passwords to version control
2. **Rotation**: Rotate certificates before they expire
3. **Backup**: Keep secure backups of certificates and passwords
4. **Access Control**: Limit who has access to signing credentials
5. **Audit**: Regularly audit who has access to GitHub Secrets
6. **Testing**: Test signed builds before releasing to users
7. **Documentation**: Keep this guide updated with any changes

## Cost Summary

| Platform | Requirement | Annual Cost |
|----------|-------------|-------------|
| Windows | Code Signing Certificate | $100-$500 |
| macOS | Apple Developer Account | $99 |
| Linux | None | $0 |
| **Total** | | **$199-$599/year** |

## Additional Resources

- [Electron Builder Code Signing](https://www.electron.build/code-signing)
- [Windows Code Signing](https://docs.microsoft.com/en-us/windows/win32/seccrypto/cryptography-tools)
- [Apple Notarization](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [electron-builder Configuration](https://www.electron.build/configuration/configuration)

## Support

If you encounter issues with code signing:
1. Check the [Troubleshooting](#troubleshooting) section above
2. Review the [electron-builder documentation](https://www.electron.build/code-signing)
3. Open an issue on the [GitHub repository](https://github.com/Ankesh-007/peft-studioissues)
