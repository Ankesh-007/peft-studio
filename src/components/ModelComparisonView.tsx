import React from 'react';
import { ModelMetadata } from '../types/model';

interface ModelComparisonViewProps {
  models: ModelMetadata[];
  onClose: () => void;
  onRemoveModel: (modelId: string) => void;
  onClearAll: () => void;
}

const ModelComparisonView: React.FC<ModelComparisonViewProps> = ({
  models,
  onClose,
  onRemoveModel,
  onClearAll,
}) => {
  const formatNumber = (num: number | null): string => {
    if (!num) return 'N/A';
    if (num >= 1_000_000_000) return `${(num / 1_000_000_000).toFixed(1)}B`;
    if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
    if (num >= 1_000) return `${(num / 1_000).toFixed(1)}K`;
    return num.toString();
  };

  const formatSize = (sizeMb: number | null): string => {
    if (!sizeMb) return 'N/A';
    if (sizeMb >= 1024) return `${(sizeMb / 1024).toFixed(1)} GB`;
    return `${sizeMb.toFixed(0)} MB`;
  };

  const comparisonMetrics = [
    { key: 'downloads', label: 'Downloads', format: formatNumber },
    { key: 'likes', label: 'Likes', format: formatNumber },
    { key: 'parameters', label: 'Parameters', format: formatNumber },
    { key: 'size_mb', label: 'Size', format: formatSize },
    { key: 'architecture', label: 'Architecture', format: (v: unknown) => v || 'N/A' },
    { key: 'license', label: 'License', format: (v: unknown) => v || 'N/A' },
    { key: 'library_name', label: 'Library', format: (v: unknown) => v || 'N/A' },
  ];

  const getBestValue = (key: string): unknown => {
    const values = models.map((m) => (m as Record<string, unknown>)[key]).filter((v) => v != null);
    if (values.length === 0) return null;
    
    if (key === 'downloads' || key === 'likes') {
      return Math.max(...(values as number[]));
    }
    if (key === 'parameters') {
      // Smallest is often better for efficiency
      return Math.min(...(values as number[]));
    }
    if (key === 'size_mb') {
      return Math.min(...(values as number[]));
    }
    return null;
  };

  const isBestValue = (model: ModelMetadata, key: string): boolean => {
    const value = (model as Record<string, unknown>)[key];
    const bestValue = getBestValue(key);
    return value != null && bestValue != null && value === bestValue;
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-6xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-6 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Model Comparison
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Comparing {models.length} model{models.length !== 1 ? 's' : ''}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onClearAll}
              className="px-4 py-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 
                       rounded-lg transition-colors"
            >
              Clear All
            </button>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Comparison Table */}
        <div className="p-6 overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <th className="text-left p-4 font-semibold text-gray-900 dark:text-white">
                  Metric
                </th>
                {models.map((model) => (
                  <th key={model.model_id} className="p-4">
                    <div className="text-center">
                      <div className="font-semibold text-gray-900 dark:text-white mb-1">
                        {model.model_name}
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        by {model.author}
                      </div>
                      <button
                        onClick={() => onRemoveModel(model.model_id)}
                        className="mt-2 text-red-600 hover:text-red-700 text-sm"
                      >
                        Remove
                      </button>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {comparisonMetrics.map((metric) => (
                <tr
                  key={metric.key}
                  className="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50"
                >
                  <td className="p-4 font-medium text-gray-900 dark:text-white">
                    {metric.label}
                  </td>
                  {models.map((model) => {
                    const value = (model as Record<string, unknown>)[metric.key];
                    const isBest = isBestValue(model, metric.key);
                    return (
                      <td key={model.model_id} className="p-4 text-center">
                        <span
                          className={`inline-block px-3 py-1 rounded ${
                            isBest
                              ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 font-semibold'
                              : 'text-gray-900 dark:text-white'
                          }`}
                        >
                          {metric.format(value)}
                        </span>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Legend */}
        <div className="p-6 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-100 dark:bg-green-900/30 rounded"></div>
              <span>Best value</span>
            </div>
            <span className="mx-2">•</span>
            <span>For parameters and size, smaller is highlighted as more efficient</span>
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 p-6 flex items-center justify-end">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 
                     transition-colors font-medium"
          >
            Close Comparison
          </button>
        </div>
      </div>
    </div>
  );
};

export default ModelComparisonView;
