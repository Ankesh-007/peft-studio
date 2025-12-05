# CI Failure Diagnostic Report

**Generated:** December 5, 2025  
**Workflow Run:** 19959050260  
**Branch:** main  
**Commit:** docs: add repository cleanup summary

## Executive Summary

The CI pipeline has **8 failing checks** across multiple jobs. All failures stem from **3 root causes**:
1. **ESLint Configuration Issue** - ESM/CommonJS module conflict
2. **Python Dependency Conflict** - huggingface-hub version incompatibility
3. **TypeScript Type Errors** - Type mismatches in error handling code

## Failed Jobs Overview

| Job | Status | Root Cause | Priority |
|-----|--------|------------|----------|
| Lint | ❌ Failed | ESLint config ESM issue | **Critical** |
| Test Frontend | ❌ Failed | Vitest config ESM issue | **Critical** |
| Test Backend | ❌ Failed | Python dependency conflict | **Critical** |
| Build Check (Ubuntu) | ❌ Failed | TypeScript type errors | **High** |
| Build Check (Windows) | ❌ Failed | TypeScript type errors | **High** |
| Build Check (macOS) | ❌ Failed | TypeScript type errors | **High** |
| Security Scan | ❌ Failed | Python dependency conflict | **High** |
| All Checks Passed | ❌ Failed | Dependent on above | **N/A** |

## Detailed Failure Analysis

### 1. Lint Job Failure

**Category:** Configuration / Environment Issue  
**Step Failed:** Run ESLint  
**Exit Code:** 2

**Error Message:**
```
SyntaxError: Cannot use import statement outside a module
at /home/runner/work/peft-studio/peft-studio/eslint.config.js:1
import js from '@eslint/js';
^^^^^^
```

**Root Cause:**
- ESLint 9.39 is trying to load `eslint.config.js` which uses ES module syntax (`import`)
- Node.js is treating the file as CommonJS because `package.json` doesn't have `"type": "module"`
- The warning message indicates: "To load an ES module, set 'type': 'module' in the package.json or use the .mjs extension"

**Impact:**
- Blocks all linting checks
- Prevents TypeScript type checking (skipped due to lint failure)
- Cascades to prevent merge

**Recommended Fix:**
1. Add `"type": "module"` to `package.json`, OR
2. Rename `eslint.config.js` to `eslint.config.mjs`, OR
3. Convert `eslint.config.js` to use CommonJS syntax (`require()` instead of `import`)

---

### 2. Test Frontend Job Failure

**Category:** Configuration / Environment Issue  
**Step Failed:** Run frontend tests  
**Exit Code:** 1

**Error Message:**
```
Error [ERR_REQUIRE_ESM]: require() of ES Module /home/runner/work/peft-studio/peft-studio/node_modules/vite/dist/node/index.js from /home/runner/work/peft-studio/peft-studio/node_modules/vitest/dist/config.cjs not supported.
```

**Root Cause:**
- Same ESM/CommonJS conflict as lint job
- Vitest is trying to load Vite as a CommonJS module but Vite 7.2 is an ES module
- This is likely caused by the same missing `"type": "module"` in `package.json`

**Impact:**
- No frontend tests are executed
- No coverage reports generated
- Codecov upload skipped

**Recommended Fix:**
- Same as Lint job - add `"type": "module"` to `package.json`

---

### 3. Test Backend Job Failure

**Category:** Dependency Conflict  
**Step Failed:** Install dependencies  
**Exit Code:** 1

**Error Message:**
```
ERROR: Cannot install -r requirements.txt (line 10), -r requirements.txt (line 11), -r requirements.txt (line 6), -r requirements.txt (line 8), huggingface-hub==0.19.4 and transformers because these package versions have conflicting dependencies.

The conflict is caused by:
    The user requested huggingface-hub==0.19.4
    transformers 4.35.0 depends on huggingface-hub<1.0 and >=0.16.4
    accelerate 0.24.0 depends on huggingface-hub
    datasets 2.14.6 depends on huggingface-hub<1.0.0 and >=0.14.0
    evaluate 0.4.1 depends on huggingface-hub>=0.7.0
    tokenizers 0.14.1 depends on huggingface_hub<0.18 and >=0.16.4
    tokenizers 0.14.0 depends on huggingface_hub<0.17 and >=0.16.4
```

**Root Cause:**
- `huggingface-hub==0.19.4` is pinned in requirements.txt (line 19)
- `tokenizers 0.14.1` requires `huggingface_hub<0.18` (incompatible with 0.19.4)
- `tokenizers 0.14.0` requires `huggingface_hub<0.17` (incompatible with 0.19.4)
- Pip cannot resolve this dependency conflict

**Impact:**
- Backend dependencies cannot be installed
- No backend tests run
- Security scan also fails (same dependency issue)

**Recommended Fix:**
1. Downgrade `huggingface-hub` to 0.17.x (compatible with tokenizers 0.14.x), OR
2. Upgrade `transformers` to a version that supports newer huggingface-hub, OR
3. Remove the version pin and let pip resolve automatically

**Suggested Change:**
```diff
- huggingface-hub==0.19.4
+ huggingface-hub>=0.16.4,<0.18
```

---

### 4. Build Check Failures (All Platforms)

**Category:** TypeScript Type Errors  
**Step Failed:** Build frontend  
**Exit Code:** 1 (all platforms)

