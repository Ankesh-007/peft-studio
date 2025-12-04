/// <reference types="vite/client" />

interface Window {
  api: {
    startTraining: (config: any) => Promise<any>;
    pauseTraining: (id: number) => Promise<any>;
    resumeTraining: (id: number) => Promise<any>;
    stopTraining: (id: number) => Promise<any>;
    uploadDataset: (file: File) => Promise<any>;
    listDatasets: () => Promise<any>;
    deleteDataset: (id: number) => Promise<any>;
    listModels: () => Promise<any>;
    downloadModel: (modelId: string) => Promise<any>;
    deleteModel: (id: number) => Promise<any>;
    generateText: (config: any) => Promise<any>;
    getSystemInfo: () => Promise<any>;
    onTrainingProgress: (callback: (data: any) => void) => void;
    onTrainingComplete: (callback: (data: any) => void) => void;
    onTrainingError: (callback: (data: any) => void) => void;
    showNotification: (options: any) => Promise<any>;
    setProgress: (progress: number) => Promise<any>;
    checkDND: () => Promise<any>;
    // Auto-update methods
    checkForUpdates: () => Promise<{ success: boolean; updateInfo?: any; error?: string; message?: string }>;
    downloadUpdate: () => Promise<{ success: boolean; error?: string; message?: string }>;
    installUpdate: () => Promise<{ success: boolean; error?: string; message?: string }>;
    getAppVersion: () => Promise<{ version: string }>;
    onUpdateAvailable: (callback: (data: { version: string; releaseNotes?: string; releaseDate?: string }) => void) => void;
    onUpdateDownloadProgress: (callback: (data: { percent: number; bytesPerSecond: number; transferred: number; total: number }) => void) => void;
    onUpdateDownloaded: (callback: (data: { version: string; releaseNotes?: string }) => void) => void;
    onUpdateStatus: (callback: (data: { status: string; message?: string }) => void) => void;
    onUpdateChecksumFailed: (callback: (data: { expected: string; actual: string; file: string }) => void) => void;
    // Backend management methods
    getBackendStatus: () => Promise<{ running: boolean; port: number; pid?: number; startTime?: Date; restartAttempts: number }>;
    restartBackend: () => Promise<{ running: boolean; port: number; pid?: number; startTime?: Date }>;
    forceRestartBackend: () => Promise<{ running: boolean; port: number; pid?: number; startTime?: Date }>;
    checkBackendHealth: () => Promise<{ healthy: boolean; response?: any; error?: string }>;
    getBackendLogs: () => Promise<{ logPath: string; logs: string }>;
    installDependencies: () => Promise<{ success: boolean; output?: string; error?: string }>;
    checkPort: (port: number) => Promise<{ port: number; available: boolean }>;
    openLogFile: () => Promise<{ logPath: string }>;
    onBackendStatus: (callback: (data: any) => void) => void;
  };
  electron?: {
    invoke: (channel: string, ...args: any[]) => Promise<any>;
  };
}
