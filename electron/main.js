const { app, BrowserWindow, Notification, ipcMain, dialog } = require('electron');
const { autoUpdater } = require('electron-updater');
const path = require('path');
const log = require('electron-log');
const http = require('http');

let mainWindow;
let pythonProcess;

// Configure logging
log.transports.file.level = 'info';
autoUpdater.logger = log;

// Backend Service Manager
class BackendServiceManager {
  constructor() {
    this.process = null;
    this.port = 8000;
    this.maxRestartAttempts = 3;
    this.restartAttempts = 0;
    this.healthCheckInterval = null;
    this.healthCheckIntervalMs = 5000; // Check every 5 seconds
    this.startTime = null;
    this.isShuttingDown = false;
  }

  /**
   * Resolve the backend path based on development or production mode
   * @returns {Promise<Object>} Object containing path information and execution details
   */
  async getBackendPath() {
    const mode = app.isPackaged ? 'production' : 'development';
    const platform = process.platform;
    
    log.info(`Resolving backend path - Mode: ${mode}, Platform: ${platform}`);
    
    if (app.isPackaged) {
      // Production mode: use bundled executable
      const exeName = platform === 'win32' ? 'peft_engine.exe' : 'peft_engine';
      const backendPath = path.join(process.resourcesPath, 'backend', exeName);
      
      log.info(`Production mode - Backend executable path: ${backendPath}`);
      
      return {
        mode: 'production',
        executable: backendPath,
        args: [],
        platform
      };
    } else {
      // Development mode: use Python script with system Python
      const scriptPath = path.join(__dirname, '../backend/main.py');
      const pythonCmd = await this.findPythonExecutable();
      
      log.info(`Development mode - Python: ${pythonCmd}, Script: ${scriptPath}`);
      
      return {
        mode: 'development',
        executable: pythonCmd,
        args: [scriptPath],
        platform
      };
    }
  }

  /**
   * Get backend version information
   * @param {string} backendPath - Path to backend executable or script
   * @returns {Promise<Object>} Version information including app version and backend file info
   */
  async getBackendVersion(backendPath) {
    const fs = require('fs');
    const crypto = require('crypto');
    
    try {
      const appVersion = app.getVersion();
      
      // If backend executable exists, get its file stats and checksum
      if (fs.existsSync(backendPath)) {
        const stats = fs.statSync(backendPath);
        const fileBuffer = fs.readFileSync(backendPath);
        const checksum = crypto.createHash('sha256').update(fileBuffer).digest('hex');
        
        return {
          appVersion,
          backendPath,
          backendSize: stats.size,
          backendModified: stats.mtime.toISOString(),
          backendChecksum: checksum.substring(0, 16), // First 16 chars for logging
          platform: process.platform,
          mode: app.isPackaged ? 'production' : 'development'
        };
      } else {
        return {
          appVersion,
          backendPath,
          backendExists: false,
          platform: process.platform,
          mode: app.isPackaged ? 'production' : 'development'
        };
      }
    } catch (error) {
      log.warn('Failed to get backend version info:', error.message);
      return {
        appVersion: app.getVersion(),
        error: error.message
      };
    }
  }

  /**
   * Log structured error information for diagnostics
   * @param {string} errorType - Type of error
   * @param {string} errorMessage - Error message
   * @param {Object} context - Additional context
   */
  logStructuredError(errorType, errorMessage, context = {}) {
    const errorInfo = {
      type: errorType,
      message: errorMessage,
      platform: process.platform,
      mode: app.isPackaged ? 'production' : 'development',
      timestamp: new Date().toISOString(),
      ...context
    };
    
    log.error('Backend Error:', JSON.stringify(errorInfo, null, 2));
    return errorInfo;
  }

