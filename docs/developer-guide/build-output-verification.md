# Build Output Verification

This guide explains how to verify that the build process has produced all expected outputs and that they meet quality standards.

## Overview

The build output verification process ensures that:
- All expected frontend build artifacts are present
- Bundle sizes are reasonable
- The backend can start successfully
- All assets are properly referenced

This verification is part of task 3.4 in the CI Infrastructure Fix specification and validates Requirements 2.4 and 2.5.

## Quick Start

To verify build outputs after running a build:

```bash
npm run verify:build-outputs
```

This will run all verification checks and report any issues.

## What Gets Verified

### 1. Frontend Build Outputs

The verification checks that the `dist/` directory contains:

- **index.html**: The main HTML entry point
- **assets/**: Directory containing bundled JavaScript and CSS
- **JavaScript bundles**: All compiled and bundled JS files
- **CSS bundles**: All compiled and bundled CSS files
- **Main bundle**: The primary application entry point (index-*.js)
- **Vendor bundles**: Code-split vendor libraries (if enabled)
- **samples/**: Sample data files for the application

### 2. Bundle Sizes

The verification analyzes bundle sizes to ensure they're reasonable:

- **Individual file sizes**: Checks each bundle against size thresholds
  - Warning: Files over 500 KB
  - Error: Files over 1 MB
- **Total bundle size**: Ensures the total size is reasonable (< 5 MB)
- **Code splitting**: Verifies that vendor code is split into separate bundles

### 3. index.html Validation

The verification checks that index.html:

- Contains a module script tag for the main bundle
- Includes a stylesheet link
- Has a root div element for React mounting
- References assets that actually exist in the dist/ directory

### 4. Backend Start Test

The verification tests that:

- The backend main.py can be imported without errors
- All Python dependencies are available
- No import errors or syntax errors exist

## Expected Output

When all checks pass, you'll see output like:

```
Build Output Verification
Validates: Requirements 2.4, 2.5

============================================================
Frontend Build Verification
============================================================
✓ dist directory exists: dist
✓ index.html exists: dist/index.html
✓ assets directory exists: dist/assets
✓ Found 17 JavaScript bundles
✓ Found 1 CSS bundles
✓ Main bundle found: index-D1Sfqmdy.js
✓ Found 2 vendor bundles (code splitting enabled)
✓ samples directory exists: dist/samples
✓ sample dataset exists: dist/samples/sample-dataset.jsonl

============================================================
Bundle Size Verification
============================================================
✓ Total bundle size (0.81 MB) is reasonable

============================================================
index.html Verification
============================================================
✓ index.html contains module script tag
✓ index.html contains stylesheet link
✓ index.html contains root div
✓ Referenced script exists: assets/index-D1Sfqmdy.js

============================================================
Backend Start Verification
============================================================
✓ Backend main.py imports successfully

============================================================
Verification Summary
============================================================
Passed: 16
Warnings: 0
Failed: 0
✓ All build output verifications passed!
```

## Troubleshooting

### Missing dist/ Directory

**Problem**: The dist/ directory doesn't exist.

**Solution**: Run the build first:
```bash
npm run build
```

### Missing JavaScript Bundles

**Problem**: No JavaScript files found in dist/assets/.

**Solution**: 
1. Check for build errors: `npm run build`
2. Verify Vite configuration in `vite.config.ts`
3. Check that TypeScript compilation succeeded: `npm run type-check`

### Large Bundle Sizes

**Problem**: Bundle sizes exceed thresholds.

**Solution**:
1. Review bundle analysis: `npm run build:analyze`
2. Check for accidentally imported large dependencies
3. Ensure code splitting is configured properly
4. Consider lazy loading for large components

### Backend Import Fails

**Problem**: Backend main.py cannot be imported.

**Solution**:
1. Check Python dependencies: `cd backend && pip install -r requirements.txt`
2. Look for syntax errors in backend code
3. Verify all imports are available
4. Check Python version (3.10+ required)

### Referenced Assets Missing

**Problem**: index.html references assets that don't exist.

**Solution**:
1. Clean and rebuild: `rm -rf dist && npm run build`
2. Check Vite build configuration
3. Verify asset paths in vite.config.ts

## Integration with CI

This verification is part of the CI pipeline and runs automatically after builds. To integrate it into your workflow:

```yaml
# .github/workflows/ci.yml
- name: Build
  run: npm run build

- name: Verify Build Outputs
  run: npm run verify:build-outputs
```

## Manual Verification

If you prefer to manually verify build outputs:

### Check Frontend Build

```bash
# Verify dist directory exists
ls -la dist/

# Check for JavaScript bundles
ls -la dist/assets/*.js

# Check for CSS bundles
ls -la dist/assets/*.css

# Verify index.html
cat dist/index.html
```

### Check Bundle Sizes

```bash
# On Unix/Mac
du -sh dist/assets/*

# On Windows (PowerShell)
Get-ChildItem dist/assets | Select-Object Name, @{Name="Size(KB)";Expression={[math]::Round($_.Length/1KB, 2)}}
```

### Test Backend Start

```bash
cd backend
python -c "import sys; sys.path.insert(0, '.'); import main; print('Backend imports successfully')"
```

## Requirements Validation

This verification validates the following requirements from the CI Infrastructure Fix specification:

### Requirement 2.4: Build Output Verification

> WHEN builds complete THEN the system SHALL verify that all expected output files exist

**Validated by**:
- Checking dist/ directory exists
- Verifying index.html exists
- Confirming JavaScript and CSS bundles are present
- Checking sample data files exist

### Requirement 2.5: Build Error Messages

> WHEN builds fail THEN the system SHALL provide clear error messages indicating the specific failure point

**Validated by**:
- Providing specific error messages for missing files
- Identifying which assets are missing
- Reporting exact file paths that failed verification
- Giving actionable troubleshooting steps

## Related Documentation

- [Build Configuration](./build-and-installers.md)
- [CI/CD Setup](./ci-cd-setup.md)
- [Testing Guide](./testing.md)
- [Release Process](./release-process.md)

## Script Location

The verification script is located at:
```
scripts/verify-build-outputs.js
```

It can be run directly:
```bash
node scripts/verify-build-outputs.js
```

Or via npm script:
```bash
npm run verify:build-outputs
```
