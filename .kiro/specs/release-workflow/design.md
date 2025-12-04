# Release Workflow Design

## Overview

The release workflow system provides an automated, reliable process for building, verifying, and publishing PEFT Studio releases across all supported platforms. The system integrates with electron-builder for creating platform-specific installers, generates cryptographic checksums for security verification, and manages GitHub releases with proper asset organization.

The workflow is designed to be:
- **Automated**: Single command execution for the entire release process
- **Reliable**: Comprehensive validation and error handling at each step
- **Secure**: Code signing and checksum verification for all artifacts
- **Transparent**: Detailed logging and dry-run mode for testing
- **Flexible**: Support for multiple release channels and configurations

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Release Workflow System                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Validation  │  │    Build     │  │   Checksum   │      │
│  │   Module     │→ │   Module     │→ │   Generator  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         ↓                  ↓                  ↓              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │    Config    │  │    Code      │  │   Release    │      │
│  │  Validator   │  │   Signing    │  │   Manager    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
                  ┌──────────────────┐
                  │  GitHub Releases │
                  │      API         │
                  └──────────────────┘
```

### Data Flow

1. **Validation Phase**: Verify configuration, environment, and prerequisites
2. **Build Phase**: Execute electron-builder for all platforms
3. **Signing Phase**: Code sign installers (Windows and macOS)
4. **Checksum Phase**: Generate SHA-256 checksums for all artifacts
5. **Verification Phase**: Validate built artifacts and checksums
6. **Release Phase**: Create GitHub release and upload assets
7. **Notification Phase**: Report completion status and provide release URL

## Components and Interfaces

### 1. Validation Module

**Purpose**: Validates configuration and environment before building

**Interface**:
```typescript
interface ValidationModule {
  validatePackageJson(): ValidationResult;
  validateBuildConfig(): ValidationResult;
  validateEnvironment(): ValidationResult;
  validateWorkingDirectory(): ValidationResult;
  validateSigningCredentials(): ValidationResult;
}

interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}
```

**Responsibilities**:
- Verify package.json structure and required fields
- Validate electron-builder configuration
- Check for required environment variables
- Ensure working directory is clean
- Verify signing credentials availability

### 2. Build Module

**Purpose**: Orchestrates the build process using electron-builder

**Interface**:
```typescript
interface BuildModule {
  buildWindows(): Promise<BuildResult>;
  buildMacOS(): Promise<BuildResult>;
  buildLinux(): Promise<BuildResult>;
  buildAll(): Promise<BuildResult[]>;
}

interface BuildResult {
  platform: 'windows' | 'macos' | 'linux';
  artifacts: Artifact[];
  success: boolean;
  errors: string[];
}

interface Artifact {
  filename: string;
  path: string;
  size: number;
  type: 'installer' | 'portable' | 'archive';
}
```

**Responsibilities**:
- Execute electron-builder with platform-specific configurations
- Monitor build progress and capture output
- Collect built artifacts and metadata
- Handle build failures and retries

### 3. Code Signing Module

**Purpose**: Signs installers for Windows and macOS

**Interface**:
```typescript
interface CodeSigningModule {
  signWindows(artifacts: Artifact[]): Promise<SigningResult>;
  signMacOS(artifacts: Artifact[]): Promise<SigningResult>;
  notarizeMacOS(artifacts: Artifact[]): Promise<NotarizationResult>;
}

interface SigningResult {
  signed: boolean;
  artifacts: string[];
  errors: string[];
}

interface NotarizationResult {
  notarized: boolean;
  requestId: string;
  status: string;
}
```

**Responsibilities**:
- Sign Windows executables using signtool
- Sign macOS applications using codesign
- Notarize macOS applications with Apple
- Handle signing failures gracefully

### 4. Checksum Generator

**Purpose**: Generates SHA-256 checksums for verification

**Interface**:
```typescript
interface ChecksumGenerator {
  generateChecksums(artifacts: Artifact[]): Promise<ChecksumResult>;
  writeChecksumsFile(checksums: Checksum[]): Promise<void>;
  verifyChecksums(checksumFile: string): Promise<boolean>;
}

interface ChecksumResult {
  checksums: Checksum[];
  checksumFile: string;
}

interface Checksum {
  filename: string;
  hash: string;
  algorithm: 'sha256';
}
```

**Responsibilities**:
- Calculate SHA-256 hashes for all artifacts
- Format checksums in standard format
- Write checksums.txt file
- Verify checksum file integrity

### 5. Release Manager

**Purpose**: Creates and manages GitHub releases

**Interface**:
```typescript
interface ReleaseManager {
  createRelease(options: ReleaseOptions): Promise<Release>;
  uploadAssets(release: Release, artifacts: Artifact[]): Promise<void>;
  generateReleaseNotes(version: string): Promise<string>;
  publishRelease(release: Release): Promise<void>;
}

