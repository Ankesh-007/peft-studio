/**
 * Performance Utilities Tests
 * 
 * Tests for performance monitoring and optimization utilities.
 * 
 * Requirements: 14.3
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
  PerformanceMonitor,
  AnimationScheduler,
  throttleRAF,
  debounceRAF,
  DOMBatcher,
  FPSCounter
} from '../../lib/performance';

describe('PerformanceMonitor', () => {
  let monitor: PerformanceMonitor;

  beforeEach(() => {
    monitor = new PerformanceMonitor();
  });

  afterEach(() => {
    monitor.destroy();
  });

  it('should measure sync function execution time', () => {
    const result = monitor.measure('test-sync', () => {
      let sum = 0;
      for (let i = 0; i < 1000; i++) {
        sum += i;
      }
      return sum;
    });

    expect(result).toBe(499500);
    
    const stats = monitor.getStats('test-sync');
    expect(stats).toBeDefined();
    expect(stats!.count).toBe(1);
    expect(stats!.avg).toBeGreaterThan(0);
  });

  it('should measure async function execution time', async () => {
    const result = await monitor.measureAsync('test-async', async () => {
      await new Promise(resolve => setTimeout(resolve, 10));
      return 'done';
    });

    expect(result).toBe('done');
    
    const stats = monitor.getStats('test-async');
    expect(stats).toBeDefined();
    expect(stats!.count).toBe(1);
    expect(stats!.avg).toBeGreaterThanOrEqual(10);
  });

  it('should calculate statistics correctly', () => {
    // Record multiple measurements
    for (let i = 0; i < 10; i++) {
      monitor.measure('test-stats', () => i * 10);
    }

    const stats = monitor.getStats('test-stats');
    expect(stats).toBeDefined();
    expect(stats!.count).toBe(10);
    expect(stats!.min).toBeGreaterThanOrEqual(0);
    expect(stats!.max).toBeGreaterThan(0);
    expect(stats!.avg).toBeGreaterThan(0);
  });

  it('should clear metrics', () => {
    monitor.measure('test-clear', () => 42);
    expect(monitor.getStats('test-clear')).toBeDefined();
    
    monitor.clear();
    expect(monitor.getStats('test-clear')).toBeNull();
  });

  it('should get all stats', () => {
    monitor.measure('metric1', () => 1);
    monitor.measure('metric2', () => 2);
    
    const allStats = monitor.getAllStats();
    expect(Object.keys(allStats)).toContain('metric1');
    expect(Object.keys(allStats)).toContain('metric2');
  });
});

describe('AnimationScheduler', () => {
  let scheduler: AnimationScheduler;

  beforeEach(() => {
    scheduler = new AnimationScheduler();
  });

  afterEach(() => {
    scheduler.clear();
  });

  it('should schedule callbacks', () => {
    return new Promise<void>((resolve) => {
      let called = false;
      
      scheduler.schedule(() => {
        called = true;
        expect(called).toBe(true);
        resolve();
      });
    });
  });

  it('should return cleanup function', () => {
    const callback = vi.fn();
    const cleanup = scheduler.schedule(callback);
    
    cleanup();
    
    // Wait a frame to ensure callback wasn't called
    setTimeout(() => {
      expect(callback).not.toHaveBeenCalled();
    }, 20);
  });

  it('should handle multiple callbacks', () => {
    return new Promise<void>((resolve) => {
      let count = 0;
      
      scheduler.schedule(() => count++);
      scheduler.schedule(() => count++);
      scheduler.schedule(() => {
        count++;
        expect(count).toBe(3);
        resolve();
      });
    });
  });
});

describe('throttleRAF', () => {
  it('should throttle function calls', () => {
    return new Promise<void>((resolve) => {
      let callCount = 0;
      const throttled = throttleRAF(() => {
        callCount++;
      });

      // Call multiple times rapidly
      throttled();
      throttled();
      throttled();

      // Should only execute once per frame
      setTimeout(() => {
        expect(callCount).toBeLessThanOrEqual(2);
        resolve();
      }, 50);
    });
  });
});

describe('debounceRAF', () => {
  it('should debounce function calls', async () => {
    let callCount = 0;
    const debounced = debounceRAF(() => {
      callCount++;
    }, 2);

    // Call multiple times
    debounced();
    debounced();
    debounced();

    // Should only execute once after frames
    await new Promise(resolve => setTimeout(resolve, 100));
    expect(callCount).toBe(1);
  });
});

describe('DOMBatcher', () => {
  let batcher: DOMBatcher;

  beforeEach(() => {
    batcher = new DOMBatcher();
  });

  it('should batch read operations', async () => {
    let readExecuted = false;
    
    batcher.read(() => {
      readExecuted = true;
    });

    await new Promise(resolve => setTimeout(resolve, 20));
    expect(readExecuted).toBe(true);
  });

  it('should batch write operations', async () => {
    let writeExecuted = false;
    
    batcher.write(() => {
      writeExecuted = true;
    });

    await new Promise(resolve => setTimeout(resolve, 20));
    expect(writeExecuted).toBe(true);
  });

  it('should execute reads before writes', async () => {
    const order: string[] = [];
    
    batcher.write(() => order.push('write'));
    batcher.read(() => order.push('read'));

    await new Promise(resolve => setTimeout(resolve, 20));
    expect(order).toEqual(['read', 'write']);
  });
});

describe('FPSCounter', () => {
  let counter: FPSCounter;

  beforeEach(() => {
    counter = new FPSCounter();
  });

  afterEach(() => {
    counter.stop();
  });

  it('should track FPS', async () => {
    let fps = 0;
    
    counter.start((currentFps) => {
      fps = currentFps;
    });

    await new Promise(resolve => setTimeout(resolve, 1100)); // Wait just over 1 second
    expect(fps).toBeGreaterThan(0);
    expect(fps).toBeLessThanOrEqual(60);
  });

  it('should stop tracking', () => {
    const callback = vi.fn();
    counter.start(callback);
    counter.stop();
    
    // Callback should not be called after stop
    setTimeout(() => {
      const callCount = callback.mock.calls.length;
      setTimeout(() => {
        expect(callback.mock.calls.length).toBe(callCount);
      }, 100);
    }, 100);
  });
});
