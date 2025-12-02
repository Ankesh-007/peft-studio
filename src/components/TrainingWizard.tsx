import { ChevronLeft, ChevronRight } from "lucide-react";
import React, { useState, useRef, useEffect } from "react";

import { useKeyboardNavigation } from "../hooks/useKeyboardNavigation";
import { usePrefersReducedMotion } from "../hooks/useMediaQuery";

import { AccessibleButton } from "./AccessibleButton";
import { SkeletonWizardStep } from "./LoadingStates";
import DatasetUploadStep from "./wizard/DatasetUploadStep";
import ModelSelectionStep from "./wizard/ModelSelectionStep";
import SmartConfigurationStep from "./wizard/SmartConfigurationStep";
import UseCaseSelection from "./wizard/UseCaseSelection";

import type {
  WizardState,
  OptimizationProfile,
  Dataset,
  ModelInfo,
  TrainingEstimates,
} from "../types/wizard";

interface TrainingWizardProps {
  onComplete?: (state: WizardState) => void;
  onCancel?: () => void;
}

const STEPS = [
  {
    id: 1,
    name: "Use Case",
    component: UseCaseSelection,
    description: "Select your training use case",
  },
  {
    id: 2,
    name: "Dataset",
    component: DatasetUploadStep,
    description: "Upload and validate your training data",
  },
  {
    id: 3,
    name: "Model",
    component: ModelSelectionStep,
    description: "Choose a base model to fine-tune",
  },
  {
    id: 4,
    name: "Configuration",
    component: SmartConfigurationStep,
    description: "Review and adjust training settings",
  },
  {
    id: 5,
    name: "Review",
    component: null,
    description: "Review and launch your training",
  }, // To be implemented
];

/**
 * Training Wizard - Multi-step guided interface for configuring training runs
 * with full keyboard navigation and accessibility support
 */
