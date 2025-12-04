# Repository Professionalization Design

## Overview

This design document outlines the system for professionalizing the PEFT Studio repository by automating the complete release process, cleaning unnecessary files, and ensuring the repository presents a professional appearance. The system builds on existing scripts and infrastructure while adding new capabilities for repository cleanup, documentation enhancement, and automated release management.

The design focuses on:
- **Automation**: Single-command execution for the entire release workflow
- **Cleanliness**: Removing build artifacts and temporary files while preserving essential content
- **Professionalism**: Ensuring documentation, metadata, and structure meet industry standards
- **Security**: Generating checksums and validating releases
- **Reliability**: Comprehensive validation and error handling

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│            Repository Professionalization System             │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Cleanup    │  │    Build     │  │   Checksum   │      │
│  │   Module     │→ │   Module     │→ │   Module     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         ↓                  ↓                  ↓              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Documentation│  │  Validation  │  │   Release    │      │
│  │   Enhancer   │  │   Module     │  │   Manager    │      │
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

1. **Cleanup Phase**: Remove unnecessary files and update .gitignore
2. **Validation Phase**: Verify repository structure and readiness
3. **Documentation Phase**: Enhance README and documentation
4. **Build Phase**: Create installers for all platforms
5. **Checksum Phase**: Generate SHA-256 checksums
6. **Verification Phase**: Validate all artifacts
7. **Release Phase**: Create GitHub release and upload assets
8. **Finalization Phase**: Update repository metadata and tags

## Components and Interfaces

### 1. Cleanup Module

**Purpose**: Removes unnecessary files while preserving essential content

**Interface**:
```typescript
interface CleanupModule {
  identifyUnnecessaryFiles(): Promise<FileList>;
  removeFiles(files: FileList): Promise<CleanupResult>;
  updateGitignore(patterns: string[]): Promise<void>;
  generateCleanupReport(): CleanupReport;
}

interface FileList {
  buildArtifacts: string[];
  temporaryFiles: string[];
  testCaches: string[];
  redundantDocs: string[];
}

interface CleanupResult {
  removed: string[];
  preserved: string[];
  errors: string[];
  totalSizeFreed: number;
}

interface CleanupReport {
  filesRemoved: number;
  sizeFreed: string;
  categoriesCleared: string[];
  timestamp: string;
}
```

**Responsibilities**:
- Identify build artifacts in release/, dist/, build/ directories
- Remove test caches (.pytest_cache/, .hypothesis/)
- Clean temporary files and logs
- Remove redundant documentation files (*_SUMMARY.md, *_STATUS.md)
- Update .gitignore to prevent re-addition
- Generate cleanup summary report

### 2. Build Module

**Purpose**: Orchestrates multi-platform installer builds

**Interface**:
```typescript
interface BuildModule {
  buildAll(): Promise<BuildResult>;
  buildPlatform(platform: Platform): Promise<PlatformBuildResult>;
  verifyBuildOutputs(): Promise<VerificationResult>;
}

interface BuildResult {
  platforms: PlatformBuildResult[];
  totalArtifacts: number;
  success: boolean;
  duration: number;
}

interface PlatformBuildResult {
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
  platform: string;
  architecture: string;
}
```

**Responsibilities**:
- Execute electron-builder for Windows (NSIS + Portable)
- Execute electron-builder for macOS (DMG + ZIP, x64 + arm64)
- Execute electron-builder for Linux (AppImage + DEB)
- Collect and catalog all generated artifacts
- Verify expected outputs exist
- Report build status and errors

### 3. Checksum Module

**Purpose**: Generates and verifies SHA-256 checksums

**Interface**:
```typescript
interface ChecksumModule {
  generateChecksums(artifacts: Artifact[]): Promise<Checksum[]>;
  writeChecksumsFile(checksums: Checksum[], path: string): Promise<void>;
  verifyChecksums(checksumFile: string): Promise<VerificationResult>;
}

interface Checksum {
  filename: string;
  hash: string;
  algorithm: 'sha256';
  size: number;
}

interface VerificationResult {
  valid: boolean;
  verified: string[];
  failed: string[];
  missing: string[];
}
```

**Responsibilities**:
- Calculate SHA-256 hashes for all installer artifacts
- Format checksums in standard format (hash  filename)
- Write SHA256SUMS.txt file
- Verify checksums by recalculation
- Report verification status

### 4. Documentation Enhancer

**Purpose**: Improves repository documentation and metadata

**Interface**:
```typescript
interface DocumentationEnhancer {
  enhanceReadme(): Promise<void>;
  addBadges(): Promise<void>;
  verifyDocumentation(): Promise<DocVerificationResult>;
  updateMetadata(): Promise<void>;
}

interface DocVerificationResult {
  readmeComplete: boolean;
  contributingExists: boolean;
  licenseExists: boolean;
  changelogCurrent: boolean;
  missingDocs: string[];
}
```

