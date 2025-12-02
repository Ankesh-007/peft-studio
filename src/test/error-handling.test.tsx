import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import "@testing-library/jest-dom";

import ErrorBoundary from "../components/ErrorBoundary";
import ErrorDisplay from "../components/ErrorDisplay";
import ErrorToast from "../components/ErrorToast";

describe("Error Handling Components", () => {
  describe("ErrorBoundary", () => {
    it("should render children when no error occurs", () => {
      render(
        <ErrorBoundary>
          <div>Test content</div>
        </ErrorBoundary>
      );
      expect(screen.getByText("Test content")).toBeInTheDocument();
    });

    it("should catch and display errors from children", () => {
      const ThrowError = () => {
        throw new Error("Test error");
      };

      // Suppress console.error for this test
      const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
      consoleSpy.mockRestore();
    });
  });

  describe("ErrorDisplay", () => {
    it("should render error message", () => {
      render(<ErrorDisplay message="Test error message" />);
      expect(screen.getByText("Test error message")).toBeInTheDocument();
    });

    it("should render with error title", () => {
      render(
        <ErrorDisplay message="Test error" title="Error Occurred" />
      );
      expect(screen.getByText("Error Occurred")).toBeInTheDocument();
      expect(screen.getByText("Test error")).toBeInTheDocument();
    });

    it("should call onRetry when retry button is clicked", () => {
      const onRetry = vi.fn();
      render(<ErrorDisplay message="Test error" onRetry={onRetry} />);
      
      const retryButton = screen.getByRole("button", { name: /retry/i });
      retryButton.click();
      
      expect(onRetry).toHaveBeenCalledTimes(1);
    });
  });

  describe("ErrorToast", () => {
    it("should render error toast with message", () => {
      render(<ErrorToast message="Toast error message" />);
      expect(screen.getByText("Toast error message")).toBeInTheDocument();
    });

    it("should call onClose when close button is clicked", () => {
      const onClose = vi.fn();
      render(<ErrorToast message="Test error" onClose={onClose} />);
      
      const closeButton = screen.getByRole("button", { name: /close/i });
      closeButton.click();
      
      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it("should render with different severity levels", () => {
      const { rerender } = render(
        <ErrorToast message="Error" severity="error" />
      );
      expect(screen.getByText("Error")).toBeInTheDocument();

      rerender(<ErrorToast message="Warning" severity="warning" />);
      expect(screen.getByText("Warning")).toBeInTheDocument();

      rerender(<ErrorToast message="Info" severity="info" />);
      expect(screen.getByText("Info")).toBeInTheDocument();
    });
  });
});
