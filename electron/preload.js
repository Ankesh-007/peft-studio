const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('api', {
  // Training operations
  startTraining: (config) => ipcRenderer.invoke('training:start', config),
  pauseTraining: (id) => ipcRenderer.invoke('training:pause', id),
  resumeTraining: (id) => ipcRenderer.invoke('training:resume', id),
  stopTraining: (id) => ipcRenderer.invoke('training:stop', id),
  
  // Dataset operations
  uploadDataset: (file) => ipcRenderer.invoke('dataset:upload', file),
  listDatasets: () => ipcRenderer.invoke('dataset:list'),
  deleteDataset: (id) => ipcRenderer.invoke('dataset:delete', id),
  
  // Model operations
  listModels: () => ipcRenderer.invoke('model:list'),
  downloadModel: (modelId) => ipcRenderer.invoke('model:download', modelId),
  deleteModel: (id) => ipcRenderer.invoke('model:delete', id),
  
  // Inference operations
  generateText: (config) => ipcRenderer.invoke('inference:generate', config),
  
  // System operations
  getSystemInfo: () => ipcRenderer.invoke('system:info'),
  
  // WebSocket-like events for training progress
  onTrainingProgress: (callback) => {
    ipcRenderer.on('training:progress', (event, data) => callback(data));
  },
  
  onTrainingComplete: (callback) => {
    ipcRenderer.on('training:complete', (event, data) => callback(data));
  },
  
  onTrainingError: (callback) => {
    ipcRenderer.on('training:error', (event, data) => callback(data));
  },
  
  // Notification operations
  showNotification: (options) => ipcRenderer.invoke('show-notification', options),
  setProgress: (progress) => ipcRenderer.invoke('set-progress', progress),
  checkDND: () => ipcRenderer.invoke('check-dnd'),
  
  // Auto-update operations
  checkForUpdates: () => ipcRenderer.invoke('check-for-updates'),
  downloadUpdate: () => ipcRenderer.invoke('download-update'),
  installUpdate: () => ipcRenderer.invoke('install-update'),
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  
  // Auto-update events
  onUpdateAvailable: (callback) => {
    ipcRenderer.on('update-available', (event, data) => callback(data));
  },
  onUpdateDownloadProgress: (callback) => {
    ipcRenderer.on('update-download-progress', (event, data) => callback(data));
  },
  onUpdateDownloaded: (callback) => {
    ipcRenderer.on('update-downloaded', (event, data) => callback(data));
  },
  onUpdateStatus: (callback) => {
    ipcRenderer.on('update-status', (event, data) => callback(data));
  },
  onUpdateChecksumFailed: (callback) => {
    ipcRenderer.on('update-checksum-failed', (event, data) => callback(data));
  },
});
