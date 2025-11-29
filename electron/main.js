const { app, BrowserWindow, Notification, ipcMain } = require('electron');
const path = require('path');

let mainWindow;
let pythonProcess;

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

app.whenReady().then(() => {
  createWindow();
  startPythonBackend();

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
