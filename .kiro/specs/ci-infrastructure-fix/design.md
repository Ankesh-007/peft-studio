# Design Document

## Overview

This design document outlines a systematic approach to diagnosing and fixing the 8 failing CI checks in the PEFT Studio repository. The solution follows a "Diagnosis First, Fix Second" methodology, prioritizing understanding root causes before applying fixes. The approach ensures fixes work in both CI and local environments, preventing future regressions.

The CI pipeline consists of 5 main jobs:
1. **Lint** - ESLint and TypeScript type checking
2. **Test Frontend** - Vitest unit, integration, and property-based tests
3. **Test Backend** - pytest for Python backend services
4. **Build Check** - Multi-platform builds (Ubuntu, Windows, macOS)
5. **Security Scan** - npm audit and pip-audit for vulnerabilities

The design addresses each failure systematically, starting with linting (which often blocks other steps), then builds, then tests, ensuring each fix is reproducible locally before pushing to CI.

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions CI                         │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Lint   │  │ Test Frontend│  │ Test Backend │          │
│  │  Job     │  │    Job       │  │    Job       │          │
│  └────┬─────┘  └──────┬───────┘  └──────┬───────┘          │
│       │               │                  │                   │
│  ┌────▼───────────────▼──────────────────▼───────┐          │
│  │         Build Check (Matrix)                   │          │
│  │  Ubuntu │ Windows │ macOS                      │          │
│  └────────────────────┬───────────────────────────┘          │
│                       │                                       │
│  ┌────────────────────▼───────────────────────────┐          │
│  │         Security Scan                           │          │
│  └────────────────────┬───────────────────────────┘          │
│                       │                                       │
│  ┌────────────────────▼───────────────────────────┐          │
│  │         All Checks Passed                       │          │
│  └─────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### Diagnosis Workflow

```
1. Fetch CI Logs → 2. Categorize Failures → 3. Identify Root Causes
                                                      ↓
                                            4. Reproduce Locally
                                                      ↓
                                            5. Apply Targeted Fix
                                                      ↓
                                            6. Verify Locally
                                                      ↓
                                            7. Push & Verify CI
```

### Technology Stack

- **Frontend**: React 18, TypeScript 5.7, Vite 7.2
- **Backend**: Python 3.10, FastAPI, PyTorch
- **Testing**: Vitest 4.0 (frontend), pytest 7.4 (backend), fast-check 3.15 (PBT)
- **Linting**: ESLint 9.39, TypeScript compiler
- **Build**: Electron Builder 25.1, Vite bundler
- **CI**: GitHub Actions with Ubuntu, Windows, macOS runners

## Components and Interfaces

### 1. Diagnostic System

**CI Log Analyzer**
```typescript
interface CILogAnalyzer {
  fetchWorkflowRuns(): Promise<WorkflowRun[]>;
  extractFailures(run: WorkflowRun): Failure[];
  categorizeFailures(failures: Failure[]): FailureCategory[];
  generateReport(): DiagnosticReport;
}

interface Failure {
  job: string;
  step: string;
  errorMessage: string;
  stackTrace?: string;
  exitCode: number;
}

interface FailureCategory {
  type: 'lint' | 'test' | 'build' | 'dependency' | 'environment';
  failures: Failure[];
  rootCause: string;
  suggestedFix: string;
}
```

**Environment Comparator**
```typescript
interface EnvironmentComparator {
  compareNodeVersions(): VersionDiff;
  comparePythonVersions(): VersionDiff;
  compareDependencies(): DependencyDiff[];
  compareScripts(): ScriptDiff[];
}

interface VersionDiff {
  local: string;
  ci: string;
  compatible: boolean;
}

interface DependencyDiff {
  package: string;
  localVersion: string;
  ciVersion: string;
  mismatch: boolean;
}
```

### 2. Linting Fix System

**ESLint Auto-Fixer**
```typescript
interface ESLintFixer {
  runAutoFix(): Promise<FixResult>;
  identifyManualFixes(): ManualFix[];
  validateFixes(): ValidationResult;
}

interface FixResult {
  filesFixed: string[];
  errorsFixed: number;
  warningsFixed: number;
  remainingIssues: LintIssue[];
}

interface ManualFix {
  file: string;
  line: number;
  rule: string;
  message: string;
  suggestedFix: string;
}
```

