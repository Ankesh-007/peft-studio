import React, { useEffect, useState, useCallback } from "react";
import { cn } from "../lib/utils";

export type ToastType = "success" | "error" | "warning" | "info";

export interface ToastData {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number; // milliseconds, 0 means no auto-hide
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface ToastProps {
  toast: ToastData;
  onDismiss: () => void;
}

export const Toast: React.FC<ToastProps> = ({ toast, onDismiss }) => {
  const [isExiting, setIsExiting] = useState(false);

  const handleDismiss = useCallback(() => {
    setIsExiting(true);
    setTimeout(() => {
      onDismiss();
    }, 300); // Match animation duration
  }, [onDismiss]);

  useEffect(() => {
    const duration = toast.duration ?? 5000;
    if (duration > 0) {
      const timer = setTimeout(() => {
        handleDismiss();
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [toast.duration, handleDismiss]);



  const getTypeStyles = (type: ToastType): string => {
    switch (type) {
      case "success":
        return "bg-green-600 border-green-700";
      case "error":
        return "bg-red-600 border-red-700";
      case "warning":
        return "bg-yellow-600 border-yellow-700";
      case "info":
        return "bg-blue-600 border-blue-700";
      default:
        return "bg-gray-600 border-gray-700";
    }
  };

  const getTypeIcon = (type: ToastType): string => {
    switch (type) {
      case "success":
        return "✓";
      case "error":
        return "✕";
      case "warning":
        return "⚠";
      case "info":
        return "ℹ";
      default:
        return "•";
    }
  };

  const getAriaRole = (type: ToastType): "status" | "alert" => {
    return type === "error" || type === "warning" ? "alert" : "status";
  };

  return (
    <div
      className={cn(
        "w-full max-w-md overflow-hidden rounded-lg border-2 shadow-lg transition-all duration-300",
        isExiting ? "translate-x-full opacity-0" : "translate-x-0 opacity-100",
        getTypeStyles(toast.type),
      )}
      role={getAriaRole(toast.type)}
      aria-live={toast.type === "error" ? "assertive" : "polite"}
    >
      <div className="p-12 text-white">
        <div className="mb-8 flex items-start justify-between">
          <div className="flex items-center gap-8">
            <span
              className={cn(
                "flex h-20 w-20 items-center justify-center rounded-full bg-white/20 text-base font-bold",
              )}
            >
              {getTypeIcon(toast.type)}
            </span>
            <h3 className="text-base font-bold">{toast.title}</h3>
          </div>
          <button
            onClick={handleDismiss}
            className="text-2xl leading-none text-white hover:text-gray-200"
            aria-label="Dismiss notification"
          >
            ×
          </button>
        </div>

        {toast.message && (
          <p className="mb-8 text-small text-white/90">{toast.message}</p>
        )}

        {toast.action && (
          <button
            onClick={() => {
              toast.action?.onClick();
              handleDismiss();
            }}
            className="rounded bg-white/20 px-12 py-6 text-small font-medium transition-colors hover:bg-white/30"
          >
            {toast.action.label}
          </button>
        )}
      </div>

      {(toast.duration ?? 5000) > 0 && (
        <div className="h-4 bg-white/30">
          <div
            className="h-full bg-white transition-all"
            style={{
              width: "100%",
              animation: `shrink ${toast.duration ?? 5000}ms linear`,
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
