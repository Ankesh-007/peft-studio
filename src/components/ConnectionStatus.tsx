import React from "react";
import { cn } from "../lib/utils";

export type ConnectionState = "online" | "offline" | "connecting";

interface ConnectionStatusProps {
  status: ConnectionState;
  reconnectAttempts?: number;
  className?: string;
  showLabel?: boolean;
}

/**
 * Connection status indicator component
 * Displays online/offline/connecting states with visual feedback
 */
export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
  status,
  reconnectAttempts = 0,
  className,
  showLabel = true,
}) => {
  const getStatusColor = (): string => {
    switch (status) {
      case "online":
        return "bg-green-500";
      case "offline":
        return "bg-red-500";
      case "connecting":
        return "bg-yellow-500";
      default:
        return "bg-gray-500";
    }
  };

  const getStatusText = (): string => {
    switch (status) {
      case "online":
        return "Connected";
      case "offline":
        return reconnectAttempts > 0
          ? `Reconnecting (${reconnectAttempts})`
          : "Disconnected";
      case "connecting":
        return "Connecting...";
      default:
        return "Unknown";
    }
  };

  const getAriaLabel = (): string => {
    switch (status) {
      case "online":
        return "Connection status: online";
      case "offline":
        return reconnectAttempts > 0
          ? `Connection status: offline, reconnection attempt ${reconnectAttempts}`
          : "Connection status: offline";
      case "connecting":
        return "Connection status: connecting";
      default:
        return "Connection status: unknown";
    }
  };

  return (
    <div
      className={cn("flex items-center gap-8", className)}
      role="status"
      aria-label={getAriaLabel()}
    >
      <div className="relative flex h-12 w-12 items-center justify-center">
        <span
          className={cn(
            "h-8 w-8 rounded-full",
            getStatusColor(),
            status === "connecting" && "animate-pulse",
          )}
        />
        {status === "connecting" && (
          <span
            className={cn(
              "absolute h-12 w-12 animate-ping rounded-full opacity-75",
              getStatusColor(),
            )}
          />
        )}
      </div>
      {showLabel && (
        <span className="text-small text-dark-text-secondary">
          {getStatusText()}
        </span>
      )}
    </div>
  );
};
