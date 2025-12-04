import { useState, useEffect } from "react";

/**
 * Hook for responsive design - detects media query matches
 */
export const useMediaQuery = (query: string): boolean => {
  const [matches, setMatches] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.matchMedia(query).matches;
    }
    return false;
  });

  useEffect(() => {
    const media = window.matchMedia(query);

    // Set initial value
    // setMatches(media.matches); // Removed to avoid set-state-in-effect

    // Create listener
    const listener = (e: MediaQueryListEvent) => {
      setMatches(e.matches);
    };

    // Add listener
    if (media.addEventListener) {
      media.addEventListener("change", listener);
    } else {
      // Fallback for older browsers
      media.addListener(listener);
    }

    // Cleanup
    return () => {
      if (media.removeEventListener) {
        media.removeEventListener("change", listener);
      } else {
        media.removeListener(listener);
      }
    };
  }, [query]);

  return matches;
};

/**
 * Predefined breakpoint hooks
 */
export const useIsMobile = () => useMediaQuery("(max-width: 768px)");
export const useIsTablet = () =>
  useMediaQuery("(min-width: 769px) and (max-width: 1024px)");
export const useIsDesktop = () => useMediaQuery("(min-width: 1025px)");
export const useIsLargeScreen = () => useMediaQuery("(min-width: 1440px)");

/**
 * Hook for detecting reduced motion preference
 */
export const usePrefersReducedMotion = () => {
  return useMediaQuery("(prefers-reduced-motion: reduce)");
};

/**
 * Hook for detecting dark mode preference
 */
export const usePrefersDarkMode = () => {
  return useMediaQuery("(prefers-color-scheme: dark)");
};
