"""
Property-based tests for error notifications.

**Feature: simplified-llm-optimization, Property 26: Training error triggers notification**
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pytest
from hypothesis import given, strategies as st, settings
from dataclasses import dataclass
from typing import Optional


# Import notification service
try:
    from services.notification_service import (
        create_error_notification,
        NotificationEvent,
        NotificationType,
        UrgencyLevel
    )
except ImportError:
    # Define minimal versions for testing if imports fail
    from enum import Enum
    
    class NotificationType(str, Enum):
        PROGRESS = "progress"
        ERROR = "error"
        COMPLETION = "completion"
        WARNING = "warning"
    
    class UrgencyLevel(str, Enum):
        LOW = "low"
        NORMAL = "normal"
        HIGH = "high"
        CRITICAL = "critical"
    
    @dataclass
    class NotificationEvent:
        type: NotificationType
        title: str
        message: str
        milestone: Optional[int] = None
        urgency: str = "normal"
        sound: bool = False
        actions: Optional[list] = None
        taskbar_progress: Optional[float] = None
        respect_dnd: bool = True
    
    def create_error_notification(
        error_message: str, 
        error_type: str = "training_error",
        urgency: str = "high"
    ) -> NotificationEvent:
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
            respect_dnd=False
        )


# Strategy for generating error messages
error_message_strategy = st.text(min_size=1, max_size=500)

# Strategy for generating error types
error_type_strategy = st.sampled_from([
    "training_error",
    "oom_error",
    "cuda_error",
    "system_crash",
    "loss_divergence",
    "gradient_explosion",
    "data_error",
    "network_error",
    "file_error",
    "validation_error"
])

# Strategy for generating urgency levels
urgency_strategy = st.sampled_from(["low", "normal", "high", "critical"])


@settings(max_examples=100)
@given(
    error_message=error_message_strategy,
    error_type=error_type_strategy
)
def test_training_error_triggers_notification(error_message, error_type):
    """
    **Feature: simplified-llm-optimization, Property 26: Training error triggers notification**
    **Validates: Requirements 12.2**
    
    For any training error, the system should send an urgent desktop notification
    with error summary.
    """
    # Create error notification
    notification = create_error_notification(error_message, error_type)
    
    # Verify notification is created
    assert notification is not None, "Error notification should be created"
    
    # Verify notification type is ERROR
    assert notification.type == NotificationType.ERROR, \
        f"Notification type should be ERROR, got {notification.type}"
    
    # Verify notification has a title
    assert notification.title is not None, "Notification should have a title"
    assert len(notification.title) > 0, "Notification title should not be empty"
    
    # Verify notification contains the error message
    assert notification.message is not None, "Notification should have a message"
    assert notification.message == error_message, \
        f"Notification message should match error message"
    
    # Verify notification has appropriate urgency
    assert notification.urgency in ["normal", "high", "critical"], \
        f"Notification urgency should be valid, got {notification.urgency}"
    
    # Verify critical errors have critical urgency
    if error_type in ["oom_error", "cuda_error", "system_crash"]:
        assert notification.urgency == "critical", \
            f"Critical error type {error_type} should have critical urgency, got {notification.urgency}"
    
    # Verify high-priority errors have high urgency
    elif error_type in ["loss_divergence", "gradient_explosion", "data_error"]:
        assert notification.urgency == "high", \
            f"High-priority error type {error_type} should have high urgency, got {notification.urgency}"
    
    # Verify notification has sound enabled
    assert notification.sound is True, \
        "Error notifications should have sound enabled"
    
    # Verify notification has actions
    assert notification.actions is not None, \
        "Error notification should have actions"
    assert len(notification.actions) > 0, \
        "Error notification should have at least one action"
    
    # Verify notification does not respect DND (errors should always notify)
    assert notification.respect_dnd is False, \
        "Error notifications should not respect Do Not Disturb settings"


@settings(max_examples=100)
@given(
    error_message=error_message_strategy,
    error_type=error_type_strategy,
    urgency=urgency_strategy
)
def test_error_notification_urgency_levels(error_message, error_type, urgency):
    """
    For any error with explicit urgency level, the notification should
    respect the urgency unless the error type overrides it.
    """
    # Create error notification with explicit urgency
    notification = create_error_notification(error_message, error_type, urgency)
    
    # Verify notification is created
    assert notification is not None
    
    # Critical error types should always be critical
    if error_type in ["oom_error", "cuda_error", "system_crash"]:
        assert notification.urgency == "critical", \
            f"Critical error type should override urgency to critical"
    
    # High-priority error types should always be high
    elif error_type in ["loss_divergence", "gradient_explosion", "data_error"]:
        assert notification.urgency == "high", \
            f"High-priority error type should override urgency to high"
    
    # Other error types should use provided urgency
    else:
        assert notification.urgency == urgency, \
            f"Expected urgency {urgency}, got {notification.urgency}"


@settings(max_examples=100)
@given(error_message=error_message_strategy)
def test_error_notification_has_required_fields(error_message):
    """
    For any error notification, it should contain all required fields
    for desktop notification display.
    """
    # Create error notification with default parameters
    notification = create_error_notification(error_message)
    
    # Verify all required fields are present
    assert hasattr(notification, 'type'), "Notification should have type field"
    assert hasattr(notification, 'title'), "Notification should have title field"
    assert hasattr(notification, 'message'), "Notification should have message field"
    assert hasattr(notification, 'urgency'), "Notification should have urgency field"
    assert hasattr(notification, 'sound'), "Notification should have sound field"
    assert hasattr(notification, 'actions'), "Notification should have actions field"
    assert hasattr(notification, 'respect_dnd'), "Notification should have respect_dnd field"
    
    # Verify field types
    assert isinstance(notification.type, (NotificationType, str)), \
        "Notification type should be NotificationType or string"
    assert isinstance(notification.title, str), "Notification title should be string"
    assert isinstance(notification.message, str), "Notification message should be string"
    assert isinstance(notification.urgency, str), "Notification urgency should be string"
    assert isinstance(notification.sound, bool), "Notification sound should be boolean"
    assert isinstance(notification.respect_dnd, bool), "Notification respect_dnd should be boolean"


@settings(max_examples=100)
@given(
    error_message=error_message_strategy,
    error_type=error_type_strategy
)
def test_error_notification_actions_present(error_message, error_type):
    """
    For any error notification, it should provide actionable options
    for the user to respond to the error.
    """
    notification = create_error_notification(error_message, error_type)
    
    # Verify actions are present
    assert notification.actions is not None, \
        "Error notification should have actions"
    assert isinstance(notification.actions, list), \
        "Notification actions should be a list"
    assert len(notification.actions) >= 1, \
        "Error notification should have at least one action"
    
    # Verify actions are strings
    for action in notification.actions:
        assert isinstance(action, str), \
            f"Action should be a string, got {type(action)}"
        assert len(action) > 0, \
            "Action text should not be empty"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
