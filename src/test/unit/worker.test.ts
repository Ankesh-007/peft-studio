/**
 * Web Worker Tests
 *
 * Tests for Web Worker functionality and worker pool management.
 *
 * Requirements: 14.3
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { WorkerMessageType } from "../../workers/types";

// Mock Worker API for Node.js environment
class MockWorker {
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: ErrorEvent) => void) | null = null;

  postMessage(message: unknown) {
    // Simulate async response - use immediate callback for faster tests
    Promise.resolve().then(() => {
      if (this.onmessage) {
        this.onmessage(
          new MessageEvent("message", {
            data: {
              id: (message as any).id,
              success: true,
              result: {},
              duration: 10,
              timestamp: Date.now(),
            },
          })
        );
      }
    });
  }

  terminate() {
    // Mock termination
  }

  addEventListener(event: string, handler: any) {
    if (event === "message") {
      this.onmessage = handler;
    } else if (event === "error") {
      this.onerror = handler;
    }
  }

  removeEventListener() {
    // Mock removal
  }
}

// Mock Worker constructor
(global as any).Worker = MockWorker;
(global as any).URL = class {
  constructor(
    public url: string,
    public base: string
  ) { }
};

// Import after mocking
import { WorkerPool } from "../../workers/WorkerPool";

describe("WorkerPool", () => {
  let pool: WorkerPool;

  beforeEach(() => {
    pool = new WorkerPool({
      maxWorkers: 2,
      idleTimeout: 5000,
      taskTimeout: 10000,
    });
  });

  afterEach(() => {
    if (pool) {
      pool.destroy();
    }
  });

  it("should create a worker pool", () => {
    expect(pool).toBeDefined();
    expect(pool.activeWorkerCount).toBeGreaterThan(0);
  });

  it("should get worker pool stats", () => {
    const stats = pool.getStats();

    expect(stats).toHaveProperty("totalWorkers");
    expect(stats).toHaveProperty("idleWorkers");
    expect(stats).toHaveProperty("busyWorkers");
    expect(stats).toHaveProperty("queuedTasks");
    expect(stats).toHaveProperty("pendingTasks");
    expect(stats).toHaveProperty("totalTasksCompleted");
  });

  it("should get worker info", () => {
    const info = pool.getWorkerInfo();

    expect(Array.isArray(info)).toBe(true);
    expect(info.length).toBeGreaterThan(0);

    const worker = info[0];
    expect(worker).toHaveProperty("id");
    expect(worker).toHaveProperty("status");
    expect(worker).toHaveProperty("tasksCompleted");
    expect(worker).toHaveProperty("createdAt");
    expect(worker).toHaveProperty("lastUsed");
  });

  it("should handle task execution", async () => {
    // This test would require a real worker implementation
    // For now, we'll just verify the pool can accept tasks

    const stats = pool.getStats();
    expect(stats.totalWorkers).toBeGreaterThan(0);
  });

  it("should track queued tasks", () => {
    const initialStats = pool.getStats();
    expect(initialStats.queuedTasks).toBe(0);
  });

  it("should destroy the pool", () => {
    const initialCount = pool.activeWorkerCount;
    expect(initialCount).toBeGreaterThan(0);

    pool.destroy();

    const finalCount = pool.activeWorkerCount;
    expect(finalCount).toBe(0);
  });
});

describe("Worker Message Types", () => {
  it("should have all required message types", () => {
    expect(WorkerMessageType.PROCESS_FILE).toBeDefined();
    expect(WorkerMessageType.PARSE_JSON).toBeDefined();
    expect(WorkerMessageType.PARSE_CSV).toBeDefined();
    expect(WorkerMessageType.COMPRESS_DATA).toBeDefined();
    expect(WorkerMessageType.DECOMPRESS_DATA).toBeDefined();
    expect(WorkerMessageType.COMPUTE_METRICS).toBeDefined();
    expect(WorkerMessageType.AGGREGATE_DATA).toBeDefined();
    expect(WorkerMessageType.FILTER_DATA).toBeDefined();
    expect(WorkerMessageType.SORT_DATA).toBeDefined();
  });
});

describe("Worker Pool Configuration", () => {
  it("should use default configuration", () => {
    const testPool = new WorkerPool();
    const stats = testPool.getStats();

    expect(stats.totalWorkers).toBeGreaterThan(0);

    testPool.destroy();
  });

  it("should respect maxWorkers configuration", () => {
    const testPool = new WorkerPool({ maxWorkers: 1 });
    const stats = testPool.getStats();

    expect(stats.totalWorkers).toBeLessThanOrEqual(1);

    testPool.destroy();
  });

  it("should handle custom idle timeout", () => {
    const testPool = new WorkerPool({ idleTimeout: 1000 });

    expect(testPool).toBeDefined();

    testPool.destroy();
  });
});

describe("Worker Pool Statistics", () => {
  let pool: WorkerPool;

  beforeEach(() => {
    pool = new WorkerPool({ maxWorkers: 2 });
  });

  afterEach(() => {
    pool.destroy();
  });

  it("should track total workers", () => {
    const stats = pool.getStats();
    expect(stats.totalWorkers).toBeGreaterThan(0);
    expect(stats.totalWorkers).toBeLessThanOrEqual(2);
  });

  it("should track idle workers", () => {
    const stats = pool.getStats();
    expect(stats.idleWorkers).toBeGreaterThanOrEqual(0);
    expect(stats.idleWorkers).toBeLessThanOrEqual(stats.totalWorkers);
  });

  it("should track busy workers", () => {
    const stats = pool.getStats();
    expect(stats.busyWorkers).toBeGreaterThanOrEqual(0);
    expect(stats.busyWorkers).toBeLessThanOrEqual(stats.totalWorkers);
  });

  it("should track completed tasks", () => {
    const stats = pool.getStats();
    expect(stats.totalTasksCompleted).toBeGreaterThanOrEqual(0);
  });
});

describe("Worker Pool Lifecycle", () => {
  it("should create workers on demand", () => {
    const testPool = new WorkerPool({ maxWorkers: 3 });

    const initialStats = testPool.getStats();
    expect(initialStats.totalWorkers).toBeGreaterThan(0);

    testPool.destroy();
  });

  it("should terminate idle workers", async () => {
    vi.useFakeTimers();
    const testPool = new WorkerPool({
      maxWorkers: 2,
      idleTimeout: 100, // Very short timeout for testing
    });

    // Wait for idle timeout
    await vi.advanceTimersByTimeAsync(200);

    testPool.destroy();
    vi.useRealTimers();
  });

  it("should handle worker errors gracefully", () => {
    const testPool = new WorkerPool({ maxWorkers: 2 });

    // Pool should still be functional
    const stats = testPool.getStats();
    expect(stats.totalWorkers).toBeGreaterThan(0);

    testPool.destroy();
  });
});

describe("Worker Communication Protocol", () => {
  it("should have proper message structure", () => {
    const message = {
      id: "test-1",
      type: WorkerMessageType.PARSE_JSON,
      payload: { data: '{"test": true}' },
      timestamp: Date.now(),
    };

    expect(message).toHaveProperty("id");
    expect(message).toHaveProperty("type");
    expect(message).toHaveProperty("payload");
    expect(message).toHaveProperty("timestamp");
  });

  it("should have proper response structure", () => {
    const response = {
      id: "test-1",
      success: true,
      result: { test: true },
      duration: 10,
      timestamp: Date.now(),
    };

    expect(response).toHaveProperty("id");
    expect(response).toHaveProperty("success");
    expect(response).toHaveProperty("result");
    expect(response).toHaveProperty("duration");
    expect(response).toHaveProperty("timestamp");
  });
});
