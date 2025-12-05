import React, { useState } from "react";

import { useError } from "../lib/ErrorContext";
import useErrorHandler from "../lib/useErrorHandler";

import ErrorDisplay from "./ErrorDisplay";

/**
 * Demo component showing how to use the error handling system.
 * This demonstrates both the global error context and local error handling.
 */
export const ErrorHandlingDemo: React.FC = () => {
  const { showError: showGlobalError } = useError();
  const { error: localError, handleError: handleLocalError, clearError } = useErrorHandler();
  const [selectedErrorType, setSelectedErrorType] = useState<string>("memory");

  const errorExamples = {
    memory: new Error("CUDA out of memory"),
    file: new Error("FileNotFoundError: No such file or directory: /path/to/dataset.csv"),
    connection: new Error("ConnectionError: Failed to connect to HuggingFace Hub"),
    permission: new Error("PermissionError: Permission denied when writing checkpoint"),
    disk: new Error("OSError: [Errno 28] No space left on device"),
    generic: new Error("An unexpected error occurred during training"),
  };

  const handleTriggerGlobalError = () => {
    const error = errorExamples[selectedErrorType as keyof typeof errorExamples];
    showGlobalError(error, {
      component: "ErrorHandlingDemo",
      action: "trigger_global",
    });
  };

  const handleTriggerLocalError = () => {
    const error = errorExamples[selectedErrorType as keyof typeof errorExamples];
    handleLocalError(error, {
      component: "ErrorHandlingDemo",
      action: "trigger_local",
    });
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h1 className="text-2xl font-bold mb-4">Error Handling System Demo</h1>
        <p className="text-gray-600 mb-6">
          This demo shows how the error handling system formats errors into plain language with
          actionable suggestions.
        </p>

        {/* Error Type Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">Select Error Type:</label>
          <select
            value={selectedErrorType}
            onChange={(e) => setSelectedErrorType(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="memory">GPU Out of Memory</option>
            <option value="file">File Not Found</option>
            <option value="connection">Connection Error</option>
            <option value="permission">Permission Denied</option>
            <option value="disk">Disk Space Full</option>
            <option value="generic">Generic Error</option>
          </select>
        </div>

        {/* Trigger Buttons */}
        <div className="flex gap-4">
          <button
            onClick={handleTriggerGlobalError}
            className="px-6 py-3 bg-red-600 text-white rounded-md hover:bg-red-700 font-medium transition-colors"
          >
            Trigger Global Error (Toast)
          </button>
          <button
            onClick={handleTriggerLocalError}
            className="px-6 py-3 bg-orange-600 text-white rounded-md hover:bg-orange-700 font-medium transition-colors"
          >
            Trigger Local Error (Display)
          </button>
        </div>

        {/* Features List */}
        <div className="mt-8 p-4 bg-blue-50 rounded-md">
          <h3 className="font-semibold text-blue-900 mb-2">Features Demonstrated:</h3>
          <ul className="list-disc list-inside space-y-1 text-blue-800 text-sm">
            <li>Plain-language error messages (no stack traces)</li>
            <li>2-3 actionable suggestions per error</li>
            <li>Automatic fix options for recoverable errors</li>
            <li>Help documentation links</li>
            <li>Severity-based styling and icons</li>
            <li>Global toast notifications for non-critical errors</li>
            <li>Local error displays for component-specific errors</li>
          </ul>
        </div>
      </div>

      {/* Local Error Display */}
      {localError && (
        <div className="animate-fadeIn">
          <ErrorDisplay error={localError} onDismiss={clearError} context={{ demo: true }} />
        </div>
      )}

      {/* Usage Examples */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4">Usage Examples</h2>

        <div className="space-y-4">
          <div>
            <h3 className="font-semibold mb-2">1. Using Global Error Context:</h3>
            <pre className="bg-gray-800 text-gray-100 p-4 rounded-md overflow-x-auto text-sm">
              {`import { useError } from '../lib/ErrorContext';

function MyComponent() {
  const { showError } = useError();
  
  const handleAction = async () => {
    try {
      await riskyOperation();
    } catch (error) {
      showError(error, { component: 'MyComponent' });
    }
  };
}`}
            </pre>
          </div>

          <div>
            <h3 className="font-semibold mb-2">2. Using Local Error Handler:</h3>
            <pre className="bg-gray-800 text-gray-100 p-4 rounded-md overflow-x-auto text-sm">
              {`import useErrorHandler from '../lib/useErrorHandler';

function MyComponent() {
  const { error, handleError, clearError } = useErrorHandler();
  
  const handleAction = async () => {
    try {
      await riskyOperation();
    } catch (error) {
      await handleError(error);
    }
  };
  
  return error ? <ErrorDisplay error={error} onDismiss={clearError} /> : null;
}`}
            </pre>
          </div>

          <div>
            <h3 className="font-semibold mb-2">3. Using Error Boundary:</h3>
            <pre className="bg-gray-800 text-gray-100 p-4 rounded-md overflow-x-auto text-sm">
              {`import { ErrorBoundary } from '../components/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary>
      <YourApp />
    </ErrorBoundary>
  );
}`}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ErrorHandlingDemo;
