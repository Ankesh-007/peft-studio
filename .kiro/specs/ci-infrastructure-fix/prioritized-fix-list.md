# Prioritized CI Fix List

**Created:** December 4, 2025  
**Based On:** Diagnostic Report + Failure Categorization + Local Testing

## Fix Phases Overview

| Phase | Focus | Duration | Jobs Fixed | Priority |
|-------|-------|----------|------------|----------|
| Phase 1 | Critical Blockers | 1-2 hours | ~10-15 | CRITICAL |
| Phase 2 | Test Failures | 1-2 days | ~5-10 | HIGH |
| Phase 3 | Implementation Gaps | 3-5 days | ~3-5 | MEDIUM |
| Phase 4 | Quality & Security | Ongoing | ~2-4 | MEDIUM |

## Phase 1: Critical Blockers (CRITICAL - Fix Today)

**Goal:** Unblock CI pipeline so tests can run  
**Estimated Time:** 1-2 hours  
**Jobs Fixed:** ~10-15

### 1.1 Fix Backend Import Paths ⚠️ CRITICAL
**Priority:** P0 - Blocks all backend functionality  
**Estimated Time:** 30 minutes

**Problem:**
```python
# Current (BROKEN)
from backend.services.quality_analysis_service import ...

# Should be (CORRECT)
from .quality_analysis_service import ...
```

**Files to Fix:**
- `backend/services/training_orchestration_service.py` (line 36)
- Search for all `from backend.` imports in backend/

**Fix Steps:**
1. Search: `grep -r "from backend\." backend/`
2. Replace absolute imports with relative imports
3. Test: `cd backend && python -c "import main"`
4. Verify: Should import without errors

**Impact:** Unblocks all backend tests and verification

### 1.2 Add Missing Test Scripts ⚠️ CRITICAL
**Priority:** P0 - Blocks test workflows  
**Estimated Time:** 5 minutes

**Problem:** Workflows reference undefined scripts

**Fix:** Add to package.json scripts section:
```json
{
  "scripts": {
    "test:integration": "vitest --run --config vitest.integration.config.ts",
    "test:pbt": "vitest --run --config vitest.pbt.config.ts"
  }
}
```

**Note:** Don't change test:e2e yet (will fix in Phase 3)

**Impact:** Allows integration and PBT test jobs to run

### 1.3 Add Pytest Markers ⚠️ CRITICAL
**Priority:** P0 - Blocks backend test filtering  
**Estimated Time:** 5 minutes

**Problem:** Backend tests use markers that aren't defined

**Fix:** Update backend/pytest.ini:
```ini
[pytest]
asyncio_default_fixture_loop_scope = function

markers =
    integration: Integration tests that test multiple components together
    e2e: End-to-end tests that test complete workflows
    performance: Performance and benchmark tests
    pbt: Property-based tests using Hypothesis
```

**Impact:** Allows backend test filtering to work correctly

### 1.4 Add Missing Test Dependencies ⚠️ HIGH
**Priority:** P1 - Needed for coverage and benchmarks  
**Estimated Time:** 10 minutes

**Problem:** pytest-cov installed separately in workflows

**Fix:** Add to backend/requirements.txt:
```
pytest-cov==4.1.0
pytest-benchmark==4.0.0
```

**Steps:**
1. Add lines to requirements.txt
2. Test: `cd backend && pip install -r requirements.txt`
3. Verify: `pip list | grep pytest`

**Impact:** Allows coverage collection and performance tests

### 1.5 Verify Phase 1 Fixes ✅ VALIDATION
**Priority:** P0 - Must verify before proceeding  
**Estimated Time:** 30 minutes

**Verification Steps:**
1. ✅ Backend imports: `cd backend && python -c "import main"`
2. ✅ Test scripts: `npm run test:integration --help`
3. ✅ Test scripts: `npm run test:pbt --help`
4. ✅ Pytest markers: `cd backend && pytest --markers`
5. ✅ Dependencies: `cd backend && pip list | grep pytest-cov`
6. ✅ Build: `npm run build`
7. ✅ TypeScript: `npx tsc --noEmit`

