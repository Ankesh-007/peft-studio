/**
 * Deployment Configuration Wizard
 * 
 * Multi-step wizard for configuring model deployments.
 * Allows users to select platform, configure settings, and deploy models.
 * 
 * Requirements: 9.1, 9.2
 */

import React, { useState } from 'react';

interface DeploymentConfig {
  deployment_id: string;
  name: string;
  platform: string;
  model_path: string;
  base_model?: string;
  instance_type?: string;
  min_instances: number;
  max_instances: number;
  auto_scaling: boolean;
  max_batch_size: number;
  timeout_seconds: number;
  environment_vars: Record<string, string>;
  description?: string;
  tags: string[];
}

interface DeploymentConfigurationWizardProps {
  onDeploy: (config: DeploymentConfig) => Promise<void>;
  onCancel: () => void;
  availableModels: Array<{ path: string; name: string; base_model?: string }>;
}

type WizardStep = 'platform' | 'model' | 'configuration' | 'review';

const PLATFORMS = [
  {
    id: 'predibase',
    name: 'Predibase',
    description: 'Hot-swappable adapter serving on shared base models',
    features: ['LoRAX', 'Multi-adapter', 'Cost-effective'],
    icon: '🚀'
  },
  {
    id: 'together_ai',
    name: 'Together AI',
    description: 'Serverless endpoints with pay-per-token pricing',
    features: ['Serverless', 'Auto-scaling', 'Global CDN'],
    icon: '⚡'
  },
  {
    id: 'modal',
    name: 'Modal',
    description: 'Function deployment with cold-start optimization',
    features: ['Fast cold-start', 'Flexible', 'Developer-friendly'],
    icon: '🎯'
  },
  {
    id: 'replicate',
    name: 'Replicate',
    description: 'Simple model deployment with version management',
    features: ['Easy setup', 'Versioning', 'Public/Private'],
    icon: '🔄'
  }
];

