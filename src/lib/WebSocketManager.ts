/**
 * Centralized WebSocket Manager
 * Provides connection pooling, automatic reconnection, and message routing
 */

type MessageHandler = (data: any) => void;
type ConnectionStatusHandler = (connected: boolean) => void;

interface Subscription {
  id: string;
  handler: MessageHandler;
}

interface WebSocketConnection {
  ws: WebSocket;
  url: string;
  subscriptions: Map<string, Subscription>;
  reconnectAttempts: number;
  reconnectTimeout: NodeJS.Timeout | null;
  isIntentionallyClosed: boolean;
}

export class WebSocketManager {
  private connections: Map<string, WebSocketConnection> = new Map();
  private maxReconnectAttempts = 5;
  private baseReconnectDelay = 1000; // 1 second
  private maxReconnectDelay = 30000; // 30 seconds
  private pingInterval = 30000; // 30 seconds
  private pingTimers: Map<string, NodeJS.Timeout> = new Map();

  /**
   * Connect to a WebSocket endpoint
   * @param url WebSocket URL
   * @returns Connection key for managing this connection
   */
  connect(url: string): string {
    const key = url;

    // Return existing connection if already connected
    if (this.connections.has(key)) {
      const conn = this.connections.get(key)!;
      if (conn.ws.readyState === WebSocket.OPEN) {
        return key;
      }
    }

    this.createConnection(key, url);
    return key;
  }

  /**
   * Subscribe to messages from a WebSocket connection
   * @param connectionKey Connection key returned from connect()
   * @param handler Message handler function
   * @returns Subscription ID for unsubscribing
   */
  subscribe(connectionKey: string, handler: MessageHandler): string {
    const conn = this.connections.get(connectionKey);
    if (!conn) {
      throw new Error(`No connection found for key: ${connectionKey}`);
    }

    const subscriptionId = `sub-${Date.now()}-${Math.random()}`;
    conn.subscriptions.set(subscriptionId, {
      id: subscriptionId,
      handler,
    });

    return subscriptionId;
  }

  /**
   * Unsubscribe from messages
   * @param connectionKey Connection key
   * @param subscriptionId Subscription ID returned from subscribe()
   */
  unsubscribe(connectionKey: string, subscriptionId: string): void {
    const conn = this.connections.get(connectionKey);
    if (conn) {
      conn.subscriptions.delete(subscriptionId);

      // Close connection if no more subscribers
      if (conn.subscriptions.size === 0) {
        this.disconnect(connectionKey);
      }
    }
  }

  /**
   * Send a message through a WebSocket connection
   * @param connectionKey Connection key
   * @param message Message to send (will be JSON stringified if object)
   */
  send(connectionKey: string, message: string | object): void {
    const conn = this.connections.get(connectionKey);
    if (!conn || conn.ws.readyState !== WebSocket.OPEN) {
      console.warn(`Cannot send message: connection not open for ${connectionKey}`);
      return;
    }

    const data = typeof message === "string" ? message : JSON.stringify(message);
    conn.ws.send(data);
  }

  /**
   * Disconnect from a WebSocket
   * @param connectionKey Connection key
   */
  disconnect(connectionKey: string): void {
    const conn = this.connections.get(connectionKey);
    if (!conn) return;

    conn.isIntentionallyClosed = true;

    // Clear reconnect timeout
    if (conn.reconnectTimeout) {
      clearTimeout(conn.reconnectTimeout);
      conn.reconnectTimeout = null;
    }

    // Clear ping timer
    const pingTimer = this.pingTimers.get(connectionKey);
    if (pingTimer) {
      clearInterval(pingTimer);
      this.pingTimers.delete(connectionKey);
    }

    // Close WebSocket
    if (conn.ws.readyState === WebSocket.OPEN || conn.ws.readyState === WebSocket.CONNECTING) {
      conn.ws.close();
    }

    this.connections.delete(connectionKey);
  }

  /**
   * Get connection status
   * @param connectionKey Connection key
   * @returns true if connected, false otherwise
   */
  isConnected(connectionKey: string): boolean {
    const conn = this.connections.get(connectionKey);
    return conn ? conn.ws.readyState === WebSocket.OPEN : false;
  }

  /**
   * Disconnect all connections
   */
  disconnectAll(): void {
    const keys = Array.from(this.connections.keys());
    keys.forEach((key) => this.disconnect(key));
  }

  private createConnection(key: string, url: string): void {
    const ws = new WebSocket(url);

    const connection: WebSocketConnection = {
      ws,
      url,
      subscriptions: new Map(),
      reconnectAttempts: 0,
      reconnectTimeout: null,
      isIntentionallyClosed: false,
    };

    ws.onopen = () => {
      console.log(`WebSocket connected: ${url}`);
      connection.reconnectAttempts = 0;
      this.startPingTimer(key);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // Broadcast to all subscribers
        connection.subscriptions.forEach((sub) => {
          try {
            sub.handler(data);
          } catch (err) {
            console.error("Error in subscription handler:", err);
          }
        });
      } catch (err) {
        console.error("Error parsing WebSocket message:", err);
      }
    };

    ws.onerror = (event) => {
      console.error(`WebSocket error for ${url}:`, event);
    };

    ws.onclose = () => {
      console.log(`WebSocket closed: ${url}`);
      
      // Clear ping timer
      const pingTimer = this.pingTimers.get(key);
      if (pingTimer) {
        clearInterval(pingTimer);
        this.pingTimers.delete(key);
      }

      // Attempt reconnection if not intentionally closed
      if (!connection.isIntentionallyClosed) {
        this.attemptReconnect(key, connection);
      }
    };

    this.connections.set(key, connection);
  }

  private attemptReconnect(key: string, connection: WebSocketConnection): void {
    if (connection.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error(`Max reconnection attempts reached for ${connection.url}`);
      this.connections.delete(key);
      return;
    }

    connection.reconnectAttempts += 1;
    const delay = Math.min(
      this.baseReconnectDelay * Math.pow(2, connection.reconnectAttempts - 1),
      this.maxReconnectDelay,
    );

    console.log(
      `Reconnecting to ${connection.url} in ${delay}ms (attempt ${connection.reconnectAttempts}/${this.maxReconnectAttempts})`,
    );

    connection.reconnectTimeout = setTimeout(() => {
      this.createConnection(key, connection.url);
    }, delay);
  }

  private startPingTimer(key: string): void {
    // Clear existing timer
    const existingTimer = this.pingTimers.get(key);
    if (existingTimer) {
      clearInterval(existingTimer);
    }

    // Start new ping timer
    const timer = setInterval(() => {
      const conn = this.connections.get(key);
      if (conn && conn.ws.readyState === WebSocket.OPEN) {
        conn.ws.send("ping");
      }
    }, this.pingInterval);

    this.pingTimers.set(key, timer);
  }
}

// Singleton instance
export const webSocketManager = new WebSocketManager();
