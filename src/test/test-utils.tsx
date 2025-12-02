/**
 * Test utilities for common component testing patterns
 */

import { render, RenderOptions } from "@testing-library/react";
import { ReactElement } from "react";
import { vi } from "vitest";

// ============================================================================
// Component Testing Utilities
// ============================================================================

/**
 * Custom render function that wraps components with common providers
 */
export function renderWithProviders(
  ui: ReactElement,
  options?: Omit<RenderOptions, "wrapper">,
) {
  // For now, just use standard render
  // Can be extended with providers like Router, Theme, etc.
  return render(ui, options);
}

/**
 * Wait for async operations to complete
 */
export async function waitForAsync(ms: number = 0): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Simulate user typing with realistic delays
 */
export async function typeWithDelay(
  element: HTMLElement,
  text: string,
  delayMs: number = 50,
): Promise<void> {
  const { fireEvent } = await import("@testing-library/react");

  for (const char of text) {
    fireEvent.change(element, {
      target: { value: (element as HTMLInputElement).value + char },
    });
    await waitForAsync(delayMs);
  }
}

/**
 * Get all text content from an element and its children
 */
export function getAllTextContent(element: HTMLElement): string {
  return element.textContent || "";
}

/**
 * Check if element has specific CSS class
 */
export function hasClass(element: HTMLElement, className: string): boolean {
  return element.classList.contains(className);
}

/**
 * Get computed style property value
 */
export function getStyleProperty(
  element: HTMLElement,
  property: string,
): string {
  return window.getComputedStyle(element).getPropertyValue(property);
}

// ============================================================================
// Async Testing Helpers
// ============================================================================

/**
 * Wait for a condition to be true
 */
export async function waitForCondition(
  condition: () => boolean,
  timeout: number = 5000,
  interval: number = 100,
): Promise<void> {
  const startTime = Date.now();

  while (!condition()) {
    if (Date.now() - startTime > timeout) {
      throw new Error("Timeout waiting for condition");
    }
    await waitForAsync(interval);
  }
}

/**
 * Create a promise that resolves after a delay
 */
export function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Create a promise that rejects after a delay
 */
export function delayedReject(ms: number, error: Error): Promise<never> {
  return new Promise((_, reject) => setTimeout(() => reject(error), ms));
}

// ============================================================================
// API Mocking Helpers
// ============================================================================

/**
 * Create a mock API response
 */
export function createMockResponse<T>(
  data: T,
  options: {
    status?: number;
    statusText?: string;
    headers?: Record<string, string>;
  } = {},
): Response {
  const { status = 200, statusText = "OK", headers = {} } = options;

  return new Response(JSON.stringify(data), {
    status,
    statusText,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
  });
}

/**
 * Create a mock API error response
 */
export function createMockErrorResponse(
  message: string,
  status: number = 500,
): Response {
  return createMockResponse(
    { error: message },
    { status, statusText: "Error" },
  );
}

/**
 * Mock fetch with custom responses
 */
export function mockFetch(
  responses: Record<string, any> | ((url: string) => any),
): void {
  global.fetch = vi.fn((url: string) => {
    const data = typeof responses === "function" ? responses(url) : responses[url];

    if (!data) {
      return Promise.resolve(createMockErrorResponse("Not found", 404));
    }

    return Promise.resolve(createMockResponse(data));
  });
}

/**
 * Mock fetch to reject with error
 */
export function mockFetchError(error: Error): void {
  global.fetch = vi.fn(() => Promise.reject(error));
}

/**
 * Mock fetch to timeout
 */
export function mockFetchTimeout(timeoutMs: number = 5000): void {
  global.fetch = vi.fn(
    () =>
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error("Request timeout")), timeoutMs),
      ),
  );
}

/**
 * Create a mock API handler that tracks calls
 */
export function createMockApiHandler<T = any>() {
  const calls: Array<{ url: string; options?: RequestInit }> = [];

  const handler = vi.fn((url: string, options?: RequestInit) => {
    calls.push({ url, options });
    return Promise.resolve(createMockResponse({} as T));
  });

  return {
    handler,
    calls,
    reset: () => {
      calls.length = 0;
      handler.mockClear();
    },
  };
}

// ============================================================================
// Event Simulation Helpers
// ============================================================================

/**
 * Simulate file upload
 */
export function createMockFile(
  name: string,
  size: number,
  type: string,
  content: string = "",
): File {
  const blob = new Blob([content], { type });
  return new File([blob], name, { type });
}

/**
 * Simulate drag and drop event
 */
export function createDragEvent(
  type: string,
  files: File[],
): DragEvent {
  const dataTransfer = new DataTransfer();
  files.forEach((file) => dataTransfer.items.add(file));

  return new DragEvent(type, {
    bubbles: true,
    cancelable: true,
    dataTransfer,
  });
}

// ============================================================================
// LocalStorage Mocking
// ============================================================================

/**
 * Create a mock localStorage
 */
export function createMockLocalStorage(): Storage {
  const store: Record<string, string> = {};

  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      Object.keys(store).forEach((key) => delete store[key]);
    }),
    key: vi.fn((index: number) => Object.keys(store)[index] || null),
    get length() {
      return Object.keys(store).length;
    },
  };
}

/**
 * Setup mock localStorage for tests
 */
export function setupMockLocalStorage(): void {
  global.localStorage = createMockLocalStorage();
}

// ============================================================================
// Console Mocking
// ============================================================================

/**
 * Suppress console errors during tests
 */
export function suppressConsoleErrors(): void {
  const originalError = console.error;
  console.error = vi.fn();

  return () => {
    console.error = originalError;
  };
}

/**
 * Suppress console warnings during tests
 */
export function suppressConsoleWarnings(): void {
  const originalWarn = console.warn;
  console.warn = vi.fn();

  return () => {
    console.warn = originalWarn;
  };
}

// ============================================================================
// Re-export commonly used testing library functions
// ============================================================================

export * from "@testing-library/react";
export { default as userEvent } from "@testing-library/user-event";
