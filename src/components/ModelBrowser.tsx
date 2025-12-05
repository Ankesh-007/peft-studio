import React, { useState, useEffect, useCallback } from 'react';
import { apiClient } from '../api/client';
import { ModelMetadata, ModelSearchFilters } from '../types/model';
import ModelSearchBar from './ModelSearchBar';
import ModelFilters from './ModelFilters';
import ModelGrid from './ModelGrid';
import ModelDetailModal from './ModelDetailModal';
import ModelComparisonView from './ModelComparisonView';
import { Spinner } from './LoadingStates';

interface ModelBrowserProps {
  onModelSelect?: (model: ModelMetadata) => void;
}

const ModelBrowser: React.FC<ModelBrowserProps> = ({ onModelSelect }) => {
  const [models, setModels] = useState<ModelMetadata[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<ModelSearchFilters>({
    task: 'text-generation',
    sort: 'downloads',
  });
  const [selectedModel, setSelectedModel] = useState<ModelMetadata | null>(null);
  const [comparisonModels, setComparisonModels] = useState<ModelMetadata[]>([]);
  const [showComparison, setShowComparison] = useState(false);
  const [view, setView] = useState<'grid' | 'list'>('grid');
  const [showCacheManager, setShowCacheManager] = useState(false);
  const [cachedModels, setCachedModels] = useState<Array<{ id: string; name: string; [key: string]: unknown }>>([]);

  // Load popular models on mount
  useEffect(() => {
    loadPopularModels();
  }, []);

  const loadPopularModels = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.getPopularModels('text-generation', 20) as { models: ModelMetadata[] };
      setModels(response.models || []);
    } catch (err) {
      setError('Failed to load popular models. Please try again.');
      console.error('Error loading popular models:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = useCallback(async (searchFilters: ModelSearchFilters) => {
    setLoading(true);
    setError(null);
    setFilters(searchFilters);

    try {
      // Use multi-registry search for better coverage
      const registries = searchFilters.registries && searchFilters.registries.length > 0
        ? searchFilters.registries
        : ['huggingface']; // Default to HuggingFace if no registries selected
      
      const response = await apiClient.searchMultiRegistry(
        searchFilters.query || '',
        searchFilters.task,
        registries,
        20
      ) as { models: ModelMetadata[] };
      setModels(response.models || []);
    } catch (err) {
      setError('Failed to search models. Please try again.');
      console.error('Error searching models:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleModelClick = (model: ModelMetadata) => {
    setSelectedModel(model);
  };

  const handleModelSelect = (model: ModelMetadata) => {
    if (onModelSelect) {
      onModelSelect(model);
    }
    setSelectedModel(null);
  };

  const handleAddToComparison = (model: ModelMetadata) => {
    if (comparisonModels.length < 4 && !comparisonModels.find(m => m.model_id === model.model_id)) {
      setComparisonModels([...comparisonModels, model]);
    }
  };

  const handleRemoveFromComparison = (modelId: string) => {
    setComparisonModels(comparisonModels.filter(m => m.model_id !== modelId));
  };

  const handleClearComparison = () => {
    setComparisonModels([]);
    setShowComparison(false);
  };

  const loadCachedModels = async () => {
    try {
      const response = await apiClient.getCachedModels() as { cached_models: Array<{ id: string; name: string; [key: string]: unknown }> };
      setCachedModels(response.cached_models || []);
      setShowCacheManager(true);
    } catch (err) {
      console.error('Error loading cached models:', err);
    }
  };

  const handleClearCache = async () => {
    try {
      await apiClient.clearModelCache();
      setCachedModels([]);
      alert('Cache cleared successfully');
    } catch (err) {
      console.error('Error clearing cache:', err);
      alert('Failed to clear cache');
    }
  };

  const handleRemoveFromCache = async (modelId: string, registry: string) => {
    try {
      await apiClient.clearModelCache(modelId);
      setCachedModels(cachedModels.filter(c => !(c.model_id === modelId && c.registry === registry)));
    } catch (err) {
      console.error('Error removing from cache:', err);
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Model Browser
          </h1>
          <div className="flex items-center gap-2">
            {/* View Toggle */}
            <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
              <button
                onClick={() => setView('grid')}
                className={`px-3 py-1 rounded ${
                  view === 'grid'
                    ? 'bg-white dark:bg-gray-600 shadow'
                    : 'text-gray-600 dark:text-gray-400'
                }`}
              >
                Grid
              </button>
              <button
                onClick={() => setView('list')}
                className={`px-3 py-1 rounded ${
                  view === 'list'
                    ? 'bg-white dark:bg-gray-600 shadow'
                    : 'text-gray-600 dark:text-gray-400'
                }`}
              >
                List
              </button>
            </div>

            {/* Cache Manager Button */}
            <button
              onClick={loadCachedModels}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              title="View cached models"
            >
              <svg className="w-5 h-5 inline-block mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
              </svg>
              Cache
            </button>

            {/* Comparison Button */}
            {comparisonModels.length > 0 && (
              <button
                onClick={() => setShowComparison(!showComparison)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Compare ({comparisonModels.length})
              </button>
            )}
          </div>
        </div>

        {/* Search Bar */}
        <ModelSearchBar onSearch={handleSearch} initialFilters={filters} />
      </div>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Filters Sidebar */}
        <div className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 overflow-y-auto">
          <ModelFilters
            filters={filters}
            onFiltersChange={handleSearch}
          />
        </div>

        {/* Models Display */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading && (
            <div className="flex flex-col items-center justify-center h-64 gap-4">
              <Spinner size="lg" />
              <p className="text-dark-text-secondary">Loading models...</p>
            </div>
          )}

          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-red-900 dark:text-red-100 mb-2">
                Error Loading Models
              </h3>
              <p className="text-red-700 dark:text-red-300 mb-4">{error}</p>
              <button
                onClick={loadPopularModels}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Retry
              </button>
            </div>
          )}

          {!loading && !error && models.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-500 dark:text-gray-400 text-lg">
                No models found. Try adjusting your search filters.
              </p>
            </div>
          )}

          {!loading && !error && models.length > 0 && (
            <>
              <div className="mb-4 text-sm text-gray-600 dark:text-gray-400">
                Found {models.length} models
              </div>
              <ModelGrid
                models={models}
                view={view}
                onModelClick={handleModelClick}
                onAddToComparison={handleAddToComparison}
                comparisonModels={comparisonModels}
              />
            </>
          )}
        </div>
      </div>

      {/* Model Detail Modal */}
      {selectedModel && (
        <ModelDetailModal
          model={selectedModel}
          onClose={() => setSelectedModel(null)}
          onSelect={handleModelSelect}
          onAddToComparison={handleAddToComparison}
          isInComparison={comparisonModels.some(m => m.model_id === selectedModel.model_id)}
        />
      )}

      {/* Comparison View */}
      {showComparison && comparisonModels.length > 0 && (
        <ModelComparisonView
          models={comparisonModels}
          onClose={() => setShowComparison(false)}
          onRemoveModel={handleRemoveFromComparison}
          onClearAll={handleClearComparison}
        />
      )}

      {/* Cache Manager Modal */}
      {showCacheManager && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-6 flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                  Cached Models
                </h2>
                <p className="text-gray-600 dark:text-gray-400 mt-1">
                  {cachedModels.length} model{cachedModels.length !== 1 ? 's' : ''} cached
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleClearCache}
                  className="px-4 py-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                >
                  Clear All
                </button>
                <button
                  onClick={() => setShowCacheManager(false)}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            <div className="p-6">
              {cachedModels.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-gray-500 dark:text-gray-400">No cached models</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {cachedModels.map((cached) => (
                    <div
                      key={`${cached.registry}:${cached.model_id}`}
                      className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 flex items-center justify-between"
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-gray-900 dark:text-white">
                            {cached.metadata.model_name}
                          </h3>
                          <span className="px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded text-xs">
                            {cached.registry}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          by {cached.metadata.author}
                        </p>
                        <div className="flex items-center gap-4 mt-2 text-xs text-gray-500 dark:text-gray-400">
                          <span>Cached: {new Date(cached.cached_at).toLocaleString()}</span>
                          <span>Expires: {new Date(cached.expires_at).toLocaleString()}</span>
                        </div>
                      </div>
                      <button
                        onClick={() => handleRemoveFromCache(cached.model_id, cached.registry)}
                        className="px-3 py-1 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors text-sm"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ModelBrowser;
