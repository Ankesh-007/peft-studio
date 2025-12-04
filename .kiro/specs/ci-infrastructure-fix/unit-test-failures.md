# Unit Test Failures Analysis

## Summary
- **Total Test Files**: 32 (13 failed, 19 passed)
- **Total Tests**: 270 (41 failed, 229 passed)
- **Duration**: 50.39s

## Failure Categories

### 1. Import/Component Errors (6 failures)
**Type**: Missing or incorrect component exports

- `src/test/preset-library.test.tsx` - All 6 tests failing
  - Error: "Element type is invalid: expected a string (for built-in components) or a class/function (for composite components) but got: undefined"
  - **Root Cause**: PresetLibrary component not properly exported or imported

### 2. Missing UI Elements (10 failures)
**Type**: Tests expecting UI elements that don't exist in rendered output

#### CommandPalette Tests (1 failure)
- `src/test/navigation.test.tsx > CommandPalette > should filter commands based on search input`
  - Missing: searchbox role element
  - **Root Cause**: CommandPalette doesn't render searchbox with proper role

#### Training Flow Integration Tests (3 failures)
- `src/test/training-flow-integration.test.tsx > should allow pausing and resuming training`
  - Missing: "quick actions" text
- `src/test/training-flow-integration.test.tsx > should handle training completion`
  - Missing: "good morning" text (greeting)
- `src/test/training-flow-integration.test.tsx > should allow exporting trained model`
  - Missing: "quick actions" text
  - **Root Cause**: Dashboard component renders loading state instead of actual content

### 3. Timeout Issues (6 failures)
**Type**: Tests timing out after 10 seconds

#### UpdateNotification Tests (4 failures)
- `should show not available state and auto-dismiss`
- `should dismiss notification when X button clicked`
- `should format bytes correctly`
- `should show current version in update available notification`
  - **Root Cause**: Tests using fake timers but not properly advancing them, or waiting for async operations that never complete

#### Bundle Size Test (1 failure)
- `src/test/unit/bundle-size-constraint.test.ts > should ensure production build does not exceed 200MB`
  - **Root Cause**: Test attempts to build application which takes longer than 10s timeout

### 4. Missing Files (1 failure)
**Type**: Configuration files don't exist

- `src/test/unit/electron-builder-config.test.ts > Code signing configuration is present`
  - Missing: macOS entitlements file
  - **Root Cause**: Entitlements file path configured but file doesn't exist

### 5. Property-Based Test Failures (2 failures)
**Type**: PBT tests finding counterexamples

#### GitHub Release Workflow Tests (2 failures)
- `Property 4: Release notes include installation instructions`
  - Counterexample: `[[0,0,0]]` (version 0.0.0)
  - Missing: "## 📋 Installation Instructions" section
  
- `Property 24: Platform-specific instructions in notes`
  - Counterexample: `{"major":0,"minor":0,"patch":0,"platform":"windows"}`
  - Missing: "### Windows Installation" section
  - **Root Cause**: Release notes template doesn't include installation instructions sections

## Fix Priority

### High Priority (Blocking many tests)
1. **PresetLibrary component export** - 6 tests
2. **Dashboard loading state** - 3 tests  
3. **UpdateNotification async handling** - 4 tests

### Medium Priority
4. **CommandPalette searchbox role** - 1 test
5. **Release notes template** - 2 tests (PBT)
6. **Bundle size test timeout** - 1 test

### Low Priority
7. **macOS entitlements file** - 1 test

## Detailed Failure List

### Import/Component Errors
1. ❌ `src/test/preset-library.test.tsx > PresetLibrary > should render preset library component`
2. ❌ `src/test/preset-library.test.tsx > PresetLibrary > should display available presets`
3. ❌ `src/test/preset-library.test.tsx > PresetLibrary > should call onSelectPreset when preset is clicked`
4. ❌ `src/test/preset-library.test.tsx > PresetLibrary > should show preset details on hover or selection`
5. ❌ `src/test/preset-library.test.tsx > PresetLibrary > should filter presets by category`
6. ❌ `src/test/preset-library.test.tsx > PresetLibrary > should display preset configuration preview`

### Missing UI Elements
7. ❌ `src/test/navigation.test.tsx > CommandPalette > should filter commands based on search input`
8. ❌ `src/test/training-flow-integration.test.tsx > Training Flow Integration > should allow pausing and resuming training`
9. ❌ `src/test/training-flow-integration.test.tsx > Training Flow Integration > should handle training completion`
10. ❌ `src/test/training-flow-integration.test.tsx > Training Flow Integration > should allow exporting trained model`

### Timeout Issues
11. ❌ `src/test/components/UpdateNotification.test.tsx > UpdateNotification > should show not available state and auto-dismiss`
12. ❌ `src/test/components/UpdateNotification.test.tsx > UpdateNotification > should dismiss notification when X button clicked`
13. ❌ `src/test/components/UpdateNotification.test.tsx > UpdateNotification > should format bytes correctly`
14. ❌ `src/test/components/UpdateNotification.test.tsx > UpdateNotification > should show current version in update available notification`
15. ❌ `src/test/unit/bundle-size-constraint.test.ts > Bundle Size Constraint Property Test > should ensure production build does not exceed 200MB`

### Missing Files
16. ❌ `src/test/unit/electron-builder-config.test.ts > Code Signing Configuration Properties > Code signing configuration is present`

### Property-Based Test Failures
17. ❌ `src/test/unit/github-release-workflow.test.ts > GitHub Release Notes Template Properties > Property 4: Release notes include installation instructions`
18. ❌ `src/test/unit/github-release-workflow.test.ts > GitHub Release Notes Template Properties > Property 24: Platform-specific instructions in notes`

## Next Steps

1. Fix PresetLibrary component import/export
2. Fix Dashboard component to render actual content instead of loading state in tests
3. Fix UpdateNotification tests to properly handle async operations and timers
4. Fix CommandPalette to include searchbox with proper role
5. Update release notes template to include installation instructions
6. Increase timeout or skip bundle size test
7. Create macOS entitlements file or update test expectations
