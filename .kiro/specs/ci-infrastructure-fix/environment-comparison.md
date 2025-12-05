# Environment Comparison Report

**Generated:** December 5, 2025  
**Purpose:** Compare local development environment with CI environment

## Version Comparison

### Node.js

| Environment | Version | Compatible | Notes |
|-------------|---------|------------|-------|
| **Local** | v25.1.0 | ⚠️ Warning | Significantly newer than CI |
| **CI** | v18.x | ✅ Standard | Specified in workflow |
| **Recommendation** | Use v18.x locally | | Use nvm or volta to match CI |

**Impact:** 
- Local environment uses Node.js 25.1.0 while CI uses 18.x
- This could cause compatibility issues with ESM/CommonJS handling
- Node 25 has different module resolution behavior than Node 18

**Action Required:**
- Install Node.js 18.x locally for testing: `nvm install 18` or `nvm use 18`
- Verify fixes work with Node 18 before pushing to CI

---

### Python

| Environment | Version | Compatible | Notes |
|-------------|---------|------------|-------|
| **Local** | 3.14.0 | ⚠️ Warning | Significantly newer than CI |
| **CI** | 3.10.19 | ✅ Standard | Specified in workflow |
| **Recommendation** | Use 3.10.x locally | | Use pyenv or conda |

**Impact:**
- Local environment uses Python 3.14.0 while CI uses 3.10.19
- Python 3.14 is very new and may have different behavior
- Dependency resolution may differ between versions

**Action Required:**
- Install Python 3.10.x locally: `pyenv install 3.10` or use conda
- Test backend fixes with Python 3.10 before pushing

---

### npm

| Environment | Version | Compatible | Notes |
|-------------|---------|------------|-------|
| **Local** | 11.6.2 | ✅ Compatible | Bundled with Node 25 |
| **CI** | ~10.x | ✅ Compatible | Bundled with Node 18 |
| **Recommendation** | Match Node version | | npm version follows Node |

**Impact:**
- Minor differences in npm behavior between versions
- Both versions support `npm ci` and modern features
- No significant compatibility issues expected

---

## Package.json Configuration

### Module Type

| Setting | Current Value | CI Expectation | Issue |
|---------|---------------|----------------|-------|
| `"type"` | **Missing** | `"module"` or `.mjs` files | ❌ **CRITICAL** |

**Problem:**
- `package.json` does not specify `"type": "module"`
- ESLint config (`eslint.config.js`) uses ES module syntax (`import`)
- Node.js treats `.js` files as CommonJS by default without `"type": "module"`
- This causes the ESLint and Vitest failures in CI

**Solution:**
```json
{
  "type": "module",
  ...
}
```

---

### Scripts Comparison

Comparing `package.json` scripts with CI workflow commands:

| CI Job | CI Command | package.json Script | Match | Notes |
|--------|------------|---------------------|-------|-------|
| Lint | `npm run lint` | ✅ `eslint src --ext .ts,.tsx --report-unused-disable-directives` | ✅ | Exact match |
| Lint | `npm run type-check` | ✅ `tsc --noEmit` | ✅ | Exact match |
| Test Frontend | `npm run test:coverage` | ✅ `vitest --run --coverage` | ✅ | Exact match |
| Build Check | `npm run build` | ✅ `tsc && vite build` | ✅ | Exact match |

**Result:** All CI commands match package.json scripts exactly. No script mismatches detected.

---

## Dependency Version Analysis

### Frontend Dependencies

#### Critical Dependencies:

| Package | Version | CI Behavior | Notes |
|---------|---------|-------------|-------|
| `vite` | 7.2.6 | ✅ Installs | ES module only |
| `vitest` | 4.0.14 | ✅ Installs | Requires Vite as ES module |
| `eslint` | 9.39.1 | ✅ Installs | Requires ES module config |
| `typescript` | 5.7.2 | ✅ Installs | Latest stable |
| `react` | 18.3.1 | ✅ Installs | Stable |

**Issue:**
- Vite 7.x is ES module only
- Vitest 4.x requires Vite as ES module
- ESLint 9.x prefers ES module config
- Without `"type": "module"`, these tools fail to load properly

---

### Backend Dependencies

#### Conflicting Dependencies:

| Package | Required Version | Constraint | Conflict |
|---------|------------------|------------|----------|
| `huggingface-hub` | 0.19.4 (pinned) | - | ❌ |
| `transformers` | 4.35.0 | requires `huggingface-hub<1.0 and >=0.16.4` | ✅ |
| `tokenizers` | 0.14.1 | requires `huggingface_hub<0.18 and >=0.16.4` | ❌ **CONFLICT** |
| `tokenizers` | 0.14.0 | requires `huggingface_hub<0.17 and >=0.16.4` | ❌ **CONFLICT** |
| `datasets` | 2.14.6 | requires `huggingface-hub<1.0.0 and >=0.14.0` | ✅ |
| `evaluate` | 0.4.1 | requires `huggingface-hub>=0.7.0` | ✅ |
| `accelerate` | 0.24.0 | requires `huggingface-hub` | ✅ |

