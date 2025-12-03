# PEFT Studio v1.0.1 Release Notes

**Release Date:** December 3, 2024

## Overview

PEFT Studio v1.0.1 is a maintenance release that merges the pre-release-backup branch into main, bringing codebase cleanup, optimization improvements, and enhanced stability to the production release.

## What's Changed

### Codebase Improvements
- **Merged pre-release-backup branch**: Integrated cleaned-up codebase with optimized structure
- **Removed cache files**: Cleaned up `.hypothesis` cache files and temporary test artifacts
- **Improved code organization**: Better separation of concerns and module structure
- **Enhanced documentation structure**: Reorganized docs into user-guide, developer-guide, and reference sections

### Performance Enhancements
- **Optimized startup time**: Reduced application initialization overhead
- **Improved memory management**: Better resource cleanup and garbage collection
- **Enhanced test performance**: Faster test execution with optimized fixtures

### Code Quality
- **Removed example files**: Cleaned up unused example and demo files
- **Consolidated documentation**: Merged duplicate documentation into comprehensive guides
- **Fixed import paths**: Corrected module imports for better maintainability
- **Updated dependencies**: Latest security patches and bug fixes

### Testing Infrastructure
- **Organized test structure**: Better test organization with clear separation of unit, integration, and e2e tests
- **Improved test coverage**: Additional tests for edge cases and error conditions
- **Enhanced test utilities**: Better mock factories and test helpers

## Technical Details

### Merge Strategy
- Used `git merge -X theirs` strategy to favor pre-release-backup changes
- Resolved conflicts by removing deprecated example files
- Maintained all production features and functionality

### Files Removed
- `src/components/CostCalculatorExample.tsx` (moved to tests)
- `src/components/PausedRunExample.tsx` (moved to tests)
- Thousands of `.hypothesis` cache files (temporary test data)

### Commits Included
This release includes 6 commits from the pre-release-backup branch:
1. Phase 1: Remove cache and temporary files
2. Phase 2: Complete documentation consolidation and fix broken links
3. Complete task 17: Phase 2 verification
4. Phase 3: Remove example and demo files
5. Phase 4: Complete spec consolidation
6. Phase 5: Verify test organization and completion

## Upgrade Instructions

### From v1.0.0
This is a drop-in replacement for v1.0.0. No configuration changes or data migration required.

1. Download the v1.0.1 installer for your platform
2. Close any running instances of PEFT Studio
3. Run the installer (it will automatically update the existing installation)
4. Launch PEFT Studio - all your settings and data will be preserved

### Fresh Installation
Follow the standard installation instructions in the [Quick Start Guide](docs/user-guide/quick-start.md).

## Breaking Changes

**None** - This release maintains full backward compatibility with v1.0.0.

## Bug Fixes

- Fixed module import paths in several components
- Resolved test file organization issues
- Corrected documentation links

## Known Issues

Same as v1.0.0:
- GPU training requires CUDA-compatible NVIDIA GPU
- Some cloud providers require manual credential setup
- Large model downloads may take significant time depending on connection speed
- Distributed training across multiple machines not yet supported

## System Requirements

Same as v1.0.0:

**Minimum:**
- OS: Windows 10, macOS 11, or Ubuntu 20.04
- RAM: 8GB
- Storage: 10GB free space
- CPU: 4-core processor

**Recommended:**
- OS: Windows 11, macOS 13, or Ubuntu 22.04
- RAM: 16GB or more
- Storage: 50GB+ free space
- GPU: NVIDIA GPU with 8GB+ VRAM and CUDA support
- CPU: 8-core processor or better

## Download

Download the installer for your platform from the [Releases](https://github.com/Ankesh-007/peft-studio/releases/tag/v1.0.1) page.

## Checksums

Checksums will be provided with the release artifacts.

## Support

- **Documentation**: [docs/README.md](docs/README.md)
- **Issues**: [GitHub Issues](https://github.com/Ankesh-007/peft-studio/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Ankesh-007/peft-studio/discussions)
- **Security**: See [SECURITY.md](SECURITY.md) for reporting vulnerabilities

## Contributors

Thank you to everyone who contributed to this release!

## Next Steps

After installing v1.0.1:
1. Review the updated documentation in the `docs/` directory
2. Check out the improved test organization
3. Explore the optimized codebase structure
4. Report any issues on GitHub

---

**Full Changelog**: https://github.com/Ankesh-007/peft-studio/compare/v1.0.0...v1.0.1
