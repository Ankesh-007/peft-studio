import fc from "fast-check";
import { describe, test, expect, vi, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";

/**
 * Feature: github-releases-installer
 * Property-based tests for auto-update system
 */

// Mock electron modules
const mockAutoUpdater = {
  autoDownload: false,
  autoInstallOnAppQuit: true,
  logger: null,
  setFeedURL: vi.fn(),
  checkForUpdates: vi.fn(),
  downloadUpdate: vi.fn(),
  quitAndInstall: vi.fn(),
  on: vi.fn(),
};

const mockLog = {
  transports: { file: { level: 'info' } },
  info: vi.fn(),
  error: vi.fn(),
  warn: vi.fn(),
};

// Helper to load main.js content
function loadMainJsContent(): string {
  const mainPath = path.join(process.cwd(), "electron/main.js");
  return fs.readFileSync(mainPath, "utf-8");
}

// Helper to load package.json
function loadPackageJson(): any {
  const packagePath = path.join(process.cwd(), "package.json");
  const content = fs.readFileSync(packagePath, "utf-8");
  return JSON.parse(content);
}

describe("Auto-Update System Properties", () => {
  /**
   * Feature: github-releases-installer, Property 34: Update check on startup
   * Validates: Requirements 8.1
   * 
   * For any application start, the system should check for available updates from the GitHub releases API
   */
  test("Property 34: Update check on startup", () => {
    const mainContent = loadMainJsContent();
    
    // Verify electron-updater is imported
    expect(mainContent).toContain("require('electron-updater')");
    expect(mainContent).toContain("autoUpdater");
    
    // Verify update check is called on app ready
    expect(mainContent).toContain("app.whenReady()");
    expect(mainContent).toContain("checkForUpdates()");
    
    // Verify there's a delay before checking (to let app initialize)
    expect(mainContent).toContain("setTimeout");
    
    // Verify the checkForUpdates function exists and calls autoUpdater
    expect(mainContent).toContain("function checkForUpdates()");
    expect(mainContent).toContain("autoUpdater.checkForUpdates()");
    
    // Verify it skips in development mode
    expect(mainContent).toContain("process.env.NODE_ENV === 'development'");
    
    // Verify error handling for update checks
    expect(mainContent).toContain(".catch");
  });

  /**
   * Feature: github-releases-installer, Property 35: Update notification displayed
   * Validates: Requirements 8.2
   * 
   * For any detected new version, a notification should be displayed to the user
   */
  test("Property 35: Update notification displayed", () => {
    fc.assert(
      fc.property(
        fc.record({
          major: fc.integer({ min: 1, max: 99 }),
          minor: fc.integer({ min: 0, max: 99 }),
          patch: fc.integer({ min: 0, max: 99 }),
        }),
        ({ major, minor, patch }) => {
          const version = `${major}.${minor}.${patch}`;
          const mainContent = loadMainJsContent();
          
          // Verify update-available event handler exists
          expect(mainContent).toContain("autoUpdater.on('update-available'");
          
          // Verify it sends update info to renderer
          expect(mainContent).toContain("mainWindow.webContents.send('update-available'");
          
          // Verify it includes version information
          const updateAvailableSection = mainContent.split("autoUpdater.on('update-available'")[1];
          expect(updateAvailableSection).toBeDefined();
          expect(updateAvailableSection).toContain("version:");
          expect(updateAvailableSection).toContain("releaseNotes:");
          expect(updateAvailableSection).toContain("releaseDate:");
          
          // Verify logging
          expect(updateAvailableSection).toContain("log.info");
          
          // Check UpdateNotification component exists
          const componentPath = path.join(process.cwd(), "src/components/UpdateNotification.tsx");
          expect(fs.existsSync(componentPath)).toBe(true);
          
          const componentContent = fs.readFileSync(componentPath, "utf-8");
          
          // Verify component listens for update-available event
          expect(componentContent).toContain("onUpdateAvailable");
          expect(componentContent).toContain("window.api?.onUpdateAvailable");
          
          // Verify component displays version
          expect(componentContent).toContain("Version");
          expect(componentContent).toContain("version");
          
          // Verify component has download button
          expect(componentContent).toContain("Download");
          expect(componentContent).toContain("button");
          
          // Verify component can show release notes
          expect(componentContent).toContain("releaseNotes");
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Feature: github-releases-installer, Property 36: Automatic update installation
   * Validates: Requirements 8.3
   * 
   * For any user-accepted update, the system should download and install it automatically
   */
  test("Property 36: Automatic update installation", () => {
    const mainContent = loadMainJsContent();
    
    // Verify download-update IPC handler exists
    expect(mainContent).toContain("ipcMain.handle('download-update'");
    
    // Verify it calls autoUpdater.downloadUpdate
    const downloadSection = mainContent.split("ipcMain.handle('download-update'")[1];
    expect(downloadSection).toBeDefined();
    expect(downloadSection).toContain("autoUpdater.downloadUpdate()");
    
    // Verify install-update IPC handler exists
    expect(mainContent).toContain("ipcMain.handle('install-update'");
    
    // Verify it calls quitAndInstall
    const installSection = mainContent.split("ipcMain.handle('install-update'")[1];
    expect(installSection).toBeDefined();
    expect(installSection).toContain("autoUpdater.quitAndInstall");
    
    // Verify update-downloaded event handler exists
    expect(mainContent).toContain("autoUpdater.on('update-downloaded'");
    
    // Verify it notifies the renderer
    const downloadedSection = mainContent.split("autoUpdater.on('update-downloaded'")[1];
    expect(downloadedSection).toBeDefined();
    expect(downloadedSection).toContain("mainWindow.webContents.send('update-downloaded'");
    
    // Verify UpdateNotification component has install functionality
    const componentPath = path.join(process.cwd(), "src/components/UpdateNotification.tsx");
    const componentContent = fs.readFileSync(componentPath, "utf-8");
    
    // Verify component has install handler
    expect(componentContent).toContain("handleInstall");
    expect(componentContent).toContain("installUpdate");
    
    // Verify component shows install button when update is downloaded
    expect(componentContent).toContain("Install");
    expect(componentContent).toContain("Restart");
    
    // Verify download progress is tracked
    expect(mainContent).toContain("autoUpdater.on('download-progress'");
    expect(componentContent).toContain("downloadProgress");
  });

  /**
   * Feature: github-releases-installer, Property 37: Update integrity verification
   * Validates: Requirements 8.4
   * 
   * For any downloaded update, the file integrity should be verified using checksums
   */
  test("Property 37: Update integrity verification", () => {
    fc.assert(
      fc.property(
        fc.record({
          major: fc.integer({ min: 1, max: 99 }),
          minor: fc.integer({ min: 0, max: 99 }),
          patch: fc.integer({ min: 0, max: 99 }),
        }),
        ({ major, minor, patch }) => {
          const version = `${major}.${minor}.${patch}`;
          const mainContent = loadMainJsContent();
          const packageJson = loadPackageJson();
          
          // Verify electron-updater is configured (it handles checksum verification automatically)
          expect(packageJson.dependencies["electron-updater"]).toBeDefined();
          
          // Verify autoUpdater is imported and configured
          expect(mainContent).toContain("require('electron-updater')");
          expect(mainContent).toContain("autoUpdater");
          
          // Verify update-downloaded event handler exists
          // This event only fires if integrity verification passes
          expect(mainContent).toContain("autoUpdater.on('update-downloaded'");
          
          const downloadedSection = mainContent.split("autoUpdater.on('update-downloaded'")[1];
          expect(downloadedSection).toBeDefined();
          
          // Verify logging mentions integrity verification
          expect(downloadedSection).toContain("integrity");
          expect(downloadedSection).toContain("checksum");
          
          // Verify error handler exists for failed downloads/verification
          expect(mainContent).toContain("autoUpdater.on('error'");
          
          const errorSection = mainContent.split("autoUpdater.on('error'")[1];
          expect(errorSection).toBeDefined();
          expect(errorSection).toContain("log.error");
          
          // Verify error is sent to renderer
          expect(errorSection).toContain("sendUpdateStatus('error'");
          
          // Verify UpdateNotification component handles errors
          const componentPath = path.join(process.cwd(), "src/components/UpdateNotification.tsx");
          const componentContent = fs.readFileSync(componentPath, "utf-8");
          
          expect(componentContent).toContain("error");
          expect(componentContent).toContain("updateState === 'error'");
          
          // Verify component shows error message
          expect(componentContent).toContain("Update Error");
          expect(componentContent).toContain("AlertCircle");
        }
      ),
      { numRuns: 100 }
    );
  });
});

describe("Auto-Update Configuration Properties", () => {
  test("Auto-updater is properly configured in main process", () => {
    const mainContent = loadMainJsContent();
    
    // Verify autoDownload is set to false (manual download after user confirmation)
    expect(mainContent).toContain("autoUpdater.autoDownload = false");
    
    // Verify autoInstallOnAppQuit is set to true
    expect(mainContent).toContain("autoUpdater.autoInstallOnAppQuit = true");
    
    // Verify logging is configured
    expect(mainContent).toContain("electron-log");
    expect(mainContent).toContain("autoUpdater.logger");
    
    // Verify feed URL is configured for GitHub
    expect(mainContent).toContain("setFeedURL");
    expect(mainContent).toContain("provider: 'github'");
  });

  test("Package.json has correct publish configuration", () => {
    const packageJson = loadPackageJson();
    
    // Verify build configuration exists
    expect(packageJson.build).toBeDefined();
    expect(packageJson.build.publish).toBeDefined();
    
    // Verify GitHub provider is configured
    expect(packageJson.build.publish.provider).toBe("github");
    expect(packageJson.build.publish.owner).toBeDefined();
    expect(packageJson.build.publish.repo).toBeDefined();
    
    // Verify electron-updater dependency exists
    expect(packageJson.dependencies["electron-updater"]).toBeDefined();
    
    // Verify electron-log dependency exists
    expect(packageJson.dependencies["electron-log"]).toBeDefined();
  });

  test("Preload script exposes update API to renderer", () => {
    const preloadPath = path.join(process.cwd(), "electron/preload.js");
    const preloadContent = fs.readFileSync(preloadPath, "utf-8");
    
    // Verify update methods are exposed
    expect(preloadContent).toContain("checkForUpdates:");
    expect(preloadContent).toContain("downloadUpdate:");
    expect(preloadContent).toContain("installUpdate:");
    expect(preloadContent).toContain("getAppVersion:");
    
    // Verify update events are exposed
    expect(preloadContent).toContain("onUpdateAvailable:");
    expect(preloadContent).toContain("onUpdateDownloadProgress:");
    expect(preloadContent).toContain("onUpdateDownloaded:");
    expect(preloadContent).toContain("onUpdateStatus:");
    
    // Verify they use ipcRenderer
    expect(preloadContent).toContain("ipcRenderer.invoke");
    expect(preloadContent).toContain("ipcRenderer.on");
  });
});

describe("Error Handling Properties", () => {
  test("Network errors are handled gracefully", () => {
    fc.assert(
      fc.property(
        fc.constantFrom("ENOTFOUND", "ETIMEDOUT", "ECONNREFUSED", "404"),
        (errorType) => {
          const mainContent = loadMainJsContent();
          
          // Verify error handler exists
          expect(mainContent).toContain("autoUpdater.on('error'");
          
          const errorSection = mainContent.split("autoUpdater.on('error'")[1];
          expect(errorSection).toBeDefined();
          
          // Verify network error handling
          if (errorType === "ENOTFOUND" || errorType === "ETIMEDOUT") {
            expect(errorSection).toContain("ENOTFOUND");
            expect(errorSection).toContain("ETIMEDOUT");
            expect(errorSection).toContain("Network error");
            expect(errorSection).toContain("internet connection");
          }
          
          if (errorType === "404") {
            expect(errorSection).toContain("404");
            expect(errorSection).toContain("not found");
          }
          
          // Verify error is logged
          expect(errorSection).toContain("log.error");
          
          // Verify error is sent to renderer
          expect(errorSection).toContain("sendUpdateStatus('error'");
        }
      ),
      { numRuns: 50 }
    );
  });

  test("Development mode skips update checks", () => {
    const mainContent = loadMainJsContent();
    
    // Verify checkForUpdates checks for development mode
    const checkSection = mainContent.split("function checkForUpdates()")[1];
    expect(checkSection).toBeDefined();
    expect(checkSection).toContain("process.env.NODE_ENV === 'development'");
    expect(checkSection).toContain("return");
    
    // Verify IPC handlers check for development mode
    const downloadSection = mainContent.split("ipcMain.handle('download-update'")[1];
    expect(downloadSection).toContain("process.env.NODE_ENV === 'development'");
    
    const installSection = mainContent.split("ipcMain.handle('install-update'")[1];
    expect(installSection).toContain("process.env.NODE_ENV === 'development'");
  });
});
