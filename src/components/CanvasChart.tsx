/**
 * Canvas-based Chart Component
 *
 * High-performance chart rendering using HTML5 Canvas for large datasets.
 * Much faster than SVG-based charts for datasets with 1000+ points.
 *
 * Requirements: 14.3
 */

import React, { useRef, useEffect, memo, useMemo, useCallback } from "react";
import { throttleRAF } from "../lib/performance";

interface DataPoint {
  x: number;
  y: number;
  label?: string;
}

interface CanvasChartProps {
  data: DataPoint[];
  width?: number;
  height?: number;
  lineColor?: string;
  fillColor?: string;
  showGrid?: boolean;
  showAxes?: boolean;
  showPoints?: boolean;
  animate?: boolean;
  className?: string;
}

export const CanvasChart: React.FC<CanvasChartProps> = memo(
  ({
    data,
    width = 600,
    height = 300,
    lineColor = "#6366f1",
    fillColor = "rgba(99, 102, 241, 0.1)",
    showGrid = true,
    showAxes = true,
    showPoints = false,
    animate = true,
    className = "",
  }) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const animationRef = useRef<number | null>(null);
    const progressRef = useRef(0);

    // Calculate bounds
    const bounds = useMemo(() => {
      if (data.length === 0) {
        return { minX: 0, maxX: 1, minY: 0, maxY: 1 };
      }

      const xs = data.map((d) => d.x);
      const ys = data.map((d) => d.y);

      return {
        minX: Math.min(...xs),
        maxX: Math.max(...xs),
        minY: Math.min(...ys),
        maxY: Math.max(...ys),
      };
    }, [data]);

    // Scale functions
    const scaleX = useMemo(() => {
      const padding = 40;
      const range = bounds.maxX - bounds.minX || 1;
      return (x: number) => ((x - bounds.minX) / range) * (width - 2 * padding) + padding;
    }, [bounds, width]);

    const scaleY = useMemo(() => {
      const padding = 40;
      const range = bounds.maxY - bounds.minY || 1;
      return (y: number) => height - padding - ((y - bounds.minY) / range) * (height - 2 * padding);
    }, [bounds, height]);

    // Draw function
    const draw = useCallback(
      (ctx: CanvasRenderingContext2D, progress: number = 1) => {
        // Clear canvas
        ctx.clearRect(0, 0, width, height);

        // Set high DPI
        const dpr = window.devicePixelRatio || 1;
        ctx.scale(dpr, dpr);

        // Draw grid
        if (showGrid) {
          ctx.strokeStyle = "#e5e7eb";
          ctx.lineWidth = 1;
          ctx.setLineDash([5, 5]);

          // Vertical grid lines
          for (let i = 0; i <= 10; i++) {
            const x = 40 + (i / 10) * (width - 80);
            ctx.beginPath();
            ctx.moveTo(x, 40);
            ctx.lineTo(x, height - 40);
            ctx.stroke();
          }

          // Horizontal grid lines
          for (let i = 0; i <= 5; i++) {
            const y = 40 + (i / 5) * (height - 80);
            ctx.beginPath();
            ctx.moveTo(40, y);
            ctx.lineTo(width - 40, y);
            ctx.stroke();
          }

          ctx.setLineDash([]);
        }

        // Draw axes
        if (showAxes) {
          ctx.strokeStyle = "#374151";
          ctx.lineWidth = 2;

          // X axis
          ctx.beginPath();
          ctx.moveTo(40, height - 40);
          ctx.lineTo(width - 40, height - 40);
          ctx.stroke();

          // Y axis
          ctx.beginPath();
          ctx.moveTo(40, 40);
          ctx.lineTo(40, height - 40);
          ctx.stroke();
        }

        if (data.length === 0) return;

        // Calculate visible data points based on animation progress
        const visibleCount = Math.floor(data.length * progress);
        const visibleData = data.slice(0, visibleCount);

        if (visibleData.length === 0) return;

        // Draw fill area
        ctx.fillStyle = fillColor;
        ctx.beginPath();
        ctx.moveTo(scaleX(visibleData[0].x), height - 40);
        visibleData.forEach((point) => {
          ctx.lineTo(scaleX(point.x), scaleY(point.y));
        });
        ctx.lineTo(scaleX(visibleData[visibleData.length - 1].x), height - 40);
        ctx.closePath();
        ctx.fill();

        // Draw line
        ctx.strokeStyle = lineColor;
        ctx.lineWidth = 2;
        ctx.lineJoin = "round";
        ctx.lineCap = "round";
        ctx.beginPath();
        ctx.moveTo(scaleX(visibleData[0].x), scaleY(visibleData[0].y));
        visibleData.forEach((point) => {
          ctx.lineTo(scaleX(point.x), scaleY(point.y));
        });
        ctx.stroke();

        // Draw points
        if (showPoints) {
          ctx.fillStyle = lineColor;
          visibleData.forEach((point) => {
            ctx.beginPath();
            ctx.arc(scaleX(point.x), scaleY(point.y), 4, 0, Math.PI * 2);
            ctx.fill();
          });
        }

        // Reset scale
        ctx.setTransform(1, 0, 0, 1, 0, 0);
      },
      [data, width, height, lineColor, fillColor, showGrid, showAxes, showPoints, scaleX, scaleY]
    );

    // Animation loop
    useEffect(() => {
      const canvas = canvasRef.current;
      if (!canvas) return;

      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      // Set canvas size with device pixel ratio
      const dpr = window.devicePixelRatio || 1;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;

      if (animate && data.length > 0) {
        progressRef.current = 0;
        const startTime = performance.now();
        const duration = 1000; // 1 second animation

        const animationLoop = (currentTime: number) => {
          const elapsed = currentTime - startTime;
          progressRef.current = Math.min(elapsed / duration, 1);

          draw(ctx, progressRef.current);

          if (progressRef.current < 1) {
            animationRef.current = requestAnimationFrame(animationLoop);
          }
        };

        animationRef.current = requestAnimationFrame(animationLoop);
      } else {
        draw(ctx, 1);
      }

      return () => {
        if (animationRef.current) {
          cancelAnimationFrame(animationRef.current);
        }
      };
    }, [data, width, height, lineColor, fillColor, showGrid, showAxes, showPoints, animate, draw]);

    // Handle resize
    useEffect(() => {
      const handleResize = throttleRAF(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        const currentProgress = progressRef.current;
        draw(ctx, currentProgress);
      });

      window.addEventListener("resize", handleResize);
      return () => window.removeEventListener("resize", handleResize);
    }, [data, width, height, draw]);

    return <canvas ref={canvasRef} className={className} style={{ width, height }} />;
  }
);

