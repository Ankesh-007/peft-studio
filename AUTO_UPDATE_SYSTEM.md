# Auto-Update System Implementation

## Overview

The auto-update system provides seamless application updates using `electron-updater`. It checks for updates on startup, downloads them in the background, and allows users to install updates with a single click.

## Features

### 1. Automatic Update Checking
- Checks for updates 3 seconds after application startup
- Skips update checks in development mode
- Provides manual "Check for Updates" button

### 2. Background Download
- Downloads updates in the background without blocking the UI
- Shows real-time download progress with speed and size information
- Allows users to continue working while downloading

### 3. Update Notification UI
- Non-intrusive notification in the bottom-right corner
- Shows update status with appropriate icons and colors
- Displays release notes for new versions
- Progress bar for download status

### 4. Release Notes Display
- Fetches and displays release notes from GitHub releases
- Collapsible release notes section
- Formatted display of changes and improvements

### 5. Install and Restart
- One-click installation after download completes
- Automatically quits and installs the update
- Preserves user data and settings

## Architecture

### Main Process (electron/main.js)

```javascript
// Auto-updater configuration
autoUpdater.autoDownload = false; // Manual download after user confirmation
autoUpdater.autoInstallOnAppQuit = true; // Install on quit

// Event handlers
autoUpdater.on('checking-for-update', ...)
autoUpdater.on('update-available', ...)
autoUpdater.on('update-not-available', ...)
autoUpdater.on('error', ...)
autoUpdater.on('download-progress', ...)
autoUpdater.on('update-downloaded', ...)
```

### IPC Communication

**Main → Renderer:**
- `update-available`: New version available
- `update-download-progress`: Download progress updates
- `update-downloaded`: Download complete
- `update-status`: General status updates

**Renderer → Main:**
- `check-for-updates`: Manually check for updates
- `download-update`: Start downloading update
- `install-update`: Install and restart
- `get-app-version`: Get current version

### React Component (UpdateNotification.tsx)

The component manages the entire update UI lifecycle:

1. **Checking State**: Shows spinner while checking
2. **Available State**: Shows version info and download button
3. **Downloading State**: Shows progress bar and speed
4. **Downloaded State**: Shows install button
5. **Error State**: Shows error message and retry button
6. **Not Available State**: Shows "up to date" message

## Configuration

### package.json

```json
{
  "build": {
    "publish": {
      "provider": "github",
      "owner": "your-github-username",
      "repo": "peft-studio"
    }
  }
}
```

### GitHub Releases

1. Create a new release on GitHub
2. Tag the release with version number (e.g., `v1.0.1`)
3. Upload build artifacts (`.exe`, `.dmg`, `.AppImage`)
4. Add release notes in the description
5. Publish the release

The auto-updater will automatically detect new releases and download the appropriate artifact for the user's platform.

## Update Flow

```
App Startup
    ↓
Wait 3 seconds
    ↓
Check for Updates (autoUpdater.checkForUpdates())
    ↓
┌─────────────────┐
│ Update Found?   │
└─────────────────┘
    ↓ Yes              ↓ No
Show Notification   Show "Up to Date"
    ↓
User Clicks "Download"
    ↓
Download in Background
    ↓
Show Progress Bar
    ↓
Download Complete
    ↓
Show "Install and Restart"
    ↓
User Clicks Install
    ↓
Quit and Install
    ↓
App Restarts with New Version
```

## User Experience

### Update Available
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

### Downloading
```
┌─────────────────────────────────────┐
│ ⟳ Downloading Update           ✕    │
├─────────────────────────────────────┤
│ 45%                    2.5 MB/s     │
│ ████████████░░░░░░░░░░░░░░░         │
│ 45 MB                      100 MB   │
└─────────────────────────────────────┘
```

### Ready to Install
```
┌─────────────────────────────────────┐
│ ✓ Update Ready                 ✕    │
├─────────────────────────────────────┤
│ Version 1.0.1 has been downloaded   │
│ and is ready to install.            │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │    Install and Restart          │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

## Security

### Code Signing

**Windows:**
```bash
# Sign the executable
electron-builder --win --publish never
```

**macOS:**
```bash
# Sign and notarize
electron-builder --mac --publish never
```

### Update Verification

- electron-updater verifies signatures automatically
- Only downloads from configured GitHub repository
- Uses HTTPS for all communications
- Validates checksums before installation

## Testing

### Development Testing

```bash
# Set environment variable to test updates
export GH_TOKEN=your_github_token

# Build and publish to GitHub
npm run electron:build -- --publish always
```

### Manual Testing

1. Build version 1.0.0
2. Install on test machine
3. Create GitHub release for 1.0.1
4. Launch app and verify update notification
5. Download and install update
6. Verify app restarts with new version

### Automated Testing

```typescript
// Test update notification component
describe('UpdateNotification', () => {
  it('should show update available notification', () => {
    // Mock window.api.onUpdateAvailable
    // Trigger update available event
    // Verify notification is displayed
  });

  it('should download update when button clicked', () => {
    // Mock window.api.downloadUpdate
    // Click download button
    // Verify download started
  });

  it('should show progress during download', () => {
    // Mock window.api.onUpdateDownloadProgress
    // Trigger progress events
    // Verify progress bar updates
  });
});
```

## Troubleshooting

### Update Check Fails

**Problem:** "Error checking for updates"

**Solutions:**
1. Check internet connection
2. Verify GitHub repository is public
3. Check `package.json` publish configuration
4. Verify GitHub token (if using private repo)

### Download Fails

**Problem:** Download starts but fails midway

**Solutions:**
1. Check available disk space
2. Verify network stability
3. Check firewall settings
4. Try manual download from GitHub releases

### Installation Fails

**Problem:** "Failed to install update"

**Solutions:**
1. Close all app instances
2. Run as administrator (Windows)
3. Check file permissions
4. Verify antivirus isn't blocking

## Best Practices

1. **Version Numbering**: Use semantic versioning (MAJOR.MINOR.PATCH)
2. **Release Notes**: Always include clear, user-friendly release notes
3. **Testing**: Test updates on all platforms before releasing
4. **Rollback**: Keep previous versions available for rollback
5. **Communication**: Notify users of breaking changes
6. **Timing**: Release updates during off-peak hours
7. **Monitoring**: Track update adoption rates

## Future Enhancements

1. **Delta Updates**: Download only changed files
2. **Staged Rollout**: Release to percentage of users first
3. **Update Scheduling**: Allow users to schedule updates
4. **Automatic Installation**: Option for automatic updates
5. **Update History**: Show history of installed updates
6. **Rollback**: Allow users to rollback to previous version
7. **Beta Channel**: Opt-in to beta updates

## References

- [electron-updater Documentation](https://www.electron.build/auto-update)
- [GitHub Releases API](https://docs.github.com/en/rest/releases)
- [Code Signing Guide](https://www.electron.build/code-signing)
- [Electron Security Best Practices](https://www.electronjs.org/docs/latest/tutorial/security)
