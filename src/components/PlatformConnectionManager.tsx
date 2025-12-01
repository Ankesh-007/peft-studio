import React, { useState, useEffect } from 'react';
import { PlatformConnectionCard } from './PlatformConnectionCard';
import { PlatformCredentialForm } from './PlatformCredentialForm';
import { Spinner } from './LoadingStates';

interface Platform {
  name: string;
  display_name: string;
  description: string;
  version: string;
  supports_training: boolean;
  supports_inference: boolean;
  supports_registry: boolean;
  supports_tracking: boolean;
  required_credentials: string[];
  connected: boolean;
}

interface PlatformConnection {
  platform_name: string;
  display_name: string;
  status: string;
  connected_at?: string;
  last_verified?: string;
  error_message?: string;
  features: string[];
  metadata: Record<string, any>;
}

/**
 * Platform Connection Manager UI
 * 
 * Provides a comprehensive interface for managing platform connections.
 * Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5
 */
export const PlatformConnectionManager: React.FC = () => {
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [connections, setConnections] = useState<PlatformConnection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPlatform, setSelectedPlatform] = useState<Platform | null>(null);
  const [showCredentialForm, setShowCredentialForm] = useState(false);
  const [editingPlatform, setEditingPlatform] = useState<string | null>(null);

  // Load available platforms and connections
  useEffect(() => {
    loadPlatforms();
    loadConnections();
  }, []);

  const loadPlatforms = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/platforms');
      if (!response.ok) throw new Error('Failed to load platforms');
      
      const data = await response.json();
      setPlatforms(data.platforms);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load platforms');
    } finally {
      setLoading(false);
    }
  };

  const loadConnections = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/platforms/connections');
      if (!response.ok) throw new Error('Failed to load connections');
      
      const data = await response.json();
      setConnections(data.connections);
    } catch (err) {
      console.error('Error loading connections:', err);
    }
  };

  const handleConnect = (platform: Platform) => {
    setSelectedPlatform(platform);
    setEditingPlatform(null);
    setShowCredentialForm(true);
  };

  const handleEdit = (platform: Platform) => {
    setSelectedPlatform(platform);
    setEditingPlatform(platform.name);
    setShowCredentialForm(true);
  };

  const handleDisconnect = async (platformName: string) => {
    if (!confirm(`Are you sure you want to disconnect from ${platformName}?`)) {
      return;
    }

    try {
      const response = await fetch(
        `http://localhost:8000/api/platforms/disconnect/${platformName}`,
        { method: 'POST' }
      );

      if (!response.ok) throw new Error('Failed to disconnect');

      // Reload data
      await loadPlatforms();
      await loadConnections();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to disconnect');
    }
  };

  const handleVerify = async (platformName: string) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/platforms/verify/${platformName}`,
        { method: 'POST' }
      );

      if (!response.ok) throw new Error('Failed to verify connection');

      const result = await response.json();
      
      if (result.valid) {
        alert(`Connection to ${platformName} is valid!`);
      } else {
        alert(`Connection to ${platformName} failed: ${result.error}`);
      }

      // Reload connections to update status
      await loadConnections();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to verify connection');
    }
  };

  const handleCredentialSubmit = async (credentials: Record<string, string>) => {
    if (!selectedPlatform) return;

    try {
      const endpoint = editingPlatform
        ? `http://localhost:8000/api/platforms/credentials/${selectedPlatform.name}`
        : 'http://localhost:8000/api/platforms/connect';

      const method = editingPlatform ? 'PUT' : 'POST';

      const response = await fetch(endpoint, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          platform_name: selectedPlatform.name,
          credentials
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to connect');
      }

      // Close form and reload data
      setShowCredentialForm(false);
      setSelectedPlatform(null);
      setEditingPlatform(null);
      await loadPlatforms();
      await loadConnections();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to connect');
    }
  };

  const handleFormCancel = () => {
    setShowCredentialForm(false);
    setSelectedPlatform(null);
    setEditingPlatform(null);
  };

  const getConnectionForPlatform = (platformName: string): PlatformConnection | undefined => {
    return connections.find(c => c.platform_name === platformName);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <Spinner size="lg" />
        <p className="text-dark-text-secondary">Loading platforms...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <h3 className="text-red-800 font-semibold mb-2">Error Loading Platforms</h3>
        <p className="text-red-600">{error}</p>
        <button
          onClick={() => {
            setError(null);
            setLoading(true);
            loadPlatforms();
          }}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Platform Connections</h2>
          <p className="text-gray-600 mt-1">
            Connect to cloud GPU providers, model registries, and experiment trackers
          </p>
        </div>
        <button
          onClick={() => loadConnections()}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Refresh
        </button>
      </div>

      {/* Connection Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600">Total Platforms</div>
          <div className="text-2xl font-bold text-gray-900">{platforms.length}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600">Connected</div>
          <div className="text-2xl font-bold text-green-600">
            {platforms.filter(p => p.connected).length}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600">Available</div>
          <div className="text-2xl font-bold text-blue-600">
            {platforms.filter(p => !p.connected).length}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600">Errors</div>
          <div className="text-2xl font-bold text-red-600">
            {connections.filter(c => c.status === 'error').length}
          </div>
        </div>
      </div>

      {/* Platform Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {platforms.map(platform => (
          <PlatformConnectionCard
            key={platform.name}
            platform={platform}
            connection={getConnectionForPlatform(platform.name)}
            onConnect={() => handleConnect(platform)}
            onDisconnect={() => handleDisconnect(platform.name)}
            onVerify={() => handleVerify(platform.name)}
            onEdit={() => handleEdit(platform)}
          />
        ))}
      </div>

      {/* Credential Form Modal */}
      {showCredentialForm && selectedPlatform && (
        <PlatformCredentialForm
          platform={selectedPlatform}
          isEditing={!!editingPlatform}
          onSubmit={handleCredentialSubmit}
          onCancel={handleFormCancel}
        />
      )}
    </div>
  );
};
