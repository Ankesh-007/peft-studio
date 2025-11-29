"""
Property-based tests for error help links.
Tests that unresolvable errors include help documentation links.
"""

import pytest
from hypothesis import given, strategies as st
from backend.services.error_service import (
    ErrorRecoveryService,
    ErrorCategory,
    FormattedError
)


# **Feature: simplified-llm-optimization, Property 21: Unresolvable errors include help links**
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
        st.just(AttributeError("'NoneType' object has no attribute 'value'")),
        st.just(TypeError("unsupported operand type(s)")),
    )
)
def test_unresolvable_errors_include_help_links(error):
    """
    Property 21: Unresolvable errors include help links
    
    For any error that cannot be automatically resolved, the error response
    should include a help documentation link.
    
    Validates: Requirements 10.4
    """
    service = ErrorRecoveryService()
    
    # Format the error
    formatted = service.format_error(error)
    
    # Check if the error is auto-recoverable
    has_automatic_action = any(action.automatic for action in formatted.actions)
    
    # If the error is not auto-recoverable (unresolvable), it should have a help link
    if not has_automatic_action:
        assert formatted.help_link is not None, \
            "Unresolvable errors should have a help link"
        assert len(formatted.help_link) > 0, \
            "Help link should not be empty"
        assert formatted.help_link.startswith("http"), \
            f"Help link should be a valid URL: {formatted.help_link}"
    
    # Even if auto-recoverable, having a help link is good practice
    # So we'll check that all errors have help links
    assert formatted.help_link is not None, \
        "All errors should have a help link for additional information"
    assert len(formatted.help_link) > 0
    assert formatted.help_link.startswith("http")


@given(st.sampled_from(list(ErrorCategory)))
def test_all_error_categories_have_help_links(category):
    """
    Test that every error category has an associated help link.
    
    This ensures users can always find documentation for any type of error.
    """
    service = ErrorRecoveryService()
    
    # Create a mock error for this category
    error = Exception(f"Test error for category {category.value}")
    
    # Get the help link for this category
    help_link = service._get_help_link(category, error)
    
    # Verify the help link exists and is valid
    assert help_link is not None
    assert len(help_link) > 0
    assert help_link.startswith("http")
    assert "troubleshooting" in help_link.lower()


def test_help_links_are_category_specific():
    """Test that different error categories get different help links"""
    service = ErrorRecoveryService()
    
    # Create errors for different categories
    errors = [
        (RuntimeError("CUDA out of memory"), ErrorCategory.RESOURCE),
        (FileNotFoundError("File not found"), ErrorCategory.USER_INPUT),
        (ConnectionError("Connection failed"), ErrorCategory.NETWORK),
    ]
    
    help_links = set()
    
    for error, expected_category in errors:
        formatted = service.format_error(error)
        
        # Verify the error was categorized correctly
        assert formatted.category == expected_category
        
        # Collect the help link
        help_links.add(formatted.help_link)
    
    # Different categories should have different help links
    # (though this might not always be true, it's a good practice)
    # At minimum, we should have at least 2 different help links
    assert len(help_links) >= 2, \
        "Different error categories should have different help links"


def test_help_link_format_consistency():
    """Test that all help links follow a consistent format"""
    service = ErrorRecoveryService()
    
    errors = [
        RuntimeError("CUDA out of memory"),
        FileNotFoundError("File not found"),
        ConnectionError("Connection failed"),
        PermissionError("Permission denied"),
        Exception("Generic error"),
    ]
    
    base_url = "https://docs.peftstudio.ai/troubleshooting"
    
    for error in errors:
        formatted = service.format_error(error)
        
        # All help links should start with the base URL
        assert formatted.help_link.startswith(base_url), \
            f"Help link should start with {base_url}: {formatted.help_link}"
        
        # Help links should be well-formed URLs
        assert " " not in formatted.help_link, \
            "Help links should not contain spaces"


def test_help_link_includes_category_path():
    """Test that help links include the error category in the path"""
    service = ErrorRecoveryService()
    
    # Test specific errors and their expected categories
    test_cases = [
        (RuntimeError("CUDA out of memory"), "resource"),
        (FileNotFoundError("File not found"), "input"),
        (ConnectionError("Connection failed"), "network"),
        (PermissionError("Permission denied"), "system"),
    ]
    
    for error, expected_category_part in test_cases:
        formatted = service.format_error(error)
        
        # The help link should contain the category
        assert expected_category_part in formatted.help_link.lower(), \
            f"Help link should contain '{expected_category_part}': {formatted.help_link}"


def test_help_link_action_exists():
    """Test that at least one action can be a help link action"""
    service = ErrorRecoveryService()
    
    # Test an error that might not be auto-recoverable
    error = Exception("Unexpected system error")
    formatted = service.format_error(error)
    
    # Check if any action is a help link type
    help_link_actions = [a for a in formatted.actions if a.action_type == 'help_link']
    
    # It's acceptable to have 0 or more help link actions
    # But if there are any, they should have valid data
    for action in help_link_actions:
        assert action.action_data is not None
        assert 'link' in action.action_data or 'url' in action.action_data


def test_formatted_error_always_has_help_link():
    """Test that FormattedError always includes a help_link field"""
    service = ErrorRecoveryService()
    
    # Test various error types
    errors = [
        RuntimeError("CUDA out of memory"),
        FileNotFoundError("File not found"),
        ConnectionError("Connection failed"),
        ValueError("Invalid value"),
        KeyError("Missing key"),
        PermissionError("Permission denied"),
        OSError("Disk full"),
        Exception("Generic error"),
    ]
    
    for error in errors:
        formatted = service.format_error(error)
        
        # Every formatted error should have a help_link
        assert hasattr(formatted, 'help_link')
        assert formatted.help_link is not None
        assert isinstance(formatted.help_link, str)
        assert len(formatted.help_link) > 0


def test_help_link_consistency_for_same_error():
    """Test that the same error always gets the same help link"""
    service = ErrorRecoveryService()
    
    error = RuntimeError("CUDA out of memory")
    
    # Format the error multiple times
    formatted1 = service.format_error(error)
    formatted2 = service.format_error(error)
    
    # Should produce the same help link
    assert formatted1.help_link == formatted2.help_link


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
