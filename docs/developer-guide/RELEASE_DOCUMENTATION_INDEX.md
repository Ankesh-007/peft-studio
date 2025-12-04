# Release Documentation Index

Complete index of all release-related documentation for PEFT Studio.

## Quick Access

- **[RELEASE_GUIDE.md](../../RELEASE_GUIDE.md)** - Quick reference in repository root
- **[Complete Release Process](./release-process.md)** - Start here for overview
- **[Step-by-Step Guide](./release-step-by-step.md)** - Detailed instructions
- **[Scripts Reference](./release-scripts-reference.md)** - All script options
- **[Troubleshooting](./release-troubleshooting.md)** - Problem solving
- **[Dry-Run Testing](./release-dry-run-testing.md)** - Safe testing

## Documentation Structure

### 1. Release Process Overview

**File**: [release-process.md](./release-process.md)

**Contents**:
- Overview of the complete release workflow
- Prerequisites and requirements
- Quick release vs step-by-step approaches
- Script reference summary
- Troubleshooting overview
- Best practices

**Use when**: You need a high-level understanding of the release process

---

### 2. Step-by-Step Release Guide

**File**: [release-step-by-step.md](./release-step-by-step.md)

**Contents**:
- Detailed preparation steps
- Pre-release checklist
- Step-by-step release instructions
- Post-release verification
- Rollback procedures
- Release timing and communication

**Use when**: You're performing a release and need detailed instructions

---

### 3. Release Scripts Reference

**File**: [release-scripts-reference.md](./release-scripts-reference.md)

**Contents**:
- Complete documentation for all scripts:
  - cleanup-repository.js
  - validate-release.js
  - build.js
  - generate-checksums.js
  - release-to-github.js
  - complete-release.js
- Usage, options, and examples
- Environment variables
- Exit codes

**Use when**: You need to understand specific script options or behavior

---

### 4. Release Troubleshooting Guide

**File**: [release-troubleshooting.md](./release-troubleshooting.md)

**Contents**:
- Environment issues
- Validation failures
- Build failures
- Checksum issues
- GitHub release issues
- Platform-specific problems
- Network issues
- Recovery procedures

**Use when**: You encounter errors or issues during release

---

### 5. Dry-Run Testing Guide

**File**: [release-dry-run-testing.md](./release-dry-run-testing.md)

**Contents**:
- What is dry-run mode
- Why use dry-run
- Testing individual scripts
- Testing complete release
- Interpreting output
- Common test scenarios
- Best practices

**Use when**: You want to test the release process safely

---

### 6. Quick Reference Guide

**File**: [../../RELEASE_GUIDE.md](../../RELEASE_GUIDE.md) (repository root)

**Contents**:
- Quick release commands
- Common options
- Version numbering
- Basic troubleshooting
- Links to detailed docs

**Use when**: You need a quick reminder of release commands

---

## Documentation by Task

### First-Time Release

1. Read [Release Process Overview](./release-process.md)
2. Follow [Step-by-Step Guide](./release-step-by-step.md)
3. Use [Dry-Run Testing](./release-dry-run-testing.md) to test
4. Keep [Troubleshooting Guide](./release-troubleshooting.md) handy

### Regular Releases

1. Use [Quick Reference](../../RELEASE_GUIDE.md)
2. Refer to [Scripts Reference](./release-scripts-reference.md) for options
3. Check [Troubleshooting](./release-troubleshooting.md) if issues arise

### Debugging Release Issues

1. Check [Troubleshooting Guide](./release-troubleshooting.md) first
2. Review [Scripts Reference](./release-scripts-reference.md) for correct usage
3. Use [Dry-Run Testing](./release-dry-run-testing.md) to isolate issues

### Learning the Release Process

1. Start with [Release Process Overview](./release-process.md)
2. Read [Step-by-Step Guide](./release-step-by-step.md)
3. Practice with [Dry-Run Testing](./release-dry-run-testing.md)
4. Review [Scripts Reference](./release-scripts-reference.md) for details

---

## Documentation by Role

### Release Manager

**Primary docs**:
- [Release Process](./release-process.md)
- [Step-by-Step Guide](./release-step-by-step.md)
- [Troubleshooting](./release-troubleshooting.md)

**Reference docs**:
- [Scripts Reference](./release-scripts-reference.md)
- [Quick Reference](../../RELEASE_GUIDE.md)

### Developer

**Primary docs**:
- [Quick Reference](../../RELEASE_GUIDE.md)
- [Dry-Run Testing](./release-dry-run-testing.md)

**Reference docs**:
- [Scripts Reference](./release-scripts-reference.md)
- [Troubleshooting](./release-troubleshooting.md)

### New Team Member

**Learning path**:
1. [Release Process Overview](./release-process.md)
2. [Dry-Run Testing Guide](./release-dry-run-testing.md)
3. [Step-by-Step Guide](./release-step-by-step.md)
4. [Scripts Reference](./release-scripts-reference.md)

---

## Related Documentation

### Build Documentation

- [Build and Installers Guide](./build-and-installers.md)
- [Installer Build Guide](./installer-build-guide.md)
- [Code Signing](./code-signing.md)

### Testing Documentation

- [Test Release Process](./test-release-process.md)
- [Test Windows Installer](./test-windows-installer.md)
- [Test macOS Installer](./test-macos-installer.md)
- [Test Linux Installer](./test-linux-installer.md)
- [Test Auto-Update](./test-auto-update.md)

### General Documentation

- [BUILDING.md](../../BUILDING.md) - Building from source
- [DEVELOPMENT.md](../../DEVELOPMENT.md) - Development setup
- [CONTRIBUTING.md](../../CONTRIBUTING.md) - Contribution guidelines

---

## Quick Commands Reference

### Complete Release

```bash
# Test release
node scripts/complete-release.js --dry-run

# Execute release
node scripts/complete-release.js
```

### Individual Steps

```bash
# Cleanup
node scripts/cleanup-repository.js

# Validate
node scripts/validate-release.js

# Build
node scripts/build.js all

# Checksums
node scripts/generate-checksums.js

# Release
node scripts/release-to-github.js
```

### Common Options

```bash
# Skip cleanup
node scripts/complete-release.js --skip-cleanup

# Skip tests
node scripts/complete-release.js --skip-tests

# Draft release
node scripts/complete-release.js --draft

# Dry run
node scripts/complete-release.js --dry-run
```

---

## Documentation Maintenance

### Updating Documentation

When updating release scripts or process:

1. Update relevant documentation files
2. Update this index if structure changes
3. Update [Quick Reference](../../RELEASE_GUIDE.md)
4. Update [Scripts README](../../scripts/README.md)
5. Test all documented commands
6. Update "Last Updated" dates

### Documentation Standards

- Use clear, concise language
- Include code examples
- Provide troubleshooting tips
- Link to related documentation
- Keep examples up to date
- Test all commands before documenting

---

## Feedback

If you find issues with the documentation or have suggestions:

- Open an issue on GitHub
- Submit a pull request with improvements
- Contact the maintainers

---

**Last Updated**: 2024-12-04
