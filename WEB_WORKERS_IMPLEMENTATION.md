# Web Workers Implementation

## Overview

This document describes the implementation of Web Workers for offloading heavy tasks to background threads, keeping the UI responsive.

**Requirements:** 14.3

## Architecture

### Components

1. **Worker Pool Manager** (`src/workers/WorkerPool.ts`)
   - Manages a pool of Web Workers
   - Distributes tasks across available workers
   - Handles worker lifecycle (creation, termination, idle timeout)
   - Provides task queuing and execution

2. **Worker Script** (`src/workers/worker.ts`)
   - Main worker implementation
   - Handles various task types (file processing, data processing, etc.)
   - Implements worker communication protocol

3. **Type Definitions** (`src/workers/types.ts`)
   - Message types and structures
   - Worker configuration interfaces
   - Task payload definitions

4. **React Hooks** (`src/hooks/useWorker.ts`)
   - `useWorkerPool()` - Access to worker pool
   - `useFileProcessor()` - File processing operations
   - `useDataProcessor()` - Data processing operations
   - `useWorkerStats()` - Worker pool statistics

## Features

### Worker Pool Management

The `WorkerPool` class manages multiple workers efficiently:

```typescript
const pool = new WorkerPool({
  maxWorkers: 4,           // Maximum number of workers
  idleTimeout: 30000,      // Terminate idle workers after 30s
  taskTimeout: 60000,      // Task timeout (60s)
});
```

**Features:**
- Dynamic worker creation based on load
- Automatic idle worker termination
- Task queuing when all workers are busy
- Error handling and worker recovery
- Performance statistics

### Supported Task Types

#### File Processing
- `PROCESS_FILE` - Process files in chunks
- `PARSE_JSON` - Parse JSON data
- `PARSE_CSV` - Parse CSV data
- `COMPRESS_DATA` - Compress data using CompressionStream
- `DECOMPRESS_DATA` - Decompress data

#### Data Processing
- `COMPUTE_METRICS` - Calculate statistical metrics (mean, median, std, etc.)
- `AGGREGATE_DATA` - Group and aggregate data
- `FILTER_DATA` - Filter data using predicates
- `SORT_DATA` - Sort data by key

#### Image Processing (Future)
- `RESIZE_IMAGE` - Resize images
- `CONVERT_IMAGE` - Convert image formats

#### Model Processing (Future)
- `VALIDATE_CONFIG` - Validate training configurations
- `CALCULATE_COST` - Calculate training costs

## Usage Examples

### Using React Hooks

#### File Processing

```typescript
import { useFileProcessor } from '../hooks/useWorker';

function MyComponent() {
  const { processFile, parseCSV, processing, error } = useFileProcessor();

  const handleFileUpload = async (file: File) => {
    try {
      const result = await processFile(file);
      console.log('File processed:', result);
    } catch (err) {
      console.error('Error:', err);
    }
  };

  const handleCSVParse = async (csvData: string) => {
    const result = await parseCSV(csvData, {
      delimiter: ',',
      headers: true,
    });
    console.log('Parsed data:', result);
  };

  return (
    <div>
      <input type="file" onChange={(e) => handleFileUpload(e.target.files[0])} />
      {processing && <div>Processing...</div>}
      {error && <div>Error: {error.message}</div>}
    </div>
  );
}
```

#### Data Processing

```typescript
import { useDataProcessor } from '../hooks/useWorker';

function DataAnalysis() {
  const { computeMetrics, sortData, processing } = useDataProcessor();

  const analyzeData = async (numbers: number[]) => {
    const metrics = await computeMetrics(numbers, [
      'mean', 'median', 'std', 'min', 'max', 'p95', 'p99'
    ]);
    console.log('Metrics:', metrics);
  };

  const sortResults = async (data: any[]) => {
    const sorted = await sortData(data, 'score', 'desc');
    console.log('Sorted:', sorted);
  };

  return (
    <div>
      {processing && <div>Processing...</div>}
    </div>
  );
}
```

#### Worker Statistics

```typescript
import { useWorkerStats } from '../hooks/useWorker';

function WorkerMonitor() {
  const stats = useWorkerStats(1000); // Update every second

  return (
    <div>
      <div>Total Workers: {stats.totalWorkers}</div>
      <div>Idle Workers: {stats.idleWorkers}</div>
      <div>Busy Workers: {stats.busyWorkers}</div>
      <div>Tasks Completed: {stats.totalTasksCompleted}</div>
      <div>Queued Tasks: {stats.queuedTasks}</div>
    </div>
  );
}
```

### Direct Worker Pool Usage

