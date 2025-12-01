import React from 'react';

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

interface PlatformConnectionCardProps {
  platform: Platform;
  connection?: PlatformConnection;
  onConnect: () => void;
  onDisconnect: () => void;
  onVerify: () => void;
  onEdit: () => void;
}

/**
 * Platform Connection Card Component
 * 
 * Displays platform information and connection status with action buttons.
 * Validates: Requirements 1.1, 1.4
 */
export const PlatformConnectionCard: React.FC<PlatformConnectionCardProps> = ({
  platform,
  connection,
  onConnect,
  onDisconnect,
  onVerify,
  onEdit
}) => {
  const isConnected = connection?.status === 'connected';
  const isError = connection?.status === 'error';
  const isVerifying = connection?.status === 'verifying';

  const getStatusColor = () => {
    if (isConnected) return 'bg-green-100 text-green-800 border-green-200';
    if (isError) return 'bg-red-100 text-red-800 border-red-200';
    if (isVerifying) return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    return 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const getStatusText = () => {
    if (isConnected) return 'Connected';
    if (isError) return 'Error';
    if (isVerifying) return 'Verifying...';
    return 'Not Connected';
  };

  const getStatusIcon = () => {
    if (isConnected) return '✓';
    if (isError) return '✗';
    if (isVerifying) return '⟳';
    return '○';
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const getFeatureIcons = () => {
    const features = [];
    if (platform.supports_training) features.push({ icon: '🎓', label: 'Training' });
    if (platform.supports_inference) features.push({ icon: '🤖', label: 'Inference' });
    if (platform.supports_registry) features.push({ icon: '📦', label: 'Registry' });
    if (platform.supports_tracking) features.push({ icon: '📊', label: 'Tracking' });
    return features;
  };

  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden hover:shadow-lg transition-shadow">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900">
              {platform.display_name}
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              {platform.description}
            </p>
          </div>
          <div className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor()}`}>
            <span className="mr-1">{getStatusIcon()}</span>
            {getStatusText()}
          </div>
        </div>
      </div>

      {/* Features */}
      <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
        <div className="flex flex-wrap gap-2">
          {getFeatureIcons().map(feature => (
            <div
              key={feature.label}
              className="flex items-center gap-1 px-2 py-1 bg-white rounded text-xs text-gray-700 border border-gray-200"
              title={feature.label}
            >
              <span>{feature.icon}</span>
              <span>{feature.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Connection Details */}
      {connection && (
        <div className="px-4 py-3 space-y-2 text-sm">
          {connection.connected_at && (
            <div className="flex justify-between">
              <span className="text-gray-600">Connected:</span>
              <span className="text-gray-900 font-medium">
                {formatDate(connection.connected_at)}
              </span>
            </div>
          )}
          {connection.last_verified && (
            <div className="flex justify-between">
              <span className="text-gray-600">Last Verified:</span>
              <span className="text-gray-900 font-medium">
                {formatDate(connection.last_verified)}
              </span>
            </div>
          )}
          {connection.error_message && (
            <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded">
              <p className="text-xs text-red-700">
                <strong>Error:</strong> {connection.error_message}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
        {!isConnected ? (
          <button
            onClick={onConnect}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            Connect
          </button>
        ) : (
          <div className="grid grid-cols-3 gap-2">
            <button
              onClick={onVerify}
              disabled={isVerifying}
              className="px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              title="Verify Connection"
            >
              Verify
            </button>
            <button
              onClick={onEdit}
              className="px-3 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors text-sm font-medium"
              title="Edit Credentials"
            >
              Edit
            </button>
            <button
              onClick={onDisconnect}
              className="px-3 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm font-medium"
              title="Disconnect"
            >
              Disconnect
            </button>
          </div>
        )}
      </div>

      {/* Version Info */}
      <div className="px-4 py-2 bg-gray-100 text-xs text-gray-600 text-center">
        Version {platform.version}
      </div>
    </div>
  );
};