**Error Messages:**
```
error TS2322: Type '"system"' is not assignable to type 'ErrorCategory'.
  at src/api/errors.ts(45,7)

error TS2322: Type '"medium"' is not assignable to type 'ErrorSeverity'.
  at src/api/errors.ts(46,7)

error TS2322: Type 'SavedConfiguration' is not assignable to type 'Record<string, unknown>'.
  at src/components/ConfigurationManagement.tsx(245,17)

error TS2322: Type '(config: SavedConfiguration) => void' is not assignable to type '(config: Record<string, unknown>) => void'.
  at src/components/ConfigurationManagement.tsx(291,11)

error TS2322: Type '"system"' is not assignable to type 'ErrorCategory'.
  at src/components/ErrorBoundary.tsx(71,11)

error TS2322: Type '"high"' is not assignable to type 'ErrorSeverity'.
  at src/components/ErrorBoundary.tsx(72,11)
```

**Root Cause:**
- Type definitions for `ErrorCategory` and `ErrorSeverity` don't include values being used
- `SavedConfiguration` type is incompatible with `Record<string, unknown>`
- These are code-level type errors, not configuration issues

**Impact:**
- Build fails on all platforms (Ubuntu, Windows, macOS)
- No dist directory created
- Electron packaging cannot proceed

**Recommended Fix:**
1. Update type definitions to include missing values:
   - Add `"system"` to `ErrorCategory` type
   - Add `"medium"` and `"high"` to `ErrorSeverity` type
2. Fix `SavedConfiguration` type compatibility in ConfigurationManagement.tsx

---

### 5. Security Scan Job Failure

**Category:** Dependency Conflict (same as Test Backend)  
**Step Failed:** Install backend dependencies  
**Exit Code:** 1

**Error Message:**
Same as Test Backend job - huggingface-hub dependency conflict

**Root Cause:**
Same as Test Backend - Python dependency version conflict

**Impact:**
- pip-audit cannot run
- No security vulnerability scanning for Python dependencies

**Recommended Fix:**
Same as Test Backend - fix huggingface-hub version constraint

---

### 6. All Checks Passed Job Failure

**Category:** Aggregation Failure  
**Step Failed:** Check if all jobs passed  
**Exit Code:** 1

**Root Cause:**
- This job depends on all other jobs passing
- Since lint, test-frontend, test-backend, and build-check all failed, this job correctly fails

**Impact:**
- Pull requests cannot be merged
- CI status shows as failed

**Recommended Fix:**
- Fix all upstream job failures
- This job will automatically pass once dependencies pass

## Failure Categories Summary

### By Type:
- **Configuration Issues:** 2 (Lint, Test Frontend)
- **Dependency Conflicts:** 2 (Test Backend, Security Scan)
- **Type Errors:** 3 (Build Check on all platforms)
- **Aggregation:** 1 (All Checks Passed)

### By Priority:
- **Critical:** 3 (Lint, Test Frontend, Test Backend)
- **High:** 4 (Build Check x3, Security Scan)
- **N/A:** 1 (All Checks Passed)

## Root Causes Ranked by Impact

### 1. ESM/CommonJS Module Conflict (CRITICAL)
**Affects:** Lint, Test Frontend  
**Fix Complexity:** Low  
**Estimated Time:** 5 minutes

**Solution:**
Add `"type": "module"` to package.json

### 2. Python Dependency Conflict (CRITICAL)
**Affects:** Test Backend, Security Scan  
**Fix Complexity:** Low  
**Estimated Time:** 10 minutes

**Solution:**
Update huggingface-hub version constraint in requirements.txt

### 3. TypeScript Type Errors (HIGH)
**Affects:** Build Check (all platforms)  
**Fix Complexity:** Medium  
**Estimated Time:** 20-30 minutes

**Solution:**
Update type definitions and fix type mismatches in error handling code

## Recommended Fix Order

1. **Fix ESM/CommonJS issue** (Lint + Test Frontend)
   - Add `"type": "module"` to package.json
   - Verify lint and test commands work locally

2. **Fix Python dependency conflict** (Test Backend + Security Scan)
   - Update huggingface-hub version in requirements.txt
   - Test backend installation locally

3. **Fix TypeScript type errors** (Build Check)
   - Update ErrorCategory and ErrorSeverity types
   - Fix SavedConfiguration type compatibility
   - Run `npm run type-check` locally

4. **Verify all checks pass**
   - Run complete CI locally using verification script
   - Push fixes and monitor CI

## Environment Information

### CI Environment:
- **OS:** Ubuntu 22.04 (ubuntu-latest), Windows Server 2022 (windows-latest), macOS 14 (macos-latest)
- **Node.js:** 18.x
- **Python:** 3.10.19
- **npm:** Bundled with Node 18
- **pip:** Latest

### Workflow Configuration:
- **Workflow File:** `.github/workflows/ci.yml`
- **Timeout:** 15-20 minutes per job
- **Caching:** Enabled for npm and pip
- **Fail Fast:** Disabled for build matrix

## Next Steps

1. ✅ Complete environment comparison (subtask 1.3)
2. ✅ Create this diagnostic report (subtask 1.2)
3. ⏭️ Proceed to fix linting issues (task 2)
4. ⏭️ Fix backend dependencies (task 4)
5. ⏭️ Fix frontend build (task 6)
6. ⏭️ Monitor CI after fixes

## Additional Notes

- All failures are deterministic and reproducible
- No intermittent or flaky test failures observed
- No infrastructure or runner issues detected
- All failures are code/configuration related and fixable
