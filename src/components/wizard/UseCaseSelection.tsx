import { Loader2 } from "lucide-react";
import React, { useEffect, useState } from "react";

import { apiClient } from "../../api/client";
import Tooltip from "../Tooltip";

import type { OptimizationProfile, WizardState } from "../../types/wizard";

interface UseCaseSelectionProps {
  wizardState: WizardState;
  onProfileSelect: (profile: OptimizationProfile) => void;
}

/**
 * Step 1: Use Case Selection
 * Displays optimization profiles with descriptions, icons, and hardware requirements
 */
const UseCaseSelection: React.FC<UseCaseSelectionProps> = ({
  wizardState,
  onProfileSelect,
}) => {
  const [profiles, setProfiles] = useState<OptimizationProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProfiles();
  }, []);

  const loadProfiles = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch("http://127.0.0.1:8000/api/profiles");
      const data = await response.json();
      setProfiles(data.profiles);
    } catch (err) {
      setError(
        "Failed to load optimization profiles. Please ensure the backend is running.",
      );
      console.error("Error loading profiles:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="ml-3 text-gray-600">
          Loading optimization profiles...
        </span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <p className="text-red-800 mb-4">{error}</p>
        <button
          onClick={loadProfiles}
          className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome Message */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-blue-900 mb-2">
          Welcome to the Training Wizard!
        </h2>
        <p className="text-blue-800">
          Let's start by selecting what you want your model to do. Each use case
          has been pre-configured with optimal settings, so you don't need to
          worry about technical details.
        </p>
      </div>

      {/* Profile Selection */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Choose Your Use Case
          </h3>
          <Tooltip configKey="profile.use_case" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {profiles.map((profile) => (
            <button
              key={profile.id}
              onClick={() => onProfileSelect(profile)}
              className={`
                text-left p-6 rounded-lg border-2 transition-all hover:shadow-lg
                ${
                  wizardState.profile?.id === profile.id
                    ? "border-blue-600 bg-blue-50 shadow-md"
                    : "border-gray-200 bg-white hover:border-blue-300"
                }
              `}
              data-testid={`profile-card-${profile.id}`}
            >
              {/* Icon and Name */}
              <div className="flex items-center gap-3 mb-3">
                <span className="text-4xl" role="img" aria-label={profile.name}>
                  {profile.icon}
                </span>
                <div>
                  <h4 className="font-semibold text-gray-900">
                    {profile.name}
                  </h4>
                  {wizardState.profile?.id === profile.id && (
                    <span className="text-xs text-blue-600 font-medium">
                      Selected
                    </span>
                  )}
                </div>
              </div>

              {/* Description */}
              <p className="text-sm text-gray-600 mb-4">
                {profile.description}
              </p>

              {/* Example Use Cases */}
              <div className="mb-4">
                <p className="text-xs font-medium text-gray-700 mb-2">
                  Perfect for:
                </p>
                <ul className="text-xs text-gray-600 space-y-1">
                  {profile.example_use_cases.slice(0, 3).map((useCase, idx) => (
                    <li key={idx} className="flex items-start">
                      <span className="text-blue-600 mr-2">•</span>
                      <span>{useCase}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Hardware Requirements */}
              <div className="border-t border-gray-200 pt-4 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-600 flex items-center gap-1">
                    <Tooltip configKey="min_gpu_memory">
                      <span>Min GPU Memory</span>
                    </Tooltip>
                  </span>
                  <span className="font-medium text-gray-900">
                    {profile.requirements.min_gpu_memory_gb} GB
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-600 flex items-center gap-1">
                    <Tooltip configKey="min_dataset_size">
                      <span>Min Dataset Size</span>
                    </Tooltip>
                  </span>
                  <span className="font-medium text-gray-900">
                    {profile.requirements.min_dataset_size} samples
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-600 flex items-center gap-1">
                    <Tooltip configKey="estimated_time">
                      <span>Est. Time/Epoch</span>
                    </Tooltip>
                  </span>
                  <span className="font-medium text-gray-900">
                    ~{profile.requirements.estimated_time_per_epoch_minutes} min
                  </span>
                </div>
              </div>

              {/* Tags */}
              {profile.tags && profile.tags.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-1">
                  {profile.tags.slice(0, 3).map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Selected Profile Details */}
      {wizardState.profile && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <h4 className="font-semibold text-green-900 mb-2">
            ✓ {wizardState.profile.name} Selected
          </h4>
          <p className="text-sm text-green-800 mb-3">
            Your training will be optimized for {wizardState.profile.use_case}{" "}
            tasks. Click "Next" to continue with dataset upload.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-green-700 font-medium">LoRA Rank:</span>
              <span className="ml-2 text-green-900">
                {wizardState.profile.config.lora_r}
              </span>
            </div>
            <div>
              <span className="text-green-700 font-medium">Learning Rate:</span>
              <span className="ml-2 text-green-900">
                {wizardState.profile.config.learning_rate}
              </span>
            </div>
            <div>
              <span className="text-green-700 font-medium">Epochs:</span>
              <span className="ml-2 text-green-900">
                {wizardState.profile.config.num_epochs}
              </span>
            </div>
            <div>
              <span className="text-green-700 font-medium">Max Length:</span>
              <span className="ml-2 text-green-900">
                {wizardState.profile.config.max_seq_length}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UseCaseSelection;
