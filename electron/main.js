const { app, BrowserWindow, Notification, ipcMain, dialog } = require('electron');
const { autoUpdater } = require('electron-updater');
const path = require('path');
const log = require('electron-log');

let mainWindow;
let pythonProcess;

// Configure logging
log.transports.file.level = 'info';
autoUpdater.logger = log;

// Configure auto-updater
autoUpdater.autoDownload = false; // We'll download manually after user confirmation
autoUpdater.autoInstallOnAppQuit = true;

// Set update feed URL (GitHub releases)
if (process.env.NODE_ENV !== 'development') {
  autoUpdater.setFeedURL({
    provider: 'github',
    owner: 'Ankesh-007',
    repo: 'peft-studio'
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  // Load the app
  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Start Python backend
function startPythonBackend() {
  const { spawn } = require('child_process');
  const pythonPath = path.join(__dirname, '../backend/main.py');
  
  pythonProcess = spawn('python', [pythonPath]);
  
  pythonProcess.stdout.on('data', (data) => {
    console.log(`Python: ${data}`);
  });
  
  pythonProcess.stderr.on('data', (data) => {
    console.error(`Python Error: ${data}`);
  });
  
  pythonProcess.on('close', (code) => {
    console.log(`Python process exited with code ${code}`);
  });
}

// Auto-updater functions
function checkForUpdates() {
  if (process.env.NODE_ENV === 'development') {
    log.info('Skipping update check in development mode');
    return;
  }
  
  log.info('Checking for updates...');
  autoUpdater.checkForUpdates().catch(err => {
    log.error('Error checking for updates:', err);
    sendUpdateStatus('error', { message: err.message });
  });
}

// Auto-updater event handlers
autoUpdater.on('checking-for-update', () => {
  log.info('Checking for updates...');
  sendUpdateStatus('checking');
});

autoUpdater.on('update-available', (info) => {
  log.info('Update available:', {
    version: info.version,
    releaseDate: info.releaseDate,
    files: info.files?.map(f => ({ url: f.url, size: f.size }))
  });
  sendUpdateStatus('available', info);
  
  // Show notification to user
  if (mainWindow) {
    mainWindow.webContents.send('update-available', {
      version: info.version,
      releaseNotes: info.releaseNotes,
      releaseDate: info.releaseDate
    });
  }
});

autoUpdater.on('update-not-available', (info) => {
  log.info('Update not available. Current version is up to date:', info.version);
  sendUpdateStatus('not-available', info);
});

autoUpdater.on('error', (err) => {
  log.error('Update error:', err);
  
  // Handle different types of errors
  let errorMessage = err.message;
  let errorType = 'general';
  
  if (err.message.includes('ENOTFOUND') || err.message.includes('ETIMEDOUT')) {
    errorMessage = 'Network error: Unable to check for updates. Please check your internet connection.';
    errorType = 'network';
  } else if (err.message.includes('404')) {
    errorMessage = 'Update server not found. Please try again later.';
    errorType = 'not-found';
  } else if (err.message.includes('sha512') || err.message.includes('checksum') || err.message.includes('integrity')) {
    // Checksum verification failure
    errorMessage = '⚠️ Update integrity verification failed. The downloaded update file may be corrupted or tampered with. For your security, the update will not be installed. Please try again later or download manually from GitHub.';
    errorType = 'checksum-mismatch';
    log.error('❌ CHECKSUM VERIFICATION FAILED - Update rejected for security');
    
    // Show critical notification to user
    if (mainWindow) {
      mainWindow.webContents.send('update-checksum-failed', {
        message: errorMessage,
        severity: 'critical'
      });
    }
  }
  
  sendUpdateStatus('error', { 
    message: errorMessage,
    type: errorType,
    originalError: err.message
  });
});

autoUpdater.on('download-progress', (progressObj) => {
  log.info(`Download progress: ${progressObj.percent.toFixed(2)}% (${progressObj.bytesPerSecond} bytes/sec)`);
  sendUpdateStatus('downloading', {
    percent: progressObj.percent,
    bytesPerSecond: progressObj.bytesPerSecond,
    transferred: progressObj.transferred,
    total: progressObj.total
  });
  
  if (mainWindow) {
    mainWindow.webContents.send('update-download-progress', progressObj);
  }
});

autoUpdater.on('update-downloaded', (info) => {
  log.info('Update downloaded successfully:', {
    version: info.version,
    files: info.files?.map(f => ({ url: f.url, sha512: f.sha512 }))
  });
  
  // electron-updater automatically verifies checksums during download
  // The update will only reach this point if integrity verification passed
  // electron-updater uses SHA512 for verification (more secure than SHA256)
  log.info('✅ Update integrity verified via SHA512 checksum');
  log.info('Checksum verification details:', {
    verified: true,
    algorithm: 'SHA512',
    files: info.files?.map(f => ({
      name: f.url.split('/').pop(),
      checksumVerified: true
    }))
  });
  
  sendUpdateStatus('downloaded', info);
  
  // Show notification that update is ready to install
  if (mainWindow) {
    mainWindow.webContents.send('update-downloaded', {
      version: info.version,
      releaseNotes: info.releaseNotes,
      checksumVerified: true
    });
  }
});

function sendUpdateStatus(status, data = {}) {
  if (mainWindow && mainWindow.webContents) {
    mainWindow.webContents.send('update-status', { status, ...data });
  }
}

app.whenReady().then(() => {
  createWindow();
  startPythonBackend();
  
  // Check for updates after a short delay to let the app initialize
  setTimeout(() => {
    checkForUpdates();
  }, 3000);

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('quit', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
});

// Desktop notification support
ipcMain.handle('show-notification', async (event, options) => {
  try {
    const notification = new Notification({
      title: options.title || 'PEFT Studio',
      body: options.message || '',
      silent: !options.sound,
      urgency: options.urgency || 'normal', // low, normal, critical
      timeoutType: options.urgency === 'critical' ? 'never' : 'default'
    });
    
    // Handle notification click
    if (options.actions && options.actions.length > 0) {
      notification.on('click', () => {
        if (mainWindow) {
          mainWindow.show();
          mainWindow.focus();
        }
      });
    }
    
    notification.show();
    return { success: true };
  } catch (error) {
    console.error('Error showing notification:', error);
    return { success: false, error: error.message };
  }
});

// Taskbar progress support
ipcMain.handle('set-progress', async (event, progress) => {
  try {
    if (mainWindow) {
      // progress should be between 0 and 1
      if (progress < 0 || progress > 1) {
        progress = Math.max(0, Math.min(1, progress));
      }
      
      if (progress >= 1) {
        // Training complete - flash the taskbar
        mainWindow.setProgressBar(1, { mode: 'none' });
        mainWindow.flashFrame(true);
        setTimeout(() => {
          mainWindow.flashFrame(false);
          mainWindow.setProgressBar(-1); // Remove progress bar
        }, 3000);
      } else if (progress > 0) {
        mainWindow.setProgressBar(progress);
      } else {
        mainWindow.setProgressBar(-1); // Remove progress bar
      }
    }
    return { success: true };
  } catch (error) {
    console.error('Error setting progress:', error);
    return { success: false, error: error.message };
  }
});

// Check Do Not Disturb status
ipcMain.handle('check-dnd', async () => {
  try {
    // Electron doesn't have direct DND detection, but we can check system preferences
    // This is a placeholder - actual implementation would need native modules
    return { enabled: false };
  } catch (error) {
    console.error('Error checking DND:', error);
    return { enabled: false };
  }
});

// Auto-update IPC handlers
ipcMain.handle('check-for-updates', async () => {
  try {
    if (process.env.NODE_ENV === 'development') {
      log.info('Updates disabled in development mode');
      return { success: false, message: 'Updates disabled in development mode' };
    }
    
    log.info('Manual update check requested');
    const result = await autoUpdater.checkForUpdates();
    log.info('Update check result:', result.updateInfo);
    
    return { success: true, updateInfo: result.updateInfo };
  } catch (error) {
    log.error('Error checking for updates:', error);
    
    // Handle network errors gracefully
    let errorMessage = error.message;
    if (error.message.includes('ENOTFOUND') || error.message.includes('ETIMEDOUT')) {
      errorMessage = 'Network error: Unable to check for updates. Please check your internet connection.';
    }
    
    return { success: false, error: errorMessage };
  }
});

ipcMain.handle('download-update', async () => {
  try {
    if (process.env.NODE_ENV === 'development') {
      log.info('Updates disabled in development mode');
      return { success: false, message: 'Updates disabled in development mode' };
    }
    
    log.info('Starting update download');
    await autoUpdater.downloadUpdate();
    log.info('Update download initiated successfully');
    
    return { success: true };
  } catch (error) {
    log.error('Error downloading update:', error);
    
    // Handle network errors gracefully
    let errorMessage = error.message;
    if (error.message.includes('ENOTFOUND') || error.message.includes('ETIMEDOUT')) {
      errorMessage = 'Network error: Unable to download update. Please check your internet connection.';
    }
    
    return { success: false, error: errorMessage };
  }
});

ipcMain.handle('install-update', async () => {
  try {
    if (process.env.NODE_ENV === 'development') {
      log.info('Updates disabled in development mode');
      return { success: false, message: 'Updates disabled in development mode' };
    }
    
    log.info('Installing update and restarting application');
    // This will quit the app and install the update
    // false = don't force run after finish, true = restart after install
    autoUpdater.quitAndInstall(false, true);
    
    return { success: true };
  } catch (error) {
    log.error('Error installing update:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('get-app-version', async () => {
  const version = app.getVersion();
  log.info('App version requested:', version);
  return { version };
});