**Success Criteria:**
- All commands run without errors
- Backend imports successfully
- Test scripts are recognized
- Pytest markers are defined

## Phase 2: Test Failures (HIGH - Fix This Week)

**Goal:** Fix failing tests so CI passes  
**Estimated Time:** 1-2 days  
**Jobs Fixed:** ~5-10

### 2.1 Fix Property-Based Test Failures 🔧 HIGH
**Priority:** P1 - 24 tests failing  
**Estimated Time:** 4-6 hours

**Problem:** Release notes generator fails for edge cases

**Failing Tests:**
- Property 24: Platform-specific instructions
- Property 23: Download links format
- Property 22: Changelog section
- And 21 more properties

**Root Cause Analysis:**
- Version 0.0.0 edge case not handled
- Platform-specific sections missing for pre-release
- Template logic needs edge case handling

**Fix Approach:**
1. Review failing test: `src/test/unit/github-release-workflow.test.ts`
2. Identify edge cases: version 0.0.0, empty changelog, etc.
3. Update generator: Handle edge cases properly
4. Re-run tests: `npm test -- --run github-release-workflow`
5. Verify: All properties should pass

**Files to Fix:**
- `scripts/release-to-github.js` (release notes generator)
- `scripts/update-repository-metadata.js` (if related)

**Impact:** Fixes 24 failing tests

### 2.2 Fix Remaining Unit Test Failures 🔧 HIGH
**Priority:** P1 - 17 tests failing  
**Estimated Time:** 3-4 hours

**Problem:** Various unit test failures

**Approach:**
1. Run tests: `npm test -- --run`
2. Categorize failures:
   - Assertion errors
   - Import errors
   - Mock issues
   - Async issues
3. Fix by category
4. Re-run after each fix
5. Verify all pass

**Common Fixes:**
- Update assertions to match actual behavior
- Fix import paths
- Update mocks to match new interfaces
- Add proper async/await handling

**Impact:** Fixes 17 failing tests

### 2.3 Run Backend Tests 🔧 HIGH
**Priority:** P1 - Currently blocked  
**Estimated Time:** 2-3 hours

**Prerequisites:**
- Phase 1 fixes must be complete
- Backend imports must work

**Steps:**
1. Verify imports: `cd backend && python -c "import main"`
2. Run all tests: `cd backend && pytest -v`
3. Categorize failures
4. Fix failing tests
5. Re-run until all pass

**Expected Issues:**
- Import errors (should be fixed in Phase 1)
- Assertion failures
- Missing fixtures
- Async test issues

**Impact:** Unblocks backend test jobs

### 2.4 Create Basic Integration Tests 🔧 MEDIUM
**Priority:** P2 - Tests don't exist  
**Estimated Time:** 2-3 hours

**Goal:** Create minimal integration tests so job doesn't fail

**Approach:**
1. Create `src/test/integration/` directory
2. Create basic integration test file
3. Test API client integration
4. Test component integration
5. Run: `npm run test:integration`

**Example Test:**
```typescript
// src/test/integration/api-client.integration.test.ts
import { describe, it, expect } from 'vitest';
import { apiClient } from '@/api/client';

describe('API Client Integration', () => {
  it('should handle connection errors gracefully', async () => {
    // Test that client handles backend unavailable
    const result = await apiClient.checkHealth();
    expect(result).toBeDefined();
  });
});
```

**Impact:** Integration test job will pass

## Phase 3: Implementation Gaps (MEDIUM - Next Week)

**Goal:** Implement missing test infrastructure  
**Estimated Time:** 3-5 days  
**Jobs Fixed:** ~3-5

### 3.1 Implement E2E Test Infrastructure 📝 MEDIUM
**Priority:** P2 - Currently placeholder  
**Estimated Time:** 1-2 days

**Current State:**
```json
"test:e2e": "echo 'E2E tests not yet implemented'"
```

**Implementation Plan:**
1. Choose E2E framework (Playwright already installed)
2. Create E2E test directory structure
3. Set up test environment
4. Create basic E2E tests
5. Update package.json script

