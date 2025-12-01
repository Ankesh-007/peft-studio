# Design Document

## Overview

This design outlines a systematic approach to cleaning and optimizing the PEFT Studio codebase by removing unnecessary files, consolidating documentation, and improving organization. The cleanup will reduce repository size, improve maintainability, and make the codebase easier to navigate.

## Architecture

### Cleanup Strategy

The cleanup process follows a phased approach:

1. **Analysis Phase**: Identify all files to be removed or consolidated
2. **Consolidation Phase**: Merge related documentation and code files
3. **Removal Phase**: Delete unnecessary cache, temporary, and duplicate files
4. **Organization Phase**: Restructure remaining files into clear hierarchy
5. **Verification Phase**: Ensure all references are updated and nothing is broken

### File Categories

**Files to Remove:**
- `.hypothesis/` directory (4000+ cache files)
- `.pytest_cache/` directories
- `*_SUMMARY.md` files (consolidate into main docs)
- `*_QUICK_START.md` files (integrate into main docs)
- `*_example.py` files (duplicates of actual implementations)
- `*Example.tsx` components (demo components not used in app)
- Empty or placeholder directories

**Files to Consolidate:**
- Implementation guides + summaries → Single comprehensive guide
- Quick start + detailed guide → Unified documentation
- Multiple spec files for same feature → Single spec
- Related test files → Comprehensive test suites

**Files to Reorganize:**
- Root-level markdown files → `docs/` subdirectories
- Feature documentation → `docs/user-guide/` or `docs/developer-guide/`
- Reference materials → `docs/reference/`

## Components and Interfaces

### Documentation Structure

```
docs/
├── README.md                          # Documentation index
├── user-guide/
│   ├── quick-start.md                # Getting started (consolidated)
│   ├── training-configuration.md     # Training guide
│   ├── platform-connections.md       # Platform integration
│   ├── deployment.md                 # Deployment guide (consolidated)
│   ├── inference-playground.md       # Testing models
│   └── configuration-management.md   # Config import/export
├── developer-guide/
│   ├── api-documentation.md          # API reference
│   ├── connector-development.md      # Building connectors
│   ├── architecture.md               # System architecture
│   ├── performance-optimization.md   # Performance guide (consolidated)
│   ├── security.md                   # Security best practices (consolidated)
│   └── testing.md                    # Testing guide (consolidated)
├── reference/
│   ├── troubleshooting.md           # Common issues
│   ├── faq.md                       # Frequently asked questions
│   ├── changelog.md                 # Version history
│   └── glossary.md                  # Terms and definitions
└── video-tutorials/
    └── index.md                     # Video tutorial links
```

### Spec Structure

```
.kiro/specs/
├── README.md                        # Spec index
├── unified-llm-platform/           # Main platform spec
│   ├── requirements.md
│   ├── design.md
│   └── tasks.md
└── codebase-cleanup/               # This cleanup spec
    ├── requirements.md
    ├── design.md
    └── tasks.md
```

## Data Models

### File Mapping

