/**
 * E2E Test: Navigation and View Switching
 *
 * Tests user navigation between different views:
 * - Dashboard
 * - Training
 * - Deployments
 * - Gradio Demos
 * - Inference
 * - Configurations
 * - Logging
 *
 * Requirements: 3.3
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "../../App";

describe("E2E: Navigation and View Switching", () => {
  beforeEach(() => {
    sessionStorage.clear();
    localStorage.clear();
    sessionStorage.setItem("backendAvailable", "true");

    // Skip onboarding for tests
    localStorage.setItem(
      "peft-studio-onboarding",
      JSON.stringify({
        hasCompletedWelcome: true,
        hasCompletedSetup: true,
        hasCompletedTour: true,
        isFirstVisit: false,
      })
    );

    if (!window.electron) {
      (window as any).electron = {
        invoke: vi.fn(),
        on: vi.fn(),
        removeListener: vi.fn(),
      };
    }
  });

  const waitForAppReady = async () => {
    await waitFor(
      () => {
        const dashboardButton = screen.queryByRole("button", { name: /dashboard/i });
        expect(dashboardButton).toBeInTheDocument();
      },
      { timeout: 5000 }
    );
  };

  it("should start on dashboard view by default", async () => {
    render(<App />);
    await waitForAppReady();

    // Dashboard button should be active (has blue background)
    const dashboardButton = screen.getByRole("button", { name: /dashboard/i });
    expect(dashboardButton).toHaveClass("bg-blue-500");
  });

  it("should navigate to training view when training button is clicked", async () => {
    const user = userEvent.setup();
    render(<App />);
    await waitForAppReady();

    // Click training button
    const trainingButton = screen.getByRole("button", { name: /training/i });
    await user.click(trainingButton);

    // Training button should now be active
    expect(trainingButton).toHaveClass("bg-blue-500");

    // Dashboard button should no longer be active
    const dashboardButton = screen.getByRole("button", { name: /dashboard/i });
    expect(dashboardButton).not.toHaveClass("bg-blue-500");
  });

  it("should navigate to deployment view", async () => {
    const user = userEvent.setup();
    render(<App />);
    await waitForAppReady();

    const deploymentButton = screen.getByRole("button", { name: /deployments/i });
    await user.click(deploymentButton);

    expect(deploymentButton).toHaveClass("bg-blue-500");
  });

  it("should navigate to gradio demos view", async () => {
    const user = userEvent.setup();
    render(<App />);
    await waitForAppReady();

    const gradioButton = screen.getByRole("button", { name: /gradio demos/i });
    await user.click(gradioButton);

    expect(gradioButton).toHaveClass("bg-blue-500");
  });

  it("should navigate to inference view", async () => {
    const user = userEvent.setup();
    render(<App />);
    await waitForAppReady();

    const inferenceButton = screen.getByRole("button", { name: /inference/i });
    await user.click(inferenceButton);

    expect(inferenceButton).toHaveClass("bg-blue-500");
  });

  it("should navigate to configurations view", async () => {
    const user = userEvent.setup();
    render(<App />);
    await waitForAppReady();

    const configButton = screen.getByRole("button", { name: /configurations/i });
    await user.click(configButton);

    expect(configButton).toHaveClass("bg-blue-500");
  });

  it("should navigate to logging view", async () => {
    const user = userEvent.setup();
    render(<App />);
    await waitForAppReady();

    const loggingButton = screen.getByRole("button", { name: /logging/i });
    await user.click(loggingButton);

    expect(loggingButton).toHaveClass("bg-blue-500");
  });

  it("should switch between multiple views correctly", async () => {
    const user = userEvent.setup();
    render(<App />);
    await waitForAppReady();

    // Navigate to training
    const trainingButton = screen.getByRole("button", { name: /training/i });
    await user.click(trainingButton);
    expect(trainingButton).toHaveClass("bg-blue-500");

    // Navigate to inference
    const inferenceButton = screen.getByRole("button", { name: /inference/i });
    await user.click(inferenceButton);
    expect(inferenceButton).toHaveClass("bg-blue-500");
    expect(trainingButton).not.toHaveClass("bg-blue-500");

    // Navigate back to dashboard
    const dashboardButton = screen.getByRole("button", { name: /dashboard/i });
    await user.click(dashboardButton);
    expect(dashboardButton).toHaveClass("bg-blue-500");
    expect(inferenceButton).not.toHaveClass("bg-blue-500");
  });

  it("should maintain only one active view at a time", async () => {
    const user = userEvent.setup();
    render(<App />);
    await waitForAppReady();

    // Click through all views
    const views = [
      "training",
      "deployments",
      "gradio demos",
      "inference",
      "configurations",
      "logging",
      "dashboard",
    ];

    for (const viewName of views) {
      const button = screen.getByRole("button", { name: new RegExp(viewName, "i") });
      await user.click(button);

      // Count active buttons (should be exactly 1)
      const allButtons = screen
        .getAllByRole("button")
        .filter((btn) =>
          btn.textContent?.match(
            /dashboard|training|deployments|gradio demos|inference|configurations|logging/i
          )
        );

      const activeButtons = allButtons.filter((btn) => btn.className.includes("bg-blue-500"));

      expect(activeButtons).toHaveLength(1);
      expect(activeButtons[0]).toBe(button);
    }
  });
});
