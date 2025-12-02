import { Upload, File, AlertCircle, CheckCircle, Info, X } from "lucide-react";
import React, { useState, useCallback } from "react";

import Tooltip from "../Tooltip";

import type {
  Dataset,
  ValidationResult,
  WizardState,
} from "../../types/wizard";

interface DatasetUploadStepProps {
  wizardState: WizardState;
  onDatasetSelect: (dataset: Dataset, validation: ValidationResult[]) => void;
}

/**
 * Step 2: Dataset Upload with drag-and-drop, validation, and preview
 */
const DatasetUploadStep: React.FC<DatasetUploadStepProps> = ({
  wizardState,
  onDatasetSelect,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [preview, setPreview] = useState<any[] | null>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      await handleFileUpload(files[0]);
    }
  }, []);

  const handleFileSelect = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        await handleFileUpload(files[0]);
      }
    },
    [],
  );

  const handleFileUpload = async (file: File) => {
    setUploading(true);

    try {
      // Upload file
      const formData = new FormData();
      formData.append("file", file);

      const uploadResponse = await fetch(
        "http://127.0.0.1:8000/api/datasets/upload",
        {
          method: "POST",
          body: formData,
        },
      );

      if (!uploadResponse.ok) {
        throw new Error("Upload failed");
      }

      const uploadData = await uploadResponse.json();

      // Mock validation for now (backend endpoint to be implemented)
      const validation: ValidationResult[] = [];

      // Detect format
      const extension = file.name.split(".").pop()?.toLowerCase();
      let format = "unknown";
      if (extension === "csv") format = "csv";
      else if (extension === "json") format = "json";
      else if (extension === "jsonl") format = "jsonl";
      else if (extension === "txt") format = "txt";

      // Create dataset object
      const dataset: Dataset = {
        id: uploadData.id || Date.now().toString(),
        name: file.name,
        path: uploadData.path || file.name,
        format,
        size: file.size,
        num_samples: uploadData.num_samples,
      };

      // Mock preview data
      setPreview([
        { text: "Sample training example 1...", tokens: 150 },
        { text: "Sample training example 2...", tokens: 200 },
        { text: "Sample training example 3...", tokens: 180 },
      ]);

      // Add validation messages
      if (dataset.num_samples && dataset.num_samples < 100) {
        validation.push({
          field: "dataset_size",
          level: "warning",
          message: `Dataset has only ${dataset.num_samples} samples`,
          suggestion:
            "Consider adding more training examples for better results. Recommended: 500+ samples.",
          autoFixable: false,
        });
      }

      if (format === "unknown") {
        validation.push({
          field: "format",
          level: "error",
          message: "Unsupported file format",
          suggestion: "Please upload a CSV, JSON, JSONL, or TXT file.",
          autoFixable: false,
        });
      } else {
        validation.push({
          field: "format",
          level: "info",
          message: `Format detected: ${format.toUpperCase()}`,
          autoFixable: false,
        });
      }

      onDatasetSelect(dataset, validation);
    } catch (error) {
      console.error("Upload error:", error);
      const validation: ValidationResult[] = [
        {
          field: "upload",
          level: "error",
          message: "Failed to upload dataset",
          suggestion: "Please check your connection and try again.",
          autoFixable: false,
        },
      ];
      onDatasetSelect(
        {
          id: "",
          name: file.name,
          path: "",
          format: "unknown",
          size: file.size,
        },
        validation,
      );
    } finally {
      setUploading(false);
    }
  };

  const handleRemoveDataset = () => {
    onDatasetSelect(null as any, []);
    setPreview(null);
  };

  const getValidationIcon = (level: ValidationResult["level"]) => {
    switch (level) {
      case "error":
        return <AlertCircle className="w-5 h-5 text-red-600" />;
      case "warning":
        return <AlertCircle className="w-5 h-5 text-yellow-600" />;
      case "info":
        return <Info className="w-5 h-5 text-blue-600" />;
      default:
        return <CheckCircle className="w-5 h-5 text-green-600" />;
    }
  };

  const getValidationBgColor = (level: ValidationResult["level"]) => {
    switch (level) {
      case "error":
        return "bg-red-50 border-red-200";
      case "warning":
        return "bg-yellow-50 border-yellow-200";
      case "info":
        return "bg-blue-50 border-blue-200";
      default:
        return "bg-green-50 border-green-200";
    }
  };

  const hasErrors = wizardState.validation.some((v) => v.level === "error");

  return (
    <div className="space-y-6">
      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-blue-900 mb-2">
          Upload Your Training Data
        </h2>
        <p className="text-blue-800 mb-3">
          Upload your dataset in CSV, JSON, JSONL, or plain text format. We'll
          automatically validate it and show you a preview.
        </p>
        <div className="flex items-center gap-2">
          <Tooltip configKey="dataset_format">
            <span className="text-sm text-blue-700 underline cursor-help">
              What formats are supported?
            </span>
          </Tooltip>
        </div>
      </div>

      {/* Upload Area */}
      {!wizardState.dataset ? (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`
            border-2 border-dashed rounded-lg p-12 text-center transition-colors
            ${
              isDragging
                ? "border-blue-600 bg-blue-50"
                : "border-gray-300 bg-white hover:border-gray-400"
            }
          `}
        >
          <Upload
            className={`w-16 h-16 mx-auto mb-4 ${isDragging ? "text-blue-600" : "text-gray-400"}`}
          />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {isDragging ? "Drop your file here" : "Drag and drop your dataset"}
          </h3>
          <p className="text-gray-600 mb-4">or</p>
          <label className="inline-block">
            <input
              type="file"
              accept=".csv,.json,.jsonl,.txt"
              onChange={handleFileSelect}
              className="hidden"
              disabled={uploading}
            />
            <span className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer inline-block">
              {uploading ? "Uploading..." : "Browse Files"}
            </span>
          </label>
          <p className="text-sm text-gray-500 mt-4">
            Supported formats: CSV, JSON, JSONL, TXT
          </p>
        </div>
      ) : (
        /* Dataset Info */
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <File className="w-8 h-8 text-blue-600" />
              <div>
                <h3 className="font-semibold text-gray-900">
                  {wizardState.dataset.name}
                </h3>
                <p className="text-sm text-gray-600">
                  {(wizardState.dataset.size / 1024).toFixed(2)} KB
                  {wizardState.dataset.num_samples &&
                    ` • ${wizardState.dataset.num_samples} samples`}
                  {wizardState.dataset.format &&
                    ` • ${wizardState.dataset.format.toUpperCase()}`}
                </p>
              </div>
            </div>
            <button
              onClick={handleRemoveDataset}
              className="p-2 text-gray-400 hover:text-red-600 rounded-lg hover:bg-red-50"
              title="Remove dataset"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Validation Results */}
          {wizardState.validation.length > 0 && (
            <div className="space-y-2 mb-4">
              <div className="flex items-center gap-2">
                <h4 className="text-sm font-semibold text-gray-900">
                  Validation Results
                </h4>
                <Tooltip configKey="dataset_validation" />
              </div>
              {wizardState.validation.map((result, idx) => (
                <div
                  key={idx}
                  className={`flex items-start gap-3 p-4 rounded-lg border ${getValidationBgColor(result.level)}`}
                  data-testid={`validation-${result.level}-${idx}`}
                >
                  {getValidationIcon(result.level)}
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">
                      {result.message}
                    </p>
                    {result.suggestion && (
                      <p className="text-sm text-gray-600 mt-1">
                        {result.suggestion}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Preview */}
          {preview && preview.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-gray-900 mb-3">
                Dataset Preview
              </h4>
              <div className="space-y-2">
                {preview.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-3 bg-gray-50 rounded border border-gray-200"
                  >
                    <p className="text-sm text-gray-700 mb-1">{item.text}</p>
                    <p className="text-xs text-gray-500">
                      ~{item.tokens} tokens
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Error Summary */}
      {hasErrors && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h4 className="font-semibold text-red-900 mb-2">⚠️ Cannot Proceed</h4>
          <p className="text-sm text-red-800">
            Please fix the errors above before continuing to the next step.
          </p>
        </div>
      )}

      {/* Success Message */}
      {wizardState.dataset && !hasErrors && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <h4 className="font-semibold text-green-900 mb-2">✓ Dataset Ready</h4>
          <p className="text-sm text-green-800">
            Your dataset has been validated and is ready for training. Click
            "Next" to select a model.
          </p>
        </div>
      )}
    </div>
  );
};

export default DatasetUploadStep;
