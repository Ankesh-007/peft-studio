import { useState, useEffect, useCallback, useRef } from "react";

export interface TrainingMetrics {
  step: number;
  epoch: number;
  loss: number;
  learning_rate: number;
  grad_norm?: number;
  throughput: number;
  samples_per_second: number;
  gpu_utilization: number[];
  gpu_memory_used: number[];
  gpu_temperature: number[];
  cpu_utilization: number;
  ram_used: number;
  val_loss?: number;
  val_perplexity?: number;
  timestamp: string;
  elapsed_time: number;
  estimated_time_remaining: number;
}

export interface UseTrainingMonitorResult {
  metrics: TrainingMetrics | null;
  metricsHistory: TrainingMetrics[];
  isConnected: boolean;
  error: string | null;
  connect: () => void;
  disconnect: () => void;
}

const WS_URL = "ws://127.0.0.1:8000/ws/training";

export function useTrainingMonitor(jobId: string): UseTrainingMonitorResult {
  const [metrics, setMetrics] = useState<TrainingMetrics | null>(null);
  const [metricsHistory, setMetricsHistory] = useState<TrainingMetrics[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;

  const connectRef = useRef<() => void>(() => {});

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    try {
      const ws = new WebSocket(`${WS_URL}/${jobId}`);

      ws.onopen = () => {
        console.log(`WebSocket connected for job ${jobId}`);
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          if (message.type === "metrics" && message.data) {
            const newMetrics = message.data as TrainingMetrics;
            setMetrics(newMetrics);
            setMetricsHistory((prev) => [...prev, newMetrics].slice(-100)); // Keep last 100
          } else if (message.type === "connected") {
            console.log("Connected to training metrics stream");
          } else if (message.type === "pong") {
            // Heartbeat response
          }
        } catch (err) {
          console.error("Error parsing WebSocket message:", err);
        }
      };

      ws.onerror = (event) => {
        console.error("WebSocket error:", event);
        setError("WebSocket connection error");
      };

      ws.onclose = () => {
        console.log("WebSocket disconnected");
        setIsConnected(false);
        wsRef.current = null;

        // Attempt to reconnect
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current += 1;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
          console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current})`);

          reconnectTimeoutRef.current = setTimeout(() => {
            connectRef.current();
          }, delay);
        } else {
          setError("Failed to connect after multiple attempts");
        }
      };

      wsRef.current = ws;
    } catch (err) {
      console.error("Error creating WebSocket:", err);
      setError("Failed to create WebSocket connection");
    }
  }, [jobId]);

  useEffect(() => {
    connectRef.current = connect;
  }, [connect]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
    reconnectAttemptsRef.current = 0;
  }, []);

  // Send periodic ping to keep connection alive
  useEffect(() => {
    if (!isConnected || !wsRef.current) return;

    const pingInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send("ping");
      }
    }, 30000); // Ping every 30 seconds

    return () => clearInterval(pingInterval);
  }, [isConnected]);

  // Auto-connect on mount
  useEffect(() => {
    // Call connect in a setTimeout to avoid calling setState during render
    const timer = setTimeout(() => {
      connect();
    }, 0);

    return () => {
      clearTimeout(timer);
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    metrics,
    metricsHistory,
    isConnected,
    error,
    connect,
    disconnect,
  };
}
