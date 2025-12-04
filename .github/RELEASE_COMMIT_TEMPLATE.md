# Release Commit Template

Use this template when preparing a release commit.

## Commit Message Format

```
chore: prepare v{VERSION} release

- Clean up build artifacts and cache files
- Update version to {VERSION}
- Generate installers for all platforms
- Create checksums for verification
- Update documentation

Release notes: See CHANGELOG.md
```

## Example

```
chore: prepare v1.0.1 release

- Clean up build artifacts and cache files
- Update version to 1.0.1
- Generate installers for all platforms
- Create checksums for verification
- Update documentation

Release notes: See CHANGELOG.md
```

## Tag Message Format

```
Release v{VERSION}

{Brief description of what's in this release}

See CHANGELOG.md for full details.
```

## Example

```
Release v1.0.1

Bug fixes and improvements:
- Fixed dependency verification
- Improved error handling
- Enhanced startup performance
- Updated documentation

See CHANGELOG.md for full details.
```
