import React, { useEffect, useState } from "react";

import { usePrefersReducedMotion } from "../hooks/useMediaQuery";
import { cn } from "../lib/utils";

interface AnimatedTransitionProps {
  children: React.ReactNode;
  show: boolean;
  type?: "fade" | "slide-up" | "slide-down" | "scale";
  duration?: number;
  className?: string;
}

/**
 * Animated transition wrapper that respects reduced motion preferences
 */
export const AnimatedTransition: React.FC<AnimatedTransitionProps> = ({
  children,
  show,
  type = "fade",
  duration = 300,
  className,
}) => {
  const [shouldRender, setShouldRender] = useState(show);
  const [isVisible, setIsVisible] = useState(false);
  const prefersReducedMotion = usePrefersReducedMotion();

  useEffect(() => {
    if (show) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setShouldRender(true);
      // Trigger animation after render
      requestAnimationFrame(() => {
        setIsVisible(true);
      });
    } else {
      setIsVisible(false);
      // Wait for animation to complete before unmounting
      const timer = setTimeout(
        () => {
          setShouldRender(false);
        },
        prefersReducedMotion ? 0 : duration,
      );
      return () => clearTimeout(timer);
    }
  }, [show, duration, prefersReducedMotion]);

  if (!shouldRender) return null;

  const getTransitionClasses = () => {
    const baseClasses = prefersReducedMotion
      ? ""
      : `transition-all duration-${duration}`;

    const typeClasses = {
      fade: isVisible ? "opacity-100" : "opacity-0",
      "slide-up": isVisible
        ? "opacity-100 translate-y-0"
        : "opacity-0 translate-y-4",
      "slide-down": isVisible
        ? "opacity-100 translate-y-0"
        : "opacity-0 -translate-y-4",
      scale: isVisible ? "opacity-100 scale-100" : "opacity-0 scale-95",
    };

    return cn(baseClasses, typeClasses[type], className);
  };

  return <div className={getTransitionClasses()}>{children}</div>;
};

interface StaggeredListProps {
  children: React.ReactNode[];
  staggerDelay?: number;
  className?: string;
}

/**
 * Staggered animation for list items
 */
export const StaggeredList: React.FC<StaggeredListProps> = ({
  children,
  staggerDelay = 50,
  className,
}) => {
  const prefersReducedMotion = usePrefersReducedMotion();

  return (
    <div className={className}>
      {React.Children.map(children, (child, index) => (
        <div
          className={cn(!prefersReducedMotion && "animate-fade-in")}
          style={{
            animationDelay: prefersReducedMotion
              ? "0ms"
              : `${index * staggerDelay}ms`,
          }}
        >
          {child}
        </div>
      ))}
    </div>
  );
};

interface PulseProps {
  children: React.ReactNode;
  active?: boolean;
  className?: string;
}

/**
 * Pulse animation for attention-grabbing elements
 */
export const Pulse: React.FC<PulseProps> = ({
  children,
  active = true,
  className,
}) => {
  const prefersReducedMotion = usePrefersReducedMotion();

  return (
    <div
      className={cn(
        active && !prefersReducedMotion && "animate-pulse",
        className,
      )}
    >
      {children}
    </div>
  );
};
