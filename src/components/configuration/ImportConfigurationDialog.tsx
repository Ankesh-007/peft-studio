/**
 * Import Configuration Dialog
 * Dialog for importing training configurations with validation
 * Validates: Requirement 18.2 - Import configuration with validation
 */

import React, { useState } from 'react';
import { X, Upload, AlertCircle, CheckCircle, FileText } from 'lucide-react';
import ConfigurationPreview from './ConfigurationPreview';

interface ImportConfigurationDialogProps {
  onClose: () => void;
  onSuccess: (config: Record<string, unknown>) => void;
}

const ImportConfigurationDialog: React.FC<ImportConfigurationDialogProps> = ({
  onClose,
  onSuccess,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [jsonText, setJsonText] = useState('');
  const [importMode, setImportMode] = useState<'file' | 'text'>('file');
  const [previewConfig, setPreviewConfig] = useState<Record<string, unknown> | null>(null);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
      setValidationErrors([]);
      setPreviewConfig(null);

      // Read and preview file
      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const content = event.target?.result as string;
          const parsed = JSON.parse(content);
          validateAndPreview(parsed);
        } catch {
          setError('Invalid JSON file');
        }
      };
      reader.readAsText(selectedFile);
    }
  };

  const handleTextChange = (text: string) => {
    setJsonText(text);
    setError(null);
    setValidationErrors([]);
    setPreviewConfig(null);

    if (text.trim()) {
      try {
        const parsed = JSON.parse(text);
        validateAndPreview(parsed);
      } catch {
        setError('Invalid JSON format');
      }
    }
  };

  const validateAndPreview = (data: Record<string, unknown>) => {
    const errors: string[] = [];

    // Validate structure
    if (!data.configuration) {
      errors.push('Missing "configuration" field');
    }

    if (!data.metadata) {
      errors.push('Missing "metadata" field');
    }

    // Validate metadata
    if (data.metadata) {
      if (!data.metadata.name) {
        errors.push('Missing configuration name in metadata');
      }
    }

    // Validate configuration fields
    if (data.configuration) {
      const requiredFields = [
        'base_model',
        'algorithm',
        'provider',
        'learning_rate',
        'batch_size',
        'num_epochs',
      ];

      for (const field of requiredFields) {
        if (!(field in data.configuration)) {
          errors.push(`Missing required field: ${field}`);
        }
      }
    }

    setValidationErrors(errors);

    if (errors.length === 0) {
      setPreviewConfig(data);
    }
  };

  const handleImport = async () => {
    if (!previewConfig) {
      setError('No valid configuration to import');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      let response;

      if (importMode === 'file' && file) {
        // Import from file
        const formData = new FormData();
        formData.append('file', file);

        response = await fetch('http://localhost:8000/api/configurations/import-file', {
          method: 'POST',
          body: formData,
        });
      } else {
        // Import from JSON text
        response = await fetch('http://localhost:8000/api/configurations/import', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(previewConfig),
        });
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to import configuration');
      }

      const data = await response.json();
      onSuccess(data.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to import configuration');
      console.error('Error importing configuration:', err);
    } finally {
      setLoading(false);
    }
  };

  const isValid = previewConfig && validationErrors.length === 0;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <Upload className="w-6 h-6 text-green-600" />
            <h2 className="text-2xl font-bold text-gray-900">Import Configuration</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
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

          {/* Import Mode Selection */}
          <div className="flex gap-4 border-b border-gray-200">
            <button
              onClick={() => setImportMode('file')}
              className={`pb-3 px-4 font-medium transition-colors ${
                importMode === 'file'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Upload File
            </button>
            <button
              onClick={() => setImportMode('text')}
              className={`pb-3 px-4 font-medium transition-colors ${
                importMode === 'text'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Paste JSON
            </button>
          </div>

          {/* File Upload */}
          {importMode === 'file' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Configuration File
              </label>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-500 transition-colors">
                <input
                  type="file"
                  accept=".json"
                  onChange={handleFileChange}
                  className="hidden"
                  id="file-upload"
                />
                <label
                  htmlFor="file-upload"
                  className="cursor-pointer flex flex-col items-center"
                >
                  <FileText className="w-12 h-12 text-gray-400 mb-3" />
                  <span className="text-sm font-medium text-gray-900 mb-1">
                    {file ? file.name : 'Click to upload or drag and drop'}
                  </span>
                  <span className="text-xs text-gray-500">
                    JSON files only
                  </span>
                </label>
              </div>
            </div>
          )}

          {/* Text Input */}
          {importMode === 'text' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Paste Configuration JSON
              </label>
              <textarea
                value={jsonText}
                onChange={(e) => handleTextChange(e.target.value)}
                placeholder='{"configuration": {...}, "metadata": {...}}'
                rows={10}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
              />
            </div>
          )}

          {/* Validation Status */}
          {(file || jsonText) && (
            <div className="space-y-3">
              {validationErrors.length > 0 ? (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-start gap-3 mb-2">
                    <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="text-sm font-medium text-red-900 mb-2">
                        Validation Errors
                      </h4>
                      <ul className="list-disc list-inside space-y-1">
                        {validationErrors.map((error, index) => (
                          <li key={index} className="text-sm text-red-800">
                            {error}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              ) : previewConfig ? (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    <p className="text-sm font-medium text-green-900">
                      Configuration is valid and ready to import
                    </p>
                  </div>
                </div>
              ) : null}
            </div>
          )}

          {/* Configuration Preview */}
          {previewConfig && validationErrors.length === 0 && (
            <div className="border-t border-gray-200 pt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Configuration Preview
              </h3>
              <ConfigurationPreview
                configuration={previewConfig}
                compact={true}
              />
            </div>
          )}
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
            onClick={handleImport}
            disabled={loading || !isValid}
            className="flex items-center gap-2 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Importing...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                Import Configuration
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ImportConfigurationDialog;
