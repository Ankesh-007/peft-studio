/**
 * Experiment Tracking Dashboard
 * 
 * Main dashboard for viewing and managing experiment tracking across
 * multiple platforms (W&B, Comet ML, Phoenix).
 * 
 * Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
 */

import React, { useState, useEffect } from 'react';
import { Play, Pause, Square, ExternalLink, TrendingUp, Database, Tag } from 'lucide-react';

interface Experiment {
  job_id: string;
  tracker: string;
  project: string;
  name: string;
  status: string;
  started_at: string;
  finished_at?: string;
  metadata: {
    model_name: string;
    dataset_name: string;
    use_case: string;
    provider: string;
    algorithm: string;
  };
  hyperparameters: Record<string, any>;
  tags: string[];
  artifacts?: Array<{
    id: string;
    name: string;
    type: string;
    linked_at: string;
  }>;
  summary?: Record<string, any>;
  url?: string;
}

interface ExperimentTrackingDashboardProps {
  onCompare?: (jobIds: string[]) => void;
  onViewDetails?: (jobId: string) => void;
}

export const ExperimentTrackingDashboard: React.FC<ExperimentTrackingDashboardProps> = ({
  onCompare,
  onViewDetails,
}) => {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedExperiments, setSelectedExperiments] = useState<Set<string>>(new Set());
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterTracker, setFilterTracker] = useState<string>('all');

  useEffect(() => {
    loadExperiments();
    
    // Refresh every 5 seconds for active experiments
    const interval = setInterval(loadExperiments, 5000);
    return () => clearInterval(interval);
  }, [filterStatus, filterTracker]);

  const loadExperiments = async () => {
    try {
      const params = new URLSearchParams();
      if (filterStatus !== 'all') {
        params.append('status', filterStatus);
      }
      if (filterTracker !== 'all') {
        params.append('tracker', filterTracker);
      }
      params.append('limit', '100');

      const response = await fetch(`/api/experiments?${params}`);
      if (!response.ok) {
        throw new Error('Failed to load experiments');
      }

      const data = await response.json();
      setExperiments(data.experiments || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load experiments');
    } finally {
      setLoading(false);
    }
  };

  const toggleExperimentSelection = (jobId: string) => {
    const newSelection = new Set(selectedExperiments);
    if (newSelection.has(jobId)) {
      newSelection.delete(jobId);
    } else {
      newSelection.add(jobId);
    }
    setSelectedExperiments(newSelection);
  };

  const handleCompare = () => {
    if (onCompare && selectedExperiments.size > 0) {
      onCompare(Array.from(selectedExperiments));
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getTrackerColor = (tracker: string) => {
    switch (tracker) {
      case 'wandb':
        return 'bg-yellow-100 text-yellow-800';
      case 'cometml':
        return 'bg-purple-100 text-purple-800';
      case 'phoenix':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const formatDuration = (startDate: string, endDate?: string) => {
    const start = new Date(startDate);
    const end = endDate ? new Date(endDate) : new Date();
    const durationMs = end.getTime() - start.getTime();
    
    const hours = Math.floor(durationMs / (1000 * 60 * 60));
    const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  if (loading && experiments.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading experiments...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Experiment Tracking</h2>
          <p className="text-gray-600 mt-1">
            Monitor and compare experiments across W&B, Comet ML, and Phoenix
          </p>
        </div>
        
        {selectedExperiments.size > 0 && (
          <button
            onClick={handleCompare}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Compare {selectedExperiments.size} Experiments
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Status
          </label>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Status</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Tracker
          </label>
          <select
            value={filterTracker}
            onChange={(e) => setFilterTracker(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Trackers</option>
            <option value="wandb">Weights & Biases</option>
            <option value="cometml">Comet ML</option>
            <option value="phoenix">Arize Phoenix</option>
          </select>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {/* Experiments List */}
      {experiments.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <TrendingUp className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No experiments found</p>
          <p className="text-gray-500 text-sm mt-2">
            Start a training run with experiment tracking enabled
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {experiments.map((experiment) => (
            <div
              key={experiment.job_id}
              className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4 flex-1">
                  {/* Selection Checkbox */}
                  <input
                    type="checkbox"
                    checked={selectedExperiments.has(experiment.job_id)}
                    onChange={() => toggleExperimentSelection(experiment.job_id)}
                    className="mt-1 w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                  />

                  {/* Experiment Info */}
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {experiment.name || experiment.job_id}
                      </h3>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(experiment.status)}`}>
                        {experiment.status}
                      </span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getTrackerColor(experiment.tracker)}`}>
                        {experiment.tracker}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-sm text-gray-600 mb-3">
                      <div>
                        <span className="font-medium">Model:</span> {experiment.metadata.model_name}
                      </div>
                      <div>
                        <span className="font-medium">Algorithm:</span> {experiment.metadata.algorithm}
                      </div>
                      <div>
                        <span className="font-medium">Dataset:</span> {experiment.metadata.dataset_name}
                      </div>
                      <div>
                        <span className="font-medium">Provider:</span> {experiment.metadata.provider}
                      </div>
                      <div>
                        <span className="font-medium">Started:</span> {formatDate(experiment.started_at)}
                      </div>
                      <div>
                        <span className="font-medium">Duration:</span> {formatDuration(experiment.started_at, experiment.finished_at)}
                      </div>
                    </div>

                    {/* Tags */}
                    {experiment.tags && experiment.tags.length > 0 && (
                      <div className="flex items-center gap-2 mb-3">
                        <Tag className="w-4 h-4 text-gray-400" />
                        <div className="flex gap-2">
                          {experiment.tags.map((tag, index) => (
                            <span
                              key={index}
                              className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Summary Metrics */}
                    {experiment.summary && Object.keys(experiment.summary).length > 0 && (
                      <div className="flex items-center gap-4 text-sm">
                        {Object.entries(experiment.summary).slice(0, 4).map(([key, value]) => (
                          <div key={key} className="flex items-center gap-2">
                            <span className="text-gray-600">{key}:</span>
                            <span className="font-medium text-gray-900">
                              {typeof value === 'number' ? value.toFixed(4) : value}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Artifacts */}
                    {experiment.artifacts && experiment.artifacts.length > 0 && (
                      <div className="flex items-center gap-2 mt-3 text-sm text-gray-600">
                        <Database className="w-4 h-4" />
                        <span>{experiment.artifacts.length} artifact(s)</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  {experiment.url && (
                    <a
                      href={experiment.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                      title="View on tracker"
                    >
                      <ExternalLink className="w-5 h-5" />
                    </a>
                  )}
                  
                  {onViewDetails && (
                    <button
                      onClick={() => onViewDetails(experiment.job_id)}
                      className="px-3 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                    >
                      Details
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ExperimentTrackingDashboard;
