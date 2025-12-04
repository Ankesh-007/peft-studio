# PEFT Studio Release Guide

Quick reference for creating PEFT Studio releases.

## Prerequisites

- Node.js 18+
- Git
- GitHub token with `repo` scope
- Clean working directory
- Updated CHANGELOG.md

## Quick Release

```bash
# Set GitHub token
export GITHUB_TOKEN="your_github_token"

# Bump version
npm version patch  # or minor, or major

# Update CHANGELOG.md
# Add entry for new version

# Commit changes
git add .
git commit -m "chore: prepare release v1.0.0"
git push origin main

# Test release (dry-run)
node scripts/complete-release.js --dry-run

# Execute release
node scripts/complete-release.js
```

## Release Steps

The `complete-release.js` script executes these steps automatically:

1. **Cleanup**: Remove unnecessary files
2. **Validate**: Verify repository readiness
3. **Build**: Create installers for all platforms
4. **Checksum**: Generate SHA256 checksums
5. **Release**: Create GitHub release and upload assets

## Manual Step-by-Step

If you prefer to run steps individually:

```bash
# 1. Clean repository
node scripts/cleanup-repository.js

# 2. Validate readiness
node scripts/validate-release.js

# 3. Build installers
node scripts/build.js all

# 4. Generate checksums
node scripts/generate-checksums.js

# 5. Create GitHub release
node scripts/release-to-github.js
```

## Common Options

```bash
# Dry run (test without changes)
node scripts/complete-release.js --dry-run

# Skip cleanup
node scripts/complete-release.js --skip-cleanup

# Skip tests (faster)
node scripts/complete-release.js --skip-tests

# Create draft release
node scripts/complete-release.js --draft

# Combine options
node scripts/complete-release.js --dry-run --skip-tests
```

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **Patch** (1.0.0 → 1.0.1): Bug fixes
- **Minor** (1.0.0 → 1.1.0): New features (backward compatible)
- **Major** (1.0.0 → 2.0.0): Breaking changes

```bash
npm version patch   # Bug fixes
npm version minor   # New features
npm version major   # Breaking changes
```

## Troubleshooting

### GITHUB_TOKEN not set

```bash
export GITHUB_TOKEN="your_token_here"
```

### Working directory not clean

```bash
git status
git add .
git commit -m "commit message"
```

### CHANGELOG missing version

Edit `CHANGELOG.md` and add:

```markdown
## [1.0.0] - 2024-12-04

### Added
- Feature description

### Changed
- Change description

### Fixed
- Bug fix description
```

### Tests failing

```bash
npm run test:run
# Fix failing tests
```

### Build fails

```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Retry build
node scripts/build.js all
```

## Comprehensive Documentation

For detailed information, see:

- **[Complete Release Process](docs/developer-guide/release-process.md)** - Full release workflow
- **[Step-by-Step Guide](docs/developer-guide/release-step-by-step.md)** - Detailed instructions
- **[Scripts Reference](docs/developer-guide/release-scripts-reference.md)** - All script options
- **[Troubleshooting](docs/developer-guide/release-troubleshooting.md)** - Common issues and solutions
- **[Dry-Run Testing](docs/developer-guide/release-dry-run-testing.md)** - Safe testing guide

## Support

- Check [Troubleshooting Guide](docs/developer-guide/release-troubleshooting.md)
- Review script output for errors
- Open an issue on GitHub

---

**Quick Tip**: Always run `--dry-run` first to test the release process safely!
