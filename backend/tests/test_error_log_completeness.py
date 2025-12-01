"""
Property-based tests for error log completeness.

**Feature: unified-llm-platform, Property 16: Error log completeness**
**Validates: Requirements 19.2, 19.5**
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime
from typing import Optional


# Import logging service
try:
    from services.logging_service import (
        get_logging_service,
        LoggingService,
        ErrorLog,
        SystemState,
        ErrorSeverity,
        DiagnosticReport
    )
except ImportError as e:
    pytest.skip(f"Could not import logging service: {e}", allow_module_level=True)


# Strategies for generating test data

# Generate error messages
error_message_strategy = st.text(min_size=1, max_size=500).filter(lambda x: len(x.strip()) > 0)

# Generate error types
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
    "validation_error",
    "configuration_error"
])

# Generate severity levels
severity_strategy = st.sampled_from([
    ErrorSeverity.LOW,
    ErrorSeverity.MEDIUM,
    ErrorSeverity.HIGH,
    ErrorSeverity.CRITICAL
])

# Generate context dictionaries
context_strategy = st.one_of(
    st.none(),
    st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.one_of(
            st.text(max_size=100),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.booleans()
        ),
        max_size=10
    )
)


def create_test_exception(message: str) -> Exception:
    """Create a test exception with a stack trace"""
    try:
        # Create a nested call stack to generate a realistic stack trace
        def inner_function():
            raise ValueError(message)
        
        def middle_function():
            inner_function()
        
        def outer_function():
            middle_function()
        
        outer_function()
    except Exception as e:
        return e


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    error_message=error_message_strategy,
    error_type=error_type_strategy,
    severity=severity_strategy,
    context=context_strategy
)
def test_error_log_contains_timestamp(error_message, error_type, severity, context):
    """
    **Feature: unified-llm-platform, Property 16: Error log completeness**
    **Validates: Requirements 19.2**
    
    For any training error, the error log should include a timestamp.
    """
    # Create logging service
    service = LoggingService()
    
    # Create test exception
    error = create_test_exception(error_message)
    
    # Log the error
    error_log = service.log_error(error, error_type, severity, context)
    
    # Verify timestamp is present
    assert error_log.timestamp is not None, "Error log should have a timestamp"
    assert isinstance(error_log.timestamp, datetime), \
        f"Timestamp should be datetime, got {type(error_log.timestamp)}"
    
    # Verify timestamp is recent (within last minute)
    time_diff = (datetime.now() - error_log.timestamp).total_seconds()
    assert time_diff < 60, \
        f"Timestamp should be recent, but was {time_diff} seconds ago"


@settings(max_examples=100)
@given(
    error_message=error_message_strategy,
    error_type=error_type_strategy,
    severity=severity_strategy,
    context=context_strategy
)
def test_error_log_contains_error_message(error_message, error_type, severity, context):
    """
    **Feature: unified-llm-platform, Property 16: Error log completeness**
    **Validates: Requirements 19.2**
    
    For any training error, the error log should include the error message.
    """
    # Create logging service
    service = LoggingService()
    
    # Create test exception
    error = create_test_exception(error_message)
    
    # Log the error
    error_log = service.log_error(error, error_type, severity, context)
    
    # Verify error message is present
    assert error_log.error_message is not None, "Error log should have an error message"
    assert len(error_log.error_message.strip()) > 0, \
        "Error message should not be empty"
    
    # Verify error message matches the original
    assert error_message in error_log.error_message, \
        f"Error message should contain original message"


@settings(max_examples=100)
@given(
    error_message=error_message_strategy,
    error_type=error_type_strategy,
    severity=severity_strategy,
    context=context_strategy
)
def test_error_log_contains_stack_trace(error_message, error_type, severity, context):
    """
    **Feature: unified-llm-platform, Property 16: Error log completeness**
    **Validates: Requirements 19.2**
    
    For any training error, the error log should include a complete stack trace.
    """
    # Create logging service
    service = LoggingService()
    
    # Create test exception
    error = create_test_exception(error_message)
    
    # Log the error
    error_log = service.log_error(error, error_type, severity, context)
    
    # Verify stack trace is present
    assert error_log.stack_trace is not None, "Error log should have a stack trace"
    assert len(error_log.stack_trace.strip()) > 0, \
        "Stack trace should not be empty"
    
    # Verify stack trace contains expected elements
    assert "Traceback" in error_log.stack_trace, \
        "Stack trace should contain 'Traceback'"
    assert "File" in error_log.stack_trace, \
        "Stack trace should contain file references"
    assert "line" in error_log.stack_trace, \
        "Stack trace should contain line numbers"


@settings(max_examples=100)
@given(
    error_message=error_message_strategy,
    error_type=error_type_strategy,
    severity=severity_strategy,
    context=context_strategy
)
def test_error_log_contains_system_state(error_message, error_type, severity, context):
    """
    **Feature: unified-llm-platform, Property 16: Error log completeness**
    **Validates: Requirements 19.2**
    
    For any training error, the error log should include system state information.
    """
    # Create logging service
    service = LoggingService()
    
    # Create test exception
    error = create_test_exception(error_message)
    
    # Log the error
    error_log = service.log_error(error, error_type, severity, context)
    
    # Verify system state is present
    assert error_log.system_state is not None, "Error log should have system state"
    assert isinstance(error_log.system_state, SystemState), \
        f"System state should be SystemState, got {type(error_log.system_state)}"
    
    # Verify system state has required fields
    assert error_log.system_state.timestamp is not None, \
        "System state should have timestamp"
    assert error_log.system_state.platform is not None, \
        "System state should have platform"
    assert len(error_log.system_state.platform.strip()) > 0, \
        "Platform should not be empty"
    assert error_log.system_state.python_version is not None, \
        "System state should have Python version"
    assert len(error_log.system_state.python_version.strip()) > 0, \
        "Python version should not be empty"


@settings(max_examples=100)
@given(
    error_message=error_message_strategy,
    error_type=error_type_strategy,
    severity=severity_strategy,
    context=context_strategy
)
def test_error_log_is_complete(error_message, error_type, severity, context):
    """
    **Feature: unified-llm-platform, Property 16: Error log completeness**
    **Validates: Requirements 19.2, 19.5**
    
    For any training error, the error log should be complete with all required fields:
    - timestamp
    - error message
    - stack trace
    - system state
    """
    # Create logging service
    service = LoggingService()
    
    # Create test exception
    error = create_test_exception(error_message)
    
    # Log the error
    error_log = service.log_error(error, error_type, severity, context)
    
    # Verify error log is complete
    assert error_log.is_complete(), \
        "Error log should be complete with all required fields"
    
    # Verify all required fields are present and non-empty
    assert error_log.timestamp is not None
    assert error_log.error_message is not None
    assert len(error_log.error_message.strip()) > 0
    assert error_log.stack_trace is not None
    assert len(error_log.stack_trace.strip()) > 0
    assert error_log.system_state is not None
    assert error_log.system_state.timestamp is not None
    assert error_log.system_state.platform is not None
    assert len(error_log.system_state.platform.strip()) > 0
    assert error_log.system_state.python_version is not None
    assert len(error_log.system_state.python_version.strip()) > 0


@settings(max_examples=100)
@given(
    error_message=error_message_strategy,
    error_type=error_type_strategy,
    severity=severity_strategy,
    context=context_strategy
)
def test_error_log_serialization(error_message, error_type, severity, context):
    """
    For any error log, it should be serializable to a dictionary for storage/export.
    """
    # Create logging service
    service = LoggingService()
    
    # Create test exception
    error = create_test_exception(error_message)
    
    # Log the error
    error_log = service.log_error(error, error_type, severity, context)
    
    # Serialize to dictionary
    log_dict = error_log.to_dict()
    
    # Verify dictionary contains all required fields
    assert "timestamp" in log_dict
    assert "error_message" in log_dict
    assert "stack_trace" in log_dict
    assert "system_state" in log_dict
    assert "error_type" in log_dict
    assert "severity" in log_dict
    
    # Verify system state is also serialized
    assert isinstance(log_dict["system_state"], dict)
    assert "timestamp" in log_dict["system_state"]
    assert "platform" in log_dict["system_state"]
    assert "python_version" in log_dict["system_state"]


@settings(max_examples=50, deadline=None)
@given(
    num_errors=st.integers(min_value=1, max_value=10),
    error_type=error_type_strategy
)
def test_diagnostic_report_includes_all_errors(num_errors, error_type):
    """
    **Feature: unified-llm-platform, Property 16: Error log completeness**
    **Validates: Requirements 19.2, 19.5**
    
    For any set of training errors, the diagnostic report should include all error logs.
    """
    # Create logging service
    service = LoggingService()
    
    # Log multiple errors
    for i in range(num_errors):
        error = create_test_exception(f"Test error {i}")
        service.log_error(error, error_type, ErrorSeverity.MEDIUM)
    
    # Generate diagnostic report
    report = service.generate_diagnostic_report()
    
    # Verify report contains all errors
    assert len(report.error_logs) == num_errors, \
        f"Diagnostic report should contain {num_errors} errors, got {len(report.error_logs)}"
    
    # Verify all error logs are complete
    for error_log in report.error_logs:
        assert error_log.is_complete(), \
            "All error logs in diagnostic report should be complete"


@settings(max_examples=50)
@given(
    error_message=error_message_strategy,
    error_type=error_type_strategy
)
def test_diagnostic_report_has_required_fields(error_message, error_type):
    """
    **Feature: unified-llm-platform, Property 16: Error log completeness**
    **Validates: Requirements 19.2, 19.5**
    
    For any diagnostic report, it should contain all required fields for troubleshooting.
    """
    # Create logging service
    service = LoggingService()
    
    # Log an error
    error = create_test_exception(error_message)
    service.log_error(error, error_type, ErrorSeverity.MEDIUM)
    
    # Generate diagnostic report
    report = service.generate_diagnostic_report(
        configuration={"model": "test-model", "batch_size": 4},
        environment_info={"platform": "test"}
    )
    
    # Verify report has required fields
    assert report.report_id is not None, "Report should have an ID"
    assert len(report.report_id) > 0, "Report ID should not be empty"
    
    assert report.generated_at is not None, "Report should have generation timestamp"
    assert isinstance(report.generated_at, datetime), \
        "Generation timestamp should be datetime"
    
    assert report.error_logs is not None, "Report should have error logs"
    assert len(report.error_logs) > 0, "Report should contain at least one error log"
    
    assert report.configuration is not None, "Report should have configuration"
    assert isinstance(report.configuration, dict), "Configuration should be a dictionary"
    
    assert report.environment_info is not None, "Report should have environment info"
    assert isinstance(report.environment_info, dict), "Environment info should be a dictionary"
    
    assert report.recent_operations is not None, "Report should have recent operations"
    assert isinstance(report.recent_operations, list), "Recent operations should be a list"


@settings(max_examples=50)
@given(
    error_message=error_message_strategy,
    error_type=error_type_strategy,
    num_actions=st.integers(min_value=1, max_value=20)
)
def test_error_log_includes_recent_actions(error_message, error_type, num_actions):
    """
    **Feature: unified-llm-platform, Property 16: Error log completeness**
    **Validates: Requirements 19.2**
    
    For any training error, the error log should include recent user actions.
    """
    # Create logging service
    service = LoggingService()
    
    # Track some actions
    actions = []
    for i in range(num_actions):
        action = f"Action {i}: test action"
        service.track_action(action)
        actions.append(action)
    
    # Log an error
    error = create_test_exception(error_message)
    error_log = service.log_error(error, error_type, ErrorSeverity.MEDIUM)
    
    # Verify error log includes recent actions
    assert error_log.recent_actions is not None, \
        "Error log should include recent actions"
    assert isinstance(error_log.recent_actions, list), \
        "Recent actions should be a list"
    
    # Verify actions are captured (at least some of them)
    assert len(error_log.recent_actions) > 0, \
        "Error log should contain at least one recent action"
    
    # Verify actions contain expected content
    for action in error_log.recent_actions:
        assert "Action" in action or "test action" in action, \
            f"Action should contain expected content: {action}"


@settings(max_examples=50)
@given(
    error_message=error_message_strategy,
    error_type=error_type_strategy,
    severity=severity_strategy
)
def test_error_log_preserves_context(error_message, error_type, severity):
    """
    For any error with context, the error log should preserve the context information.
    """
    # Create logging service
    service = LoggingService()
    
    # Create context
    context = {
        "job_id": "test-job-123",
        "model_name": "test-model",
        "batch_size": 4,
        "epoch": 2
    }
    
    # Create test exception
    error = create_test_exception(error_message)
    
    # Log the error with context
    error_log = service.log_error(error, error_type, severity, context)
    
    # Verify context is preserved
    assert error_log.context is not None, "Error log should have context"
    assert error_log.context == context, \
        "Error log context should match original context"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
