/**
 * Accessibility utilities for ARIA labels, focus management, and screen reader support
 */

/**
 * Generate unique IDs for ARIA attributes
 */
let idCounter = 0;
export function generateId(prefix: string = "id"): string {
  return `${prefix}-${++idCounter}`;
}

/**
 * Focus trap for modals and dialogs
 */
export class FocusTrap {
  private element: HTMLElement;
  private previousFocus: HTMLElement | null = null;
  private focusableElements: HTMLElement[] = [];

  constructor(element: HTMLElement) {
    this.element = element;
  }

  /**
   * Activate the focus trap
   */
  activate(): void {
    // Store the currently focused element
    this.previousFocus = document.activeElement as HTMLElement;

    // Get all focusable elements within the trap
    this.focusableElements = this.getFocusableElements();

    // Focus the first focusable element
    if (this.focusableElements.length > 0) {
      this.focusableElements[0].focus();
    }

    // Add event listener for Tab key
    this.element.addEventListener("keydown", this.handleKeyDown);
  }

  /**
   * Deactivate the focus trap and restore previous focus
   */
  deactivate(): void {
    this.element.removeEventListener("keydown", this.handleKeyDown);

    // Restore focus to the previously focused element
    if (this.previousFocus && this.previousFocus.focus) {
      this.previousFocus.focus();
    }
  }

  private handleKeyDown = (event: KeyboardEvent): void => {
    if (event.key !== "Tab") {
      return;
    }

    const firstElement = this.focusableElements[0];
    const lastElement = this.focusableElements[this.focusableElements.length - 1];

    if (event.shiftKey) {
      // Shift + Tab
      if (document.activeElement === firstElement) {
        event.preventDefault();
        lastElement.focus();
      }
    } else {
      // Tab
      if (document.activeElement === lastElement) {
        event.preventDefault();
        firstElement.focus();
      }
    }
  };

  private getFocusableElements(): HTMLElement[] {
    const selector = [
      "a[href]",
      "button:not([disabled])",
      "textarea:not([disabled])",
      "input:not([disabled])",
      "select:not([disabled])",
      '[tabindex]:not([tabindex="-1"])',
    ].join(", ");

    return Array.from(this.element.querySelectorAll(selector));
  }
}

/**
 * React hook for focus trap
 */
import { useEffect, useRef } from "react";

export function useFocusTrap(isActive: boolean): React.RefObject<HTMLDivElement> {
  const ref = useRef<HTMLDivElement>(null);
  const trapRef = useRef<FocusTrap | null>(null);

  useEffect(() => {
    if (!ref.current) return;

    if (isActive) {
      trapRef.current = new FocusTrap(ref.current);
      trapRef.current.activate();
    }

    return () => {
      if (trapRef.current) {
        trapRef.current.deactivate();
        trapRef.current = null;
      }
    };
  }, [isActive]);

  return ref;
}

/**
 * Announce message to screen readers using ARIA live region
 */
export function announceToScreenReader(
  message: string,
  priority: "polite" | "assertive" = "polite"
): void {
  // Create or get the live region
  let liveRegion = document.getElementById("screen-reader-announcements");

  if (!liveRegion) {
    liveRegion = document.createElement("div");
    liveRegion.id = "screen-reader-announcements";
    liveRegion.setAttribute("role", "status");
    liveRegion.setAttribute("aria-live", priority);
    liveRegion.setAttribute("aria-atomic", "true");
    liveRegion.className = "sr-only";
    document.body.appendChild(liveRegion);
  }

  // Update the message
  liveRegion.textContent = message;

  // Clear after a delay to allow for repeated announcements
  setTimeout(() => {
    if (liveRegion) {
      liveRegion.textContent = "";
    }
  }, 1000);
}

/**
 * Check if an element is visible to screen readers
 */
export function isVisibleToScreenReader(element: HTMLElement): boolean {
  const style = window.getComputedStyle(element);

  return (
    style.display !== "none" &&
    style.visibility !== "hidden" &&
    element.getAttribute("aria-hidden") !== "true" &&
    parseFloat(style.opacity) > 0
  );
}

/**
 * Get accessible name for an element
 */
export function getAccessibleName(element: HTMLElement): string {
  // Check aria-label
  const ariaLabel = element.getAttribute("aria-label");
  if (ariaLabel) return ariaLabel;

  // Check aria-labelledby
  const labelledBy = element.getAttribute("aria-labelledby");
  if (labelledBy) {
    const labelElement = document.getElementById(labelledBy);
    if (labelElement) return labelElement.textContent || "";
  }

  // Check associated label
  if (element instanceof HTMLInputElement) {
    const labels = element.labels;
    if (labels && labels.length > 0) {
      return labels[0].textContent || "";
    }
  }

  // Check title attribute
  const title = element.getAttribute("title");
  if (title) return title;

  // Check placeholder for inputs
  if (element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement) {
    const placeholder = element.getAttribute("placeholder");
    if (placeholder) return placeholder;
  }

  // Fallback to text content
  return element.textContent || "";
}

/**
 * Validate color contrast ratio
 * @param foreground - Foreground color in hex format
 * @param background - Background color in hex format
 * @returns Contrast ratio
 */
export function getContrastRatio(foreground: string, background: string): number {
  const getLuminance = (color: string): number => {
    // Remove # if present
    color = color.replace("#", "");

    // Convert to RGB
    const r = parseInt(color.substr(0, 2), 16) / 255;
    const g = parseInt(color.substr(2, 2), 16) / 255;
    const b = parseInt(color.substr(4, 2), 16) / 255;

    // Calculate relative luminance
    const [rs, gs, bs] = [r, g, b].map((c) => {
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });

    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
  };

  const l1 = getLuminance(foreground);
  const l2 = getLuminance(background);

  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);

  return (lighter + 0.05) / (darker + 0.05);
}

/**
 * Check if contrast ratio meets WCAG standards
 */
export function meetsContrastRequirement(
  foreground: string,
  background: string,
  level: "AA" | "AAA" = "AA",
  isLargeText: boolean = false
): boolean {
  const ratio = getContrastRatio(foreground, background);

  if (level === "AAA") {
    return isLargeText ? ratio >= 4.5 : ratio >= 7;
  }

  // AA level
  return isLargeText ? ratio >= 3 : ratio >= 4.5;
}

/**
 * React hook for managing ARIA live regions
 */
export function useAriaLive() {
  const announce = (message: string, priority: "polite" | "assertive" = "polite") => {
    announceToScreenReader(message, priority);
  };

  return { announce };
}

/**
 * React hook for keyboard navigation
 */
export function useKeyboardNavigation<T = unknown>(
  items: T[],
  onSelect: (item: T, index: number) => void
) {
  const [selectedIndex, setSelectedIndex] = React.useState(0);

  const handleKeyDown = (event: React.KeyboardEvent) => {
    switch (event.key) {
      case "ArrowDown":
        event.preventDefault();
        setSelectedIndex((prev) => Math.min(prev + 1, items.length - 1));
        break;
      case "ArrowUp":
        event.preventDefault();
        setSelectedIndex((prev) => Math.max(prev - 1, 0));
        break;
      case "Enter":
      case " ":
        event.preventDefault();
        onSelect(items[selectedIndex], selectedIndex);
        break;
      case "Home":
        event.preventDefault();
        setSelectedIndex(0);
        break;
      case "End":
        event.preventDefault();
        setSelectedIndex(items.length - 1);
        break;
    }
  };

  return { selectedIndex, handleKeyDown, setSelectedIndex };
}

// Add React import at the top
import React from "react";