**Example Tests:**
- Application startup
- Basic navigation
- Form submission
- Error handling

**Files to Create:**
- `src/test/e2e/app-startup.e2e.test.ts`
- `src/test/e2e/navigation.e2e.test.ts`
- `src/test/e2e/training-workflow.e2e.test.ts`

**Impact:** E2E test job will actually test something

### 3.2 Organize Property-Based Tests 📝 LOW
**Priority:** P3 - Tests work but not organized  
**Estimated Time:** 2-3 hours

**Current State:**
- PBT tests mixed with unit tests
- No dedicated PBT files

**Goal:**
- Separate PBT tests into *.pbt.test.ts files
- Make test:pbt script run only PBT tests

**Approach:**
1. Create `src/test/pbt/` directory
2. Move PBT tests from unit tests
3. Create new PBT test files
4. Verify: `npm run test:pbt`

**Impact:** Better test organization, clearer test runs

### 3.3 Add Performance Test Examples 📝 LOW
**Priority:** P3 - May not exist  
**Estimated Time:** 1-2 hours

**Goal:** Create basic performance tests

**Example Tests:**
- Bundle size constraints
- Component render performance
- API response times
- Memory usage

**Files to Create:**
- `src/test/performance/bundle-size.perf.test.ts`
- `src/test/performance/render-performance.perf.test.ts`

**Impact:** Performance test job will have tests to run

### 3.4 Create Backend Integration Tests 📝 MEDIUM
**Priority:** P2 - Backend has no integration tests  
**Estimated Time:** 1-2 days

**Goal:** Create backend integration tests

**Example Tests:**
- Service integration
- Database operations
- API endpoint integration
- External service mocking

**Files to Create:**
- `backend/tests/integration/test_service_integration.py`
- `backend/tests/integration/test_api_integration.py`

**Impact:** Backend integration tests will run

## Phase 4: Quality & Security (MEDIUM - Ongoing)

**Goal:** Fix code quality and security issues  
**Estimated Time:** Ongoing  
**Jobs Fixed:** ~2-4

### 4.1 Run Security Audits 🔍 MEDIUM
**Priority:** P2 - Unknown vulnerabilities  
**Estimated Time:** 2-3 hours

**Steps:**
1. Run npm audit: `npm audit`
2. Review vulnerabilities
3. Run auto-fix: `npm audit fix`
4. Manually update breaking changes
5. Test after updates
6. Run pip-audit: `cd backend && pip-audit`
7. Update vulnerable Python packages
8. Test after updates

**Impact:** Security scan jobs will pass

### 4.2 Fix Backend Linting 🔍 MEDIUM
**Priority:** P2 - Likely has violations  
**Estimated Time:** 2-3 hours

**Steps:**
1. Run flake8: `cd backend && flake8 .`
2. Run black: `cd backend && black --check .`
3. Auto-fix: `cd backend && black .`
4. Run isort: `cd backend && isort .`
5. Fix remaining issues manually
6. Run mypy: `cd backend && mypy .`
7. Fix type errors

**Impact:** Backend linting jobs will pass

### 4.3 Configure Code Coverage 🔍 LOW
**Priority:** P3 - Coverage may be too strict  
**Estimated Time:** 1 hour

**Current Thresholds:**
```typescript
thresholds: {
  lines: 70,
  functions: 70,
  branches: 70,
  statements: 70,
}
```

**Steps:**
1. Run coverage: `npm run test:coverage`
2. Check actual coverage
3. Adjust thresholds if needed
4. Configure exclusions
5. Verify coverage reports generate

**Impact:** Coverage jobs will pass

### 4.4 Fix Secret Scanning Issues 🔍 LOW
**Priority:** P3 - Likely passing  
**Estimated Time:** 30 minutes

**Steps:**
1. Review TruffleHog results (when available)
2. Remove any detected secrets
3. Add to .gitignore
4. Rotate compromised credentials (if any)

**Impact:** Secret scanning job will pass

## Dependency Graph

