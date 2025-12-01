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

  it('should schedule callbacks', (done) => {
    let called = false;
    
    scheduler.schedule(() => {
      called = true;
      expect(called).toBe(true);
      done();
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

  it('should handle multiple callbacks', (done) => {
    let count = 0;
    
    scheduler.schedule(() => count++);
    scheduler.schedule(() => count++);
    scheduler.schedule(() => {
      count++;
      expect(count).toBe(3);
      done();
    });
  });
});

describe('throttleRAF', () => {
  it('should throttle function calls', (done) => {
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
      done();
    }, 50);
  });
});

describe('debounceRAF', () => {
  it('should debounce function calls', (done) => {
    let callCount = 0;
    const debounced = debounceRAF(() => {
      callCount++;
    }, 2);

    // Call multiple times
    debounced();
    debounced();
    debounced();

    // Should only execute once after frames
    setTimeout(() => {
      expect(callCount).toBe(1);
      done();
    }, 100);
  });
});

describe('DOMBatcher', () => {
  let batcher: DOMBatcher;

  beforeEach(() => {
    batcher = new DOMBatcher();
  });

  it('should batch read operations', (done) => {
    let readExecuted = false;
    
    batcher.read(() => {
      readExecuted = true;
    });

    setTimeout(() => {
      expect(readExecuted).toBe(true);
      done();
    }, 20);
  });

  it('should batch write operations', (done) => {
    let writeExecuted = false;
    
    batcher.write(() => {
      writeExecuted = true;
    });

    setTimeout(() => {
      expect(writeExecuted).toBe(true);
      done();
    }, 20);
  });

  it('should execute reads before writes', (done) => {
    const order: string[] = [];
    
    batcher.write(() => order.push('write'));
    batcher.read(() => order.push('read'));

    setTimeout(() => {
      expect(order).toEqual(['read', 'write']);
      done();
    }, 20);
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

  it('should track FPS', (done) => {
    let fps = 0;
    
    counter.start((currentFps) => {
      fps = currentFps;
    });

    setTimeout(() => {
      expect(fps).toBeGreaterThan(0);
      expect(fps).toBeLessThanOrEqual(60);
      done();
    }, 1100); // Wait just over 1 second
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
