/**
 * Performance Utilities
 * 
 * Utilities for performance monitoring, profiling, and optimization.
 * Implements requestAnimationFrame for smooth animations and performance tracking.
 * 
 * Requirements: 14.3
 */

// Performance monitoring
export class PerformanceMonitor {
  private metrics: Map<string, number[]> = new Map();
  private observers: PerformanceObserver[] = [];

  constructor() {
    this.initializeObservers();
  }

  private initializeObservers() {
    // Monitor long tasks
    if ('PerformanceObserver' in window) {
      try {
        const longTaskObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            console.warn('Long task detected:', {
              duration: entry.duration,
              startTime: entry.startTime,
              name: entry.name
            });
          }
        });
        longTaskObserver.observe({ entryTypes: ['longtask'] });
        this.observers.push(longTaskObserver);
      } catch (e) {
        // longtask not supported in all browsers
      }

      // Monitor layout shifts
      try {
        const layoutShiftObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            const cls = entry as any;
            if (cls.hadRecentInput) continue;
            console.warn('Layout shift detected:', {
              value: cls.value,
              sources: cls.sources
            });
          }
        });
        layoutShiftObserver.observe({ entryTypes: ['layout-shift'] });
        this.observers.push(layoutShiftObserver);
      } catch (e) {
        // layout-shift not supported in all browsers
      }
    }
  }

  /**
   * Measure execution time of a function
   */
  measure<T>(name: string, fn: () => T): T {
    const start = performance.now();
    const result = fn();
    const duration = performance.now() - start;
    
    this.recordMetric(name, duration);
    
    if (duration > 16.67) { // More than one frame (60fps)
      console.warn(`Slow operation: ${name} took ${duration.toFixed(2)}ms`);
    }
    
    return result;
  }

  /**
   * Measure async function execution time
   */
  async measureAsync<T>(name: string, fn: () => Promise<T>): Promise<T> {
    const start = performance.now();
    const result = await fn();
    const duration = performance.now() - start;
    
    this.recordMetric(name, duration);
    
    if (duration > 100) {
      console.warn(`Slow async operation: ${name} took ${duration.toFixed(2)}ms`);
    }
    
    return result;
  }

  private recordMetric(name: string, duration: number) {
    if (!this.metrics.has(name)) {
      this.metrics.set(name, []);
    }
    const metrics = this.metrics.get(name)!;
    metrics.push(duration);
    
    // Keep only last 100 measurements
    if (metrics.length > 100) {
      metrics.shift();
    }
  }

  /**
   * Get statistics for a metric
   */
  getStats(name: string) {
    const metrics = this.metrics.get(name);
    if (!metrics || metrics.length === 0) {
      return null;
    }

    const sorted = [...metrics].sort((a, b) => a - b);
    const sum = metrics.reduce((a, b) => a + b, 0);
    
    return {
      count: metrics.length,
      avg: sum / metrics.length,
      min: sorted[0],
      max: sorted[sorted.length - 1],
      p50: sorted[Math.floor(sorted.length * 0.5)],
      p95: sorted[Math.floor(sorted.length * 0.95)],
      p99: sorted[Math.floor(sorted.length * 0.99)]
    };
  }

  /**
   * Get all metrics
   */
  getAllStats() {
    const stats: Record<string, any> = {};
    for (const [name] of this.metrics) {
      stats[name] = this.getStats(name);
    }
    return stats;
  }

  /**
   * Clear all metrics
   */
  clear() {
    this.metrics.clear();
  }

  /**
   * Cleanup observers
   */
  destroy() {
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
  }
}

// Global performance monitor instance
export const performanceMonitor = new PerformanceMonitor();

/**
 * RequestAnimationFrame utilities for smooth animations
 */
export class AnimationScheduler {
  private rafId: number | null = null;
  private callbacks: Set<(timestamp: number) => void> = new Set();

  /**
   * Schedule a callback to run on the next animation frame
   */
  schedule(callback: (timestamp: number) => void): () => void {
    this.callbacks.add(callback);
    
    if (!this.rafId) {
      this.rafId = requestAnimationFrame(this.tick);
    }

    // Return cleanup function
    return () => {
      this.callbacks.delete(callback);
      if (this.callbacks.size === 0 && this.rafId) {
        cancelAnimationFrame(this.rafId);
        this.rafId = null;
      }
    };
  }

  private tick = (timestamp: number) => {
    // Execute all callbacks
    this.callbacks.forEach(callback => {
      try {
        callback(timestamp);
      } catch (error) {
        console.error('Animation callback error:', error);
      }
    });

    // Schedule next frame if there are still callbacks
    if (this.callbacks.size > 0) {
      this.rafId = requestAnimationFrame(this.tick);
    } else {
      this.rafId = null;
    }
  };

  /**
   * Clear all scheduled callbacks
   */
  clear() {
    if (this.rafId) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
    this.callbacks.clear();
  }
}

// Global animation scheduler
export const animationScheduler = new AnimationScheduler();

/**
 * Throttle function using requestAnimationFrame
 */
export function throttleRAF<T extends (...args: any[]) => void>(
  callback: T
): (...args: Parameters<T>) => void {
  let rafId: number | null = null;
  let lastArgs: Parameters<T> | null = null;

  return (...args: Parameters<T>) => {
    lastArgs = args;
    
    if (rafId === null) {
      rafId = requestAnimationFrame(() => {
        if (lastArgs) {
          callback(...lastArgs);
        }
        rafId = null;
        lastArgs = null;
      });
    }
  };
}

