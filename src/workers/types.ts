/**
 * Web Worker Types
 * 
 * Type definitions for worker communication protocol.
 * 
 * Requirements: 14.3
 */

// Worker message types
export enum WorkerMessageType {
  // File processing
  PROCESS_FILE = 'PROCESS_FILE',
  PARSE_JSON = 'PARSE_JSON',
  PARSE_CSV = 'PARSE_CSV',
  COMPRESS_DATA = 'COMPRESS_DATA',
  DECOMPRESS_DATA = 'DECOMPRESS_DATA',
  
  // Data processing
  COMPUTE_METRICS = 'COMPUTE_METRICS',
  AGGREGATE_DATA = 'AGGREGATE_DATA',
  FILTER_DATA = 'FILTER_DATA',
  SORT_DATA = 'SORT_DATA',
  
  // Image processing
  RESIZE_IMAGE = 'RESIZE_IMAGE',
  CONVERT_IMAGE = 'CONVERT_IMAGE',
  
  // Model processing
  VALIDATE_CONFIG = 'VALIDATE_CONFIG',
  CALCULATE_COST = 'CALCULATE_COST',
  
  // Generic
  CUSTOM = 'CUSTOM',
}

// Worker message structure
export interface WorkerMessage<T = any> {
  id: string;
  type: WorkerMessageType;
  payload: T;
  timestamp: number;
}

// Worker response structure
export interface WorkerResponse<T = any> {
  id: string;
  success: boolean;
  result?: T;
  error?: string;
  duration: number;
  timestamp: number;
}

// Worker task
export interface WorkerTask<T = any, R = any> {
  id: string;
  type: WorkerMessageType;
  payload: T;
  resolve: (result: R) => void;
  reject: (error: Error) => void;
  startTime: number;
  timeout?: number;
}

// Worker pool configuration
export interface WorkerPoolConfig {
  maxWorkers?: number;
  idleTimeout?: number;
  taskTimeout?: number;
  workerScript?: string;
}

// Worker status
export enum WorkerStatus {
  IDLE = 'IDLE',
  BUSY = 'BUSY',
  ERROR = 'ERROR',
  TERMINATED = 'TERMINATED',
}

// Worker info
export interface WorkerInfo {
  id: string;
  status: WorkerStatus;
  tasksCompleted: number;
  currentTask: string | null;
  createdAt: number;
  lastUsed: number;
}

// File processing payloads
export interface ProcessFilePayload {
  file: File | ArrayBuffer;
  options?: {
    chunkSize?: number;
    encoding?: string;
  };
}

export interface ParseJSONPayload {
  data: string | ArrayBuffer;
  reviver?: string; // Serialized function
}

export interface ParseCSVPayload {
  data: string;
  delimiter?: string;
  headers?: boolean;
}

export interface CompressDataPayload {
  data: string | ArrayBuffer;
  algorithm?: 'gzip' | 'deflate';
}

// Data processing payloads
export interface ComputeMetricsPayload {
  data: number[];
  metrics: ('mean' | 'median' | 'std' | 'min' | 'max' | 'p95' | 'p99')[];
}

export interface AggregateDataPayload {
  data: any[];
  groupBy: string;
  aggregations: {
    field: string;
    operation: 'sum' | 'avg' | 'count' | 'min' | 'max';
  }[];
}

export interface FilterDataPayload {
  data: any[];
  predicate: string; // Serialized function
}

export interface SortDataPayload {
  data: any[];
  key: string;
  order: 'asc' | 'desc';
}

// Image processing payloads
export interface ResizeImagePayload {
  imageData: ArrayBuffer;
  width: number;
  height: number;
  quality?: number;
}

export interface ConvertImagePayload {
  imageData: ArrayBuffer;
  format: 'webp' | 'jpeg' | 'png';
  quality?: number;
}

// Model processing payloads
export interface ValidateConfigPayload {
  config: any;
  schema: any;
}

export interface CalculateCostPayload {
  provider: string;
  resourceId: string;
  duration: number;
  options?: any;
}