CanvasChart.displayName = "CanvasChart";

/**
 * Canvas-based Bar Chart
 */
interface BarChartProps {
  data: Array<{ label: string; value: number; color?: string }>;
  width?: number;
  height?: number;
  animate?: boolean;
  className?: string;
}

export const CanvasBarChart: React.FC<BarChartProps> = memo(
  ({ data, width = 600, height = 300, animate = true, className = "" }) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const animationRef = useRef<number | null>(null);

    const maxValue = useMemo(() => {
      return Math.max(...data.map((d) => d.value), 1);
    }, [data]);

    const draw = useCallback(
      (ctx: CanvasRenderingContext2D, progress: number = 1) => {
        ctx.clearRect(0, 0, width, height);

        const dpr = window.devicePixelRatio || 1;
        ctx.scale(dpr, dpr);

        const padding = 40;
        const barWidth = (width - 2 * padding) / data.length - 10;
        const chartHeight = height - 2 * padding;

        data.forEach((item, index) => {
          const x = padding + index * ((width - 2 * padding) / data.length);
          const barHeight = (item.value / maxValue) * chartHeight * progress;
          const y = height - padding - barHeight;

          // Draw bar
          ctx.fillStyle = item.color || "#6366f1";
          ctx.fillRect(x, y, barWidth, barHeight);

          // Draw label
          ctx.fillStyle = "#374151";
          ctx.font = "12px sans-serif";
          ctx.textAlign = "center";
          ctx.fillText(item.label, x + barWidth / 2, height - padding + 20);

          // Draw value
          ctx.fillText(item.value.toFixed(0), x + barWidth / 2, y - 5);
        });

        ctx.setTransform(1, 0, 0, 1, 0, 0);
      },
      [data, width, height, maxValue]
    );

    useEffect(() => {
      const canvas = canvasRef.current;
      if (!canvas) return;

      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      const dpr = window.devicePixelRatio || 1;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;

      if (animate) {
        let progress = 0;
        const startTime = performance.now();
        const duration = 800;

        const animationLoop = (currentTime: number) => {
          const elapsed = currentTime - startTime;
          progress = Math.min(elapsed / duration, 1);

          // Ease out cubic
          const eased = 1 - Math.pow(1 - progress, 3);
          draw(ctx, eased);

          if (progress < 1) {
            animationRef.current = requestAnimationFrame(animationLoop);
          }
        };

        animationRef.current = requestAnimationFrame(animationLoop);
      } else {
        draw(ctx, 1);
      }

      return () => {
        if (animationRef.current) {
          cancelAnimationFrame(animationRef.current);
        }
      };
    }, [data, width, height, animate, draw]);

    return <canvas ref={canvasRef} className={className} style={{ width, height }} />;
  }
);

CanvasBarChart.displayName = "CanvasBarChart";

export default CanvasChart;
