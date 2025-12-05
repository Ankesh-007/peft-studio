import React, { useState, useEffect, useCallback } from 'react';
import { ModelMetadata, ModelCompatibility } from '../types/model';
import { apiClient } from '../api/client';
import { Spinner } from './LoadingStates';

interface ModelDetailModalProps {
  model: ModelMetadata;
  onClose: () => void;
  onSelect: (model: ModelMetadata) => void;
  onAddToComparison: (model: ModelMetadata) => void;
  isInComparison: boolean;
}

const ModelDetailModal: React.FC<ModelDetailModalProps> = ({
  model,
  onClose,
  onSelect,
  onAddToComparison,
  isInComparison,
}) => {
  const [compatibility, setCompatibility] = useState<ModelCompatibility | null>(null);
  const [loadingCompatibility, setLoadingCompatibility] = useState(false);
  const [gpuMemory, setGpuMemory] = useState<number>(0);

  useEffect(() => {
    // Load GPU memory from hardware profile
    const loadHardwareInfo = async () => {
      try {
        const hardware = await apiClient.getHardwareProfile() as { gpus?: Array<{ memory_total_gb: number }> };
        if (hardware.gpus && hardware.gpus.length > 0) {
          setGpuMemory(hardware.gpus[0].memory_total_gb);
        }
      } catch (error) {
        console.error('Error loading hardware info:', error);
      }
    };
    loadHardwareInfo();
  }, []);

  const checkCompatibility = useCallback(async () => {
    setLoadingCompatibility(true);
    try {
      const result = await apiClient.checkModelCompatibility(model.model_id, gpuMemory) as ModelCompatibility;
      setCompatibility(result);
    } catch (error) {
      console.error('Error checking compatibility:', error);
    } finally {
      setLoadingCompatibility(false);
    }
  }, [model.model_id, gpuMemory]);

  useEffect(() => {
    if (gpuMemory > 0) {
      checkCompatibility();
    }
  }, [gpuMemory, checkCompatibility]);

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

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-6 flex items-start justify-between">
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-1">
              {model.model_name}
            </h2>
            <p className="text-gray-600 dark:text-gray-400">by {model.author}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Downloads</div>
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                {formatNumber(model.downloads)}
              </div>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Likes</div>
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                {formatNumber(model.likes)}
              </div>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Parameters</div>
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                {formatNumber(model.parameters)}
              </div>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Size</div>
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                {formatSize(model.size_mb)}
              </div>
            </div>
          </div>

          {/* Details */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Details</h3>
            <div className="grid grid-cols-2 gap-4">
              {model.architecture && (
                <div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">Architecture</div>
                  <div className="text-gray-900 dark:text-white font-medium">{model.architecture}</div>
                </div>
              )}
              {model.license && (
                <div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">License</div>
                  <div className="text-gray-900 dark:text-white font-medium">{model.license}</div>
                </div>
              )}
              {model.pipeline_tag && (
                <div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">Task</div>
                  <div className="text-gray-900 dark:text-white font-medium">{model.pipeline_tag}</div>
                </div>
              )}
              {model.library_name && (
                <div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">Library</div>
                  <div className="text-gray-900 dark:text-white font-medium">{model.library_name}</div>
                </div>
              )}
            </div>
          </div>

          {/* Tags */}
          {model.tags && model.tags.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Tags</h3>
              <div className="flex flex-wrap gap-2">
                {model.tags.slice(0, 10).map((tag) => (
                  <span
                    key={tag}
                    className="px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 
                             rounded-full text-sm"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Compatibility Check */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Compatibility Check
            </h3>
            {loadingCompatibility ? (
              <div className="flex items-center gap-2">
                <Spinner size="sm" />
                <span className="text-dark-text-secondary">Checking compatibility...</span>
              </div>
            ) : compatibility ? (
              <div className="space-y-3">
                <div
                  className={`p-4 rounded-lg ${
                    compatibility.compatible
                      ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
                      : 'bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    {compatibility.compatible ? (
                      <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                    )}
                    <span className={`font-semibold ${compatibility.compatible ? 'text-green-700 dark:text-green-300' : 'text-yellow-700 dark:text-yellow-300'}`}>
                      {compatibility.compatible ? 'Compatible with your hardware' : 'May require adjustments'}
                    </span>
                  </div>
                  <div className="text-sm text-gray-700 dark:text-gray-300">
                    Estimated VRAM: {compatibility.estimatedVRAM.toFixed(1)} GB
                  </div>
                </div>

                {compatibility.warnings.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="font-medium text-gray-900 dark:text-white">Warnings:</h4>
                    <ul className="list-disc list-inside space-y-1 text-sm text-gray-700 dark:text-gray-300">
                      {compatibility.warnings.map((warning, idx) => (
                        <li key={idx}>{warning}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {compatibility.recommendations.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="font-medium text-gray-900 dark:text-white">Recommendations:</h4>
                    <ul className="list-disc list-inside space-y-1 text-sm text-gray-700 dark:text-gray-300">
                      {compatibility.recommendations.map((rec, idx) => (
                        <li key={idx}>{rec}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-gray-600 dark:text-gray-400">
                Unable to check compatibility. Please ensure your hardware profile is available.
              </p>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 p-6 flex items-center justify-end gap-3">
          <button
            onClick={() => onAddToComparison(model)}
            disabled={isInComparison}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              isInComparison
                ? 'bg-gray-200 dark:bg-gray-700 text-gray-500 cursor-not-allowed'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white hover:bg-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            {isInComparison ? 'In Comparison' : 'Add to Comparison'}
          </button>
          <button
            onClick={() => onSelect(model)}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 
                     transition-colors font-medium"
          >
            Select Model
          </button>
        </div>
      </div>
    </div>
  );
};

export default ModelDetailModal;