/**
 * Debounce function with requestAnimationFrame
 */
export function debounceRAF<T extends (...args: any[]) => void>(
  callback: T,
  frames: number = 1
): (...args: Parameters<T>) => void {
  let rafId: number | null = null;
  let frameCount = 0;
  let lastArgs: Parameters<T> | null = null;

  const tick = () => {
    frameCount++;
    
    if (frameCount >= frames) {
      if (lastArgs) {
        callback(...lastArgs);
      }
      rafId = null;
      frameCount = 0;
      lastArgs = null;
    } else {
      rafId = requestAnimationFrame(tick);
    }
  };

  return (...args: Parameters<T>) => {
    lastArgs = args;
    frameCount = 0;
    
    if (rafId === null) {
      rafId = requestAnimationFrame(tick);
    }
  };
}

/**
 * Smooth scroll using requestAnimationFrame
 */
export function smoothScroll(
  element: HTMLElement,
  targetY: number,
  duration: number = 300
): Promise<void> {
  return new Promise((resolve) => {
    const startY = element.scrollTop;
    const distance = targetY - startY;
    const startTime = performance.now();

    const tick = (currentTime: number) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      // Easing function (ease-in-out)
      const eased = progress < 0.5
        ? 2 * progress * progress
        : 1 - Math.pow(-2 * progress + 2, 2) / 2;
      
      element.scrollTop = startY + distance * eased;
      
      if (progress < 1) {
        requestAnimationFrame(tick);
      } else {
        resolve();
      }
    };

    requestAnimationFrame(tick);
  });
}

/**
 * Batch DOM updates using requestAnimationFrame
 */
export class DOMBatcher {
  private readCallbacks: Set<() => void> = new Set();
  private writeCallbacks: Set<() => void> = new Set();
  private rafId: number | null = null;

  /**
   * Schedule a DOM read operation
   */
  read(callback: () => void) {
    this.readCallbacks.add(callback);
    this.scheduleFlush();
  }

  /**
   * Schedule a DOM write operation
   */
  write(callback: () => void) {
    this.writeCallbacks.add(callback);
    this.scheduleFlush();
  }

  private scheduleFlush() {
    if (this.rafId === null) {
      this.rafId = requestAnimationFrame(() => {
        this.flush();
      });
    }
  }

  private flush() {
    // Execute all reads first
    this.readCallbacks.forEach(callback => {
      try {
        callback();
      } catch (error) {
        console.error('DOM read error:', error);
      }
    });
    this.readCallbacks.clear();

    // Then execute all writes
    this.writeCallbacks.forEach(callback => {
      try {
        callback();
      } catch (error) {
        console.error('DOM write error:', error);
      }
    });
    this.writeCallbacks.clear();

    this.rafId = null;
  }
}

// Global DOM batcher
export const domBatcher = new DOMBatcher();

/**
 * FPS counter
 */
export class FPSCounter {
  private frames: number[] = [];
  private rafId: number | null = null;
  private callback: ((fps: number) => void) | null = null;

  start(callback: (fps: number) => void) {
    this.callback = callback;
    this.frames = [];
    this.tick(performance.now());
  }

  private tick = (timestamp: number) => {
    this.frames.push(timestamp);
    
    // Keep only last second of frames
    const oneSecondAgo = timestamp - 1000;
    this.frames = this.frames.filter(t => t > oneSecondAgo);
    
    if (this.callback) {
      this.callback(this.frames.length);
    }
    
    this.rafId = requestAnimationFrame(this.tick);
  };

  stop() {
    if (this.rafId) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
    this.callback = null;
    this.frames = [];
  }
}

/**
 * Memory usage tracker
 */
export function getMemoryUsage() {
  if ('memory' in performance) {
    const memory = (performance as any).memory;
    return {
      usedJSHeapSize: memory.usedJSHeapSize,
      totalJSHeapSize: memory.totalJSHeapSize,
      jsHeapSizeLimit: memory.jsHeapSizeLimit,
      usedPercent: (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100
    };
  }
  return null;
}

/**
 * Log performance metrics to console
 */
export function logPerformanceMetrics() {
  console.group('Performance Metrics');
  
  // Navigation timing
  if (performance.timing) {
    const timing = performance.timing;
    console.log('Page Load:', timing.loadEventEnd - timing.navigationStart, 'ms');
    console.log('DOM Ready:', timing.domContentLoadedEventEnd - timing.navigationStart, 'ms');
  }

  // Memory usage
  const memory = getMemoryUsage();
  if (memory) {
    console.log('Memory Usage:', {
      used: `${(memory.usedJSHeapSize / 1024 / 1024).toFixed(2)} MB`,
      total: `${(memory.totalJSHeapSize / 1024 / 1024).toFixed(2)} MB`,
      limit: `${(memory.jsHeapSizeLimit / 1024 / 1024).toFixed(2)} MB`,
      percent: `${memory.usedPercent.toFixed(2)}%`
    });
  }

  // Custom metrics
  const stats = performanceMonitor.getAllStats();
  if (Object.keys(stats).length > 0) {
    console.log('Custom Metrics:', stats);
  }

  console.groupEnd();
}
