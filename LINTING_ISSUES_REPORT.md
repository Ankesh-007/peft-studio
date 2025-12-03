# Linting Issues Report

## Summary
- **Total Issues**: 346 (64 errors, 282 warnings)
- **Date**: December 1, 2025
- **Status**: Documented for future resolution

## Critical Errors (64)

### React Hooks Violations

#### 1. Components Created During Render
**File**: `src/components/configuration/ConfigurationPreview.tsx`
- **Issue**: `InfoRow` component defined inside render function
- **Impact**: Component state resets on every render
- **Fix**: Move `InfoRow` component outside the parent component
- **Occurrences**: 18 instances

#### 2. Refs Accessed During Render
**File**: `src/hooks/usePerformance.ts`
- **Issue**: `renderCount.current` accessed during render (line 28)
- **Impact**: Component doesn't update as expected
- **Fix**: Access refs only in effects or event handlers

#### 3. setState in Effect
**File**: `src/hooks/useMediaQuery.ts`
- **Issue**: `setMatches` called synchronously in effect (line 13)
- **Impact**: Can cause cascading renders
- **Fix**: Use proper effect pattern or move to event handler

#### 4. Variable Accessed Before Declaration
**File**: `src/lib/useTrainingMonitor.ts`
- **Issue**: `connect` function accessed before declaration (line 95)
- **Impact**: Prevents proper updates
- **Fix**: Restructure code to declare before use

#### 5. Impure Function During Render
**File**: `src/hooks/usePerformance.ts`
- **Issue**: `performance.now()` called during render (line 107)
- **Impact**: Unstable results on re-render
- **Fix**: Move to useEffect or useRef initialization

### JSX Unescaped Entities (11 errors)

**Files**:
- `src/components/onboarding/SetupWizard.tsx` (line 75)
- `src/components/wizard/DatasetUploadStep.tsx` (lines 182, 310)
- `src/components/wizard/EnhancedConfigurationStep.tsx` (lines 289, 590)
- `src/components/wizard/ModelSelectionStep.tsx` (lines 106, 308)
- `src/components/wizard/SmartConfigurationStep.tsx` (lines 129, 457)
- `src/components/wizard/UseCaseSelection.tsx` (lines 71, 72, 186)

**Fix**: Replace `'` with `&apos;` and `"` with `&quot;` in JSX text

### Case Block Declarations (3 errors)

**File**: `src/workers/worker.ts`
- **Lines**: 294, 301, 302
- **Fix**: Wrap case blocks in curly braces

## Warnings (282)

### TypeScript `any` Type (250+ warnings)
- **Impact**: Reduces type safety
- **Recommendation**: Gradually replace with proper types
- **Priority**: Low (warnings only)

### Unused Variables (20+ warnings)
- **Impact**: Code cleanliness
- **Recommendation**: Remove or prefix with underscore
- **Priority**: Low

### React Hooks Dependencies (10+ warnings)
- **Impact**: Potential stale closures
- **Recommendation**: Add missing dependencies or use suppressions
- **Priority**: Medium

## Backend Linting

### Missing Tools
- `flake8` - Not installed
- `black` - Not installed
- `pylint` - Not installed

### Recommendation
Add to `backend/requirements.txt`:
```
flake8==7.0.0
black==23.12.1
pylint==3.0.3
```

## Action Plan

### Immediate (Blocking)
1. Fix React Hooks violations in ConfigurationPreview.tsx
2. Fix refs access in usePerformance.ts
3. Fix setState in useMediaQuery.ts
4. Fix variable scoping in useTrainingMonitor.ts

### Short-term (Pre-release)
1. Fix all JSX unescaped entities
2. Fix case block declarations
3. Install Python linting tools
4. Run Python linting

### Long-term (Post-release)
1. Gradually replace `any` types with proper types
2. Clean up unused variables
3. Review and fix React Hooks dependencies
4. Establish linting as part of CI/CD

## Notes

- ESLint 9 configuration created (eslint.config.js)
- Prettier configuration created (.prettierrc.json)
- Linting is now part of the build process
- Many warnings are acceptable for initial release
- Critical errors should be fixed before public release
