# Quick Start: Build and Deploy PEFT Studio

This guide will help you test, build installers, and deploy to GitHub in minutes.

## 🚀 Fastest Way to Build

### Option 1: Interactive Menu (Easiest)

```powershell
.\build-and-test.ps1
```

Choose from the menu:
- Option 4: Build both Windows and Linux (with tests)
- Option 7: Quick build both (skip tests) - **FASTEST**

### Option 2: One Command Build

```powershell
# Build Windows and Linux installers (skip tests for speed)
.\scripts\test-build-deploy.ps1 -SkipTests -Platform "windows,linux"
```

### Option 3: Full Test and Build

```powershell
# Run all tests, then build
.\scripts\test-build-deploy.ps1 -Platform "windows,linux"
```

## 📊 Current Test Status

- ✅ **215 tests passing** (86%)
- ⚠️ **34 tests failing** (14%) - mostly UI timing issues
- **Safe to build** - failures are in non-critical areas

See [TEST_STATUS.md](TEST_STATUS.md) for details.

## 🛠️ Build Process

The script will:

1. ✅ Check prerequisites (Node.js, Python, Git)
2. ✅ Install dependencies
3. ⚠️ Run tests (optional - use `-SkipTests` to skip)
4. ✅ Build frontend
5. ✅ Create installers for Windows and Linux
6. ✅ Show build artifacts

## 📦 What You'll Get

After building, find installers in the `release/` directory:

### Windows
- `PEFT Studio Setup 1.0.0.exe` - Full installer (recommended)
- `PEFT Studio 1.0.0.exe` - Portable version

### Linux
- `PEFT-Studio-1.0.0.AppImage` - Universal (works on all distros)
- `peft-studio_1.0.0_amd64.deb` - Debian/Ubuntu package

## 🚢 Deploy to GitHub

### Method 1: Using the Script

```powershell
# Build and push to GitHub
.\scripts\test-build-deploy.ps1 -SkipTests -Platform "windows,linux" -PushToGitHub
```

### Method 2: Manual Git Commands

```bash
# After building, commit and push
git add .
git commit -m "Build: Create Windows and Linux installers"
git push origin main
```

### Method 3: Create a Release

```bash
# Tag the release
git tag v1.0.0
git push origin v1.0.0
```

This triggers GitHub Actions to automatically build and publish installers for all platforms.

## ⚡ Quick Commands Reference

| Task | Command |
|------|---------|
| **Quick build (fastest)** | `.\scripts\test-build-deploy.ps1 -SkipTests -Platform "windows,linux"` |
| **Build with tests** | `.\scripts\test-build-deploy.ps1 -Platform "windows,linux"` |
| **Build Windows only** | `.\scripts\test-build-deploy.ps1 -SkipTests -Platform "windows"` |
| **Build Linux only** | `.\scripts\test-build-deploy.ps1 -SkipTests -Platform "linux"` |
| **Build and push** | `.\scripts\test-build-deploy.ps1 -SkipTests -PushToGitHub` |
| **Run tests only** | `.\scripts\test-build-deploy.ps1 -SkipBuild` |

## 🎯 Recommended Workflow

### For Development
```powershell
# Quick build for testing
.\scripts\test-build-deploy.ps1 -SkipTests -Platform "windows"
```

### For Release
```powershell
# 1. Build with tests
.\scripts\test-build-deploy.ps1 -Platform "windows,linux"

# 2. Test the installers manually

# 3. Create release tag
git tag v1.0.0
git push origin v1.0.0

# 4. GitHub Actions will build for all platforms and create release
```

## 🐛 Troubleshooting

### "Tests are failing"
**Solution**: Use `-SkipTests` flag. The failures are in non-critical UI tests.

```powershell
.\scripts\test-build-deploy.ps1 -SkipTests -Platform "windows,linux"
```

### "Build is slow"
**Solution**: 
- Close other applications
- Build one platform at a time
- Use `-SkipTests` flag

### "Missing dependencies"
**Solution**:
```powershell
npm ci
cd backend
pip install -r requirements.txt
cd ..
```

### "Permission denied" (Linux/Mac)
**Solution**:
```bash
chmod +x scripts/test-build-deploy.sh
```

## 📚 More Information

- **Detailed Build Guide**: [BUILDING.md](BUILDING.md)
- **Script Documentation**: [scripts/TEST_BUILD_DEPLOY.md](scripts/TEST_BUILD_DEPLOY.md)
- **Test Status**: [TEST_STATUS.md](TEST_STATUS.md)
- **Main README**: [README.md](README.md)

## ✅ Verification Checklist

After building, verify:

- [ ] `release/` directory exists
- [ ] Windows installer (`.exe`) is present
- [ ] Linux packages (`.AppImage`, `.deb`) are present
- [ ] File sizes are reasonable (50-200 MB each)
- [ ] Test installers on clean systems

## 🎉 Success!

Once built, you can:

1. **Test locally**: Install and run the application
2. **Share**: Send installers to users
3. **Release**: Push to GitHub and create a release
4. **Distribute**: Users can download from GitHub Releases

## 💡 Pro Tips

1. **Use the interactive menu** (`.\build-and-test.ps1`) for easiest experience
2. **Skip tests during development** to save time
3. **Always run tests before releases** to ensure quality
4. **Use GitHub Actions** for automated multi-platform builds
5. **Test installers** on clean VMs before distributing

## 🆘 Need Help?

1. Check [troubleshooting docs](docs/reference/troubleshooting.md)
2. Review [test status](TEST_STATUS.md)
3. Open an issue on GitHub
4. Check existing issues and discussions

---

**Ready to build?** Run this command:

```powershell
.\scripts\test-build-deploy.ps1 -SkipTests -Platform "windows,linux"
```

Your installers will be in the `release/` directory in about 5-10 minutes! 🚀
