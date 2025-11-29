import React, { useState } from 'react';
import { Check, ChevronRight, ChevronLeft, Download, Database, Cpu } from 'lucide-react';

interface SetupWizardProps {
  onComplete: () => void;
  onSkip: () => void;
}

const SetupWizard: React.FC<SetupWizardProps> = ({ onComplete, onSkip }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [setupData, setSetupData] = useState({
    downloadSample: false,
    hardwareDetected: false,
    preferencesSet: false
  });

  const steps = [
    {
      id: 'hardware',
      title: 'Hardware Detection',
      description: 'Let\'s check your system capabilities',
      icon: Cpu,
      content: (
        <div className="space-y-24">
          <p className="text-body text-dark-text-secondary">
            PEFT Studio will automatically detect your GPU, CPU, and RAM to optimize training settings.
          </p>
          
          <div className="card bg-dark-bg-tertiary">
            <div className="flex items-center justify-between mb-16">
              <span className="text-body font-medium">GPU Detection</span>
              {setupData.hardwareDetected ? (
                <Check size={20} className="text-accent-success" />
              ) : (
                <div className="w-20 h-20 border-2 border-accent-primary border-t-transparent rounded-full animate-spin" />
              )}
            </div>
            <div className="space-y-8 text-small text-dark-text-secondary">
              <div className="flex justify-between">
                <span>GPU Memory:</span>
                <span className="text-dark-text-primary">24 GB</span>
              </div>
              <div className="flex justify-between">
                <span>CUDA Version:</span>
                <span className="text-dark-text-primary">12.1</span>
              </div>
              <div className="flex justify-between">
                <span>Compute Capability:</span>
                <span className="text-dark-text-primary">8.6</span>
              </div>
            </div>
          </div>

          <button
            onClick={() => {
              setSetupData({ ...setupData, hardwareDetected: true });
              setTimeout(() => setCurrentStep(1), 500);
            }}
            disabled={setupData.hardwareDetected}
            className="btn btn-primary w-full"
          >
            {setupData.hardwareDetected ? 'Hardware Detected' : 'Detect Hardware'}
          </button>
        </div>
      )
    },
    {
      id: 'sample',
      title: 'Sample Dataset & Model',
      description: 'Download a sample to try out the features',
      icon: Database,
      content: (
        <div className="space-y-24">
          <p className="text-body text-dark-text-secondary">
            We recommend downloading a sample dataset and model to explore PEFT Studio's features.
          </p>

          <div className="card bg-dark-bg-tertiary">
            <div className="flex items-start gap-16 mb-16">
              <Download size={24} className="text-accent-info flex-shrink-0 mt-4" />
              <div className="flex-1">
                <h4 className="text-body font-medium mb-8">Sample Package</h4>
                <p className="text-small text-dark-text-secondary mb-12">
                  Includes a small conversational dataset and Llama-3-8B model for testing
                </p>
                <div className="text-tiny text-dark-text-tertiary">
                  Size: ~500 MB • Download time: ~2 minutes
                </div>
              </div>
            </div>

            {setupData.downloadSample && (
              <div className="mt-16 p-12 bg-accent-success/10 border border-accent-success/20 rounded-lg">
                <div className="flex items-center gap-8 text-small text-accent-success">
                  <Check size={16} />
                  <span>Sample package ready to use</span>
                </div>
              </div>
            )}
          </div>

          <div className="flex gap-12">
            <button
              onClick={() => {
                setSetupData({ ...setupData, downloadSample: true });
                setTimeout(() => setCurrentStep(2), 500);
              }}
              disabled={setupData.downloadSample}
              className="btn btn-primary flex-1"
            >
              {setupData.downloadSample ? 'Downloaded' : 'Download Sample'}
            </button>
            <button
              onClick={() => setCurrentStep(2)}
              className="btn btn-secondary"
            >
              Skip
            </button>
          </div>
        </div>
      )
    },
    {
      id: 'preferences',
      title: 'Quick Preferences',
      description: 'Set your default preferences',
      icon: Check,
      content: (
        <div className="space-y-24">
          <p className="text-body text-dark-text-secondary">
            These can be changed later in settings.
          </p>

          <div className="space-y-16">
            <div className="card bg-dark-bg-tertiary">
              <label className="flex items-center justify-between cursor-pointer">
                <div>
                  <div className="text-body font-medium mb-4">Enable Notifications</div>
                  <div className="text-small text-dark-text-secondary">
                    Get notified when training completes or errors occur
                  </div>
                </div>
                <input
                  type="checkbox"
                  defaultChecked
                  className="w-20 h-20 rounded border-dark-border bg-dark-bg-primary"
                />
              </label>
            </div>

            <div className="card bg-dark-bg-tertiary">
              <label className="flex items-center justify-between cursor-pointer">
                <div>
                  <div className="text-body font-medium mb-4">Auto-Save Checkpoints</div>
                  <div className="text-small text-dark-text-secondary">
                    Automatically save model checkpoints during training
                  </div>
                </div>
                <input
                  type="checkbox"
                  defaultChecked
                  className="w-20 h-20 rounded border-dark-border bg-dark-bg-primary"
                />
              </label>
            </div>

            <div className="card bg-dark-bg-tertiary">
              <label className="flex items-center justify-between cursor-pointer">
                <div>
                  <div className="text-body font-medium mb-4">Show Advanced Settings</div>
                  <div className="text-small text-dark-text-secondary">
                    Display advanced configuration options in wizards
                  </div>
                </div>
                <input
                  type="checkbox"
                  className="w-20 h-20 rounded border-dark-border bg-dark-bg-primary"
                />
              </label>
            </div>
          </div>

          <button
            onClick={() => {
              setSetupData({ ...setupData, preferencesSet: true });
              onComplete();
            }}
            className="btn btn-primary w-full"
          >
            Complete Setup
          </button>
        </div>
      )
    }
  ];

  const currentStepData = steps[currentStep];
  const Icon = currentStepData.icon;

  return (
    <div className="min-h-screen bg-dark-bg-primary flex items-center justify-center p-24">
      <div className="max-w-2xl w-full">
        {/* Progress Bar */}
        <div className="mb-32">
          <div className="flex items-center justify-between mb-12">
            {steps.map((step, index) => (
              <React.Fragment key={step.id}>
                <div className="flex flex-col items-center">
                  <div
                    className={`w-40 h-40 rounded-full flex items-center justify-center transition-all ${
                      index <= currentStep
                        ? 'bg-accent-primary text-white'
                        : 'bg-dark-bg-tertiary text-dark-text-tertiary'
                    }`}
                  >
                    {index < currentStep ? (
                      <Check size={20} />
                    ) : (
                      <span className="text-small font-medium">{index + 1}</span>
                    )}
                  </div>
                  <span className="text-tiny text-dark-text-tertiary mt-8">
                    {step.title.split(' ')[0]}
                  </span>
                </div>
                {index < steps.length - 1 && (
                  <div
                    className={`flex-1 h-2 mx-8 rounded-full transition-all ${
                      index < currentStep ? 'bg-accent-primary' : 'bg-dark-bg-tertiary'
                    }`}
                  />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* Step Content */}
        <div className="card animate-fade-in">
          <div className="flex items-center gap-16 mb-24">
            <div className="w-56 h-56 rounded-lg bg-accent-primary/10 flex items-center justify-center">
              <Icon size={28} className="text-accent-primary" />
            </div>
            <div>
              <h2 className="text-h2 mb-4">{currentStepData.title}</h2>
              <p className="text-small text-dark-text-secondary">
                {currentStepData.description}
              </p>
            </div>
          </div>

          {currentStepData.content}
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between mt-24">
          <button
            onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
            disabled={currentStep === 0}
            className="btn btn-secondary"
          >
            <ChevronLeft size={20} className="mr-8" />
            Back
          </button>

          <button
            onClick={onSkip}
            className="text-small text-dark-text-tertiary hover:text-dark-text-secondary transition-colors"
          >
            Skip Setup
          </button>

          {currentStep < steps.length - 1 && (
            <button
              onClick={() => setCurrentStep(currentStep + 1)}
              className="btn btn-secondary"
            >
              Next
              <ChevronRight size={20} className="ml-8" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default SetupWizard;
