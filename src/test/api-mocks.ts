/**
 * API mocking utilities for testing
 */

import { vi } from "vitest";

import {
  createMockDataset,
  createMockEstimates,
  createMockHardwareInfo,
  createMockModel,
  createMockPausedRun,
  createMockPreset,
  createMockProfile,
  createMockTrainingRun,
} from "./mock-factories";

// ============================================================================
// API Response Types
// ============================================================================

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

// ============================================================================
// Mock API Endpoints
// ============================================================================

export const mockApiEndpoints = {
  // Hardware endpoints
  "/api/hardware/detect": () => createMockHardwareInfo(),
  "/api/hardware/status": () => createMockHardwareInfo(),

  // Profile endpoints
  "/api/profiles": () => ({
    items: [
      createMockProfile({ id: "chatbot", name: "Chatbot" }),
      createMockProfile({ id: "code", name: "Code Generation" }),
    ],
    total: 2,
  }),
  "/api/profiles/:id": (id: string) => createMockProfile({ id }),

  // Dataset endpoints
  "/api/datasets": () => ({
    items: [createMockDataset()],
    total: 1,
  }),
  "/api/datasets/:id": (id: string) => createMockDataset({ id }),
  "/api/datasets/upload": () => ({ success: true, dataset_id: "new-dataset" }),

  // Model endpoints
  "/api/models/search": () => ({
    items: [createMockModel()],
    total: 1,
  }),
  "/api/models/:id": (id: string) => createMockModel({ model_id: id }),

  // Training endpoints
  "/api/training/start": () => ({ job_id: "new-job-123", status: "started" }),
  "/api/training/runs": () => ({
    items: [
      createMockTrainingRun({ id: 1, status: "running" }),
      createMockTrainingRun({ id: 2, status: "completed" }),
    ],
    total: 2,
  }),
  "/api/training/runs/:id": (id: string) =>
    createMockTrainingRun({ id: parseInt(id) }),
  "/api/training/runs/:id/pause": () => ({ success: true }),
  "/api/training/runs/:id/resume": () => ({ success: true }),
  "/api/training/runs/:id/stop": () => ({ success: true }),

  // Paused runs endpoints
  "/api/training/paused": () => ({
    items: [createMockPausedRun()],
    total: 1,
  }),

  // Estimates endpoints
  "/api/estimates": () => createMockEstimates(),

  // Presets endpoints
  "/api/presets": () => ({
    items: [createMockPreset()],
    total: 1,
  }),
  "/api/presets/:id": (id: string) => createMockPreset({ id }),
  "/api/presets/save": () => ({ success: true, preset_id: "new-preset" }),
};

// ============================================================================
// Mock API Client
// ============================================================================

export class MockApiClient {
  private handlers: Map<string, (params?: any) => any> = new Map();
  private callLog: Array<{ endpoint: string; params?: any; timestamp: number }> =
    [];

  constructor() {
    this.setupDefaultHandlers();
  }

  private setupDefaultHandlers() {
    Object.entries(mockApiEndpoints).forEach(([endpoint, handler]) => {
      this.handlers.set(endpoint, handler);
    });
  }

  /**
   * Register a custom handler for an endpoint
   */
  registerHandler(endpoint: string, handler: (params?: any) => any) {
    this.handlers.set(endpoint, handler);
  }

  /**
   * Mock a successful API call
   */
  mockSuccess<T>(endpoint: string, data: T): void {
    this.handlers.set(endpoint, () => data);
  }

  /**
   * Mock an API error
   */
  mockError(endpoint: string, error: string, status: number = 500): void {
    this.handlers.set(endpoint, () => {
      throw new Error(error);
    });
  }

  /**
   * Mock a delayed response
   */
  mockDelayed<T>(endpoint: string, data: T, delayMs: number): void {
    this.handlers.set(endpoint, async () => {
      await new Promise((resolve) => setTimeout(resolve, delayMs));
      return data;
    });
  }

  /**
   * Get handler for endpoint
   */
  getHandler(endpoint: string): ((params?: any) => any) | undefined {
    // Try exact match first
    if (this.handlers.has(endpoint)) {
      return this.handlers.get(endpoint);
    }

    // Try pattern matching for parameterized routes
    for (const [pattern, handler] of this.handlers.entries()) {
      if (pattern.includes(":")) {
        const regex = new RegExp(
          "^" + pattern.replace(/:[^/]+/g, "([^/]+)") + "$",
        );
        const match = endpoint.match(regex);
        if (match) {
          return (params?: any) => (handler as any)(match[1], params);
        }
      }
    }

    return undefined;
  }

  /**
   * Call an endpoint
   */
  async call<T>(endpoint: string, params?: any): Promise<T> {
    this.callLog.push({ endpoint, params, timestamp: Date.now() });

    const handler = this.getHandler(endpoint);
    if (!handler) {
      throw new Error(`No handler registered for endpoint: ${endpoint}`);
    }

    return handler(params);
  }