interface ReleaseOptions {
  version: string;
  tag: string;
  name: string;
  body: string;
  draft: boolean;
  prerelease: boolean;
}

interface Release {
  id: number;
  url: string;
  tag: string;
  assets: Asset[];
}
```

**Responsibilities**:
- Create GitHub releases via API
- Upload artifacts as release assets
- Extract and format release notes
- Manage release publication status

## Data Models

### Build Configuration

```typescript
interface BuildConfiguration {
  version: string;
  productName: string;
  appId: string;
  platforms: PlatformConfig[];
  signing: SigningConfig;
  output: OutputConfig;
}

interface PlatformConfig {
  platform: 'windows' | 'macos' | 'linux';
  targets: BuildTarget[];
  architectures: Architecture[];
}

interface BuildTarget {
  type: 'nsis' | 'portable' | 'dmg' | 'zip' | 'appimage' | 'deb';
  options: Record<string, any>;
}

interface SigningConfig {
  windows: WindowsSigningConfig;
  macos: MacOSSigningConfig;
}

interface OutputConfig {
  directory: string;
  artifactNameTemplate: string;
}
```

### Release Metadata

```typescript
interface ReleaseMetadata {
  version: string;
  tag: string;
  date: string;
  artifacts: ArtifactMetadata[];
  checksums: Checksum[];
  releaseNotes: string;
  channel: 'stable' | 'beta' | 'alpha';
}

