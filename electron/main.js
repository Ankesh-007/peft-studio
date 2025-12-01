const { app, BrowserWindow, Notification, ipcMain, dialog } = require('electron');
const { autoUpdater } = require('electron-updater');
const path = require('path');

let mainWindow;
let pythonProcess;

// Configure auto-updater
autoUpdater.autoDownload = false; // We'll download manually after user confirmation
autoUpdater.autoInstallOnAppQuit = true;

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
    console.log('Skipping update check in development mode');
    return;
  }
  
  autoUpdater.checkForUpdates().catch(err => {
    console.error('Error checking for updates:', err);
  });
}

// Auto-updater event handlers
autoUpdater.on('checking-for-update', () => {
  console.log('Checking for updates...');
  sendUpdateStatus('checking');
});

autoUpdater.on('update-available', (info) => {
  console.log('Update available:', info);
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
  console.log('Update not available:', info);
  sendUpdateStatus('not-available', info);
});

autoUpdater.on('error', (err) => {
  console.error('Update error:', err);
  sendUpdateStatus('error', { message: err.message });
});

autoUpdater.on('download-progress', (progressObj) => {
  console.log(`Download progress: ${progressObj.percent}%`);
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
  console.log('Update downloaded:', info);
  sendUpdateStatus('downloaded', info);
  
  // Show notification that update is ready to install
  if (mainWindow) {
    mainWindow.webContents.send('update-downloaded', {
      version: info.version,
      releaseNotes: info.releaseNotes
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
      return { success: false, message: 'Updates disabled in development mode' };
    }
    const result = await autoUpdater.checkForUpdates();
    return { success: true, updateInfo: result.updateInfo };
  } catch (error) {
    console.error('Error checking for updates:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('download-update', async () => {
  try {
    if (process.env.NODE_ENV === 'development') {
      return { success: false, message: 'Updates disabled in development mode' };
    }
    await autoUpdater.downloadUpdate();
    return { success: true };
  } catch (error) {
    console.error('Error downloading update:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('install-update', async () => {
  try {
    if (process.env.NODE_ENV === 'development') {
      return { success: false, message: 'Updates disabled in development mode' };
    }
    // This will quit the app and install the update
    autoUpdater.quitAndInstall(false, true);
    return { success: true };
  } catch (error) {
    console.error('Error installing update:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('get-app-version', async () => {
  return { version: app.getVersion() };
});
