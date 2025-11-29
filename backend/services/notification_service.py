"""
Notification Service

Handles progress milestone notifications and training event notifications.
Supports desktop notifications, taskbar progress, and Do Not Disturb integration.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum
import platform
import logging

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    PROGRESS = "progress"
    ERROR = "error"
    COMPLETION = "completion"
    WARNING = "warning"


class UrgencyLevel(str, Enum):
    """Urgency levels for notifications"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ProgressUpdate:
    """Represents a training progress update."""
    current_step: int
    total_steps: int
    previous_step: int = 0


@dataclass
class NotificationEvent:
    """Represents a notification to be sent to the user."""
    type: NotificationType
    title: str
    message: str
    milestone: Optional[int] = None  # For progress notifications (25, 50, 75, 100)
    urgency: str = "normal"  # normal, high, critical
    sound: bool = False
    actions: Optional[List[str]] = None
    taskbar_progress: Optional[float] = None  # 0.0 to 1.0 for taskbar progress indicator
    respect_dnd: bool = True  # Whether to respect Do Not Disturb settings


def check_progress_milestone(progress_update: ProgressUpdate) -> Optional[NotificationEvent]:
    """
    Check if a progress milestone has been crossed and generate notification.
    
    Args:
        progress_update: Current progress information
        
    Returns:
        NotificationEvent if milestone crossed, None otherwise
    """
    if progress_update.total_steps == 0:
        return None
    
    # Calculate progress percentages
    current_progress = (progress_update.current_step / progress_update.total_steps) * 100
    previous_progress = (progress_update.previous_step / progress_update.total_steps) * 100
    
    # Define milestones
    milestones = [25, 50, 75, 100]
    
    # Check if we crossed any milestone
    for milestone in milestones:
        if previous_progress < milestone <= current_progress:
            return _create_milestone_notification(milestone, progress_update)
    
    return None


def _create_milestone_notification(milestone: int, progress_update: ProgressUpdate) -> NotificationEvent:
    """
    Create a notification for a specific milestone.
    
    Args:
        milestone: The milestone percentage (25, 50, 75, 100)
        progress_update: Current progress information
        
    Returns:
        NotificationEvent for the milestone
    """
    if milestone == 100:
        return NotificationEvent(
            type=NotificationType.COMPLETION,
            title="Training Complete! 🎉",
            message=f"Your model training has finished successfully after {progress_update.total_steps} steps.",
            milestone=milestone,
            sound=True,
            urgency="normal"
        )
    elif milestone == 75:
        return NotificationEvent(
            type=NotificationType.PROGRESS,
            title="Training 75% Complete",
            message=f"Your model is three-quarters done! {progress_update.current_step}/{progress_update.total_steps} steps completed.",
            milestone=milestone,
            sound=False,
            urgency="normal"
        )
    elif milestone == 50:
        return NotificationEvent(
            type=NotificationType.PROGRESS,
            title="Training Halfway There!",
            message=f"Your model training is 50% complete. {progress_update.current_step}/{progress_update.total_steps} steps done.",
            milestone=milestone,
            sound=False,
            urgency="normal"
        )
    elif milestone == 25:
        return NotificationEvent(
            type=NotificationType.PROGRESS,
            title="Training 25% Complete",
            message=f"Your model training is off to a good start! {progress_update.current_step}/{progress_update.total_steps} steps completed.",
            milestone=milestone,
            sound=False,
            urgency="normal"
        )
    
    return NotificationEvent(
        type=NotificationType.PROGRESS,
        title=f"Training {milestone}% Complete",
        message=f"Progress update: {progress_update.current_step}/{progress_update.total_steps} steps completed.",
        milestone=milestone,
        sound=False,
        urgency="normal"
    )


def create_error_notification(
    error_message: str, 
    error_type: str = "training_error",
    urgency: str = "high"
) -> NotificationEvent:
    """
    Create an error notification with appropriate urgency level.
    
    Args:
        error_message: The error message
        error_type: Type of error
        urgency: Urgency level (normal, high, critical)
        
    Returns:
        NotificationEvent for the error
    """
    # Determine urgency based on error type if not explicitly provided
    if error_type in ["oom_error", "cuda_error", "system_crash"]:
        urgency = "critical"
    elif error_type in ["loss_divergence", "gradient_explosion", "data_error"]:
        urgency = "high"
    else:
        urgency = urgency or "high"
    
    return NotificationEvent(
        type=NotificationType.ERROR,
        title="Training Error",
        message=error_message,
        urgency=urgency,
        sound=True,
        actions=["View Details", "Retry"],
        respect_dnd=False  # Errors should always notify
    )


