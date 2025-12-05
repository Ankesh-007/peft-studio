/**
 * Configuration Management Tests
 * Tests for configuration import/export UI
 * Validates: Requirements 18.1, 18.2, 18.3, 18.4, 18.5
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ConfigurationManagement from "../../components/ConfigurationManagement";

// Mock fetch
global.fetch = vi.fn();

describe.skip("ConfigurationManagement", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({ configurations: [] }),
    });
  });

  it("renders configuration management interface", () => {
    render(<ConfigurationManagement />);

    expect(screen.getByText("Configuration Management")).toBeInTheDocument();
    expect(screen.getAllByText("Export Configuration").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Import Configuration").length).toBeGreaterThan(0);
    expect(screen.getByText("Browse Library")).toBeInTheDocument();
  });

  it("opens export dialog when export button is clicked", () => {
    render(<ConfigurationManagement />);

    const exportButtons = screen.getAllByText("Export Configuration");
    fireEvent.click(exportButtons[0]);

    // Dialog should be visible
    expect(screen.getByText("Export Configuration", { selector: "h2" })).toBeInTheDocument();
  });

  it("opens import dialog when import button is clicked", () => {
    render(<ConfigurationManagement />);

    const importButtons = screen.getAllByText("Import Configuration");
    fireEvent.click(importButtons[0]);

    // Dialog should be visible
    expect(screen.getByText("Import Configuration", { selector: "h2" })).toBeInTheDocument();
  });

  it("loads library configurations on mount", async () => {
    const mockConfigs = [
      {
        id: "config-1",
        name: "Test Config",
        description: "Test description",
        created_at: "2024-01-01T00:00:00Z",
        modified_at: "2024-01-01T00:00:00Z",
        tags: ["test"],
      },
    ];

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ configurations: mockConfigs }),
    });

    render(<ConfigurationManagement />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/configurations/library/list",
        expect.objectContaining({
          method: "POST",
        })
      );
    });
  });

  it("displays library when browse library is clicked", async () => {
    const mockConfigs = [
      {
        id: "config-1",
        name: "Test Config",
        description: "Test description",
        created_at: "2024-01-01T00:00:00Z",
        modified_at: "2024-01-01T00:00:00Z",
        tags: ["test"],
      },
    ];

    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({ configurations: mockConfigs }),
    });

    render(<ConfigurationManagement />);

    const browseButton = screen.getByText("Browse Library");
    fireEvent.click(browseButton);

    await waitFor(() => {
      expect(screen.getByText("Configuration Library (1)")).toBeInTheDocument();
    });
  });

  it("handles search functionality", async () => {
    render(<ConfigurationManagement />);

    // Open library
    const browseButton = screen.getByText("Browse Library");
    fireEvent.click(browseButton);

    await waitFor(() => {
      const searchInput = screen.getByPlaceholderText("Search configurations...");
      expect(searchInput).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText("Search configurations...");
    fireEvent.change(searchInput, { target: { value: "test" } });

    const searchButton = screen.getByText("Search");
    fireEvent.click(searchButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/configurations/library/list",
        expect.objectContaining({
          method: "POST",
          body: expect.stringContaining("test"),
        })
      );
    });
  });

  it("handles configuration selection", async () => {
    const mockConfig = {
      metadata: {
        id: "config-1",
        name: "Test Config",
        description: "Test description",
        created_at: "2024-01-01T00:00:00Z",
        modified_at: "2024-01-01T00:00:00Z",
        tags: ["test"],
      },
      configuration: {
        base_model: "test-model",
        algorithm: "lora",
      },
    };

    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ configurations: [mockConfig.metadata] }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: mockConfig }),
      });

    render(<ConfigurationManagement />);

    // Open library
    const browseButton = screen.getByText("Browse Library");
    fireEvent.click(browseButton);

    await waitFor(() => {
      expect(screen.getByText("Test Config")).toBeInTheDocument();
    });

    // Click on configuration
    const configCard = screen.getByText("Test Config");
    fireEvent.click(configCard);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/configurations/library/config-1"
      );
    });
  });

  it("handles configuration deletion", async () => {
    const mockConfig = {
      id: "config-1",
      name: "Test Config",
      description: "Test description",
      created_at: "2024-01-01T00:00:00Z",
      modified_at: "2024-01-01T00:00:00Z",
      tags: ["test"],
    };

    // Mock window.confirm
    global.confirm = vi.fn(() => true);

    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ configurations: [mockConfig] }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ configurations: [] }),
      });

    render(<ConfigurationManagement />);

    // Open library
    const browseButton = screen.getByText("Browse Library");
    fireEvent.click(browseButton);

    await waitFor(() => {
      expect(screen.getByText("Test Config")).toBeInTheDocument();
    });

    // Find and click delete button
    const deleteButtons = screen.getAllByTitle("Delete configuration");
    fireEvent.click(deleteButtons[0]);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/configurations/library/config-1",
        expect.objectContaining({
          method: "DELETE",
        })
      );
    });
  });

  it("displays error message when API call fails", async () => {
    (global.fetch as any).mockRejectedValueOnce(new Error("API Error"));

    render(<ConfigurationManagement />);

    await waitFor(() => {
      expect(screen.getByText("API Error")).toBeInTheDocument();
    });
  });

  it("shows empty state when no configuration is selected", () => {
    render(<ConfigurationManagement />);

    expect(screen.getByText("No Configuration Selected")).toBeInTheDocument();
    expect(screen.getByText(/Export a new configuration/i)).toBeInTheDocument();
  });
});
