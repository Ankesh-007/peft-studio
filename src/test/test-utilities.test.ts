/**
 * Tests for test utilities to demonstrate their usage
 */

import { describe, it, expect, beforeEach } from "vitest";

import {
  createMockDataset,
  createMockModel,
  createMockProfile,
  createMockTrainingRun,
  createMockWizardState,
  createMockPausedRun,
  createMockEstimates,
  mockApi,
  setupFetchMock,
  restoreFetch,
  MockWebSocket,
} from "./index";

describe("Test Utilities", () => {
  describe("Custom Matchers", () => {
    it("should validate numbers within range", () => {
      expect(50).toBeWithinRange(0, 100);
      expect(0).toBeWithinRange(0, 100);
      expect(100).toBeWithinRange(0, 100);
    });

    it("should validate timestamps", () => {
      const validTimestamp = new Date().toISOString();
      expect(validTimestamp).toHaveValidTimestamp();
    });

    it("should validate percentages", () => {
      expect(0).toBeValidPercentage();
      expect(50).toBeValidPercentage();
      expect(100).toBeValidPercentage();
    });

    it("should validate required fields", () => {
      const obj = { name: "test", id: 123, value: "data" };
      expect(obj).toHaveRequiredFields(["name", "id"]);
    });
  });

  describe("Mock Factories", () => {
    it("should create mock profile with defaults", () => {
      const profile = createMockProfile();
      expect(profile).toHaveRequiredFields([
        "id",
        "name",
        "config",
        "requirements",
      ]);
      expect(profile.config.lora_r).toBe(16);
    });

    it("should create mock profile with overrides", () => {
      const profile = createMockProfile({ id: "custom-id", name: "Custom" });
      expect(profile.id).toBe("custom-id");
      expect(profile.name).toBe("Custom");
    });

    it("should create mock dataset", () => {
      const dataset = createMockDataset();
      expect(dataset).toHaveRequiredFields(["id", "name", "path", "format"]);
      expect(dataset.size).toBeGreaterThan(0);
    });

    it("should create mock model", () => {
      const model = createMockModel();
      expect(model).toHaveRequiredFields([
        "model_id",
        "author",
        "model_name",
      ]);
      expect(model.parameters).toBeGreaterThan(0);
    });

    it("should create mock training run", () => {
      const run = createMockTrainingRun();
      expect(run).toHaveRequiredFields(["id", "name", "status", "progress"]);
      expect(run.progress).toBeValidPercentage();
    });

    it("should create mock wizard state", () => {
      const state = createMockWizardState();
      expect(state).toHaveRequiredFields([
        "currentStep",
        "config",
        "validation",
      ]);
      expect(state.currentStep).toBeWithinRange(0, 10);
    });

    it("should create mock paused run", () => {
      const pausedRun = createMockPausedRun();
      expect(pausedRun).toHaveRequiredFields([
        "job_id",
        "state",
        "paused_at",
        "resource_usage",
      ]);
      expect(pausedRun.state).toBe("paused");
    });

    it("should create mock estimates", () => {
      const estimates = createMockEstimates();
      expect(estimates).toHaveRequiredFields(["duration", "cost", "resources"]);
      expect(estimates.confidence).toBeValidPercentage();
    });
  });

  describe("API Mocking", () => {
    beforeEach(() => {
      mockApi.reset();
      setupFetchMock();
    });

    afterEach(() => {
      restoreFetch();
    });

    it("should mock API endpoints", async () => {
      const data = await mockApi.call("/api/hardware/detect");
      expect(data).toHaveProperty("gpus");
      expect(data).toHaveProperty("cpu");
      expect(data).toHaveProperty("ram");
    });

    it("should track API calls", async () => {
      mockApi.clearCallLog();
      await mockApi.call("/api/profiles");
      await mockApi.call("/api/datasets");

      const log = mockApi.getCallLog();
      expect(log).toHaveLength(2);
      expect(log[0].endpoint).toBe("/api/profiles");
      expect(log[1].endpoint).toBe("/api/datasets");
    });

    it("should handle custom mock responses", async () => {
      mockApi.mockSuccess("/api/custom", { custom: "data" });
      const data = await mockApi.call("/api/custom");
      expect(data).toEqual({ custom: "data" });
    });

    it("should handle mock errors", async () => {
      mockApi.mockError("/api/error", "Test error");
      await expect(mockApi.call("/api/error")).rejects.toThrow("Test error");
    });
  });

  describe("WebSocket Mocking", () => {
    it("should create mock WebSocket", () => {
      const ws = new MockWebSocket("ws://localhost:8000");
      expect(ws.url).toBe("ws://localhost:8000");
      expect(ws.readyState).toBe(WebSocket.CONNECTING);
    });

    it("should simulate WebSocket connection", async () => {
      const ws = new MockWebSocket("ws://localhost:8000");
      
      await new Promise<void>((resolve) => {
        ws.onopen = () => {
          expect(ws.readyState).toBe(WebSocket.OPEN);
          resolve();
        };
      });
    });

    it("should simulate receiving messages", async () => {
      const ws = new MockWebSocket("ws://localhost:8000");
      
      const messagePromise = new Promise<void>((resolve) => {
        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          expect(data).toEqual({ test: "message" });
          resolve();
        };
      });

      setTimeout(() => {
        ws.simulateMessage({ test: "message" });
      }, 10);

      await messagePromise;
    });

    it("should track sent messages", async () => {
      const ws = new MockWebSocket("ws://localhost:8000");
      
      await new Promise<void>((resolve) => {
        ws.onopen = () => {
          ws.send(JSON.stringify({ action: "test" }));
          const sent = ws.getSentMessages();
          expect(sent).toHaveLength(1);
          expect(sent[0]).toEqual({ action: "test" });
          resolve();
        };
      });
    });
  });
});