**TypeScript Type Checker**
```typescript
interface TypeChecker {
  runTypeCheck(): Promise<TypeCheckResult>;
  identifyTypeErrors(): TypeError[];
  suggestTypeFixes(): TypeFix[];
}

interface TypeError {
  file: string;
  line: number;
  column: number;
  message: string;
  code: number;
}
```

### 3. Build System

**Frontend Builder**
```typescript
interface FrontendBuilder {
  cleanBuildArtifacts(): Promise<void>;
  installDependencies(): Promise<void>;
  runTypeScriptCompiler(): Promise<CompileResult>;
  runViteBuild(): Promise<BuildResult>;
  verifyBuildOutput(): Promise<VerificationResult>;
}

interface BuildResult {
  success: boolean;
  outputDir: string;
  assets: Asset[];
  errors: BuildError[];
  warnings: BuildWarning[];
}
```

**Backend Validator**
```typescript
interface BackendValidator {
  installPythonDependencies(): Promise<void>;
  validateImports(): Promise<ImportValidation>;
  runPytestDryRun(): Promise<TestDiscovery>;
}

interface ImportValidation {
  success: boolean;
  missingModules: string[];
  importErrors: ImportError[];
}
```

### 4. Test Execution System

**Frontend Test Runner**
```typescript
interface FrontendTestRunner {
  runUnitTests(): Promise<TestResult>;
  runIntegrationTests(): Promise<TestResult>;
  runPropertyBasedTests(): Promise<TestResult>;
  generateCoverage(): Promise<CoverageReport>;
}

interface TestResult {
  passed: number;
  failed: number;
  skipped: number;
  duration: number;
  failures: TestFailure[];
}
```

**Backend Test Runner**
```typescript
interface BackendTestRunner {
  runPytestTests(): Promise<PytestResult>;
  filterTestMarkers(): string[];
  generateCoverage(): Promise<CoverageReport>;
}

interface PytestResult {
  passed: number;
  failed: number;
  errors: number;
  duration: number;
  failures: PytestFailure[];
}
```

### 5. Multi-Platform Build Validator

**Platform Build Checker**
```typescript
interface PlatformBuildChecker {
  buildForPlatform(platform: 'ubuntu' | 'windows' | 'macos'): Promise<BuildResult>;
  verifyDistDirectory(): Promise<boolean>;
  checkBundleSize(): Promise<BundleSizeResult>;
}

interface BundleSizeResult {
  totalSize: number;
  withinLimit: boolean;
  largestChunks: Chunk[];
}
```

## Data Models

### Diagnostic Report Model
```typescript
interface DiagnosticReport {
  timestamp: Date;
  workflowRun: string;
  failedJobs: JobFailure[];
  rootCauses: RootCause[];
  recommendedActions: Action[];
  environmentDifferences: EnvironmentDiff[];
}

interface JobFailure {
  jobName: string;
  status: 'failed' | 'cancelled' | 'timed_out';
  duration: number;
  steps: StepResult[];
  logs: string;
}

interface RootCause {
  category: FailureCategory['type'];
  description: string;
  affectedJobs: string[];
  priority: 'critical' | 'high' | 'medium' | 'low';
}
```

### Fix Action Model
```typescript
interface FixAction {
  id: string;
  type: 'lint' | 'dependency' | 'config' | 'code';
  description: string;
  commands: string[];
  filesAffected: string[];
  automated: boolean;
  verificationSteps: string[];
}
```

