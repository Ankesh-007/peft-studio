import { Upload, X, File, CheckCircle, AlertCircle } from "lucide-react";
import React, { useState, useRef } from "react";

import { cn } from "../lib/utils";
import { formatBytes } from "../lib/utils";

export interface FileUploadProps {
  accept?: string;
  multiple?: boolean;
  maxSize?: number; // in bytes
  onFilesSelected: (files: File[]) => void;
  disabled?: boolean;
  error?: string;
  "aria-label": string;
  className?: string;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  accept,
  multiple = false,
  maxSize,
  onFilesSelected,
  disabled = false,
  error,
  "aria-label": ariaLabel,
  className,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});
  const [fileErrors, setFileErrors] = useState<Record<string, string>>({});
  const inputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): string | null => {
    if (maxSize && file.size > maxSize) {
      return `File size exceeds ${formatBytes(maxSize)}`;
    }

    if (accept) {
      const acceptedTypes = accept.split(",").map((t) => t.trim());
      const fileExtension = "." + file.name.split(".").pop();
      const mimeType = file.type;

      const isAccepted = acceptedTypes.some((type) => {
        if (type.startsWith(".")) {
          return fileExtension === type;
        }
        return mimeType.match(new RegExp(type.replace("*", ".*")));
      });

      if (!isAccepted) {
        return `File type not accepted. Accepted: ${accept}`;
      }
    }

    return null;
  };

  const handleFiles = (files: FileList | null) => {
    if (!files || disabled) return;

    const fileArray = Array.from(files);
    const errors: Record<string, string> = {};
    const validFiles: File[] = [];

    fileArray.forEach((file) => {
      const error = validateFile(file);
      if (error) {
        errors[file.name] = error;
      } else {
        validFiles.push(file);
      }
    });

    setFileErrors(errors);

    if (validFiles.length > 0) {
      const newFiles = multiple ? [...selectedFiles, ...validFiles] : validFiles;
      setSelectedFiles(newFiles);
      onFilesSelected(newFiles);

      // Simulate upload progress
      validFiles.forEach((file) => {
        simulateUpload(file.name);
      });
    }
  };

  const simulateUpload = (fileName: string) => {
    let progress = 0;
    const interval = setInterval(() => {
      progress += 10;
      setUploadProgress((prev) => ({ ...prev, [fileName]: progress }));

      if (progress >= 100) {
        clearInterval(interval);
      }
    }, 100);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  const handleRemove = (fileName: string) => {
    const newFiles = selectedFiles.filter((f) => f.name !== fileName);
    setSelectedFiles(newFiles);
    onFilesSelected(newFiles);

    setUploadProgress((prev) => {
      const updated = { ...prev };
      delete updated[fileName];
      return updated;
    });
  };

  return (
    <div className={cn("space-y-3", className)}>
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !disabled && inputRef.current?.click()}
        className={cn(
          "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
          isDragging && "border-blue-500 bg-blue-50",
          !isDragging && "border-gray-300 hover:border-gray-400",
          disabled && "opacity-50 cursor-not-allowed",
          error && "border-red-500"
        )}
        role="button"
        aria-label={ariaLabel}
        tabIndex={disabled ? -1 : 0}
      >
        <Upload
          className={cn("w-12 h-12 mx-auto mb-4", isDragging ? "text-blue-600" : "text-gray-400")}
        />
        <p className="text-sm font-medium text-gray-700 mb-1">
          {isDragging ? "Drop files here" : "Click to upload or drag and drop"}
        </p>
        <p className="text-xs text-gray-500">
          {accept && `Accepted: ${accept}`}
          {maxSize && ` • Max size: ${formatBytes(maxSize)}`}
        </p>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        onChange={(e) => handleFiles(e.target.files)}
        disabled={disabled}
        className="hidden"
        aria-label={ariaLabel}
      />

      {selectedFiles.length > 0 && (
        <div className="space-y-2">
          {selectedFiles.map((file) => {
            const progress = uploadProgress[file.name] || 0;
            const isComplete = progress === 100;
            const hasError = fileErrors[file.name];

            return (
              <div
                key={file.name}
                className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200"
              >
                <File className="w-5 h-5 text-gray-400 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-sm font-medium text-gray-900 truncate">{file.name}</p>
                    <span className="text-xs text-gray-500 ml-2">{formatBytes(file.size)}</span>
                  </div>
                  {!hasError && (
                    <div className="w-full bg-gray-200 rounded-full h-1.5">
                      <div
                        className={cn(
                          "h-1.5 rounded-full transition-all",
                          isComplete ? "bg-green-600" : "bg-blue-600"
                        )}
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  )}
                  {hasError && (
                    <p className="text-xs text-red-600 flex items-center gap-1">
                      <AlertCircle className="w-3 h-3" />
                      {hasError}
                    </p>
                  )}
                </div>
                {isComplete && <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />}
                <button
                  type="button"
                  onClick={() => handleRemove(file.name)}
                  className="p-1 hover:bg-gray-200 rounded"
                  aria-label={`Remove ${file.name}`}
                >
                  <X className="w-4 h-4 text-gray-500" />
                </button>
              </div>
            );
          })}
        </div>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
};
