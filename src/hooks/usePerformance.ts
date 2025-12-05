/**
 * Performance Hooks
 * 
 * React hooks for performance monitoring and optimization.
 * 
 * Requirements: 14.3
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import { performanceMonitor, FPSCounter, getMemoryUsage } from '../lib/performance';

/**
 * Hook to measure component render time
 */
export function useRenderTime(componentName: string) {
  const renderCount = useRef(0);
  const [count, setCount] = useState(0);

  useEffect(() => {
    renderCount.current++;
    setCount(renderCount.current);
    const renderTime = performance.now();
    const currentCount = renderCount.current;

    return () => {
      const duration = performance.now() - renderTime;
      performanceMonitor.measure(`${componentName}-render-${currentCount}`, () => duration);
    };
  }, [componentName]);

  return count;
}

/**
 * Hook to track FPS
 */
export function useFPS() {
  const [fps, setFps] = useState(60);
  const counterRef = useRef<FPSCounter | null>(null);

  useEffect(() => {
    counterRef.current = new FPSCounter();
    counterRef.current.start(setFps);

    return () => {
      counterRef.current?.stop();
    };
  }, []);

  return fps;
}

/**
 * Hook to track memory usage
 */
export function useMemoryUsage(interval: number = 1000) {
  const [memory, setMemory] = useState<ReturnType<typeof getMemoryUsage>>(null);

  useEffect(() => {
    const updateMemory = () => {
      setMemory(getMemoryUsage());
    };

    updateMemory();
    const intervalId = setInterval(updateMemory, interval);

    return () => clearInterval(intervalId);
  }, [interval]);

  return memory;
}

/**
 * Hook to measure async operation time
 */
export function useAsyncMeasure() {
  return useCallback(async <T,>(name: string, fn: () => Promise<T>): Promise<T> => {
    return performanceMonitor.measureAsync(name, fn);
  }, []);
}

/**
 * Hook to get performance stats
 */
export function usePerformanceStats(metricName?: string) {
  const [stats, setStats] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    const updateStats = () => {
      if (metricName) {
        setStats(performanceMonitor.getStats(metricName));
      } else {
        setStats(performanceMonitor.getAllStats());
      }
    };

    updateStats();
    const intervalId = setInterval(updateStats, 1000);

    return () => clearInterval(intervalId);
  }, [metricName]);

  return stats;
}

/**
 * Hook to detect slow renders
 */
export function useSlowRenderDetection(threshold: number = 16.67) {
  const [initialTime] = useState(() => performance.now());
  const lastRenderTime = useRef(initialTime);
  const [slowRenders, setSlowRenders] = useState(0);

  useEffect(() => {
    const renderDuration = performance.now() - lastRenderTime.current;
    lastRenderTime.current = performance.now();

    if (renderDuration > threshold) {
      // Use a callback to avoid triggering cascading renders
      setTimeout(() => {
        setSlowRenders(prev => prev + 1);
        console.warn(`Slow render detected: ${renderDuration.toFixed(2)}ms`);
      }, 0);
    }
  }, [threshold]);

  return slowRenders;
}

/**
 * Hook for performance profiling in development
 */
export function usePerformanceProfile(componentName: string, enabled: boolean = process.env.NODE_ENV === 'development') {
  const renderCount = useRef(0);
  const mountTime = useRef(performance.now());

  useEffect(() => {
    if (!enabled) return;

    renderCount.current++;
    const renderStart = performance.now();
    const currentCount = renderCount.current;

    return () => {
      const renderDuration = performance.now() - renderStart;

      if (renderDuration > 16.67) {
        console.warn(`[${componentName}] Slow render #${currentCount}: ${renderDuration.toFixed(2)}ms`);
      }
    };
  });

  useEffect(() => {
    if (!enabled) return;

    const mountTimeValue = mountTime.current;
    const renderCountValue = renderCount.current;

    return () => {
      const totalTime = performance.now() - mountTimeValue;
      console.log(`[${componentName}] Total lifetime: ${totalTime.toFixed(2)}ms, Renders: ${renderCountValue}`);
    };
  }, [componentName, enabled]);
}