  /**
   * Get call log
   */
  getCallLog() {
    return [...this.callLog];
  }

  /**
   * Clear call log
   */
  clearCallLog() {
    this.callLog = [];
  }

  /**
   * Reset all handlers to defaults
   */
  reset() {
    this.handlers.clear();
    this.callLog = [];
    this.setupDefaultHandlers();
  }
}

// ============================================================================
// Global Mock API Instance
// ============================================================================

export const mockApi = new MockApiClient();

// ============================================================================
// Fetch Mock Setup
// ============================================================================

/**
 * Setup fetch mock to use MockApiClient
 */
export function setupFetchMock(): void {
  global.fetch = vi.fn(async (url: RequestInfo | URL, options?: RequestInit) => {
    const urlString = url.toString();
    const endpoint = urlString.replace(/^https?:\/\/[^/]+/, "");

    try {
      const data = await mockApi.call(endpoint, options?.body);
      return new Response(JSON.stringify(data), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    } catch (error) {
      return new Response(
        JSON.stringify({ error: (error as Error).message }),
        {
          status: 500,
          headers: { "Content-Type": "application/json" },
        },
      );
    }
  });
}

/**
 * Restore original fetch
 */
export function restoreFetch(): void {
  if (vi.isMockFunction(global.fetch)) {
    (global.fetch as any).mockRestore();
  }
}

// ============================================================================
// WebSocket Mock
// ============================================================================

export class MockWebSocket {
  public url: string;
  public readyState: number = WebSocket.CONNECTING;
  public onopen: ((event: Event) => void) | null = null;
  public onmessage: ((event: MessageEvent) => void) | null = null;
  public onerror: ((event: Event) => void) | null = null;
  public onclose: ((event: CloseEvent) => void) | null = null;

  private messageQueue: unknown[] = [];

  constructor(url: string) {
    this.url = url;
    // Simulate connection opening
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event("open"));
      }
    }, 0);
  }

  send(data: string): void {
    if (this.readyState !== WebSocket.OPEN) {
      throw new Error("WebSocket is not open");
    }
    // Store sent messages for testing
    this.messageQueue.push(JSON.parse(data));
  }

  close(): void {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent("close"));
    }
  }

  // Test helper: simulate receiving a message
  simulateMessage(data: any): void {
    if (this.onmessage) {
      this.onmessage(
        new MessageEvent("message", {
          data: JSON.stringify(data),
        }),
      );
    }
  }

  // Test helper: simulate an error
  simulateError(): void {
    if (this.onerror) {
      this.onerror(new Event("error"));
    }
  }

  // Test helper: get sent messages
  getSentMessages(): unknown[] {
    return [...this.messageQueue];
  }

  // Test helper: clear message queue
  clearMessages(): void {
    this.messageQueue = [];
  }
}

/**
 * Setup WebSocket mock
 */
export function setupWebSocketMock(): void {
  (global as any).WebSocket = MockWebSocket;
}

/**
 * Restore original WebSocket
 */
export function restoreWebSocket(): void {
  delete (global as any).WebSocket;
}

// ============================================================================
// Server-Sent Events Mock
// ============================================================================

export class MockEventSource {
  public url: string;
  public readyState: number = 0; // CONNECTING
  public onopen: ((event: Event) => void) | null = null;
  public onmessage: ((event: MessageEvent) => void) | null = null;
  public onerror: ((event: Event) => void) | null = null;

  private listeners: Map<string, Array<(event: MessageEvent) => void>> =
    new Map();

  constructor(url: string) {
    this.url = url;
    // Simulate connection opening
    setTimeout(() => {
      this.readyState = 1; // OPEN
      if (this.onopen) {
        this.onopen(new Event("open"));
      }
    }, 0);
  }

  addEventListener(
    type: string,
    listener: (event: MessageEvent) => void,
  ): void {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, []);
    }
    this.listeners.get(type)!.push(listener);
  }

  removeEventListener(
    type: string,
    listener: (event: MessageEvent) => void,
  ): void {
    const listeners = this.listeners.get(type);
    if (listeners) {
      const index = listeners.indexOf(listener);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }

  close(): void {
    this.readyState = 2; // CLOSED
  }

  // Test helper: simulate receiving an event
  simulateEvent(type: string, data: any): void {
    const event = new MessageEvent(type, {
      data: JSON.stringify(data),
    });

    if (type === "message" && this.onmessage) {
      this.onmessage(event);
    }

    const listeners = this.listeners.get(type);
    if (listeners) {
      listeners.forEach((listener) => listener(event));
    }
  }

  // Test helper: simulate an error
  simulateError(): void {
    if (this.onerror) {
      this.onerror(new Event("error"));
    }
  }
}

/**
 * Setup EventSource mock
 */
export function setupEventSourceMock(): void {
  (global as any).EventSource = MockEventSource;
}

/**
 * Restore original EventSource
 */
export function restoreEventSource(): void {
  delete (global as any).EventSource;
}
