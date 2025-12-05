# Design Document

## Overview

This design document outlines the approach for improving code quality, fixing test issues, and establishing an automated release pipeline for PEFT Studio. The solution addresses linting violations through automated fixes and manual corrections, resolves test failures through proper mocking and cleanup, configures Electron Builder for Windows installer generation, and implements GitHub Actions workflows for automated releases.

The system will transform the current state (421 linting warnings, failing tests, manual builds) into a production-ready state with zero warnings, passing tests under 60 seconds, and automated Windows installer generation on version tags.

## Architecture

### Component Overview

The solution consists of four main components:

1. **Linting System**: ESLint configuration and automated fixes
2. **Testing Infrastructure**: Jest/Vitest test framework with proper mocking
3. **Build System**: Electron Builder with NSIS configuration
4. **CI/CD Pipeline**: GitHub Actions workflows for automated releases

### Data Flow

```
Developer Push → GitHub Actions Trigger → Build Frontend → Package Electron App → Generate Installer → Publish to GitHub Releases → User Downloads from README
```

### Technology Stack

- **Linting**: ESLint 9.x with TypeScript and React plugins
- **Testing**: Vitest 4.x with Testing Library
- **Build**: Electron Builder 25.x with NSIS
- **CI/CD**: GitHub Actions with Windows runners
- **Package Management**: npm with package-lock.json

## Components and Interfaces

### 1. Linting Configuration

**ESLint Configuration** (`.eslintrc.json`)
- Parser: `@typescript-eslint/parser`
- Plugins: `@typescript-eslint`, `react`, `react-hooks`
- Rules: Enforce display names, minimize `any` usage, proper hook dependencies

**Auto-fix Strategy**:
- Run `eslint --fix` for automatic corrections
- Manual fixes for React hooks violations
- Entity escaping for JSX special characters

### 2. Test Infrastructure

**Test Setup** (`src/test/setup.ts`)
```typescript
interface TestSetup {
  beforeEach: () => void;
  afterEach: () => void;
  mockConsole: () => void;
  useFakeTimers: () => void;
}
```

**Error Boundary Test Fixes**:
- Mock `console.error` to prevent test failures
- Use fake timers for async operations
- Proper cleanup in `afterEach` hooks

### 3. Build Configuration

**Electron Builder Config** (`package.json` build section)
```json
{
  "build": {
    "appId": "com.peftstudio.app",
    "productName": "PEFT Studio",
    "files": ["dist/**/*", "electron/**/*", "backend/**/*"],
    "win": {
      "target": "nsis",
      "requestedExecutionLevel": "asInvoker"
    },
    "nsis": {
      "oneClick": false,
      "allowToChangeInstallationDirectory": true,
      "createDesktopShortcut": true
    }
  }
}
```

**Build Scripts**:
- `build`: TypeScript compilation + Vite build
- `electron:build`: Full build + Electron Builder packaging

### 4. GitHub Actions Workflow

**Workflow Structure** (`.github/workflows/release.yml`)
```yaml
trigger: push to tags v*
runner: windows-latest
steps:
  - checkout
  - setup node 20
  - install dependencies
  - build frontend
  - build electron app
  - upload to GitHub Releases
```

## Data Models

### Linting Error Model
```typescript
interface LintError {
  file: string;
  line: number;
  column: number;
  rule: string;
  message: string;
  severity: 'error' | 'warning';
  fixable: boolean;
}
```

### Test Result Model
```typescript
interface TestResult {
  name: string;
  status: 'passed' | 'failed' | 'skipped';
  duration: number;
  error?: string;
}
```

### Build Artifact Model
```typescript
interface BuildArtifact {
  name: string;
  path: string;
  size: number;
  checksum: string;
  platform: 'win' | 'mac' | 'linux';
}
```

