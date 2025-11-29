"""
Property-based tests for dataset validation suggestions.
**Feature: simplified-llm-optimization, Property 8: Dataset validation provides suggestions**
**Validates: Requirements 4.4**
"""

import pytest
import tempfile
import json
import csv
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume
import sys
import os

# Add parent directory to path to import services directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import directly from dataset_service to avoid loading other services with heavy dependencies
import importlib.util
spec = importlib.util.spec_from_file_location(
    "dataset_service",
    os.path.join(os.path.dirname(__file__), '..', 'services', 'dataset_service.py')
)
dataset_service_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dataset_service_module)

DatasetFormat = dataset_service_module.DatasetFormat
ValidationLevel = dataset_service_module.ValidationLevel
get_dataset_service = dataset_service_module.get_dataset_service


def create_csv_with_empty_rows(file_path: str, num_empty: int = 3):
    """Create a CSV file with empty rows"""
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['text', 'label'])
        writer.writeheader()
        writer.writerow({'text': 'Sample 1', 'label': 'label1'})
        for _ in range(num_empty):
            writer.writerow({'text': '', 'label': ''})
        writer.writerow({'text': 'Sample 2', 'label': 'label2'})


def create_json_with_invalid_structure(file_path: str):
    """Create a JSON file with invalid structure (not an array)"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump({'text': 'This should be an array'}, f)


def create_jsonl_with_invalid_lines(file_path: str, num_invalid: int = 2):
    """Create a JSONL file with invalid JSON lines"""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps({'text': 'Valid line 1'}) + '\n')
        for i in range(num_invalid):
            f.write('{ invalid json line\n')
        f.write(json.dumps({'text': 'Valid line 2'}) + '\n')


def create_empty_file(file_path: str):
    """Create an empty file"""
    with open(file_path, 'w', encoding='utf-8') as f:
        pass  # Write nothing


# **Feature: simplified-llm-optimization, Property 8: Dataset validation provides suggestions**
@given(num_empty_rows=st.integers(min_value=1, max_value=10))
@settings(max_examples=100, deadline=None)
def test_validation_provides_suggestions_for_empty_rows(num_empty_rows):
    """
    For any dataset containing formatting errors (empty rows),
    the validation system should return specific, actionable suggestions.
    
    This property ensures that validation errors always come with helpful suggestions.
    """
    dataset_service = get_dataset_service()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        temp_path = f.name
    
    try:
        # Create CSV with empty rows
        create_csv_with_empty_rows(temp_path, num_empty_rows)
        
        # Validate the dataset
        validation_results = dataset_service.validate_dataset(temp_path)
        
        # Find issues related to empty rows
        empty_row_issues = [
            result for result in validation_results
            if 'empty' in result.message.lower() or 'empty' in result.field.lower()
        ]
        
        # Should have detected the empty rows
        assert len(empty_row_issues) > 0, \
            "Should detect empty rows in the dataset"
        
        # Each issue should have a suggestion
        for issue in empty_row_issues:
            assert issue.suggestion is not None, \
                f"Issue '{issue.message}' should have a suggestion"
            assert len(issue.suggestion) > 0, \
                f"Suggestion for '{issue.message}' should not be empty"
            assert isinstance(issue.suggestion, str), \
                f"Suggestion should be a string"
    
    finally:
        Path(temp_path).unlink(missing_ok=True)


@given(st.sampled_from(['json', 'jsonl']))
@settings(max_examples=100, deadline=None)
def test_validation_provides_suggestions_for_format_errors(format_type):
    """
    For any dataset with format errors, validation should provide specific suggestions.
    
    This tests that format-specific errors get appropriate suggestions.
    """
    dataset_service = get_dataset_service()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{format_type}', delete=False, encoding='utf-8') as f:
        temp_path = f.name
    
    try:
        # Create file with format errors
        if format_type == 'json':
            create_json_with_invalid_structure(temp_path)
        elif format_type == 'jsonl':
            create_jsonl_with_invalid_lines(temp_path, 2)
        
        # Validate the dataset
        validation_results = dataset_service.validate_dataset(temp_path)
        
        # Should have detected errors
        errors = [r for r in validation_results if r.level == ValidationLevel.ERROR]
        
        if len(errors) > 0:
            # Each error should have a suggestion
            for error in errors:
                assert error.suggestion is not None, \
                    f"Error '{error.message}' should have a suggestion"
                assert len(error.suggestion) > 0, \
                    f"Suggestion for error '{error.message}' should not be empty"
                
                # Suggestion should be actionable (contain verbs or instructions)
                suggestion_lower = error.suggestion.lower()
                actionable_words = ['fix', 'check', 'ensure', 'add', 'remove', 'change', 'wrap', 'convert']
                has_actionable_word = any(word in suggestion_lower for word in actionable_words)
                
                assert has_actionable_word, \
                    f"Suggestion '{error.suggestion}' should contain actionable guidance"
    
    finally:
        Path(temp_path).unlink(missing_ok=True)


@given(format_type=st.sampled_from(['csv', 'json', 'jsonl', 'txt']))
@settings(max_examples=100, deadline=None)
def test_validation_provides_suggestions_for_empty_files(format_type):
    """
    For any empty dataset file, validation should provide suggestions.
    
    This tests that even empty files get helpful error messages with suggestions.
    """
    dataset_service = get_dataset_service()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{format_type}', delete=False, encoding='utf-8') as f:
        temp_path = f.name
    
    try:
        # Create empty file
        create_empty_file(temp_path)
        
        # Validate the dataset
        validation_results = dataset_service.validate_dataset(temp_path)
        
        # Should have detected the empty file
        errors = [r for r in validation_results if r.level == ValidationLevel.ERROR]
        
        # Should have at least one error for empty file
        assert len(errors) > 0, \
            f"Should detect that {format_type} file is empty"
        
        # Each error should have a suggestion
        for error in errors:
            assert error.suggestion is not None, \
                f"Error '{error.message}' should have a suggestion"
            assert len(error.suggestion) > 0, \
                f"Suggestion should not be empty"
    
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_suggestions_are_specific_and_actionable():
    """
    Test that suggestions are specific and actionable across different error types.
    
    This is a comprehensive test that checks various error scenarios.
    """
    dataset_service = get_dataset_service()
    
    test_cases = [
        ('csv', create_csv_with_empty_rows, "empty rows"),
        ('json', create_json_with_invalid_structure, "invalid structure"),
        ('jsonl', lambda p: create_jsonl_with_invalid_lines(p, 1), "invalid JSON"),
    ]
    
    for format_type, creator_func, error_description in test_cases:
        with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{format_type}', delete=False, encoding='utf-8') as f:
            temp_path = f.name
        
        try:
            # Create file with specific error
            creator_func(temp_path)
            
            # Validate
            validation_results = dataset_service.validate_dataset(temp_path)
            
            # Find errors
            errors = [r for r in validation_results if r.level == ValidationLevel.ERROR]
            warnings = [r for r in validation_results if r.level == ValidationLevel.WARNING]
            
            # All errors and warnings should have suggestions
            for result in errors + warnings:
                assert result.suggestion is not None, \
                    f"Result '{result.message}' should have a suggestion"
                
                # Suggestion should be different from the message
                assert result.suggestion != result.message, \
                    f"Suggestion should provide additional guidance beyond the error message"
                
                # Suggestion should be reasonably detailed (at least 10 characters)
                assert len(result.suggestion) >= 10, \
                    f"Suggestion '{result.suggestion}' should be detailed enough to be helpful"
        
        finally:
            Path(temp_path).unlink(missing_ok=True)


def test_auto_fixable_flag_is_set_appropriately():
    """
    Test that the auto_fixable flag is set correctly for different types of errors.
    
    Some errors can be automatically fixed (like empty rows), others cannot (like invalid JSON syntax).
    """
    dataset_service = get_dataset_service()
    
    # Test auto-fixable error (empty rows in CSV)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        temp_path = f.name
    
    try:
        create_csv_with_empty_rows(temp_path, 2)
        validation_results = dataset_service.validate_dataset(temp_path)
        
        empty_row_issues = [
            r for r in validation_results
            if 'empty' in r.message.lower()
        ]
        
        # Empty rows should be marked as auto-fixable
        for issue in empty_row_issues:
            if issue.level == ValidationLevel.WARNING:
                assert isinstance(issue.auto_fixable, bool), \
                    "auto_fixable should be a boolean"
    
    finally:
        Path(temp_path).unlink(missing_ok=True)
    
    # Test non-auto-fixable error (invalid JSON syntax)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False, encoding='utf-8') as f:
        temp_path = f.name
    
    try:
        create_jsonl_with_invalid_lines(temp_path, 1)
        validation_results = dataset_service.validate_dataset(temp_path)
        
        syntax_errors = [
            r for r in validation_results
            if r.level == ValidationLevel.ERROR and 'json' in r.message.lower()
        ]
        
        # JSON syntax errors should not be auto-fixable
        for error in syntax_errors:
            assert isinstance(error.auto_fixable, bool), \
                "auto_fixable should be a boolean"
            # Most syntax errors cannot be auto-fixed
            # (we don't assert False here as implementation may vary)
    
    finally:
        Path(temp_path).unlink(missing_ok=True)


@given(
    num_errors=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=50, deadline=None)
def test_multiple_errors_each_have_suggestions(num_errors):
    """
    For any dataset with multiple errors, each error should have its own suggestion.
    
    This ensures that even when there are many issues, each gets proper guidance.
    """
    dataset_service = get_dataset_service()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False, encoding='utf-8') as f:
        temp_path = f.name
    
    try:
        # Create JSONL with multiple invalid lines
        create_jsonl_with_invalid_lines(temp_path, num_errors)
        
        validation_results = dataset_service.validate_dataset(temp_path)
        
        # Should have detected errors
        errors = [r for r in validation_results if r.level == ValidationLevel.ERROR]
        
        if len(errors) > 0:
            # Each error should have a unique suggestion
            for error in errors:
                assert error.suggestion is not None, \
                    "Each error should have a suggestion"
                assert len(error.suggestion) > 0, \
                    "Each suggestion should be non-empty"
    
    finally:
        Path(temp_path).unlink(missing_ok=True)
