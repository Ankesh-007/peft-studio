/**
 * Deployment Dashboard
 * 
 * Main dashboard for viewing and managing all deployments.
 * Shows deployment status, endpoints, and quick actions.
 * 
 * Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
 */

import React, { useState, useEffect } from 'react';

interface Deployment {
  deployment_id: string;
  config: {
    name: string;
    platform: string;
    model_path: string;
    base_model?: string;
    min_instances: number;
    max_instances: number;
    auto_scaling: boolean;
  };
  status: 'pending' | 'deploying' | 'active' | 'failed' | 'stopped' | 'updating';
  endpoint?: {
    endpoint_id: string;
    url: string;
    status: string;
    avg_latency_ms: number;
    last_health_check?: string;
  };
  platform_deployment_id?: string;
  created_at: string;
  deployed_at?: string;
  error_message?: string;
  usage_metrics?: {
    total_requests: number;
    successful_requests: number;
    failed_requests: number;
    avg_latency_ms: number;
    estimated_cost: number;
  };
}

interface DeploymentDashboardProps {
  onCreateDeployment: () => void;
  onTestEndpoint: (deploymentId: string) => void;
  onStopDeployment: (deploymentId: string) => void;
  onViewMetrics: (deploymentId: string) => void;
}

const STATUS_COLORS = {
  pending: 'bg-gray-100 text-gray-800',
  deploying: 'bg-blue-100 text-blue-800',
  active: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  stopped: 'bg-gray-100 text-gray-600',
  updating: 'bg-yellow-100 text-yellow-800'
};

const PLATFORM_ICONS: Record<string, string> = {
  predibase: '🚀',
  together_ai: '⚡',
  modal: '🎯',
  replicate: '🔄'
};

