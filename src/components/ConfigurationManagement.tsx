/**
 * Configuration Management Component
 * Main component for managing training configurations
 * Validates: Requirements 18.1, 18.2, 18.3, 18.4, 18.5
 */

import React, { useState, useEffect, useCallback } from "react";
import { Download, Upload, Library, Search } from "lucide-react";
import ExportConfigurationDialog from "./configuration/ExportConfigurationDialog";
import ImportConfigurationDialog from "./configuration/ImportConfigurationDialog";
import ConfigurationLibraryBrowser from "./configuration/ConfigurationLibraryBrowser";
import ConfigurationPreview from "./configuration/ConfigurationPreview";

export interface ConfigurationMetadata {
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

export interface SavedConfiguration {
  metadata: ConfigurationMetadata;
  configuration: Record<string, unknown>;
}

const ConfigurationManagement: React.FC = () => {
  const [showExportDialog, setShowExportDialog] = useState(false);
  const [showImportDialog, setShowImportDialog] = useState(false);
  const [showLibraryBrowser, setShowLibraryBrowser] = useState(false);
  const [selectedConfig, setSelectedConfig] = useState<SavedConfiguration | null>(null);
  const [libraryConfigs, setLibraryConfigs] = useState<ConfigurationMetadata[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTags] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadLibraryConfigurations = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch("http://localhost:8000/api/configurations/library/list", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          tags: selectedTags.length > 0 ? selectedTags : null,
          search_query: searchQuery || null,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to load library configurations");
      }

      const data = await response.json();
      setLibraryConfigs(data.configurations || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load configurations");
      console.error("Error loading library configurations:", err);
    } finally {
      setLoading(false);
    }
  }, [selectedTags, searchQuery]);

  // Load library configurations on mount
  useEffect(() => {
    loadLibraryConfigurations();
  }, [loadLibraryConfigurations]);

  const handleExportSuccess = () => {
    setShowExportDialog(false);
    loadLibraryConfigurations(); // Refresh library
  };

  const handleImportSuccess = (config: SavedConfiguration) => {
    setShowImportDialog(false);
    setSelectedConfig(config);
    loadLibraryConfigurations(); // Refresh library
  };

  const handleConfigSelect = async (configId: string) => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`http://localhost:8000/api/configurations/library/${configId}`);

      if (!response.ok) {
        throw new Error("Failed to load configuration");
      }

      const data = await response.json();
      setSelectedConfig(data.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load configuration");
      console.error("Error loading configuration:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteConfig = async (configId: string) => {
    if (!confirm("Are you sure you want to delete this configuration?")) {
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`http://localhost:8000/api/configurations/library/${configId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error("Failed to delete configuration");
      }

      // Clear selection if deleted config was selected
      if (selectedConfig?.metadata.id === configId) {
        setSelectedConfig(null);
      }

      loadLibraryConfigurations(); // Refresh library
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete configuration");
      console.error("Error deleting configuration:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    loadLibraryConfigurations();
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Configuration Management</h1>
          <p className="text-gray-600">Export, import, and manage your training configurations</p>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="mb-6 flex flex-wrap gap-3">
          <button
            onClick={() => setShowExportDialog(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Download className="w-4 h-4" />
            Export Configuration
          </button>

          <button
            onClick={() => setShowImportDialog(true)}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <Upload className="w-4 h-4" />
            Import Configuration
          </button>

          <button
            onClick={() => setShowLibraryBrowser(!showLibraryBrowser)}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          >
            <Library className="w-4 h-4" />
            {showLibraryBrowser ? "Hide Library" : "Browse Library"}
          </button>
        </div>

        {/* Search and Filter */}
        {showLibraryBrowser && (
          <div className="mb-6 bg-white rounded-lg shadow-sm p-4">
            <div className="flex gap-3">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && handleSearch()}
                    placeholder="Search configurations..."
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
              <button
                onClick={handleSearch}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Search
              </button>
            </div>
          </div>
        )}

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Library Browser */}
          {showLibraryBrowser && (
            <div className="bg-white rounded-lg shadow-sm">
              <ConfigurationLibraryBrowser
                configurations={libraryConfigs}
                onSelect={handleConfigSelect}
                onDelete={handleDeleteConfig}
                loading={loading}
              />
            </div>
          )}

          {/* Configuration Preview */}
          {selectedConfig && (
            <div className="bg-white rounded-lg shadow-sm">
              <ConfigurationPreview
                configuration={selectedConfig}
                onClose={() => setSelectedConfig(null)}
              />
            </div>
          )}

          {/* Empty State */}
          {!showLibraryBrowser && !selectedConfig && (
            <div className="col-span-2 bg-white rounded-lg shadow-sm p-12 text-center">
              <Library className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                No Configuration Selected
              </h3>
              <p className="text-gray-600 mb-6">
                Export a new configuration, import an existing one, or browse your library
              </p>
              <div className="flex justify-center gap-3">
                <button
                  onClick={() => setShowExportDialog(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Export Configuration
                </button>
                <button
                  onClick={() => setShowImportDialog(true)}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                >
                  Import Configuration
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Dialogs */}
      {showExportDialog && (
        <ExportConfigurationDialog
          onClose={() => setShowExportDialog(false)}
          onSuccess={handleExportSuccess}
        />
      )}

      {showImportDialog && (
        <ImportConfigurationDialog
          onClose={() => setShowImportDialog(false)}
          onSuccess={handleImportSuccess}
        />
      )}
    </div>
  );
};

export default ConfigurationManagement;
