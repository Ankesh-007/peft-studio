"""
Property-based tests for progress milestone notifications.

**Feature: simplified-llm-optimization, Property 25: Progress milestone notifications**
**Validates: Requirements 12.1**
"""

import pytest
from hypothesis import given, strategies as st, assume
from backend.services.notification_service import (
    check_progress_milestone,
    NotificationEvent,
    ProgressUpdate
)


@given(
    total_steps=st.integers(min_value=100, max_value=10000),
    progress_percent=st.floats(min_value=0.0, max_value=1.0),
    step_size=st.integers(min_value=1, max_value=10)
)
def test_progress_milestone_notifications(total_steps, progress_percent, step_size):
    """
    Property 25: Progress milestone notifications
    
    For any training run, when progress reaches 25%, 50%, 75%, or 100%,
    the system should generate a desktop notification.
    
    Validates: Requirements 12.1
    """
    # Calculate current and previous steps based on progress
    current_step = min(int(total_steps * progress_percent), total_steps)
    previous_step = max(0, current_step - step_size)
    
    progress_update = ProgressUpdate(
        current_step=current_step,
        total_steps=total_steps,
        previous_step=previous_step
    )
    
    # Check if milestone was crossed
    notification = check_progress_milestone(progress_update)
    
    # Calculate progress percentages
    current_progress = (current_step / total_steps) * 100
    previous_progress = (previous_step / total_steps) * 100 if previous_step > 0 else 0
    
    milestones = [25, 50, 75, 100]
    
    # Check if we crossed any milestone
    crossed_milestone = None
    for milestone in milestones:
        if previous_progress < milestone <= current_progress:
            crossed_milestone = milestone
            break
    
    if crossed_milestone:
        # Property: Should generate notification when milestone crossed
        assert notification is not None
        assert isinstance(notification, NotificationEvent)
        
        # Property: Notification should have required fields
        assert hasattr(notification, 'type')
        assert hasattr(notification, 'title')
        assert hasattr(notification, 'message')
        assert hasattr(notification, 'milestone')
        
        # Property: Notification type should be 'progress' or 'completion' (for 100%)
        assert notification.type in ['progress', 'completion']
        
        # Property: Milestone should match the crossed milestone
        assert notification.milestone == crossed_milestone
        
        # Property: Title and message should not be empty
        assert len(notification.title) > 0
        assert len(notification.message) > 0
        
        # Property: Message should mention the milestone percentage or completion
        # Note: 100% completion may use different wording (e.g., "finished", "complete")
        if crossed_milestone == 100:
            # For 100%, check for completion-related words instead of the number
            completion_words = ['complete', 'finished', 'done', '100']
            assert any(word in notification.message.lower() or word in notification.title.lower() 
                      for word in completion_words)
        else:
            # For other milestones, the percentage should appear in the message or title
            assert str(crossed_milestone) in notification.message or str(crossed_milestone) in notification.title
    else:
        # Property: Should not generate notification if no milestone crossed
        assert notification is None


@given(
    st.integers(min_value=100, max_value=10000)
)
def test_completion_notification_at_100_percent(total_steps):
    """
    Test that 100% completion always triggers a notification.
    """
    # Start from 99% to ensure we only cross 100%
    previous_step = int(total_steps * 0.99)
    
    progress_update = ProgressUpdate(
        current_step=total_steps,
        total_steps=total_steps,
        previous_step=previous_step
    )
    
    notification = check_progress_milestone(progress_update)
    
    # Should always notify at completion
    assert notification is not None
    assert notification.milestone == 100
    assert notification.type in ['progress', 'completion']


@given(
    st.integers(min_value=100, max_value=10000)
)
def test_25_percent_milestone(total_steps):
    """
    Test that 25% milestone triggers notification.
    """
    # Calculate step that crosses 25%
    target_step = int(total_steps * 0.25) + 1
    previous_step = int(total_steps * 0.24)
    
    progress_update = ProgressUpdate(
        current_step=target_step,
        total_steps=total_steps,
        previous_step=previous_step
    )
    
    notification = check_progress_milestone(progress_update)
    
    # Should notify at 25% since we crossed it
    assert notification is not None
    assert notification.milestone == 25


@given(
    st.integers(min_value=100, max_value=10000)
)
def test_50_percent_milestone(total_steps):
    """
    Test that 50% milestone triggers notification.
    """
    # Calculate step that crosses 50%
    target_step = int(total_steps * 0.50) + 1
    previous_step = int(total_steps * 0.49)
    
    progress_update = ProgressUpdate(
        current_step=target_step,
        total_steps=total_steps,
        previous_step=previous_step
    )
    
    notification = check_progress_milestone(progress_update)
    
    # Should notify at 50% since we crossed it
    assert notification is not None
    assert notification.milestone == 50


@given(
    st.integers(min_value=100, max_value=10000)
)
def test_75_percent_milestone(total_steps):
    """
    Test that 75% milestone triggers notification.
    """
    # Calculate step that crosses 75%
    target_step = int(total_steps * 0.75) + 1
    previous_step = int(total_steps * 0.74)
    
    progress_update = ProgressUpdate(
        current_step=target_step,
        total_steps=total_steps,
        previous_step=previous_step
    )
    
    notification = check_progress_milestone(progress_update)
    
    # Should notify at 75% since we crossed it
    assert notification is not None
    assert notification.milestone == 75


def test_no_notification_between_milestones():
    """
    Test that no notification is generated between milestones.
    """
    progress_update = ProgressUpdate(
        current_step=300,
        total_steps=1000,
        previous_step=299
    )
    
    notification = check_progress_milestone(progress_update)
    
    # 30% is between 25% and 50%, should not notify
    assert notification is None


def test_notification_not_repeated_for_same_milestone():
    """
    Test that the same milestone doesn't trigger multiple notifications.
    """
    # Already at 50%, moving to 51%
    progress_update = ProgressUpdate(
        current_step=510,
        total_steps=1000,
        previous_step=500
    )
    
    notification = check_progress_milestone(progress_update)
    
    # Should not notify again for 50% milestone
    assert notification is None