### CI Configuration Model
```typescript
interface CIConfiguration {
  workflows: WorkflowConfig[];
  jobs: JobConfig[];
  runners: RunnerConfig[];
  secrets: SecretConfig[];
}

interface JobConfig {
  name: string;
  runsOn: string;
  timeout: number;
  steps: StepConfig[];
  dependencies: string[];
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: CI Log Failure Extraction Completeness
*For any* CI workflow run with failures, the diagnostic system should identify all failing jobs and extract their specific error messages without missing any failures.
**Validates: Requirements 1.1**

### Property 2: Failure Categorization Consistency
*For any* set of failure messages, the categorization system should consistently group them by type (linting, test, build, dependency) with the same failure always receiving the same category.
**Validates: Requirements 1.2**

### Property 3: Environment Comparison Completeness
*For any* two environment configurations (local and CI), the comparison should identify all differences in Node.js version, Python version, and dependency versions.
**Validates: Requirements 1.3**

### Property 4: Dependency Mismatch Detection
*For any* set of dependency files (package.json, requirements.txt, workflow YAML), all version conflicts should be identified and reported.
**Validates: Requirements 1.4**

### Property 5: Build Script Consistency Verification
*For any* package.json and GitHub Actions workflow file, all mismatches between defined scripts and called commands should be detected.
**Validates: Requirements 1.5**

### Property 6: ESLint Auto-Fix Idempotence
*For any* source file, running ESLint auto-fix multiple times should produce the same result after the first application, with no additional changes on subsequent runs.
**Validates: Requirements 2.3**

### Property 7: Python Import Resolution
*For any* Python module in the backend directory, if imports resolve successfully locally with Python 3.10, they should resolve in CI with the same Python version and requirements.txt.
**Validates: Requirements 3.2**

### Property 8: npm ci Determinism
*For any* package-lock.json file, running npm ci should install the exact same dependency versions in both local and CI environments, producing identical node_modules.
**Validates: Requirements 4.1**

### Property 9: TypeScript Type Check Consistency
*For any* TypeScript codebase, if type checking passes locally with TypeScript 5.7, it should pass in CI with the same TypeScript version and tsconfig.json.
**Validates: Requirements 4.3**

### Property 10: Build Output Completeness
*For any* successful Vite build, the dist directory should contain all required assets including index.html, JavaScript bundles, CSS files, and asset manifests.
**Validates: Requirements 4.4**

### Property 11: Multi-Platform Build Consistency
*For any* Electron Builder configuration, if the build succeeds on one platform (Ubuntu, Windows, or macOS), the build process should succeed on all configured platforms with the same source code.
**Validates: Requirements 4.5, 7.2**

### Property 12: CI Job Dependency Correctness
*For any* set of CI job results, the all-checks-passed job should correctly aggregate the results, passing only when all required jobs (lint, test-frontend, test-backend, build-check) pass.
**Validates: Requirements 9.1**

### Property 13: Local-CI Parity
*For any* fix applied locally, if the fix makes lint/test/build commands pass locally, the same fix should make them pass in CI when the environment versions match.
**Validates: Requirements 10.4**

## Error Handling

### Diagnostic Phase Errors
- **API Rate Limiting**: Implement exponential backoff when fetching GitHub Actions logs
- **Log Parsing Failures**: Provide raw logs if structured parsing fails
- **Missing Workflow Runs**: Handle cases where no recent runs exist

### Linting Errors
- **Unfixable Syntax Errors**: Report with file location and suggested manual fix
- **Configuration Conflicts**: Detect conflicts between .eslintrc.json and eslint.config.js
- **Parser Errors**: Validate TypeScript syntax before running ESLint

### Build Errors
- **Missing Dependencies**: Check package.json and requirements.txt before building
- **TypeScript Compilation Failures**: Report type errors with file and line numbers
- **Vite Build Failures**: Capture and display Rollup errors
- **Disk Space Issues**: Check available disk space before building

### Test Errors
- **Test Timeouts**: Increase timeout or identify slow tests
- **Environment Setup Failures**: Validate test setup files exist and are correct
- **Coverage Generation Failures**: Continue even if coverage upload fails

### CI-Specific Errors
- **Runner Unavailability**: Retry job or use different runner
- **Secret Access Errors**: Validate required secrets exist
- **Artifact Upload Failures**: Retry with exponential backoff

## Testing Strategy

### Unit Testing

Unit tests will cover:
- CI log parsing and failure categorization
- ESLint auto-fix application
- TypeScript type error extraction
- Dependency version comparison
- Build output verification
- Test result parsing

### Property-Based Testing

Property-based tests will use `fast-check` library to verify:
- Property 1: Diagnostic completeness across random workflow runs
- Property 2: Lint fix idempotence with random source files
- Property 3: Type check consistency with random TypeScript code
- Property 6: Test execution reproducibility with random test suites
- Property 10: Local-CI parity with random fix scenarios

### Integration Testing

Integration tests will verify:
- End-to-end diagnostic workflow (fetch logs → analyze → report)
- End-to-end lint fix workflow (run ESLint → apply fixes → verify)
- End-to-end build workflow (clean → install → build → verify)
- End-to-end test workflow (setup → run tests → generate coverage)

### Manual Testing

Manual verification required for:
- Reviewing actual CI workflow run logs on GitHub
- Verifying fixes work in CI after pushing
- Confirming all 8 checks turn green
- Testing on different platforms (Windows, macOS, Linux)

### Test Configuration

- **Framework**: Vitest 4.x for frontend, pytest 7.x for backend
- **Property Testing Library**: fast-check 3.x
- **Minimum Iterations**: 100 per property test
- **Timeout**: 10 seconds per unit test, 30 seconds for integration tests
- **Coverage Target**: 80% for diagnostic and fix utilities

### Test Organization

```
src/test/ci-fix/
  ├── diagnostic/
  │   ├── log-analyzer.test.ts
  │   └── log-analyzer.pbt.test.ts
  ├── linting/
  │   ├── eslint-fixer.test.ts
  │   └── eslint-fixer.pbt.test.ts
  ├── build/
  │   ├── frontend-builder.test.ts
  │   └── build-verification.pbt.test.ts
  └── integration/
      ├── end-to-end-fix.test.ts
      └── local-ci-parity.pbt.test.ts
