import React from "react";

import { cn } from "../lib/utils";

/**
 * Skeleton loader for text content
 */
export const SkeletonText: React.FC<{
  lines?: number;
  className?: string;
}> = ({ lines = 1, className }) => {
  return (
    <div
      className={cn("space-y-2", className)}
      role="status"
      aria-label="Loading content"
    >
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="h-4 bg-dark-bg-tertiary rounded animate-pulse"
          style={{ width: `${70 + (i * 10) % 30}%` }}
        />
      ))}
      <span className="sr-only">Loading...</span>
    </div>
  );
};

/**
 * Skeleton loader for card components
 */
export const SkeletonCard: React.FC<{
  className?: string;
}> = ({ className }) => {
  return (
    <div
      className={cn("card animate-pulse", className)}
      role="status"
      aria-label="Loading card"
    >
      <div className="h-6 bg-dark-bg-tertiary rounded w-1/3 mb-4" />
      <div className="space-y-2">
        <div className="h-4 bg-dark-bg-tertiary rounded w-full" />
        <div className="h-4 bg-dark-bg-tertiary rounded w-5/6" />
        <div className="h-4 bg-dark-bg-tertiary rounded w-4/6" />
      </div>
      <span className="sr-only">Loading...</span>
    </div>
  );
};

/**
 * Skeleton loader for table rows
 */
export const SkeletonTable: React.FC<{
  rows?: number;
  columns?: number;
  className?: string;
}> = ({ rows = 5, columns = 4, className }) => {
  return (
    <div
      className={cn("space-y-2", className)}
      role="status"
      aria-label="Loading table"
    >
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4 animate-pulse">
          {Array.from({ length: columns }).map((_, j) => (
            <div key={j} className="h-10 bg-dark-bg-tertiary rounded flex-1" />
          ))}
        </div>
      ))}
      <span className="sr-only">Loading table data...</span>
    </div>
  );
};

/**
 * Spinner component for inline loading states
 */
export const Spinner: React.FC<{
  size?: "sm" | "md" | "lg";
  className?: string;
}> = ({ size = "md", className }) => {
  const sizeClasses = {
    sm: "w-4 h-4 border-2",
    md: "w-8 h-8 border-3",
    lg: "w-12 h-12 border-4",
  };

  return (
    <div
      className={cn(
        "inline-block rounded-full border-accent-primary border-t-transparent animate-spin",
        sizeClasses[size],
        className,
      )}
      role="status"
      aria-label="Loading"
    >
      <span className="sr-only">Loading...</span>
    </div>
  );
};

/**
 * Full page loading overlay
 */
export const LoadingOverlay: React.FC<{
  message?: string;
  visible: boolean;
}> = ({ message = "Loading...", visible }) => {
  if (!visible) return null;

  return (
    <div
      className="fixed inset-0 bg-dark-bg-primary/80 backdrop-blur-sm flex items-center justify-center z-50 transition-opacity duration-300"
      role="status"
      aria-label={message}
      aria-live="polite"
    >
      <div className="card text-center max-w-sm animate-scale-in">
        <Spinner size="lg" className="mx-auto mb-4" />
        <p className="text-body text-dark-text-primary">{message}</p>
      </div>
    </div>
  );
};

/**
 * Progress bar component
 */
export const ProgressBar: React.FC<{
  progress: number;
  label?: string;
  showPercentage?: boolean;
  className?: string;
}> = ({ progress, label, showPercentage = true, className }) => {
  const clampedProgress = Math.min(100, Math.max(0, progress));

  return (
    <div
      className={cn("space-y-2", className)}
      role="progressbar"
      aria-valuenow={clampedProgress}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      {(label || showPercentage) && (
        <div className="flex justify-between text-small text-dark-text-secondary">
          {label && <span>{label}</span>}
          {showPercentage && <span>{clampedProgress.toFixed(0)}%</span>}
        </div>
      )}
      <div className="h-2 bg-dark-bg-tertiary rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-accent-primary to-accent-info transition-all duration-300 ease-out"
          style={{ width: `${clampedProgress}%` }}
        />
      </div>
    </div>
  );
};

/**
 * Skeleton loader for wizard steps
 */
export const SkeletonWizardStep: React.FC = () => {
  return (
    <div
      className="space-y-6 animate-pulse"
      role="status"
      aria-label="Loading wizard step"
    >
      <div className="h-8 bg-dark-bg-tertiary rounded w-1/4 mb-8" />
      <div className="grid grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="card h-48" />
        ))}
      </div>
      <span className="sr-only">Loading wizard step...</span>
    </div>
  );
};
