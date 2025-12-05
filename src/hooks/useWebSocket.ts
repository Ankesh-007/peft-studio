import { useState, useEffect, useCallback, useRef } from "react";
import { webSocketManager } from "../lib/WebSocketManager";

export interface UseWebSocketOptions {
  /**
   * Whether to automatically connect on mount
   * @default true
   */
  autoConnect?: boolean;

  /**
   * Callback when connection status changes
   */
  onConnectionChange?: (connected: boolean) => void;

  /**
   * Callback when an error occurs
   */
  onError?: (error: Error) => void;
}

export interface UseWebSocketResult<T = unknown> {
  /**
   * Latest message received
   */
  data: T | null;

  /**
   * Connection status
   */
  isConnected: boolean;

  /**
   * Error message if any
   */
  error: string | null;

  /**
   * Manually connect to WebSocket
   */
  connect: () => void;

  /**
   * Disconnect from WebSocket
   */
  disconnect: () => void;

  /**
   * Send a message through the WebSocket
   */
  send: (message: string | object) => void;

  /**
   * Subscribe to specific message types
   */
  subscribe: (handler: (data: T) => void) => () => void;
}

/**
 * Hook for managing WebSocket connections
 *
 * @example
 * ```tsx
 * const { data, isConnected, send } = useWebSocket<TrainingMetrics>(
 *   'ws://localhost:8000/ws/training/job-123',
 *   {
 *     autoConnect: true,
 *     onConnectionChange: (connected) => console.log('Connected:', connected)
 *   }
 * );
 * ```
 */
export function useWebSocket<T = unknown>(
  url: string,
  options: UseWebSocketOptions = {}
): UseWebSocketResult<T> {
  const { autoConnect = true, onConnectionChange, onError } = options;

  const [data, setData] = useState<T | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const connectionKeyRef = useRef<string | null>(null);
  const subscriptionIdRef = useRef<string | null>(null);
  const statusCheckIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    try {
      // Connect to WebSocket
      const key = webSocketManager.connect(url);
      connectionKeyRef.current = key;

      // Subscribe to messages
      const subId = webSocketManager.subscribe(key, (message: any) => {
        setData(message as T);
        setError(null);
      });
      subscriptionIdRef.current = subId;

      // Start checking connection status
      statusCheckIntervalRef.current = setInterval(() => {
        if (connectionKeyRef.current) {
          const connected = webSocketManager.isConnected(connectionKeyRef.current);
          setIsConnected(connected);
          onConnectionChange?.(connected);
        }
      }, 1000);

      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to connect";
      setError(errorMessage);
      onError?.(err instanceof Error ? err : new Error(errorMessage));
    }
  }, [url, onConnectionChange, onError]);

  const disconnect = useCallback(() => {
    // Clear status check interval
    if (statusCheckIntervalRef.current) {
      clearInterval(statusCheckIntervalRef.current);
      statusCheckIntervalRef.current = null;
    }

    // Unsubscribe and disconnect
    if (connectionKeyRef.current && subscriptionIdRef.current) {
      webSocketManager.unsubscribe(connectionKeyRef.current, subscriptionIdRef.current);
      subscriptionIdRef.current = null;
      connectionKeyRef.current = null;
    }

    setIsConnected(false);
  }, []);

  const send = useCallback((message: string | object) => {
    if (connectionKeyRef.current) {
      webSocketManager.send(connectionKeyRef.current, message);
    } else {
      console.warn("Cannot send message: not connected");
    }
  }, []);

  const subscribe = useCallback((handler: (data: T) => void): (() => void) => {
    if (!connectionKeyRef.current) {
      console.warn("Cannot subscribe: not connected");
      return () => { };
    }

    const subId = webSocketManager.subscribe(connectionKeyRef.current, handler as any);

    // Return unsubscribe function
    return () => {
      if (connectionKeyRef.current) {
        webSocketManager.unsubscribe(connectionKeyRef.current, subId);
      }
    };
  }, []);

  // Auto-connect on mount if enabled
  useEffect(() => {
    if (autoConnect) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    data,
    isConnected,
    error,
    connect,
    disconnect,
    send,
    subscribe,
  };
}
