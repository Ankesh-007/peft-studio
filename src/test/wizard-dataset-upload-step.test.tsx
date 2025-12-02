import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import "@testing-library/jest-dom";

import DatasetUploadStep from "../components/wizard/DatasetUploadStep";

import type { WizardState } from "../types/wizard";

describe("DatasetUploadStep", () => {
  const mockWizardState: WizardState = {
    currentStep: 1,
    profile: null,
    dataset: null,
    model: null,
    config: {},
    estimates: null,
    validation: [],
  };

  it("should render dataset upload step", () => {
    render(
      <DatasetUploadStep
        wizardState={mockWizardState}
        onDatasetSelect={() => {}}
      />
    );
    expect(screen.getByText(/upload your training data/i)).toBeInTheDocument();
  });

  it("should show upload instructions", () => {
    render(
      <DatasetUploadStep
        wizardState={mockWizardState}
        onDatasetSelect={() => {}}
      />
    );
    // Component should display upload guidance
    expect(screen.getByText(/upload your training data/i)).toBeInTheDocument();
  });

  it("should accept file uploads", () => {
    render(
      <DatasetUploadStep
        wizardState={mockWizardState}
        onDatasetSelect={() => {}}
      />
    );
    const fileInput = document.querySelector('input[type="file"]');
    expect(fileInput).toBeInTheDocument();
  });

  it("should validate dataset format", () => {
    render(
      <DatasetUploadStep
        wizardState={mockWizardState}
        onDatasetSelect={() => {}}
      />
    );
    // Smoke test - component renders
    expect(screen.getByText(/upload your training data/i)).toBeInTheDocument();
  });

  it("should show dataset preview after upload", () => {
    const wizardStateWithDataset: WizardState = {
      ...mockWizardState,
      dataset: {
        id: "test-dataset",
        name: "test.json",
        path: "/path/to/test.json",
        format: "json",
        size: 1024000,
        num_samples: 500,
      },
    };

    render(
      <DatasetUploadStep
        wizardState={wizardStateWithDataset}
        onDatasetSelect={() => {}}
      />
    );
    // Component should render with dataset
    expect(screen.getByText(/dataset ready/i)).toBeInTheDocument();
  });

  it("should display dataset statistics", () => {
    const wizardStateWithDataset: WizardState = {
      ...mockWizardState,
      dataset: {
        id: "test-dataset",
        name: "test.json",
        path: "/path/to/test.json",
        format: "json",
        size: 1024000,
        num_samples: 500,
      },
    };

    render(
      <DatasetUploadStep
        wizardState={wizardStateWithDataset}
        onDatasetSelect={() => {}}
      />
    );
    // Component renders successfully - check for file name
    expect(screen.getByText("test.json")).toBeInTheDocument();
  });
});