### Release Model
```typescript
interface Release {
  version: string;
  tag: string;
  artifacts: BuildArtifact[];
  releaseNotes: string;
  publishedAt: Date;
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Linting Completeness
*For any* source file in the `src` directory, running ESLint should produce zero errors and zero warnings after fixes are applied.
**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**

### Property 2: Test Execution Speed
*For any* test suite execution, the total runtime should be less than 90 seconds when all tests pass.
**Validates: Requirements 2.1**

### Property 3: Test Cleanup Completeness
*For any* test execution, all mocks, timers, and handles should be cleaned up after the test completes, leaving no memory leaks or open handles.
**Validates: Requirements 2.3, 2.5**

### Property 4: Build Artifact Completeness
*For any* successful Electron Builder execution, the output directory should contain a valid NSIS installer executable with all required resources (dist, electron, backend).
**Validates: Requirements 3.1, 3.2, 3.3**

### Property 5: Installer Execution Success
*For any* generated installer executable, running it should successfully install the application without requiring administrator privileges by default.
**Validates: Requirements 3.4, 3.5**

### Property 6: Workflow Trigger Reliability
*For any* version tag push matching the pattern `v*`, the GitHub Actions release workflow should trigger automatically within 60 seconds.
**Validates: Requirements 4.1**

### Property 7: Release Artifact Availability
*For any* successful workflow execution, the generated installer should be available as a downloadable asset on the GitHub Releases page.
**Validates: Requirements 4.3, 4.4**

### Property 8: README Download Link Validity
*For any* published release, the download badge in the README should link to a valid GitHub release page containing the installer executable.
**Validates: Requirements 5.1, 5.2, 5.3**

### Property 9: CI Test Success Rate
*For any* CI workflow execution, all test jobs (lint, test-frontend, test-backend, build-check) should complete successfully with zero failures.
**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**

### Property 10: Test Execution Performance
*For any* local test execution using npm run test, the total execution time should be less than 90 seconds for the complete test suite.
**Validates: Requirements 7.1, 7.2, 7.3**

## Error Handling

### Linting Errors
- **Unfixable Errors**: Manual intervention required, provide clear guidance
- **Configuration Errors**: Validate ESLint config before running
- **File Access Errors**: Check file permissions and paths

### Test Errors
- **Timeout Errors**: Increase timeout or use fake timers
- **Mock Errors**: Ensure proper mock setup and cleanup
- **Assertion Errors**: Review test expectations and actual behavior

### Build Errors
- **Missing Dependencies**: Run `npm install` before building
- **TypeScript Errors**: Fix type errors before building
- **Resource Missing**: Ensure all required files exist in specified paths

### CI/CD Errors
- **Authentication Errors**: Verify `GITHUB_TOKEN` permissions
- **Build Failures**: Check logs for specific error messages
- **Upload Failures**: Verify artifact paths and GitHub API availability

## Testing Strategy

### Unit Testing

Unit tests will cover:
- Individual linting rule fixes
- Test mock setup and cleanup functions
- Build configuration validation
- Workflow YAML syntax validation

### Property-Based Testing

Property-based tests will use `fast-check` library to verify:
- Property 1: Linting completeness across random file samples
- Property 2: Test execution speed with varying test counts
- Property 3: Test cleanup completeness with random mock scenarios
- Property 4: Build artifact completeness with different configurations
- Property 7: Release artifact availability across multiple releases

### Integration Testing

Integration tests will verify:
- End-to-end linting process (run ESLint → apply fixes → verify zero warnings)
- End-to-end test execution (setup → run tests → cleanup → verify results)
- End-to-end build process (clean → build frontend → package electron → verify installer)
- End-to-end release workflow (push tag → trigger workflow → build → publish → verify download)

### Manual Testing

Manual verification required for:
- Installer execution on clean Windows machine
- SmartScreen warning handling
- Desktop shortcut creation
- Application launch after installation
- README download link functionality

### Test Configuration

- **Framework**: Vitest 4.x
- **Property Testing Library**: fast-check 3.x
- **Minimum Iterations**: 100 per property test
- **Timeout**: 30 seconds per test, 60 seconds for integration tests
- **Coverage Target**: 80% for new code

### Test Organization

```
src/test/
  ├── linting/
  │   ├── eslint-fixes.test.ts
  │   └── eslint-fixes.pbt.test.ts
  ├── testing/
  │   ├── mock-cleanup.test.ts
  │   └── test-performance.pbt.test.ts
  └── build/
      ├── electron-builder.test.ts
      └── artifact-validation.pbt.test.ts

.github/workflows/
  └── test/
      ├── workflow-validation.test.ts
      └── release-process.pbt.test.ts
```

## Implementation Notes

### Prerequisites (Manual Steps)

Before automated fixes can be applied, the following manual steps must be completed:

1. **Clean Project Environment**:
   ```bash
   rm -rf node_modules package-lock.json dist release
   npm install
   npm install --save-dev electron-builder electron-updater
   ```

2. **Update package.json**:
   - Ensure `main` points to `electron/main.js`
   - Add `electron:build` script: `npm run build && electron-builder build --win --x64`
   - Verify all dependencies are listed

3. **Create electron-builder.json**:
   - Configure NSIS installer settings
   - Specify file inclusions (dist, electron, backend)
   - Set Windows-specific options

### Linting Implementation

1. Run automated fixes: `npm run lint:fix`
2. Manually fix React hooks violations:
   - Add proper dependency arrays
   - Move state updates to event handlers
   - Add conditional checks in useEffect
3. Fix entity escaping:
   - Replace `'` with `&apos;` or `{" '"}` 
   - Replace `"` with `&quot;` or `{' " '}`
4. Add display names to components:
   ```typescript
   Component.displayName = 'ComponentName';
   ```

