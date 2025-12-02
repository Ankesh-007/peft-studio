import { Upload, FileText, Check, X, Loader2 } from "lucide-react";
import React, { useState, useCallback } from "react";

import { cn, formatBytes } from "../lib/utils";

interface UploadState {
  status: "idle" | "dragover" | "uploading" | "completed" | "error";
  progress: number;
  file?: File;
  error?: string;
}

const DatasetUpload: React.FC = () => {
  const [uploadState, setUploadState] = useState<UploadState>({
    status: "idle",
    progress: 0,
  });

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setUploadState((prev) => ({ ...prev, status: "dragover" }));
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setUploadState((prev) => ({ ...prev, status: "idle" }));
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) {
      handleFileUpload(file);
    }
  }, []);

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        handleFileUpload(file);
      }
    },
    [],
  );

  const handleFileUpload = (file: File) => {
    setUploadState({
      status: "uploading",
      progress: 0,
      file,
    });

    // Simulate upload progress
    let progress = 0;
    const interval = setInterval(() => {
      progress += 10;
      setUploadState((prev) => ({ ...prev, progress }));

      if (progress >= 100) {
        clearInterval(interval);
        setUploadState((prev) => ({ ...prev, status: "completed" }));
      }
    }, 200);
  };

  const handleReset = () => {
    setUploadState({ status: "idle", progress: 0 });
  };

  return (
    <div className="space-y-24">
      <div>
        <h1 className="text-h1 mb-8">Upload Dataset</h1>
        <p className="text-body text-dark-text-secondary">
          Upload your training data to get started with fine-tuning
        </p>
      </div>

      {/* Upload Zone */}
      <div
        className={cn(
          "relative h-[400px] border-2 border-dashed rounded-2xl transition-all duration-200",
          "flex flex-col items-center justify-center",
          uploadState.status === "idle" &&
            "border-[#3a3a3a] bg-gradient-radial from-[#151515] to-[#0a0a0a]",
          uploadState.status === "dragover" &&
            "border-accent-primary bg-accent-primary/5 scale-[1.02]",
          uploadState.status === "uploading" &&
            "border-accent-info bg-accent-info/5",
          uploadState.status === "completed" &&
            "border-accent-success bg-accent-success/5",
          uploadState.status === "error" &&
            "border-accent-error bg-accent-error/5",
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {/* Idle State */}
        {uploadState.status === "idle" && (
          <div className="text-center">
            <Upload
              size={64}
              className="text-dark-text-tertiary mx-auto mb-16"
            />
            <h2 className="text-h2 mb-8">Upload Your Dataset</h2>
            <p className="text-body text-dark-text-secondary mb-16">
              Drag and drop files here, or click to browse
            </p>
            <p className="text-small text-dark-text-tertiary mb-24">
              Supported formats: CSV, JSON, JSONL, TXT, Parquet
            </p>
            <label className="btn-primary cursor-pointer inline-block">
              <input
                type="file"
                className="hidden"
                accept=".csv,.json,.jsonl,.txt,.parquet"
                onChange={handleFileSelect}
              />
              Choose File
            </label>
            <p className="text-tiny text-dark-text-tertiary mt-12">
              Max 500MB per file
            </p>
          </div>
        )}

        {/* Drag Over State */}
        {uploadState.status === "dragover" && (
          <div className="text-center">
            <Upload
              size={64}
              className="text-accent-primary mx-auto mb-16 animate-bounce"
            />
            <h2 className="text-h2 text-accent-primary">Drop to upload</h2>
          </div>
        )}

        {/* Uploading State */}
        {uploadState.status === "uploading" && uploadState.file && (
          <div className="w-full max-w-[500px] px-32">
            <div className="flex items-center gap-16 mb-16">
              <Loader2 size={48} className="text-accent-info animate-spin" />
              <div className="flex-1">
                <div className="flex items-center justify-between mb-8">
                  <span className="text-body font-medium">
                    {uploadState.file.name}
                  </span>
                  <button
                    onClick={handleReset}
                    className="text-dark-text-tertiary hover:text-dark-text-primary"
                  >
                    <X size={16} />
                  </button>
                </div>
                <p className="text-small text-dark-text-secondary">
                  {formatBytes(uploadState.file.size)} • Uploading...
                </p>
              </div>
            </div>

            <div className="space-y-8">
              <div className="flex justify-between text-small">
                <span className="text-dark-text-secondary">Progress</span>
                <span className="text-accent-info font-medium">
                  {uploadState.progress}%
                </span>
              </div>
              <div className="h-8 bg-dark-bg-primary rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-accent-primary to-accent-info transition-all duration-300"
                  style={{ width: `${uploadState.progress}%` }}
                ></div>
              </div>
              <p className="text-tiny text-dark-text-tertiary text-center">
                Upload speed: 12.5 MB/s
              </p>
            </div>
          </div>
        )}

        {/* Completed State */}
        {uploadState.status === "completed" && uploadState.file && (
          <div className="text-center">
            <div className="w-64 h-64 bg-accent-success/10 rounded-full flex items-center justify-center mx-auto mb-16 animate-scale-in">
              <Check size={32} className="text-accent-success" />
            </div>
            <h2 className="text-h2 mb-8">Upload Complete!</h2>

            <div className="card max-w-[500px] mx-auto text-left mt-24">
              <div className="flex items-start gap-16">
                <FileText size={40} className="text-accent-primary" />
                <div className="flex-1">
                  <h3 className="text-body font-medium mb-4">
                    {uploadState.file.name}
                  </h3>
                  <p className="text-small text-dark-text-secondary mb-8">
                    {formatBytes(uploadState.file.size)}
                  </p>
                  <div className="flex gap-8 text-tiny text-dark-text-tertiary">
                    <span>10,234 rows detected</span>
                    <span>•</span>
                    <span>CSV format</span>
                  </div>
                </div>
              </div>

              <div className="flex gap-8 mt-16">
                <button className="btn-primary flex-1">View Dataset</button>
                <button className="btn-secondary flex-1">Edit</button>
                <button onClick={handleReset} className="btn-ghost">
                  <X size={16} />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Alternative Import Options */}
      <div>
        <p className="text-small text-dark-text-tertiary mb-12">
          Or import from:
        </p>
        <div className="grid grid-cols-3 gap-12">
          <button className="btn-ghost justify-center py-16">
            <span>🤗 Hugging Face</span>
          </button>
          <button className="btn-ghost justify-center py-16">
            <span>📝 Paste Text</span>
          </button>
          <button className="btn-ghost justify-center py-16">
            <span>🗄️ Connect Database</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default DatasetUpload;
