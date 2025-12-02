/**
 * Preset Library Component
 *
 * Displays saved configuration presets with search and filtering capabilities.
 * Allows users to load, export, import, and delete presets.
 */

import React, { useState, useEffect } from "react";

import {
  listPresets,
  deletePreset,
  downloadPresetAsFile,
  uploadPresetFile,
} from "../api/presets";

import type { ConfigurationPreset } from "../types/wizard";

interface PresetLibraryProps {
  onSelectPreset: (preset: ConfigurationPreset) => void;
  onClose: () => void;
}

export const PresetLibrary: React.FC<PresetLibraryProps> = ({
  onSelectPreset,
  onClose,
}) => {
  const [presets, setPresets] = useState<ConfigurationPreset[]>([]);
  const [filteredPresets, setFilteredPresets] = useState<ConfigurationPreset[]>(
    [],
  );
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [allTags, setAllTags] = useState<string[]>([]);

  // Load presets on mount
  useEffect(() => {
    loadPresets();
  }, []);

  // Filter presets when search or tags change
  useEffect(() => {
    filterPresets();
  }, [searchTerm, selectedTags, presets]);

  const loadPresets = async () => {
    try {
      setLoading(true);
      setError(null);
      const loadedPresets = await listPresets();
      setPresets(loadedPresets);

      // Extract all unique tags
      const tags = new Set<string>();
      loadedPresets.forEach((preset) => {
        preset.tags.forEach((tag) => tags.add(tag));
      });
      setAllTags(Array.from(tags).sort());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load presets");
    } finally {
      setLoading(false);
    }
  };

  const filterPresets = () => {
    let filtered = presets;

    // Apply search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(
        (preset) =>
          preset.name.toLowerCase().includes(term) ||
          preset.description.toLowerCase().includes(term),
      );
    }

    // Apply tag filter
    if (selectedTags.length > 0) {
      filtered = filtered.filter((preset) =>
        selectedTags.some((tag) => preset.tags.includes(tag)),
      );
    }

    setFilteredPresets(filtered);
  };

  const handleDelete = async (presetId: string) => {
    if (!confirm("Are you sure you want to delete this preset?")) {
      return;
    }

    try {
      await deletePreset(presetId);
      await loadPresets();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to delete preset");
    }
  };

  const handleExport = async (presetId: string) => {
    try {
      await downloadPresetAsFile(presetId);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to export preset");
    }
  };

  const handleImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      await uploadPresetFile(file);
      await loadPresets();
      alert("Preset imported successfully!");
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to import preset");
    }

    // Reset file input
    event.target.value = "";
  };

  const toggleTag = (tag: string) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag],
    );
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-2xl font-semibold text-gray-900">
            Configuration Presets
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Search and Filter Bar */}
        <div className="px-6 py-4 border-b border-gray-200 space-y-4">
          <div className="flex gap-4">
            {/* Search Input */}
            <div className="flex-1">
              <input
                type="text"
                placeholder="Search presets by name or description..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Import Button */}
            <label className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors cursor-pointer flex items-center gap-2">
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
                />
              </svg>
              Import
              <input
                type="file"
                accept=".json"
                onChange={handleImport}
                className="hidden"
              />
            </label>
          </div>

          {/* Tag Filter */}
          {allTags.length > 0 && (
            <div className="flex flex-wrap gap-2">
              <span className="text-sm text-gray-600 py-1">
                Filter by tags:
              </span>
              {allTags.map((tag) => (
                <button
                  key={tag}
                  onClick={() => toggleTag(tag)}
                  className={`px-3 py-1 rounded-full text-sm transition-colors ${
                    selectedTags.includes(tag)
                      ? "bg-blue-600 text-white"
                      : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                  }`}
                >
                  {tag}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Preset List */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-gray-500">Loading presets...</div>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-red-600">{error}</div>
            </div>
          ) : filteredPresets.length === 0 ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-gray-500">
                {presets.length === 0
                  ? "No presets saved yet. Save your first configuration to get started!"
                  : "No presets match your search criteria."}
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredPresets.map((preset) => (
                <div
                  key={preset.id}
                  className="border border-gray-200 rounded-lg p-4 hover:shadow-lg transition-shadow"
                >
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-lg font-semibold text-gray-900 flex-1">
                      {preset.name}
                    </h3>
                  </div>

                  {preset.description && (
                    <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                      {preset.description}
                    </p>
                  )}

                  <div className="space-y-2 mb-3 text-sm text-gray-700">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Model:</span>
                      <span className="font-medium truncate ml-2">
                        {preset.model_name || "Not set"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Method:</span>
                      <span className="font-medium">
                        {preset.peft_method.toUpperCase()}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Batch Size:</span>
                      <span className="font-medium">{preset.batch_size}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Learning Rate:</span>
                      <span className="font-medium">
                        {preset.learning_rate}
                      </span>
                    </div>
                  </div>

                  {preset.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-3">
                      {preset.tags.map((tag) => (
                        <span
                          key={tag}
                          className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="text-xs text-gray-500 mb-3">
                    Updated: {formatDate(preset.updated_at)}
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={() => onSelectPreset(preset)}
                      className="flex-1 px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-sm"
                    >
                      Load
                    </button>
                    <button
                      onClick={() => handleExport(preset.id)}
                      className="px-3 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors text-sm"
                      title="Export"
                    >
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                        />
                      </svg>
                    </button>
                    <button
                      onClick={() => handleDelete(preset.id)}
                      className="px-3 py-2 bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors text-sm"
                      title="Delete"
                    >
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                        />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