export const DeploymentConfigurationWizard: React.FC<DeploymentConfigurationWizardProps> = ({
  onDeploy,
  onCancel,
  availableModels
}) => {
  const [currentStep, setCurrentStep] = useState<WizardStep>('platform');
  const [config, setConfig] = useState<Partial<DeploymentConfig>>({
    min_instances: 1,
    max_instances: 10,
    auto_scaling: true,
    max_batch_size: 1,
    timeout_seconds: 60,
    environment_vars: {},
    tags: []
  });
  const [isDeploying, setIsDeploying] = useState(false);

  const updateConfig = (updates: Partial<DeploymentConfig>) => {
    setConfig(prev => ({ ...prev, ...updates }));
  };

  const handleNext = () => {
    const steps: WizardStep[] = ['platform', 'model', 'configuration', 'review'];
    const currentIndex = steps.indexOf(currentStep);
    if (currentIndex < steps.length - 1) {
      setCurrentStep(steps[currentIndex + 1]);
    }
  };

  const handleBack = () => {
    const steps: WizardStep[] = ['platform', 'model', 'configuration', 'review'];
    const currentIndex = steps.indexOf(currentStep);
    if (currentIndex > 0) {
      setCurrentStep(steps[currentIndex - 1]);
    }
  };

  const handleDeploy = async () => {
    if (!isConfigComplete()) return;
    
    setIsDeploying(true);
    try {
      await onDeploy(config as DeploymentConfig);
    } finally {
      setIsDeploying(false);
    }
  };

  const isConfigComplete = (): boolean => {
    return !!(
      config.deployment_id &&
      config.name &&
      config.platform &&
      config.model_path
    );
  };

  const renderPlatformSelection = () => (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Select Deployment Platform</h2>
      <p className="text-gray-600">Choose where you want to deploy your model</p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
        {PLATFORMS.map(platform => (
          <button
            key={platform.id}
            onClick={() => updateConfig({ platform: platform.id })}
            className={`p-6 border-2 rounded-lg text-left transition-all ${
              config.platform === platform.id
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="flex items-start gap-4">
              <span className="text-4xl">{platform.icon}</span>
              <div className="flex-1">
                <h3 className="text-lg font-semibold">{platform.name}</h3>
                <p className="text-sm text-gray-600 mt-1">{platform.description}</p>
                <div className="flex flex-wrap gap-2 mt-3">
                  {platform.features.map(feature => (
                    <span
                      key={feature}
                      className="px-2 py-1 bg-gray-100 text-xs rounded"
                    >
                      {feature}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );

  const renderModelSelection = () => (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Select Model</h2>
      <p className="text-gray-600">Choose the model or adapter to deploy</p>
      
      <div className="mt-6 space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">Deployment Name</label>
          <input
            type="text"
            value={config.name || ''}
            onChange={e => updateConfig({ name: e.target.value })}
            placeholder="my-awesome-model"
            className="w-full px-4 py-2 border rounded-lg"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Deployment ID</label>
          <input
            type="text"
            value={config.deployment_id || ''}
            onChange={e => updateConfig({ deployment_id: e.target.value })}
            placeholder="deploy_123"
            className="w-full px-4 py-2 border rounded-lg"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Model/Adapter</label>
          <select
            value={config.model_path || ''}
            onChange={e => {
              const selected = availableModels.find(m => m.path === e.target.value);
              updateConfig({
                model_path: e.target.value,
                base_model: selected?.base_model
              });
            }}
            className="w-full px-4 py-2 border rounded-lg"
          >
            <option value="">Select a model...</option>
            {availableModels.map(model => (
              <option key={model.path} value={model.path}>
                {model.name}
              </option>
            ))}
          </select>
        </div>

        {config.base_model && (
          <div className="p-4 bg-blue-50 rounded-lg">
            <p className="text-sm">
              <strong>Base Model:</strong> {config.base_model}
            </p>
          </div>
        )}
      </div>
    </div>
  );

  const renderConfiguration = () => (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Configure Deployment</h2>
      <p className="text-gray-600">Set up scaling and performance parameters</p>
      
      <div className="mt-6 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Min Instances</label>
            <input
              type="number"
              min="1"
              value={config.min_instances || 1}
              onChange={e => updateConfig({ min_instances: parseInt(e.target.value) })}
              className="w-full px-4 py-2 border rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Max Instances</label>
            <input
              type="number"
              min="1"
              value={config.max_instances || 10}
              onChange={e => updateConfig({ max_instances: parseInt(e.target.value) })}
              className="w-full px-4 py-2 border rounded-lg"
            />
          </div>
        </div>

        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="auto_scaling"
            checked={config.auto_scaling || false}
            onChange={e => updateConfig({ auto_scaling: e.target.checked })}
            className="w-4 h-4"
          />
          <label htmlFor="auto_scaling" className="text-sm font-medium">
            Enable Auto-scaling
          </label>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Instance Type (Optional)</label>
          <input
            type="text"
            value={config.instance_type || ''}
            onChange={e => updateConfig({ instance_type: e.target.value })}
            placeholder="e.g., gpu.a100.1x"
            className="w-full px-4 py-2 border rounded-lg"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Max Batch Size</label>
            <input
              type="number"
              min="1"
              value={config.max_batch_size || 1}
              onChange={e => updateConfig({ max_batch_size: parseInt(e.target.value) })}
              className="w-full px-4 py-2 border rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Timeout (seconds)</label>
            <input
              type="number"
              min="1"
              value={config.timeout_seconds || 60}
              onChange={e => updateConfig({ timeout_seconds: parseInt(e.target.value) })}
              className="w-full px-4 py-2 border rounded-lg"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Description (Optional)</label>
          <textarea
            value={config.description || ''}
            onChange={e => updateConfig({ description: e.target.value })}
            placeholder="Describe your deployment..."
            rows={3}
            className="w-full px-4 py-2 border rounded-lg"
          />
        </div>
      </div>
    </div>
  );

  const renderReview = () => {
    const platform = PLATFORMS.find(p => p.id === config.platform);
    
    return (
      <div className="space-y-4">
        <h2 className="text-2xl font-bold">Review & Deploy</h2>
        <p className="text-gray-600">Review your configuration before deploying</p>
        
        <div className="mt-6 space-y-4">
          <div className="p-4 bg-gray-50 rounded-lg space-y-3">
            <div>
              <span className="text-sm font-medium text-gray-600">Platform:</span>
              <p className="text-lg">{platform?.name}</p>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-600">Deployment Name:</span>
              <p className="text-lg">{config.name}</p>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-600">Model:</span>
              <p className="text-lg">{config.model_path}</p>
            </div>
            {config.base_model && (
              <div>
                <span className="text-sm font-medium text-gray-600">Base Model:</span>
                <p className="text-lg">{config.base_model}</p>
              </div>
            )}
            <div className="grid grid-cols-2 gap-4 pt-2">
              <div>
                <span className="text-sm font-medium text-gray-600">Instances:</span>
                <p>{config.min_instances} - {config.max_instances}</p>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-600">Auto-scaling:</span>
                <p>{config.auto_scaling ? 'Enabled' : 'Disabled'}</p>
              </div>
            </div>
          </div>

          {!isConfigComplete() && (
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-800">
                Please complete all required fields before deploying.
              </p>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Progress indicator */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {['platform', 'model', 'configuration', 'review'].map((step, index) => (
            <React.Fragment key={step}>
              <div className="flex flex-col items-center">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    currentStep === step
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 text-gray-600'
                  }`}
                >
                  {index + 1}
                </div>
                <span className="text-xs mt-2 capitalize">{step}</span>
              </div>
              {index < 3 && (
                <div className="flex-1 h-1 bg-gray-200 mx-2" />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Step content */}
      <div className="bg-white rounded-lg shadow-lg p-8">
        {currentStep === 'platform' && renderPlatformSelection()}
        {currentStep === 'model' && renderModelSelection()}
        {currentStep === 'configuration' && renderConfiguration()}
        {currentStep === 'review' && renderReview()}

        {/* Navigation buttons */}
        <div className="flex justify-between mt-8 pt-6 border-t">
          <button
            onClick={currentStep === 'platform' ? onCancel : handleBack}
            className="px-6 py-2 border rounded-lg hover:bg-gray-50"
          >
            {currentStep === 'platform' ? 'Cancel' : 'Back'}
          </button>
          
          {currentStep === 'review' ? (
            <button
              onClick={handleDeploy}
              disabled={!isConfigComplete() || isDeploying}
              className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isDeploying ? 'Deploying...' : 'Deploy'}
            </button>
          ) : (
            <button
              onClick={handleNext}
              disabled={
                (currentStep === 'platform' && !config.platform) ||
                (currentStep === 'model' && (!config.name || !config.deployment_id || !config.model_path))
              }
              className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