export const DeploymentDashboard: React.FC<DeploymentDashboardProps> = ({
  onCreateDeployment,
  onTestEndpoint,
  onStopDeployment,
  onViewMetrics
}) => {
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const [platformFilter, setPlatformFilter] = useState<string>('all');

  useEffect(() => {
    loadDeployments();
    const interval = setInterval(loadDeployments, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const loadDeployments = async () => {
    try {
      const response = await fetch('/api/deployments');
      const data = await response.json();
      setDeployments(data);
    } catch (error) {
      console.error('Failed to load deployments:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredDeployments = deployments.filter(d => {
    if (filter !== 'all' && d.status !== filter) return false;
    if (platformFilter !== 'all' && d.config.platform !== platformFilter) return false;
    return true;
  });

  const stats = {
    total: deployments.length,
    active: deployments.filter(d => d.status === 'active').length,
    deploying: deployments.filter(d => d.status === 'deploying').length,
    failed: deployments.filter(d => d.status === 'failed').length
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading deployments...</div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Deployments</h1>
          <p className="text-gray-600 mt-1">Manage your model deployments across platforms</p>
        </div>
        <button
          onClick={onCreateDeployment}
          className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 flex items-center gap-2"
        >
          <span>+</span>
          <span>New Deployment</span>
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 bg-white rounded-lg shadow">
          <div className="text-sm text-gray-600">Total Deployments</div>
          <div className="text-3xl font-bold mt-2">{stats.total}</div>
        </div>
        <div className="p-4 bg-white rounded-lg shadow">
          <div className="text-sm text-gray-600">Active</div>
          <div className="text-3xl font-bold mt-2 text-green-600">{stats.active}</div>
        </div>
        <div className="p-4 bg-white rounded-lg shadow">
          <div className="text-sm text-gray-600">Deploying</div>
          <div className="text-3xl font-bold mt-2 text-blue-600">{stats.deploying}</div>
        </div>
        <div className="p-4 bg-white rounded-lg shadow">
          <div className="text-sm text-gray-600">Failed</div>
          <div className="text-3xl font-bold mt-2 text-red-600">{stats.failed}</div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <select
          value={filter}
          onChange={e => setFilter(e.target.value)}
          className="px-4 py-2 border rounded-lg"
        >
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="deploying">Deploying</option>
          <option value="pending">Pending</option>
          <option value="failed">Failed</option>
          <option value="stopped">Stopped</option>
        </select>

        <select
          value={platformFilter}
          onChange={e => setPlatformFilter(e.target.value)}
          className="px-4 py-2 border rounded-lg"
        >
          <option value="all">All Platforms</option>
          <option value="predibase">Predibase</option>
          <option value="together_ai">Together AI</option>
          <option value="modal">Modal</option>
          <option value="replicate">Replicate</option>
        </select>
      </div>

      {/* Deployments List */}
      {filteredDeployments.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <p className="text-gray-500">No deployments found</p>
          <button
            onClick={onCreateDeployment}
            className="mt-4 px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
          >
            Create Your First Deployment
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredDeployments.map(deployment => (
            <div
              key={deployment.deployment_id}
              className="bg-white rounded-lg shadow p-6"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">
                      {PLATFORM_ICONS[deployment.config.platform] || '📦'}
                    </span>
                    <div>
                      <h3 className="text-xl font-semibold">{deployment.config.name}</h3>
                      <p className="text-sm text-gray-600">
                        {deployment.deployment_id} • {deployment.config.platform}
                      </p>
                    </div>
                    <span
                      className={`px-3 py-1 rounded-full text-sm font-medium ${
                        STATUS_COLORS[deployment.status]
                      }`}
                    >
                      {deployment.status}
                    </span>
                  </div>

                  <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <span className="text-sm text-gray-600">Model:</span>
                      <p className="font-medium">{deployment.config.model_path}</p>
                    </div>
                    {deployment.endpoint && (
                      <div>
                        <span className="text-sm text-gray-600">Endpoint:</span>
                        <p className="font-medium text-blue-600 truncate">
                          {deployment.endpoint.url}
                        </p>
                      </div>
                    )}
                    {deployment.endpoint && (
                      <div>
                        <span className="text-sm text-gray-600">Avg Latency:</span>
                        <p className="font-medium">
                          {deployment.endpoint.avg_latency_ms.toFixed(0)}ms
                        </p>
                      </div>
                    )}
                  </div>

                  {deployment.usage_metrics && (
                    <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-gray-600">Requests:</span>
                          <p className="font-semibold">
                            {deployment.usage_metrics.total_requests}
                          </p>
                        </div>
                        <div>
                          <span className="text-gray-600">Success Rate:</span>
                          <p className="font-semibold">
                            {deployment.usage_metrics.total_requests > 0
                              ? (
                                  (deployment.usage_metrics.successful_requests /
                                    deployment.usage_metrics.total_requests) *
                                  100
                                ).toFixed(1)
                              : 0}
                            %
                          </p>
                        </div>
                        <div>
                          <span className="text-gray-600">Avg Latency:</span>
                          <p className="font-semibold">
                            {deployment.usage_metrics.avg_latency_ms.toFixed(0)}ms
                          </p>
                        </div>
                        <div>
                          <span className="text-gray-600">Cost:</span>
                          <p className="font-semibold">
                            ${deployment.usage_metrics.estimated_cost.toFixed(2)}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {deployment.error_message && (
                    <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                      <p className="text-sm text-red-800">{deployment.error_message}</p>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex flex-col gap-2 ml-4">
                  {deployment.status === 'active' && (
                    <>
                      <button
                        onClick={() => onTestEndpoint(deployment.deployment_id)}
                        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
                      >
                        Test
                      </button>
                      <button
                        onClick={() => onViewMetrics(deployment.deployment_id)}
                        className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 text-sm"
                      >
                        Metrics
                      </button>
                      <button
                        onClick={() => onStopDeployment(deployment.deployment_id)}
                        className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 text-sm"
                      >
                        Stop
                      </button>
                    </>
                  )}
                  {deployment.status === 'failed' && (
                    <button
                      onClick={() => onCreateDeployment()}
                      className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
                    >
                      Retry
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