**Root Cause:**
- `huggingface-hub==0.19.4` is pinned in requirements.txt
- `tokenizers 0.14.x` requires `huggingface-hub<0.18` (max 0.17.x)
- Version 0.19.4 > 0.18, causing pip to fail dependency resolution

**Solution:**
```diff
- huggingface-hub==0.19.4
+ huggingface-hub>=0.16.4,<0.18
```

This satisfies all constraints:
- ✅ transformers: `>=0.16.4` and `<1.0`
- ✅ tokenizers: `>=0.16.4` and `<0.18`
- ✅ datasets: `>=0.14.0` and `<1.0.0`
- ✅ evaluate: `>=0.7.0`

---

## CI Workflow Configuration

### Workflow File: `.github/workflows/ci.yml`

#### Job Configuration:

| Job | Runner | Timeout | Node | Python | Cache |
|-----|--------|---------|------|--------|-------|
| lint | ubuntu-latest | 15 min | 18 | - | npm |
| test-frontend | ubuntu-latest | 20 min | 18 | - | npm |
| test-backend | ubuntu-latest | 20 min | - | 3.10 | pip |
| build-check | matrix (ubuntu/windows/macos) | 20 min | 18 | - | npm |
| security-scan | ubuntu-latest | 15 min | 18 | 3.10 | npm, pip |

#### Matrix Strategy:

```yaml
strategy:
  fail-fast: false
  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]
```

**Analysis:**
- ✅ Fail-fast disabled - all platforms tested even if one fails
- ✅ Caching enabled for npm and pip
- ✅ Appropriate timeouts set
- ✅ Correct Node and Python versions specified

---

## Environment Differences Summary

### Critical Differences:

1. **Node.js Version Mismatch**
   - Local: 25.1.0
   - CI: 18.x
   - Impact: HIGH - Different ESM/CommonJS behavior
   - Action: Use Node 18 locally for testing

2. **Python Version Mismatch**
   - Local: 3.14.0
   - CI: 3.10.19
   - Impact: MEDIUM - Different dependency resolution
   - Action: Use Python 3.10 locally for testing

3. **Missing Module Type**
   - package.json: No `"type"` field
   - CI: Expects ES modules
   - Impact: CRITICAL - Causes lint and test failures
   - Action: Add `"type": "module"` to package.json

4. **Python Dependency Conflict**
   - requirements.txt: `huggingface-hub==0.19.4`
   - CI: Cannot resolve dependencies
   - Impact: CRITICAL - Blocks backend tests
   - Action: Change to `huggingface-hub>=0.16.4,<0.18`

### No Issues Found:

- ✅ package.json scripts match CI commands exactly
- ✅ CI workflow configuration is correct
- ✅ Caching is properly configured
- ✅ Timeouts are appropriate
- ✅ No missing environment variables (except optional CODECOV_TOKEN)

---

## Recommendations

### Immediate Actions:

1. **Add `"type": "module"` to package.json**
   ```json
   {
     "name": "peft-studio",
     "version": "1.0.1",
     "type": "module",
     ...
   }
   ```

2. **Fix huggingface-hub version in requirements.txt**
   ```diff
   - huggingface-hub==0.19.4
   + huggingface-hub>=0.16.4,<0.18
   ```

3. **Install matching versions locally**
   ```bash
   # Node.js
   nvm install 18
   nvm use 18
   
   # Python
   pyenv install 3.10.19
   pyenv local 3.10.19
   ```

### Testing Locally:

```bash
# Frontend
npm ci
npm run lint
npm run type-check
npm run test:run
npm run build

# Backend
cd backend
pip install -r requirements.txt
pytest -v -m "not integration and not e2e and not pbt"
```

### Verification:

After making fixes:
1. Test all commands locally with Node 18 and Python 3.10
2. Ensure all commands pass without errors
3. Push to GitHub and monitor CI workflow
4. Verify all 8 checks turn green

---

## Environment Setup Guide

### For Windows (Current Platform):

#### Node.js 18:
```powershell
# Using nvm-windows
nvm install 18
nvm use 18
node --version  # Should show v18.x.x
```

#### Python 3.10:
```powershell
# Using pyenv-win or conda
pyenv install 3.10.19
pyenv local 3.10.19
python --version  # Should show Python 3.10.19
```

### Verify Environment:

```powershell
# Check versions
node --version    # Should be v18.x.x
python --version  # Should be 3.10.x
npm --version     # Should be ~10.x

# Test frontend
npm ci
npm run lint
npm run type-check
npm run test:run
npm run build

# Test backend
cd backend
pip install -r requirements.txt
pytest -v -m "not integration and not e2e and not pbt"
```

---

## Conclusion

The environment comparison reveals:
- **2 Critical Configuration Issues** (module type, dependency conflict)
- **2 Version Mismatches** (Node.js, Python) - not blocking but should be matched
- **0 Script Mismatches** - all CI commands are correct
- **0 Workflow Issues** - CI configuration is properly set up

All issues are fixable with simple configuration changes. No infrastructure or tooling changes required.
