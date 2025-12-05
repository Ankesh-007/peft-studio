import React, { useState, useEffect } from "react";
import { AlertCircle, Info, CheckCircle, TrendingUp } from "lucide-react";

interface ParameterDefinition {
  name: string;
  display_name: string;
  description: string;
  type: string;
  default: unknown;
  min_value?: number;
  max_value?: number;
  recommended_range?: string;
}

interface AlgorithmInfo {
  id: string;
  name: string;
  description: string;
  long_description: string;
  recommended: boolean;
  use_cases: string[];
  requirements: string[];
  advantages: string[];
  disadvantages: string[];
  memory_efficiency: string;
  training_speed: string;
  parameters: ParameterDefinition[];
}

interface PEFTConfig {
  algorithm: string;
  r: number;
  lora_alpha: number;
  lora_dropout: number;
  target_modules: string[];
}

interface PEFTConfigurationProps {
  onConfigChange: (config: PEFTConfig) => void;
  initialConfig?: Partial<PEFTConfig>;
  disabled?: boolean;
}

const PEFTConfiguration: React.FC<PEFTConfigurationProps> = ({
  onConfigChange,
  initialConfig,
  disabled = false,
}) => {
  const [algorithms, setAlgorithms] = useState<AlgorithmInfo[]>([]);
  const [selectedAlgorithm, setSelectedAlgorithm] = useState<string>(
    initialConfig?.algorithm || "lora"
  );
  const [config, setConfig] = useState<PEFTConfig>({
    algorithm: initialConfig?.algorithm || "lora",
    r: initialConfig?.r || 8,
    lora_alpha: initialConfig?.lora_alpha || 16,
    lora_dropout: initialConfig?.lora_dropout || 0.1,
    target_modules: initialConfig?.target_modules || [
      "q_proj",
      "k_proj",
      "v_proj",
      "o_proj",
      "gate_proj",
      "up_proj",
      "down_proj",
    ],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  // Fetch algorithms from backend
  useEffect(() => {
    const fetchAlgorithms = async () => {
      try {
        setLoading(true);
        const response = await fetch("http://localhost:8000/api/peft/algorithms");
        if (!response.ok) {
          throw new Error("Failed to fetch PEFT algorithms");
        }
        const data = await response.json();
        setAlgorithms(data.algorithms);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
        console.error("Error fetching algorithms:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchAlgorithms();
  }, []);

  // Update parent when config changes
  useEffect(() => {
    onConfigChange(config);
  }, [config, onConfigChange]);

  const handleAlgorithmChange = (algorithmId: string) => {
    setSelectedAlgorithm(algorithmId);
    setConfig((prev) => ({ ...prev, algorithm: algorithmId }));
  };

  const handleParameterChange = (paramName: string, value: unknown) => {
    setConfig((prev) => ({ ...prev, [paramName]: value }));
  };

  const getEfficiencyBadge = (efficiency: string) => {
    const colors = {
      "very high": "bg-green-100 text-green-800",
      high: "bg-blue-100 text-blue-800",
      medium: "bg-yellow-100 text-yellow-800",
      low: "bg-red-100 text-red-800",
    };
    return colors[efficiency as keyof typeof colors] || colors.medium;
  };

  const getSpeedBadge = (speed: string) => {
    const colors = {
      fast: "bg-green-100 text-green-800",
      medium: "bg-yellow-100 text-yellow-800",
      slow: "bg-red-100 text-red-800",
    };
    return colors[speed as keyof typeof colors] || colors.medium;
  };

  const selectedAlgoInfo = algorithms.find((a) => a.id === selectedAlgorithm);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Loading PEFT algorithms...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-start">
          <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error Loading Algorithms</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Algorithm Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">PEFT Algorithm</label>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {algorithms.map((algo) => (
            <button
              key={algo.id}
              type="button"
              disabled={disabled}
              onClick={() => handleAlgorithmChange(algo.id)}
              className={`
                relative p-4 rounded-lg border-2 text-left transition-all
                ${
                  selectedAlgorithm === algo.id
                    ? "border-blue-500 bg-blue-50"
                    : "border-gray-200 bg-white hover:border-gray-300"
                }
                ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}
              `}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center">
                  <span className="font-semibold text-gray-900">{algo.name}</span>
                  {algo.recommended && (
                    <span className="ml-2 px-2 py-0.5 text-xs font-medium bg-green-100 text-green-800 rounded">
                      Recommended
                    </span>
                  )}
                </div>
                {selectedAlgorithm === algo.id && <CheckCircle className="h-5 w-5 text-blue-600" />}
              </div>
              <p className="text-sm text-gray-600 mb-3">{algo.description}</p>
              <div className="flex gap-2">
                <span
                  className={`px-2 py-1 text-xs rounded ${getEfficiencyBadge(algo.memory_efficiency)}`}
                >
                  {algo.memory_efficiency} memory
                </span>
                <span className={`px-2 py-1 text-xs rounded ${getSpeedBadge(algo.training_speed)}`}>
                  {algo.training_speed} speed
                </span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Algorithm Details */}
      {selectedAlgoInfo && (
        <div className="bg-gray-50 rounded-lg p-4 space-y-4">
          <div className="flex items-start justify-between">
            <h3 className="text-lg font-semibold text-gray-900">
              {selectedAlgoInfo.name} Configuration
            </h3>
            <button
              type="button"
              onClick={() => setShowDetails(!showDetails)}
              className="text-sm text-blue-600 hover:text-blue-700 flex items-center"
            >
              <Info className="h-4 w-4 mr-1" />
              {showDetails ? "Hide" : "Show"} Details
            </button>
          </div>

          {showDetails && (
            <div className="space-y-4 border-t border-gray-200 pt-4">
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Description</h4>
                <p className="text-sm text-gray-600">{selectedAlgoInfo.long_description}</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                    <CheckCircle className="h-4 w-4 mr-1 text-green-600" />
                    Advantages
                  </h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    {selectedAlgoInfo.advantages.map((adv, idx) => (
                      <li key={idx} className="flex items-start">
                        <span className="mr-2">•</span>
                        <span>{adv}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                    <AlertCircle className="h-4 w-4 mr-1 text-yellow-600" />
                    Considerations
                  </h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    {selectedAlgoInfo.disadvantages.map((dis, idx) => (
                      <li key={idx} className="flex items-start">
                        <span className="mr-2">•</span>
                        <span>{dis}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                  <TrendingUp className="h-4 w-4 mr-1 text-blue-600" />
                  Best Use Cases
                </h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  {selectedAlgoInfo.use_cases.map((useCase, idx) => (
                    <li key={idx} className="flex items-start">
                      <span className="mr-2">•</span>
                      <span>{useCase}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Parameters */}
      {selectedAlgoInfo && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">Parameters</h3>

          {selectedAlgoInfo.parameters.map((param) => (
            <div key={param.name} className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="block text-sm font-medium text-gray-700">
                  {param.display_name}
                </label>
                {param.recommended_range && (
                  <span className="text-xs text-gray-500">
                    Recommended: {param.recommended_range}
                  </span>
                )}
              </div>

              <div className="relative group">
                {param.type === "int" || param.type === "float" ? (
                  <input
                    type="number"
                    disabled={disabled}
                    value={config[param.name as keyof PEFTConfig] as number}
                    onChange={(e) =>
                      handleParameterChange(
                        param.name,
                        param.type === "int" ? parseInt(e.target.value) : parseFloat(e.target.value)
                      )
                    }
                    min={param.min_value}
                    max={param.max_value}
                    step={param.type === "float" ? 0.01 : 1}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                  />
                ) : param.type === "list" ? (
                  <input
                    type="text"
                    disabled={disabled}
                    value={(config[param.name as keyof PEFTConfig] as string[]).join(", ")}
                    onChange={(e) =>
                      handleParameterChange(
                        param.name,
                        e.target.value
                          .split(",")
                          .map((s) => s.trim())
                          .filter((s) => s)
                      )
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                  />
                ) : null}

                {/* Tooltip */}
                <div className="absolute left-0 bottom-full mb-2 hidden group-hover:block z-10 w-full max-w-xs">
                  <div className="bg-gray-900 text-white text-xs rounded-lg p-3 shadow-lg">
                    <p>{param.description}</p>
                    {param.min_value !== undefined && param.max_value !== undefined && (
                      <p className="mt-1 text-gray-300">
                        Range: {param.min_value} - {param.max_value}
                      </p>
                    )}
                  </div>
                </div>
              </div>

              <p className="text-xs text-gray-500">{param.description}</p>
            </div>
          ))}
        </div>
      )}

      {/* Validation Messages */}
      {config.r > 64 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
          <div className="flex items-start">
            <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
            <div className="ml-3">
              <p className="text-sm text-yellow-800">
                High rank value (r={config.r}) may increase training time and memory usage. Consider
                using a lower value (4-32) for most models.
              </p>
            </div>
          </div>
        </div>
      )}

      {config.lora_alpha !== config.r * 2 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <div className="flex items-start">
            <Info className="h-5 w-5 text-blue-600 mt-0.5" />
            <div className="ml-3">
              <p className="text-sm text-blue-800">
                LoRA Alpha is typically set to 2x the rank value. Current: {config.lora_alpha},
                Suggested: {config.r * 2}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PEFTConfiguration;