```typescript
interface FileMapping {
  source: string[];           // Original file paths
  destination: string;        // New consolidated file path
  action: 'merge' | 'move' | 'delete';
  preserveContent: boolean;   // Whether to preserve all content
}

interface CleanupManifest {
  filesToDelete: string[];
  filesToConsolidate: FileMapping[];
  filesToMove: FileMapping[];
  directoriesToRemove: string[];
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

Before defining properties, let's analyze the testable acceptance criteria:

**1.1 - Documentation consolidation**: Testable as property - we can verify all unique content is preserved
**1.3 - Content preservation**: Testable as property - verify no information loss during merge
**2.1 - Cache removal**: Testable as property - verify .hypothesis directory is removed
**2.4 - .gitignore coverage**: Testable as property - verify all cache patterns are in .gitignore
**3.1 - Feature consolidation**: Testable as property - verify one primary doc per feature
**4.1 - Documentation organization**: Testable as property - verify no docs remain in root
**5.4 - Active specs**: Testable as property - verify each feature has one active spec
**6.4 - No broken imports**: Testable as property - verify no imports reference deleted files
**8.1 - README accuracy**: Testable as property - verify README matches actual structure

### Property 1: Content Preservation During Consolidation

*For any* set of files being consolidated, the merged output SHALL contain all unique information from all source files, with no content loss.

**Validates: Requirements 1.3, 3.4**

### Property 2: Cache Directory Removal Completeness

*For any* cache directory pattern (.hypothesis, .pytest_cache, __pycache__), after cleanup the repository SHALL contain no instances of these directories.

**Validates: Requirements 2.1, 2.2**

### Property 3: Documentation Organization Completeness

*For any* markdown file in the repository, after reorganization it SHALL either be in the docs/ directory hierarchy or be a required root-level file (README.md, LICENSE, etc.).

**Validates: Requirements 4.1, 4.5**

### Property 4: Single Source of Truth Per Feature

*For any* major feature in the system, after consolidation there SHALL be exactly one primary documentation file describing that feature.

**Validates: Requirements 3.1, 3.5**

### Property 5: Import Reference Integrity

*For any* file deleted during cleanup, after cleanup completion there SHALL be no import statements in the codebase that reference the deleted file.

**Validates: Requirements 6.4**

### Property 6: Spec Consolidation Completeness

*For any* feature area, after spec cleanup there SHALL be at most one active spec directory containing requirements, design, and tasks.

**Validates: Requirements 5.4**

### Property 7: .gitignore Coverage

*For any* cache or temporary file pattern, after cleanup the .gitignore file SHALL contain patterns that exclude these files from version control.

**Validates: Requirements 2.4**

### Property 8: README Structural Accuracy

*For any* directory or documentation section mentioned in README.md, after cleanup that directory or section SHALL actually exist in the repository.

**Validates: Requirements 8.1, 8.2**

## Error Handling

### Validation Before Deletion

- Verify no active imports reference files to be deleted
- Check for unique content before consolidating
- Backup critical files before major changes
- Validate all cross-references after reorganization

### Rollback Strategy

- Create git branch before cleanup
- Document all file movements and deletions
- Maintain manifest of changes for potential rollback
- Test build and tests after each major phase

### Error Recovery

- If imports break: restore deleted files and update imports first
- If content lost: restore from git history
- If tests fail: identify affected tests and fix before proceeding
- If build fails: restore build-related files

## Testing Strategy

### Unit Testing

**File Operation Tests:**
- Test file consolidation logic preserves content
- Test file movement updates references correctly
- Test deletion removes only intended files
- Test .gitignore pattern matching

**Content Validation Tests:**
- Test markdown parsing and merging
- Test cross-reference detection and updating
- Test unique content identification
- Test section header preservation

### Property-Based Testing

**Property Test 1: Content Preservation**
- Generate random sets of markdown files with overlapping content
- Consolidate them using the merge logic
- Verify all unique content appears in output
- Verify no content duplication

**Property Test 2: Reference Integrity**
- Generate random file deletion scenarios
- Check all remaining files for broken imports
- Verify no references to deleted files exist

**Property Test 3: Documentation Completeness**
- Generate random documentation structures
- Apply reorganization rules
- Verify all docs end up in correct locations
- Verify no docs remain in wrong locations

### Integration Testing

**End-to-End Cleanup Test:**
1. Run full cleanup process on test repository
2. Verify build succeeds
3. Verify all tests pass
4. Verify documentation links work
5. Verify no broken imports

**Documentation Navigation Test:**
1. Parse all markdown files
2. Extract all internal links
3. Verify all links point to existing files
4. Verify all referenced sections exist

## Implementation Details

### Phase 1: Cache and Temporary File Removal

**Files to Delete:**
```
.hypothesis/                    # 4000+ cache files
backend/.hypothesis/
backend/.pytest_cache/
backend/__pycache__/
.pytest_cache/
backend/test_artifacts/
backend/test_checkpoints/
checkpoints/
artifacts/
build/ (except README.md)
dist/
node_modules/ (if committed)
```

**Action:** Direct deletion, add to .gitignore

### Phase 2: Documentation Consolidation

**Consolidation Map:**

1. **Auto-Update Documentation:**
   - Merge: `AUTO_UPDATE_SYSTEM.md` + `AUTO_UPDATE_IMPLEMENTATION_SUMMARY.md` + `AUTO_UPDATE_QUICK_START.md` + `AUTO_UPDATE_VERIFICATION.md`
   - Output: `docs/developer-guide/auto-update-system.md`

2. **CI/CD Documentation:**
   - Merge: `CI_CD_SETUP.md` + `CI_CD_IMPLEMENTATION_SUMMARY.md` + `CI_CD_QUICK_START.md`
   - Output: `docs/developer-guide/ci-cd-setup.md`

3. **Build and Installer Documentation:**
   - Merge: `INSTALLER_GUIDE.md` + `INSTALLER_PACKAGES_IMPLEMENTATION.md` + `INSTALLER_PACKAGES_SUMMARY.md` + `BUILD_QUICK_START.md`
   - Output: `docs/developer-guide/build-and-installers.md`

4. **Performance Optimization:**
   - Merge: `BUNDLE_OPTIMIZATION.md` + `BUNDLE_SIZE_OPTIMIZATION_SUMMARY.md` + `RENDERING_PERFORMANCE_OPTIMIZATION.md` + `STARTUP_OPTIMIZATION_IMPLEMENTATION.md` + `WEB_WORKERS_IMPLEMENTATION.md` + `WEB_WORKERS_SUMMARY.md` + `BACKEND_PERFORMANCE_OPTIMIZATION.md` + `OPTIMIZATION_SUMMARY.md`
   - Output: `docs/developer-guide/performance-optimization.md`

5. **Security Documentation:**
   - Merge: `SECURITY_BEST_PRACTICES_SUMMARY.md` + `backend/services/SECURITY_IMPLEMENTATION.md`
   - Output: `docs/developer-guide/security.md`

6. **Testing Documentation:**
   - Merge: `E2E_TESTING_GUIDE.md` + `E2E_TESTING_IMPLEMENTATION_SUMMARY.md` + `E2E_QUICK_START.md`
   - Output: `docs/developer-guide/testing.md`

7. **Feature Documentation:**
   - Merge: `DEPLOYMENT_MANAGEMENT_IMPLEMENTATION.md` + `DEPLOYMENT_MANAGEMENT_COMPLETE.md` + `DEPLOYMENT_MANAGEMENT_UI_COMPLETE.md`
   - Output: `docs/user-guide/deployment.md`
   
   - Merge: `CONFIGURATION_IMPORT_EXPORT_IMPLEMENTATION.md`
   - Output: `docs/user-guide/configuration-management.md`
   
   - Merge: `INFERENCE_PLAYGROUND_IMPLEMENTATION.md`
   - Output: `docs/user-guide/inference-playground.md`
   
   - Merge: `GRADIO_DEMO_UI_IMPLEMENTATION.md`
   - Output: `docs/user-guide/gradio-demo.md`
   
   - Merge: `LOGGING_DIAGNOSTICS_IMPLEMENTATION.md`
   - Output: `docs/user-guide/logging-diagnostics.md`
   
   - Merge: `TELEMETRY_SYSTEM_IMPLEMENTATION.md` + `backend/services/TELEMETRY_SYSTEM.md`
   - Output: `docs/developer-guide/telemetry.md`

8. **Platform and Integration:**
   - Merge: `CLOUD_PLATFORM_IMPLEMENTATION.md` + `backend/services/CLOUD_PLATFORM_INTEGRATION.md`
   - Output: `docs/developer-guide/cloud-platforms.md`
   
   - Merge: `UNIFIED_MODEL_BROWSER_IMPLEMENTATION.md`
   - Output: `docs/user-guide/model-browser.md`
   
   - Merge: `COMPUTE_PROVIDER_SELECTION.md`
   - Output: `docs/user-guide/compute-providers.md`
   
   - Merge: `TRAINING_CONFIGURATION_WIZARD.md`
   - Output: `docs/user-guide/training-configuration.md` (update existing)

9. **Backend Services Documentation:**
   - Merge: `backend/services/COST_CALCULATOR.md`
   - Output: `docs/developer-guide/cost-calculator.md`
   
   - Merge: `backend/services/CREDENTIAL_MANAGEMENT.md`
   - Output: `docs/developer-guide/credential-management.md`
   
   - Merge: `backend/services/EXPORT_SYSTEM.md`
   - Output: `docs/developer-guide/export-system.md`
   
   - Merge: `backend/services/GRADIO_DEMO_GENERATOR.md`
   - Output: `docs/developer-guide/gradio-generator.md`
   
   - Merge: `backend/services/MULTI_RUN_MANAGEMENT.md`
   - Output: `docs/developer-guide/multi-run-management.md`
   
   - Merge: `backend/services/NOTIFICATION_SYSTEM.md`
   - Output: `docs/developer-guide/notification-system.md`
   
   - Merge: `backend/services/PLATFORM_CONNECTION_MANAGER.md`
   - Output: `docs/developer-guide/platform-connections.md`
   
   - Merge: `backend/services/TRAINING_ORCHESTRATOR_IMPLEMENTATION.md` + `backend/services/TRAINING_ORCHESTRATOR_API.md`
   - Output: `docs/developer-guide/training-orchestrator.md`
   
   - Merge: `backend/services/WANDB_INTEGRATION.md`
   - Output: `docs/developer-guide/wandb-integration.md`

10. **Keep in Root (Update):**
    - `README.md` - Update with new structure
    - `QUICKSTART.md` - Update with consolidated info
    - `DEVELOPMENT.md` - Update with new paths
    - `ERROR_HANDLING.md` - Move to docs/reference/
    - `FEATURES.md` - Consolidate into README.md
    - `PROJECT_STATUS.md` - Update or remove (info in README)
    - `PAUSED_RUN_MANAGEMENT.md` - Move to docs/developer-guide/

### Phase 3: Code File Cleanup

**Example Files to Remove:**
```
backend/services/*_example.py
backend/services/*_integration_example.py
src/components/*Example.tsx
```

**Specific Files:**
- `backend/services/cloud_platform_example.py` (keep cloud_platform_service.py)
- `backend/services/comparison_integration_example.py` (keep comparison_service.py)
- `backend/services/notification_integration_example.py` (keep notification_service.py)
- `backend/services/performance_example.py` (keep performance_service.py)
- `backend/services/telemetry_integration_example.py` (keep telemetry_service.py)
- `backend/services/wandb_integration_example.py` (keep wandb_integration_service.py)
- `src/components/ComputeProviderSelectorExample.tsx` (keep ComputeProviderSelector.tsx)
- `src/components/CostCalculatorExample.tsx` (keep CostEstimateDisplay.tsx)
- `src/components/PausedRunExample.tsx` (keep PausedRunDisplay.tsx)
- `src/components/WorkerDemo.tsx` (demo component, not used)

### Phase 4: Spec Consolidation

**Current Specs:**
- `.kiro/specs/desktop-app-optimization/` - Merge into unified-llm-platform
- `.kiro/specs/simplified-llm-optimization/` - Merge into unified-llm-platform
- `.kiro/specs/unified-llm-platform/` - Keep as main spec
- `.kiro/specs/codebase-cleanup/` - Keep (this spec)

**Action:** Consolidate all optimization specs into unified-llm-platform

### Phase 5: Test Organization

**Test Consolidation:**
- Group related tests into comprehensive test files
- Remove duplicate test fixtures
- Clean test artifact directories
- Ensure test structure mirrors source structure

### Phase 6: Final Updates

**Update Files:**
1. `README.md` - New structure, updated links
2. `docs/README.md` - Documentation index
3. `.gitignore` - Ensure all cache patterns covered
4. `package.json` - Verify scripts still work
5. `.kiro/specs/README.md` - Updated spec structure

## Performance Considerations

### Cleanup Performance

- Process files in batches to avoid memory issues
- Use streaming for large file operations
- Parallelize independent operations
- Cache file content analysis results

### Post-Cleanup Performance

- Reduced repository size improves clone/pull speed
- Fewer files improve IDE indexing performance
- Clearer structure improves developer navigation speed
- Consolidated docs improve search performance

## Security Considerations

### Data Safety

- Never delete files containing credentials or secrets
- Preserve all configuration files
- Backup before major deletions
- Verify no sensitive data in files to be deleted

### Access Control

- Maintain file permissions during moves
- Preserve .gitignore patterns
- Keep security-related documentation
- Maintain audit trail of changes

## Deployment Strategy

### Execution Plan

1. Create cleanup branch from main
2. Run Phase 1: Cache removal
3. Commit and verify build
4. Run Phase 2: Documentation consolidation
5. Commit and verify links
6. Run Phase 3: Code cleanup
7. Commit and verify tests
8. Run Phase 4: Spec consolidation
9. Commit and verify
10. Run Phase 5: Test organization
11. Commit and verify tests pass
12. Run Phase 6: Final updates
13. Commit and create PR
14. Review and merge

### Verification Checklist

- [ ] Build succeeds
- [ ] All tests pass
- [ ] No broken imports
- [ ] All documentation links work
- [ ] README accurately reflects structure
- [ ] .gitignore covers all cache patterns
- [ ] No duplicate documentation
- [ ] One spec per feature area
- [ ] All unique content preserved

## Maintenance

### Ongoing Cleanup

- Add pre-commit hooks to prevent cache file commits
- Regular documentation audits
- Automated link checking
- Periodic dependency cleanup
- Monitor repository size

### Documentation Standards

- One primary doc per feature
- Quick start sections in main docs
- Clear cross-references
- Consistent formatting
- Regular updates with code changes
