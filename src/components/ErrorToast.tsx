import React, { useEffect, useState } from "react";

import { ErrorSeverity } from "../types/error";

import type { FormattedError } from "../types/error";

interface ErrorToastProps {
  error: FormattedError;
  onDismiss: () => void;
  autoHideDuration?: number; // milliseconds, 0 means no auto-hide
}

export const ErrorToast: React.FC<ErrorToastProps> = ({
  error,
  onDismiss,
  autoHideDuration = 5000,
}) => {
  const [isVisible, setIsVisible] = useState(true);
  const [isExiting, setIsExiting] = useState(false);

  useEffect(() => {
    if (autoHideDuration > 0 && error.severity !== ErrorSeverity.CRITICAL) {
      const timer = setTimeout(() => {
        handleDismiss();
      }, autoHideDuration);

      return () => clearTimeout(timer);
    }
  }, [autoHideDuration, error.severity]);

  const handleDismiss = () => {
    setIsExiting(true);
    setTimeout(() => {
      setIsVisible(false);
      onDismiss();
    }, 300); // Match animation duration
  };

  const getSeverityStyles = (severity: ErrorSeverity): string => {
    switch (severity) {
      case ErrorSeverity.LOW:
        return "bg-blue-600 border-blue-700";
      case ErrorSeverity.MEDIUM:
        return "bg-yellow-600 border-yellow-700";
      case ErrorSeverity.HIGH:
        return "bg-orange-600 border-orange-700";
      case ErrorSeverity.CRITICAL:
        return "bg-red-600 border-red-700";
      default:
        return "bg-gray-600 border-gray-700";
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

  if (!isVisible) {
    return null;
  }

  return (
    <div
      className={`fixed bottom-4 right-4 max-w-md w-full shadow-lg rounded-lg border-2 overflow-hidden transition-all duration-300 ${
        isExiting ? "opacity-0 translate-x-full" : "opacity-100 translate-x-0"
      } ${getSeverityStyles(error.severity)}`}
      role="alert"
      aria-live="assertive"
    >
      <div className="p-4 text-white">
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="text-xl">{getSeverityIcon(error.severity)}</span>
            <h3 className="font-bold text-lg">{error.title}</h3>
          </div>
          <button
            onClick={handleDismiss}
            className="text-white hover:text-gray-200 text-2xl leading-none"
            aria-label="Dismiss"
          >
            ×
          </button>
        </div>
        <p className="text-sm mb-3 text-white/90">{error.what_happened}</p>
        {error.actions.length > 0 && (
          <div className="flex gap-2 flex-wrap">
            {error.actions.slice(0, 2).map((action, index) => (
              <button
                key={index}
                className="px-3 py-1 bg-white/20 hover:bg-white/30 rounded text-sm font-medium transition-colors"
                onClick={() => {
                  // Handle action click
                  if (action.action_type === "help_link" && error.help_link) {
                    window.open(error.help_link, "_blank");
                  }
                }}
              >
                {action.automatic ? "🔧 " : ""}
                {action.description.length > 30
                  ? action.description.substring(0, 30) + "..."
                  : action.description}
              </button>
            ))}
          </div>
        )}
      </div>
      {autoHideDuration > 0 && error.severity !== ErrorSeverity.CRITICAL && (
        <div className="h-1 bg-white/30">
          <div
            className="h-full bg-white transition-all"
            style={{
              width: "100%",
              animation: `shrink ${autoHideDuration}ms linear`,
            }}
          />
        </div>
      )}
      <style>{`
        @keyframes shrink {
          from { width: 100%; }
          to { width: 0%; }
        }
      `}</style>
    </div>
  );
};

export default ErrorToast;
