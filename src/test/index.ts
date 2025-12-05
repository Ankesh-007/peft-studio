/**
 * Test utilities index
 *
 * Centralized exports for all test utilities, mock factories, and API mocks
 */

// Custom matchers are automatically loaded via setup.ts

// Test utilities
export * from "./test-utils";

// Mock data factories
export * from "./mock-factories";

// API mocking utilities
export * from "./api-mocks";

// Re-export vitest for convenience
export { describe, it, test, expect, vi, beforeEach, afterEach, beforeAll, afterAll } from "vitest";
