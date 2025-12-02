/**
 * Notification Handler Component
 *
 * Handles desktop notifications, taskbar progress, and notification sounds
 * for training events.
 */

import { useEffect, useCallback } from "react";

interface NotificationOptions {
  type: "progress" | "error" | "completion" | "warning";
  title: string;
  message: string;
  milestone?: number;
  urgency?: "low" | "normal" | "high" | "critical";
  sound?: boolean;
  actions?: string[];
  taskbar_progress?: number;
  respect_dnd?: boolean;
}

interface NotificationHandlerProps {
  jobId?: string;
  onNotificationReceived?: (notification: NotificationOptions) => void;
}

export const NotificationHandler: React.FC<NotificationHandlerProps> = ({
  jobId,
  onNotificationReceived,
}) => {
  // Audio for notification sounds
  const playNotificationSound = useCallback((urgency: string = "normal") => {
    try {
      // Different sounds for different urgency levels
      const soundMap: Record<string, string> = {
        low: "/sounds/notification-low.mp3",
        normal: "/sounds/notification.mp3",
        high: "/sounds/notification-high.mp3",
        critical: "/sounds/notification-critical.mp3",
      };

      const audio = new Audio(soundMap[urgency] || soundMap.normal);
      audio.volume = 0.5;
      audio.play().catch((err) => {
        console.warn("Could not play notification sound:", err);
      });
    } catch (error) {
      console.error("Error playing notification sound:", error);
    }
  }, []);

  // Show desktop notification
  const showDesktopNotification = useCallback(
    async (options: NotificationOptions) => {
      try {
        // Check if Electron API is available
        if (window.api?.showNotification) {
          await window.api.showNotification({
            title: options.title,
            message: options.message,
            urgency: options.urgency || "normal",
            sound: options.sound || false,
          });
        } else if ("Notification" in window) {
          // Fallback to Web Notifications API
          if (Notification.permission === "granted") {
            new Notification(options.title, {
              body: options.message,
              icon: "/icon.png",
              tag: `training-${jobId}`,
              requireInteraction: options.urgency === "critical",
            });
          } else if (Notification.permission !== "denied") {
            const permission = await Notification.requestPermission();
            if (permission === "granted") {
              new Notification(options.title, {
                body: options.message,
                icon: "/icon.png",
              });
            }
          }
        }
      } catch (error) {
        console.error("Error showing desktop notification:", error);
      }
    },
    [jobId],
  );

  // Update taskbar progress
  const updateTaskbarProgress = useCallback(async (progress: number) => {
    try {
      if (window.api?.setProgress) {
        await window.api.setProgress(progress);
      }
    } catch (error) {
      console.error("Error updating taskbar progress:", error);
    }
  }, []);

  // Handle incoming notification
  const handleNotification = useCallback(
    async (notification: NotificationOptions) => {
      console.log("Received notification:", notification);

      // Call callback if provided
      if (onNotificationReceived) {
        onNotificationReceived(notification);
      }

      // Show desktop notification
      await showDesktopNotification(notification);

      // Play sound if enabled
      if (notification.sound) {
        playNotificationSound(notification.urgency);
      }

      // Update taskbar progress if provided
      if (notification.taskbar_progress !== undefined) {
        await updateTaskbarProgress(notification.taskbar_progress);
      }

      // Show in-app notification toast
      // This would integrate with your toast/notification system
      // For example: toast.show({ title: notification.title, message: notification.message })
    },
    [
      showDesktopNotification,
      playNotificationSound,
      updateTaskbarProgress,
      onNotificationReceived,
    ],
  );

  // Connect to notification WebSocket
  useEffect(() => {
    if (!jobId) return;

    let ws: WebSocket | null = null;

    const connectWebSocket = () => {
      try {
        // Connect to notification WebSocket endpoint
        ws = new WebSocket(`ws://localhost:8000/ws/notifications/${jobId}`);

        ws.onopen = () => {
          console.log("Connected to notification stream");
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);

            if (data.type === "notification" && data.data) {
              handleNotification(data.data);
            }
          } catch (error) {
            console.error("Error parsing notification message:", error);
          }
        };

        ws.onerror = (error) => {
          console.error("WebSocket error:", error);
        };

        ws.onclose = () => {
          console.log("Notification WebSocket closed");
          // Attempt to reconnect after 5 seconds
          setTimeout(connectWebSocket, 5000);
        };
      } catch (error) {
        console.error("Error connecting to notification WebSocket:", error);
      }
    };

    connectWebSocket();

    // Cleanup on unmount
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [jobId, handleNotification]);

  // Request notification permission on mount
  useEffect(() => {
    if ("Notification" in window && Notification.permission === "default") {
      Notification.requestPermission().then((permission) => {
        console.log("Notification permission:", permission);
      });
    }
  }, []);

  // This component doesn't render anything visible
  return null;
};

export default NotificationHandler;
