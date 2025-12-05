/**
 * Offline Mode Indicator Component
 *
 * Displays network connectivity status and offline queue information.
 * Shows clear indicators when the application is offline.
 */

import React, { useEffect, useState } from "react";
import { WifiOff, Wifi, Cloud, CloudOff, RefreshCw } from "lucide-react";

interface NetworkStatus {
  status: "online" | "offline" | "checking";
  is_online: boolean;
  is_offline: boolean;
  last_check: string | null;
  is_monitoring: boolean;
  check_interval: number;
}

interface QueueStats {
  total: number;
  pending: number;
  in_progress: number;
  completed: number;
  failed: number;
}

interface SyncStatus {
  is_syncing: boolean;
  network_status: string;
  is_online: boolean;
  queue_stats: QueueStats;
  conflict_strategy: string;
}

export const OfflineIndicator: React.FC = () => {
  const [networkStatus, setNetworkStatus] = useState<NetworkStatus | null>(null);
  const [queueStats, setQueueStats] = useState<QueueStats | null>(null);
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  const fetchNetworkStatus = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/offline/network-status");
      const data = await response.json();
      setNetworkStatus(data);
    } catch (error) {
      console.error("Error fetching network status:", error);
    }
  };

  const fetchQueueStats = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/offline/queue/stats");
      const data = await response.json();
      setQueueStats(data);
    } catch (error) {
      console.error("Error fetching queue stats:", error);
    }
  };

  const fetchSyncStatus = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/offline/sync/status");
      const data = await response.json();
      setSyncStatus(data);
    } catch (error) {
      console.error("Error fetching sync status:", error);
    }
  };

  useEffect(() => {
    // Fetch initial status
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchNetworkStatus();
    fetchQueueStats();
    fetchSyncStatus();

    // Poll for updates every 10 seconds
    const interval = setInterval(() => {
      fetchNetworkStatus();
      fetchQueueStats();
      fetchSyncStatus();
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  const handleManualSync = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/offline/sync", {
        method: "POST",
      });
      const result = await response.json();
      console.log("Sync result:", result);

      // Refresh stats after sync
      fetchQueueStats();
      fetchSyncStatus();
    } catch (error) {
      console.error("Error triggering sync:", error);
    }
  };

  const handleCheckConnectivity = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/offline/check-connectivity", {
        method: "POST",
      });
      const result = await response.json();
      setNetworkStatus((prev) => (prev ? { ...prev, ...result } : null));
    } catch (error) {
      console.error("Error checking connectivity:", error);
    }
  };

  if (!networkStatus) {
    return null;
  }

  const isOffline = networkStatus.status === "offline";
  const hasPendingOperations = queueStats && queueStats.pending > 0;

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {/* Compact indicator */}
      <div
        className={`
          flex items-center gap-2 px-4 py-2 rounded-lg shadow-lg cursor-pointer
          transition-all duration-200 hover:shadow-xl
          ${isOffline ? "bg-yellow-500 text-white" : "bg-green-500 text-white"}
        `}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {isOffline ? (
          <>
            <CloudOff className="w-5 h-5" />
            <span className="font-medium">Offline Mode</span>
          </>
        ) : (
          <>
            <Cloud className="w-5 h-5" />
            <span className="font-medium">Online</span>
          </>
        )}

        {hasPendingOperations && (
          <span className="ml-2 px-2 py-0.5 bg-white bg-opacity-30 rounded-full text-xs">
            {queueStats.pending} queued
          </span>
        )}
      </div>

      {/* Expanded details */}
      {isExpanded && (
        <div className="mt-2 bg-white rounded-lg shadow-xl p-4 w-80 border border-gray-200">
          <div className="space-y-3">
            {/* Network Status */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {isOffline ? (
                  <WifiOff className="w-5 h-5 text-yellow-500" />
                ) : (
                  <Wifi className="w-5 h-5 text-green-500" />
                )}
                <span className="font-medium text-gray-900">
                  {networkStatus.status === "checking"
                    ? "Checking..."
                    : isOffline
                      ? "Offline"
                      : "Online"}
                </span>
              </div>
              <button
                onClick={handleCheckConnectivity}
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                Check Now
              </button>
            </div>

            {/* Queue Stats */}
            {queueStats && (
              <div className="border-t pt-3">
                <div className="text-sm font-medium text-gray-700 mb-2">Offline Queue</div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Pending:</span>
                    <span className="font-medium text-yellow-600">{queueStats.pending}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">In Progress:</span>
                    <span className="font-medium text-blue-600">{queueStats.in_progress}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Completed:</span>
                    <span className="font-medium text-green-600">{queueStats.completed}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Failed:</span>
                    <span className="font-medium text-red-600">{queueStats.failed}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Sync Status */}
            {syncStatus && (
              <div className="border-t pt-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Synchronization</span>
                  {syncStatus.is_syncing && (
                    <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />
                  )}
                </div>

                {!isOffline && hasPendingOperations && (
                  <button
                    onClick={handleManualSync}
                    disabled={syncStatus.is_syncing}
                    className={`
                      w-full px-3 py-2 rounded text-sm font-medium
                      transition-colors duration-200
                      ${
                        syncStatus.is_syncing
                          ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                          : "bg-blue-500 text-white hover:bg-blue-600"
                      }
                    `}
                  >
                    {syncStatus.is_syncing ? "Syncing..." : "Sync Now"}
                  </button>
                )}

                {isOffline && hasPendingOperations && (
                  <div className="text-xs text-gray-600 bg-yellow-50 p-2 rounded">
                    {queueStats.pending} operation(s) will sync when online
                  </div>
                )}
              </div>
            )}

            {/* Last Check */}
            {networkStatus.last_check && (
              <div className="text-xs text-gray-500 text-center border-t pt-2">
                Last checked: {new Date(networkStatus.last_check).toLocaleTimeString()}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default OfflineIndicator;
