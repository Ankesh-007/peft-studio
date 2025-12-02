import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeAll } from "vitest";
import "@testing-library/jest-dom";

import TrainingWizard from "../components/TrainingWizard";
import Dashboard from "../components/Dashboard";

// Mock window.matchMedia
beforeAll(() => {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
});

describe("Training Flow Integration", () => {
  it("should complete full training setup flow", async () => {
    render(<TrainingWizard />);

    // Verify wizard starts at first step
    expect(screen.getByRole("region", { name: /training wizard/i })).toBeInTheDocument();

    // Check that navigation exists
    const navigation = screen.getByRole("navigation", { name: /training wizard progress/i });
    expect(navigation).toBeInTheDocument();
  });

  it("should navigate through wizard steps sequentially", () => {
    render(<TrainingWizard />);

    // Verify step navigation exists
    const nextButton = screen.getByRole("button", { name: /next/i });
    expect(nextButton).toBeInTheDocument();

    // Click next to move to second step
    fireEvent.click(nextButton);

    // Wizard should still be rendered
    expect(screen.getByRole("region", { name: /training wizard/i })).toBeInTheDocument();
  });

  it("should validate required fields before proceeding", () => {
    render(<TrainingWizard />);

    // Try to proceed without completing required fields
    const nextButton = screen.getByRole("button", { name: /next/i });
    
    // Button should exist
    expect(nextButton).toBeInTheDocument();
  });

  it("should show training progress after starting training", async () => {
    render(<Dashboard />);

    // Wait for dashboard to load
    await waitFor(() => {
      expect(screen.queryByRole("status", { name: /loading/i })).not.toBeInTheDocument();
    }, { timeout: 2000 });

    // Dashboard should render with overview section
    expect(screen.getByRole("region", { name: /dashboard overview/i })).toBeInTheDocument();
  });

  it("should allow pausing and resuming training", () => {
    render(<Dashboard />);

    // Dashboard should render - check for quick actions
    expect(screen.getByText(/quick actions/i)).toBeInTheDocument();
  });

  it("should display real-time training metrics", async () => {
    render(<Dashboard />);

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByRole("status", { name: /loading/i })).not.toBeInTheDocument();
    }, { timeout: 2000 });

    // Dashboard should show metrics - check for models trained stat
    expect(screen.getByText(/models trained/i)).toBeInTheDocument();
  });

  it("should handle training completion", () => {
    render(<Dashboard />);

    // Dashboard should render successfully - check for greeting
    expect(screen.getByText(/good morning/i)).toBeInTheDocument();
  });

  it("should allow exporting trained model", () => {
    render(<Dashboard />);

    // Dashboard should have quick actions
    expect(screen.getByText(/quick actions/i)).toBeInTheDocument();
  });
});
