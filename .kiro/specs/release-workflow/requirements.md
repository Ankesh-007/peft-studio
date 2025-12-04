# Release Workflow Requirements

## Introduction

This specification defines the complete release workflow for PEFT Studio, covering the process of building installers for all platforms, generating checksums for verification, and creating GitHub releases with proper asset management. The workflow ensures that users can download, verify, and install PEFT Studio safely and reliably across Windows, macOS, and Linux platforms.

## Glossary

- **Release Workflow System**: The automated system that builds, verifies, and publishes PEFT Studio releases
- **Installer**: A platform-specific executable or package that installs PEFT Studio on a user's system
- **Checksum**: A cryptographic hash (SHA-256) used to verify file integrity and authenticity
- **GitHub Release**: A tagged version of the software with associated release notes and downloadable assets
- **Asset**: A file attached to a GitHub release (installers, checksums, source code)
- **Artifact**: A build output file (installer, portable executable, etc.)
- **Code Signing**: The process of digitally signing executables to verify publisher identity
- **electron-builder**: The build tool used to create platform-specific installers
- **Release Notes**: Documentation describing changes, fixes, and new features in a release
- **Semantic Versioning**: Version numbering scheme (MAJOR.MINOR.PATCH) used for releases
- **CI/CD**: Continuous Integration/Continuous Deployment automation system
- **Dry-run Mode**: A simulation mode that validates the release process without creating actual artifacts or releases
- **Pre-release**: A version marked for testing before stable release (beta, alpha, release candidate)

## Requirements

### Requirement 1: Build Platform Installers

**User Story:** As a release manager, I want to build installers for all supported platforms, so that users can install PEFT Studio on their operating systems.

#### Acceptance Criteria

1. WHEN the build process is initiated, THE Release Workflow System SHALL build Windows installers (NSIS and Portable) for x64 architecture
2. WHEN the build process is initiated, THE Release Workflow System SHALL build macOS installers (DMG and ZIP) for both x64 and arm64 architectures
3. WHEN the build process is initiated, THE Release Workflow System SHALL build Linux installers (AppImage and DEB) for x64 architecture
4. WHEN building installers, THE Release Workflow System SHALL use the version number from package.json in artifact filenames
5. WHEN building installers, THE Release Workflow System SHALL output all artifacts to the release/ directory

### Requirement 2: Generate Verification Checksums

**User Story:** As a security-conscious user, I want to verify downloaded installers using checksums, so that I can ensure the files haven't been tampered with.

#### Acceptance Criteria

1. WHEN installers are built, THE Release Workflow System SHALL generate SHA-256 checksums for all installer artifacts
2. WHEN generating checksums, THE Release Workflow System SHALL create a checksums.txt file containing all checksums with filenames
3. WHEN generating checksums, THE Release Workflow System SHALL use the format "HASH  FILENAME" for each entry
4. WHEN generating checksums, THE Release Workflow System SHALL include checksums for Windows, macOS, and Linux installers
5. WHEN checksums are generated, THE Release Workflow System SHALL save the checksums.txt file in the release/ directory

### Requirement 3: Create GitHub Release

**User Story:** As a user, I want to download PEFT Studio from GitHub releases, so that I can install the latest version easily.

#### Acceptance Criteria

1. WHEN creating a release THEN the system SHALL create a GitHub release with the version tag from package.json
2. WHEN creating a release THEN the system SHALL upload all installer artifacts as release assets
3. WHEN creating a release THEN the system SHALL upload the checksums.txt file as a release asset
4. WHEN creating a release THEN the system SHALL include release notes from CHANGELOG.md
5. WHEN creating a release THEN the system SHALL mark the release as a draft if specified, otherwise publish immediately

### Requirement 4: Validate Build Configuration

**User Story:** As a developer, I want to validate the build configuration before releasing, so that I can catch configuration errors early.

#### Acceptance Criteria

