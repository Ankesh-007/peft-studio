/**
 * Cloud Platform Cost Comparison Component
 *
 * Displays cost comparison across cloud GPU platforms
 * Validates: Requirements 9.2
 */

import React, { useState, useEffect } from "react";

interface CloudInstance {
  platform: string;
  gpu: string;
  cost: string;
  hourly_rate?: string;
  setup_time: string;
  availability?: string;
  pros: string[];
  cons: string[];
}

interface CostComparison {
  summary: {
    cheapest: {
      platform: string;
      cost: string;
      gpu: string;
    };
    fastest: {
      platform: string;
      setup_time: string;
      gpu: string;
    };
    recommended: {
      platform: string;
      cost: string;
      gpu: string;
      reason: string;
    };
    savings_vs_local?: string;
  };
  options: CloudInstance[];
}

interface CloudPlatformComparisonProps {
  trainingHours: number;
  localGpuType?: string;
  localElectricityCost?: number;
  minMemoryGb?: number;
  onPlatformSelect?: (platform: string) => void;
}

export const CloudPlatformComparison: React.FC<
  CloudPlatformComparisonProps
> = ({
  trainingHours,
  localGpuType,
  localElectricityCost,
  minMemoryGb,
  onPlatformSelect,
}) => {
  const [comparison, setComparison] = useState<CostComparison | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);

  useEffect(() => {
    fetchComparison();
  }, [trainingHours, localGpuType, localElectricityCost, minMemoryGb]);

  const fetchComparison = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        "http://localhost:8000/api/cloud/compare-costs",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            training_hours: trainingHours,
            local_gpu_type: localGpuType,
            local_electricity_cost: localElectricityCost,
            min_memory_gb: minMemoryGb,
          }),
        },
      );

      if (!response.ok) {
        throw new Error("Failed to fetch cost comparison");
      }

      const data = await response.json();
      setComparison(data);

      // Auto-select recommended platform
      setSelectedPlatform(data.summary.recommended.platform);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const handlePlatformSelect = (platform: string) => {
    setSelectedPlatform(platform);
    if (onPlatformSelect) {
      onPlatformSelect(platform);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        <span className="ml-4 text-gray-600">Comparing cloud platforms...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error: {error}</p>
        <button
          onClick={fetchComparison}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!comparison) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Cheapest Option */}
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-green-800">Cheapest</h3>
            <span className="text-xs bg-green-200 text-green-800 px-2 py-1 rounded">
              Best Value
            </span>
          </div>
          <p className="text-2xl font-bold text-green-900">
            {comparison.summary.cheapest.cost}
          </p>
          <p className="text-sm text-green-700 mt-1">
            {comparison.summary.cheapest.platform}
          </p>
          <p className="text-xs text-green-600 mt-1">
            {comparison.summary.cheapest.gpu}
          </p>
        </div>

        {/* Fastest Option */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-blue-800">Fastest</h3>
            <span className="text-xs bg-blue-200 text-blue-800 px-2 py-1 rounded">
              Quick Start
            </span>
          </div>
          <p className="text-2xl font-bold text-blue-900">
            {comparison.summary.fastest.setup_time}
          </p>
          <p className="text-sm text-blue-700 mt-1">
            {comparison.summary.fastest.platform}
          </p>
          <p className="text-xs text-blue-600 mt-1">
            {comparison.summary.fastest.gpu}
          </p>
        </div>

        {/* Recommended Option */}
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-purple-800">Recommended</h3>
            <span className="text-xs bg-purple-200 text-purple-800 px-2 py-1 rounded">
              ⭐ Best Choice
            </span>
          </div>
          <p className="text-2xl font-bold text-purple-900">
            {comparison.summary.recommended.cost}
          </p>
          <p className="text-sm text-purple-700 mt-1">
            {comparison.summary.recommended.platform}
          </p>
          <p className="text-xs text-purple-600 mt-1">
            {comparison.summary.recommended.reason}
          </p>
        </div>
      </div>

      {/* Savings Banner */}
      {comparison.summary.savings_vs_local && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-yellow-800">
            💰 Save <strong>{comparison.summary.savings_vs_local}</strong> by
            using cloud instead of local training
          </p>
        </div>
      )}

      {/* All Options */}
      <div>
        <h3 className="text-lg font-semibold mb-4">All Available Options</h3>
        <div className="space-y-4">
          {comparison.options.map((option, index) => (
            <div
              key={index}
              className={`border rounded-lg p-4 cursor-pointer transition-all ${
                selectedPlatform === option.platform
                  ? "border-blue-500 bg-blue-50 shadow-md"
                  : "border-gray-200 hover:border-gray-300 hover:shadow"
              }`}
              onClick={() => handlePlatformSelect(option.platform)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h4 className="text-lg font-semibold capitalize">
                      {option.platform.replace("_", " ")}
                    </h4>
                    <span className="text-sm text-gray-600">{option.gpu}</span>
                    {selectedPlatform === option.platform && (
                      <span className="text-xs bg-blue-500 text-white px-2 py-1 rounded">
                        Selected
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-4 mb-3">
                    <div>
                      <span className="text-2xl font-bold text-gray-900">
                        {option.cost}
                      </span>
                      {option.hourly_rate && (
                        <span className="text-sm text-gray-600 ml-2">
                          ({option.hourly_rate})
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-gray-600">
                      Setup: {option.setup_time}
                    </div>
                    {option.availability && (
                      <div className="text-sm">
                        <span
                          className={`px-2 py-1 rounded ${
                            option.availability === "high"
                              ? "bg-green-100 text-green-800"
                              : option.availability === "medium"
                                ? "bg-yellow-100 text-yellow-800"
                                : "bg-red-100 text-red-800"
                          }`}
                        >
                          {option.availability} availability
                        </span>
                      </div>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Pros */}
                    <div>
                      <h5 className="text-sm font-medium text-green-700 mb-2">
                        Pros
                      </h5>
                      <ul className="space-y-1">
                        {option.pros.map((pro, i) => (
                          <li
                            key={i}
                            className="text-sm text-gray-700 flex items-start"
                          >
                            <span className="text-green-500 mr-2">✓</span>
                            <span>{pro}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Cons */}
                    <div>
                      <h5 className="text-sm font-medium text-red-700 mb-2">
                        Cons
                      </h5>
                      <ul className="space-y-1">
                        {option.cons.map((con, i) => (
                          <li
                            key={i}
                            className="text-sm text-gray-700 flex items-start"
                          >
                            <span className="text-red-500 mr-2">✗</span>
                            <span>{con}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-between items-center pt-4 border-t">
        <button
          onClick={fetchComparison}
          className="px-4 py-2 text-gray-700 border border-gray-300 rounded hover:bg-gray-50"
        >
          Refresh Prices
        </button>

        {selectedPlatform && (
          <button
            onClick={() => {
              // Handle platform selection
              console.log("Selected platform:", selectedPlatform);
            }}
            className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 font-medium"
          >
            Continue with {selectedPlatform.replace("_", " ")}
          </button>
        )}
      </div>
    </div>
  );
};

export default CloudPlatformComparison;
