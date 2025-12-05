import React, { forwardRef } from "react";

import { cn } from "../lib/utils";

import { Spinner } from "./LoadingStates";

export interface AccessibleButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: "left" | "right";
  fullWidth?: boolean;
  ariaLabel?: string;
}

/**
 * Accessible button component with loading states and proper ARIA attributes
 */
export const AccessibleButton = forwardRef<HTMLButtonElement, AccessibleButtonProps>(
  (
    {
      variant = "primary",
      size = "md",
      loading = false,
      icon,
      iconPosition = "left",
      fullWidth = false,
      ariaLabel,
      className,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const variantClasses = {
      primary: "bg-accent-primary text-white hover:bg-accent-primary/90 focus:ring-accent-primary",
      secondary:
        "bg-dark-bg-tertiary text-dark-text-primary hover:bg-dark-bg-tertiary/80 focus:ring-dark-border",
      ghost:
        "bg-transparent border border-dark-border text-dark-text-secondary hover:bg-dark-bg-tertiary hover:text-dark-text-primary focus:ring-dark-border",
      danger: "bg-accent-error text-white hover:bg-accent-error/90 focus:ring-accent-error",
    };

    const sizeClasses = {
      sm: "px-12 py-6 text-small",
      md: "px-16 py-8 text-body",
      lg: "px-20 py-10 text-body",
    };

    const isDisabled = disabled || loading;

    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center gap-8 rounded-lg font-medium transition-all duration-150",
          "focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-dark-bg-primary",
          "active:scale-98",
          "disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100",
          variantClasses[variant],
          sizeClasses[size],
          fullWidth && "w-full",
          className
        )}
        disabled={isDisabled}
        aria-label={ariaLabel || (typeof children === "string" ? children : undefined)}
        aria-busy={loading}
        {...props}
      >
        {loading && <Spinner size="sm" />}
        {!loading && icon && iconPosition === "left" && icon}
        {children}
        {!loading && icon && iconPosition === "right" && icon}
      </button>
    );
  }
);

AccessibleButton.displayName = "AccessibleButton";
