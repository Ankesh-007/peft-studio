# Checksum Generation Process for Release 1.0.1

## Overview

The checksum generation process creates SHA256 hashes for all installer files to ensure download integrity and security.

## Script Ready ✅

The checksum generation script is located at `scripts/generate-checksums.js` and is fully functional.

## Usage

### After Installers are Built

Once the installers are built (via GitHub Actions or manual build), run:

```bash
npm run generate:checksums
```

Or directly:

```bash
node scripts/generate-checksums.js ./release
```

## What the Script Does

1. **Scans the release directory** for installer files:
   - Windows: `.exe` files (NSIS installer, portable)
   - macOS: `.dmg` and `.zip` files
   - Linux: `.AppImage` and `.deb` files

2. **Calculates SHA256 checksums** for each installer file

3. **Creates `SHA256SUMS.txt`** in the release directory with format:
   ```
   <hash>  <filename>
   <hash>  <filename>
   ```

4. **Verifies** that all expected installer files have checksums

## Expected Output

For release 1.0.1, the following files should be checksummed:

### Windows
- `PEFT Studio-Setup-1.0.1.exe` (NSIS installer)
- `PEFT Studio-Portable-1.0.1.exe` (Portable version)

### macOS
- `PEFT Studio-1.0.1-x64.dmg` (Intel)
- `PEFT Studio-1.0.1-arm64.dmg` (Apple Silicon)
- `PEFT Studio-1.0.1-x64.zip` (Intel)
- `PEFT Studio-1.0.1-arm64.zip` (Apple Silicon)

### Linux
- `PEFT Studio-1.0.1-x64.AppImage`
- `PEFT Studio-1.0.1-x64.deb`

## Verification Process

### Manual Verification

After generating checksums, verify them manually:

**On Windows (PowerShell):**
```powershell
Get-FileHash -Algorithm SHA256 "release\PEFT Studio-Setup-1.0.1.exe"
```

**On macOS/Linux:**
```bash
shasum -a 256 "release/PEFT Studio-1.0.1-x64.dmg"
```

Compare the output with the corresponding line in `SHA256SUMS.txt`.

### Automated Verification

The script includes verification logic that can be tested:

```bash
# Run checksum tests
npm test -- src/test/pbt/checksum-generation.pbt.test.ts
npm test -- src/test/pbt/checksum-verification.pbt.test.ts
```

## Integration with GitHub Release

When creating the GitHub release (task 7.5), the `SHA256SUMS.txt` file should be:

1. **Uploaded as a release asset** alongside the installers
2. **Included in the release notes** for user reference
3. **Documented in user guides** for verification instructions

## User Documentation

Users can verify their downloads using the checksums:

**Windows (PowerShell):**
```powershell
$hash = (Get-FileHash -Algorithm SHA256 "PEFT Studio-Setup-1.0.1.exe").Hash.ToLower()
$expected = (Get-Content SHA256SUMS.txt | Select-String "PEFT Studio-Setup-1.0.1.exe").Line.Split()[0]
if ($hash -eq $expected) { Write-Host "✓ Checksum verified" } else { Write-Host "✗ Checksum mismatch" }
```

**macOS/Linux:**
```bash
shasum -a 256 -c SHA256SUMS.txt
```

## Status

- ✅ Script implemented and tested
- ✅ Property-based tests created
- ⏳ Awaiting installer builds to generate actual checksums
- ⏳ Will be executed as part of GitHub Actions release workflow

## Next Steps

1. Wait for installers to be built (via GitHub Actions)
2. Run `npm run generate:checksums`
3. Verify checksums manually for at least one file per platform
4. Upload `SHA256SUMS.txt` to GitHub release
5. Update user documentation with verification instructions

## Related Files

- `scripts/generate-checksums.js` - Main script
- `src/test/pbt/checksum-generation.pbt.test.ts` - Property-based tests
- `src/test/pbt/checksum-verification.pbt.test.ts` - Verification tests
- `docs/user-guide/checksum-verification.md` - User documentation
