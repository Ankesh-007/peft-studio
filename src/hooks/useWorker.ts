/**
 * Worker Hooks
 *
 * React hooks for using Web Workers in components.
 *
 * Requirements: 14.3
 */

import { useEffect, useRef, useCallback, useState } from "react";
import { getWorkerPool, destroyWorkerPool } from "../workers/WorkerPool";
import { WorkerMessageType } from "../workers/types";

/**
 * Hook to use the worker pool
 */
export function useWorkerPool() {
  const poolRef = useRef(getWorkerPool());

  useEffect(() => {
    return () => {
      // Don't destroy on unmount as it's a global pool
      // Only destroy when the app unmounts
    };
  }, []);

  const execute = useCallback(
    async <T = unknown, R = unknown>(
      type: WorkerMessageType,
      payload: T,
      timeout?: number
    ): Promise<R> => {
      return poolRef.current.execute<T, R>(type, payload, timeout);
    },
    []
  );

  const getStats = useCallback(() => {
    return poolRef.current.getStats();
  }, []);

  const getWorkerInfo = useCallback(() => {
    return poolRef.current.getWorkerInfo();
  }, []);

  return {
    execute,
    getStats,
    getWorkerInfo,
  };
}

/**
 * Hook to process files in a worker
 */
export function useFileProcessor() {
  const { execute } = useWorkerPool();
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<Error | null>(null);

  const processFile = useCallback(
    async (file: File, options?: Record<string, unknown>) => {
      setProcessing(true);
      setProgress(0);
      setError(null);

      try {
        // Read file as ArrayBuffer
        const buffer = await file.arrayBuffer();

        // Process in worker
        const result = await execute(WorkerMessageType.PROCESS_FILE, { file: buffer, options });

        setProgress(100);
        return result;
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        throw error;
      } finally {
        setProcessing(false);
      }
    },
    [execute]
  );

  const parseJSON = useCallback(
    async (data: string | ArrayBuffer) => {
      setProcessing(true);
      setError(null);

      try {
        const result = await execute(WorkerMessageType.PARSE_JSON, { data });
        return result;
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        throw error;
      } finally {
        setProcessing(false);
      }
    },
    [execute]
  );

  const parseCSV = useCallback(
    async (data: string, options?: { delimiter?: string; headers?: boolean }) => {
      setProcessing(true);
      setError(null);

      try {
        const result = await execute(WorkerMessageType.PARSE_CSV, { data, ...options });
        return result;
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        throw error;
      } finally {
        setProcessing(false);
      }
    },
    [execute]
  );

  return {
    processFile,
    parseJSON,
    parseCSV,
    processing,
    progress,
    error,
  };
}

/**
 * Hook to process data in a worker
 */
export function useDataProcessor() {
  const { execute } = useWorkerPool();
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const computeMetrics = useCallback(
    async (data: number[], metrics: string[]) => {
      setProcessing(true);
      setError(null);

      try {
        const result = await execute(WorkerMessageType.COMPUTE_METRICS, { data, metrics });
        return result;
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        throw error;
      } finally {
        setProcessing(false);
      }
    },
    [execute]
  );

  const aggregateData = useCallback(
    async (
      data: Record<string, unknown>[],
      groupBy: string,
      aggregations: Array<{ field: string; operation: string }>
    ) => {
      setProcessing(true);
      setError(null);

      try {
        const result = await execute(WorkerMessageType.AGGREGATE_DATA, {
          data,
          groupBy,
          aggregations,
        });
        return result;
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        throw error;
      } finally {
        setProcessing(false);
      }
    },
    [execute]
  );

  const filterData = useCallback(
    async (data: Record<string, unknown>[], predicate: string) => {
      setProcessing(true);
      setError(null);

      try {
        const result = await execute(WorkerMessageType.FILTER_DATA, { data, predicate });
        return result;
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        throw error;
      } finally {
        setProcessing(false);
      }
    },
    [execute]
  );

  const sortData = useCallback(
    async (data: Record<string, unknown>[], key: string, order: "asc" | "desc") => {
      setProcessing(true);
      setError(null);

      try {
        const result = await execute(WorkerMessageType.SORT_DATA, { data, key, order });
        return result;
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        throw error;
      } finally {
        setProcessing(false);
      }
    },
    [execute]
  );

  return {
    computeMetrics,
    aggregateData,
    filterData,
    sortData,
    processing,
    error,
  };
}

/**
 * Hook to monitor worker pool stats
 */
export function useWorkerStats(interval: number = 1000) {
  const { getStats } = useWorkerPool();
  const [stats, setStats] = useState(getStats());

  useEffect(() => {
    const updateStats = () => {
      setStats(getStats());
    };

    const intervalId = setInterval(updateStats, interval);
    return () => clearInterval(intervalId);
  }, [getStats, interval]);

  return stats;
}

/**
 * Hook to cleanup worker pool on app unmount
 */
export function useWorkerPoolCleanup() {
  useEffect(() => {
    return () => {
      destroyWorkerPool();
    };
  }, []);
}
