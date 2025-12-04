import "@testing-library/jest-dom";

import { expect, vi, beforeEach } from "vitest";

// ============================================================================
// Storage Mocks (for E2E tests)
// ============================================================================

// Mock localStorage and sessionStorage for jsdom environment
class StorageMock {
  private store: Record<string, string> = {};

  clear() {
    this.store = {};
  }

  getItem(key: string) {
    return this.store[key] || null;
  }

  setItem(key: string, value: string) {
    this.store[key] = String(value);
  }

  removeItem(key: string) {
    delete this.store[key];
  }

  get length() {
    return Object.keys(this.store).length;
  }

  key(index: number) {
    const keys = Object.keys(this.store);
    return keys[index] || null;
  }
}

// Setup storage mocks before each test
beforeEach(() => {
  if (typeof window !== 'undefined') {
    Object.defineProperty(window, 'localStorage', {
      value: new StorageMock(),
      writable: true,
    });
    Object.defineProperty(window, 'sessionStorage', {
      value: new StorageMock(),
      writable: true,
    });
  }
});

// ============================================================================
// Custom Matchers
// ============================================================================

interface CustomMatchers<R = unknown> {
  toBeWithinRange(min: number, max: number): R;
  toHaveValidTimestamp(): R;
  toBeValidPercentage(): R;
  toHaveRequiredFields(fields: string[]): R;
}

declare module "vitest" {
  interface Assertion<T = any> extends CustomMatchers<T> { }
  interface AsymmetricMatchersContaining extends CustomMatchers { }
}

// Custom matcher: Check if number is within range
expect.extend({
  toBeWithinRange(received: number, min: number, max: number) {
    const pass = received >= min && received <= max;
    return {
      pass,
      message: () =>
        pass
          ? `Expected ${received} not to be within range ${min}-${max}`
          : `Expected ${received} to be within range ${min}-${max}`,
    };
  },
});

// Custom matcher: Check if string is a valid ISO timestamp
expect.extend({
  toHaveValidTimestamp(received: string) {
    const date = new Date(received);
    const pass = !isNaN(date.getTime());
    return {
      pass,
      message: () =>
        pass
          ? `Expected ${received} not to be a valid timestamp`
          : `Expected ${received} to be a valid timestamp`,
    };
  },
});

// Custom matcher: Check if number is a valid percentage (0-100)
expect.extend({
  toBeValidPercentage(received: number) {
    const pass = received >= 0 && received <= 100;
    return {
      pass,
      message: () =>
        pass
          ? `Expected ${received} not to be a valid percentage`
          : `Expected ${received} to be a valid percentage (0-100)`,
    };
  },
});

// Custom matcher: Check if object has required fields
expect.extend({
  toHaveRequiredFields(received: any, fields: string[]) {
    const missingFields = fields.filter((field) => !(field in received));
    const pass = missingFields.length === 0;
    return {
      pass,
      message: () =>
        pass
          ? `Expected object not to have all required fields`
          : `Expected object to have fields: ${missingFields.join(", ")}`,
    };
  },
});
// Mock lucide-react icons
import React from 'react';

// Mock lucide-react icons
vi.mock("lucide-react", () => {
  return new Proxy({}, {
    get: (target, prop) => {
      if (prop === '__esModule') return true;
      // Return a component for any named export
      return () => React.createElement('div', { 'data-testid': `icon-${String(prop).toLowerCase()}` });
    }
  });
});