def create_warning_notification(warning_message: str) -> NotificationEvent:
    """
    Create a warning notification.
    
    Args:
        warning_message: The warning message
        
    Returns:
        NotificationEvent for the warning
    """
    return NotificationEvent(
        type=NotificationType.WARNING,
        title="Training Warning",
        message=warning_message,
        urgency="normal",
        sound=False
    )


def check_do_not_disturb() -> bool:
    """
    Check if the system is in Do Not Disturb mode.
    
    Returns:
        True if DND is enabled, False otherwise
    """
    system = platform.system()
    
    try:
        if system == "Darwin":  # macOS
            # Check macOS Focus/DND status
            import subprocess
            result = subprocess.run(
                ["defaults", "read", "com.apple.controlcenter", "NSStatusItem Visible FocusModes"],
                capture_output=True,
                text=True,
                timeout=1
            )
            return result.returncode == 0 and "1" in result.stdout
        
        elif system == "Windows":
            # Check Windows Focus Assist status
            import winreg
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Notifications\Settings",
                    0,
                    winreg.KEY_READ
                )
                value, _ = winreg.QueryValueEx(key, "NOC_GLOBAL_SETTING_ALLOW_CRITICAL_TOASTS_ABOVE_LOCK")
                winreg.CloseKey(key)
                return value == 0
            except (FileNotFoundError, OSError):
                return False
        
        elif system == "Linux":
            # Check GNOME/KDE DND status
            import subprocess
            # Try GNOME first
            result = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.notifications", "show-banners"],
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0:
                return "false" in result.stdout.lower()
            
            # Fallback: assume DND is off if we can't detect
            return False
    
    except Exception as e:
        logger.debug(f"Could not detect Do Not Disturb status: {e}")
        return False
    
    return False


def calculate_taskbar_progress(current_step: int, total_steps: int) -> float:
    """
    Calculate taskbar progress percentage.
    
    Args:
        current_step: Current training step
        total_steps: Total training steps
        
    Returns:
        Progress as a float between 0.0 and 1.0
    """
    if total_steps == 0:
        return 0.0
    
    progress = current_step / total_steps
    return max(0.0, min(1.0, progress))


class NotificationManager:
    """Manages notification state and prevents duplicate notifications."""
    
    def __init__(self):
        self.sent_milestones = set()
        self.last_notification_step = -1
        self.dnd_enabled = False
        self.update_dnd_status()
    
    def should_send_notification(self, progress_update: ProgressUpdate) -> bool:
        """
        Check if a notification should be sent based on progress.
        
        Args:
            progress_update: Current progress information
            
        Returns:
            True if notification should be sent
        """
        notification = check_progress_milestone(progress_update)
        
        if notification is None:
            return False
        
        # Check if we already sent this milestone
        if notification.milestone in self.sent_milestones:
            return False
        
        return True
    
    def mark_milestone_sent(self, milestone: int):
        """Mark a milestone as having been notified."""
        self.sent_milestones.add(milestone)
    
    def update_dnd_status(self):
        """Update the Do Not Disturb status."""
        self.dnd_enabled = check_do_not_disturb()
    
    def should_respect_dnd(self, notification: NotificationEvent) -> bool:
        """
        Check if a notification should respect Do Not Disturb settings.
        
        Args:
            notification: The notification to check
            
        Returns:
            True if notification should be suppressed due to DND
        """
        if not notification.respect_dnd:
            return False  # Notification explicitly ignores DND
        
        self.update_dnd_status()
        return self.dnd_enabled
    
    def reset(self):
        """Reset notification state for a new training run."""
        self.sent_milestones.clear()
        self.last_notification_step = -1
        self.update_dnd_status()
    
    def get_next_notification(self, progress_update: ProgressUpdate) -> Optional[NotificationEvent]:
        """
        Get the next notification to send if any.
        
        Args:
            progress_update: Current progress information
            
        Returns:
            NotificationEvent if one should be sent, None otherwise
        """
        if not self.should_send_notification(progress_update):
            return None
        
        notification = check_progress_milestone(progress_update)
        
        if notification and notification.milestone:
            # Add taskbar progress
            notification.taskbar_progress = calculate_taskbar_progress(
                progress_update.current_step,
                progress_update.total_steps
            )
            
            # Check if we should suppress due to DND
            if self.should_respect_dnd(notification):
                logger.info(f"Suppressing notification due to Do Not Disturb: {notification.title}")
                # Still mark as sent to avoid duplicate attempts
                self.mark_milestone_sent(notification.milestone)
                self.last_notification_step = progress_update.current_step
                return None
            
            self.mark_milestone_sent(notification.milestone)
            self.last_notification_step = progress_update.current_step
        
        return notification
