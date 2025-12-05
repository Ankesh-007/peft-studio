import { useState, useCallback } from "react";

import { formatError, executeAutoFix } from "../api/errors";

import type { FormattedError, ErrorCategory, ErrorSeverity } from "../types/error";

interface UseErrorHandlerReturn {
  error: FormattedError | null;
  isRecovering: boolean;
  handleError: (error: Error, context?: Record<string, unknown>) => Promise<void>;
  clearError: () => void;
  retryWithAutoFix: (actionIndex: number) => Promise<boolean>;
}

/**
 * Hook for handling errors in functional components.
 * Provides error formatting, display, and recovery functionality.
 */
export function useErrorHandler(): UseErrorHandlerReturn {
  const [error, setError] = useState<FormattedError | null>(null);
  const [isRecovering, setIsRecovering] = useState(false);

  const handleError = useCallback(async (err: Error, context?: Record<string, unknown>) => {
    try {
      const formatted = await formatError(err, context);
      setError(formatted);
    } catch (e) {
      console.error("Failed to format error:", e);
      // Fallback error
      setError({
        title: "Error Occurred",
        what_happened: err.message || "An unexpected error occurred.",
        why_it_happened: "The system encountered an issue.",
        actions: [
          {
            description: "Try the operation again",
            automatic: false,
            action_type: "manual_step",
          },
        ],
        category: "system" as ErrorCategory,
        severity: "medium" as ErrorSeverity,
        help_link: "https://docs.peftstudio.ai/troubleshooting",
        auto_recoverable: false,
      });
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
    setIsRecovering(false);
  }, []);

  const retryWithAutoFix = useCallback(
    async (actionIndex: number): Promise<boolean> => {
      if (!error || actionIndex >= error.actions.length) {
        return false;
      }

      const action = error.actions[actionIndex];
      if (!action.automatic || !action.action_data) {
        return false;
      }

      setIsRecovering(true);
      try {
        const success = await executeAutoFix(action.action_data, {});
        if (success) {
          clearError();
        }
        return success;
      } catch (e) {
        console.error("Auto-fix failed:", e);
        return false;
      } finally {
        setIsRecovering(false);
      }
    },
    [error, clearError]
  );

  return {
    error,
    isRecovering,
    handleError,
    clearError,
    retryWithAutoFix,
  };
}

export default useErrorHandler;