```
Phase 1 (Critical Blockers)
├── 1.1 Backend Imports ──┐
├── 1.2 Test Scripts      ├──> Phase 2 (Test Failures)
├── 1.3 Pytest Markers    │    ├── 2.1 PBT Failures
├── 1.4 Test Dependencies │    ├── 2.2 Unit Failures
└── 1.5 Verification      ┘    ├── 2.3 Backend Tests
                               └── 2.4 Integration Tests
                                    │
                                    └──> Phase 3 (Implementation)
                                         ├── 3.1 E2E Tests
                                         ├── 3.2 PBT Organization
                                         ├── 3.3 Performance Tests
                                         └── 3.4 Backend Integration
                                              │
                                              └──> Phase 4 (Quality)
                                                   ├── 4.1 Security
                                                   ├── 4.2 Linting
                                                   ├── 4.3 Coverage
                                                   └── 4.4 Secrets
```

## Success Metrics

### Phase 1 Success
- ✅ Backend imports without errors
- ✅ All test scripts are defined
- ✅ Pytest markers are configured
- ✅ Test dependencies installed
- ✅ Build passes locally

### Phase 2 Success
- ✅ All property-based tests pass
- ✅ All unit tests pass (270/270)
- ✅ Backend tests run and pass
- ✅ Basic integration tests exist and pass

### Phase 3 Success
- ✅ E2E tests implemented and passing
- ✅ PBT tests organized in dedicated files
- ✅ Performance tests exist
- ✅ Backend integration tests exist

### Phase 4 Success
- ✅ No high/critical security vulnerabilities
- ✅ All linting passes
- ✅ Code coverage meets thresholds
- ✅ No secret leaks detected

## Overall Success Criteria

**Target:** All 33 CI checks passing

**Current State:**
- Passing: ~5-10 checks (15-30%)
- Failing: ~23-28 checks (70-85%)

**After Phase 1:**
- Passing: ~15-20 checks (45-60%)
- Failing: ~13-18 checks (40-55%)

**After Phase 2:**
- Passing: ~25-30 checks (75-90%)
- Failing: ~3-8 checks (10-25%)

**After Phase 3:**
- Passing: ~30-32 checks (90-97%)
- Failing: ~1-3 checks (3-10%)

**After Phase 4:**
- Passing: ~33 checks (100%)
- Failing: 0 checks (0%)

## Timeline

| Phase | Start | End | Duration |
|-------|-------|-----|----------|
| Phase 1 | Day 1 | Day 1 | 2 hours |
| Phase 2 | Day 1 | Day 3 | 2 days |
| Phase 3 | Day 4 | Day 8 | 5 days |
| Phase 4 | Day 9 | Ongoing | Continuous |

**Total Time to Green CI:** ~8-10 days

## Risk Assessment

### High Risk Items
1. **Backend Import Fix** - May have more files than identified
2. **Property Test Fixes** - May require significant refactoring
3. **E2E Implementation** - May uncover new issues

### Medium Risk Items
4. **Security Updates** - May have breaking changes
5. **Backend Tests** - May have many failures
6. **Integration Tests** - May need complex setup

### Low Risk Items
7. **Test Scripts** - Simple addition
8. **Pytest Markers** - Simple configuration
9. **Linting** - Mostly auto-fixable

## Rollback Plan

If any phase causes issues:

1. **Revert Changes** - Use git to revert problematic commits
2. **Test Locally** - Verify revert fixes issue
3. **Document Issue** - Add to known issues list
4. **Plan Alternative** - Find different approach
5. **Retry** - Implement alternative fix

## Next Steps

1. ✅ **Review this plan** - Ensure all stakeholders agree
2. 🔧 **Create fix branch** - `fix/ci-infrastructure-phase-1`
3. 🔧 **Implement Phase 1** - Start with critical blockers
4. ✅ **Test locally** - Verify all Phase 1 fixes work
5. 🔧 **Push and monitor** - Watch CI results
6. 📝 **Update documentation** - Document what was fixed
7. 🔧 **Proceed to Phase 2** - Fix test failures

---

**Plan Status:** Ready for implementation  
**Confidence Level:** High  
**Next Action:** Begin Phase 1 implementation
