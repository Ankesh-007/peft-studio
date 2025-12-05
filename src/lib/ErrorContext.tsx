import React, { createContext, useContext, useState, useCallback } from "react";

import { formatError } from "../api/errors";
import ErrorToast from "../components/ErrorToast";

import type { FormattedError, ErrorCategory, ErrorSeverity } from "../types/error";
import type { ReactNode } from "react";

interface ErrorContextType {
  showError: (error: Error, context?: Record<string, unknown>) => Promise<void>;
  clearError: () => void;
  currentError: FormattedError | null;
}

const ErrorContext = createContext<ErrorContextType | undefined>(undefined);

interface ErrorProviderProps {
  children: ReactNode;
}

/**
 * Global error handling context provider.
 * Provides a centralized way to handle and display errors throughout the app.
 */
export const ErrorProvider: React.FC<ErrorProviderProps> = ({ children }) => {
  const [currentError, setCurrentError] = useState<FormattedError | null>(null);
  const [toastErrors, setToastErrors] = useState<FormattedError[]>([]);

  const showError = useCallback(async (error: Error, context?: Record<string, unknown>) => {
    try {
      const formatted = await formatError(error, context);

      // Critical errors are shown as full-screen modals
      if (formatted.severity === "critical") {
        setCurrentError(formatted);
      } else {
        // Other errors are shown as toasts
        setToastErrors((prev) => [...prev, formatted]);
      }
    } catch (e) {
      console.error("Failed to format error:", e);
      // Fallback
      const fallbackError: FormattedError = {
        title: "Error Occurred",
        what_happened: error.message || "An unexpected error occurred.",
        why_it_happened: "The system encountered an issue.",
        actions: [
          {
            description: "Try again",
            automatic: false,
            action_type: "manual_step",
          },
        ],
        category: "system" as ErrorCategory,
        severity: "medium" as ErrorSeverity,
        help_link: "https://docs.peftstudio.ai/troubleshooting",
        auto_recoverable: false,
      };
      setToastErrors((prev) => [...prev, fallbackError]);
    }
  }, []);

  const clearError = useCallback(() => {
    setCurrentError(null);
  }, []);

  const dismissToast = useCallback((index: number) => {
    setToastErrors((prev) => prev.filter((_, i) => i !== index));
  }, []);

  return (
    <ErrorContext.Provider value={{ showError, clearError, currentError }}>
      {children}

      {/* Render toast notifications */}
      <div className="fixed bottom-0 right-0 p-4 space-y-2 pointer-events-none">
        <div className="space-y-2 pointer-events-auto">
          {toastErrors.map((error, index) => (
            <ErrorToast
              key={index}
              error={error}
              onDismiss={() => dismissToast(index)}
              autoHideDuration={error.severity === "low" ? 5000 : 0}
            />
          ))}
        </div>
      </div>
    </ErrorContext.Provider>
  );
};

/**
 * Hook to access the error context.
 */
export const useError = (): ErrorContextType => {
  const context = useContext(ErrorContext);
  if (!context) {
    throw new Error("useError must be used within an ErrorProvider");
  }
  return context;
};

export default ErrorProvider;
