/**
 * Configuration Preview Component
 * Displays a preview of configuration before import
 * Validates: Requirement 18.2 - Configuration preview before import
 */

import React from 'react';
import { X, Calendar, User, Tag, Cpu, Database, Zap } from 'lucide-react';

interface ConfigurationPreviewProps {
  configuration: Record<string, unknown>;
  onClose?: () => void;
  compact?: boolean;
}

const InfoRow: React.FC<{ label: string; value: unknown; icon?: React.ReactNode }> = ({
  label,
  value,
  icon,
}) => (
  <div className="flex items-start gap-3 py-2">
    {icon && <div className="text-gray-400 mt-0.5">{icon}</div>}
    <div className="flex-1 min-w-0">
      <div className="text-sm font-medium text-gray-500">{label}</div>
      <div className="text-sm text-gray-900 break-words">{value || 'N/A'}</div>
    </div>
  </div>
);

const ConfigurationPreview: React.FC<ConfigurationPreviewProps> = ({
  configuration,
  onClose,
  compact = false,
}) => {
  const { metadata, configuration: config } = configuration;

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  return (
    <div className={compact ? '' : 'p-6'}>
      {/* Header */}
      {!compact && (
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-bold text-gray-900">Configuration Preview</h3>
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>
      )}

      {/* Metadata Section */}
      <div className={`${compact ? 'mb-4' : 'mb-6'}`}>
        <h4 className="text-lg font-semibold text-gray-900 mb-3">Metadata</h4>
        <div className="bg-gray-50 rounded-lg p-4 space-y-1">
          <InfoRow label="Name" value={metadata?.name} />
          <InfoRow label="Description" value={metadata?.description} />
          {metadata?.author && <InfoRow label="Author" value={metadata.author} icon={<User className="w-4 h-4" />} />}
          {metadata?.created_at && (
            <InfoRow
              label="Created"
              value={formatDate(metadata.created_at)}
              icon={<Calendar className="w-4 h-4" />}
            />
          )}
          {metadata?.tags && metadata.tags.length > 0 && (
            <div className="flex items-start gap-3 py-2">
              <Tag className="w-4 h-4 text-gray-400 mt-0.5" />
              <div className="flex-1">
                <div className="text-sm font-medium text-gray-500 mb-1">Tags</div>
                <div className="flex flex-wrap gap-2">
                  {metadata.tags.map((tag: string, index: number) => (
                    <span
                      key={index}
                      className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Configuration Section */}
      <div className={`${compact ? 'mb-4' : 'mb-6'}`}>
        <h4 className="text-lg font-semibold text-gray-900 mb-3">Training Configuration</h4>

        {/* Model Settings */}
        <div className="bg-gray-50 rounded-lg p-4 mb-3">
          <h5 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
            <Database className="w-4 h-4" />
            Model Settings
          </h5>
          <div className="space-y-1">
            <InfoRow label="Base Model" value={config?.base_model} />
            <InfoRow label="Model Source" value={config?.model_source} />
            <InfoRow label="Algorithm" value={config?.algorithm?.toUpperCase()} />
            <InfoRow label="Quantization" value={config?.quantization} />
          </div>
        </div>

        {/* PEFT Parameters */}
        <div className="bg-gray-50 rounded-lg p-4 mb-3">
          <h5 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
            <Zap className="w-4 h-4" />
            PEFT Parameters
          </h5>
          <div className="grid grid-cols-2 gap-x-4">
            <InfoRow label="Rank" value={config?.rank} />
            <InfoRow label="Alpha" value={config?.alpha} />
            <InfoRow label="Dropout" value={config?.dropout} />
            <InfoRow
              label="Target Modules"
              value={config?.target_modules?.join(', ')}
            />
          </div>
        </div>

        {/* Training Parameters */}
        <div className="bg-gray-50 rounded-lg p-4 mb-3">
          <h5 className="text-sm font-semibold text-gray-700 mb-2">Training Parameters</h5>
          <div className="grid grid-cols-2 gap-x-4">
            <InfoRow label="Learning Rate" value={config?.learning_rate} />
            <InfoRow label="Batch Size" value={config?.batch_size} />
            <InfoRow label="Epochs" value={config?.num_epochs} />
            <InfoRow label="Warmup Steps" value={config?.warmup_steps} />
            <InfoRow
              label="Gradient Accumulation"
              value={config?.gradient_accumulation_steps}
            />
          </div>
        </div>

        {/* Compute Settings */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h5 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
            <Cpu className="w-4 h-4" />
            Compute Settings
          </h5>
          <div className="space-y-1">
            <InfoRow label="Provider" value={config?.provider} />
            <InfoRow label="Resource ID" value={config?.resource_id} />
            <InfoRow label="Experiment Tracker" value={config?.experiment_tracker} />
            <InfoRow label="Project Name" value={config?.project_name} />
          </div>
        </div>
      </div>

      {/* Hardware Requirements */}
      {metadata?.hardware_requirements && (
        <div className="mb-6">
          <h4 className="text-lg font-semibold text-gray-900 mb-3">Hardware Requirements</h4>
          <div className="bg-gray-50 rounded-lg p-4">
            <pre className="text-xs text-gray-700 font-mono overflow-x-auto">
              {JSON.stringify(metadata.hardware_requirements, null, 2)}
            </pre>
          </div>
        </div>
      )}

      {/* Training Results */}
      {metadata?.training_results && (
        <div>
          <h4 className="text-lg font-semibold text-gray-900 mb-3">Training Results</h4>
          <div className="bg-gray-50 rounded-lg p-4">
            <pre className="text-xs text-gray-700 font-mono overflow-x-auto">
              {JSON.stringify(metadata.training_results, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};

export default ConfigurationPreview;