**Responsibilities**:
- Ensure README includes all required sections
- Add/update badges (version, license, downloads)
- Verify CONTRIBUTING.md exists and is complete
- Ensure LICENSE file is present
- Verify CHANGELOG.md has current version entry
- Update package.json metadata

### 5. Validation Module

**Purpose**: Validates repository readiness for release

**Interface**:
```typescript
interface ValidationModule {
  validateStructure(): Promise<StructureValidation>;
  validateMetadata(): Promise<MetadataValidation>;
  validateReadiness(): Promise<ReadinessValidation>;
}

interface StructureValidation {
  valid: boolean;
  gitignoreCorrect: boolean;
  docsWellFormatted: boolean;
  licenseExists: boolean;
  errors: string[];
}

interface MetadataValidation {
  valid: boolean;
  packageJsonComplete: boolean;
  versionValid: boolean;
  repositoryUrlCorrect: boolean;
  errors: string[];
}

interface ReadinessValidation {
  ready: boolean;
  testsPass: boolean;
  changelogUpdated: boolean;
  workingDirectoryClean: boolean;
  issues: string[];
}
```

**Responsibilities**:
- Verify repository structure follows best practices
- Validate package.json completeness
- Check version follows semantic versioning
- Verify all tests pass
- Ensure CHANGELOG has current version
- Check working directory is clean

### 6. Release Manager

**Purpose**: Creates and manages GitHub releases

**Interface**:
```typescript
interface ReleaseManager {
  createRelease(options: ReleaseOptions): Promise<Release>;
  uploadAssets(release: Release, artifacts: Artifact[]): Promise<void>;
  extractReleaseNotes(version: string): Promise<string>;
  publishRelease(release: Release): Promise<void>;
  createGitTag(version: string): Promise<void>;
}

interface ReleaseOptions {
  version: string;
  tag: string;
  name: string;
  body: string;
  draft: boolean;
  prerelease: boolean;
  repository: string;
}

interface Release {
  id: number;
  url: string;
  tag: string;
  uploadUrl: string;
  assets: Asset[];
}

interface Asset {
  id: number;
  name: string;
  size: number;
  downloadUrl: string;
}
```

**Responsibilities**:
- Create GitHub release via API
- Extract release notes from CHANGELOG.md
- Upload all installer artifacts
- Upload checksums file
- Create and push git tag
- Publish release

## Data Models

### Repository Structure

```typescript
interface RepositoryStructure {
  root: string;
  directories: {
    source: string[];
    build: string[];
    docs: string[];
    scripts: string[];
  };
  essentialFiles: string[];
  unnecessaryPatterns: string[];
}
```

### Release Configuration

```typescript
interface ReleaseConfiguration {
  version: string;
  repository: {
    owner: string;
    name: string;
    url: string;
  };
  platforms: PlatformConfig[];
  artifacts: ArtifactConfig;
  checksums: ChecksumConfig;
}

interface PlatformConfig {
  name: 'windows' | 'macos' | 'linux';
  enabled: boolean;
  targets: string[];
  architectures: string[];
}

interface ArtifactConfig {
  outputDirectory: string;
  namingTemplate: string;
  expectedFiles: string[];
}

interface ChecksumConfig {
  algorithm: 'sha256';
  filename: string;
  format: string;
}
```

### Cleanup Configuration

