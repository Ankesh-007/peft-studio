# Build and Release PEFT Studio v1.0.1 - FINAL STEPS

## ✅ COMPLETED
- Code committed and pushed to GitHub
- Tag v1.0.1 created and pushed
- All documentation created
- Repository cleaned up (~387 MB removed)

## 🚀 NEXT: Build Installers and Publish

### Step 1: Build the Application

```powershell
npm run build
```

**Expected:** Application builds successfully in `dist/` directory

### Step 2: Package Installers

```powershell
npm run package:all
```

**Expected:** Installers created in `release/` directory:
- Windows: `PEFT-Studio-Setup-1.0.1.exe`, `PEFT-Studio-Portable-1.0.1.exe`
- macOS: `PEFT-Studio-1.0.1-x64.dmg`, `PEFT-Studio-1.0.1-arm64.dmg`
- Linux: `PEFT-Studio-1.0.1-x64.AppImage`, `PEFT-Studio-1.0.1-x64.deb`

**Time:** ~10-15 minutes

### Step 3: Generate Checksums

```powershell
npm run generate:checksums
```

**Expected:** `checksums.txt` file created in `release/` directory

### Step 4: Create GitHub Release

1. **Go to:** https://github.com/Ankesh-007/peft-studio/releases

2. **Click:** "Draft a new release"

3. **Select tag:** v1.0.1

4. **Title:** PEFT Studio v1.0.1

5. **Description:** Copy from `RELEASE_COMPLETE.md` (section "Add Release Notes")

6. **Upload files from `release/` directory:**
   - All `.exe` files (Windows)
   - All `.dmg` and `.zip` files (macOS)
   - All `.AppImage` and `.deb` files (Linux)
   - `checksums.txt`

7. **Click:** "Publish release"

## 📋 Quick Command Sequence

Run these commands in order:

```powershell
# 1. Build
npm run build

# 2. Package
npm run package:all

# 3. Checksums
npm run generate:checksums

# 4. Verify files exist
dir release\

# 5. Go to GitHub and create release
start https://github.com/Ankesh-007/peft-studio/releases/new?tag=v1.0.1
```

## ⏱️ Time Estimate

- Build: ~2-3 minutes
- Package: ~10-15 minutes
- Checksums: ~10 seconds
- Upload to GitHub: ~5 minutes
- **Total: ~20-25 minutes**

## ✅ Success Criteria

After completing all steps:
- [ ] Build completed without errors
- [ ] All installer files exist in `release/` directory
- [ ] Checksums file generated
- [ ] GitHub release published
- [ ] All installers uploaded
- [ ] Release visible at https://github.com/Ankesh-007/peft-studio/releases

## 🆘 Troubleshooting

### Build fails
```powershell
npm run type-check
npm run lint
```
Fix any errors and retry.

### Package fails
```powershell
npm install
npm run build
npm run package:all
```

### Missing files in release/
Check that build completed successfully:
```powershell
dir dist\
```

## 📚 Documentation

- **Full Guide:** `RELEASE_GUIDE.md`
- **Checklist:** `RELEASE_CHECKLIST.md`
- **Automation:** `.kiro/specs/peft-application-fix/RELEASE_AUTOMATION.md`

## 🎉 After Release

1. Test installers on each platform
2. Verify auto-update works
3. Monitor GitHub issues
4. Announce release (if applicable)

---

**Ready? Run the commands above to complete the release!**
