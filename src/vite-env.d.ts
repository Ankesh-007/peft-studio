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
  };
}
