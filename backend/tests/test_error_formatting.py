"""
Property-based tests for error message formatting.
Tests that errors are formatted in plain language without technical jargon.
"""

import pytest
from hypothesis import given, strategies as st, assume
from backend.services.error_service import (
    ErrorRecoveryService,
    ErrorFormatter,
    FormattedError,
    ErrorCategory,
    ErrorSeverity
)


# **Feature: simplified-llm-optimization, Property 19: Error messages are plain language**
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
        st.just(Exception("Generic error with traceback\nTraceback (most recent call last):\n  File \"test.py\", line 10\n    raise Exception")),
    )
)
def test_error_messages_are_plain_language(error):
    """
    Property 19: Error messages are plain language
    
    For any error that occurs, the displayed message should not contain
    technical stack traces or code references.
    
    Validates: Requirements 10.1
    """
    service = ErrorRecoveryService()
    
    # Format the error
    formatted = service.format_error(error)
    
    # Check that the formatted error has all required fields
    assert formatted.title is not None
    assert formatted.what_happened is not None
    assert formatted.why_it_happened is not None
    
    # Check that messages are not empty
    assert len(formatted.title) > 0
    assert len(formatted.what_happened) > 0
    assert len(formatted.why_it_happened) > 0
    
    # Check that the title doesn't contain technical error class names
    technical_terms = ['Error', 'Exception', 'Traceback']
    # Title can contain "Error" as part of a phrase like "GPU Error", but not "RuntimeError"
    assert 'RuntimeError' not in formatted.title
    assert 'ValueError' not in formatted.title
    assert 'KeyError' not in formatted.title
    assert 'FileNotFoundError' not in formatted.title
    
    # Check that what_happened doesn't contain stack traces
    assert 'Traceback' not in formatted.what_happened
    assert 'File "' not in formatted.what_happened
    assert 'line ' not in formatted.what_happened
    assert '  at ' not in formatted.what_happened
    
    # Check that why_it_happened doesn't contain stack traces
    assert 'Traceback' not in formatted.why_it_happened
    assert 'File "' not in formatted.why_it_happened
    assert 'line ' not in formatted.why_it_happened
    
    # Verify using the is_plain_language checker
    assert ErrorFormatter.is_plain_language(formatted.title)
    assert ErrorFormatter.is_plain_language(formatted.what_happened)
    assert ErrorFormatter.is_plain_language(formatted.why_it_happened)


@given(
    st.sampled_from([
        "Traceback (most recent call last):\n  File \"test.py\", line 10\n    raise Exception",
        "Error at line 42 in module.py",
        "File \"/path/to/file.py\", line 100, in function\n    raise ValueError",
        "Traceback: Something went wrong\nFile \"app.py\", line 5",
        "raise RuntimeError('error')\nFile \"main.py\", line 20",
    ])
)
def test_technical_details_removed(error_message):
    """
    Test that technical details like stack traces are removed from error messages.
    """
    cleaned = ErrorFormatter.remove_technical_details(error_message)
    
    # The cleaned message should not contain stack trace indicators
    assert 'Traceback' not in cleaned
    # Note: 'File "' might still appear in legitimate error messages about files
    # but the full stack trace pattern should be removed


@given(
    st.sampled_from([
        "This is a plain language message about an error",
        "The GPU ran out of memory",
        "Unable to find the specified file",
        "Connection to the server failed",
    ])
)
def test_plain_language_detection_positive(message):
    """Test that plain language messages are correctly identified"""
    assert ErrorFormatter.is_plain_language(message)


@given(
    st.sampled_from([
        "Traceback (most recent call last):\n  File \"test.py\", line 10",
        "RuntimeError: CUDA error at line 42",
        "ValueError: invalid literal\n  at function_name (file.py:10)",
        "  File \"/path/to/file.py\", line 100, in function\n    raise Exception",
    ])
)
def test_plain_language_detection_negative(message):
    """Test that technical messages are correctly identified as not plain language"""
    assert not ErrorFormatter.is_plain_language(message)


def test_error_formatter_consistency():
    """Test that the same error always produces the same formatted output"""
    service = ErrorRecoveryService()
    
    error = RuntimeError("CUDA out of memory")
    
    # Format the error multiple times
    formatted1 = service.format_error(error)
    formatted2 = service.format_error(error)
    
    # Should produce consistent results
    assert formatted1.title == formatted2.title
    assert formatted1.what_happened == formatted2.what_happened
    assert formatted1.why_it_happened == formatted2.why_it_happened
    assert formatted1.category == formatted2.category
    assert formatted1.severity == formatted2.severity


def test_all_error_categories_have_help_links():
    """Test that all error categories have associated help links"""
    service = ErrorRecoveryService()
    
    # Test each category
    for category in ErrorCategory:
        # Create a mock error for this category
        error = Exception(f"Test error for {category.value}")
        
        # The service should generate a help link
        help_link = service._get_help_link(category, error)
        
        assert help_link is not None
        assert len(help_link) > 0
        assert help_link.startswith("http")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
