import { useEffect, useCallback } from "react";

import type { RefObject } from "react";

/**
 * Hook for managing keyboard navigation within a component
 */
export const useKeyboardNavigation = (
  containerRef: RefObject<HTMLElement>,
  options: {
    onEscape?: () => void;
    onEnter?: () => void;
    onArrowUp?: () => void;
    onArrowDown?: () => void;
    onArrowLeft?: () => void;
    onArrowRight?: () => void;
    onTab?: (shiftKey: boolean) => void;
    enabled?: boolean;
  } = {}
) => {
  const { enabled = true } = options;

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return;

      switch (event.key) {
        case "Escape":
          if (options.onEscape) {
            event.preventDefault();
            options.onEscape();
          }
          break;
        case "Enter":
          if (options.onEnter) {
            event.preventDefault();
            options.onEnter();
          }
          break;
        case "ArrowUp":
          if (options.onArrowUp) {
            event.preventDefault();
            options.onArrowUp();
          }
          break;
        case "ArrowDown":
          if (options.onArrowDown) {
            event.preventDefault();
            options.onArrowDown();
          }
          break;
        case "ArrowLeft":
          if (options.onArrowLeft) {
            event.preventDefault();
            options.onArrowLeft();
          }
          break;
        case "ArrowRight":
          if (options.onArrowRight) {
            event.preventDefault();
            options.onArrowRight();
          }
          break;
        case "Tab":
          if (options.onTab) {
            event.preventDefault();
            options.onTab(event.shiftKey);
          }
          break;
      }
    },
    [enabled, options]
  );

  useEffect(() => {
    const container = containerRef.current;
    if (!container || !enabled) return;

    container.addEventListener("keydown", handleKeyDown as EventListener);
    return () => {
      container.removeEventListener("keydown", handleKeyDown as EventListener);
    };
  }, [containerRef, handleKeyDown, enabled]);
};

/**
 * Hook for managing focus trap within a modal or dialog
 */
export const useFocusTrap = (containerRef: RefObject<HTMLElement>, enabled: boolean = true) => {
  useEffect(() => {
    if (!enabled) return;

    const container = containerRef.current;
    if (!container) return;

    const focusableElements = container.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key !== "Tab") return;

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement?.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement?.focus();
        }
      }
    };

    // Focus first element when trap is enabled
    firstElement?.focus();

    container.addEventListener("keydown", handleTabKey as EventListener);
    return () => {
      container.removeEventListener("keydown", handleTabKey as EventListener);
    };
  }, [containerRef, enabled]);
};

/**
 * Hook for managing roving tabindex in a list
 */
export const useRovingTabIndex = (
  itemsRef: RefObject<HTMLElement[]>,
  options: {
    orientation?: "horizontal" | "vertical";
    loop?: boolean;
  } = {}
) => {
  const { orientation = "vertical", loop = true } = options;

  const focusItem = useCallback(
    (index: number) => {
      const items = itemsRef.current;
      if (!items || !items[index]) return;

      items.forEach((item, i) => {
        item.setAttribute("tabindex", i === index ? "0" : "-1");
      });
      items[index].focus();
    },
    [itemsRef]
  );

  const handleKeyDown = useCallback(
    (event: KeyboardEvent, currentIndex: number) => {
      const items = itemsRef.current;
      if (!items) return;

      const isNext =
        (orientation === "vertical" && event.key === "ArrowDown") ||
        (orientation === "horizontal" && event.key === "ArrowRight");
      const isPrev =
        (orientation === "vertical" && event.key === "ArrowUp") ||
        (orientation === "horizontal" && event.key === "ArrowLeft");

      if (!isNext && !isPrev) return;

      event.preventDefault();

      let nextIndex = currentIndex;
      if (isNext) {
        nextIndex = currentIndex + 1;
        if (nextIndex >= items.length) {
          nextIndex = loop ? 0 : items.length - 1;
        }
      } else if (isPrev) {
        nextIndex = currentIndex - 1;
        if (nextIndex < 0) {
          nextIndex = loop ? items.length - 1 : 0;
        }
      }

      focusItem(nextIndex);
    },
    [itemsRef, orientation, loop, focusItem]
  );

  return { focusItem, handleKeyDown };
};