  async start() {
    if (this.process) {
      log.info('Backend service already running');
      return { running: true, port: this.port, pid: this.process.pid };
    }

    log.info('Starting Python backend service...');
    this.startTime = new Date();

    try {
      const { spawn } = require('child_process');
      
      // Resolve backend path based on mode
      const backendInfo = await this.getBackendPath();
      
      // In development mode, check if Python is available
      if (backendInfo.mode === 'development' && !backendInfo.executable) {
        const error = 'Python 3.10+ is required but not found. Please install Python from python.org';
        this.logStructuredError('PYTHON_NOT_FOUND', error, {
          mode: backendInfo.mode,
          platform: backendInfo.platform
        });
        this.sendStatusToRenderer('error', { error, code: 'PYTHON_NOT_FOUND' });
        return { running: false, error, code: 'PYTHON_NOT_FOUND' };
      }
      
      // In production mode, check if executable exists
      if (backendInfo.mode === 'production') {
        const fs = require('fs');
        if (!fs.existsSync(backendInfo.executable)) {
          const error = 'Backend executable not found. Installation may be corrupted. Please reinstall the application.';
          this.logStructuredError('EXECUTABLE_NOT_FOUND', error, {
            path: backendInfo.executable,
            mode: backendInfo.mode,
            platform: backendInfo.platform
          });
          this.sendStatusToRenderer('error', { error, code: 'EXECUTABLE_NOT_FOUND', path: backendInfo.executable });
          return { running: false, error, code: 'EXECUTABLE_NOT_FOUND' };
        }
        
        // On Unix systems, ensure executable has execute permissions
        if (backendInfo.platform !== 'win32') {
          try {
            fs.accessSync(backendInfo.executable, fs.constants.X_OK);
            log.info('Executable has proper execute permissions');
          } catch (permError) {
            log.warn('Executable lacks execute permission, attempting to fix...');
            try {
              fs.chmodSync(backendInfo.executable, 0o755);
              log.info('Execute permission granted successfully');
            } catch (chmodError) {
              const error = 'Backend executable lacks execute permission. Please run: chmod +x ' + backendInfo.executable;
              this.logStructuredError('PERMISSION_DENIED', error, {
                path: backendInfo.executable,
                mode: backendInfo.mode,
                platform: backendInfo.platform,
                chmodError: chmodError.message
              });
              this.sendStatusToRenderer('error', { error, code: 'PERMISSION_DENIED', path: backendInfo.executable });
              return { running: false, error, code: 'PERMISSION_DENIED' };
            }
          }
        }
      }

      // Log backend version information
      const versionInfo = await this.getBackendVersion(backendInfo.executable);
      log.info('Backend Version Information:', JSON.stringify(versionInfo, null, 2));
      
      // Start the backend process
      log.info(`Spawning backend process: ${backendInfo.executable} ${backendInfo.args.join(' ')}`);
      this.process = spawn(backendInfo.executable, backendInfo.args, {
        env: { ...process.env, PYTHONUNBUFFERED: '1' }
      });

      this.process.stdout.on('data', (data) => {
        const output = data.toString();
        log.info(`Backend: ${output}`);
        
        // Check if backend is ready
        if (output.includes('Uvicorn running on') || output.includes('Application startup complete')) {
          const startupTime = Date.now() - this.startTime.getTime();
          const startupSeconds = (startupTime / 1000).toFixed(2);
          
          log.info(`Backend service started successfully in ${startupSeconds}s`);
          
          // Log performance warning if startup is slow
          const targetTime = app.isPackaged ? 5000 : 3000; // 5s for production, 3s for development
          if (startupTime > targetTime) {
            log.warn(
              `SLOW BACKEND STARTUP: ${startupSeconds}s exceeds ${targetTime/1000}s target\n` +
              `Mode: ${app.isPackaged ? 'production' : 'development'}\n` +
              `Platform: ${process.platform}\n` +
              `Consider investigating performance bottlenecks`
            );
          }
          
          this.sendStatusToRenderer('ready', { 
            port: this.port, 
            pid: this.process.pid,
            startupTime: startupTime,
            startupSeconds: parseFloat(startupSeconds)
          });
          this.startHealthChecks();
        }
      });

      this.process.stderr.on('data', (data) => {
        const error = data.toString();
        log.error(`Backend Error: ${error}`);
        
        // Check for specific errors and provide detailed messages
        if (error.includes('Address already in use') || error.includes('EADDRINUSE')) {
          this.logStructuredError('PORT_IN_USE', `Port ${this.port} is already in use`, {
            port: this.port,
            stderr: error
          });
          this.sendStatusToRenderer('error', { 
            error: `Port ${this.port} is in use. Trying alternative port...`,
            code: 'PORT_IN_USE',
            port: this.port
          });
          this.tryAlternativePort();
        } else if (error.includes('ModuleNotFoundError') || error.includes('ImportError')) {
          // Extract module name from error message
          const moduleMatch = error.match(/No module named ['"]([\w.]+)['"]/);
          const missingModule = moduleMatch ? moduleMatch[1] : 'unknown';
          
          const errorMessage = `Missing Python package: ${missingModule}. Please run: pip install -r requirements.txt`;
          this.logStructuredError('MISSING_PACKAGE', errorMessage, {
            missingModule,
            stderr: error
          });
          this.sendStatusToRenderer('error', {
            error: errorMessage,
            code: 'MISSING_PACKAGE',
            missingModule
          });
        } else if (error.includes('Permission denied') || error.includes('EACCES')) {
          const errorMessage = 'Permission denied accessing backend resources. Please check file permissions.';
          this.logStructuredError('PERMISSION_ERROR', errorMessage, {
            stderr: error
          });
          this.sendStatusToRenderer('error', {
            error: errorMessage,
            code: 'PERMISSION_ERROR'
          });
        } else {
          // Generic error - still log it with structure
          this.logStructuredError('BACKEND_ERROR', 'Backend process error', {
            stderr: error
          });
        }
      });

      this.process.on('close', (code) => {
        const uptime = this.startTime ? (Date.now() - this.startTime.getTime()) / 1000 : 0;
        
        this.logStructuredError('PROCESS_CLOSED', `Backend process exited with code ${code}`, {
          exitCode: code,
          uptime: `${uptime.toFixed(2)}s`,
          isShuttingDown: this.isShuttingDown,
          restartAttempts: this.restartAttempts
        });
        
        if (!this.isShuttingDown && code !== 0) {
          log.warn('Backend crashed unexpectedly');
          this.handleCrash(code);
        }
        
        this.process = null;
        this.stopHealthChecks();
      });

      this.process.on('error', (err) => {
        const errorMessage = `Failed to start backend process. Please check the logs for details.`;
        this.logStructuredError('PROCESS_START_FAILED', errorMessage, {
          originalError: err.message,
          errorCode: err.code,
          errorStack: err.stack
        });
        this.sendStatusToRenderer('error', {
          error: errorMessage,
          code: 'PROCESS_START_FAILED',
          details: err.message
        });
      });

      return { 
        running: true, 
        port: this.port, 
        pid: this.process.pid,
        startTime: this.startTime
      };

    } catch (error) {
      log.error('Error starting backend:', error);
      this.sendStatusToRenderer('error', {
        error: error.message,
        code: 'START_ERROR'
      });
      return { running: false, error: error.message };
    }
  }

  async findPythonExecutable() {
    const { exec } = require('child_process');
    const { promisify } = require('util');
    const execAsync = promisify(exec);

    // Try different Python commands
    const pythonCommands = ['python', 'python3', 'py'];
    
    for (const cmd of pythonCommands) {
      try {
        const { stdout } = await execAsync(`${cmd} --version`);
        const version = stdout.trim();
        log.info(`Found Python: ${version}`);
        
        // Check if version is 3.10+
        const match = version.match(/Python (\d+)\.(\d+)/);
        if (match) {
          const major = parseInt(match[1]);
          const minor = parseInt(match[2]);
          if (major === 3 && minor >= 10) {
            return cmd;
          }
        }
      } catch (err) {
        // Command not found, try next
        continue;
      }
    }
    
    return null;
  }

  async tryAlternativePort() {
    // Try ports 8001-8010
    for (let port = 8001; port <= 8010; port++) {
      const available = await this.isPortAvailable(port);
      if (available) {
        log.info(`Switching to alternative port: ${port}`);
        this.port = port;
        // Restart with new port
        await this.stop();
        await this.start();
        return;
      }
    }
    
    const errorMessage = 'All ports 8000-8010 are in use. Please close other applications.';
    this.logStructuredError('NO_AVAILABLE_PORTS', errorMessage, {
      portRange: '8000-8010',
      attemptedPorts: Array.from({ length: 11 }, (_, i) => 8000 + i)
    });
    this.sendStatusToRenderer('error', {
      error: errorMessage,
      code: 'NO_AVAILABLE_PORTS',
      portRange: '8000-8010'
    });
  }

  async isPortAvailable(port) {
    return new Promise((resolve) => {
      const server = require('net').createServer();
      server.once('error', () => resolve(false));
      server.once('listening', () => {
        server.close();
        resolve(true);
      });
      server.listen(port);
    });
  }

  async checkBackendHealth() {
    return new Promise((resolve) => {
      const options = {
        hostname: 'localhost',
        port: this.port,
        path: '/api/health',
        method: 'GET',
        timeout: 3000
      };

      const req = http.request(options, (res) => {
        let data = '';
        res.on('data', (chunk) => { data += chunk; });
        res.on('end', () => {
          if (res.statusCode === 200) {
            try {
              const response = JSON.parse(data);
              resolve({ healthy: true, response });
            } catch (err) {
              resolve({ healthy: false, error: 'Invalid response' });
            }
          } else {
            resolve({ healthy: false, error: `Status ${res.statusCode}` });
          }
        });
      });

      req.on('error', (err) => {
        resolve({ healthy: false, error: err.message });
      });

      req.on('timeout', () => {
        req.destroy();
        resolve({ healthy: false, error: 'Timeout' });
      });

      req.end();
    });
  }

  startHealthChecks() {
    if (this.healthCheckInterval) {
      return;
    }

    log.info('Starting health check monitoring');
    let consecutiveFailures = 0;

    this.healthCheckInterval = setInterval(async () => {
      const health = await this.checkBackendHealth();
      
      if (health.healthy) {
        consecutiveFailures = 0;
        this.sendStatusToRenderer('healthy', { port: this.port });
      } else {
        consecutiveFailures++;
        log.warn(`Health check failed (${consecutiveFailures}/3): ${health.error}`);
        
        if (consecutiveFailures >= 3) {
          log.error('Backend service is unhealthy after 3 consecutive failures');
          this.sendStatusToRenderer('unhealthy', { error: health.error });
          this.handleCrash();
        }
      }
    }, this.healthCheckIntervalMs);
  }

  stopHealthChecks() {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
      this.healthCheckInterval = null;
      log.info('Stopped health check monitoring');
    }
  }

  async handleCrash(exitCode = null) {
    this.stopHealthChecks();
    
    if (this.restartAttempts < this.maxRestartAttempts) {
      this.restartAttempts++;
      log.info(`Attempting to restart backend (attempt ${this.restartAttempts}/${this.maxRestartAttempts})`);
      this.sendStatusToRenderer('restarting', { 
        attempt: this.restartAttempts,
        maxAttempts: this.maxRestartAttempts
      });
      
      // Wait a bit before restarting
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      await this.start();
    } else {
      const errorMessage = 'Backend service failed to start after multiple attempts. Please check the logs and try restarting the application.';
      this.logStructuredError('MAX_RESTARTS_EXCEEDED', errorMessage, {
        restartAttempts: this.restartAttempts,
        maxRestartAttempts: this.maxRestartAttempts,
        lastExitCode: exitCode
      });
      this.sendStatusToRenderer('failed', {
        error: errorMessage,
        code: 'MAX_RESTARTS_EXCEEDED',
        attempts: this.restartAttempts
      });
    }
  }

  async stop() {
    this.isShuttingDown = true;
    this.stopHealthChecks();
    
    if (this.process) {
      log.info('Stopping backend service...');
      this.process.kill('SIGTERM');
      
      // Wait for graceful shutdown
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Force kill if still running
      if (this.process) {
        this.process.kill('SIGKILL');
      }
      
      this.process = null;
    }
  }

  async restart() {
    log.info('Restarting backend service...');
    await this.stop();
    this.restartAttempts = 0;
    return await this.start();
  }

  getStatus() {
    return {
      running: this.process !== null,
      port: this.port,
      pid: this.process?.pid,
      startTime: this.startTime,
      restartAttempts: this.restartAttempts
    };
  }

  /**
   * Get startup performance metrics
   * @returns {Object} Startup metrics including time and mode
   */
  getStartupMetrics() {
    if (!this.startTime) {
      return {
        available: false,
        message: 'Backend has not been started yet'
      };
    }

    const now = Date.now();
    const uptime = now - this.startTime.getTime();
    const uptimeSeconds = (uptime / 1000).toFixed(2);
    const mode = app.isPackaged ? 'production' : 'development';
    const targetTime = app.isPackaged ? 5000 : 3000;

    return {
      available: true,
      startTime: this.startTime.toISOString(),
      uptime: uptime,
      uptimeSeconds: parseFloat(uptimeSeconds),
      mode: mode,
      platform: process.platform,
      targetTime: targetTime,
      meetsTarget: uptime < targetTime,
      running: this.process !== null,
      port: this.port,
      pid: this.process?.pid
    };
  }

  sendStatusToRenderer(status, data = {}) {
    if (mainWindow && mainWindow.webContents) {
      mainWindow.webContents.send('backend-status', { status, ...data });
    }
  }
}

// Create backend service manager instance
const backendManager = new BackendServiceManager();

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

// Start Python backend using BackendServiceManager
async function startPythonBackend() {
  const status = await backendManager.start();
  return status;
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
  backendManager.stop();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('quit', () => {
  backendManager.stop();
});

app.on('before-quit', async (event) => {
  if (backendManager.process) {
    event.preventDefault();
    await backendManager.stop();
    app.quit();
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

// Backend management IPC handlers
ipcMain.handle('backend-status', async () => {
  return backendManager.getStatus();
});

ipcMain.handle('backend-restart', async () => {
  log.info('Backend restart requested');
  return await backendManager.restart();
});

ipcMain.handle('backend-health-check', async () => {
  return await backendManager.checkBackendHealth();
});

// Error recovery IPC handlers
ipcMain.handle('backend-force-restart', async () => {
  log.info('Backend force restart requested');
  backendManager.restartAttempts = 0; // Reset restart counter
  return await backendManager.restart();
});

ipcMain.handle('backend-get-logs', async () => {
  log.info('Backend logs requested');
  const logPath = log.transports.file.getFile().path;
  return { logPath, logs: log.transports.file.readAllLogs() };
});

ipcMain.handle('backend-install-dependencies', async () => {
  log.info('Backend dependency installation requested');
  const { exec } = require('child_process');
  const { promisify } = require('util');
  const execAsync = promisify(exec);
  
  try {
    const pythonCmd = await backendManager.findPythonExecutable();
    if (!pythonCmd) {
      return { success: false, error: 'Python not found' };
    }
    
    const requirementsPath = path.join(__dirname, '../backend/requirements.txt');
    const { stdout, stderr } = await execAsync(`${pythonCmd} -m pip install -r "${requirementsPath}"`);
    
    log.info('Dependency installation output:', stdout);
    if (stderr) {
      log.warn('Dependency installation warnings:', stderr);
    }
    
    return { success: true, output: stdout };
  } catch (error) {
    log.error('Dependency installation failed:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('backend-check-port', async (event, port) => {
  log.info(`Checking if port ${port} is available`);
  const available = await backendManager.isPortAvailable(port);
  return { port, available };
});

ipcMain.handle('open-log-file', async () => {
  log.info('Opening log file');
  const { shell } = require('electron');
  const logPath = log.transports.file.getFile().path;
  shell.showItemInFolder(logPath);
  return { logPath };
});
