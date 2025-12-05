/**
 * Web Worker Implementation
 *
 * Main worker script that handles various heavy tasks.
 *
 * Requirements: 14.3
 */

import {
  WorkerMessage,
  WorkerResponse,
  WorkerMessageType,
  ProcessFilePayload,
  ParseJSONPayload,
  ParseCSVPayload,
  CompressDataPayload,
  ComputeMetricsPayload,
  AggregateDataPayload,
  FilterDataPayload,
  SortDataPayload,
} from "./types";

// Worker context
const ctx: Worker = self as unknown as Worker;

/**
 * Handle incoming messages
 */
ctx.addEventListener("message", async (event: MessageEvent<WorkerMessage>) => {
  const message = event.data;
  const startTime = performance.now();

  try {
    let result: unknown;

    switch (message.type) {
      case WorkerMessageType.PROCESS_FILE:
        result = await processFile(message.payload as ProcessFilePayload);
        break;

      case WorkerMessageType.PARSE_JSON:
        result = parseJSON(message.payload as ParseJSONPayload);
        break;

      case WorkerMessageType.PARSE_CSV:
        result = parseCSV(message.payload as ParseCSVPayload);
        break;

      case WorkerMessageType.COMPRESS_DATA:
        result = await compressData(message.payload as CompressDataPayload);
        break;

      case WorkerMessageType.DECOMPRESS_DATA:
        result = await decompressData(message.payload as CompressDataPayload);
        break;

      case WorkerMessageType.COMPUTE_METRICS:
        result = computeMetrics(message.payload as ComputeMetricsPayload);
        break;

      case WorkerMessageType.AGGREGATE_DATA:
        result = aggregateData(message.payload as AggregateDataPayload);
        break;

      case WorkerMessageType.FILTER_DATA:
        result = filterData(message.payload as FilterDataPayload);
        break;

      case WorkerMessageType.SORT_DATA:
        result = sortData(message.payload as SortDataPayload);
        break;

      default:
        throw new Error(`Unknown message type: ${message.type}`);
    }

    const duration = performance.now() - startTime;

    const response: WorkerResponse = {
      id: message.id,
      success: true,
      result,
      duration,
      timestamp: Date.now(),
    };

    ctx.postMessage(response);
  } catch (error) {
    const duration = performance.now() - startTime;

    const response: WorkerResponse = {
      id: message.id,
      success: false,
      error: error instanceof Error ? error.message : String(error),
      duration,
      timestamp: Date.now(),
    };

    ctx.postMessage(response);
  }
});

/**
 * Process file in chunks
 */
async function processFile(payload: ProcessFilePayload): Promise<{
  size: number;
  type: string;
  chunks: number;
}> {
  const { file, options = {} } = payload;
  const chunkSize = options.chunkSize || 1024 * 1024; // 1MB chunks

  if (file instanceof ArrayBuffer) {
    return {
      size: file.byteLength,
      type: "arraybuffer",
      chunks: Math.ceil(file.byteLength / chunkSize),
    };
  }

  // For File objects, we'd need to read them
  // This is a simplified version
  return {
    size: 0,
    type: "unknown",
    chunks: 0,
  };
}

/**
 * Parse JSON data
 */
function parseJSON(payload: ParseJSONPayload): unknown {
  const { data, reviver } = payload;

  let jsonString: string;
  if (data instanceof ArrayBuffer) {
    const decoder = new TextDecoder();
    jsonString = decoder.decode(data);
  } else {
    jsonString = data;
  }

  // If reviver is provided, evaluate it (be careful with this in production)
  const reviverFn = reviver ? eval(`(${reviver})`) : undefined;

  return JSON.parse(jsonString, reviverFn);
}

/**
 * Parse CSV data
 */
function parseCSV(payload: ParseCSVPayload): Array<Record<string, string> | string[]> {
  const { data, delimiter = ",", headers = true } = payload;

  const lines = data.trim().split("\n");
  if (lines.length === 0) return [];

  const headerRow = headers ? lines[0].split(delimiter) : null;
  const dataRows = headers ? lines.slice(1) : lines;

  return dataRows.map((line) => {
    const values = line.split(delimiter);

    if (headerRow) {
      const obj: Record<string, string> = {};
      headerRow.forEach((header, index) => {
        obj[header.trim()] = values[index]?.trim() || "";
      });
      return obj;
    }

    return values.map((v) => v.trim());
  });
}

/**
 * Compress data using CompressionStream API
 */
async function compressData(payload: CompressDataPayload): Promise<ArrayBuffer> {
  const { data, algorithm = "gzip" } = payload;

  // Convert string to ArrayBuffer if needed
  let buffer: ArrayBuffer;
  if (typeof data === "string") {
    const encoder = new TextEncoder();
    buffer = encoder.encode(data).buffer;
  } else {
    buffer = data;
  }

  // Use CompressionStream if available
  if ("CompressionStream" in self) {
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(new Uint8Array(buffer));
        controller.close();
      },
    });

    const compressedStream = stream.pipeThrough(
      new (
        self as typeof globalThis & {
          CompressionStream: new (algorithm: string) => TransformStream;
        }
      ).CompressionStream(algorithm)
    );

    const reader = compressedStream.getReader();
    const chunks: Uint8Array[] = [];

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      if (value instanceof Uint8Array) chunks.push(value);
    }

    // Combine chunks
    const totalLength = chunks.reduce((acc, chunk) => acc + chunk.length, 0);
    const result = new Uint8Array(totalLength);
    let offset = 0;
    for (const chunk of chunks) {
      result.set(chunk, offset);
      offset += chunk.length;
    }

    return result.buffer;
  }

  // Fallback: return original data
  return buffer;
}