const TrainingWizard: React.FC<TrainingWizardProps> = ({
  onComplete,
  onCancel,
}) => {
  const [wizardState, setWizardState] = useState<WizardState>({
    currentStep: 1,
    profile: null,
    dataset: null,
    model: null,
    config: {},
    estimates: null,
    validation: [],
  });
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const prefersReducedMotion = usePrefersReducedMotion();

  const currentStepData = STEPS.find((s) => s.id === wizardState.currentStep);
  const StepComponent = currentStepData?.component;

  const canGoNext = (): boolean => {
    switch (wizardState.currentStep) {
      case 1:
        return wizardState.profile !== null;
      case 2:
        return (
          wizardState.dataset !== null &&
          wizardState.validation.filter((v) => v.level === "error").length === 0
        );
      case 3:
        return wizardState.model !== null;
      case 4:
        return true; // Config has smart defaults
      case 5:
        return true;
      default:
        return false;
    }
  };

  // Keyboard navigation
  useKeyboardNavigation(containerRef, {
    onArrowRight: () => {
      if (canGoNext() && wizardState.currentStep < STEPS.length) {
        handleNext();
      }
    },
    onArrowLeft: () => {
      if (wizardState.currentStep > 1) {
        handlePrevious();
      }
    },
    onEscape: () => {
      if (onCancel) {
        onCancel();
      }
    },
  });

  // Announce step changes to screen readers
  useEffect(() => {
    const currentStep = STEPS.find((s) => s.id === wizardState.currentStep);
    if (currentStep) {
      const announcement = `Step ${wizardState.currentStep} of ${STEPS.length}: ${currentStep.name}. ${currentStep.description}`;
      const liveRegion = document.getElementById("wizard-live-region");
      if (liveRegion) {
        liveRegion.textContent = announcement;
      }
    }
  }, [wizardState.currentStep]);

  const handleNext = async () => {
    if (!canGoNext() || wizardState.currentStep >= STEPS.length) return;

    setIsTransitioning(true);

    // Simulate async validation/processing
    await new Promise((resolve) =>
      setTimeout(resolve, prefersReducedMotion ? 0 : 300),
    );

    setWizardState((prev) => ({
      ...prev,
      currentStep: prev.currentStep + 1,
    }));

    setIsTransitioning(false);

    // Scroll to top of step content
    containerRef.current?.scrollTo({
      top: 0,
      behavior: prefersReducedMotion ? "auto" : "smooth",
    });
  };

  const handlePrevious = async () => {
    if (wizardState.currentStep <= 1) return;

    setIsTransitioning(true);

    await new Promise((resolve) =>
      setTimeout(resolve, prefersReducedMotion ? 0 : 300),
    );

    setWizardState((prev) => ({
      ...prev,
      currentStep: prev.currentStep - 1,
    }));

    setIsTransitioning(false);

    // Scroll to top of step content
    containerRef.current?.scrollTo({
      top: 0,
      behavior: prefersReducedMotion ? "auto" : "smooth",
    });
  };

  const handleProfileSelect = (profile: OptimizationProfile) => {
    setWizardState((prev) => ({
      ...prev,
      profile,
      config: {
        ...prev.config,
        loraR: profile.config.lora_r,
        loraAlpha: profile.config.lora_alpha,
        loraDropout: profile.config.lora_dropout,
        targetModules: profile.config.target_modules,
        learningRate: profile.config.learning_rate,
        epochs: profile.config.num_epochs,
        warmupSteps: Math.floor(profile.config.warmup_ratio * 1000), // Placeholder
        scheduler: profile.config.scheduler as any,
        weightDecay: profile.config.weight_decay,
        maxGradNorm: profile.config.max_grad_norm,
      },
    }));
  };

  const handleDatasetSelect = (dataset: Dataset, validation: any[]) => {
    setWizardState((prev) => ({
      ...prev,
      dataset,
      validation,
    }));
  };

  const handleModelSelect = (model: ModelInfo) => {
    setWizardState((prev) => ({
      ...prev,
      model,
    }));
  };

  const handleConfigUpdate = (config: any, estimates: TrainingEstimates) => {
    setWizardState((prev) => ({
      ...prev,
      config: {
        ...prev.config,
        ...config,
      },
      estimates,
    }));
  };

  const handleLaunch = () => {
    if (onComplete) {
      onComplete(wizardState);
    }
  };

  return (
    <div
      ref={containerRef}
      className="flex flex-col h-full bg-gray-50"
      role="region"
      aria-label="Training wizard"
    >
      {/* Screen reader announcements */}
      <div
        id="wizard-live-region"
        className="sr-only"
        role="status"
        aria-live="polite"
        aria-atomic="true"
      />

      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <h1 className="text-2xl font-bold text-gray-900">Training Wizard</h1>
        <p className="text-sm text-gray-600 mt-1">
          Follow these steps to configure and launch your model training
        </p>
      </header>

      {/* Step Indicator */}
      <nav
        className="bg-white border-b border-gray-200 px-6 py-4"
        aria-label="Training wizard progress"
      >
        <ol className="flex items-center justify-between max-w-4xl mx-auto">
          {STEPS.map((step, index) => (
            <React.Fragment key={step.id}>
              <li className="flex items-center">
                <div
                  className={`
                    flex items-center justify-center w-10 h-10 rounded-full border-2 font-semibold
                    transition-all duration-300 ease-in-out
                    ${
                      wizardState.currentStep === step.id
                        ? "border-blue-600 bg-blue-600 text-white scale-110"
                        : wizardState.currentStep > step.id
                          ? "border-green-600 bg-green-600 text-white"
                          : "border-gray-300 bg-white text-gray-400"
                    }
                  `}
                  role="img"
                  aria-label={
                    wizardState.currentStep === step.id
                      ? `Current step: ${step.name}`
                      : wizardState.currentStep > step.id
                        ? `Completed step: ${step.name}`
                        : `Upcoming step: ${step.name}`
                  }
                >
                  {wizardState.currentStep > step.id ? "✓" : step.id}
                </div>
                <span
                  className={`ml-2 text-sm font-medium transition-colors duration-200 ${
                    wizardState.currentStep >= step.id
                      ? "text-gray-900"
                      : "text-gray-400"
                  }`}
                >
                  {step.name}
                </span>
              </li>
              {index < STEPS.length - 1 && (
                <div
                  className={`flex-1 h-0.5 mx-4 transition-all duration-500 ${
                    wizardState.currentStep > step.id
                      ? "bg-green-600"
                      : "bg-gray-300"
                  }`}
                  role="presentation"
                />
              )}
            </React.Fragment>
          ))}
        </ol>
      </nav>

      {/* Step Content */}
      <main
        className="flex-1 overflow-auto p-6"
        role="main"
        aria-label={`Step ${wizardState.currentStep}: ${currentStepData?.name}`}
      >
        <div className="max-w-5xl mx-auto">
          {isLoading || isTransitioning ? (
            <SkeletonWizardStep />
          ) : (
            <div
              className={`
                transition-all duration-300 ease-in-out
                ${isTransitioning ? "opacity-0 translate-y-4" : "opacity-100 translate-y-0"}
              `}
            >
              {StepComponent && (
                <StepComponent
                  wizardState={wizardState}
                  onProfileSelect={handleProfileSelect}
                  onDatasetSelect={handleDatasetSelect}
                  onModelSelect={handleModelSelect}
                  onConfigUpdate={handleConfigUpdate}
                />
              )}
              {!StepComponent && (
                <div className="text-center py-12">
                  <p className="text-gray-500">This step is coming soon...</p>
                </div>
              )}
            </div>
          )}
        </div>
      </main>

      {/* Navigation Footer */}
      <footer className="bg-white border-t border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between max-w-5xl mx-auto">
          <AccessibleButton
            variant="ghost"
            onClick={wizardState.currentStep === 1 ? onCancel : handlePrevious}
            disabled={isTransitioning}
            icon={<ChevronLeft className="w-4 h-4" />}
            iconPosition="left"
            ariaLabel={
              wizardState.currentStep === 1
                ? "Cancel wizard"
                : "Go to previous step"
            }
          >
            {wizardState.currentStep === 1 ? "Cancel" : "Previous"}
          </AccessibleButton>

          <div
            className="text-sm text-gray-600"
            role="status"
            aria-label={`Step ${wizardState.currentStep} of ${STEPS.length}`}
          >
            Step {wizardState.currentStep} of {STEPS.length}
          </div>

          {wizardState.currentStep < STEPS.length ? (
            <AccessibleButton
              variant="primary"
              onClick={handleNext}
              disabled={!canGoNext() || isTransitioning}
              loading={isTransitioning}
              icon={<ChevronRight className="w-4 h-4" />}
              iconPosition="right"
              ariaLabel="Go to next step"
            >
              Next
            </AccessibleButton>
          ) : (
            <AccessibleButton
              variant="primary"
              onClick={handleLaunch}
              disabled={!canGoNext() || isTransitioning}
              loading={isTransitioning}
              ariaLabel="Launch training"
              className="bg-green-600 hover:bg-green-700 focus:ring-green-600"
            >
              Launch Training
            </AccessibleButton>
          )}
        </div>
      </footer>
    </div>
  );
};

export default TrainingWizard;
