import React, { createContext, useContext, useState, useCallback } from "react";
import { Toast, ToastData, ToastType } from "../components/Toast";

interface ToastContextType {
  showToast: (
    type: ToastType,
    title: string,
    message?: string,
    options?: Partial<Omit<ToastData, "id" | "type" | "title" | "message">>
  ) => string;
  success: (title: string, message?: string) => string;
  error: (title: string, message?: string) => string;
  warning: (title: string, message?: string) => string;
  info: (title: string, message?: string) => string;
  dismissToast: (id: string) => void;
  clearAll: () => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

interface ToastProviderProps {
  children: React.ReactNode;
  maxToasts?: number;
}

/**
 * Toast notification context provider.
 * Provides a centralized way to display toast notifications throughout the app.
 */
export const ToastProvider: React.FC<ToastProviderProps> = ({ children, maxToasts = 5 }) => {
  const [toasts, setToasts] = useState<ToastData[]>([]);

  const showToast = useCallback(
    (
      type: ToastType,
      title: string,
      message?: string,
      options?: Partial<Omit<ToastData, "id" | "type" | "title" | "message">>
    ): string => {
      const id = `toast-${Date.now()}-${Math.random()}`;
      const newToast: ToastData = {
        id,
        type,
        title,
        message,
        duration: options?.duration ?? 5000,
        action: options?.action,
      };

      setToasts((prev) => {
        const updated = [...prev, newToast];
        // Keep only the most recent toasts up to maxToasts
        return updated.slice(-maxToasts);
      });

      return id;
    },
    [maxToasts]
  );

  const success = useCallback(
    (title: string, message?: string): string => {
      return showToast("success", title, message);
    },
    [showToast]
  );

  const error = useCallback(
    (title: string, message?: string): string => {
      return showToast("error", title, message, { duration: 0 }); // Errors don't auto-dismiss
    },
    [showToast]
  );

  const warning = useCallback(
    (title: string, message?: string): string => {
      return showToast("warning", title, message, { duration: 7000 });
    },
    [showToast]
  );

  const info = useCallback(
    (title: string, message?: string): string => {
      return showToast("info", title, message);
    },
    [showToast]
  );

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const clearAll = useCallback(() => {
    setToasts([]);
  }, []);

  return (
    <ToastContext.Provider
      value={{
        showToast,
        success,
        error,
        warning,
        info,
        dismissToast,
        clearAll,
      }}
    >
      {children}

      {/* Render toast notifications */}
      <div
        className="pointer-events-none fixed bottom-0 right-0 z-50 p-16"
        aria-live="polite"
        aria-atomic="false"
      >
        <div className="pointer-events-auto space-y-8">
          {toasts.map((toast) => (
            <Toast key={toast.id} toast={toast} onDismiss={() => dismissToast(toast.id)} />
          ))}
        </div>
      </div>
    </ToastContext.Provider>
  );
};

/**
 * Hook to access the toast context.
 * Provides methods to show success, error, warning, and info toasts.
 *
 * @example
 * const toast = useToast();
 * toast.success("Operation completed", "Your changes have been saved");
 * toast.error("Operation failed", "Please try again");
 */
export const useToast = (): ToastContextType => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
};