1. WHEN validating configuration THEN the system SHALL verify that package.json contains valid version, name, and build settings
2. WHEN validating configuration THEN the system SHALL verify that electron-builder configuration is complete for all platforms
3. WHEN validating configuration THEN the system SHALL verify that required signing scripts exist (sign-windows.js, sign-macos.js)
4. WHEN validating configuration THEN the system SHALL verify that required environment variables are set for code signing
5. WHEN validation fails THEN the system SHALL report specific configuration errors with remediation guidance

### Requirement 5: Automate Release Process

**User Story:** As a release manager, I want to automate the entire release process, so that I can create releases consistently and efficiently.

#### Acceptance Criteria

1. WHEN running the release script THEN the system SHALL execute all steps in sequence: validate, build, checksum, release
2. WHEN any step fails THEN the system SHALL halt the process and report the failure with context
3. WHEN running in dry-run mode THEN the system SHALL simulate all steps without making actual changes
4. WHEN the release process completes THEN the system SHALL provide a summary of created artifacts and release URL
5. WHEN running the release script THEN the system SHALL verify that the working directory is clean (no uncommitted changes)

### Requirement 6: Code Sign Installers

**User Story:** As a user, I want installers to be code-signed, so that my operating system trusts the application.

#### Acceptance Criteria

1. WHEN building Windows installers THEN the system SHALL sign executables using the Windows code signing certificate
2. WHEN building macOS installers THEN the system SHALL sign the application bundle using the Apple Developer certificate
3. WHEN building macOS installers THEN the system SHALL notarize the application with Apple's notarization service
4. WHEN code signing fails THEN the system SHALL report the failure but continue the build process
5. WHEN code signing credentials are missing THEN the system SHALL log a warning and create unsigned installers

### Requirement 7: Verify Installer Integrity

**User Story:** As a quality assurance engineer, I want to verify that built installers are valid and complete, so that users receive working software.

#### Acceptance Criteria

1. WHEN installers are built THEN the system SHALL verify that all expected artifacts exist in the release/ directory
2. WHEN installers are built THEN the system SHALL verify that artifact file sizes are within expected ranges
3. WHEN installers are built THEN the system SHALL verify that artifact filenames match the expected naming convention
4. WHEN installers are built THEN the system SHALL verify that the checksums.txt file contains entries for all artifacts
5. WHEN verification fails THEN the system SHALL report which artifacts are missing or invalid

### Requirement 8: Manage Release Assets

**User Story:** As a release manager, I want to manage release assets efficiently, so that users can find and download the correct installer for their platform.

#### Acceptance Criteria

1. WHEN uploading assets THEN the system SHALL organize assets by platform (Windows, macOS, Linux)
2. WHEN uploading assets THEN the system SHALL include clear naming conventions indicating platform and architecture
3. WHEN uploading assets THEN the system SHALL verify that all assets uploaded successfully
4. WHEN uploading assets THEN the system SHALL retry failed uploads up to 3 times
5. WHEN all assets are uploaded THEN the system SHALL verify the total number of assets matches expectations

### Requirement 9: Generate Release Notes

**User Story:** As a user, I want to read release notes, so that I understand what changed in the new version.

#### Acceptance Criteria

1. WHEN creating a release THEN the system SHALL extract release notes from CHANGELOG.md for the current version
2. WHEN extracting release notes THEN the system SHALL include all changes between version headers
3. WHEN extracting release notes THEN the system SHALL format release notes as Markdown
4. WHEN release notes are missing THEN the system SHALL generate a default message with the version number
5. WHEN release notes are generated THEN the system SHALL include links to documentation and installation guides

### Requirement 10: Support Multiple Release Channels

**User Story:** As a developer, I want to create pre-release versions, so that I can test releases before making them public.

#### Acceptance Criteria

1. WHEN creating a pre-release THEN the system SHALL mark the GitHub release as a pre-release
2. WHEN creating a pre-release THEN the system SHALL append a pre-release identifier to the version tag (e.g., -beta, -rc)
3. WHEN creating a stable release THEN the system SHALL mark the GitHub release as the latest release
4. WHEN creating a release THEN the system SHALL allow specifying the release channel (stable, beta, alpha)
5. WHEN creating a pre-release THEN the system SHALL include a warning in the release notes about pre-release status

