/**
 * Configuration Library Browser Component
 * Browse and manage saved configurations
 * Validates: Requirement 18.3 - Configuration library browser
 */

import React from 'react';
import { Calendar, User, Tag, Trash2, Share2, FileText } from 'lucide-react';

interface ConfigurationMetadata {
  id: string;
  name: string;
  description: string;
  created_at: string;
  modified_at: string;
  author?: string;
  tags: string[];
  training_results?: Record<string, unknown>;
  hardware_requirements?: Record<string, unknown>;
}

interface ConfigurationLibraryBrowserProps {
  configurations: ConfigurationMetadata[];
  onSelect: (configId: string) => void;
  onDelete: (configId: string) => void;
  loading?: boolean;
}

const ConfigurationLibraryBrowser: React.FC<ConfigurationLibraryBrowserProps> = ({
  configurations,
  onSelect,
  onDelete,
  loading = false,
}) => {
  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

      if (diffDays === 0) {
        return 'Today';
      } else if (diffDays === 1) {
        return 'Yesterday';
      } else if (diffDays < 7) {
        return `${diffDays} days ago`;
      } else {
        return date.toLocaleDateString();
      }
    } catch {
      return dateString;
    }
  };

  const handleShare = async (config: ConfigurationMetadata) => {
    try {
      // Download the configuration file
      const response = await fetch(`http://localhost:8000/api/configurations/library/${config.id}`);
      if (!response.ok) {
        throw new Error('Failed to load configuration');
      }

      const data = await response.json();
      const blob = new Blob([JSON.stringify(data.data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${config.name.replace(/[^a-z0-9]/gi, '_')}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error sharing configuration:', err);
      alert('Failed to share configuration');
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center py-12">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
        </div>
      </div>
    );
  }

  if (configurations.length === 0) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            No Configurations Found
          </h3>
          <p className="text-gray-600">
            Export a configuration to add it to your library
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Configuration Library ({configurations.length})
      </h3>

      <div className="space-y-3">
        {configurations.map((config) => (
          <div
            key={config.id}
            className="border border-gray-200 rounded-lg p-4 hover:border-blue-500 hover:shadow-md transition-all cursor-pointer"
            onClick={() => onSelect(config.id)}
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1 min-w-0">
                <h4 className="text-base font-semibold text-gray-900 truncate">
                  {config.name}
                </h4>
                {config.description && (
                  <p className="text-sm text-gray-600 line-clamp-2 mt-1">
                    {config.description}
                  </p>
                )}
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2 ml-3">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleShare(config);
                  }}
                  className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                  title="Share configuration"
                >
                  <Share2 className="w-4 h-4" />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(config.id);
                  }}
                  className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                  title="Delete configuration"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Metadata */}
            <div className="flex flex-wrap items-center gap-4 text-xs text-gray-500 mt-3">
              {config.author && (
                <div className="flex items-center gap-1">
                  <User className="w-3 h-3" />
                  <span>{config.author}</span>
                </div>
              )}

              <div className="flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                <span>{formatDate(config.modified_at)}</span>
              </div>

              {config.training_results && (
                <div className="flex items-center gap-1">
                  <span className="px-2 py-0.5 bg-green-100 text-green-800 rounded-full text-xs font-medium">
                    Has Results
                  </span>
                </div>
              )}
            </div>

            {/* Tags */}
            {config.tags && config.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-3">
                {config.tags.map((tag, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center gap-1 px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-full"
                  >
                    <Tag className="w-3 h-3" />
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ConfigurationLibraryBrowser;
