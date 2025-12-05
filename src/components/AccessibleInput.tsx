import { AlertCircle } from "lucide-react";
import React, { forwardRef } from "react";

import { cn } from "../lib/utils";

export interface AccessibleInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  required?: boolean;
  icon?: React.ReactNode;
  fullWidth?: boolean;
}

/**
 * Accessible input component with proper labels and error handling
 */
export const AccessibleInput = forwardRef<HTMLInputElement, AccessibleInputProps>(
  ({ label, error, hint, required, icon, fullWidth = false, className, id, ...props }, ref) => {
    const [randomId] = React.useState(() => Math.random().toString(36).substr(2, 9));
    const inputId = id || `input-${randomId}`;
    const errorId = `${inputId}-error`;
    const hintId = `${inputId}-hint`;

    return (
      <div className={cn("space-y-2", fullWidth && "w-full")}>
        {label && (
          <label htmlFor={inputId} className="block text-small font-medium text-dark-text-primary">
            {label}
            {required && (
              <span className="text-accent-error ml-1" aria-label="required">
                *
              </span>
            )}
          </label>
        )}

        <div className="relative">
          {icon && (
            <div className="absolute left-12 top-1/2 -translate-y-1/2 text-dark-text-tertiary">
              {icon}
            </div>
          )}

          <input
            ref={ref}
            id={inputId}
            className={cn(
              "input w-full",
              icon && "pl-40",
              error && "border-accent-error focus:border-accent-error focus:ring-accent-error",
              className
            )}
            aria-invalid={!!error}
            aria-describedby={cn(error && errorId, hint && hintId)}
            aria-required={required}
            {...props}
          />

          {error && (
            <div className="absolute right-12 top-1/2 -translate-y-1/2 text-accent-error">
              <AlertCircle className="w-5 h-5" />
            </div>
          )}
        </div>

        {hint && !error && (
          <p id={hintId} className="text-tiny text-dark-text-tertiary">
            {hint}
          </p>
        )}

        {error && (
          <p
            id={errorId}
            className="text-tiny text-accent-error flex items-center gap-2"
            role="alert"
          >
            <AlertCircle className="w-4 h-4" />
            {error}
          </p>
        )}
      </div>
    );
  }
);

AccessibleInput.displayName = "AccessibleInput";
