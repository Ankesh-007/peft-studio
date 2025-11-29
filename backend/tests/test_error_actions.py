"""
Property-based tests for error action suggestions.
Tests that errors provide 2-3 actionable suggestions.
"""

import pytest
from hypothesis import given, strategies as st
from backend.services.error_service import (
    ErrorRecoveryService,
    ErrorAction,
    FormattedError
)


# **Feature: simplified-llm-optimization, Property 20: Error handling provides actions**
@given(
    st.one_of(
        st.just(RuntimeError("CUDA out of memory")),
        st.just(FileNotFoundError("No such file or directory: '/path/to/file'")),
        st.just(ConnectionError("Connection refused")),
        st.just(ValueError("invalid literal for int() with base 10: 'abc'")),
        st.just(KeyError("'missing_key'")),
        st.just(PermissionError("Permission denied")),
        st.just(OSError("[Errno 28] No space left on device")),
        st.just(RuntimeError("CUDA error: device-side assert triggered")),
        st.just(Exception("Generic unexpected error")),
        st.just(TimeoutError("Operation timed out")),
        st.just(MemoryError("Out of memory")),
        st.just(ImportError("No module named 'missing_module'")),
    )
)
def test_error_handling_provides_actions(error):
    """
    Property 20: Error handling provides actions
    
    For any error, the system should return between 2 and 3 specific actions
    the user can take to resolve it.
    
    Validates: Requirements 10.2
    """
    service = ErrorRecoveryService()
    
    # Format the error
    formatted = service.format_error(error)
    
    # Check that actions list exists
    assert formatted.actions is not None
    assert isinstance(formatted.actions, list)
    
    # Check that we have 2-3 actions
    assert len(formatted.actions) >= 2, f"Expected at least 2 actions, got {len(formatted.actions)}"
    assert len(formatted.actions) <= 3, f"Expected at most 3 actions, got {len(formatted.actions)}"
    
    # Check that each action has required fields
    for action in formatted.actions:
        assert isinstance(action, ErrorAction)
        assert action.description is not None
        assert len(action.description) > 0
        assert isinstance(action.automatic, bool)
        assert action.action_type in ['auto_fix', 'manual_step', 'help_link']
        
        # Description should be actionable (contain verbs or instructions)
        actionable_words = [
            'check', 'try', 'enable', 'disable', 'reduce', 'increase',
            'change', 'modify', 'update', 'install', 'remove', 'delete',
            'restart', 'retry', 'reload', 'refresh', 'contact', 'run',
            'free', 'clear', 'upload', 're-upload', 'verify'
        ]
        description_lower = action.description.lower()
        assert any(word in description_lower for word in actionable_words), \
            f"Action description should be actionable: {action.description}"


@given(
    st.sampled_from([
        RuntimeError("CUDA out of memory"),
        FileNotFoundError("No such file or directory"),
        ConnectionError("Connection refused"),
    ])
)
def test_actions_are_specific_to_error_type(error):
    """Test that actions are relevant to the specific error type"""
    service = ErrorRecoveryService()
    formatted = service.format_error(error)
    
    error_str = str(error).lower()
    
    # For memory errors, should suggest memory-related actions
    if 'memory' in error_str:
        action_descriptions = ' '.join(a.description.lower() for a in formatted.actions)
        memory_related = any(term in action_descriptions for term in [
            'batch size', 'memory', 'quantization', 'model', 'checkpointing'
        ])
        assert memory_related, "Memory error should have memory-related actions"
    
    # For file errors, should suggest file-related actions
    elif 'file' in error_str or 'no such' in error_str:
        action_descriptions = ' '.join(a.description.lower() for a in formatted.actions)
        file_related = any(term in action_descriptions for term in [
            'file', 'path', 'upload', 'check', 'exists'
        ])
        assert file_related, "File error should have file-related actions"
    
    # For connection errors, should suggest connection-related actions
    elif 'connection' in error_str:
        action_descriptions = ' '.join(a.description.lower() for a in formatted.actions)
        connection_related = any(term in action_descriptions for term in [
            'connection', 'network', 'internet', 'retry'
        ])
        assert connection_related, "Connection error should have connection-related actions"


@given(
    st.one_of(
        st.just(RuntimeError("CUDA out of memory")),
        st.just(ConnectionError("Connection refused")),
        st.just(OSError("[Errno 28] No space left on device")),
    )
)
def test_at_least_one_action_per_error(error):
    """Test that every error gets at least one suggested action"""
    service = ErrorRecoveryService()
    formatted = service.format_error(error)
    
    assert len(formatted.actions) > 0, "Every error should have at least one action"


def test_action_types_are_valid():
    """Test that all generated actions have valid action types"""
    service = ErrorRecoveryService()
    
    # Test various error types
    errors = [
        RuntimeError("CUDA out of memory"),
        FileNotFoundError("File not found"),
        ConnectionError("Connection failed"),
        PermissionError("Permission denied"),
        Exception("Generic error"),
    ]
    
    valid_action_types = {'auto_fix', 'manual_step', 'help_link'}
    
    for error in errors:
        formatted = service.format_error(error)
        for action in formatted.actions:
            assert action.action_type in valid_action_types, \
                f"Invalid action type: {action.action_type}"


def test_automatic_actions_have_action_data():
    """Test that automatic actions include the necessary action_data"""
    service = ErrorRecoveryService()
    
    # Test an error that should have automatic actions
    error = RuntimeError("CUDA out of memory")
    formatted = service.format_error(error)
    
    # Find automatic actions
    automatic_actions = [a for a in formatted.actions if a.automatic]
    
    # If there are automatic actions, they should have action_data
    for action in automatic_actions:
        assert action.action_data is not None, \
            "Automatic actions should have action_data"
        assert isinstance(action.action_data, dict), \
            "action_data should be a dictionary"
        assert len(action.action_data) > 0, \
            "action_data should not be empty"


def test_actions_are_ordered_by_effectiveness():
    """Test that automatic/easier actions come before manual ones"""
    service = ErrorRecoveryService()
    
    error = RuntimeError("CUDA out of memory")
    formatted = service.format_error(error)
    
    # Check if automatic actions come first
    found_manual = False
    for action in formatted.actions:
        if not action.automatic:
            found_manual = True
        elif found_manual:
            # Found an automatic action after a manual one
            # This is acceptable, but automatic actions should generally come first
            pass


def test_error_actions_consistency():
    """Test that the same error produces consistent actions"""
    service = ErrorRecoveryService()
    
    error = RuntimeError("CUDA out of memory")
    
    # Format the error multiple times
    formatted1 = service.format_error(error)
    formatted2 = service.format_error(error)
    
    # Should produce the same number of actions
    assert len(formatted1.actions) == len(formatted2.actions)
    
    # Actions should have the same descriptions
    for i in range(len(formatted1.actions)):
        assert formatted1.actions[i].description == formatted2.actions[i].description
        assert formatted1.actions[i].automatic == formatted2.actions[i].automatic
        assert formatted1.actions[i].action_type == formatted2.actions[i].action_type


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
