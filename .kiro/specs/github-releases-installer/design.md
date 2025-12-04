# Design Document

## Overview

This design document outlines the implementation of an automated GitHub releases system for PEFT Studio. The system will build platform-specific installers, publish them to GitHub releases, provide clear download instructions, and enable automatic updates for end users.

The solution leverages GitHub Actions for CI/CD, electron-builder for packaging, and electron-updater for auto-updates. It ensures a professional release experience with code signing, checksums, and comprehensive documentation.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Developer Workflow                       │
│  1. Create version tag (v1.0.0)                             │
│  2. Push tag to GitHub                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  GitHub Actions Workflow                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Windows    │  │    macOS     │  │    Linux     │     │
│  │   Builder    │  │   Builder    │  │   Builder    │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│                            ▼                                 │
│                  ┌──────────────────┐                       │
│                  │  Release Creator │                       │
│                  │  - Upload assets │                       │
│                  │  - Generate notes│                       │
│                  │  - Create release│                       │
│                  └──────────────────┘                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      GitHub Release                          │
│  - Windows: .exe (NSIS), .exe (portable)                    │
│  - macOS: .dmg, .zip                                        │
│  - Linux: .AppImage, .deb                                   │
│  - SHA256SUMS.txt                                           │
│  - Release notes with instructions                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      End Users                               │
│  1. Visit releases page                                      │
│  2. Download installer for their platform                    │
│  3. Install application                                      │
│  4. Receive automatic updates                                │
└─────────────────────────────────────────────────────────────┘
```

### Component Architecture

1. **GitHub Actions Workflow** (`release.yml`)
   - Triggered by version tags (v*.*.*)
   - Parallel build jobs for each platform
   - Release creation and asset upload
   - Checksum generation

2. **Electron Builder Configuration** (`package.json`)
   - Platform-specific build targets
   - Code signing configuration
   - Auto-update configuration
   - File associations and metadata

3. **Auto-Update System** (electron-updater)
   - Checks GitHub releases API
   - Downloads and verifies updates
   - Applies updates with user consent

4. **Documentation Updates**
   - README with download links
   - Installation guides per platform
   - Troubleshooting documentation

## Components and Interfaces

### 1. GitHub Actions Release Workflow

**File**: `.github/workflows/release.yml`

**Purpose**: Automate the build and release process when version tags are pushed.

**Jobs**:

- `build-windows`: Builds Windows installers (NSIS + portable)
- `build-macos`: Builds macOS installers (DMG + ZIP)
- `build-linux`: Builds Linux installers (AppImage + DEB)
- `create-release`: Creates GitHub release with all assets
- `generate-checksums`: Generates SHA256 checksums

**Inputs**:
- Git tag (e.g., `v1.0.0`)
- Repository secrets (code signing certificates)

**Outputs**:
- GitHub release with installer assets
- SHA256SUMS.txt file
- Auto-generated release notes

### 2. Electron Builder Configuration

**File**: `package.json` (build section)

**Purpose**: Configure electron-builder for platform-specific packaging.

**Configuration**:
```json
{
  "build": {
    "appId": "com.peftstudio.app",
    "productName": "PEFT Studio",
    "publish": {
      "provider": "github",
      "owner": "YOUR_USERNAME",
      "repo": "peft-studio"
    },
    "win": {
      "target": ["nsis", "portable"],
      "sign": "./scripts/sign-windows.js"
    },
    "mac": {
      "target": ["dmg", "zip"],
      "hardenedRuntime": true,
      "gatekeeperAssess": false
    },
    "linux": {
      "target": ["AppImage", "deb"],
      "category": "Development"
    }
  }
}
```

### 3. Auto-Update System

**File**: `electron/main.js`

**Purpose**: Check for and apply application updates.

**Interface**:
```typescript
interface UpdateChecker {
  checkForUpdates(): Promise<UpdateInfo | null>;
  downloadUpdate(): Promise<void>;
  quitAndInstall(): void;
}

