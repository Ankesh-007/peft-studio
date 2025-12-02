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
    showNotification?: (options: {
      title: string;
      message: string;
      urgency?: string;
      sound?: boolean;
    }) => Promise<{ success: boolean }>;
    setProgress?: (progress: number) => Promise<void>;
    checkDND?: () => Promise<{ enabled: boolean }>;
  };
}