```

## Implementation Notes

### Phase 1: Diagnosis (Requirements 1.1-1.5)

**Step 1: Fetch CI Logs**
- Use GitHub CLI or API to fetch recent workflow runs
- Filter for failed runs on main/develop branches
- Download logs for all failed jobs

**Step 2: Analyze Failures**
```bash
# Fetch recent workflow runs
gh run list --workflow=ci.yml --limit=5

# Download logs for failed run
gh run view <run-id> --log-failed
```

**Step 3: Categorize Failures**
- Parse logs to extract error messages
- Group by job name (lint, test-frontend, test-backend, build-check)
- Identify patterns (syntax errors, missing imports, type errors, timeouts)

**Step 4: Compare Environments**
```bash
# Check local versions
node --version
npm --version
python --version

# Compare with CI workflow
cat .github/workflows/ci.yml | grep "node-version"
cat .github/workflows/ci.yml | grep "python-version"
```

### Phase 2: Fix Linting (Requirements 2.1-2.5)

**Priority**: Fix linting first as it often blocks builds

**Step 1: Run ESLint Locally**
```bash
npm run lint
```

**Step 2: Apply Auto-Fixes**
```bash
npm run lint:fix
```

**Step 3: Fix Remaining Issues**
- Review ESLint output for unfixable errors
- Common issues:
  - Missing React component display names
  - Unescaped JSX entities
  - React hooks dependency arrays
  - TypeScript `any` types

**Step 4: Run Type Check**
```bash
npm run type-check
```

**Step 5: Fix Type Errors**
- Add missing type definitions
- Fix incorrect type annotations
- Resolve import path issues

### Phase 3: Fix Backend Build (Requirements 3.1-3.5)

**Step 1: Verify Python Environment**
```bash
cd backend
python --version  # Should be 3.10
```

**Step 2: Install Dependencies**
```bash
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio hypothesis
```

**Step 3: Validate Imports**
```bash
python -c "import fastapi; import torch; import transformers; import peft"
```

**Step 4: Run Tests Locally**
```bash
pytest -v -m "not integration and not e2e and not pbt"
```

### Phase 4: Fix Frontend Build (Requirements 4.1-4.5)

**Step 1: Clean and Reinstall**
```bash
rm -rf node_modules package-lock.json dist
npm install
```

**Step 2: Run TypeScript Compiler**
```bash
npm run type-check
```

**Step 3: Run Vite Build**
```bash
npm run build
```

**Step 4: Verify Build Output**
```bash
ls -lah dist/
# Should contain: index.html, assets/, favicon, etc.
```

### Phase 5: Fix Frontend Tests (Requirements 5.1-5.5)

**Step 1: Run Tests Locally**
```bash
npm run test:run
```

**Step 2: Fix Failing Tests**
- Review test output for failures
- Common issues:
  - Missing mocks
  - Incorrect assertions
  - Timeout issues
  - Environment setup problems

**Step 3: Run with Coverage**
```bash
npm run test:coverage
```

### Phase 6: Fix Backend Tests (Requirements 6.1-6.5)

**Step 1: Run pytest Locally**
```bash
cd backend
pytest -v --cov=. --cov-report=term -m "not integration and not e2e and not pbt"
```

**Step 2: Fix Import Errors**
- Ensure all modules are importable
- Fix circular dependencies
- Add missing __init__.py files

**Step 3: Fix Test Failures**
- Review pytest output
- Fix assertion errors
- Update test fixtures

### Phase 7: Verify Multi-Platform Builds (Requirements 7.1-7.5)

**Step 1: Verify Build Configuration**
```bash
npm run verify:build
```

**Step 2: Test Local Build**
```bash
npm run build
npm run electron:build -- --dir
```

**Step 3: Verify CI Matrix**
- Check .github/workflows/ci.yml for platform matrix
- Ensure all platforms (ubuntu-latest, windows-latest, macos-latest) are included

### Phase 8: Address Security Scans (Requirements 8.1-8.5)

**Step 1: Run npm audit**
```bash
npm audit --audit-level=moderate
```

**Step 2: Fix Critical Vulnerabilities**
```bash
npm audit fix
```

**Step 3: Run pip-audit**
```bash
cd backend
pip install pip-audit
pip-audit
```

### Phase 9: Verify All Checks (Requirements 9.1-9.5)

**Step 1: Run Complete CI Locally**
```bash
npm run ci
```

**Step 2: Push and Monitor**
```bash
git add .
git commit -m "fix: resolve CI pipeline failures"
git push
```

**Step 3: Monitor GitHub Actions**
- Watch workflow run in real-time
- Verify all jobs pass
- Check "All Checks Passed" job succeeds

### Phase 10: Ensure Local-CI Parity (Requirements 10.1-10.5)

**Document Environment Differences**
- Create `.github/docs/ci-environment.md`
- List Node.js, Python, and OS versions
- Document any CI-specific configurations

**Create Local CI Script**
```bash
# scripts/run-ci-locally.sh
#!/bin/bash
set -e

