/**
 * Compute Provider Selection UI
 * 
 * Comprehensive interface for selecting compute providers with:
 * - Provider comparison table
 * - Real-time pricing display
 * - Availability indicators
 * - Resource specification display
 * - Provider recommendation engine
 * 
 * Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5
 */

import React, { useState, useEffect } from 'react';

interface GPUInstance {
  platform: string;
  gpu_type: string;
  gpu_count: number;
  memory_gb: number;
  vcpus: number;
  ram_gb: number;
  storage_gb: number;
  hourly_rate_usd: number;
  availability: 'high' | 'medium' | 'low' | 'unavailable';
  region: string;
  instance_id?: string;
}

interface PlatformEstimate {
  platform: string;
  instance: GPUInstance;
  training_hours: number;
  total_cost_usd: number;
  setup_time_minutes: number;
  estimated_start_time: string;
  pros: string[];
  cons: string[];
}

interface CostComparison {
  local_estimate?: PlatformEstimate;
  cloud_estimates: PlatformEstimate[];
  cheapest_option: PlatformEstimate;
  fastest_option: PlatformEstimate;
  recommended_option: PlatformEstimate;
  savings_vs_local?: number;
}

interface ComputeProviderSelectorProps {
  trainingHours: number;
  minMemoryGb?: number;
  localGpuType?: string;
  localElectricityCost?: number;
  onProviderSelect: (platform: string, instance: GPUInstance) => void;
  onCancel?: () => void;
}

