import React, { useState, useEffect, useCallback } from "react";
import { Zap, DollarSign, Leaf, Clock, HelpCircle, Server, Cpu, Database } from "lucide-react";
import { WizardState, TrainingEstimates } from "../../types/wizard";
import Tooltip from "../Tooltip";

interface EnhancedConfigurationStepProps {
  wizardState: WizardState;
  onConfigUpdate: (config: Partial<TrainingConfig>, estimates: TrainingEstimates) => void;
}

type PEFTAlgorithm = "lora" | "qlora" | "dora" | "pissa" | "rslora";
type QuantizationType = "none" | "int8" | "int4" | "nf4";
type ComputeProvider = "local" | "runpod" | "lambda" | "vastai";
type ExperimentTracker = "none" | "wandb" | "cometml" | "phoenix";

interface EnhancedConfig {
  // Provider
  provider: ComputeProvider;
  resourceId?: string;

  // Algorithm
  algorithm: PEFTAlgorithm;

  // Quantization
  quantization: QuantizationType;

  // Experiment Tracking
  experimentTracker: ExperimentTracker;
  projectName?: string;

  // Core settings (from smart config)
  batchSize: number;
  gradientAccumulation: number;
  learningRate: number;
  epochs: number;
  precision: string;
}

/**
 * Enhanced Configuration Step with Provider, Algorithm, Quantization, and Tracker Selection
 * Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5
 */
