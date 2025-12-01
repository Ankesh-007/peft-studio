# Auto-Update Quick Start Guide

## 🚀 Quick Setup (5 Minutes)

### Step 1: Configure GitHub Repository

Edit `package.json`:

```json
{
  "build": {
    "publish": {
      "provider": "github",
      "owner": "YOUR_GITHUB_USERNAME",
      "repo": "peft-studio"
    }
  }
}
```

Replace `YOUR_GITHUB_USERNAME` with your actual GitHub username.

### Step 2: Build Your Application

```bash
npm run build
npm run electron:build
```

This creates installers in the `release/` directory.

### Step 3: Create GitHub Release

1. Go to your GitHub repository
2. Click "Releases" → "Create a new release"
3. Tag version: `v1.0.0` (must start with 'v')
4. Release title: `Version 1.0.0`
5. Add release notes describing changes
6. Upload the build artifacts from `release/`:
   - Windows: `PEFT-Studio-Setup-1.0.0.exe`
   - macOS: `PEFT-Studio-1.0.0.dmg`
   - Linux: `PEFT-Studio-1.0.0.AppImage`
7. Click "Publish release"

### Step 4: Test Updates

1. Install version 1.0.0 on a test machine
2. Create a new release (v1.0.1) with updated artifacts
3. Launch the app
4. Wait 3 seconds - update notification should appear
5. Click "Download Update"
6. Click "Install and Restart"
7. Verify app restarts with version 1.0.1

## 🎯 How It Works

```
User launches app
    ↓
App checks GitHub for new releases (after 3s)
    ↓
New version found?
    ↓ YES
Shows notification with version info
    ↓
User clicks "Download Update"
    ↓
Downloads in background (shows progress)
    ↓
Download complete
    ↓
User clicks "Install and Restart"
    ↓
App quits, installs update, and restarts
```

## 📋 Release Checklist

Before creating a new release:

- [ ] Update version in `package.json`
- [ ] Build application: `npm run electron:build`
- [ ] Test build locally
- [ ] Create Git tag: `git tag v1.0.1`
- [ ] Push tag: `git push origin v1.0.1`
- [ ] Create GitHub release
- [ ] Upload all platform artifacts
- [ ] Write clear release notes
- [ ] Publish release
- [ ] Test update on each platform

## 🔧 Troubleshooting

### Update Check Fails

**Problem**: "Error checking for updates"

**Fix**: 
1. Check internet connection
2. Verify GitHub repository is public
3. Check `package.json` configuration

### No Update Notification

**Problem**: App doesn't show update notification

**Fix**:
1. Wait at least 3 seconds after launch
2. Check console for errors (Ctrl+Shift+I)
3. Verify GitHub release is published
4. Ensure version number is higher than current

### Download Fails

**Problem**: Download starts but fails

**Fix**:
1. Check available disk space
2. Verify network stability
3. Check firewall settings

## 💡 Tips

1. **Version Numbering**: Always use semantic versioning (MAJOR.MINOR.PATCH)
2. **Release Notes**: Write user-friendly descriptions of changes
3. **Testing**: Test on all platforms before releasing
4. **Timing**: Release during off-peak hours
5. **Communication**: Notify users of breaking changes

## 🔐 Security Notes

- Updates are downloaded over HTTPS only
- Signatures are verified automatically
- Only downloads from your configured GitHub repository
- Checksums validated before installation

## 📱 User Experience

Users will see a notification like this:

```
┌─────────────────────────────────────┐
│ 📥 Update Available            ✕    │
├─────────────────────────────────────┤
│ Version 1.0.1 is available          │
│ Current version: 1.0.0              │
│                                     │
│ [Show Release Notes]                │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │    Download Update              │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

## 🎓 Learn More

- Full documentation: `AUTO_UPDATE_SYSTEM.md`
- Implementation details: `AUTO_UPDATE_IMPLEMENTATION_SUMMARY.md`
- electron-updater docs: https://www.electron.build/auto-update

---

**Need Help?** Check the troubleshooting section in `AUTO_UPDATE_SYSTEM.md`
