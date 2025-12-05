/// <reference types="vite/client" />

// Import types from electron.d.ts
type TrainingConfig = import("./types/electron").TrainingConfig;
type TrainingResult = import("./types/electron").TrainingResult;
type TrainingProgress = import("./types/electron").TrainingProgress;
type DatasetInfo = import("./types/electron").DatasetInfo;
type ModelInfo = import("./types/electron").ModelInfo;
type InferenceConfig = import("./types/electron").InferenceConfig;
type InferenceResult = import("./types/electron").InferenceResult;
type SystemInfo = import("./types/electron").SystemInfo;
type NotificationOptions = import("./types/electron").NotificationOptions;
type UpdateInfo = import("./types/electron").UpdateInfo;
type UpdateResult = import("./types/electron").UpdateResult;
type BackendStatus = import("./types/electron").BackendStatus;
type BackendHealth = import("./types/electron").BackendHealth;

interface Window {
  api: {
    startTraining: (config: TrainingConfig) => Promise<TrainingResult>;
    pauseTraining: (id: number) => Promise<TrainingResult>;
    resumeTraining: (id: number) => Promise<TrainingResult>;
    stopTraining: (id: number) => Promise<TrainingResult>;
    uploadDataset: (file: File) => Promise<DatasetInfo>;
    listDatasets: () => Promise<DatasetInfo[]>;
    deleteDataset: (id: number) => Promise<{ success: boolean }>;
    listModels: () => Promise<ModelInfo[]>;
    downloadModel: (modelId: string) => Promise<ModelInfo>;
    deleteModel: (id: number) => Promise<{ success: boolean }>;
    generateText: (config: InferenceConfig) => Promise<InferenceResult>;
    getSystemInfo: () => Promise<SystemInfo>;
    onTrainingProgress: (callback: (data: TrainingProgress) => void) => void;
    onTrainingComplete: (callback: (data: TrainingResult) => void) => void;
    onTrainingError: (callback: (data: { error: string; id?: string }) => void) => void;
    showNotification: (options: NotificationOptions) => Promise<{ success: boolean }>;
    setProgress: (progress: number) => Promise<{ success: boolean }>;
    checkDND: () => Promise<boolean>;
    // Auto-update methods
    checkForUpdates: () => Promise<UpdateResult & { updateInfo?: UpdateInfo }>;
    downloadUpdate: () => Promise<UpdateResult>;
    installUpdate: () => Promise<UpdateResult>;
    getAppVersion: () => Promise<{ version: string }>;
    onUpdateAvailable: (callback: (data: UpdateInfo & { releaseDate?: string }) => void) => void;
    onUpdateDownloadProgress: (
      callback: (data: {
        percent: number;
        bytesPerSecond: number;
        transferred: number;
        total: number;
      }) => void
    ) => void;
    onUpdateDownloaded: (callback: (data: UpdateInfo) => void) => void;
    onUpdateStatus: (callback: (data: { status: string; message?: string }) => void) => void;
    onUpdateChecksumFailed: (
      callback: (data: { expected: string; actual: string; file: string }) => void
    ) => void;
    // Backend management methods
    getBackendStatus: () => Promise<BackendStatus>;
    restartBackend: () => Promise<BackendStatus>;
    forceRestartBackend: () => Promise<BackendStatus>;
    checkBackendHealth: () => Promise<BackendHealth>;
    getBackendLogs: () => Promise<{ logPath: string; logs: string }>;
    installDependencies: () => Promise<{ success: boolean; output?: string; error?: string }>;
    checkPort: (port: number) => Promise<{ port: number; available: boolean }>;
    openLogFile: () => Promise<{ logPath: string }>;
    onBackendStatus: (callback: (data: BackendStatus) => void) => void;
  };
  electron?: {
    // Kept as any for low-level Electron invoke - this is a generic IPC channel
    // This is intentionally any as it's a low-level IPC channel that can accept any arguments
    invoke: (channel: string, ...args: unknown[]) => Promise<unknown>;
  };
}
