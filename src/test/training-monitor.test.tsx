import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import "@testing-library/jest-dom";

import TrainingMonitor from "../components/TrainingMonitor";

describe("TrainingMonitor", () => {
  it("should render training monitor component", () => {
    render(<TrainingMonitor runId="test-run-1" runName="Test Training Run" />);
    expect(screen.getByText("Test Training Run")).toBeInTheDocument();
  });

  it("should display training metrics when available", () => {
    render(<TrainingMonitor runId="test-run-1" runName="Test Training Run" />);
    // Check for common training metrics sections
    expect(screen.getByText("Current Loss")).toBeInTheDocument();
    expect(screen.getByText("Learning Rate")).toBeInTheDocument();
  });

  it("should show status indicator", () => {
    render(<TrainingMonitor runId="test-run-1" runName="Test Training Run" />);
    // Training monitor should show status
    expect(screen.getByText("running")).toBeInTheDocument();
  });

  it("should render control buttons", () => {
    render(<TrainingMonitor runId="test-run-1" runName="Test Training Run" />);
    // Verify control buttons are present
    expect(screen.getByText("Pause")).toBeInTheDocument();
    expect(screen.getByText("Stop & Save")).toBeInTheDocument();
    expect(screen.getByText("Snapshot")).toBeInTheDocument();
  });

  it("should display progress percentage", () => {
    render(<TrainingMonitor runId="test-run-1" runName="Test Training Run" />);
    // Smoke test - verify component renders with progress
    expect(screen.getByText("Complete")).toBeInTheDocument();
  });
});
