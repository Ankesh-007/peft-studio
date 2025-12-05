import {
  ChevronDown,
  ChevronUp,
  Info,
  Zap,
  DollarSign,
  Leaf,
  Clock,
  HelpCircle,
} from "lucide-react";
import React, { useState, useEffect, useCallback } from "react";

import Tooltip from "../Tooltip";
import PEFTConfiguration from "../PEFTConfiguration";

import type { WizardState, TrainingEstimates } from "../../types/wizard";

interface SmartConfigurationStepProps {
  wizardState: WizardState;
  onConfigUpdate: (config: Partial<TrainingConfig>, estimates: TrainingEstimates) => void;
}

/**
 * Step 4: Smart Configuration Display
 * Shows auto-calculated settings with explanations and real-time estimates
 */
const SmartConfigurationStep: React.FC<SmartConfigurationStepProps> = ({
  wizardState,
  onConfigUpdate,
}) => {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [loading, setLoading] = useState(true);
  const [electricityRate, setElectricityRate] = useState(0.12);
  const [smartConfig, setSmartConfig] = useState<Record<string, unknown> | null>(null);
  const [estimates, setEstimates] = useState<TrainingEstimates | null>(null);
  const [peftConfig, setPeftConfig] = useState<Record<string, unknown> | null>(null);
  const [quantization, setQuantization] = useState<"4bit" | "8bit" | "none">("none");
  const [gradientCheckpointing, setGradientCheckpointing] = useState(false);

  const calculateSmartDefaults = useCallback(async () => {
    try {
      setLoading(true);

      // Get hardware profile
      const hardwareResponse = await fetch("http://127.0.0.1:8000/api/hardware/profile");
      const hardwareData = await hardwareResponse.json();

      const gpuMemoryMB = hardwareData.gpus[0]?.memory_available_gb * 1024 || 8000;
      const cpuCores = hardwareData.cpu?.cores_physical || 8;
      const ramGB = hardwareData.ram?.available_gb || 16;

      // Calculate smart defaults
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
        }),
      });

      const configData = await configResponse.json();
      setSmartConfig(configData);

      // Set initial quantization from smart config
      if (configData.quantization && configData.quantization !== "none") {
        setQuantization(configData.quantization);
      }

      // Set initial gradient checkpointing
      setGradientCheckpointing(configData.gradient_checkpointing || false);

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
      onConfigUpdate(
        {
          ...configData,
          quantization,
          gradient_checkpointing: gradientCheckpointing,
        },
        newEstimates
      );
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
    quantization,
    gradientCheckpointing,
    onConfigUpdate,
  ]);

  useEffect(() => {
    if (wizardState.model && wizardState.dataset && wizardState.profile) {
      calculateSmartDefaults();
    }
  }, [wizardState.model, wizardState.dataset, wizardState.profile, calculateSmartDefaults]);

  const handleQuantizationChange = (value: "4bit" | "8bit" | "none") => {
    setQuantization(value);
    if (smartConfig && estimates) {
      onConfigUpdate(
        {
          ...smartConfig,
          quantization: value,
          gradient_checkpointing: gradientCheckpointing,
          peft: peftConfig,
        },
        estimates
      );
    }
  };

  const handleGradientCheckpointingChange = (enabled: boolean) => {
    setGradientCheckpointing(enabled);
    if (smartConfig && estimates) {
      const updatedConfig = {
        ...smartConfig,
        quantization,
        gradient_checkpointing: enabled,
        peft: peftConfig,
        estimated_memory_mb: enabled
          ? (smartConfig as any).estimated_memory_mb * 0.7
          : (smartConfig as any).estimated_memory_mb / 0.7,
      };

      onConfigUpdate(updatedConfig, estimates);
    }
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
        <h2 className="text-xl font-semibold text-blue-900 mb-2">Smart Configuration Ready</h2>
        <p className="text-blue-800">
          We&apos;ve automatically calculated the optimal settings for your hardware and dataset.
          Everything is ready to go, but you can adjust advanced settings if needed.
        </p>
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

        <div className="mt-4 p-3 bg-gray-50 rounded border border-gray-200">
          <p className="text-xs text-gray-600">
            <Info className="w-3 h-3 inline mr-1" />
            Estimates are based on your hardware profile and may vary by ±20%. Confidence:{" "}
            {(estimates.confidence * 100).toFixed(0)}%
          </p>
        </div>
      </div>

      {/* Core Configuration */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Core Configuration</h3>

        {/* Quantization Options */}
        <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <div className="flex items-center gap-2 mb-3">
            <label className="text-sm font-medium text-gray-700">Quantization</label>
            <Tooltip configKey="quantization">
              <HelpCircle className="w-4 h-4 text-gray-400 cursor-help" />
            </Tooltip>
          </div>
          <div className="space-y-3">
            <label
              className="flex items-start p-3 border-2 rounded-lg cursor-pointer transition-all hover:bg-white"
              style={{
                borderColor: quantization === "none" ? "#3B82F6" : "#E5E7EB",
                backgroundColor: quantization === "none" ? "#EFF6FF" : "transparent",
              }}
            >
              <input
                type="radio"
                name="quantization"
                value="none"
                checked={quantization === "none"}
                onChange={(e) =>
                  handleQuantizationChange(e.target.value as "4bit" | "8bit" | "none")
                }
                className="mt-1 mr-3"
              />
              <div className="flex-1">
                <div className="font-medium text-gray-900">No Quantization (FP16/BF16)</div>
                <div className="text-sm text-gray-600 mt-1">
                  Full precision training. Best quality but requires more memory.
                </div>
              </div>
            </label>

            <label
              className="flex items-start p-3 border-2 rounded-lg cursor-pointer transition-all hover:bg-white"
              style={{
                borderColor: quantization === "8bit" ? "#3B82F6" : "#E5E7EB",
                backgroundColor: quantization === "8bit" ? "#EFF6FF" : "transparent",
              }}
            >
              <input
                type="radio"
                name="quantization"
                value="8bit"
                checked={quantization === "8bit"}
                onChange={(e) =>
                  handleQuantizationChange(e.target.value as "4bit" | "8bit" | "none")
                }
                className="mt-1 mr-3"
              />
              <div className="flex-1">
                <div className="font-medium text-gray-900">8-bit Quantization</div>
                <div className="text-sm text-gray-600 mt-1">
                  Reduces memory by ~50% with minimal quality loss. Good balance.
                </div>
              </div>
            </label>

            <label
              className="flex items-start p-3 border-2 rounded-lg cursor-pointer transition-all hover:bg-white"
              style={{
                borderColor: quantization === "4bit" ? "#3B82F6" : "#E5E7EB",
                backgroundColor: quantization === "4bit" ? "#EFF6FF" : "transparent",
              }}
            >
              <input
                type="radio"
                name="quantization"
                value="4bit"
                checked={quantization === "4bit"}
                onChange={(e) =>
                  handleQuantizationChange(e.target.value as "4bit" | "8bit" | "none")
                }
                className="mt-1 mr-3"
              />
              <div className="flex-1">
                <div className="font-medium text-gray-900">4-bit Quantization</div>
                <div className="text-sm text-gray-600 mt-1">
                  Reduces memory by ~75%. Enables training larger models on limited hardware.
                </div>
              </div>
            </label>
          </div>
        </div>

        {/* Gradient Checkpointing Toggle */}
        <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <label className="text-sm font-medium text-gray-700">Gradient Checkpointing</label>
                <Tooltip configKey="gradient_checkpointing">
                  <HelpCircle className="w-4 h-4 text-gray-400 cursor-help" />
                </Tooltip>
              </div>
              <p className="text-sm text-gray-600 mb-2">
                Trades computation time for memory savings. Reduces memory usage by ~30% but
                increases training time by ~20%.
              </p>
              {gradientCheckpointing && (
                <div className="flex items-center gap-2 text-sm text-green-700 bg-green-50 px-3 py-2 rounded border border-green-200">
                  <Leaf className="w-4 h-4" />
                  <span>
                    Estimated memory savings:{" "}
                    {(((smartConfig as any).estimated_memory_mb * 0.3) / 1024).toFixed(1)} GB
                  </span>
                </div>
              )}
            </div>
            <label className="relative inline-flex items-center cursor-pointer ml-4">
              <input
                type="checkbox"
                checked={gradientCheckpointing}
                onChange={(e) => handleGradientCheckpointingChange(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Batch Size */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <label className="text-sm font-medium text-gray-700">Batch Size</label>
              <Tooltip configKey="batch_size">
                <HelpCircle className="w-4 h-4 text-gray-400 cursor-help" />
              </Tooltip>
            </div>
            <div className="p-3 bg-gray-50 rounded border border-gray-200">
              <p className="text-lg font-semibold text-gray-900">{(smartConfig as any).batch_size}</p>
              <p className="text-xs text-gray-600 mt-1">
                {(smartConfig as any).explanations?.batch_size || "Optimized for your GPU memory"}
              </p>
            </div>
          </div>

          {/* Gradient Accumulation */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <label className="text-sm font-medium text-gray-700">Gradient Accumulation</label>
              <Tooltip configKey="gradient_accumulation">
                <HelpCircle className="w-4 h-4 text-gray-400 cursor-help" />
              </Tooltip>
            </div>
            <div className="p-3 bg-gray-50 rounded border border-gray-200">
              <p className="text-lg font-semibold text-gray-900">
                {(smartConfig as any).gradient_accumulation_steps}
              </p>
              <p className="text-xs text-gray-600 mt-1">
                Effective batch size: {(smartConfig as any).effective_batch_size}
              </p>
            </div>
          </div>

          {/* Learning Rate */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <label className="text-sm font-medium text-gray-700">Learning Rate</label>
              <Tooltip configKey="learning_rate">
                <HelpCircle className="w-4 h-4 text-gray-400 cursor-help" />
              </Tooltip>
            </div>
            <div className="p-3 bg-gray-50 rounded border border-gray-200">
              <p className="text-lg font-semibold text-gray-900">{(smartConfig as any).learning_rate}</p>
              <p className="text-xs text-gray-600 mt-1">
                {(smartConfig as any).explanations?.learning_rate || "Scaled for batch size"}
              </p>
            </div>
          </div>

          {/* Precision */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <label className="text-sm font-medium text-gray-700">Precision</label>
              <Tooltip configKey="precision">
                <HelpCircle className="w-4 h-4 text-gray-400 cursor-help" />
              </Tooltip>
            </div>
            <div className="p-3 bg-gray-50 rounded border border-gray-200">
              <p className="text-lg font-semibold text-gray-900 uppercase">
                {(smartConfig as any).precision}
                {(smartConfig as any).quantization !== "none" && ` + ${(smartConfig as any).quantization}`}
              </p>
              <p className="text-xs text-gray-600 mt-1">
                {(smartConfig as any).explanations?.precision || "Optimized for your GPU"}
              </p>
            </div>
          </div>

          {/* Epochs */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <label className="text-sm font-medium text-gray-700">Training Epochs</label>
              <Tooltip configKey="epochs">
                <HelpCircle className="w-4 h-4 text-gray-400 cursor-help" />
              </Tooltip>
            </div>
            <div className="p-3 bg-gray-50 rounded border border-gray-200">
              <p className="text-lg font-semibold text-gray-900">{(smartConfig as any).num_epochs}</p>
              <p className="text-xs text-gray-600 mt-1">Total steps: {(smartConfig as any).max_steps}</p>
            </div>
          </div>

          {/* Memory Usage */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <label className="text-sm font-medium text-gray-700">Memory Usage</label>
              <Tooltip configKey="memory_usage">
                <HelpCircle className="w-4 h-4 text-gray-400 cursor-help" />
              </Tooltip>
            </div>
            <div className="p-3 bg-gray-50 rounded border border-gray-200">
              <p className="text-lg font-semibold text-gray-900">
                {((smartConfig as any).estimated_memory_mb / 1024).toFixed(1)} GB
              </p>
              <p className="text-xs text-gray-600 mt-1">
                {(smartConfig as any).memory_utilization_percent}% of available
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Advanced Settings (Collapsible) */}
      <div className="bg-white border border-gray-200 rounded-lg">
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="w-full p-6 flex items-center justify-between hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold text-gray-900">Advanced Settings</h3>
            <span className="text-sm text-gray-500">(Optional)</span>
          </div>
          {showAdvanced ? (
            <ChevronUp className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          )}
        </button>

        {showAdvanced && (
          <div className="px-6 pb-6 border-t border-gray-200">
            {/* PEFT Algorithm Selection */}
            <div className="mt-6 mb-8">
              <h4 className="text-md font-semibold text-gray-900 mb-4">
                PEFT Algorithm Configuration
              </h4>
              <PEFTConfiguration
                onConfigChange={(config) => {
                  setPeftConfig(config as unknown as Record<string, unknown>);
                  // Update wizard state with PEFT config
                  onConfigUpdate(
                    {
                      ...smartConfig,
                      peft: config as unknown as Record<string, unknown>,
                      quantization,
                      gradient_checkpointing: gradientCheckpointing,
                    },
                    estimates!
                  );
                }}
                initialConfig={{
                  algorithm: "lora",
                  r: wizardState.profile?.config.lora_r || 8,
                  lora_alpha: wizardState.profile?.config.lora_alpha || 16,
                  lora_dropout: wizardState.profile?.config.lora_dropout || 0.1,
                }}
              />
            </div>

            <div className="border-t border-gray-200 pt-6 mt-6">
              <h4 className="text-md font-semibold text-gray-900 mb-4">
                Other Training Parameters
              </h4>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
              {/* Scheduler */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <label className="text-sm font-medium text-gray-700">LR Scheduler</label>
                  <Tooltip configKey="scheduler">
                    <HelpCircle className="w-4 h-4 text-gray-400 cursor-help" />
                  </Tooltip>
                </div>
                <div className="p-3 bg-gray-50 rounded border border-gray-200">
                  <p className="text-lg font-semibold text-gray-900 capitalize">
                    {wizardState.profile?.config.scheduler}
                  </p>
                  <p className="text-xs text-gray-600 mt-1">Learning rate schedule</p>
                </div>
              </div>

              {/* Weight Decay */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <label className="text-sm font-medium text-gray-700">Weight Decay</label>
                  <Tooltip configKey="weight_decay">
                    <HelpCircle className="w-4 h-4 text-gray-400 cursor-help" />
                  </Tooltip>
                </div>
                <div className="p-3 bg-gray-50 rounded border border-gray-200">
                  <p className="text-lg font-semibold text-gray-900">
                    {wizardState.profile?.config.weight_decay}
                  </p>
                  <p className="text-xs text-gray-600 mt-1">L2 regularization</p>
                </div>
              </div>

              {/* Max Grad Norm */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <label className="text-sm font-medium text-gray-700">Max Gradient Norm</label>
                  <Tooltip configKey="max_grad_norm">
                    <HelpCircle className="w-4 h-4 text-gray-400 cursor-help" />
                  </Tooltip>
                </div>
                <div className="p-3 bg-gray-50 rounded border border-gray-200">
                  <p className="text-lg font-semibold text-gray-900">
                    {wizardState.profile?.config.max_grad_norm}
                  </p>
                  <p className="text-xs text-gray-600 mt-1">Gradient clipping</p>
                </div>
              </div>
            </div>

            <div className="mt-6 p-4 bg-blue-50 rounded border border-blue-200">
              <p className="text-sm text-blue-800">
                <Info className="w-4 h-4 inline mr-1" />
                These advanced settings are pre-configured based on your selected use case.
                Modifying them requires understanding of fine-tuning hyperparameters.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Ready to Launch */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-6">
        <h4 className="font-semibold text-green-900 mb-2">✓ Configuration Complete</h4>
        <p className="text-sm text-green-800">
          Your training is configured and ready to launch. Click &quot;Next&quot; to review
          everything before starting.
        </p>
      </div>
    </div>
  );
};

export default SmartConfigurationStep;