interface UpdateInfo {
  version: string;
  releaseDate: string;
  releaseNotes: string;
  downloadUrl: string;
}
```

### 4. Release Notes Generator

**Purpose**: Generate comprehensive release notes with download instructions.

**Template Structure**:

- Version header
- Download links for each platform
- Installation instructions per platform
- What's new section
- System requirements
- Checksums
- Support links

### 5. Checksum Generator

**Purpose**: Generate SHA256 checksums for all release assets.

**Process**:
1. Calculate SHA256 hash for each installer file
2. Create SHA256SUMS.txt with format: `<hash>  <filename>`
3. Upload as release asset

## Data Models

### Release Metadata

```typescript
interface ReleaseMetadata {
  version: string;           // e.g., "1.0.0"
  tagName: string;           // e.g., "v1.0.0"
  name: string;              // e.g., "PEFT Studio v1.0.0"
  body: string;              // Release notes markdown
  draft: boolean;            // Whether release is draft
  prerelease: boolean;       // Whether release is pre-release
  createdAt: Date;
  publishedAt: Date;
}
```

### Release Asset

```typescript
interface ReleaseAsset {
  name: string;              // e.g., "PEFT-Studio-Setup-1.0.0.exe"
  label: string;             // Display name
  contentType: string;       // MIME type
  size: number;              // File size in bytes
  downloadCount: number;
  browserDownloadUrl: string;
  checksum: string;          // SHA256 hash
}
```

### Platform Configuration

```typescript
interface PlatformConfig {
  platform: 'windows' | 'macos' | 'linux';
  targets: string[];         // e.g., ['nsis', 'portable']
  icon: string;              // Icon file path
  category?: string;         // Linux category
  sign?: boolean;            // Whether to code sign
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


Property 1: Release page contains all platform downloads
*For any* published release, the release page should contain download links for Windows, macOS, and Linux installers
**Validates: Requirements 1.1**

Property 2: Download links serve correct files
*For any* platform download link, clicking it should download the appropriate installer file for that platform
**Validates: Requirements 1.2**

Property 3: Correct file formats per platform
*For any* platform, the downloaded installer should have the correct file format (NSIS for Windows, DMG for macOS, AppImage for Linux)
**Validates: Requirements 1.3**

Property 4: Release notes include installation instructions
*For any* published release, the release notes should contain installation instructions
**Validates: Requirements 1.4**

Property 5: Checksums displayed for all assets
*For any* release asset, a corresponding SHA256 checksum should be displayed on the release page
**Validates: Requirements 1.5**

Property 6: Version tags trigger workflow
*For any* valid version tag pushed to the repository, the release workflow should be automatically triggered
**Validates: Requirements 2.1**

Property 7: Parallel platform builds
*For any* release workflow execution, Windows, macOS, and Linux builds should run in parallel
**Validates: Requirements 2.2**

Property 8: Built installers uploaded as assets
*For any* successfully built installer, it should be uploaded as a release asset to GitHub
**Validates: Requirements 2.3**

Property 9: Checksums generated for all files
*For any* set of uploaded release assets, SHA256 checksums should be generated for each file
**Validates: Requirements 2.4**

Property 10: Release notes populated with metadata
*For any* created release, the release notes should contain version information and download instructions
**Validates: Requirements 2.5**

Property 11: Windows NSIS installer provided
*For any* Windows release, an NSIS-based setup executable should be provided
**Validates: Requirements 3.1**

Property 12: Installer allows directory selection
*For any* installer execution, the user should be able to choose the installation directory
**Validates: Requirements 3.2**

Property 13: Shortcuts created after installation
*For any* completed installation, desktop and start menu shortcuts should be created
**Validates: Requirements 3.3**

Property 14: Auto-update registration
*For any* installed application, the auto-update system should be registered
**Validates: Requirements 3.4**

Property 15: Windows portable version available
*For any* Windows release, a portable executable should be provided that requires no installation
**Validates: Requirements 3.5**

Property 16: macOS DMG provided
*For any* macOS release, a DMG disk image file should be provided
**Validates: Requirements 4.1**

Property 17: DMG contains required elements
*For any* DMG file, it should contain the application icon and Applications folder shortcut
**Validates: Requirements 4.2**

Property 18: Code signature verification
*For any* code-signed application launch, the signature should be verified
**Validates: Requirements 4.4**

Property 19: macOS ZIP archive available
*For any* macOS release, a ZIP file containing the application bundle should be provided
**Validates: Requirements 4.5**

Property 20: Linux AppImage provided
*For any* Linux release, an AppImage file should be provided
**Validates: Requirements 5.1**

Property 21: AppImage runs without installation
*For any* executable AppImage, it should run without requiring installation
**Validates: Requirements 5.2**

Property 22: AppImage desktop integration
*For any* running AppImage, it should integrate with the desktop environment
**Validates: Requirements 5.3**

Property 23: Debian package available
*For any* Linux release, a .deb package should be provided
**Validates: Requirements 5.4**

Property 24: Platform-specific instructions in notes
*For any* release notes, they should contain platform-specific installation instructions
**Validates: Requirements 6.1**

Property 25: Step-by-step guidance for all platforms
*For any* set of installation instructions, they should include step-by-step guidance for Windows, macOS, and Linux
**Validates: Requirements 6.2**

Property 26: Troubleshooting links provided
*For any* release, the release notes should include links to troubleshooting documentation
**Validates: Requirements 6.3**

Property 27: System requirements displayed
*For any* release, minimum OS versions and hardware requirements should be displayed
**Validates: Requirements 6.4**

Property 28: Checksum verification instructions
*For any* release with checksums, instructions for verifying file integrity should be included
**Validates: Requirements 6.5**

Property 29: Windows code signing when configured
*For any* Windows build with code signing configured, the executable should be signed with a certificate
**Validates: Requirements 7.1**

Property 30: macOS signing and notarization when configured
*For any* macOS build with code signing configured, the application should be signed and notarized
**Validates: Requirements 7.2**

Property 31: Unsigned builds documented
*For any* build without code signing credentials, unsigned installers should be produced and security implications documented
**Validates: Requirements 7.3**

Property 32: Unsigned installer bypass instructions
*For any* unsigned installer, instructions for bypassing OS security warnings should be provided
**Validates: Requirements 7.4**

Property 33: Signature validation before upload
*For any* signed build, the signature should be validated before uploading the release asset
**Validates: Requirements 7.5**

Property 34: Update check on startup
*For any* application start, the system should check for available updates from the GitHub releases API
**Validates: Requirements 8.1**

Property 35: Update notification displayed
*For any* detected new version, a notification should be displayed to the user
**Validates: Requirements 8.2**

Property 36: Automatic update installation
*For any* user-accepted update, the system should download and install it automatically
**Validates: Requirements 8.3**

Property 37: Update integrity verification
*For any* downloaded update, the file integrity should be verified using checksums
**Validates: Requirements 8.4**

Property 38: Application restart after update
*For any* installed update, the application should restart to apply the update
**Validates: Requirements 8.5**

Property 39: Download link navigates to releases
*For any* download link in the README, it should navigate to the GitHub releases page
**Validates: Requirements 9.2**

Property 40: Placeholder URL replacement
*For any* README update, placeholder URLs should be replaced with actual repository URLs
**Validates: Requirements 9.3**

Property 41: Platform guide links present
*For any* platform, the documentation should include a link to its installation guide
**Validates: Requirements 9.4**

Property 42: Username placeholder replacement
*For any* project publication, all instances of "YOUR_USERNAME" should be replaced with the actual GitHub username
**Validates: Requirements 9.5**

Property 43: Checksums generated for all installers
*For any* published release, SHA256 checksums should be generated for all installer files
**Validates: Requirements 10.1**

Property 44: Checksums uploaded as asset
*For any* generated set of checksums, they should be uploaded as a SHA256SUMS.txt release asset
**Validates: Requirements 10.2**

Property 45: Checksum verification instructions provided
*For any* installer download, instructions for verifying the checksum should be provided
**Validates: Requirements 10.3**

Property 46: Checksum verification matches
*For any* downloaded file, the calculated SHA256 hash should match the published checksum
**Validates: Requirements 10.4**

Property 47: Checksum mismatch warning
*For any* checksum verification failure, a warning should be displayed advising not to install the file
**Validates: Requirements 10.5**

## Error Handling

### Build Failures

**Scenario**: Platform-specific build fails during workflow execution

**Handling**:
1. Log detailed error information
2. Continue with other platform builds
3. Mark release as draft if any build fails
4. Notify maintainers via GitHub Actions notifications
5. Provide troubleshooting steps in workflow logs

### Code Signing Failures

**Scenario**: Code signing fails due to missing or invalid certificates

**Handling**:
1. Fall back to unsigned build
2. Add warning to release notes about unsigned installer
3. Provide instructions for users to bypass security warnings
4. Log certificate validation errors
5. Continue with release process

### Checksum Generation Failures

**Scenario**: Checksum generation fails for release assets

**Handling**:
1. Retry checksum generation up to 3 times
2. If still failing, create release without checksums
3. Add warning to release notes
4. Log error details for debugging
5. Notify maintainers

### Auto-Update Failures

**Scenario**: Application fails to check for or download updates

**Handling**:
1. Silently fail without disrupting user experience
2. Log error details for diagnostics
3. Retry on next application start
4. Provide manual update link in settings
5. Display user-friendly error message if update download fails

### Network Failures

**Scenario**: GitHub API is unavailable during release or update check

**Handling**:
1. Implement exponential backoff retry strategy
2. Cache last successful update check result
3. Provide offline mode for application
4. Display network error message to user
5. Allow manual retry

## Testing Strategy

### Unit Tests

**Build Configuration Tests**:
- Verify electron-builder configuration is valid
- Test platform-specific build settings
- Validate code signing configuration
- Test checksum generation logic

**Auto-Update Tests**:
- Test update check logic
- Verify update download and verification
- Test update installation process
- Validate version comparison logic

**Documentation Tests**:
- Verify README contains download links
- Test placeholder replacement logic
- Validate release notes template
- Check installation instructions completeness

### Integration Tests

**Workflow Tests**:
- Test complete release workflow end-to-end
- Verify parallel build execution
- Test asset upload to GitHub
- Validate release creation

**Installer Tests**:
- Test Windows installer on Windows VM
- Test macOS installer on macOS VM
- Test Linux installer on Linux VM
- Verify shortcuts and file associations
- Test auto-update mechanism

**Checksum Tests**:
- Verify checksum generation for all assets
- Test checksum verification logic
- Validate SHA256SUMS.txt format
- Test checksum mismatch handling

### Property-Based Tests

We will use fast-check (JavaScript/TypeScript) for property-based testing. Each property test should run a minimum of 100 iterations.

**Property Test Requirements**:
- Each property-based test must be tagged with a comment referencing the design document
- Tag format: `**Feature: github-releases-installer, Property {number}: {property_text}**`
- Each correctness property must be implemented by a single property-based test
- Tests should use smart generators that constrain to the input space intelligently

### Manual Testing

**Release Process**:
- Create test release with version tag
- Verify all platform builds complete successfully
- Download and install on each platform
- Test auto-update mechanism
- Verify checksums match downloaded files

**User Experience**:
- Test installation wizard on Windows
- Test DMG installation on macOS
- Test AppImage execution on Linux
- Verify shortcuts and desktop integration
- Test uninstallation process

## Implementation Notes

### GitHub Actions Secrets

Required secrets for code signing:
- `CSC_LINK`: Windows code signing certificate (base64 encoded)
- `CSC_KEY_PASSWORD`: Certificate password
- `APPLE_ID`: Apple ID for macOS notarization
- `APPLE_ID_PASSWORD`: App-specific password
- `APPLE_TEAM_ID`: Apple Developer Team ID

### Version Tagging Convention

Follow semantic versioning:
- `v1.0.0` - Major release
- `v1.1.0` - Minor release (new features)
- `v1.0.1` - Patch release (bug fixes)
- `v1.0.0-beta.1` - Pre-release

### Release Notes Template

Location: `.github/release-template.md`

Template variables:
- `{{VERSION}}` - Version number
- `{{TAG_NAME}}` - Git tag name
- `{{RELEASE_DATE}}` - Release date
- `{{CHANGELOG}}` - Auto-generated changelog

### Auto-Update Configuration

Update channel: `latest`
Update check interval: On application start
Update download: Background download with user notification
Update installation: Requires user confirmation

### Platform-Specific Considerations

**Windows**:
- NSIS installer with custom branding
- Portable version for users without admin rights
- SmartScreen warning for unsigned builds
- Auto-update via electron-updater

**macOS**:
- DMG with custom background and layout
- ZIP archive for automation/scripting
- Gatekeeper warning for unsigned builds
- Notarization required for macOS 10.15+

**Linux**:
- AppImage for universal compatibility
- DEB package for Debian/Ubuntu
- Desktop file for menu integration
- Auto-update via AppImageUpdate

## Dependencies

### Build Dependencies
- `electron-builder`: ^25.1.8 - Application packaging
- `electron`: ^39.2.4 - Electron framework
- `electron-updater`: ^6.6.2 - Auto-update system

### CI/CD Dependencies
- GitHub Actions workflows
- GitHub Releases API
- Platform-specific build runners (Windows, macOS, Linux)

### External Services
- GitHub for hosting releases
- GitHub API for update checks
- Code signing services (optional)

## Security Considerations

### Code Signing
- Use valid code signing certificates for production releases
- Store certificates securely in GitHub Secrets
- Validate signatures before distribution
- Document unsigned build implications

### Checksum Verification
- Generate SHA256 checksums for all release assets
- Verify checksums during auto-update
- Provide user instructions for manual verification
- Fail safely if checksums don't match

### Update Security
- Use HTTPS for all update checks and downloads
- Verify update signatures before installation
- Implement rollback mechanism for failed updates
- Rate limit update checks to prevent abuse

### Credential Management
- Never commit code signing certificates to repository
- Use GitHub Secrets for sensitive data
- Rotate credentials regularly
- Audit access to secrets

## Performance Considerations

### Build Performance
- Parallel platform builds reduce total build time
- Cache npm dependencies between builds
- Use incremental builds when possible
- Optimize asset compression

### Download Performance
- Provide multiple download mirrors if needed
- Use CDN for release assets (GitHub provides this)
- Compress installers to reduce download size
- Implement resume capability for large downloads

### Update Performance
- Background download doesn't block application
- Delta updates for smaller download sizes
- Efficient checksum verification
- Minimal application restart time

## Deployment Strategy

### Initial Release (v1.0.0)
1. Update all placeholder URLs in documentation
2. Configure code signing (if available)
3. Create and push version tag
4. Monitor workflow execution
5. Test installers on all platforms
6. Publish release (remove draft status)
7. Announce release to users

### Subsequent Releases
1. Update CHANGELOG.md with changes
2. Bump version in package.json
3. Create and push version tag
4. Workflow automatically builds and publishes
5. Verify auto-update works for existing users
6. Monitor download statistics

### Hotfix Releases
1. Create hotfix branch from release tag
2. Apply critical fixes
3. Bump patch version
4. Follow standard release process
5. Expedite testing and publication

## Monitoring and Analytics

### Release Metrics
- Download count per platform
- Update adoption rate
- Installation success rate
- Error rates during installation

### User Feedback
- GitHub Issues for bug reports
- GitHub Discussions for questions
- Analytics on download patterns
- User surveys for satisfaction

### Continuous Improvement
- Monitor common installation issues
- Track auto-update success rates
- Analyze platform-specific problems
- Iterate on documentation based on feedback
