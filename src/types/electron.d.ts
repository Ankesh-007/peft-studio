// Type declarations for Electron IPC API exposed via preload script

interface BackendStatus {
  running: boolean;
  port: number;
  pid?: number;
  startTime?: Date;
  restartAttempts: number;
}

interface BackendHealth {
  healthy: boolean;
  response?: any;
  error?: string;
}

interface BackendLogs {
  logPath: string;
  logs: string;
}

interface DependencyInstallResult {
  success: boolean;
  output?: string;
  error?: string;
}

interface PortCheckResult {
  port: number;
  available: boolean;
}

interface LogFileResult {
  logPath: string;
}

interface ElectronAPI {
  // Training operations
  startTraining: (config: any) => Promise<any>;
  pauseTraining: (id: string) => Promise<any>;
  resumeTraining: (id: string) => Promise<any>;
  stopTraining: (id: string) => Promise<any>;

  // Dataset operations
  uploadDataset: (file: any) => Promise<any>;
  listDatasets: () => Promise<any>;
  deleteDataset: (id: string) => Promise<any>;

  // Model operations
  listModels: () => Promise<any>;
  downloadModel: (modelId: string) => Promise<any>;
  deleteModel: (id: string) => Promise<any>;

  // Inference operations
  generateText: (config: any) => Promise<any>;

  // System operations
  getSystemInfo: () => Promise<any>;

  // Training events
  onTrainingProgress: (callback: (data: any) => void) => void;
  onTrainingComplete: (callback: (data: any) => void) => void;
  onTrainingError: (callback: (data: any) => void) => void;

  // Notification operations
  showNotification: (options: any) => Promise<any>;
  setProgress: (progress: number) => Promise<any>;
  checkDND: () => Promise<boolean>;

  // Auto-update operations
  checkForUpdates: () => Promise<any>;
  downloadUpdate: () => Promise<any>;
  installUpdate: () => Promise<any>;
  getAppVersion: () => Promise<string>;

  // Auto-update events
  onUpdateAvailable: (callback: (data: any) => void) => void;
  onUpdateDownloadProgress: (callback: (data: any) => void) => void;
  onUpdateDownloaded: (callback: (data: any) => void) => void;
  onUpdateStatus: (callback: (data: any) => void) => void;
  onUpdateChecksumFailed: (callback: (data: any) => void) => void;

  // Backend management operations
  getBackendStatus: () => Promise<BackendStatus>;
  restartBackend: () => Promise<BackendStatus>;
  forceRestartBackend: () => Promise<BackendStatus>;
  checkBackendHealth: () => Promise<BackendHealth>;
  getBackendLogs: () => Promise<BackendLogs>;
  installDependencies: () => Promise<DependencyInstallResult>;
  checkPort: (port: number) => Promise<PortCheckResult>;
  openLogFile: () => Promise<LogFileResult>;

  // Backend status events
  onBackendStatus: (callback: (data: any) => void) => void;
}

declare global {
  interface Window {
    api: ElectronAPI;
  }
}

export {};
