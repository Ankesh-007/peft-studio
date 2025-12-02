/**
 * Unit tests for PausedRunDisplay component
 */

import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import PausedRunDisplay from "../components/PausedRunDisplay";

describe("PausedRunDisplay", () => {
  const mockPausedRun = {
    job_id: "test_job_123",
    state: "paused",
    paused_at: "2025-11-29T10:30:00Z",
    started_at: "2025-11-29T09:00:00Z",
    elapsed_time: 5400, // 1.5 hours in seconds
    remaining_time_estimate: 3600, // 1 hour in seconds
    current_step: 500,
    current_epoch: 2,
    current_loss: 0.4532,
    resource_usage: {
      gpu_utilization: [98.5, 45.2],
      gpu_memory_used: [78400000000, 32100000000], // bytes
      cpu_utilization: 62.3,
      ram_used: 45000000000, // bytes
    },
    model_name: "Llama-3-8B",
    dataset_name: "Finance-10k",
  };

  const mockOnResume = vi.fn();
  const mockOnStop = vi.fn();

  it("renders paused run information", () => {
    render(
      <PausedRunDisplay
        pausedRun={mockPausedRun}
        onResume={mockOnResume}
        onStop={mockOnStop}
      />,
    );

    // Check for job ID
    expect(screen.getByText(/test_job_123/i)).toBeInTheDocument();

    // Check for paused status (may appear multiple times in different contexts)
    const pausedElements = screen.getAllByText(/PAUSED/i);
    expect(pausedElements.length).toBeGreaterThan(0);

    // Check for training progress
    expect(screen.getByText(/500/)).toBeInTheDocument(); // current step
    // Note: "2" appears in multiple places (epoch and timestamps), so we check it exists
    const twoElements = screen.getAllByText(/^2$/);
    expect(twoElements.length).toBeGreaterThan(0); // current epoch
    expect(screen.getByText(/0.4532/)).toBeInTheDocument(); // current loss
  });

  it("displays elapsed time", () => {
    render(
      <PausedRunDisplay
        pausedRun={mockPausedRun}
        onResume={mockOnResume}
        onStop={mockOnStop}
      />,
    );

    // Should display elapsed time (1.5 hours = 1h 30m)
    expect(screen.getByText(/Elapsed Time/i)).toBeInTheDocument();
  });

  it("displays remaining time estimate", () => {
    render(
      <PausedRunDisplay
        pausedRun={mockPausedRun}
        onResume={mockOnResume}
        onStop={mockOnStop}
      />,
    );

    // Should display remaining time
    expect(screen.getByText(/Remaining Time/i)).toBeInTheDocument();
  });

  it("displays resource usage at pause time", () => {
    render(
      <PausedRunDisplay
        pausedRun={mockPausedRun}
        onResume={mockOnResume}
        onStop={mockOnStop}
      />,
    );

    // Check for resource usage section
    expect(
      screen.getByText(/Resource Usage at Pause Time/i),
    ).toBeInTheDocument();

    // Check for GPU utilization
    expect(screen.getByText(/GPU Utilization/i)).toBeInTheDocument();

    // Check for GPU memory
    expect(screen.getByText(/GPU Memory/i)).toBeInTheDocument();

    // Check for CPU utilization
    expect(screen.getByText(/CPU Utilization/i)).toBeInTheDocument();

    // Check for RAM usage
    expect(screen.getByText(/RAM Usage/i)).toBeInTheDocument();
  });

  it("calls onResume when resume button is clicked", () => {
    render(
      <PausedRunDisplay
        pausedRun={mockPausedRun}
        onResume={mockOnResume}
        onStop={mockOnStop}
      />,
    );

    const resumeButton = screen.getByRole("button", {
      name: /Resume Training/i,
    });
    fireEvent.click(resumeButton);

    expect(mockOnResume).toHaveBeenCalledWith("test_job_123");
  });

  it("calls onStop when stop button is clicked", () => {
    render(
      <PausedRunDisplay
        pausedRun={mockPausedRun}
        onResume={mockOnResume}
        onStop={mockOnStop}
      />,
    );

    const stopButton = screen.getByRole("button", { name: /Stop & Save/i });
    fireEvent.click(stopButton);

    expect(mockOnStop).toHaveBeenCalledWith("test_job_123");
  });

  it("displays model and dataset names when provided", () => {
    render(
      <PausedRunDisplay
        pausedRun={mockPausedRun}
        onResume={mockOnResume}
        onStop={mockOnStop}
      />,
    );

    expect(screen.getByText(/Llama-3-8B/i)).toBeInTheDocument();
    expect(screen.getByText(/Finance-10k/i)).toBeInTheDocument();
  });

  it("handles multiple GPUs correctly", () => {
    render(
      <PausedRunDisplay
        pausedRun={mockPausedRun}
        onResume={mockOnResume}
        onStop={mockOnStop}
      />,
    );

    // Should show GPU 0 and GPU 1 (may appear multiple times in the UI)
    const gpu0Elements = screen.getAllByText(/GPU 0/i);
    const gpu1Elements = screen.getAllByText(/GPU 1/i);
    expect(gpu0Elements.length).toBeGreaterThan(0);
    expect(gpu1Elements.length).toBeGreaterThan(0);

    // Should show utilization percentages
    expect(screen.getByText(/98.5%/)).toBeInTheDocument();
    expect(screen.getByText(/45.2%/)).toBeInTheDocument();
  });

  it("renders without stop button when onStop is not provided", () => {
    render(
      <PausedRunDisplay pausedRun={mockPausedRun} onResume={mockOnResume} />,
    );

    const resumeButton = screen.getByRole("button", {
      name: /Resume Training/i,
    });
    expect(resumeButton).toBeInTheDocument();

    const stopButton = screen.queryByRole("button", { name: /Stop & Save/i });
    expect(stopButton).not.toBeInTheDocument();
  });

  it("displays paused timestamp", () => {
    render(
      <PausedRunDisplay
        pausedRun={mockPausedRun}
        onResume={mockOnResume}
        onStop={mockOnStop}
      />,
    );

    expect(screen.getByText(/Paused At/i)).toBeInTheDocument();
  });

  it("displays info banner about paused state", () => {
    render(
      <PausedRunDisplay
        pausedRun={mockPausedRun}
        onResume={mockOnResume}
        onStop={mockOnStop}
      />,
    );

    expect(screen.getByText(/Training Paused/i)).toBeInTheDocument();
    expect(screen.getByText(/can be resumed at any time/i)).toBeInTheDocument();
  });
});
