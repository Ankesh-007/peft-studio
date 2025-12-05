import React, { useState } from 'react';
import { ModelSearchFilters } from '../types/model';

interface ModelFiltersProps {
  filters: ModelSearchFilters;
  onFiltersChange: (filters: ModelSearchFilters) => void;
}

const ModelFilters: React.FC<ModelFiltersProps> = ({ filters, onFiltersChange }) => {
  const [localFilters, setLocalFilters] = useState<ModelSearchFilters>(filters);

  const handleFilterChange = (key: keyof ModelSearchFilters, value: unknown) => {
    const newFilters = { ...localFilters, [key]: value };
    setLocalFilters(newFilters);
    onFiltersChange(newFilters);
  };

  const handleParameterRangeChange = (min?: number, max?: number) => {
    const newFilters = {
      ...localFilters,
      minParameters: min,
      maxParameters: max,
    };
    setLocalFilters(newFilters);
    onFiltersChange(newFilters);
  };

  const clearFilters = () => {
    const defaultFilters: ModelSearchFilters = {
      task: 'text-generation',
      sort: 'downloads',
    };
    setLocalFilters(defaultFilters);
    onFiltersChange(defaultFilters);
  };

  return (
    <div className="p-4 space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Filters</h3>
        <button
          onClick={clearFilters}
          className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400"
        >
          Clear All
        </button>
      </div>

      {/* Registry */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Registry
        </label>
        <div className="space-y-2">
          {['HuggingFace', 'Civitai', 'Ollama'].map((registry) => (
            <label key={registry} className="flex items-center">
              <input
                type="checkbox"
                checked={localFilters.registries?.includes(registry.toLowerCase()) || false}
                onChange={(e) => {
                  const current = localFilters.registries || [];
                  const registryLower = registry.toLowerCase();
                  const newRegistries = e.target.checked
                    ? [...current, registryLower]
                    : current.filter((r) => r !== registryLower);
                  handleFilterChange('registries', newRegistries.length > 0 ? newRegistries : undefined);
                }}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">{registry}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Sort By */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Sort By
        </label>
        <select
          value={localFilters.sort || 'downloads'}
          onChange={(e) => handleFilterChange('sort', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
                   bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
        >
          <option value="downloads">Most Downloaded</option>
          <option value="likes">Most Liked</option>
          <option value="trending">Trending</option>
        </select>
      </div>

      {/* Library */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Library
        </label>
        <select
          value={localFilters.library || ''}
          onChange={(e) => handleFilterChange('library', e.target.value || undefined)}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
                   bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
        >
          <option value="">All Libraries</option>
          <option value="transformers">Transformers</option>
          <option value="diffusers">Diffusers</option>
          <option value="sentence-transformers">Sentence Transformers</option>
        </select>
      </div>

      {/* Model Size */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Model Size (Parameters)
        </label>
        <div className="space-y-2">
          <button
            onClick={() => handleParameterRangeChange(undefined, 1_000_000_000)}
            className={`w-full px-3 py-2 text-sm rounded-lg border transition-colors ${
              localFilters.maxParameters === 1_000_000_000
                ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-500 text-blue-700 dark:text-blue-300'
                : 'border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
            }`}
          >
            &lt; 1B
          </button>
          <button
            onClick={() => handleParameterRangeChange(1_000_000_000, 7_000_000_000)}
            className={`w-full px-3 py-2 text-sm rounded-lg border transition-colors ${
              localFilters.minParameters === 1_000_000_000 && localFilters.maxParameters === 7_000_000_000
                ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-500 text-blue-700 dark:text-blue-300'
                : 'border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
            }`}
          >
            1B - 7B
          </button>
          <button
            onClick={() => handleParameterRangeChange(7_000_000_000, 13_000_000_000)}
            className={`w-full px-3 py-2 text-sm rounded-lg border transition-colors ${
              localFilters.minParameters === 7_000_000_000 && localFilters.maxParameters === 13_000_000_000
                ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-500 text-blue-700 dark:text-blue-300'
                : 'border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
            }`}
          >
            7B - 13B
          </button>
          <button
            onClick={() => handleParameterRangeChange(13_000_000_000, undefined)}
            className={`w-full px-3 py-2 text-sm rounded-lg border transition-colors ${
              localFilters.minParameters === 13_000_000_000 && !localFilters.maxParameters
                ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-500 text-blue-700 dark:text-blue-300'
                : 'border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
            }`}
          >
            &gt; 13B
          </button>
        </div>
      </div>

      {/* Architecture */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Architecture
        </label>
        <div className="space-y-2">
          {['Llama', 'Mistral', 'GPT', 'Falcon', 'MPT'].map((arch) => (
            <label key={arch} className="flex items-center">
              <input
                type="checkbox"
                checked={localFilters.architectures?.includes(arch) || false}
                onChange={(e) => {
                  const current = localFilters.architectures || [];
                  const newArchs = e.target.checked
                    ? [...current, arch]
                    : current.filter((a) => a !== arch);
                  handleFilterChange('architectures', newArchs.length > 0 ? newArchs : undefined);
                }}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">{arch}</span>
            </label>
          ))}
        </div>
      </div>

      {/* License */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          License
        </label>
        <div className="space-y-2">
          {['apache-2.0', 'mit', 'cc-by-4.0', 'llama2', 'other'].map((license) => (
            <label key={license} className="flex items-center">
              <input
                type="checkbox"
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="ml-2 text-sm text-gray-700 dark:text-gray-300 capitalize">
                {license}
              </span>
            </label>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ModelFilters;
