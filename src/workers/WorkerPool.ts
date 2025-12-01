/**
 * Worker Pool Manager
 * 
 * Manages a pool of Web Workers for efficient task distribution.
 * 
 * Requirements: 14.3
 */

import {
  WorkerMessage,
  WorkerResponse,
  WorkerTask,
  WorkerPoolConfig,
  WorkerStatus,
  WorkerInfo,
  WorkerMessageType,
} from './types';

interface ManagedWorker {
  id: string;
  worker: Worker;
  status: WorkerStatus;
  currentTask: WorkerTask | null;
  tasksCompleted: number;
  createdAt: number;
  lastUsed: number;
  idleTimer: number | null;
}

export class WorkerPool {
  private workers: Map<string, ManagedWorker> = new Map();
  private taskQueue: WorkerTask[] = [];
  private pendingTasks: Map<string, WorkerTask> = new Map();
  private config: Required<WorkerPoolConfig>;
  private nextWorkerId = 0;
  private nextTaskId = 0;

  constructor(config: WorkerPoolConfig = {}) {
    this.config = {
      maxWorkers: config.maxWorkers || navigator.hardwareConcurrency || 4,
      idleTimeout: config.idleTimeout || 30000, // 30 seconds
      taskTimeout: config.taskTimeout || 60000, // 60 seconds
      workerScript: config.workerScript || '/src/workers/worker.ts',
    };

    // Initialize with one worker
    this.createWorker();
  }

  /**
   * Execute a task on a worker
   */
  async execute<T = any, R = any>(
    type: WorkerMessageType,
    payload: T,
    timeout?: number
  ): Promise<R> {
    return new Promise((resolve, reject) => {
      const task: WorkerTask<T, R> = {
        id: `task-${this.nextTaskId++}`,
        type,
        payload,
        resolve,
        reject,
        startTime: Date.now(),
        timeout: timeout || this.config.taskTimeout,
      };

      this.pendingTasks.set(task.id, task);
      this.taskQueue.push(task);
      this.processQueue();

      // Set timeout
      setTimeout(() => {
        if (this.pendingTasks.has(task.id)) {
          this.pendingTasks.delete(task.id);
          reject(new Error(`Task ${task.id} timed out after ${task.timeout}ms`));
        }
      }, task.timeout);
    });
  }

  /**
   * Process the task queue
   */
  private processQueue(): void {
    // Find idle workers
    const idleWorkers = Array.from(this.workers.values()).filter(
      (w) => w.status === WorkerStatus.IDLE
    );

    // If no idle workers and we can create more, create one
    if (idleWorkers.length === 0 && this.workers.size < this.config.maxWorkers) {
      this.createWorker();
      this.processQueue();
      return;
    }

    // Assign tasks to idle workers
    while (this.taskQueue.length > 0 && idleWorkers.length > 0) {
      const task = this.taskQueue.shift()!;
      const worker = idleWorkers.shift()!;
      this.assignTask(worker, task);
    }
  }

  /**
   * Assign a task to a worker
   */
  private assignTask(managedWorker: ManagedWorker, task: WorkerTask) {
    managedWorker.status = WorkerStatus.BUSY;
    managedWorker.currentTask = task;
    managedWorker.lastUsed = Date.now();

    // Clear idle timer
    if (managedWorker.idleTimer !== null) {
      clearTimeout(managedWorker.idleTimer);
      managedWorker.idleTimer = null;
    }

    const message: WorkerMessage = {
      id: task.id,
      type: task.type,
      payload: task.payload,
      timestamp: Date.now(),
    };

    managedWorker.worker.postMessage(message);
  }

  /**
   * Create a new worker
   */
  private createWorker(): ManagedWorker {
    const id = `worker-${this.nextWorkerId++}`;
    
    // Create worker with module type
    const worker = new Worker(
      new URL('./worker.ts', import.meta.url),
      { type: 'module' }
    );

    const managedWorker: ManagedWorker = {
      id,
      worker,
      status: WorkerStatus.IDLE,
      currentTask: null,
      tasksCompleted: 0,
      createdAt: Date.now(),
      lastUsed: Date.now(),
      idleTimer: null,
    };

    // Handle messages from worker
    worker.addEventListener('message', (event: MessageEvent<WorkerResponse>) => {
      this.handleWorkerResponse(managedWorker, event.data);
    });

    // Handle errors
    worker.addEventListener('error', (event: ErrorEvent) => {
      this.handleWorkerError(managedWorker, event);
    });

    // Handle message errors
    worker.addEventListener('messageerror', (event: MessageEvent) => {
      console.error(`Worker ${id} message error:`, event);
      managedWorker.status = WorkerStatus.ERROR;
    });

    this.workers.set(id, managedWorker);
    console.log(`Created worker ${id}. Total workers: ${this.workers.size}`);

    return managedWorker;
  }

