/**
 * Experiment Comparison View
 *
 * Component for comparing multiple experiments side-by-side with
 * metrics, hyperparameters, and performance analysis.
 *
 * Requirements: 6.3, 6.4, 17.1, 17.2, 17.3
 */

import React, { useState, useEffect, useCallback } from "react";
import { TrendingUp, TrendingDown, Award, X, Download } from "lucide-react";

interface ComparisonData {
  experiments: Array<{
    job_id: string;
    tracker: string;
    project: string;
    name: string;
    status: string;
    started_at: string;
    metadata: Record<string, unknown>;
  }>;
  metrics: Record<string, Record<string, number>>;
  hyperparameters: Record<string, Record<string, unknown>>;
  artifacts: Record<string, Array<Record<string, unknown>>>;
  summary: Record<string, Record<string, unknown>>;
  statistics: {
    total_experiments: number;
    trackers_used: string[];
    status_counts: Record<string, number>;
    [key: string]: unknown;
  };
}

interface ExperimentComparisonViewProps {
  jobIds: string[];
  onClose?: () => void;
}

export const ExperimentComparisonView: React.FC<ExperimentComparisonViewProps> = ({
  jobIds,
  onClose,
}) => {
  const [comparisonData, setComparisonData] = useState<ComparisonData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>([]);
  const [viewMode, setViewMode] = useState<"metrics" | "hyperparameters" | "summary">("metrics");

  const loadComparisonData = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch("/api/experiments/compare", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          job_ids: jobIds,
          metrics: null, // Get all metrics
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to load comparison data");
      }

      const data = await response.json();
      setComparisonData(data.comparison);

      // Auto-select common metrics
      if (data.comparison.metrics) {
        const allMetrics = new Set<string>();
        Object.values(data.comparison.metrics).forEach((metrics: any) => {
          Object.keys(metrics).forEach((metric) => allMetrics.add(metric));
        });
        setSelectedMetrics(Array.from(allMetrics).slice(0, 5)); // Show first 5 metrics
      }

      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load comparison");
    } finally {
      setLoading(false);
    }
  }, [jobIds]);

  useEffect(() => {
    loadComparisonData();
  }, [loadComparisonData]);

  const getBestPerformer = (metricName: string): string | null => {
    if (!comparisonData?.metrics) return null;

    const values: Record<string, number> = {};
    Object.entries(comparisonData.metrics).forEach(([jobId, metrics]) => {
      if (metricName in metrics) {
        values[jobId] = metrics[metricName];
      }
    });

    if (Object.keys(values).length === 0) return null;

    // For loss metrics, lower is better; for accuracy/score metrics, higher is better
    const isLossMetric =
      metricName.toLowerCase().includes("loss") || metricName.toLowerCase().includes("error");

    const bestJobId = isLossMetric
      ? Object.keys(values).reduce((a, b) => (values[a] < values[b] ? a : b))
      : Object.keys(values).reduce((a, b) => (values[a] > values[b] ? a : b));

    return bestJobId;
  };

  const getMetricDifference = (jobId: string, metricName: string, bestJobId: string): number => {
    if (!comparisonData?.metrics) return 0;

    const currentValue = comparisonData.metrics[jobId]?.[metricName];
    const bestValue = comparisonData.metrics[bestJobId]?.[metricName];

    if (currentValue === undefined || bestValue === undefined) return 0;

    return ((currentValue - bestValue) / bestValue) * 100;
  };

  const exportComparison = () => {
    if (!comparisonData) return;

    const exportData = {
      comparison_date: new Date().toISOString(),
      experiments: comparisonData.experiments,
      metrics: comparisonData.metrics,
      hyperparameters: comparisonData.hyperparameters,
      statistics: comparisonData.statistics,
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `experiment-comparison-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading comparison data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error}</p>
      </div>
    );
  }

  if (!comparisonData) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Experiment Comparison</h2>
          <p className="text-gray-600 mt-1">
            Comparing {comparisonData.experiments.length} experiments
          </p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={exportComparison}
            className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            Export
          </button>

          {onClose && (
            <button
              onClick={onClose}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>

      {/* View Mode Tabs */}
      <div className="flex gap-2 border-b border-gray-200">
        <button
          onClick={() => setViewMode("metrics")}
          className={`px-4 py-2 font-medium transition-colors ${viewMode === "metrics"
            ? "text-blue-600 border-b-2 border-blue-600"
            : "text-gray-600 hover:text-gray-900"
            }`}
        >
          Metrics
        </button>
        <button
          onClick={() => setViewMode("hyperparameters")}
          className={`px-4 py-2 font-medium transition-colors ${viewMode === "hyperparameters"
            ? "text-blue-600 border-b-2 border-blue-600"
            : "text-gray-600 hover:text-gray-900"
            }`}
        >
          Hyperparameters
        </button>
        <button
          onClick={() => setViewMode("summary")}
          className={`px-4 py-2 font-medium transition-colors ${viewMode === "summary"
            ? "text-blue-600 border-b-2 border-blue-600"
            : "text-gray-600 hover:text-gray-900"
            }`}
        >
          Summary
        </button>
      </div>

      {/* Statistics Overview */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm text-gray-600">Total Experiments</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">
            {comparisonData.statistics.total_experiments}
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm text-gray-600">Trackers Used</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">
            {comparisonData.statistics.trackers_used.length}
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm text-gray-600">Completed</div>
          <div className="text-2xl font-bold text-green-600 mt-1">
            {comparisonData.statistics.status_counts.completed || 0}
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm text-gray-600">Running</div>
          <div className="text-2xl font-bold text-blue-600 mt-1">
            {comparisonData.statistics.status_counts.running || 0}
          </div>
        </div>
      </div>

      {/* Metrics View */}
      {viewMode === "metrics" && (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Metric
                  </th>
                  {comparisonData.experiments.map((exp) => (
                    <th
                      key={exp.job_id}
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      <div className="truncate max-w-xs" title={exp.name || exp.job_id}>
                        {exp.name || exp.job_id.slice(0, 8)}
                      </div>
                      <div className="text-xs text-gray-400 font-normal normal-case">
                        {exp.tracker}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {selectedMetrics.map((metricName) => {
                  const bestJobId = getBestPerformer(metricName);

                  return (
                    <tr key={metricName}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {metricName}
                      </td>
                      {comparisonData.experiments.map((exp) => {
                        const value = comparisonData.metrics[exp.job_id]?.[metricName];
                        const isBest = exp.job_id === bestJobId;
                        const diff = bestJobId
                          ? getMetricDifference(exp.job_id, metricName, bestJobId)
                          : 0;

                        return (
                          <td
                            key={exp.job_id}
                            className={`px-6 py-4 whitespace-nowrap text-sm ${isBest ? "bg-green-50" : ""
                              }`}
                          >
                            {value !== undefined ? (
                              <div>
                                <div className="flex items-center gap-2">
                                  <span
                                    className={
                                      isBest ? "font-bold text-green-700" : "text-gray-900"
                                    }
                                  >
                                    {typeof value === "number" ? value.toFixed(4) : value}
                                  </span>
                                  {isBest && <Award className="w-4 h-4 text-green-600" />}
                                </div>
                                {!isBest && diff !== 0 && (
                                  <div
                                    className={`text-xs flex items-center gap-1 ${diff > 0 ? "text-red-600" : "text-green-600"
                                      }`}
                                  >
                                    {diff > 0 ? (
                                      <TrendingUp className="w-3 h-3" />
                                    ) : (
                                      <TrendingDown className="w-3 h-3" />
                                    )}
                                    {Math.abs(diff).toFixed(1)}%
                                  </div>
                                )}
                              </div>
                            ) : (
                              <span className="text-gray-400">-</span>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Hyperparameters View */}
      {viewMode === "hyperparameters" && (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Parameter
                  </th>
                  {comparisonData.experiments.map((exp) => (
                    <th
                      key={exp.job_id}
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      <div className="truncate max-w-xs" title={exp.name || exp.job_id}>
                        {exp.name || exp.job_id.slice(0, 8)}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {Object.keys(
                  comparisonData.hyperparameters[comparisonData.experiments[0]?.job_id] || {}
                ).map((paramName) => (
                  <tr key={paramName}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {paramName}
                    </td>
                    {comparisonData.experiments.map((exp) => {
                      const value = comparisonData.hyperparameters[exp.job_id]?.[paramName];

                      return (
                        <td
                          key={exp.job_id}
                          className="px-6 py-4 whitespace-nowrap text-sm text-gray-900"
                        >
                          {value !== undefined ? (
                            typeof value === "object" ? (
                              JSON.stringify(value)
                            ) : (
                              String(value)
                            )
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Summary View */}
      {viewMode === "summary" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {comparisonData.experiments.map((exp) => (
            <div key={exp.job_id} className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">{exp.name || exp.job_id}</h3>

              <div className="space-y-3">
                <div>
                  <div className="text-sm text-gray-600">Status</div>
                  <div className="text-base font-medium text-gray-900">{exp.status}</div>
                </div>

                <div>
                  <div className="text-base font-medium text-gray-900">{exp.tracker as React.ReactNode}</div>
                </div>

                <div>
                  <div className="text-sm text-gray-600">Model</div>
                  <div className="text-base font-medium text-gray-900">
                    {(exp.metadata as any).model_name}
                  </div>
                </div>

                <div>
                  <div className="text-sm text-gray-600">Algorithm</div>
                  <div className="text-base font-medium text-gray-900">
                    {(exp.metadata as any).algorithm}
                  </div>
                </div>

                {comparisonData.artifacts[exp.job_id] && (
                  <div>
                    <div className="text-sm text-gray-600">Artifacts</div>
                    <div className="text-base font-medium text-gray-900">
                      {comparisonData.artifacts[exp.job_id].length} artifact(s)
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ExperimentComparisonView;
