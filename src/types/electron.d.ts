// Type declarations for Electron IPC API exposed via preload script

// Training types
interface TrainingConfig {
  modelName: string;
  datasetPath: string;
  [key: string]: unknown;
}

interface TrainingResult {
  id: string;
  status: string;
  [key: string]: unknown;
}

interface TrainingProgress {
  id: string;
  progress: number;
  [key: string]: unknown;
}

// Dataset types
interface DatasetInfo {
  id: string;
  name: string;
  path: string;
  [key: string]: unknown;
}

// Model types
interface ModelInfo {
  id: string;
  name: string;
  [key: string]: unknown;
}

// Inference types
interface InferenceConfig {
  modelId: string;
  prompt: string;
  [key: string]: unknown;
}

interface InferenceResult {
  text: string;
  [key: string]: unknown;
}

// System types
interface SystemInfo {
  platform: string;
  arch: string;
  [key: string]: unknown;
}

// Notification types
interface NotificationOptions {
  title: string;
  body: string;
  [key: string]: unknown;
}

// Update types
interface UpdateInfo {
  version: string;
  releaseNotes?: string;
  [key: string]: unknown;
}

interface UpdateResult {
  success: boolean;
  error?: string;
  message?: string;
  [key: string]: unknown;
}

interface BackendStatus {
  running: boolean;
  port: number;
  pid?: number;
  startTime?: Date;
  restartAttempts: number;
}

interface BackendHealth {
  healthy: boolean;
  response?: Record<string, unknown>;
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
  startTraining: (config: TrainingConfig) => Promise<TrainingResult>;
  pauseTraining: (id: string) => Promise<TrainingResult>;
  resumeTraining: (id: string) => Promise<TrainingResult>;
  stopTraining: (id: string) => Promise<TrainingResult>;

  // Dataset operations
  uploadDataset: (file: File) => Promise<DatasetInfo>;
  listDatasets: () => Promise<DatasetInfo[]>;
  deleteDataset: (id: string) => Promise<{ success: boolean }>;

  // Model operations
  listModels: () => Promise<ModelInfo[]>;
  downloadModel: (modelId: string) => Promise<ModelInfo>;
  deleteModel: (id: string) => Promise<{ success: boolean }>;

  // Inference operations
  generateText: (config: InferenceConfig) => Promise<InferenceResult>;

  // System operations
  getSystemInfo: () => Promise<SystemInfo>;

  // Training events
  onTrainingProgress: (callback: (data: TrainingProgress) => void) => void;
  onTrainingComplete: (callback: (data: TrainingResult) => void) => void;
  onTrainingError: (callback: (data: { error: string; id?: string }) => void) => void;

  // Notification operations
  showNotification: (options: NotificationOptions) => Promise<{ success: boolean }>;
  setProgress: (progress: number) => Promise<{ success: boolean }>;
  checkDND: () => Promise<boolean>;

  // Auto-update operations
  checkForUpdates: () => Promise<UpdateResult & { updateInfo?: UpdateInfo }>;
  downloadUpdate: () => Promise<UpdateResult>;
  installUpdate: () => Promise<UpdateResult>;
  getAppVersion: () => Promise<string>;

  // Auto-update events
  onUpdateAvailable: (callback: (data: UpdateInfo) => void) => void;
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
  onBackendStatus: (callback: (data: BackendStatus) => void) => void;
}

declare global {
  interface Window {
    api: ElectronAPI;
  }
}

export {};