  /**
   * Handle response from worker
   */
  private handleWorkerResponse(managedWorker: ManagedWorker, response: WorkerResponse) {
    const task = this.pendingTasks.get(response.id);
    
    if (!task) {
      console.warn(`Received response for unknown task: ${response.id}`);
      return;
    }

    this.pendingTasks.delete(response.id);

    if (response.success) {
      task.resolve(response.result);
    } else {
      task.reject(new Error(response.error || 'Worker task failed'));
    }

    // Update worker status
    managedWorker.status = WorkerStatus.IDLE;
    managedWorker.currentTask = null;
    managedWorker.tasksCompleted++;
    managedWorker.lastUsed = Date.now();

    // Set idle timer
    managedWorker.idleTimer = window.setTimeout(() => {
      this.terminateIdleWorker(managedWorker);
    }, this.config.idleTimeout);

    // Process next task in queue
    this.processQueue();
  }

  /**
   * Handle worker error
   */
  private handleWorkerError(managedWorker: ManagedWorker, event: ErrorEvent) {
    console.error(`Worker ${managedWorker.id} error:`, event.message);
    managedWorker.status = WorkerStatus.ERROR;

    // Reject current task if any
    if (managedWorker.currentTask) {
      const task = this.pendingTasks.get(managedWorker.currentTask.id);
      if (task) {
        this.pendingTasks.delete(task.id);
        task.reject(new Error(`Worker error: ${event.message}`));
      }
      managedWorker.currentTask = null;
    }

    // Terminate and remove the worker
    this.terminateWorker(managedWorker);

    // Create a new worker to replace it
    if (this.workers.size < this.config.maxWorkers) {
      this.createWorker();
    }

    // Process queue with remaining workers
    this.processQueue();
  }

  /**
   * Terminate an idle worker
   */
  private terminateIdleWorker(managedWorker: ManagedWorker) {
    // Don't terminate if it's the last worker or if it's busy
    if (this.workers.size <= 1 || managedWorker.status !== WorkerStatus.IDLE) {
      return;
    }

    console.log(`Terminating idle worker ${managedWorker.id}`);
    this.terminateWorker(managedWorker);
  }

  /**
   * Terminate a worker
   */
  private terminateWorker(managedWorker: ManagedWorker) {
    if (managedWorker.idleTimer !== null) {
      clearTimeout(managedWorker.idleTimer);
    }

    managedWorker.worker.terminate();
    managedWorker.status = WorkerStatus.TERMINATED;
    this.workers.delete(managedWorker.id);

    console.log(`Terminated worker ${managedWorker.id}. Remaining workers: ${this.workers.size}`);
  }

  /**
   * Get worker pool statistics
   */
  getStats() {
    const workers = Array.from(this.workers.values());
    
    return {
      totalWorkers: workers.length,
      idleWorkers: workers.filter((w) => w.status === WorkerStatus.IDLE).length,
      busyWorkers: workers.filter((w) => w.status === WorkerStatus.BUSY).length,
      errorWorkers: workers.filter((w) => w.status === WorkerStatus.ERROR).length,
      queuedTasks: this.taskQueue.length,
      pendingTasks: this.pendingTasks.size,
      totalTasksCompleted: workers.reduce((sum, w) => sum + w.tasksCompleted, 0),
    };
  }

  /**
   * Get information about all workers
   */
  getWorkerInfo(): WorkerInfo[] {
    return Array.from(this.workers.values()).map((w) => ({
      id: w.id,
      status: w.status,
      tasksCompleted: w.tasksCompleted,
      currentTask: w.currentTask?.id || null,
      createdAt: w.createdAt,
      lastUsed: w.lastUsed,
    }));
  }

  /**
   * Terminate all workers and clear queue
   */
  destroy() {
    // Reject all pending tasks
    for (const task of this.pendingTasks.values()) {
      task.reject(new Error('Worker pool destroyed'));
    }
    this.pendingTasks.clear();

    // Clear queue
    this.taskQueue = [];

    // Terminate all workers
    for (const managedWorker of this.workers.values()) {
      this.terminateWorker(managedWorker);
    }

    console.log('Worker pool destroyed');
  }

  /**
   * Get the number of active workers
   */
  get activeWorkerCount(): number {
    return this.workers.size;
  }

  /**
   * Get the number of queued tasks
   */
  get queuedTaskCount(): number {
    return this.taskQueue.length;
  }
}

// Global worker pool instance
let globalWorkerPool: WorkerPool | null = null;

/**
 * Get or create the global worker pool
 */
export function getWorkerPool(config?: WorkerPoolConfig): WorkerPool {
  if (!globalWorkerPool) {
    globalWorkerPool = new WorkerPool(config);
  }
  return globalWorkerPool;
}

/**
 * Destroy the global worker pool
 */
export function destroyWorkerPool() {
  if (globalWorkerPool) {
    globalWorkerPool.destroy();
    globalWorkerPool = null;
  }
}
