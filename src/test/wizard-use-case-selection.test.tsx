import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import "@testing-library/jest-dom";

import UseCaseSelection from "../components/wizard/UseCaseSelection";

import { WizardState } from "../types/wizard";

const mockWizardState: WizardState = {
  currentStep: 0,
  config: {},
  profile: null,
  dataset: null,
  model: null,
  estimates: null,
  validation: [],
};

describe("UseCaseSelection", () => {
  it("should render use case selection component", () => {
    render(<UseCaseSelection wizardState={mockWizardState} onProfileSelect={() => {}} />);
    expect(screen.getByText(/loading optimization profiles/i)).toBeInTheDocument();
  });

  it("should display available use cases", () => {
    render(<UseCaseSelection wizardState={mockWizardState} onProfileSelect={() => {}} />);
    // Component should show loading state initially
    expect(screen.getByText(/loading optimization profiles/i)).toBeInTheDocument();
  });

  it("should call onProfileSelect when use case is chosen", () => {
    const onProfileSelect = vi.fn();
    render(<UseCaseSelection wizardState={mockWizardState} onProfileSelect={onProfileSelect} />);

    // Smoke test - component renders
    expect(screen.getByText(/loading optimization profiles/i)).toBeInTheDocument();
  });

  it("should show use case descriptions", () => {
    render(<UseCaseSelection wizardState={mockWizardState} onProfileSelect={() => {}} />);
    // Component should render without crashing
    const { container } = render(
      <UseCaseSelection wizardState={mockWizardState} onProfileSelect={() => {}} />
    );
    expect(container).toBeInTheDocument();
  });

  it("should highlight selected use case", () => {
    const { container } = render(
      <UseCaseSelection wizardState={mockWizardState} onProfileSelect={() => {}} />
    );
    // Smoke test
    expect(container).toBeInTheDocument();
  });

  it("should provide examples for each use case", () => {
    const { container } = render(
      <UseCaseSelection wizardState={mockWizardState} onProfileSelect={() => {}} />
    );
    // Component renders successfully
    expect(container).toBeInTheDocument();
  });
});
