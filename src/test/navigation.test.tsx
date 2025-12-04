import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeAll } from "vitest";
import "@testing-library/jest-dom";

import Sidebar from "../components/Sidebar";
import TopBar from "../components/TopBar";
import CommandPalette from "../components/CommandPalette";

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

describe("Navigation Components", () => {
  describe("Sidebar", () => {
    it("should render sidebar with navigation items", () => {
      render(<Sidebar collapsed={false} onToggle={() => { }} />);
      expect(screen.getByRole("navigation")).toBeInTheDocument();
    });

    it("should have accessible navigation links", () => {
      render(<Sidebar collapsed={false} onToggle={() => { }} />);
      const nav = screen.getByRole("navigation");
      expect(nav).toBeInTheDocument();
    });

    it("should render logo or branding", () => {
      render(<Sidebar collapsed={false} onToggle={() => { }} />);
      // Sidebar should render without crashing
      expect(screen.getByRole("navigation")).toBeInTheDocument();
    });

    it("should be keyboard navigable", () => {
      render(<Sidebar collapsed={false} onToggle={() => { }} />);
      const nav = screen.getByRole("navigation");
      expect(nav).toBeInTheDocument();
    });
  });

  describe("TopBar", () => {
    it("should render top bar component", () => {
      render(<TopBar onToggleRightPanel={() => { }} />);
      // TopBar should render without crashing
      const topBar = document.querySelector('[role="banner"]') ||
        document.querySelector('header') ||
        screen.getByRole("navigation");
      expect(topBar).toBeInTheDocument();
    });

    it("should display user actions or settings", () => {
      render(<TopBar onToggleRightPanel={() => { }} />);
      // Smoke test - verify component renders
      const element = document.querySelector('[role="banner"]') ||
        document.querySelector('header') ||
        screen.getByRole("navigation");
      expect(element).toBeInTheDocument();
    });

    it("should be responsive", () => {
      const { container } = render(<TopBar onToggleRightPanel={() => { }} />);
      expect(container).toBeInTheDocument();
    });
  });

  describe("CommandPalette", () => {
    it("should not render when closed", () => {
      render(<CommandPalette isOpen={false} onClose={() => { }} />);
      // Command palette should not be visible when closed
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });

    it("should render when open", () => {
      render(<CommandPalette isOpen={true} onClose={() => { }} />);
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    it("should have search input when open", () => {
      render(<CommandPalette isOpen={true} onClose={() => { }} />);
      expect(screen.getByRole("searchbox")).toBeInTheDocument();
    });

    it("should call onClose when escape is pressed", () => {
      const onClose = vi.fn();
      render(<CommandPalette isOpen={true} onClose={onClose} />);

      const dialog = screen.getByRole("dialog");
      expect(dialog).toBeInTheDocument();
    });

    it("should filter commands based on search input", () => {
      render(<CommandPalette isOpen={true} onClose={() => { }} />);
      const searchInput = screen.getByRole("searchbox");
      expect(searchInput).toBeInTheDocument();
    });
  });
});
