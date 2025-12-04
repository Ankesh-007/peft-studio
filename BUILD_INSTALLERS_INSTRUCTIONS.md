# Build Installers for v1.0.1 - Instructions

## ✅ What's Complete

- ✅ Code committed and pushed to GitHub
- ✅ Tag v1.0.1 created and pushed
- ✅ Application builds successfully (`npm run build`)
- ✅ TypeScript compilation fixed
- ✅ All source code ready

## ⚠️ Issue: Permission Error on Windows

The installer build is failing due to Windows permission restrictions:
```
ERROR: Cannot create symbolic link : A required privilege is not held by the client
```

## 🔧 Solutions

### Option 1: Run PowerShell as Administrator (Recommended)

1. **Close current PowerShell**
2. **Right-click PowerShell** → "Run as Administrator"
3. **Navigate to project:**
   ```powershell
   cd "D:\PEFT Studio"
   ```
4. **Build installers:**
   ```powershell
   npm run build
   npx electron-builder --win --linux
   ```

### Option 2: Enable Developer Mode (Windows 10/11)

1. Open **Settings** → **Update & Security** → **For Developers**
2. Turn on **Developer Mode**
3. Restart PowerShell
4. Run:
   ```powershell
   npm run build
   npx electron-builder --win --linux
   ```

### Option 3: Use GitHub Actions (Automated)

The repository already has GitHub Actions configured. You can:

1. Go to: https://github.com/Ankesh-007/peft-studio/actions
2. Find the "Build Installers" workflow
3. Click "Run workflow"
4. Select branch: `main`
5. Click "Run workflow"

This will build installers for all platforms (Windows, macOS, Linux) automatically.

### Option 4: Build Only Windows (Skip Linux)

If you only need Windows installers:

```powershell
# Run as Administrator
npm run build
npx electron-builder --win
```

## 📦 Expected Output

After successful build, you'll have in `release/` directory:

**Windows:**
- `PEFT-Studio-Setup-1.0.1.exe` (~97 MB)
- `PEFT-Studio-Portable-1.0.1.exe` (~97 MB)

**Linux:**
- `PEFT-Studio-1.0.1-x86_64.AppImage` (~119 MB)
- `PEFT-Studio-1.0.1-amd64.deb` (~80 MB)

**Note:** macOS installers can only be built on macOS machines.

## 🚀 After Building

1. **Generate checksums:**
   ```powershell
   npm run generate:checksums
   ```

2. **Verify files exist:**
   ```powershell
   dir release\
   ```

3. **Create GitHub Release:**
   - Go to: https://github.com/Ankesh-007/peft-studio/releases/new?tag=v1.0.1
   - Upload all installer files
   - Upload `checksums.txt`
   - Publish release

## 📋 Alternative: Manual Upload of v1.0.0 with Note

If building is problematic, you can:

1. Create GitHub release for v1.0.1
2. Add release notes explaining the fixes
3. Note that installers will be added soon
4. Or temporarily link to v1.0.0 installers with upgrade instructions

## 🆘 Troubleshooting

### Still getting permission errors?
- Ensure you're running PowerShell as Administrator
- Check Windows Defender isn't blocking
- Try disabling antivirus temporarily

### Build takes too long?
- Normal build time: 10-15 minutes
- Be patient, especially for first build

### Out of disk space?
- Build requires ~2GB free space
- Clean up: `npm run prepare:release`

## ✅ Verification

After build completes:

```powershell
# Check files exist
Test-Path release\PEFT-Studio-Setup-1.0.1.exe
Test-Path release\PEFT-Studio-Portable-1.0.1.exe

# Check file sizes (should be ~97 MB each)
(Get-Item release\PEFT-Studio-Setup-1.0.1.exe).Length / 1MB
```

## 📞 Need Help?

- Check: `RELEASE_GUIDE.md`
- Check: `BUILD_AND_RELEASE_NOW.md`
- GitHub Issues: https://github.com/Ankesh-007/peft-studio/issues

---

**Current Status:** Code is ready, just need to build installers with proper permissions.

**Recommended:** Run PowerShell as Administrator and execute `npx electron-builder --win --linux`
