/**
 * Web Workers Module
 * 
 * Exports all worker-related functionality.
 * 
 * Requirements: 14.3
 */

export * from './types';
export * from './WorkerPool';
export { getWorkerPool, destroyWorkerPool } from './WorkerPool';
