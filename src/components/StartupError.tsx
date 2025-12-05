import React from "react";
import { AlertCircle, RefreshCw, FileText, ExternalLink } from "lucide-react";

export interface StartupErrorInfo {
  type:
    | "python_not_found"
    | "port_conflict"
    | "missing_packages"
    | "backend_crash"
    | "cuda_error"
    | "unknown";
  message: string;
  cause?: string;
  fixInstructions: string[];
  technicalDetails?: string;
  timestamp: Date;
}

interface StartupErrorProps {
  error: StartupErrorInfo;
  onRetry: () => void;
  onViewLogs: () => void;
}

const errorTypeConfig = {
  python_not_found: {
    title: "Python Not Found",
    icon: "🐍",
    color: "red",
    severity: "critical",
  },
  port_conflict: {
    title: "Port Conflict",
    icon: "🔌",
    color: "yellow",
    severity: "warning",
  },
  missing_packages: {
    title: "Missing Dependencies",
    icon: "📦",
    color: "orange",
    severity: "error",
  },
  backend_crash: {
    title: "Backend Service Crashed",
    icon: "💥",
    color: "red",
    severity: "critical",
  },
  cuda_error: {
    title: "CUDA Error",
    icon: "🎮",
    color: "yellow",
    severity: "warning",
  },
  unknown: {
    title: "Startup Error",
    icon: "⚠️",
    color: "red",
    severity: "error",
  },
};

export const StartupError: React.FC<StartupErrorProps> = ({ error, onRetry, onViewLogs }) => {
  const config = errorTypeConfig[error.type];

  const getSeverityColor = () => {
    switch (config.severity) {
      case "critical":
        return "border-red-500 bg-red-500/10";
      case "error":
        return "border-orange-500 bg-orange-500/10";
      case "warning":
        return "border-yellow-500 bg-yellow-500/10";
      default:
        return "border-gray-500 bg-gray-500/10";
    }
  };

  const getTextColor = () => {
    switch (config.severity) {
      case "critical":
        return "text-red-400";
      case "error":
        return "text-orange-400";
      case "warning":
        return "text-yellow-400";
      default:
        return "text-gray-400";
    }
  };

  return (
    <div className="fixed inset-0 bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center z-50 p-4">
      <div className="max-w-2xl w-full">
        {/* Error Card */}
        <div className={`border-2 rounded-xl p-6 ${getSeverityColor()}`}>
          {/* Header */}
          <div className="flex items-start gap-4 mb-6">
            <div className="text-5xl">{config.icon}</div>
            <div className="flex-1">
              <h1 className={`text-2xl font-bold mb-2 ${getTextColor()}`}>{config.title}</h1>
              <p className="text-gray-300 text-lg">{error.message}</p>
            </div>
            <AlertCircle className={`w-6 h-6 ${getTextColor()}`} />
          </div>

          {/* Cause Section */}
          {error.cause && (
            <div className="mb-6 p-4 bg-black/30 rounded-lg">
              <h3 className="text-sm font-semibold text-gray-400 mb-2">Why this happened:</h3>
              <p className="text-gray-300 text-sm">{error.cause}</p>
            </div>
          )}

          {/* Fix Instructions */}
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-gray-400 mb-3">How to fix:</h3>
            <ol className="space-y-2">
              {error.fixInstructions.map((instruction, index) => (
                <li key={index} className="flex gap-3">
                  <span className={`font-bold ${getTextColor()} min-w-[24px]`}>{index + 1}.</span>
                  <span className="text-gray-300 text-sm">{instruction}</span>
                </li>
              ))}
            </ol>
          </div>

          {/* Technical Details (Collapsible) */}
          {error.technicalDetails && (
            <details className="mb-6">
              <summary className="cursor-pointer text-sm font-semibold text-gray-400 hover:text-gray-300 mb-2">
                Technical Details
              </summary>
              <div className="p-3 bg-black/40 rounded-lg font-mono text-xs text-gray-400 overflow-x-auto">
                <pre className="whitespace-pre-wrap">{error.technicalDetails}</pre>
              </div>
            </details>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3 flex-wrap">
            <button
              onClick={onRetry}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Retry
            </button>
            <button
              onClick={onViewLogs}
              className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors"
            >
              <FileText className="w-4 h-4" />
              View Logs
            </button>
            {error.type === "python_not_found" && (
              <button
                onClick={() => window.open("https://www.python.org/downloads/", "_blank")}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors"
              >
                <ExternalLink className="w-4 h-4" />
                Download Python
              </button>
            )}
            {error.type === "missing_packages" && (
              <button
                onClick={async () => {
                  try {
                    if (window.api) {
                      const result = await window.api.installDependencies();
                      if (result.success) {
                        alert("Dependencies installed successfully! Click Retry to restart.");
                      } else {
                        alert(`Failed to install dependencies: ${result.error}`);
                      }
                    }
                  } catch (err) {
                    console.error("Failed to install dependencies:", err);
                    alert("Failed to install dependencies. Please install manually.");
                  }
                }}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors"
              >
                <ExternalLink className="w-4 h-4" />
                Install Dependencies
              </button>
            )}
          </div>

          {/* Timestamp */}
          <div className="mt-6 pt-4 border-t border-gray-700">
            <p className="text-xs text-gray-500">
              Error occurred at: {error.timestamp.toLocaleString()}
            </p>
          </div>
        </div>

        {/* Common Errors Reference */}
        <div className="mt-6 p-4 bg-gray-800/50 rounded-lg border border-gray-700">
          <h3 className="text-sm font-semibold text-gray-400 mb-3">Common Startup Issues:</h3>
          <ul className="space-y-2 text-xs text-gray-400">
            <li>
              <strong className="text-gray-300">Python not found:</strong> Install Python 3.10+ from
              python.org
            </li>
            <li>
              <strong className="text-gray-300">Port conflict:</strong> Another application is using
              port 8000
            </li>
            <li>
              <strong className="text-gray-300">Missing packages:</strong> Run: pip install -r
              requirements.txt
            </li>
            <li>
              <strong className="text-gray-300">CUDA not available:</strong> Install CUDA toolkit
              for GPU support
            </li>
          </ul>
        </div>

        {/* Support Link */}
        <div className="mt-4 text-center">
          <a
            href="https://github.com/yourusername/peft-studio/issues"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-blue-400 hover:text-blue-300 underline"
          >
            Still having issues? Get help on GitHub
          </a>
        </div>
      </div>
    </div>
  );
};

export default StartupError;
