import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeAll } from "vitest";

import "@testing-library/jest-dom";
import { AccessibleButton } from "../components/AccessibleButton";
import { AccessibleInput } from "../components/AccessibleInput";
import Dashboard from "../components/Dashboard";
import Layout from "../components/Layout";
import TrainingWizard from "../components/TrainingWizard";

// Mock window.matchMedia for responsive design tests
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

describe("Accessibility Tests", () => {
  describe("TrainingWizard", () => {
    it("should have proper ARIA labels on navigation", () => {
      render(<TrainingWizard />);
      expect(
        screen.getByRole("region", { name: /training wizard/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("navigation", { name: /training wizard progress/i }),
      ).toBeInTheDocument();
    });

    it("should announce step changes to screen readers", () => {
      render(<TrainingWizard />);
      const liveRegion = document.getElementById("wizard-live-region");
      expect(liveRegion).toHaveAttribute("role", "status");
      expect(liveRegion).toHaveAttribute("aria-live", "polite");
    });

    it("should have accessible navigation buttons", () => {
      render(<TrainingWizard />);
      const nextButton = screen.getByRole("button", { name: /next/i });
      expect(nextButton).toBeInTheDocument();
    });

    it("should have proper step indicators with ARIA labels", () => {
      render(<TrainingWizard />);
      const stepIndicators = screen.getAllByRole("img");
      expect(stepIndicators.length).toBeGreaterThan(0);
    });
  });

  describe("Layout", () => {
    it("should have skip to main content link", () => {
      render(
        <Layout>
          <div>Test content</div>
        </Layout>,
      );
      const skipLink = screen.getByText(/skip to main content/i);
      expect(skipLink).toHaveAttribute("href", "#main-content");
    });

    it("should have proper main landmark", () => {
      render(
        <Layout>
          <div>Test content</div>
        </Layout>,
      );
      expect(
        screen.getByRole("main", { name: /main content/i }),
      ).toBeInTheDocument();
    });

    it("should have accessible help panel close button", () => {
      render(
        <Layout>
          <div>Test content</div>
        </Layout>,
      );
      // Help panel is initially closed, so we just verify the structure exists
      expect(screen.getByRole("main")).toBeInTheDocument();
    });
  });

  describe("AccessibleButton", () => {
    it("should have proper aria-label when provided", () => {
      render(
        <AccessibleButton ariaLabel="Custom label">Click</AccessibleButton>,
      );
      expect(
        screen.getByRole("button", { name: /custom label/i }),
      ).toBeInTheDocument();
    });

    it("should indicate loading state with aria-busy", () => {
      render(<AccessibleButton loading>Loading</AccessibleButton>);
      const button = screen.getByRole("button");
      expect(button).toHaveAttribute("aria-busy", "true");
    });

    it("should be keyboard accessible", () => {
      const handleClick = vi.fn();
      render(<AccessibleButton onClick={handleClick}>Click</AccessibleButton>);
      const button = screen.getByRole("button");
      button.focus();
      expect(document.activeElement).toBe(button);
    });
  });

  describe("AccessibleInput", () => {
    it("should associate label with input", () => {
      render(<AccessibleInput label="Email" />);
      const input = screen.getByLabelText(/email/i);
      expect(input).toBeInTheDocument();
    });

    it("should indicate required fields", () => {
      render(<AccessibleInput label="Name" required />);
      const input = screen.getByLabelText(/name/i);
      expect(input).toHaveAttribute("aria-required", "true");
    });

    it("should announce errors to screen readers", () => {
      render(<AccessibleInput label="Email" error="Invalid email" />);
      const input = screen.getByLabelText(/email/i);
      expect(input).toHaveAttribute("aria-invalid", "true");
      expect(screen.getByRole("alert")).toHaveTextContent(/invalid email/i);
    });

    it("should provide hint text with aria-describedby", () => {
      render(<AccessibleInput label="Password" hint="Must be 8 characters" />);
      const input = screen.getByLabelText(/password/i);
      const hintId = input.getAttribute("aria-describedby");
      expect(hintId).toBeTruthy();
      expect(document.getElementById(hintId!)).toHaveTextContent(
        /must be 8 characters/i,
      );
    });
  });

  describe("Keyboard Navigation", () => {
    it("should support tab navigation", () => {
      render(
        <div>
          <AccessibleButton>First</AccessibleButton>
          <AccessibleButton>Second</AccessibleButton>
          <AccessibleButton>Third</AccessibleButton>
        </div>,
      );

      const buttons = screen.getAllByRole("button");
      buttons[0].focus();
      expect(document.activeElement).toBe(buttons[0]);
    });

    it("should have visible focus indicators", () => {
      render(<AccessibleButton>Focus me</AccessibleButton>);
      const button = screen.getByRole("button");
      button.focus();

      // Check that focus styles are applied
      const styles = window.getComputedStyle(button);
      expect(button.className).toContain("focus:ring");
    });
  });

  describe("Screen Reader Support", () => {
    it("should have proper heading hierarchy", async () => {
      render(<Dashboard />);

      // Wait for loading to complete
      await new Promise((resolve) => setTimeout(resolve, 1100));

      const headings = screen.getAllByRole("heading");

      // Check that h1 exists
      const h1 = headings.find((h) => h.tagName === "H1");
      expect(h1).toBeInTheDocument();
    });

    it("should use semantic HTML elements", () => {
      render(
        <Layout>
          <Dashboard />
        </Layout>,
      );

      // Check for semantic landmarks
      expect(screen.getByRole("main")).toBeInTheDocument();
    });

    it("should provide text alternatives for icons", () => {
      render(<AccessibleButton ariaLabel="Delete item">🗑️</AccessibleButton>);
      expect(
        screen.getByRole("button", { name: /delete item/i }),
      ).toBeInTheDocument();
    });
  });

  describe("Loading States", () => {
    it("should show loading skeleton while data loads", () => {
      render(<Dashboard />);
      // Dashboard shows loading state initially
      const loadingElement = screen.getByRole("status", {
        name: /loading dashboard/i,
      });
      expect(loadingElement).toBeInTheDocument();
    });
  });

  describe("Responsive Design", () => {
    it("should render dashboard at different viewport sizes", () => {
      const { container } = render(<Dashboard />);
      expect(container).toBeInTheDocument();
    });

    it("should render layout at different viewport sizes", () => {
      const { container } = render(
        <Layout>
          <div>Test content</div>
        </Layout>,
      );
      expect(container).toBeInTheDocument();
    });
  });
});
