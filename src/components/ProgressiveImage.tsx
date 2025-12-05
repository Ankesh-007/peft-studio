/**
 * Progressive Image Component
 * Loads images progressively with low-quality placeholder
 */

import React, { useState, useEffect } from "react";
import { cn } from "../lib/utils";

interface ProgressiveImageProps {
  src: string;
  placeholderSrc?: string;
  alt: string;
  className?: string;
  width?: number;
  height?: number;
  onLoad?: () => void;
  onError?: (error: Error) => void;
}

export const ProgressiveImage: React.FC<ProgressiveImageProps> = ({
  src,
  placeholderSrc,
  alt,
  className,
  width,
  height,
  onLoad,
  onError,
}) => {
  const [currentSrc, setCurrentSrc] = useState(placeholderSrc || src);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    // Create image object to preload
    const img = new Image();

    img.onload = () => {
      setCurrentSrc(src);
      setLoading(false);
      onLoad?.();
    };

    img.onerror = () => {
      setError(true);
      setLoading(false);
      onError?.(new Error(`Failed to load image: ${src}`));
    };

    img.src = src;

    return () => {
      img.onload = null;
      img.onerror = null;
    };
  }, [src, onLoad, onError]);

  if (error) {
    return (
      <div
        className={cn("flex items-center justify-center bg-gray-100 text-gray-400", className)}
        style={{ width, height }}
        role="img"
        aria-label={alt}
      >
        <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
          />
        </svg>
      </div>
    );
  }

  return (
    <img
      src={currentSrc}
      alt={alt}
      width={width}
      height={height}
      className={cn(
        "transition-opacity duration-300",
        loading && placeholderSrc ? "opacity-50 blur-sm" : "opacity-100",
        className
      )}
      loading="lazy"
    />
  );
};

/**
 * Generate placeholder image URL (base64 encoded tiny image)
 */
export function generatePlaceholder(
  width: number,
  height: number,
  color: string = "#e5e7eb"
): string {
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;

  const ctx = canvas.getContext("2d");
  if (ctx) {
    ctx.fillStyle = color;
    ctx.fillRect(0, 0, width, height);
  }

  return canvas.toDataURL();
}