export const ComputeProviderSelector: React.FC<ComputeProviderSelectorProps> = ({
  trainingHours,
  minMemoryGb,
  localGpuType,
  localElectricityCost,
  onProviderSelect,
  onCancel
}) => {
  const [comparison, setComparison] = useState<CostComparison | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);
  const [selectedInstance, setSelectedInstance] = useState<GPUInstance | null>(null);
  const [viewMode, setViewMode] = useState<'table' | 'cards'>('table');
  const [sortBy, setSortBy] = useState<'cost' | 'performance' | 'availability'>('cost');
  const [refreshInterval, setRefreshInterval] = useState<number | null>(null);

  useEffect(() => {
    fetchComparison();

    // Set up auto-refresh every 30 seconds for real-time pricing
    const interval = setInterval(() => {
      fetchComparison();
    }, 30000);

    setRefreshInterval(interval as any);

    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  }, [trainingHours, minMemoryGb, localGpuType, localElectricityCost]);

  const fetchComparison = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/api/cloud/compare-costs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          training_hours: trainingHours,
          local_gpu_type: localGpuType,
          local_electricity_cost: localElectricityCost,
          min_memory_gb: minMemoryGb,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch cost comparison');
      }

      const data = await response.json();
      setComparison(data);

      // Auto-select recommended platform
      if (!selectedPlatform) {
        setSelectedPlatform(data.recommended_option.platform);
        setSelectedInstance(data.recommended_option.instance);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleProviderSelect = (platform: string, instance: GPUInstance) => {
    setSelectedPlatform(platform);
    setSelectedInstance(instance);
  };

  const handleConfirm = () => {
    if (selectedPlatform && selectedInstance) {
      onProviderSelect(selectedPlatform, selectedInstance);
    }
  };

  const getAvailabilityColor = (availability: string) => {
    switch (availability) {
      case 'high':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'low':
        return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'unavailable':
        return 'bg-red-100 text-red-800 border-red-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getAvailabilityIcon = (availability: string) => {
    switch (availability) {
      case 'high':
        return '🟢';
      case 'medium':
        return '🟡';
      case 'low':
        return '🟠';
      case 'unavailable':
        return '🔴';
      default:
        return '⚪';
    }
  };

  const getSortedEstimates = (estimates: PlatformEstimate[]) => {
    const sorted = [...estimates];

    switch (sortBy) {
      case 'cost':
        sorted.sort((a, b) => a.total_cost_usd - b.total_cost_usd);
        break;
      case 'performance':
        sorted.sort((a, b) => a.setup_time_minutes - b.setup_time_minutes);
        break;
      case 'availability': {
        const availabilityOrder = { high: 0, medium: 1, low: 2, unavailable: 3 };
        sorted.sort((a, b) =>
          availabilityOrder[a.instance.availability] - availabilityOrder[b.instance.availability]
        );
        break;
      }
    }

    return sorted;
  };

  if (loading && !comparison) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg">Comparing compute providers...</p>
          <p className="text-gray-500 text-sm mt-2">Fetching real-time pricing and availability</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-start">
          <span className="text-red-500 text-2xl mr-3">⚠️</span>
          <div className="flex-1">
            <h3 className="text-red-800 font-semibold mb-2">Error Loading Providers</h3>
            <p className="text-red-700 mb-4">{error}</p>
            <div className="flex gap-3">
              <button
                onClick={fetchComparison}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition"
              >
                Retry
              </button>
              {onCancel && (
                <button
                  onClick={onCancel}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition"
                >
                  Cancel
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!comparison) {
    return null;
  }

  const allEstimates = [
    ...(comparison.local_estimate ? [comparison.local_estimate] : []),
    ...comparison.cloud_estimates
  ];

  const sortedEstimates = getSortedEstimates(allEstimates);

  return (
    <div className="space-y-6">
      {/* Header with Controls */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Select Compute Provider</h2>
          <p className="text-gray-600 mt-1">
            Estimated training time: <span className="font-semibold">{trainingHours.toFixed(1)} hours</span>
            {minMemoryGb && <span className="ml-3">Minimum GPU memory: <span className="font-semibold">{minMemoryGb} GB</span></span>}
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* View Mode Toggle */}
          <div className="flex bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode('table')}
              className={`px-3 py-1 rounded ${viewMode === 'table'
                  ? 'bg-white shadow text-gray-900'
                  : 'text-gray-600 hover:text-gray-900'
                }`}
            >
              Table
            </button>
            <button
              onClick={() => setViewMode('cards')}
              className={`px-3 py-1 rounded ${viewMode === 'cards'
                  ? 'bg-white shadow text-gray-900'
                  : 'text-gray-600 hover:text-gray-900'
                }`}
            >
              Cards
            </button>
          </div>

          {/* Sort By */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="cost">Sort by Cost</option>
            <option value="performance">Sort by Speed</option>
            <option value="availability">Sort by Availability</option>
          </select>

          {/* Refresh Button */}
          <button
            onClick={fetchComparison}
            disabled={loading}
            className="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition disabled:opacity-50"
            title="Refresh pricing"
          >
            {loading ? '🔄' : '↻'} Refresh
          </button>
        </div>
      </div>

      {/* Recommendation Banner */}
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-4">
        <div className="flex items-start">
          <span className="text-3xl mr-3">⭐</span>
          <div className="flex-1">
            <h3 className="text-purple-900 font-semibold text-lg mb-1">Recommended Option</h3>
            <p className="text-purple-800 mb-2">
              <span className="font-bold capitalize">{comparison.recommended_option.platform.replace('_', ' ')}</span>
              {' '}- {comparison.recommended_option.instance.gpu_type}
              {' '}for <span className="font-bold">${comparison.recommended_option.total_cost_usd.toFixed(2)}</span>
            </p>
            <p className="text-purple-700 text-sm">
              {comparison.recommended_option.platform === comparison.cheapest_option.platform
                ? '💰 Lowest cost option'
                : comparison.recommended_option.platform === comparison.fastest_option.platform
                  ? '⚡ Fastest to start'
                  : '⚖️ Best balance of cost and convenience'}
            </p>
          </div>
        </div>
      </div>

      {/* Savings Banner */}
      {comparison.savings_vs_local && comparison.savings_vs_local > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <p className="text-green-800">
            💰 Save <strong>{comparison.savings_vs_local.toFixed(1)}%</strong> by using cloud instead of local training
          </p>
        </div>
      )}

      {/* Table View */}
      {viewMode === 'table' && (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Provider
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    GPU
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Specs
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Cost
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Availability
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Setup Time
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {sortedEstimates.map((estimate, index) => (
                  <tr
                    key={index}
                    className={`hover:bg-gray-50 transition cursor-pointer ${selectedPlatform === estimate.platform ? 'bg-blue-50' : ''
                      }`}
                    onClick={() => handleProviderSelect(estimate.platform, estimate.instance)}
                  >
                    <td className="px-4 py-4">
                      <div className="flex items-center">
                        {selectedPlatform === estimate.platform && (
                          <span className="text-blue-500 mr-2">✓</span>
                        )}
                        <div>
                          <div className="font-semibold text-gray-900 capitalize">
                            {estimate.platform.replace('_', ' ')}
                          </div>
                          <div className="text-xs text-gray-500">{estimate.instance.region}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <div className="font-medium text-gray-900">{estimate.instance.gpu_type}</div>
                      <div className="text-xs text-gray-500">{estimate.instance.memory_gb} GB VRAM</div>
                    </td>
                    <td className="px-4 py-4">
                      <div className="text-sm text-gray-700">
                        {estimate.instance.vcpus > 0 && <div>{estimate.instance.vcpus} vCPUs</div>}
                        {estimate.instance.ram_gb > 0 && <div>{estimate.instance.ram_gb} GB RAM</div>}
                        {estimate.instance.storage_gb > 0 && <div>{estimate.instance.storage_gb} GB Storage</div>}
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <div className="font-bold text-lg text-gray-900">
                        ${estimate.total_cost_usd.toFixed(2)}
                      </div>
                      <div className="text-xs text-gray-500">
                        ${estimate.instance.hourly_rate_usd.toFixed(2)}/hr
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getAvailabilityColor(estimate.instance.availability)
                        }`}>
                        {getAvailabilityIcon(estimate.instance.availability)}
                        <span className="ml-1 capitalize">{estimate.instance.availability}</span>
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <div className="text-sm text-gray-700">{estimate.estimated_start_time}</div>
                    </td>
                    <td className="px-4 py-4">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleProviderSelect(estimate.platform, estimate.instance);
                        }}
                        className={`px-3 py-1 rounded text-sm font-medium transition ${selectedPlatform === estimate.platform
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                          }`}
                      >
                        {selectedPlatform === estimate.platform ? 'Selected' : 'Select'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Cards View */}
      {viewMode === 'cards' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sortedEstimates.map((estimate, index) => (
            <div
              key={index}
              className={`border rounded-lg p-4 cursor-pointer transition-all ${selectedPlatform === estimate.platform
                  ? 'border-blue-500 bg-blue-50 shadow-lg ring-2 ring-blue-200'
                  : 'border-gray-200 hover:border-gray-300 hover:shadow-md'
                }`}
              onClick={() => handleProviderSelect(estimate.platform, estimate.instance)}
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h3 className="font-bold text-lg text-gray-900 capitalize">
                    {estimate.platform.replace('_', ' ')}
                  </h3>
                  <p className="text-sm text-gray-600">{estimate.instance.region}</p>
                </div>
                {selectedPlatform === estimate.platform && (
                  <span className="bg-blue-500 text-white px-2 py-1 rounded text-xs font-medium">
                    ✓ Selected
                  </span>
                )}
              </div>

              {/* GPU Info */}
              <div className="mb-3 pb-3 border-b border-gray-200">
                <div className="font-semibold text-gray-900">{estimate.instance.gpu_type}</div>
                <div className="text-sm text-gray-600 mt-1">
                  {estimate.instance.memory_gb} GB VRAM
                </div>
              </div>

              {/* Cost */}
              <div className="mb-3">
                <div className="text-3xl font-bold text-gray-900">
                  ${estimate.total_cost_usd.toFixed(2)}
                </div>
                <div className="text-sm text-gray-600">
                  ${estimate.instance.hourly_rate_usd.toFixed(2)}/hr × {trainingHours.toFixed(1)}h
                </div>
              </div>

              {/* Availability */}
              <div className="mb-3">
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getAvailabilityColor(estimate.instance.availability)
                  }`}>
                  {getAvailabilityIcon(estimate.instance.availability)}
                  <span className="ml-2 capitalize">{estimate.instance.availability} availability</span>
                </span>
              </div>

              {/* Setup Time */}
              <div className="mb-3 text-sm text-gray-700">
                <span className="font-medium">Setup:</span> {estimate.estimated_start_time}
              </div>

              {/* Specs */}
              <div className="mb-3 text-sm text-gray-700 space-y-1">
                {estimate.instance.vcpus > 0 && <div>• {estimate.instance.vcpus} vCPUs</div>}
                {estimate.instance.ram_gb > 0 && <div>• {estimate.instance.ram_gb} GB RAM</div>}
                {estimate.instance.storage_gb > 0 && <div>• {estimate.instance.storage_gb} GB Storage</div>}
              </div>

              {/* Pros/Cons */}
              <details className="text-sm">
                <summary className="cursor-pointer text-blue-600 hover:text-blue-700 font-medium">
                  View Details
                </summary>
                <div className="mt-2 space-y-2">
                  <div>
                    <div className="font-medium text-green-700 mb-1">Pros:</div>
                    <ul className="space-y-1">
                      {estimate.pros.slice(0, 3).map((pro, i) => (
                        <li key={i} className="text-gray-700 flex items-start">
                          <span className="text-green-500 mr-1">✓</span>
                          <span>{pro}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <div className="font-medium text-red-700 mb-1">Cons:</div>
                    <ul className="space-y-1">
                      {estimate.cons.slice(0, 3).map((con, i) => (
                        <li key={i} className="text-gray-700 flex items-start">
                          <span className="text-red-500 mr-1">✗</span>
                          <span>{con}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </details>
            </div>
          ))}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex justify-between items-center pt-6 border-t border-gray-200">
        <div className="text-sm text-gray-600">
          {loading && <span className="animate-pulse">Updating prices...</span>}
          {!loading && <span>Prices updated {new Date().toLocaleTimeString()}</span>}
        </div>

        <div className="flex gap-3">
          {onCancel && (
            <button
              onClick={onCancel}
              className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition font-medium"
            >
              Cancel
            </button>
          )}

          <button
            onClick={handleConfirm}
            disabled={!selectedPlatform || !selectedInstance}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Continue with {selectedPlatform ? selectedPlatform.replace('_', ' ') : 'Selected Provider'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ComputeProviderSelector;
