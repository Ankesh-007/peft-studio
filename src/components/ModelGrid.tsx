import React from 'react';
import { ModelMetadata } from '../types/model';

interface ModelGridProps {
  models: ModelMetadata[];
  view: 'grid' | 'list';
  onModelClick: (model: ModelMetadata) => void;
  onAddToComparison: (model: ModelMetadata) => void;
  comparisonModels: ModelMetadata[];
}

const ModelGrid: React.FC<ModelGridProps> = ({
  models,
  view,
  onModelClick,
  onAddToComparison,
  comparisonModels,
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

  const isInComparison = (modelId: string) => {
    return comparisonModels.some((m) => m.model_id === modelId);
  };

  if (view === 'list') {
    return (
      <div className="space-y-2">
        {models.map((model) => (
          <div
            key={model.model_id}
            className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 
                     rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => onModelClick(model)}
          >
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {model.model_name}
                  </h3>
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    by {model.author}
                  </span>
                  {(model as Record<string, unknown>).registry && (
                    <span className="px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded text-xs">
                      {(model as Record<string, unknown>).registry as string}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-4 mt-2 text-sm text-gray-600 dark:text-gray-400">
                  <span className="flex items-center gap-1">
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                    {formatNumber(model.likes)}
                  </span>
                  <span className="flex items-center gap-1">
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                    {formatNumber(model.downloads)}
                  </span>
                  {model.parameters && (
                    <span>{formatNumber(model.parameters)} params</span>
                  )}
                  {model.size_mb && <span>{formatSize(model.size_mb)}</span>}
                  {model.license && (
                    <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs">
                      {model.license}
                    </span>
                  )}
                </div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onAddToComparison(model);
                }}
                disabled={isInComparison(model.model_id) || comparisonModels.length >= 4}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isInComparison(model.model_id)
                    ? 'bg-gray-200 dark:bg-gray-700 text-gray-500 cursor-not-allowed'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                {isInComparison(model.model_id) ? 'In Comparison' : 'Compare'}
              </button>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {models.map((model) => (
        <div
          key={model.model_id}
          className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 
                   rounded-lg p-4 hover:shadow-lg transition-shadow cursor-pointer"
          onClick={() => onModelClick(model)}
        >
          <div className="flex items-start justify-between mb-2">
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white line-clamp-1">
                {model.model_name}
              </h3>
              {(model as Record<string, unknown>).registry && (
                <span className="inline-block mt-1 px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded text-xs">
                  {(model as Record<string, unknown>).registry as string}
                </span>
              )}
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onAddToComparison(model);
              }}
              disabled={isInComparison(model.model_id) || comparisonModels.length >= 4}
              className={`p-1 rounded ${
                isInComparison(model.model_id)
                  ? 'text-gray-400 cursor-not-allowed'
                  : 'text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20'
              }`}
              title={isInComparison(model.model_id) ? 'In comparison' : 'Add to comparison'}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </button>
          </div>

          <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">by {model.author}</p>

          <div className="space-y-2 mb-3">
            {model.parameters && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">Parameters:</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {formatNumber(model.parameters)}
                </span>
              </div>
            )}
            {model.size_mb && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">Size:</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {formatSize(model.size_mb)}
                </span>
              </div>
            )}
            {model.architecture && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">Architecture:</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {model.architecture}
                </span>
              </div>
            )}
          </div>

          <div className="flex items-center justify-between pt-3 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
              <span className="flex items-center gap-1">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
                {formatNumber(model.likes)}
              </span>
              <span className="flex items-center gap-1">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
                {formatNumber(model.downloads)}
              </span>
            </div>
            {model.license && (
              <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs text-gray-700 dark:text-gray-300">
                {model.license}
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default ModelGrid;
