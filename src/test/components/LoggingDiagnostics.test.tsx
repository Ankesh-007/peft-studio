/**
 * Tests for Logging and Diagnostics UI
 *
 * Validates: Requirements 19.1, 19.2, 19.3, 19.4, 19.5
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import LoggingDiagnostics from "../../components/LoggingDiagnostics";

// Mock fetch
global.fetch = vi.fn();

const mockLogs = [
  {
    timestamp: "2024-01-01T10:00:00",
    error_message: "Out of memory error",
    stack_trace: 'Traceback (most recent call last):\n  File "train.py", line 42\n    OOMError',
    error_type: "oom_error",
    severity: "critical",
    context: { model: "llama-7b", batch_size: 32 },
    recent_actions: ["Started training", "Loaded model"],
    system_state: {
      timestamp: "2024-01-01T10:00:00",
      platform: "Linux",
      python_version: "3.10.0",
      cpu_usage_percent: 75.5,
      memory_usage_percent: 95.2,
      disk_usage_percent: 60.0,
    },
  },
  {
    timestamp: "2024-01-01T09:00:00",
    error_message: "Connection timeout",
    stack_trace: 'Traceback (most recent call last):\n  File "api.py", line 10\n    TimeoutError',
    error_type: "network_error",
    severity: "medium",
    context: { endpoint: "/api/train" },
    recent_actions: ["Attempted connection"],
    system_state: {
      timestamp: "2024-01-01T09:00:00",
      platform: "Linux",
      python_version: "3.10.0",
      cpu_usage_percent: 25.0,
      memory_usage_percent: 45.0,
      disk_usage_percent: 60.0,
    },
  },
];

const mockStats = {
  total_logs: 2,
  by_severity: {
    low: 0,
    medium: 1,
    high: 0,
    critical: 1,
  },
  by_error_type: {
    oom_error: 1,
    network_error: 1,
  },
  recent_actions_count: 3,
};

describe("LoggingDiagnostics", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Default mock responses
    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes("/api/logging/logs")) {
        return Promise.resolve({
          json: () => Promise.resolve({ logs: mockLogs, total: 2, filtered: false }),
        });
      }
      if (url.includes("/api/logging/stats")) {
        return Promise.resolve({
          json: () => Promise.resolve(mockStats),
        });
      }
      if (url.includes("/api/logging/debug-mode")) {
        return Promise.resolve({
          json: () => Promise.resolve({ enabled: false, verbose_logging: false }),
        });
      }
      return Promise.resolve({
        json: () => Promise.resolve({}),
      });
    });
  });

  describe("Requirement 19.1: Log viewer with filtering", () => {
    it("should display logs with severity filtering", async () => {
      render(<LoggingDiagnostics />);

      // Wait for logs to load
      await waitFor(() => {
        expect(screen.getByText("Out of memory error")).toBeInTheDocument();
      });

      // Check both logs are displayed
      expect(screen.getByText("Out of memory error")).toBeInTheDocument();
      expect(screen.getByText("Connection timeout")).toBeInTheDocument();

      // Open filters
      const filterButton = screen.getByText("Filters");
      fireEvent.click(filterButton);

      // Filter by critical severity
      const severitySelect = screen.getByLabelText("Severity");
      fireEvent.change(severitySelect, { target: { value: "critical" } });

      // Should fetch filtered logs
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining("severity=critical"));
      });
    });

    it("should filter logs by error type", async () => {
      render(<LoggingDiagnostics />);

      await waitFor(() => {
        expect(screen.getByText("Out of memory error")).toBeInTheDocument();
      });

      // Open filters
      const filterButton = screen.getByText("Filters");
      fireEvent.click(filterButton);

      // Filter by error type
      const errorTypeSelect = screen.getByLabelText("Error Type");
      fireEvent.change(errorTypeSelect, { target: { value: "oom_error" } });

      // Should fetch filtered logs
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining("error_type=oom_error"));
      });
    });

    it("should display log statistics", async () => {
      render(<LoggingDiagnostics />);

      await waitFor(() => {
        expect(screen.getByText("Total Logs")).toBeInTheDocument();
      });

      // Check stats are displayed
      expect(screen.getByText("2")).toBeInTheDocument(); // Total logs
      expect(screen.getByText("Critical")).toBeInTheDocument();
      expect(screen.getByText("High")).toBeInTheDocument();
      expect(screen.getByText("Medium")).toBeInTheDocument();
    });
  });

  describe("Requirement 19.2: Log search functionality", () => {
    it("should search logs by query", async () => {
      render(<LoggingDiagnostics />);

      await waitFor(() => {
        expect(screen.getByText("Out of memory error")).toBeInTheDocument();
      });

      // Search for "memory"
      const searchInput = screen.getByPlaceholderText("Search logs...");
      fireEvent.change(searchInput, { target: { value: "memory" } });

      // Should filter logs locally
      await waitFor(() => {
        expect(screen.getByText("Out of memory error")).toBeInTheDocument();
        // Connection timeout should not be visible (filtered out)
      });
    });

    it("should search in error messages and stack traces", async () => {
      render(<LoggingDiagnostics />);

      await waitFor(() => {
        expect(screen.getByText("Out of memory error")).toBeInTheDocument();
      });

      // Search for text in stack trace
      const searchInput = screen.getByPlaceholderText("Search logs...");
      fireEvent.change(searchInput, { target: { value: "OOMError" } });

      // Should find the log with OOMError in stack trace
      await waitFor(() => {
        expect(screen.getByText("Out of memory error")).toBeInTheDocument();
      });
    });

    it("should show no results message when search has no matches", async () => {
      render(<LoggingDiagnostics />);

      await waitFor(() => {
        expect(screen.getByText("Out of memory error")).toBeInTheDocument();
      });

      // Search for non-existent text
      const searchInput = screen.getByPlaceholderText("Search logs...");
      fireEvent.change(searchInput, { target: { value: "nonexistent" } });

      // Should show no results message
      await waitFor(() => {
        expect(screen.getByText(/No logs found/i)).toBeInTheDocument();
      });
    });
  });

  describe("Requirement 19.3: Diagnostic report generator", () => {
    it("should generate diagnostic report", async () => {
      const mockReport = {
        report_id: "report-123",
        generated_at: "2024-01-01T10:00:00",
        error_count: 2,
        download_url: "/api/logging/diagnostic-report/report-123/download",
      };

      (global.fetch as any).mockImplementation((url: string, options?: any) => {
        if (url.includes("/api/logging/diagnostic-report") && options?.method === "POST") {
          return Promise.resolve({
            json: () => Promise.resolve(mockReport),
          });
        }
        return Promise.resolve({
          json: () => Promise.resolve({ logs: mockLogs, total: 2 }),
        });
      });

      // Mock window.open
      const mockOpen = vi.fn();
      window.open = mockOpen;

      // Mock alert
      const mockAlert = vi.fn();
      window.alert = mockAlert;

      render(<LoggingDiagnostics />);

      await waitFor(() => {
        expect(screen.getByText("Generate Report")).toBeInTheDocument();
      });

      // Click generate report button
      const generateButton = screen.getByText("Generate Report");
      fireEvent.click(generateButton);

      // Should call API to generate report
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          "http://localhost:8000/api/logging/diagnostic-report",
          expect.objectContaining({
            method: "POST",
          })
        );
      });

      // Should open download URL
      await waitFor(() => {
        expect(mockOpen).toHaveBeenCalledWith(expect.stringContaining("report-123"), "_blank");
      });

      // Should show success alert
      expect(mockAlert).toHaveBeenCalledWith(expect.stringContaining("report-123"));
    });
  });

  describe("Requirement 19.4: Debug mode toggle", () => {
    it("should toggle debug mode", async () => {
      (global.fetch as any).mockImplementation((url: string, options?: any) => {
        if (url.includes("/api/logging/debug-mode")) {
          if (options?.method === "POST") {
            return Promise.resolve({
              json: () => Promise.resolve({ enabled: true, verbose_logging: true }),
            });
          }
          return Promise.resolve({
            json: () => Promise.resolve({ enabled: false, verbose_logging: false }),
          });
        }
        return Promise.resolve({
          json: () => Promise.resolve({ logs: mockLogs, total: 2 }),
        });
      });

      render(<LoggingDiagnostics />);

      await waitFor(() => {
        expect(screen.getByText(/Debug Mode OFF/i)).toBeInTheDocument();
      });

      // Click debug mode toggle
      const debugButton = screen.getByText(/Debug Mode OFF/i);
      fireEvent.click(debugButton);

      // Should call API to enable debug mode
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          "http://localhost:8000/api/logging/debug-mode",
          expect.objectContaining({
            method: "POST",
            body: JSON.stringify({ enabled: true }),
          })
        );
      });
    });

    it("should display debug mode status", async () => {
      (global.fetch as any).mockImplementation((url: string) => {
        if (url.includes("/api/logging/debug-mode")) {
          return Promise.resolve({
            json: () => Promise.resolve({ enabled: true, verbose_logging: true }),
          });
        }
        return Promise.resolve({
          json: () => Promise.resolve({ logs: mockLogs, total: 2 }),
        });
      });

      render(<LoggingDiagnostics />);

      await waitFor(() => {
        expect(screen.getByText(/Debug Mode ON/i)).toBeInTheDocument();
      });
    });
  });

  describe("Requirement 19.5: Log export functionality", () => {
    it("should export logs to file", async () => {
      const mockExport = {
        success: true,
        filepath: "/home/user/.peft-studio/logs/export_20240101_100000.json",
        log_count: 2,
      };

      (global.fetch as any).mockImplementation((url: string, options?: any) => {
        if (url.includes("/api/logging/export") && options?.method === "POST") {
          return Promise.resolve({
            json: () => Promise.resolve(mockExport),
          });
        }
        return Promise.resolve({
          json: () => Promise.resolve({ logs: mockLogs, total: 2 }),
        });
      });

      // Mock alert
      const mockAlert = vi.fn();
      window.alert = mockAlert;

      render(<LoggingDiagnostics />);

      await waitFor(() => {
        expect(screen.getByText("Export")).toBeInTheDocument();
      });

      // Click export button
      const exportButton = screen.getByText("Export");
      fireEvent.click(exportButton);

      // Should call API to export logs
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          "http://localhost:8000/api/logging/export",
          expect.objectContaining({
            method: "POST",
          })
        );
      });

      // Should show success alert
      await waitFor(() => {
        expect(mockAlert).toHaveBeenCalledWith(
          expect.stringContaining("export_20240101_100000.json")
        );
      });
    });

    it("should clear all logs", async () => {
      (global.fetch as any).mockImplementation((url: string, options?: any) => {
        if (url.includes("/api/logging/logs") && options?.method === "DELETE") {
          return Promise.resolve({
            json: () => Promise.resolve({ success: true }),
          });
        }
        return Promise.resolve({
          json: () => Promise.resolve({ logs: mockLogs, total: 2 }),
        });
      });

      // Mock confirm
      const mockConfirm = vi.fn(() => true);
      window.confirm = mockConfirm;

      // Mock alert
      const mockAlert = vi.fn();
      window.alert = mockAlert;

      render(<LoggingDiagnostics />);

      await waitFor(() => {
        expect(screen.getByText("Clear")).toBeInTheDocument();
      });

      // Click clear button
      const clearButton = screen.getByText("Clear");
      fireEvent.click(clearButton);

      // Should show confirmation
      expect(mockConfirm).toHaveBeenCalled();

      // Should call API to clear logs
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          "http://localhost:8000/api/logging/logs",
          expect.objectContaining({
            method: "DELETE",
          })
        );
      });

      // Should show success alert
      await waitFor(() => {
        expect(mockAlert).toHaveBeenCalledWith(expect.stringContaining("cleared successfully"));
      });
    });
  });

  describe("Log expansion and details", () => {
    it("should expand log to show details", async () => {
      render(<LoggingDiagnostics />);

      await waitFor(() => {
        expect(screen.getByText("Out of memory error")).toBeInTheDocument();
      });

      // Click on log to expand
      const logEntry = screen.getByText("Out of memory error");
      fireEvent.click(logEntry);

      // Should show stack trace
      await waitFor(() => {
        expect(screen.getByText("Stack Trace")).toBeInTheDocument();
        expect(screen.getByText(/OOMError/)).toBeInTheDocument();
      });

      // Should show system state
      expect(screen.getByText("System State")).toBeInTheDocument();
      expect(screen.getByText("CPU Usage")).toBeInTheDocument();
      expect(screen.getByText("Memory Usage")).toBeInTheDocument();

      // Should show context
      expect(screen.getByText("Context")).toBeInTheDocument();

      // Should show recent actions
      expect(screen.getByText(/Recent Actions/)).toBeInTheDocument();
    });

    it("should copy error message to clipboard", async () => {
      // Mock clipboard API
      const mockWriteText = vi.fn();
      Object.assign(navigator, {
        clipboard: {
          writeText: mockWriteText,
        },
      });

      render(<LoggingDiagnostics />);

      await waitFor(() => {
        expect(screen.getByText("Out of memory error")).toBeInTheDocument();
      });

      // Find and click copy button
      const copyButtons = screen.getAllByTitle("Copy error message");
      fireEvent.click(copyButtons[0]);

      // Should copy to clipboard
      await waitFor(() => {
        expect(mockWriteText).toHaveBeenCalledWith("Out of memory error");
      });
    });
  });

  describe("Refresh functionality", () => {
    it("should refresh logs and stats", async () => {
      render(<LoggingDiagnostics />);

      await waitFor(() => {
        expect(screen.getByText("Refresh")).toBeInTheDocument();
      });

      // Clear previous calls
      vi.clearAllMocks();

      // Click refresh button
      const refreshButton = screen.getByText("Refresh");
      fireEvent.click(refreshButton);

      // Should fetch logs and stats again
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining("/api/logging/logs"));
        expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining("/api/logging/stats"));
      });
    });
  });
});
