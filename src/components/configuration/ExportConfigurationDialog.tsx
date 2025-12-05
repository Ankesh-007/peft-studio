/**
 * Export Configuration Dialog
 * Dialog for exporting training configurations
 * Validates: Requirement 18.1 - Export configuration
 */

import React, { useState } from "react";
import { X, Download, AlertCircle } from "lucide-react";

interface ExportConfigurationDialogProps {
  onClose: () => void;
  onSuccess: () => void;
}

const ExportConfigurationDialog: React.FC<ExportConfigurationDialogProps> = ({
  onClose,
  onSuccess,
}) => {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [author, setAuthor] = useState("");
  const [tags, setTags] = useState("");
  const [saveToLibrary, setSaveToLibrary] = useState(true);
  const [downloadFile, setDownloadFile] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Mock configuration - in real app, this would come from props or context
  const mockConfiguration = {
    base_model: "meta-llama/Llama-2-7b-hf",
    model_source: "huggingface",
    algorithm: "lora",
    rank: 16,
    alpha: 32,
    dropout: 0.1,
    target_modules: ["q_proj", "v_proj"],
    quantization: "int4",
    learning_rate: 0.0002,
    batch_size: 4,
    gradient_accumulation_steps: 4,
    num_epochs: 3,
    warmup_steps: 100,
    provider: "runpod",
    resource_id: "gpu-rtx-4090",
    dataset_path: "/data/training.jsonl",
    validation_split: 0.1,
    experiment_tracker: "wandb",
    project_name: "my-project",
    output_dir: "/output",
    checkpoint_steps: 500,
  };

  const handleExport = async () => {
    if (!name.trim()) {
      setError("Configuration name is required");
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const tagList = tags
        .split(",")
        .map((t) => t.trim())
        .filter((t) => t.length > 0);

      const exportRequest = {
        configuration: mockConfiguration,
        name: name.trim(),
        description: description.trim(),
        author: author.trim() || null,
        tags: tagList.length > 0 ? tagList : null,
      };

      // Save to library if requested
      if (saveToLibrary) {
        const saveResponse = await fetch("http://localhost:8000/api/configurations/library/save", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(exportRequest),
        });

        if (!saveResponse.ok) {
          throw new Error("Failed to save configuration to library");
        }
      }

      // Download file if requested
      if (downloadFile) {
        const downloadResponse = await fetch(
          "http://localhost:8000/api/configurations/export-file",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify(exportRequest),
          }
        );

        if (!downloadResponse.ok) {
          throw new Error("Failed to download configuration file");
        }

        // Trigger download
        const blob = await downloadResponse.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${name.replace(/[^a-z0-9]/gi, "_")}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      }

      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to export configuration");
      console.error("Error exporting configuration:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <Download className="w-6 h-6 text-blue-600" />
            <h2 className="text-2xl font-bold text-gray-900">Export Configuration</h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Error Display */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-800">{error}</p>
              </div>
            </div>
          )}

          {/* Form */}
          <div className="space-y-4">
            {/* Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Configuration Name *
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Llama-2-7B LoRA Fine-tune"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe this configuration..."
                rows={3}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Author */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Author</label>
              <input
                type="text"
                value={author}
                onChange={(e) => setAuthor(e.target.value)}
                placeholder="Your name"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Tags */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Tags</label>
              <input
                type="text"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                placeholder="e.g., llama, lora, production (comma-separated)"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="mt-1 text-sm text-gray-500">Separate tags with commas</p>
            </div>

            {/* Export Options */}
            <div className="space-y-3 pt-4 border-t border-gray-200">
              <h3 className="text-sm font-medium text-gray-900">Export Options</h3>

              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={saveToLibrary}
                  onChange={(e) => setSaveToLibrary(e.target.checked)}
                  className="mt-1 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <div>
                  <div className="text-sm font-medium text-gray-900">Save to Library</div>
                  <div className="text-sm text-gray-500">
                    Save this configuration to your local library for easy access
                  </div>
                </div>
              </label>

              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={downloadFile}
                  onChange={(e) => setDownloadFile(e.target.checked)}
                  className="mt-1 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <div>
                  <div className="text-sm font-medium text-gray-900">Download as File</div>
                  <div className="text-sm text-gray-500">
                    Download a JSON file that can be shared with others
                  </div>
                </div>
              </label>
            </div>

            {/* Configuration Preview */}
            <div className="pt-4 border-t border-gray-200">
              <h3 className="text-sm font-medium text-gray-900 mb-2">Configuration Preview</h3>
              <div className="bg-gray-50 rounded-lg p-4 max-h-48 overflow-y-auto">
                <pre className="text-xs text-gray-700 font-mono">
                  {JSON.stringify(mockConfiguration, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 hover:text-gray-900 transition-colors"
            disabled={loading}
          >
            Cancel
          </button>
          <button
            onClick={handleExport}
            disabled={loading || !name.trim() || (!saveToLibrary && !downloadFile)}
            className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Exporting...
              </>
            ) : (
              <>
                <Download className="w-4 h-4" />
                Export
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ExportConfigurationDialog;
