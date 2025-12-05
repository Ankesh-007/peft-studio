import { Search, Loader2, AlertCircle, Download, Star, Tag, ExternalLink } from "lucide-react";
import React, { useState, useEffect } from "react";

import Tooltip from "../Tooltip";

import type { ModelInfo, WizardState } from "../../types/wizard";

interface ModelSelectionStepProps {
  wizardState: WizardState;
  onModelSelect: (model: ModelInfo) => void;
}

/**
 * Step 3: Model Selection with HuggingFace browser
 * Allows users to search, filter, and select models with compatibility warnings
 */
const ModelSelectionStep: React.FC<ModelSelectionStepProps> = ({ wizardState, onModelSelect }) => {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedFilter, setSelectedFilter] = useState<"all" | "small" | "medium" | "large">("all");

  useEffect(() => {
    loadPopularModels();
  }, []);

  const loadPopularModels = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(
        "http://127.0.0.1:8000/api/models/popular/text-generation?limit=20"
      );
      const data = await response.json();
      setModels(data.models);
    } catch (err) {
      setError("Failed to load models. Please ensure the backend is running.");
      console.error("Error loading models:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      loadPopularModels();
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const response = await fetch("http://127.0.0.1:8000/api/models/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: searchQuery,
          task: "text-generation",
          limit: 20,
        }),
      });
      const data = await response.json();
      setModels(data.models);
    } catch (err) {
      setError("Search failed. Please try again.");
      console.error("Error searching models:", err);
    } finally {
      setLoading(false);
    }
  };

  const getModelSizeCategory = (parameters: number): "small" | "medium" | "large" => {
    if (parameters < 3000) return "small";
    if (parameters < 13000) return "medium";
    return "large";
  };

  const getCompatibilityWarning = (model: ModelInfo): string | null => {
    if (!wizardState.profile) return null;

    const modelSizeGB = model.size_mb / 1024;
    const minGPUMemory = wizardState.profile.requirements.min_gpu_memory_gb;

    // Rough estimate: model needs ~4x its size in memory for training
    const estimatedMemoryNeeded = modelSizeGB * 4;

    if (estimatedMemoryNeeded > minGPUMemory) {
      return `This model may require more GPU memory than available. Consider using quantization (8-bit or 4-bit).`;
    }

    if (model.parameters > 13000) {
      return `Large models (${(model.parameters / 1000).toFixed(1)}B parameters) require significant resources and longer training times.`;
    }

    return null;
  };

  const filteredModels = models.filter((model) => {
    if (selectedFilter === "all") return true;
    return getModelSizeCategory(model.parameters) === selectedFilter;
  });

  return (
    <div className="space-y-6">
      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-blue-900 mb-2">Select Your Base Model</h2>
        <p className="text-blue-800 mb-3">
          Choose a pre-trained model from HuggingFace to fine-tune. We&apos;ll show you popular
          models and help you find the right one for your use case.
        </p>
        <div className="flex items-center gap-2">
          <Tooltip configKey="model_selection">
            <span className="text-sm text-blue-700 underline cursor-help">
              How do I choose a model?
            </span>
          </Tooltip>
        </div>
      </div>

      {/* Search Bar */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && handleSearch()}
              placeholder="Search models (e.g., 'llama', 'mistral', 'phi')..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={loading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Searching...
              </>
            ) : (
              "Search"
            )}
          </button>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3 mt-4">
          <span className="text-sm font-medium text-gray-700">Filter by size:</span>
          <div className="flex gap-2">
            {[
              { value: "all", label: "All Models" },
              { value: "small", label: "Small (<3B)" },
              { value: "medium", label: "Medium (3-13B)" },
              { value: "large", label: "Large (>13B)" },
            ].map((filter) => (
              <button
                key={filter.value}
                onClick={() =>
                  setSelectedFilter(filter.value as "all" | "small" | "medium" | "large")
                }
                className={`px-4 py-1.5 text-sm rounded-lg border transition-colors ${
                  selectedFilter === filter.value
                    ? "bg-blue-600 text-white border-blue-600"
                    : "bg-white text-gray-700 border-gray-300 hover:border-blue-300"
                }`}
              >
                {filter.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-red-800 font-medium">{error}</p>
            <button
              onClick={loadPopularModels}
              className="text-sm text-red-700 underline mt-1 hover:text-red-900"
            >
              Try loading popular models
            </button>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          <span className="ml-3 text-gray-600">Loading models...</span>
        </div>
      )}

      {/* Models Grid */}
      {!loading && filteredModels.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredModels.map((model) => {
            const warning = getCompatibilityWarning(model);
            const isSelected = wizardState.model?.model_id === model.model_id;

            return (
              <button
                key={model.model_id}
                onClick={() => onModelSelect(model)}
                className={`text-left p-5 rounded-lg border-2 transition-all hover:shadow-lg ${
                  isSelected
                    ? "border-blue-600 bg-blue-50 shadow-md"
                    : "border-gray-200 bg-white hover:border-blue-300"
                }`}
                data-testid={`model-card-${model.model_id}`}
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 mb-1">{model.model_name}</h3>
                    <p className="text-sm text-gray-600">{model.author}</p>
                  </div>
                  {isSelected && (
                    <span className="px-2 py-1 text-xs bg-blue-600 text-white rounded font-medium">
                      Selected
                    </span>
                  )}
                </div>

                {/* Stats */}
                <div className="flex items-center gap-4 mb-3 text-sm text-gray-600">
                  <div className="flex items-center gap-1">
                    <Download className="w-4 h-4" />
                    <span>{(model.downloads / 1000).toFixed(1)}K</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Star className="w-4 h-4" />
                    <span>{model.likes}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Tag className="w-4 h-4" />
                    <span>{(model.parameters / 1000).toFixed(1)}B params</span>
                  </div>
                </div>

                {/* Architecture & Size */}
                <div className="flex items-center gap-3 mb-3 text-sm">
                  <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded">
                    {model.architecture}
                  </span>
                  <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded">
                    {(model.size_mb / 1024).toFixed(1)} GB
                  </span>
                  {model.license && (
                    <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">
                      {model.license}
                    </span>
                  )}
                </div>

                {/* Compatibility Warning */}
                {warning && (
                  <div className="flex items-start gap-2 p-3 bg-yellow-50 border border-yellow-200 rounded mt-3">
                    <AlertCircle className="w-4 h-4 text-yellow-600 flex-shrink-0 mt-0.5" />
                    <p className="text-sm text-yellow-800">{warning}</p>
                  </div>
                )}

                {/* View on HuggingFace */}
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <a
                    href={`https://huggingface.co/${model.model_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
                  >
                    View on HuggingFace
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </button>
            );
          })}
        </div>
      )}

      {/* No Results */}
      {!loading && filteredModels.length === 0 && models.length > 0 && (
        <div className="text-center py-12">
          <p className="text-gray-600 mb-4">No models found matching your filters.</p>
          <button
            onClick={() => setSelectedFilter("all")}
            className="text-blue-600 hover:text-blue-700 underline"
          >
            Clear filters
          </button>
        </div>
      )}

      {/* Selected Model Summary */}
      {wizardState.model && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <h4 className="font-semibold text-green-900 mb-2">
            ✓ {wizardState.model.model_name} Selected
          </h4>
          <p className="text-sm text-green-800 mb-3">
            This model will be fine-tuned using your {wizardState.profile?.name} configuration.
            Click &quot;Next&quot; to review the smart configuration.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-green-700 font-medium">Parameters:</span>
              <span className="ml-2 text-green-900">
                {(wizardState.model.parameters / 1000).toFixed(1)}B
              </span>
            </div>
            <div>
              <span className="text-green-700 font-medium">Size:</span>
              <span className="ml-2 text-green-900">
                {(wizardState.model.size_mb / 1024).toFixed(1)} GB
              </span>
            </div>
            <div>
              <span className="text-green-700 font-medium">Architecture:</span>
              <span className="ml-2 text-green-900">{wizardState.model.architecture}</span>
            </div>
            <div>
              <span className="text-green-700 font-medium">Downloads:</span>
              <span className="ml-2 text-green-900">
                {(wizardState.model.downloads / 1000).toFixed(1)}K
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ModelSelectionStep;