```typescript
import { getWorkerPool } from '../workers';
import { WorkerMessageType } from '../workers/types';

const pool = getWorkerPool();

// Execute a task
const result = await pool.execute(
  WorkerMessageType.PARSE_JSON,
  { data: '{"test": true}' }
);

// Get statistics
const stats = pool.getStats();
console.log('Worker stats:', stats);

// Get worker information
const workers = pool.getWorkerInfo();
console.log('Workers:', workers);
```

## Communication Protocol

### Message Structure

```typescript
interface WorkerMessage {
  id: string;              // Unique task ID
  type: WorkerMessageType; // Task type
  payload: any;            // Task-specific data
  timestamp: number;       // Message timestamp
}
```

### Response Structure

```typescript
interface WorkerResponse {
  id: string;        // Matching task ID
  success: boolean;  // Success flag
  result?: any;      // Result data (if successful)
  error?: string;    // Error message (if failed)
  duration: number;  // Execution time (ms)
  timestamp: number; // Response timestamp
}
```

## Performance Considerations

### Worker Pool Sizing

The default maximum workers is set to `navigator.hardwareConcurrency` (typically 4-8 on modern devices). This can be configured:

```typescript
const pool = new WorkerPool({
  maxWorkers: navigator.hardwareConcurrency || 4
});
```

### Idle Worker Termination

Workers are automatically terminated after being idle for 30 seconds (configurable). This reduces memory usage when workers are not needed.

### Task Timeout

Tasks have a default timeout of 60 seconds. Long-running tasks should be broken into smaller chunks or have their timeout increased:

```typescript
await pool.execute(
  WorkerMessageType.PROCESS_FILE,
  { file: largeFile },
  120000 // 2 minute timeout
);
```

### Memory Management

- Workers are terminated when idle to free memory
- Large data should be transferred using `ArrayBuffer` or `SharedArrayBuffer`
- Use structured cloning for complex objects

## Best Practices

### 1. Use Workers for Heavy Tasks

Offload CPU-intensive operations:
- Large file parsing
- Complex calculations
- Data transformations
- Image processing

### 2. Avoid for Simple Operations

Don't use workers for:
- Simple calculations
- Small data processing
- Operations that take < 16ms

### 3. Handle Errors Gracefully

```typescript
try {
  const result = await pool.execute(type, payload);
} catch (error) {
  console.error('Worker error:', error);
  // Fallback to main thread
}
```

### 4. Monitor Performance

Use `useWorkerStats()` to monitor worker pool performance and adjust configuration as needed.

### 5. Cleanup on Unmount

```typescript
import { useWorkerPoolCleanup } from '../hooks/useWorker';

function App() {
  useWorkerPoolCleanup(); // Cleanup on app unmount
  
  return <div>...</div>;
}
```

## Testing

Run tests with:

```bash
npm test src/test/worker.test.ts
```

Tests cover:
- Worker pool creation and configuration
- Task execution
- Worker lifecycle management
- Error handling
- Statistics tracking

## Future Enhancements

1. **Transferable Objects**
   - Use `Transferable` for zero-copy data transfer
   - Implement for large ArrayBuffers

2. **SharedArrayBuffer**
   - Enable for concurrent data access
   - Requires secure context (HTTPS)

3. **Worker Caching**
   - Cache frequently used workers
   - Warm up workers on app start

4. **Priority Queue**
   - Implement task priorities
   - High-priority tasks jump the queue

5. **Progress Reporting**
   - Stream progress updates from workers
   - Show progress bars for long tasks

6. **Worker Specialization**
   - Dedicated workers for specific task types
   - Optimize worker code for specific operations

## Browser Compatibility

Web Workers are supported in all modern browsers:
- Chrome 4+
- Firefox 3.5+
- Safari 4+
- Edge 12+

CompressionStream API (used for compression) requires:
- Chrome 80+
- Firefox 113+
- Safari 16.4+

## Performance Metrics

Expected performance improvements:
- **File Processing**: 2-3x faster for files > 1MB
- **Data Processing**: 3-5x faster for datasets > 10,000 items
- **UI Responsiveness**: No blocking on heavy operations
- **Memory Usage**: Efficient with idle worker termination

## Troubleshooting

### Workers Not Starting

Check browser console for errors. Ensure worker script is accessible:

```typescript
const pool = new WorkerPool({
  workerScript: '/src/workers/worker.ts'
});
```

### Tasks Timing Out

Increase timeout for long-running tasks:

```typescript
await pool.execute(type, payload, 120000); // 2 minutes
```

### High Memory Usage

Reduce `maxWorkers` or decrease `idleTimeout`:

```typescript
const pool = new WorkerPool({
  maxWorkers: 2,
  idleTimeout: 10000 // 10 seconds
});
```

## Conclusion

The Web Workers implementation provides a robust solution for offloading heavy tasks to background threads, ensuring the UI remains responsive even during intensive operations. The worker pool automatically manages resources and scales based on demand.
