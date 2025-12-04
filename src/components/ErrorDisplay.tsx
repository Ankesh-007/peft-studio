import React, { useState } from "react";

import { executeAutoFix } from "../api/errors";
import { ErrorSeverity } from "../types/error";

import type { FormattedError, ErrorAction } from "../types/error";

interface ErrorDisplayProps {
  error: FormattedError;
  onDismiss?: () => void;
  onRetry?: () => void;
  context?: Record<string, any>;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  onDismiss,
  onRetry,
  context = {},
}) => {
  const [isExecutingFix, setIsExecutingFix] = useState(false);
  const [executedActions, setExecutedActions] = useState<Set<number>>(
    new Set(),
  );

  const getSeverityColor = (severity: ErrorSeverity): string => {
    switch (severity) {
      case ErrorSeverity.LOW:
        return "bg-blue-50 border-blue-200";
      case ErrorSeverity.MEDIUM:
        return "bg-yellow-50 border-yellow-200";
      case ErrorSeverity.HIGH:
        return "bg-orange-50 border-orange-200";
      case ErrorSeverity.CRITICAL:
        return "bg-red-50 border-red-200";
      default:
        return "bg-gray-50 border-gray-200";
    }
  };

  const getSeverityIcon = (severity: ErrorSeverity): string => {
    switch (severity) {
      case ErrorSeverity.LOW:
        return "ℹ️";
      case ErrorSeverity.MEDIUM:
        return "⚠️";
      case ErrorSeverity.HIGH:
        return "⚠️";
      case ErrorSeverity.CRITICAL:
        return "🚨";
      default:
        return "❗";
    }
  };

  const handleActionClick = async (action: ErrorAction, index: number) => {
    if (action.automatic && action.action_data) {
      setIsExecutingFix(true);
      try {
        const success = await executeAutoFix(action.action_data, context);
        if (success) {
          setExecutedActions(new Set([...executedActions, index]));
          // Optionally retry the original operation
          if (onRetry) {
            setTimeout(() => onRetry(), 1000);
          }
        } else {
          alert("Auto-fix failed. Please try manual steps.");
        }
      } catch (e) {
        console.error("Error executing auto-fix:", e);
        alert("Failed to execute auto-fix.");
      } finally {
        setIsExecutingFix(false);
      }
    } else if (action.action_type === "help_link" && action.action_data?.link) {
      // Open help link
      window.open(
        error.help_link || "https://docs.peftstudio.ai/troubleshooting",
        "_blank",
      );
    }
  };

  const getActionButtonText = (action: ErrorAction, index: number): string => {
    if (executedActions.has(index)) {
      return "✓ Applied";
    }
    if (action.automatic) {
      return isExecutingFix ? "Applying..." : "Apply Fix";
    }
    if (action.action_type === "help_link") {
      return "Get Help";
    }
    return "View Details";
  };

  return (
    <div
      className={`rounded-lg border-2 p-6 shadow-lg ${getSeverityColor(error.severity)}`}
      role="alert"
      aria-live="assertive"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="text-3xl" role="img" aria-label="error severity">
            {getSeverityIcon(error.severity)}
          </span>
          <h2 className="text-xl font-bold text-gray-900">{error.title}</h2>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
            aria-label="Dismiss error"
          >
            ×
          </button>
        )}
      </div>

      {/* What Happened */}
      <div className="mb-4">
        <h3 className="font-semibold text-gray-800 mb-2">What happened:</h3>
        <p className="text-gray-700">{error.what_happened}</p>
      </div>

      {/* Why It Happened */}
      <div className="mb-6">
        <h3 className="font-semibold text-gray-800 mb-2">Why it happened:</h3>
        <p className="text-gray-700">{error.why_it_happened}</p>
      </div>

      {/* Actions */}
      <div className="mb-4">
        <h3 className="font-semibold text-gray-800 mb-3">What you can do:</h3>
        <div className="space-y-3">
          {error.actions.map((action, index) => (
            <div
              key={index}
              className="flex items-start gap-3 p-3 bg-white rounded-md border border-gray-200"
            >
              <span className="text-lg mt-0.5">
                {action.automatic
                  ? "🔧"
                  : action.action_type === "help_link"
                    ? "📚"
                    : "👉"}
              </span>
              <div className="flex-1">
                <p className="text-gray-800">{action.description}</p>
                {action.automatic && (
                  <span className="text-xs text-green-600 font-medium">
                    Automatic fix available
                  </span>
                )}
              </div>
              {(action.automatic || action.action_type === "help_link") && (
                <button
                  onClick={() => handleActionClick(action, index)}
                  disabled={isExecutingFix || executedActions.has(index)}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${executedActions.has(index)
                      ? "bg-green-100 text-green-700 cursor-not-allowed"
                      : action.automatic
                        ? "bg-blue-600 text-white hover:bg-blue-700 disabled:bg-gray-300"
                        : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                    }`}
                >
                  {getActionButtonText(action, index)}
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Help Link */}
      {error.help_link && (
        <div className="pt-4 border-t border-gray-300">
          <button
            onClick={() => window.open(error.help_link, "_blank")}
            className="flex items-center gap-2 text-blue-600 hover:text-blue-800 font-medium"
          >
            <span>📖</span>
            <span>Get Help from Documentation</span>
            <span className="text-xs">↗</span>
          </button>
        </div>
      )}

      {/* Auto-recoverable indicator */}
      {error.auto_recoverable && (
        <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-md">
          <p className="text-sm text-green-800">
            ✓ This error can be automatically recovered. Click &quot;Apply Fix&quot; above
            to try.
          </p>
        </div>
      )}
    </div>
  );
};

export default ErrorDisplay;
