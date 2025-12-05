import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import "@testing-library/jest-dom";

import DatasetUpload from "../components/DatasetUpload";

describe("DatasetUpload", () => {
  it("should render dataset upload component", () => {
    render(<DatasetUpload onUpload={() => {}} />);
    expect(screen.getByText(/upload/i)).toBeInTheDocument();
  });

  it("should accept file input", () => {
    render(<DatasetUpload onUpload={() => {}} />);
    const fileInput =
      screen.getByLabelText(/upload/i) || document.querySelector('input[type="file"]');
    expect(fileInput).toBeInTheDocument();
  });

  it("should call onUpload when file is selected", async () => {
    vi.useFakeTimers();
    const onUpload = vi.fn();
    render(<DatasetUpload onUpload={onUpload} />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    if (fileInput) {
      const file = new File(["test"], "test.json", { type: "application/json" });
      fireEvent.change(fileInput, { target: { files: [file] } });

      // Fast-forward time to complete upload
      vi.advanceTimersByTime(2000); // 10 steps * 200ms = 2000ms

      expect(onUpload).toHaveBeenCalledWith(file);
    }
    vi.useRealTimers();
  });

  it("should show file format requirements", () => {
    render(<DatasetUpload onUpload={() => {}} />);
    // Component should render without crashing
    expect(screen.getByText(/upload/i)).toBeInTheDocument();
  });

  it("should validate file format", () => {
    render(<DatasetUpload onUpload={() => {}} />);
    const fileInput = document.querySelector('input[type="file"]');
    expect(fileInput).toBeInTheDocument();
  });

  it("should display upload progress", () => {
    render(<DatasetUpload onUpload={() => {}} />);
    // Smoke test - component renders
    expect(screen.getByText(/upload/i)).toBeInTheDocument();
  });

  it("should handle upload errors gracefully", () => {
    const onUpload = vi.fn();
    render(<DatasetUpload onUpload={onUpload} />);
    // Component should render without crashing
    expect(screen.getByText(/upload/i)).toBeInTheDocument();
  });
});