/**
 * Decompress data using DecompressionStream API
 */
async function decompressData(payload: CompressDataPayload): Promise<ArrayBuffer> {
  const { data, algorithm = "gzip" } = payload;

  const buffer = typeof data === "string" ? new TextEncoder().encode(data).buffer : data;

  // Use DecompressionStream if available
  if ("DecompressionStream" in self) {
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(new Uint8Array(buffer));
        controller.close();
      },
    });

    const decompressedStream = stream.pipeThrough(
      new (
        self as typeof globalThis & {
          DecompressionStream: new (algorithm: string) => TransformStream;
        }
      ).DecompressionStream(algorithm)
    );

    const reader = decompressedStream.getReader();
    const chunks: Uint8Array[] = [];

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      if (value instanceof Uint8Array) chunks.push(value);
    }

    // Combine chunks
    const totalLength = chunks.reduce((acc, chunk) => acc + chunk.length, 0);
    const result = new Uint8Array(totalLength);
    let offset = 0;
    for (const chunk of chunks) {
      result.set(chunk, offset);
      offset += chunk.length;
    }

    return result.buffer;
  }

  // Fallback: return original data
  return buffer;
}

/**
 * Compute statistical metrics
 */
function computeMetrics(payload: ComputeMetricsPayload): Record<string, number> {
  const { data, metrics } = payload;
  const result: Record<string, number> = {};

  if (data.length === 0) return result;

  const sorted = [...data].sort((a, b) => a - b);
  const sum = data.reduce((acc, val) => acc + val, 0);

  for (const metric of metrics) {
    switch (metric) {
      case "mean":
        result.mean = sum / data.length;
        break;

      case "median": {
        const mid = Math.floor(sorted.length / 2);
        result.median = sorted.length % 2 === 0 ? (sorted[mid - 1] + sorted[mid]) / 2 : sorted[mid];
        break;
      }

      case "std": {
        const mean = sum / data.length;
        const variance = data.reduce((acc, val) => acc + Math.pow(val - mean, 2), 0) / data.length;
        result.std = Math.sqrt(variance);
        break;
      }

      case "min":
        result.min = sorted[0];
        break;

      case "max":
        result.max = sorted[sorted.length - 1];
        break;

      case "p95":
        result.p95 = sorted[Math.floor(sorted.length * 0.95)];
        break;

      case "p99":
        result.p99 = sorted[Math.floor(sorted.length * 0.99)];
        break;
    }
  }

  return result;
}

/**
 * Aggregate data by group
 */
function aggregateData(payload: AggregateDataPayload): Record<string, unknown>[] {
  const { data, groupBy, aggregations } = payload;

  // Group data
  const groups = new Map<unknown, Record<string, unknown>[]>();
  for (const item of data) {
    const key = item[groupBy];
    if (!groups.has(key)) {
      groups.set(key, []);
    }
    groups.get(key)!.push(item);
  }

  // Aggregate each group
  const results: Record<string, unknown>[] = [];
  for (const [key, items] of groups) {
    const result: Record<string, unknown> = { [groupBy]: key };

    for (const agg of aggregations) {
      const values = items.map((item) => item[agg.field]).filter((v) => typeof v === "number");

      switch (agg.operation) {
        case "sum":
          result[`${agg.field}_sum`] = values.reduce((acc, val) => acc + val, 0);
          break;

        case "avg":
          result[`${agg.field}_avg`] =
            values.length > 0 ? values.reduce((acc, val) => acc + val, 0) / values.length : 0;
          break;

        case "count":
          result[`${agg.field}_count`] = values.length;
          break;

        case "min":
          result[`${agg.field}_min`] = values.length > 0 ? Math.min(...values) : null;
          break;

        case "max":
          result[`${agg.field}_max`] = values.length > 0 ? Math.max(...values) : null;
          break;
      }
    }

    results.push(result);
  }

  return results;
}

/**
 * Filter data using predicate
 */
function filterData(payload: FilterDataPayload): Record<string, unknown>[] {
  const { data, predicate } = payload;

  // Evaluate predicate function (be careful with this in production)
  const predicateFn = eval(`(${predicate})`);

  return data.filter(predicateFn);
}

/**
 * Sort data by key
 */
function sortData(payload: SortDataPayload): Record<string, unknown>[] {
  const { data, key, order } = payload;

  const sorted = [...data].sort((a, b) => {
    const aVal = a[key] as string | number;
    const bVal = b[key] as string | number;

    if (aVal < bVal) return order === "asc" ? -1 : 1;
    if (aVal > bVal) return order === "asc" ? 1 : -1;
    return 0;
  });

  return sorted;
}

// Export for TypeScript
export { };