```typescript
interface CleanupConfiguration {
  directories: {
    buildArtifacts: string[];
    testCaches: string[];
    temporary: string[];
  };
  filePatterns: {
    remove: string[];
    preserve: string[];
  };
  gitignorePatterns: string[];
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Cleanup Idempotence

*For any* repository state, running cleanup multiple times must produce the same result as running it once.

**Validates: Requirements 4.1, 4.2, 4.3**

### Property 2: Build Completeness

*For any* enabled platform, the build process must generate all expected installer artifacts for that platform.

**Validates: Requirements 1.1, 1.2, 1.3, 1.5**

### Property 3: Checksum Consistency

*For any* artifact, recalculating its checksum must produce the same hash as recorded in SHA256SUMS.txt.

**Validates: Requirements 2.1, 2.5**

### Property 4: Checksum File Format

*For any* line in SHA256SUMS.txt, it must match the format `^[a-f0-9]{64}  .+$` (64-character hex hash, two spaces, filename).

**Validates: Requirements 2.3**

### Property 5: Essential File Preservation

*For any* cleanup operation, all files matching essential patterns (source code, documentation, configuration) must be preserved.

**Validates: Requirements 4.3**

### Property 6: Release Asset Completeness

*For any* GitHub release, the number of uploaded assets must equal the number of built artifacts plus one (for checksums file).

**Validates: Requirements 3.3, 3.4**

### Property 7: Version Consistency

*For any* release, the version in package.json, git tag, and GitHub release must all match.

**Validates: Requirements 3.2, 8.5**

### Property 8: Gitignore Effectiveness

*For any* file pattern added to .gitignore, running `git status` must not show files matching that pattern.

**Validates: Requirements 4.4**

## Error Handling

### Cleanup Failures

**Scenario**: File deletion fails due to permissions

**Handling**:
1. Log specific file and error
2. Continue with remaining files
3. Report all failures at end
4. Provide remediation guidance
5. Exit with non-zero status if critical files failed

### Build Failures

**Scenario**: electron-builder fails for a platform

**Handling**:
1. Capture detailed error output
2. Continue building other platforms if possible
3. Report all failures at end
4. Provide platform-specific troubleshooting
5. Exit with non-zero status

### Upload Failures

**Scenario**: GitHub API fails to upload asset

**Handling**:
1. Retry upload up to 3 times with exponential backoff
2. Log each retry attempt
3. If all retries fail, report specific asset
4. Continue uploading remaining assets
5. Report incomplete upload at end

### Validation Failures

**Scenario**: Repository not ready for release

**Handling**:
1. Report all validation errors together
2. Provide specific remediation for each issue
3. Do not proceed with release
4. Exit with non-zero status
5. Log validation report to file

## Testing Strategy

### Unit Testing

**Cleanup Module Tests**:
- Test file identification logic
- Test file removal with mocked filesystem
- Test .gitignore update
- Test cleanup report generation

**Checksum Module Tests**:
- Test SHA-256 calculation
- Test checksum file formatting
- Test checksum verification
- Test handling of missing files

**Documentation Enhancer Tests**:
- Test README enhancement
- Test badge generation
- Test metadata updates
- Test documentation verification

**Release Manager Tests**:
- Test release notes extraction
- Test GitHub API interaction (mocked)
- Test asset upload retry logic
- Test git tag creation

### Property-Based Testing

**Property Test 1: Cleanup Idempotence**
- Generate random repository state
- Run cleanup twice
- Verify same files removed both times
- **Validates: Property 1**

**Property Test 2: Checksum Verification**
- Generate random file content
- Calculate checksum
- Verify checksum matches recalculation
- **Validates: Property 3**

**Property Test 3: Checksum Format**
- Generate random checksums
- Write to file
- Verify each line matches format regex
- **Validates: Property 4**

**Property Test 4: Essential File Preservation**
- Generate random file tree with essential and non-essential files
- Run cleanup
- Verify all essential files still exist
- **Validates: Property 5**

### Integration Testing

**End-to-End Release Test**:
1. Set up test repository
2. Run complete release workflow
3. Verify all artifacts created
4. Verify checksums generated correctly
5. Verify release created (with mock GitHub API)
6. Clean up test artifacts

**Multi-Platform Build Test**:
1. Configure builds for all platforms
2. Execute build process
3. Verify artifacts for each platform
4. Verify artifact naming conventions
5. Verify artifact sizes are reasonable

## Implementation Details

### Script Organization

```
scripts/
├── cleanup-repository.js       # Repository cleanup
├── build.js                    # Build orchestration (existing)
├── generate-checksums.js       # Checksum generation (existing)
├── enhance-documentation.js    # Documentation enhancement
├── validate-release.js         # Release validation
├── release-to-github.ps1       # GitHub release (existing, enhanced)
└── complete-release.ps1        # Master orchestration script
```

### Cleanup Process

```
1. Identify Unnecessary Files
   ├── Build artifacts (release/*, dist/*, build/*)
   ├── Test caches (.pytest_cache/, .hypothesis/)
   ├── Temporary files (*.tmp, *.log)
   └── Redundant docs (*_SUMMARY.md, *_STATUS.md)

2. Preserve Essential Files
   ├── Latest release installers
   ├── Source code (src/, backend/)
   ├── Documentation (docs/, *.md)
   └── Configuration files

3. Remove Files
   ├── Delete identified files
   ├── Log each deletion
   └── Report errors

4. Update .gitignore
   ├── Add patterns for removed files
   ├── Ensure no duplicates
   └── Verify effectiveness

5. Generate Report
   ├── Files removed count
   ├── Size freed
   └── Categories cleared
```

### Build Process

```
1. Validate Prerequisites
   ├── Check node_modules exists
   ├── Verify build configuration
   └── Check environment variables

2. Build Frontend
   ├── Run TypeScript compilation
   ├── Run Vite build
   └── Verify dist/ output

3. Build Installers
   ├── Windows (NSIS + Portable)
   ├── macOS (DMG + ZIP, x64 + arm64)
   └── Linux (AppImage + DEB)

4. Collect Artifacts
   ├── List all generated files
   ├── Extract metadata
   └── Verify completeness

5. Generate Checksums
   ├── Calculate SHA-256 for each artifact
   ├── Write SHA256SUMS.txt
   └── Verify checksums
```

### Release Process

```
1. Cleanup Repository
   └── Remove unnecessary files

2. Validate Readiness
   ├── Check tests pass
   ├── Verify CHANGELOG updated
   ├── Check working directory clean
   └── Validate metadata

3. Build Installers
   └── Build for all platforms

4. Generate Checksums
   └── Create SHA256SUMS.txt

5. Enhance Documentation
   ├── Update README badges
   ├── Verify documentation complete
   └── Update metadata

6. Create GitHub Release
   ├── Extract release notes
   ├── Create release via API
   ├── Upload all artifacts
   └── Upload checksums

7. Create Git Tag
   ├── Tag current commit
   └── Push tag to origin

8. Generate Report
   ├── List created artifacts
   ├── Show release URL
   └── Report any warnings
```

### File Patterns

**Files to Remove**:
```
release/**/*                    # Build artifacts (except latest)
dist/**/*                       # Distribution files
build/**/*                      # Build outputs
.pytest_cache/**/*              # Python test cache
.hypothesis/**/*                # Hypothesis test cache
backend/__pycache__/**/*        # Python bytecode
**/*.pyc                        # Python compiled files
**/*_SUMMARY.md                 # Redundant summaries
**/*_STATUS.md                  # Status files
**/*_COMPLETE.md                # Completion files
*.log                           # Log files
*.tmp                           # Temporary files
```

**Files to Preserve**:
```
src/**/*                        # Source code
backend/**/*.py                 # Python source
docs/**/*                       # Documentation
scripts/**/*                    # Build scripts
*.md                            # Markdown docs (except redundant)
package.json                    # Package metadata
tsconfig.json                   # TypeScript config
*.config.js                     # Configuration files
.gitignore                      # Git ignore
LICENSE                         # License file
```

### Environment Variables

**Required for GitHub Release**:
- `GITHUB_TOKEN`: Personal access token with repo scope
- `GITHUB_REPOSITORY`: Repository in format `owner/repo`

**Optional**:
- `SKIP_TESTS`: Skip test execution (default: false)
- `SKIP_BUILD`: Skip build step (default: false)
- `DRY_RUN`: Simulate without making changes (default: false)

### Artifact Naming

**Windows**:
- `PEFT-Studio-Setup-{version}.exe` (NSIS installer)
- `PEFT-Studio-Portable-{version}.exe` (Portable)

**macOS**:
- `PEFT-Studio-{version}-x64.dmg` (Intel DMG)
- `PEFT-Studio-{version}-arm64.dmg` (Apple Silicon DMG)
- `PEFT-Studio-{version}-x64.zip` (Intel ZIP)
- `PEFT-Studio-{version}-arm64.zip` (Apple Silicon ZIP)

**Linux**:
- `PEFT-Studio-{version}-x64.AppImage` (AppImage)
- `PEFT-Studio-{version}-amd64.deb` (Debian package)

**Checksums**:
- `SHA256SUMS.txt` (All checksums)

## Security Considerations

### Checksum Security

- Use SHA-256 (not MD5 or SHA-1)
- Include checksums in release assets
- Document verification process for users
- Provide verification scripts

### GitHub Token Security

- Use personal access tokens with minimal scope
- Store tokens in environment variables
- Never commit tokens to repository
- Rotate tokens periodically

### File Cleanup Security

- Verify file paths before deletion
- Never delete files outside repository
- Log all deletions for audit trail
- Provide dry-run mode for testing

### Release Integrity

- Verify artifacts before upload
- Use HTTPS for all API communication
- Implement upload retry with verification
- Log all upload operations

## Performance Considerations

### Cleanup Optimization

- Use parallel file deletion when safe
- Stream large file operations
- Cache file system queries
- Optimize pattern matching

### Build Optimization

- Build platforms in parallel when possible
- Cache dependencies between builds
- Use incremental builds when appropriate
- Optimize artifact compression

### Upload Optimization

- Upload assets in parallel
- Use chunked uploads for large files
- Implement resume capability
- Monitor upload progress

### Checksum Generation

- Use streaming hash calculation
- Process multiple files in parallel
- Cache checksums when files unchanged
- Optimize file I/O operations