echo "Running CI checks locally..."
npm run lint
npm run type-check
npm run test:run
npm run build
cd backend && pytest -v -m "not integration and not e2e and not pbt"
echo "All CI checks passed locally!"
```

## Performance Considerations

- **Parallel Test Execution**: Configure Vitest to run tests in parallel (already configured with `pool: 'threads'`)
- **Dependency Caching**: Use GitHub Actions cache for node_modules and pip packages
- **Incremental Builds**: Leverage Vite's incremental build capabilities
- **Test Sharding**: Consider sharding tests across multiple CI runners for large test suites

## Security Considerations

- **Dependency Audits**: Run npm audit and pip-audit regularly
- **Secret Management**: Ensure CODECOV_TOKEN and other secrets are properly configured
- **Code Signing**: Note that code signing is optional and may cause warnings if not configured
- **Vulnerability Thresholds**: Set appropriate audit levels (moderate for CI)

## Deployment Strategy

1. **Local Verification**: Test all fixes locally before pushing
2. **Branch Protection**: Ensure CI checks are required before merging
3. **Incremental Fixes**: Fix one category at a time (lint → build → test)
4. **Monitoring**: Watch CI runs closely after each push
5. **Rollback Plan**: Keep previous working commit available for quick rollback

## Monitoring and Observability

- **CI Dashboard**: Monitor GitHub Actions workflow runs
- **Test Reports**: Review test output and coverage reports
- **Build Logs**: Analyze build logs for warnings and errors
- **Performance Metrics**: Track CI job duration over time

## CI-Specific Considerations

### Node.js Version Consistency
- CI uses Node.js 18
- Local development may use different version
- Solution: Use nvm or volta to match versions

### Python Version Consistency
- CI uses Python 3.10
- Ensure local environment matches
- Solution: Use pyenv or conda

### Platform-Specific Issues
- Windows: Path separators, line endings (CRLF vs LF)
- macOS: Case-sensitive filesystem differences
- Linux: Different shell behavior

### Timeout Configuration
- Lint job: 15 minutes
- Test jobs: 20 minutes
- Build check: 20 minutes
- Adjust if jobs consistently timeout

## Future Enhancements

- Automated CI failure notifications via Slack/Discord
- CI performance optimization (faster builds, parallel tests)
- Pre-commit hooks to catch issues before pushing
- Local CI simulation using Docker containers
- Automated dependency updates with Dependabot
- CI cost optimization (reduce runner time)