interface ArtifactMetadata {
  filename: string;
  platform: string;
  architecture: string;
  type: string;
  size: number;
  checksum: string;
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Build Completeness

*For any* release build, all expected artifacts for enabled platforms must be generated successfully.

**Validates: Requirements 1.1, 1.2, 1.3**

### Property 2: Checksum Consistency

*For any* artifact, recalculating its checksum must produce the same hash value as recorded in checksums.txt.

**Validates: Requirements 2.1, 2.2, 2.3**

### Property 3: Filename Convention

*For any* generated artifact, the filename must match the pattern `${productName}-${version}-${platform}-${arch}.${ext}` or the configured naming template.

**Validates: Requirements 1.4, 7.3**

### Property 4: Asset Upload Completeness

*For any* GitHub release, the number of uploaded assets must equal the number of built artifacts plus the checksums file.

**Validates: Requirements 3.2, 3.3, 8.3**

### Property 5: Release Notes Extraction

*For any* version in CHANGELOG.md, extracting release notes must return all content between that version header and the next version header.

**Validates: Requirements 9.1, 9.2**

### Property 6: Validation Before Build

*For any* release execution, if validation fails, then no build artifacts should be created.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4**

### Property 7: Dry Run Idempotence

*For any* release configuration, running in dry-run mode multiple times must produce the same validation results without creating artifacts or releases.

**Validates: Requirements 5.3**

### Property 8: Checksum File Format

*For any* checksums.txt file, each line must match the format `^[a-f0-9]{64}  .+$` (SHA-256 hash, two spaces, filename).

**Validates: Requirements 2.3**

## Error Handling

### Build Failures

**Scenario**: electron-builder fails to create an installer

**Handling**:
1. Capture build error output
2. Log detailed error information
3. Continue building other platforms if possible
4. Report all failures at the end
5. Exit with non-zero status code

### Signing Failures

**Scenario**: Code signing fails due to missing credentials

**Handling**:
1. Log warning about unsigned installer
2. Continue with unsigned artifact
3. Mark artifact as unsigned in metadata
4. Include warning in release notes
5. Do not fail the entire build

### Upload Failures

**Scenario**: GitHub API fails to upload an asset

**Handling**:
1. Retry upload up to 3 times with exponential backoff
2. Log each retry attempt
3. If all retries fail, report the specific asset
4. Continue uploading remaining assets
5. Report incomplete upload at the end

### Validation Failures

**Scenario**: Configuration validation detects errors

**Handling**:
1. Report all validation errors together
2. Provide specific remediation guidance
3. Do not proceed with build
4. Exit with non-zero status code
5. Log validation errors to file

## Testing Strategy

### Unit Testing

**Build Module Tests**:
- Test artifact collection from build output
- Test platform-specific build configuration
- Test error handling for build failures
- Test artifact metadata extraction

**Checksum Generator Tests**:
- Test SHA-256 hash calculation
- Test checksums.txt file formatting
- Test checksum verification
- Test handling of missing files

**Release Manager Tests**:
- Test release notes extraction from CHANGELOG
- Test GitHub API interaction (mocked)
- Test asset upload retry logic
- Test release metadata generation

### Property-Based Testing

**Property Test 1: Checksum Verification**
- Generate random file content
- Calculate checksum
- Verify checksum matches recalculation
- **Validates: Property 2**

**Property Test 2: Filename Pattern Matching**
- Generate random version, platform, architecture combinations
- Create filename using template
- Verify filename matches expected pattern
- **Validates: Property 3**

**Property Test 3: Release Notes Extraction**
- Generate random CHANGELOG content with multiple versions
- Extract notes for each version
- Verify extracted content matches expected section
- **Validates: Property 5**

### Integration Testing

**End-to-End Release Test**:
1. Set up test environment with mock GitHub API
2. Run complete release workflow
3. Verify all artifacts created
4. Verify checksums generated correctly
5. Verify release created with all assets
6. Clean up test artifacts

**Multi-Platform Build Test**:
1. Configure builds for all platforms
2. Execute build process
3. Verify artifacts for each platform
4. Verify artifact naming conventions
5. Verify artifact file sizes are reasonable

## Implementation Details

### Script Organization

```
scripts/
├── build.js                    # Main build orchestration
├── generate-checksums.js       # Checksum generation
├── prepare-release.ps1         # Pre-release validation
├── release-to-github.ps1       # GitHub release creation
├── sign-windows.js             # Windows code signing
├── sign-macos.js               # macOS code signing
└── verify-build-config.js      # Configuration validation
```

### Build Process Flow

```
1. Validate Configuration
   ├── Check package.json
   ├── Verify build config
   ├── Check environment variables
   └── Validate working directory

2. Build Installers
   ├── Build Windows (NSIS + Portable)
   ├── Build macOS (DMG + ZIP, x64 + arm64)
   └── Build Linux (AppImage + DEB)

3. Sign Installers
   ├── Sign Windows executables
   ├── Sign macOS applications
   └── Notarize macOS applications

4. Generate Checksums
   ├── Calculate SHA-256 for each artifact
   ├── Format checksums.txt
   └── Verify checksum file

5. Verify Artifacts
   ├── Check all expected files exist
   ├── Verify file sizes
   └── Validate checksums

6. Create GitHub Release
   ├── Extract release notes
   ├── Create release via API
   ├── Upload all artifacts
   └── Publish release

7. Report Results
   ├── List created artifacts
   ├── Show release URL
   └── Report any warnings
```

### Environment Variables

**Required for Windows Signing**:
- `WINDOWS_CERTIFICATE_FILE`: Path to PFX certificate
- `WINDOWS_CERTIFICATE_PASSWORD`: Certificate password

**Required for macOS Signing**:
- `APPLE_ID`: Apple Developer account email
- `APPLE_ID_PASSWORD`: App-specific password
- `APPLE_TEAM_ID`: Apple Developer Team ID
- `CSC_LINK`: Path to signing certificate
- `CSC_KEY_PASSWORD`: Certificate password

**Required for GitHub Release**:
- `GITHUB_TOKEN`: Personal access token with repo scope

### Artifact Naming Conventions

**Windows**:
- NSIS: `PEFT-Studio-Setup-{version}.exe`
- Portable: `PEFT-Studio-Portable-{version}.exe`

**macOS**:
- DMG (x64): `PEFT-Studio-{version}-x64.dmg`
- DMG (arm64): `PEFT-Studio-{version}-arm64.dmg`
- ZIP (x64): `PEFT-Studio-{version}-x64.zip`
- ZIP (arm64): `PEFT-Studio-{version}-arm64.zip`

**Linux**:
- AppImage: `PEFT-Studio-{version}-x64.AppImage`
- DEB: `PEFT-Studio-{version}-x64.deb`

### Checksum File Format

```
<sha256-hash>  <filename>
<sha256-hash>  <filename>
...
```

Example:
```
a1b2c3d4...  PEFT-Studio-Setup-1.0.1.exe
e5f6g7h8...  PEFT-Studio-1.0.1-x64.dmg
i9j0k1l2...  PEFT-Studio-1.0.1-x64.AppImage
```

## Security Considerations

### Code Signing

- Store signing certificates securely (not in repository)
- Use environment variables for certificate passwords
- Implement certificate expiration monitoring
- Rotate certificates before expiration

### Checksum Verification

- Use SHA-256 (not MD5 or SHA-1)
- Include checksums in release assets
- Document verification process for users
- Provide verification scripts

### GitHub Token Security

- Use personal access tokens with minimal scope (repo only)
- Store tokens in environment variables
- Never commit tokens to repository
- Rotate tokens periodically

### Artifact Integrity

- Verify artifacts before upload
- Use HTTPS for all API communication
- Implement upload retry with verification
- Log all upload operations

## Performance Considerations

### Build Optimization

- Build platforms in parallel when possible
- Cache dependencies between builds
- Use incremental builds when appropriate
- Optimize artifact compression

### Upload Optimization

- Upload assets in parallel
- Use chunked uploads for large files
- Implement resume capability for failed uploads
- Monitor upload progress

### Checksum Generation

- Use streaming hash calculation for large files
- Process multiple files in parallel
- Cache checksums when files haven't changed
- Optimize file I/O operations