### Test Implementation

1. Update `src/test/setup.ts`:
   ```typescript
   afterEach(() => {
     vi.clearAllMocks();
     vi.clearAllTimers();
   });
   ```

2. Fix ErrorBoundary test:
   ```typescript
   const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
   // ... test code ...
   consoleSpy.mockRestore();
   ```

3. Use fake timers for async tests:
   ```typescript
   vi.useFakeTimers();
   // ... test code ...
   vi.useRealTimers();
   ```

### Build Implementation

The existing `package.json` already contains a comprehensive Electron Builder configuration. Key points:
- NSIS installer configured with user-level installation
- Portable executable also generated
- Backend resources included in build
- File associations configured for `.peft` files

### CI/CD Implementation

Create `.github/workflows/release.yml` with:
- Trigger on version tags (`v*`)
- Windows runner for NSIS builds
- Node.js 20 setup
- Dependency caching
- Build and package steps
- GitHub Release upload with `softprops/action-gh-release`

### README Implementation

Add download section:
```markdown
## Download

[![Download](https://img.shields.io/github/downloads/Ankesh-007/peft-studio/total?style=for-the-badge&label=Download%20Windows%20Installer&color=blue)](https://github.com/Ankesh-007/peft-studio/releases/latest)

### Installation

1. Download the `.exe` installer from the link above
2. Run the installer (Windows SmartScreen may warn you; click "More Info" → "Run Anyway")
3. Follow the installation wizard
4. Launch PEFT Studio from the desktop shortcut or Start menu
```

## Performance Considerations

- **Linting**: Run in parallel for multiple files
- **Testing**: Use test sharding for large test suites
- **Building**: Enable caching for node_modules and build artifacts
- **CI/CD**: Use GitHub Actions caching for dependencies

## Security Considerations

- **Code Signing**: Windows installer is not code-signed (requires certificate)
- **SmartScreen**: Users will see warnings on first run
- **Dependencies**: Regular security audits with `npm audit`
- **Secrets**: Use GitHub Secrets for sensitive tokens

## Deployment Strategy

1. **Development**: Local testing with `npm run electron:build`
2. **Staging**: Test release workflow with dry-run mode
3. **Production**: Push version tag to trigger automated release
4. **Rollback**: Delete release and tag if issues found

## Monitoring and Observability

- **Linting**: Track warning count over time
- **Testing**: Monitor test execution time and failure rates
- **Building**: Track build success rate and duration
- **Releases**: Monitor download counts and user feedback

## CI Test Failure Resolution Strategy

### Identifying Failing Tests

1. **Review CI Logs**: Examine GitHub Actions workflow logs to identify specific failing tests
2. **Categorize Failures**: Group failures by type (unit, integration, property-based, build)
3. **Prioritize Fixes**: Address critical failures first (blocking CI) before optimization

### Common CI Test Failure Patterns

1. **Timeout Issues**: Tests that pass locally but timeout in CI due to slower runners
   - Solution: Increase timeout values or optimize test execution
   
2. **Environment Differences**: Tests that depend on local environment setup
   - Solution: Mock external dependencies, use test fixtures
   
3. **Race Conditions**: Tests that fail intermittently due to timing issues
   - Solution: Use fake timers, add proper async/await handling
   
4. **Missing Dependencies**: Tests that fail due to missing packages in CI
   - Solution: Update CI workflow to install all required dependencies

### Test Performance Optimization Strategy

1. **Identify Slow Tests**: Use vitest --reporter=verbose to find tests taking >5 seconds
2. **Parallelize Tests**: Configure vitest to run tests in parallel (default behavior)
3. **Mock External Resources**: Replace API calls, file I/O with mocks
4. **Use Fake Timers**: Replace setTimeout/setInterval with vi.useFakeTimers()
5. **Optimize Test Setup**: Move expensive setup to beforeAll instead of beforeEach
6. **Skip Unnecessary Tests**: Use test.skip for tests that don't need to run on every change

### Implementation Approach

1. **Phase 1: Fix Critical CI Failures**
   - Fix tests that are currently failing in CI
   - Ensure all jobs pass (lint, test-frontend, test-backend, build-check)
   
2. **Phase 2: Optimize Test Performance**
   - Profile test execution to identify slow tests
   - Apply optimization techniques (mocking, parallelization, fake timers)
   - Verify tests complete within 60 seconds locally

3. **Phase 3: Prevent Future Failures**
   - Add pre-commit hooks to run tests locally
   - Configure CI to fail fast on first error
   - Add test performance monitoring

## Future Enhancements

- Code signing certificate for Windows
- macOS and Linux installer automation
- Automated changelog generation
- Release notes from commit messages
- Automated version bumping
- Pre-release and beta channels
- Test result caching in CI
- Parallel test execution across multiple CI runners
