import React from 'react';
import { cn } from '../lib/utils';
import { useIsMobile, useIsTablet, useIsDesktop } from '../hooks/useMediaQuery';

interface ResponsiveContainerProps {
  children: React.ReactNode;
  className?: string;
  mobileClassName?: string;
  tabletClassName?: string;
  desktopClassName?: string;
}

/**
 * Container that applies different styles based on screen size
 */
export const ResponsiveContainer: React.FC<ResponsiveContainerProps> = ({
  children,
  className,
  mobileClassName,
  tabletClassName,
  desktopClassName,
}) => {
  const isMobile = useIsMobile();
  const isTablet = useIsTablet();
  const isDesktop = useIsDesktop();

  const responsiveClass = isMobile
    ? mobileClassName
    : isTablet
    ? tabletClassName
    : desktopClassName;

  return (
    <div className={cn(className, responsiveClass)}>
      {children}
    </div>
  );
};

interface ResponsiveGridProps {
  children: React.ReactNode;
  className?: string;
  cols?: {
    mobile?: number;
    tablet?: number;
    desktop?: number;
  };
  gap?: number;
}

/**
 * Responsive grid that adjusts columns based on screen size
 */
export const ResponsiveGrid: React.FC<ResponsiveGridProps> = ({
  children,
  className,
  cols = { mobile: 1, tablet: 2, desktop: 4 },
  gap = 16,
}) => {
  const isMobile = useIsMobile();
  const isTablet = useIsTablet();

  const gridCols = isMobile
    ? cols.mobile
    : isTablet
    ? cols.tablet
    : cols.desktop;

  return (
    <div
      className={cn('grid', className)}
      style={{
        gridTemplateColumns: `repeat(${gridCols}, minmax(0, 1fr))`,
        gap: `${gap}px`,
      }}
    >
      {children}
    </div>
  );
};

/**
 * Show/hide content based on screen size
 */
export const ShowOnMobile: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isMobile = useIsMobile();
  return isMobile ? <>{children}</> : null;
};

export const HideOnMobile: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isMobile = useIsMobile();
  return !isMobile ? <>{children}</> : null;
};

export const ShowOnTablet: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isTablet = useIsTablet();
  return isTablet ? <>{children}</> : null;
};

export const ShowOnDesktop: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isDesktop = useIsDesktop();
  return isDesktop ? <>{children}</> : null;
};
