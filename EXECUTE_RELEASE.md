# Execute Release v1.0.1 - Quick Start

## Prerequisites

✅ All fixes implemented
✅ Tests passing
✅ Version updated to 1.0.1 in package.json
✅ CHANGELOG.md updated

## Option 1: Fully Automated (Recommended)

### Step 1: Dry Run First
```powershell
npm run release:dry
```

Review the output to ensure everything looks correct.

### Step 2: Execute Release
```powershell
npm run release
```

This will:
1. ✅ Clean up unnecessary files
2. ✅ Run tests
3. ✅ Build application
4. ✅ Package installers
5. ✅ Generate checksums
6. ✅ Commit changes
7. ✅ Create and push Git tag

### Step 3: Create GitHub Release

1. Go to: https://github.com/Ankesh-007/peft-studio/releases
2. Click "Draft a new release"
3. Select tag: `v1.0.1`
4. Title: `PEFT Studio v1.0.1`
5. Copy release notes from `CHANGELOG.md`
6. Upload files from `release/` directory:
   - `PEFT-Studio-Setup-1.0.1.exe`
   - `PEFT-Studio-Portable-1.0.1.exe`
   - `PEFT-Studio-1.0.1-x64.dmg`
   - `PEFT-Studio-1.0.1-arm64.dmg`
   - `PEFT-Studio-1.0.1-x64.AppImage`
   - `PEFT-Studio-1.0.1-x64.deb`
   - `checksums.txt`
7. Click "Publish release"

## Option 2: Manual Control

If you prefer step-by-step control:

```powershell
# 1. Clean up (dry run first)
npm run prepare:release:dry
npm run prepare:release

# 2. Test
npm run test:run

# 3. Build
npm run build

# 4. Package
npm run package:all

# 5. Checksums
npm run generate:checksums

# 6. Commit
git add .
git commit -m "chore: prepare v1.0.1 release"

# 7. Tag and push
git tag -a v1.0.1 -m "Release v1.0.1"
git push origin main --tags

# 8. Create GitHub release (see Step 3 above)
```

## What Gets Cleaned Up

The cleanup removes ~4000+ unnecessary files:
- Build artifacts (release/win-unpacked, dist/*)
- Backend cache (.hypothesis, .pytest_cache)
- Temporary databases and logs
- Old documentation files

**All critical files are preserved and verified!**

## Verification

After cleanup, verify:
```powershell
# Check Git status
git status

# Verify critical files exist
Test-Path package.json
Test-Path README.md
Test-Path LICENSE
Test-Path CHANGELOG.md
```

## Troubleshooting

### If tests fail:
```powershell
npm run test:run
# Fix any failing tests, then retry
```

### If build fails:
```powershell
npm run type-check
# Fix TypeScript errors, then retry
```

### If you need to undo:
```powershell
# Undo commit
git reset --soft HEAD~1

# Delete tag
git tag -d v1.0.1

# Restore files
git checkout .
```

## Time Estimate

- Automated: ~10-15 minutes
- Manual: ~20-30 minutes
- GitHub release creation: ~5 minutes

**Total: ~15-35 minutes**

## Success Criteria

✅ All unnecessary files removed
✅ All tests passing
✅ Installers built for all platforms
✅ Checksums generated
✅ Git tag created and pushed
✅ GitHub release published
✅ Installers downloadable

## Next Steps After Release

1. Test auto-update functionality
2. Verify installers work on each platform
3. Monitor GitHub issues for problems
4. Announce release (if applicable)

## Support

- Full guide: `RELEASE_GUIDE.md`
- Technical details: `.kiro/specs/peft-application-fix/RELEASE_AUTOMATION.md`
- Issues: https://github.com/Ankesh-007/peft-studio/issues

---

**Ready to release? Run:** `npm run release:dry` **first!**
