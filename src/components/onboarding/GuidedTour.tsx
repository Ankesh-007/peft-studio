import { X, ArrowRight, ArrowLeft, Check } from "lucide-react";
import React, { useState, useEffect } from "react";

interface TourStep {
  target: string;
  title: string;
  description: string;
  position: "top" | "bottom" | "left" | "right";
}

interface GuidedTourProps {
  isActive: boolean;
  onComplete: () => void;
  onSkip: () => void;
}

const GuidedTour: React.FC<GuidedTourProps> = ({ isActive, onComplete, onSkip }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [tooltipPosition, setTooltipPosition] = useState({ top: 0, left: 0 });

  const tourSteps: TourStep[] = React.useMemo(
    () => [
      {
        target: '[data-tour="dashboard"]',
        title: "Dashboard Overview",
        description:
          "This is your main dashboard where you can see all your training runs, models, and system resources at a glance.",
        position: "bottom",
      },
      {
        target: '[data-tour="start-training"]',
        title: "Start Training",
        description:
          "Click here to launch the Training Wizard. It will guide you through the entire process of fine-tuning a model.",
        position: "left",
      },
      {
        target: '[data-tour="quick-actions"]',
        title: "Quick Actions",
        description:
          "Access common tasks quickly: upload datasets, start training, test models, or browse the model library.",
        position: "left",
      },
      {
        target: '[data-tour="training-runs"]',
        title: "Training Runs",
        description:
          "Monitor all your training runs here. See progress, status, and quickly access running or completed trainings.",
        position: "top",
      },
      {
        target: '[data-tour="system-resources"]',
        title: "System Resources",
        description:
          "Keep an eye on your GPU, CPU, and RAM usage. PEFT Studio automatically optimizes based on available resources.",
        position: "top",
      },
    ],
    []
  );

  useEffect(() => {
    if (!isActive) return;

    const updateTooltipPosition = () => {
      const step = tourSteps[currentStep];
      const targetElement = document.querySelector(step.target);

      if (targetElement) {
        const rect = targetElement.getBoundingClientRect();
        let top = 0;
        let left = 0;

        switch (step.position) {
          case "bottom":
            top = rect.bottom + 16;
            left = rect.left + rect.width / 2;
            break;
          case "top":
            top = rect.top - 16;
            left = rect.left + rect.width / 2;
            break;
          case "left":
            top = rect.top + rect.height / 2;
            left = rect.left - 16;
            break;
          case "right":
            top = rect.top + rect.height / 2;
            left = rect.right + 16;
            break;
        }

        setTooltipPosition({ top, left });

        // Highlight the target element
        targetElement.classList.add("tour-highlight");
      }
    };

    updateTooltipPosition();
    window.addEventListener("resize", updateTooltipPosition);

    return () => {
      window.removeEventListener("resize", updateTooltipPosition);
      // Remove highlight from all elements
      document.querySelectorAll(".tour-highlight").forEach((el) => {
        el.classList.remove("tour-highlight");
      });
    };
  }, [currentStep, isActive, tourSteps]);

  if (!isActive) return null;

  const currentStepData = tourSteps[currentStep];
  const isLastStep = currentStep === tourSteps.length - 1;

  const handleNext = () => {
    if (isLastStep) {
      onComplete();
    } else {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  return (
    <>
      {/* Overlay */}
      <div className="fixed inset-0 bg-black/60 z-40 animate-fade-in" />

      {/* Tooltip */}
      <div
        className="fixed z-50 animate-fade-in"
        style={{
          top: `${tooltipPosition.top}px`,
          left: `${tooltipPosition.left}px`,
          transform:
            currentStepData.position === "bottom" || currentStepData.position === "top"
              ? "translateX(-50%)"
              : currentStepData.position === "left"
                ? "translateX(-100%)"
                : "translateX(0)",
          marginTop: currentStepData.position === "top" ? "-100%" : "0",
        }}
      >
        <div className="card max-w-sm shadow-2xl">
          {/* Header */}
          <div className="flex items-start justify-between mb-16">
            <div className="flex-1">
              <div className="flex items-center gap-8 mb-8">
                <span className="text-tiny font-medium text-accent-primary">
                  Step {currentStep + 1} of {tourSteps.length}
                </span>
              </div>
              <h3 className="text-h3">{currentStepData.title}</h3>
            </div>
            <button
              onClick={onSkip}
              className="text-dark-text-tertiary hover:text-dark-text-primary transition-colors"
              aria-label="Close tour"
            >
              <X size={20} />
            </button>
          </div>

          {/* Content */}
          <p className="text-body text-dark-text-secondary mb-24">{currentStepData.description}</p>

          {/* Progress Dots */}
          <div className="flex items-center gap-8 mb-24">
            {tourSteps.map((_, index) => (
              <div
                key={index}
                className={`h-6 rounded-full transition-all ${
                  index === currentStep
                    ? "w-24 bg-accent-primary"
                    : index < currentStep
                      ? "w-6 bg-accent-primary/50"
                      : "w-6 bg-dark-bg-tertiary"
                }`}
              />
            ))}
          </div>

          {/* Navigation */}
          <div className="flex items-center justify-between">
            <button
              onClick={handlePrevious}
              disabled={currentStep === 0}
              className="btn btn-secondary btn-sm"
            >
              <ArrowLeft size={16} className="mr-8" />
              Back
            </button>

            <button
              onClick={onSkip}
              className="text-small text-dark-text-tertiary hover:text-dark-text-secondary transition-colors"
            >
              Skip Tour
            </button>

            <button onClick={handleNext} className="btn btn-primary btn-sm">
              {isLastStep ? (
                <>
                  Finish
                  <Check size={16} className="ml-8" />
                </>
              ) : (
                <>
                  Next
                  <ArrowRight size={16} className="ml-8" />
                </>
              )}
            </button>
          </div>
        </div>

        {/* Arrow indicator */}
        <div
          className={`absolute w-0 h-0 border-8 ${
            currentStepData.position === "bottom"
              ? "border-transparent border-b-dark-bg-secondary -top-16 left-1/2 -translate-x-1/2"
              : currentStepData.position === "top"
                ? "border-transparent border-t-dark-bg-secondary -bottom-16 left-1/2 -translate-x-1/2"
                : currentStepData.position === "left"
                  ? "border-transparent border-l-dark-bg-secondary -right-16 top-1/2 -translate-y-1/2"
                  : "border-transparent border-r-dark-bg-secondary -left-16 top-1/2 -translate-y-1/2"
          }`}
        />
      </div>
    </>
  );
};

export default GuidedTour;
