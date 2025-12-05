/**
 * Deployment Metrics View
 *
 * Detailed view of deployment usage metrics and performance.
 * Shows request statistics, latency percentiles, and cost tracking.
 *
 * Requirements: 9.5
 */

import React, { useState, useEffect, useCallback } from "react";

interface UsageMetrics {
  deployment_id: string;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  avg_latency_ms: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
  total_input_tokens: number;
  total_output_tokens: number;
  estimated_cost: number;
  cost_per_request: number;
  period_start: string;
  period_end: string;
}

interface DeploymentMetricsViewProps {
  deploymentId: string;
  deploymentName: string;
  onClose: () => void;
}

export const DeploymentMetricsView: React.FC<DeploymentMetricsViewProps> = ({
  deploymentId,
  deploymentName,
  onClose,
}) => {
  const [metrics, setMetrics] = useState<UsageMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadMetrics = useCallback(async () => {
    try {
      const response = await fetch(`/api/deployments/${deploymentId}/metrics`);
      if (!response.ok) {
        throw new Error("Failed to load metrics");
      }
      const data = await response.json();
      setMetrics(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, [deploymentId]);

  useEffect(() => {
    loadMetrics();
    const interval = setInterval(loadMetrics, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [loadMetrics]);

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat().format(num);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(amount);
  };

  const calculateSuccessRate = () => {
    if (!metrics || metrics.total_requests === 0) return 0;
    return (metrics.successful_requests / metrics.total_requests) * 100;
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl p-8">
          <div className="text-center">Loading metrics...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl p-8 max-w-md">
          <div className="text-center">
            <div className="text-red-600 mb-4">Failed to load metrics</div>
            <p className="text-gray-600 mb-4">{error}</p>
            <button
              onClick={onClose}
              className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold">Usage Metrics</h2>
              <p className="text-gray-600 mt-1">{deploymentName}</p>
              {metrics && (
                <p className="text-sm text-gray-500 mt-1">
                  Period: {new Date(metrics.period_start).toLocaleString()} -{" "}
                  {new Date(metrics.period_end).toLocaleString()}
                </p>
              )}
            </div>
            <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {metrics && (
            <div className="space-y-6">
              {/* Request Statistics */}
              <div>
                <h3 className="text-lg font-semibold mb-4">Request Statistics</h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <div className="text-sm text-gray-600">Total Requests</div>
                    <div className="text-3xl font-bold mt-2">
                      {formatNumber(metrics.total_requests)}
                    </div>
                  </div>
                  <div className="p-4 bg-green-50 rounded-lg">
                    <div className="text-sm text-gray-600">Successful</div>
                    <div className="text-3xl font-bold mt-2 text-green-600">
                      {formatNumber(metrics.successful_requests)}
                    </div>
                  </div>
                  <div className="p-4 bg-red-50 rounded-lg">
                    <div className="text-sm text-gray-600">Failed</div>
                    <div className="text-3xl font-bold mt-2 text-red-600">
                      {formatNumber(metrics.failed_requests)}
                    </div>
                  </div>
                  <div className="p-4 bg-purple-50 rounded-lg">
                    <div className="text-sm text-gray-600">Success Rate</div>
                    <div className="text-3xl font-bold mt-2 text-purple-600">
                      {calculateSuccessRate().toFixed(1)}%
                    </div>
                  </div>
                </div>
              </div>

              {/* Latency Metrics */}
              <div>
                <h3 className="text-lg font-semibold mb-4">Latency Metrics</h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="text-sm text-gray-600">Average</div>
                    <div className="text-2xl font-bold mt-2">
                      {metrics.avg_latency_ms.toFixed(0)}ms
                    </div>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="text-sm text-gray-600">P50 (Median)</div>
                    <div className="text-2xl font-bold mt-2">
                      {metrics.p50_latency_ms.toFixed(0)}ms
                    </div>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="text-sm text-gray-600">P95</div>
                    <div className="text-2xl font-bold mt-2">
                      {metrics.p95_latency_ms.toFixed(0)}ms
                    </div>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="text-sm text-gray-600">P99</div>
                    <div className="text-2xl font-bold mt-2">
                      {metrics.p99_latency_ms.toFixed(0)}ms
                    </div>
                  </div>
                </div>

                {/* Latency visualization */}
                <div className="mt-4 p-4 bg-white border rounded-lg">
                  <div className="space-y-2">
                    <div className="flex items-center gap-4">
                      <span className="text-sm w-20">P50</span>
                      <div className="flex-1 bg-gray-200 rounded-full h-4">
                        <div
                          className="bg-blue-500 h-4 rounded-full"
                          style={{
                            width: `${(metrics.p50_latency_ms / metrics.p99_latency_ms) * 100}%`,
                          }}
                        />
                      </div>
                      <span className="text-sm w-16 text-right">
                        {metrics.p50_latency_ms.toFixed(0)}ms
                      </span>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-sm w-20">P95</span>
                      <div className="flex-1 bg-gray-200 rounded-full h-4">
                        <div
                          className="bg-yellow-500 h-4 rounded-full"
                          style={{
                            width: `${(metrics.p95_latency_ms / metrics.p99_latency_ms) * 100}%`,
                          }}
                        />
                      </div>
                      <span className="text-sm w-16 text-right">
                        {metrics.p95_latency_ms.toFixed(0)}ms
                      </span>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-sm w-20">P99</span>
                      <div className="flex-1 bg-gray-200 rounded-full h-4">
                        <div className="bg-red-500 h-4 rounded-full w-full" />
                      </div>
                      <span className="text-sm w-16 text-right">
                        {metrics.p99_latency_ms.toFixed(0)}ms
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Token Usage */}
              <div>
                <h3 className="text-lg font-semibold mb-4">Token Usage</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="text-sm text-gray-600">Input Tokens</div>
                    <div className="text-2xl font-bold mt-2">
                      {formatNumber(metrics.total_input_tokens)}
                    </div>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="text-sm text-gray-600">Output Tokens</div>
                    <div className="text-2xl font-bold mt-2">
                      {formatNumber(metrics.total_output_tokens)}
                    </div>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="text-sm text-gray-600">Total Tokens</div>
                    <div className="text-2xl font-bold mt-2">
                      {formatNumber(metrics.total_input_tokens + metrics.total_output_tokens)}
                    </div>
                  </div>
                </div>
              </div>

              {/* Cost Metrics */}
              <div>
                <h3 className="text-lg font-semibold mb-4">Cost Metrics</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-6 bg-gradient-to-br from-green-50 to-green-100 rounded-lg">
                    <div className="text-sm text-gray-600">Total Cost</div>
                    <div className="text-4xl font-bold mt-2 text-green-700">
                      {formatCurrency(metrics.estimated_cost)}
                    </div>
                  </div>
                  <div className="p-6 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg">
                    <div className="text-sm text-gray-600">Cost per Request</div>
                    <div className="text-4xl font-bold mt-2 text-blue-700">
                      {formatCurrency(metrics.cost_per_request)}
                    </div>
                  </div>
                </div>
              </div>

              {/* Summary */}
              <div className="p-6 bg-gray-50 rounded-lg">
                <h3 className="text-lg font-semibold mb-4">Summary</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Average tokens per request:</span>
                    <span className="font-semibold">
                      {metrics.total_requests > 0
                        ? formatNumber(
                            Math.round(
                              (metrics.total_input_tokens + metrics.total_output_tokens) /
                                metrics.total_requests
                            )
                          )
                        : 0}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Requests per minute (avg):</span>
                    <span className="font-semibold">
                      {(() => {
                        const start = new Date(metrics.period_start).getTime();
                        const end = new Date(metrics.period_end).getTime();
                        const minutes = (end - start) / (1000 * 60);
                        return minutes > 0 ? (metrics.total_requests / minutes).toFixed(2) : 0;
                      })()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Error rate:</span>
                    <span className="font-semibold">
                      {metrics.total_requests > 0
                        ? ((metrics.failed_requests / metrics.total_requests) * 100).toFixed(2)
                        : 0}
                      %
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t bg-gray-50">
          <div className="flex justify-between items-center">
            <button onClick={loadMetrics} className="px-4 py-2 text-blue-600 hover:text-blue-700">
              Refresh
            </button>
            <button
              onClick={onClose}
              className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
