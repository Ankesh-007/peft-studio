import React, { forwardRef, useState, useRef, useEffect } from "react";
import { cn } from "../lib/utils";

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface AccessibleSelectProps
  extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, "onChange"> {
  options: SelectOption[];
  value?: string;
  onChange?: (value: string) => void;
  placeholder?: string;
  error?: string;
  helperText?: string;
  label?: string;
  searchable?: boolean;
  ariaLabel?: string;
}

/**
 * Accessible select component with search capability and keyboard navigation
 */
export const AccessibleSelect = forwardRef<
  HTMLSelectElement,
  AccessibleSelectProps
>(
  (
    {
      options,
      value,
      onChange,
      placeholder = "Select an option",
      error,
      helperText,
      label,
      searchable = false,
      ariaLabel,
      className,
      disabled,
      ...props
    },
    ref,
  ) => {
    const [isOpen, setIsOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");
    const [focusedIndex, setFocusedIndex] = useState(-1);
    const containerRef = useRef<HTMLDivElement>(null);
    const searchInputRef = useRef<HTMLInputElement>(null);

    const selectedOption = options.find((opt) => opt.value === value);

    const filteredOptions = searchable
      ? options.filter((opt) =>
          opt.label.toLowerCase().includes(searchQuery.toLowerCase()),
        )
      : options;

    // Close dropdown when clicking outside
    useEffect(() => {
      const handleClickOutside = (event: MouseEvent) => {
        if (
          containerRef.current &&
          !containerRef.current.contains(event.target as Node)
        ) {
          setIsOpen(false);
          setSearchQuery("");
        }
      };

      document.addEventListener("mousedown", handleClickOutside);
      return () =>
        document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    // Focus search input when dropdown opens
    useEffect(() => {
      if (isOpen && searchable && searchInputRef.current) {
        searchInputRef.current.focus();
      }
    }, [isOpen, searchable]);

    const handleKeyDown = (e: React.KeyboardEvent) => {
      if (disabled) return;

      switch (e.key) {
        case "Enter":
        case " ":
          if (!isOpen) {
            e.preventDefault();
            setIsOpen(true);
          } else if (focusedIndex >= 0 && focusedIndex < filteredOptions.length) {
            e.preventDefault();
            const option = filteredOptions[focusedIndex];
            if (!option.disabled) {
              onChange?.(option.value);
              setIsOpen(false);
              setSearchQuery("");
            }
          }
          break;
        case "Escape":
          e.preventDefault();
          setIsOpen(false);
          setSearchQuery("");
          break;
        case "ArrowDown":
          e.preventDefault();
          if (!isOpen) {
            setIsOpen(true);
          } else {
            setFocusedIndex((prev) => {
              const nextIndex = prev + 1;
              return nextIndex < filteredOptions.length ? nextIndex : prev;
            });
          }
          break;
        case "ArrowUp":
          e.preventDefault();
          if (isOpen) {
            setFocusedIndex((prev) => (prev > 0 ? prev - 1 : 0));
          }
          break;
      }
    };

    const handleOptionClick = (option: SelectOption) => {
      if (!option.disabled) {
        onChange?.(option.value);
        setIsOpen(false);
        setSearchQuery("");
        setFocusedIndex(-1);
      }
    };

    return (
      <div className={cn("relative w-full", className)} ref={containerRef}>
        {label && (
          <label
            className="mb-4 block text-small font-medium text-dark-text-primary"
            id={`${props.id}-label`}
          >
            {label}
          </label>
        )}

        {/* Hidden native select for form compatibility */}
        <select
          ref={ref}
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          className="sr-only"
          aria-label={ariaLabel || label}
          disabled={disabled}
          {...props}
        >
          {options.map((opt) => (
            <option key={opt.value} value={opt.value} disabled={opt.disabled}>
              {opt.label}
            </option>
          ))}
        </select>

        {/* Custom select button */}
        <button
          type="button"
          onClick={() => !disabled && setIsOpen(!isOpen)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          className={cn(
            "flex w-full items-center justify-between rounded-lg border px-12 py-8 text-left text-body transition-all duration-150",
            "focus:outline-none focus:ring-2 focus:ring-accent-primary focus:ring-offset-2 focus:ring-offset-dark-bg-primary",
            error
              ? "border-accent-error"
              : "border-dark-border hover:border-dark-border-hover",
            disabled
              ? "cursor-not-allowed opacity-50"
              : "cursor-pointer bg-dark-bg-secondary",
            isOpen && "ring-2 ring-accent-primary",
          )}
          aria-haspopup="listbox"
          aria-expanded={isOpen}
          aria-labelledby={label ? `${props.id}-label` : undefined}
          aria-label={!label ? ariaLabel : undefined}
        >
          <span
            className={cn(
              selectedOption
                ? "text-dark-text-primary"
                : "text-dark-text-tertiary",
            )}
          >
            {selectedOption?.label || placeholder}
          </span>
          <svg
            className={cn(
              "h-16 w-16 text-dark-text-secondary transition-transform duration-200",
              isOpen && "rotate-180",
            )}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </button>

        {/* Dropdown menu */}
        {isOpen && (
          <div
            className={cn(
              "absolute z-50 mt-4 w-full rounded-lg border border-dark-border bg-dark-bg-secondary shadow-lg",
              "max-h-[240px] overflow-auto",
            )}
            role="listbox"
            aria-labelledby={label ? `${props.id}-label` : undefined}
          >
            {searchable && (
              <div className="sticky top-0 border-b border-dark-border bg-dark-bg-secondary p-8">
                <input
                  ref={searchInputRef}
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search..."
                  className={cn(
                    "w-full rounded border border-dark-border bg-dark-bg-primary px-8 py-6 text-small",
                    "focus:outline-none focus:ring-2 focus:ring-accent-primary",
                  )}
                  onClick={(e) => e.stopPropagation()}
                />
              </div>
            )}

            {filteredOptions.length === 0 ? (
              <div className="px-12 py-16 text-center text-small text-dark-text-tertiary">
                No options found
              </div>
            ) : (
              filteredOptions.map((option, index) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => handleOptionClick(option)}
                  disabled={option.disabled}
                  className={cn(
                    "w-full px-12 py-8 text-left text-body transition-colors duration-100",
                    "focus:outline-none",
                    option.disabled
                      ? "cursor-not-allowed opacity-50"
                      : "cursor-pointer hover:bg-dark-bg-tertiary",
                    option.value === value && "bg-accent-primary/10 text-accent-primary",
                    index === focusedIndex && "bg-dark-bg-tertiary",
                  )}
                  role="option"
                  aria-selected={option.value === value}
                  aria-disabled={option.disabled}
                >
                  {option.label}
                </button>
              ))
            )}
          </div>
        )}

        {/* Helper text or error message */}
        {(helperText || error) && (
          <p
            className={cn(
              "mt-4 text-small",
              error ? "text-accent-error" : "text-dark-text-tertiary",
            )}
            id={`${props.id}-description`}
            role={error ? "alert" : undefined}
          >
            {error || helperText}
          </p>
        )}
      </div>
    );
  },
);

AccessibleSelect.displayName = "AccessibleSelect";