const EnhancedConfigurationStep: React.FC<EnhancedConfigurationStepProps> = ({
  wizardState,
  onConfigUpdate,
}) => {
  const [loading, setLoading] = useState(true);
  const [electricityRate, setElectricityRate] = useState(0.12);
  const [smartConfig, setSmartConfig] = useState<Record<string, unknown> | null>(null);
  const [estimates, setEstimates] = useState<TrainingEstimates | null>(null);

  // Enhanced configuration state
  const [enhancedConfig, setEnhancedConfig] = useState<EnhancedConfig>({
    provider: "local",
    algorithm: "lora",
    quantization: "none",
    experimentTracker: "none",
    batchSize: 4,
    gradientAccumulation: 4,
    learningRate: 2e-4,
    epochs: 3,
    precision: "fp16",
  });

  const [availableProviders, setAvailableProviders] = useState<
    Array<{ id: string; name: string;[key: string]: unknown }>
  >([]);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  const fetchAvailableProviders = useCallback(async () => {
    try {
      // Fetch connected providers
      const response = await fetch("http://127.0.0.1:8000/api/platforms/connections");
      const data = await response.json();

      // Always include local
      const providers = [{ id: "local", name: "Local GPU", status: "available", cost: 0 }];

      // Add connected cloud providers
      if (data.connections) {
        data.connections.forEach(
          (conn: { status: string; platform_name: string; name: string }) => {
            if (
              conn.status === "connected" &&
              ["runpod", "lambda", "vastai"].includes(conn.platform_name)
            ) {
              providers.push({
                id: conn.platform_name,
                name: conn.platform_name.charAt(0).toUpperCase() + conn.platform_name.slice(1),
                status: "available",
                cost: 0.5, // Placeholder
              });
            }
          }
        );
      }

      setAvailableProviders(providers);
    } catch (error) {
      console.error("Error fetching providers:", error);
      setAvailableProviders([{ id: "local", name: "Local GPU", status: "available", cost: 0 }]);
    }
  }, []);

  const validateConfiguration = useCallback(
    (config: EnhancedConfig, smartConfig: Record<string, unknown>) => {
      const errors: string[] = [];

      // Validate provider selection
      if (!config.provider) {
        errors.push("Compute provider must be selected");
      }

      // Validate algorithm selection
      if (!config.algorithm) {
        errors.push("PEFT algorithm must be selected");
      }

      // Validate quantization compatibility
      if (config.quantization !== "none" && config.algorithm === "dora") {
        errors.push("DoRA is not compatible with quantization");
      }

      // Validate experiment tracker project name
      if (config.experimentTracker !== "none" && !config.projectName) {
        errors.push("Project name required for experiment tracking");
      }

      // Validate memory requirements
      if (smartConfig && (smartConfig as any).estimated_memory_mb > 24000 && config.provider === "local") {
        errors.push("Configuration requires more memory than available on local GPU");
      }

      setValidationErrors(errors);
    },
    []
  );

  const calculateSmartDefaults = useCallback(async () => {
    try {
      setLoading(true);

      // Get hardware profile
      const hardwareResponse = await fetch("http://127.0.0.1:8000/api/hardware/profile");
      const hardwareData = await hardwareResponse.json();

      const gpuMemoryMB = hardwareData.gpus[0]?.memory_available_gb * 1024 || 8000;
      const cpuCores = hardwareData.cpu?.cores_physical || 8;
      const ramGB = hardwareData.ram?.available_gb || 16;

      // Calculate smart defaults with algorithm and quantization
      const configResponse = await fetch("http://127.0.0.1:8000/api/config/smart-defaults", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          gpu_memory_mb: gpuMemoryMB,
          cpu_cores: cpuCores,
          ram_gb: ramGB,
          compute_capability: hardwareData.gpus[0]?.compute_capability,
          model_size_mb: wizardState.model!.size_mb,
          num_parameters: wizardState.model!.parameters,
          max_seq_length: wizardState.profile!.config.max_seq_length,
          architecture: wizardState.model!.architecture,
          num_samples: wizardState.dataset!.num_samples || 1000,
          avg_sequence_length: wizardState.profile!.config.max_seq_length / 2,
          max_sequence_length: wizardState.profile!.config.max_seq_length,
          target_effective_batch_size: 32,
          algorithm: enhancedConfig.algorithm,
          quantization: enhancedConfig.quantization,
        }),
      });

      const configData = await configResponse.json();
      setSmartConfig(configData);

      // Update enhanced config with smart defaults
      setEnhancedConfig((prev) => ({
        ...prev,
        batchSize: configData.batch_size,
        gradientAccumulation: configData.gradient_accumulation_steps,
        learningRate: configData.learning_rate,
        epochs: configData.num_epochs,
        precision: configData.precision,
      }));

      // Calculate estimates
      const trainingSeconds = configData.estimated_training_time_hours * 3600;
      const gpuHours = configData.estimated_training_time_hours;
      const electricityCost = gpuHours * 0.3 * electricityRate;
      const carbonFootprint = gpuHours * 0.3 * 0.5;

      const newEstimates: TrainingEstimates = {
        duration: {
          min: trainingSeconds * 0.8,
          expected: trainingSeconds,
          max: trainingSeconds * 1.2,
        },
        cost: {
          electricityCost,
          gpuHours,
          carbonFootprint,
        },
        resources: {
          peakMemory: configData.estimated_memory_mb,
          avgGPUUtilization: 85,
          diskSpace: wizardState.model!.size_mb * 2,
        },
        confidence: 0.8,
      };

      setEstimates(newEstimates);

      // Validate configuration
      validateConfiguration(enhancedConfig, configData);

      // Notify parent
      onConfigUpdate({ ...configData, ...enhancedConfig }, newEstimates);
    } catch (error) {
      console.error("Error calculating smart defaults:", error);
    } finally {
      setLoading(false);
    }
  }, [
    wizardState.model,
    wizardState.dataset,
    wizardState.profile,
    electricityRate,
    enhancedConfig,
    onConfigUpdate,
    validateConfiguration,
  ]);

  useEffect(() => {
    if (wizardState.model && wizardState.dataset && wizardState.profile) {
      calculateSmartDefaults();
      fetchAvailableProviders();
    }
  }, [
    wizardState.model,
    wizardState.dataset,
    wizardState.profile,
    calculateSmartDefaults,
    fetchAvailableProviders,
  ]);

  const handleProviderChange = (provider: ComputeProvider) => {
    const updated = { ...enhancedConfig, provider };
    setEnhancedConfig(updated);
    validateConfiguration(updated, smartConfig as Record<string, unknown>);
  };

  const handleAlgorithmChange = (algorithm: PEFTAlgorithm) => {
    const updated = { ...enhancedConfig, algorithm };
    setEnhancedConfig(updated);
    // Recalculate with new algorithm
    calculateSmartDefaults();
  };

  const handleQuantizationChange = (quantization: QuantizationType) => {
    const updated = { ...enhancedConfig, quantization };
    setEnhancedConfig(updated);
    // Recalculate with new quantization
    calculateSmartDefaults();
  };

  const handleTrackerChange = (tracker: ExperimentTracker) => {
    const updated = { ...enhancedConfig, experimentTracker: tracker };
    setEnhancedConfig(updated);
    validateConfiguration(updated, smartConfig as Record<string, unknown>);
  };

  const handleProjectNameChange = (projectName: string) => {
    const updated = { ...enhancedConfig, projectName };
    setEnhancedConfig(updated);
    validateConfiguration(updated, smartConfig as Record<string, unknown>);
  };

  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  if (loading || !smartConfig || !estimates) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <Zap className="w-12 h-12 text-blue-600 animate-pulse mx-auto mb-4" />
          <p className="text-gray-600">Calculating optimal configuration...</p>
          <p className="text-sm text-gray-500 mt-2">Analyzing your hardware, model, and dataset</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-blue-900 mb-2">
          Enhanced Training Configuration
        </h2>
        <p className="text-blue-800">
          Configure your training environment, algorithm, and tracking preferences. We&apos;ve
          calculated optimal settings, but you can customize as needed.
        </p>
      </div>

      {/* Validation Errors */}
      {validationErrors.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h4 className="font-semibold text-red-900 mb-2">Configuration Issues</h4>
          <ul className="list-disc list-inside space-y-1">
            {validationErrors.map((error, idx) => (
              <li key={idx} className="text-sm text-red-800">
                {error}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Provider Selection */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center gap-2 mb-4">
          <Server className="w-5 h-5 text-gray-700" />
          <h3 className="text-lg font-semibold text-gray-900">Compute Provider</h3>
          <Tooltip configKey="compute_provider">
            <HelpCircle className="w-4 h-4 text-gray-400 cursor-help" />
          </Tooltip>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {availableProviders.map((provider) => (
            <button
              key={provider.id}
              onClick={() => handleProviderChange(provider.id as ComputeProvider)}
              className={`
                p-4 rounded-lg border-2 transition-all text-left
                ${enhancedConfig.provider === provider.id
                  ? "border-blue-600 bg-blue-50"
                  : "border-gray-200 hover:border-gray-300"
                }
              `}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-gray-900">{provider.name}</span>
                {enhancedConfig.provider === provider.id && (
                  <span className="text-blue-600">✓</span>
                )}
              </div>
              <p className="text-sm text-gray-600">
                {provider.cost === 0 ? "Free" : `$${provider.cost}/hr`}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Algorithm Selection */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center gap-2 mb-4">
          <Cpu className="w-5 h-5 text-gray-700" />
          <h3 className="text-lg font-semibold text-gray-900">PEFT Algorithm</h3>
          <Tooltip configKey="peft_algorithm">
            <HelpCircle className="w-4 h-4 text-gray-400 cursor-help" />
          </Tooltip>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {(["lora", "qlora", "dora", "pissa", "rslora"] as PEFTAlgorithm[]).map((algo) => (
            <button
              key={algo}
              onClick={() => handleAlgorithmChange(algo)}
              className={`
                p-4 rounded-lg border-2 transition-all text-left
                ${enhancedConfig.algorithm === algo
                  ? "border-blue-600 bg-blue-50"
                  : "border-gray-200 hover:border-gray-300"
                }
              `}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-gray-900 uppercase">{algo}</span>
                {enhancedConfig.algorithm === algo && <span className="text-blue-600">✓</span>}
              </div>
              <p className="text-xs text-gray-600">
                {algo === "lora" && "Standard LoRA"}
                {algo === "qlora" && "4-bit quantized"}
                {algo === "dora" && "Weight decomposition"}
                {algo === "pissa" && "Principal singular values"}
                {algo === "rslora" && "Rank-stabilized"}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Quantization Configuration */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center gap-2 mb-4">
          <Database className="w-5 h-5 text-gray-700" />
          <h3 className="text-lg font-semibold text-gray-900">Quantization</h3>
          <Tooltip configKey="quantization">
            <HelpCircle className="w-4 h-4 text-gray-400 cursor-help" />
          </Tooltip>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {(["none", "int8", "int4", "nf4"] as QuantizationType[]).map((quant) => (
            <button
              key={quant}
              onClick={() => handleQuantizationChange(quant)}
              disabled={quant !== "none" && enhancedConfig.algorithm === "dora"}
              className={`
                p-4 rounded-lg border-2 transition-all text-left
                ${enhancedConfig.quantization === quant
                  ? "border-blue-600 bg-blue-50"
                  : "border-gray-200 hover:border-gray-300"
                }
                ${quant !== "none" && enhancedConfig.algorithm === "dora" ? "opacity-50 cursor-not-allowed" : ""}
              `}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-gray-900 uppercase">{quant}</span>
                {enhancedConfig.quantization === quant && <span className="text-blue-600">✓</span>}
              </div>
              <p className="text-xs text-gray-600">
                {quant === "none" && "Full precision"}
                {quant === "int8" && "8-bit integers"}
                {quant === "int4" && "4-bit integers"}
                {quant === "nf4" && "4-bit NormalFloat"}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Experiment Tracker Selection */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center gap-2 mb-4">
          <Database className="w-5 h-5 text-gray-700" />
          <h3 className="text-lg font-semibold text-gray-900">Experiment Tracking</h3>
          <Tooltip configKey="experiment_tracker">
            <HelpCircle className="w-4 h-4 text-gray-400 cursor-help" />
          </Tooltip>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          {(["none", "wandb", "cometml", "phoenix"] as ExperimentTracker[]).map((tracker) => (
            <button
              key={tracker}
              onClick={() => handleTrackerChange(tracker)}
              className={`
                p-4 rounded-lg border-2 transition-all text-left
                ${enhancedConfig.experimentTracker === tracker
                  ? "border-blue-600 bg-blue-50"
                  : "border-gray-200 hover:border-gray-300"
                }
              `}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-gray-900 capitalize">
                  {tracker === "none"
                    ? "None"
                    : tracker === "wandb"
                      ? "W&B"
                      : tracker === "cometml"
                        ? "Comet ML"
                        : "Phoenix"}
                </span>
                {enhancedConfig.experimentTracker === tracker && (
                  <span className="text-blue-600">✓</span>
                )}
              </div>
            </button>
          ))}
        </div>

        {enhancedConfig.experimentTracker !== "none" && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Project Name *</label>
            <input
              type="text"
              value={enhancedConfig.projectName || ""}
              onChange={(e) => handleProjectNameChange(e.target.value)}
              placeholder="my-finetuning-project"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent"
            />
          </div>
        )}
      </div>

      {/* Training Estimates */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center gap-2 mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Training Estimates</h3>
          <Tooltip configKey="training_estimates">
            <HelpCircle className="w-4 h-4 text-gray-400 cursor-help" />
          </Tooltip>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Duration */}
          <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex items-center gap-2 mb-2">
              <Clock className="w-5 h-5 text-blue-600" />
              <span className="text-sm font-medium text-blue-900">Training Time</span>
            </div>
            <p className="text-2xl font-bold text-blue-900">
              {formatDuration(estimates.duration.expected)}
            </p>
            <p className="text-xs text-blue-700 mt-1">
              {formatDuration(estimates.duration.min)} - {formatDuration(estimates.duration.max)}
            </p>
          </div>

          {/* GPU Hours */}
          <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="w-5 h-5 text-purple-600" />
              <span className="text-sm font-medium text-purple-900">GPU Hours</span>
            </div>
            <p className="text-2xl font-bold text-purple-900">
              {estimates.cost.gpuHours.toFixed(2)}
            </p>
            <p className="text-xs text-purple-700 mt-1">
              {estimates.resources.avgGPUUtilization}% avg utilization
            </p>
          </div>

          {/* Cost */}
          <div className="p-4 bg-green-50 rounded-lg border border-green-200">
            <div className="flex items-center gap-2 mb-2">
              <DollarSign className="w-5 h-5 text-green-600" />
              <span className="text-sm font-medium text-green-900">Electricity Cost</span>
            </div>
            <p className="text-2xl font-bold text-green-900">
              ${estimates.cost.electricityCost.toFixed(2)}
            </p>
            <div className="mt-2">
              <input
                type="number"
                value={electricityRate}
                onChange={(e) => setElectricityRate(parseFloat(e.target.value) || 0.12)}
                step="0.01"
                min="0"
                className="w-full text-xs px-2 py-1 border border-green-300 rounded"
                placeholder="$/kWh"
              />
            </div>
          </div>

          {/* Carbon */}
          <div className="p-4 bg-emerald-50 rounded-lg border border-emerald-200">
            <div className="flex items-center gap-2 mb-2">
              <Leaf className="w-5 h-5 text-emerald-600" />
              <span className="text-sm font-medium text-emerald-900">Carbon Footprint</span>
            </div>
            <p className="text-2xl font-bold text-emerald-900">
              {estimates.cost.carbonFootprint.toFixed(2)}
            </p>
            <p className="text-xs text-emerald-700 mt-1">kg CO₂</p>
          </div>
        </div>
      </div>

      {/* Core Configuration Display */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Core Configuration</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="text-sm font-medium text-gray-700">Batch Size</label>
            <div className="p-3 bg-gray-50 rounded border border-gray-200 mt-2">
              <p className="text-lg font-semibold text-gray-900">{enhancedConfig.batchSize}</p>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700">Gradient Accumulation</label>
            <div className="p-3 bg-gray-50 rounded border border-gray-200 mt-2">
              <p className="text-lg font-semibold text-gray-900">
                {enhancedConfig.gradientAccumulation}
              </p>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700">Learning Rate</label>
            <div className="p-3 bg-gray-50 rounded border border-gray-200 mt-2">
              <p className="text-lg font-semibold text-gray-900">{enhancedConfig.learningRate}</p>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700">Epochs</label>
            <div className="p-3 bg-gray-50 rounded border border-gray-200 mt-2">
              <p className="text-lg font-semibold text-gray-900">{enhancedConfig.epochs}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Ready Status */}
      {validationErrors.length === 0 ? (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <h4 className="font-semibold text-green-900 mb-2">✓ Configuration Complete</h4>
          <p className="text-sm text-green-800">
            Your training is configured and ready to launch. Click &quot;Next&quot; to review
            everything before starting.
          </p>
        </div>
      ) : (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <h4 className="font-semibold text-yellow-900 mb-2">⚠ Configuration Incomplete</h4>
          <p className="text-sm text-yellow-800">
            Please resolve the validation issues above before proceeding.
          </p>
        </div>
      )}
    </div>
  );
};

export default EnhancedConfigurationStep;
