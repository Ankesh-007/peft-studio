"""
Property-based tests for dataset format acceptance.
**Feature: simplified-llm-optimization, Property 6: Dataset format acceptance**
**Validates: Requirements 4.1**
"""

import pytest
import tempfile
import json
import csv
from pathlib import Path
from hypothesis import given, strategies as st, settings
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


def create_valid_csv(file_path: str, num_rows: int = 10):
    """Create a valid CSV file"""
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['text', 'label'])
        writer.writeheader()
        for i in range(num_rows):
            writer.writerow({'text': f'Sample text {i}', 'label': f'label_{i}'})


def create_valid_json(file_path: str, num_items: int = 10):
    """Create a valid JSON file"""
    data = [
        {'text': f'Sample text {i}', 'label': f'label_{i}'}
        for i in range(num_items)
    ]
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f)


def create_valid_jsonl(file_path: str, num_lines: int = 10):
    """Create a valid JSONL file"""
    with open(file_path, 'w', encoding='utf-8') as f:
        for i in range(num_lines):
            obj = {'text': f'Sample text {i}', 'label': f'label_{i}'}
            f.write(json.dumps(obj) + '\n')


def create_valid_txt(file_path: str, num_lines: int = 10):
    """Create a valid TXT file"""
    with open(file_path, 'w', encoding='utf-8') as f:
        for i in range(num_lines):
            f.write(f'Sample text line {i}\n')


# **Feature: simplified-llm-optimization, Property 6: Dataset format acceptance**
@given(st.sampled_from(['csv', 'json', 'jsonl', 'txt']))
@settings(max_examples=100, deadline=None)
def test_dataset_format_acceptance(format_type):
    """
    For any file in CSV, JSON, JSONL, or plain text format,
    the upload system should successfully accept and process the file.
    
    This property ensures that all supported formats are properly accepted
    without critical errors.
    """
    dataset_service = get_dataset_service()
    
    # Create a temporary file with the specified format
    with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{format_type}', delete=False, encoding='utf-8') as f:
        temp_path = f.name
    
    try:
        # Create valid sample data based on format
        if format_type == 'csv':
            create_valid_csv(temp_path)
        elif format_type == 'json':
            create_valid_json(temp_path)
        elif format_type == 'jsonl':
            create_valid_jsonl(temp_path)
        elif format_type == 'txt':
            create_valid_txt(temp_path)
        
        # Validate the dataset - should not raise exceptions
        validation_results = dataset_service.validate_dataset(temp_path)
        
        # Should not have any critical errors that prevent processing
        critical_errors = [
            result for result in validation_results
            if result.level == ValidationLevel.ERROR
        ]
        
        # Valid files should have no critical errors
        assert len(critical_errors) == 0, \
            f"Valid {format_type} file should not have critical errors: {critical_errors}"
        
        # Should be able to generate preview
        preview = dataset_service.generate_preview(temp_path, num_samples=3)
        assert preview is not None, f"Should be able to generate preview for {format_type}"
        assert preview.format == DatasetFormat(format_type), \
            f"Preview format should match {format_type}"
        
        # Should be able to analyze statistics
        stats = dataset_service.analyze_statistics(temp_path)
        assert stats is not None, f"Should be able to analyze statistics for {format_type}"
        assert stats.num_samples > 0, f"Should detect samples in {format_type} file"
    
    finally:
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)


@given(
    format_type=st.sampled_from(['csv', 'json', 'jsonl', 'txt']),
    num_samples=st.integers(min_value=1, max_value=100)
)
@settings(max_examples=100, deadline=None)
def test_format_acceptance_with_varying_sizes(format_type, num_samples):
    """
    For any supported format and sample count, the system should accept and process the file.
    
    This tests that format acceptance works regardless of dataset size.
    """
    dataset_service = get_dataset_service()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{format_type}', delete=False, encoding='utf-8') as f:
        temp_path = f.name
    
    try:
        # Create sample data with varying sizes
        if format_type == 'csv':
            create_valid_csv(temp_path, num_samples)
        elif format_type == 'json':
            create_valid_json(temp_path, num_samples)
        elif format_type == 'jsonl':
            create_valid_jsonl(temp_path, num_samples)
        elif format_type == 'txt':
            create_valid_txt(temp_path, num_samples)
        
        # Should be able to process without exceptions
        validation_results = dataset_service.validate_dataset(temp_path)
        
        # Check that we can get statistics
        stats = dataset_service.analyze_statistics(temp_path)
        assert stats.num_samples == num_samples, \
            f"Should correctly count {num_samples} samples in {format_type}"
    
    finally:
        Path(temp_path).unlink(missing_ok=True)


@given(format_type=st.sampled_from(['csv', 'json', 'jsonl', 'txt']))
@settings(max_examples=100, deadline=None)
def test_quality_check_acceptance(format_type):
    """
    For any supported format, the quality check should complete successfully.
    
    This tests that the comprehensive quality check works for all formats.
    """
    dataset_service = get_dataset_service()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{format_type}', delete=False, encoding='utf-8') as f:
        temp_path = f.name
    
    try:
        # Create valid sample data
        if format_type == 'csv':
            create_valid_csv(temp_path, 20)  # Use enough samples for good quality
        elif format_type == 'json':
            create_valid_json(temp_path, 20)
        elif format_type == 'jsonl':
            create_valid_jsonl(temp_path, 20)
        elif format_type == 'txt':
            create_valid_txt(temp_path, 20)
        
        # Should be able to run quality check
        quality_report = dataset_service.check_quality(temp_path)
        
        assert quality_report is not None, f"Should generate quality report for {format_type}"
        assert 0 <= quality_report.overall_score <= 100, \
            f"Quality score should be between 0 and 100 for {format_type}"
        assert isinstance(quality_report.issues, list), \
            f"Issues should be a list for {format_type}"
        assert isinstance(quality_report.recommendations, list), \
            f"Recommendations should be a list for {format_type}"
        assert isinstance(quality_report.is_ready_for_training, bool), \
            f"is_ready_for_training should be boolean for {format_type}"
    
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_acceptance_with_unicode_content():
    """Test that files with Unicode content are accepted"""
    dataset_service = get_dataset_service()
    
    # Test with various Unicode characters
    unicode_texts = [
        "Hello 世界",  # Chinese
        "Привет мир",  # Russian
        "مرحبا بالعالم",  # Arabic
        "🎉 Emoji test 🚀",  # Emoji
    ]
    
    for format_type in ['csv', 'json', 'jsonl', 'txt']:
        with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{format_type}', delete=False, encoding='utf-8') as f:
            temp_path = f.name
        
        try:
            if format_type == 'csv':
                with open(temp_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=['text'])
                    writer.writeheader()
                    for text in unicode_texts:
                        writer.writerow({'text': text})
            
            elif format_type == 'json':
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump([{'text': text} for text in unicode_texts], f, ensure_ascii=False)
            
            elif format_type == 'jsonl':
                with open(temp_path, 'w', encoding='utf-8') as f:
                    for text in unicode_texts:
                        f.write(json.dumps({'text': text}, ensure_ascii=False) + '\n')
            
            elif format_type == 'txt':
                with open(temp_path, 'w', encoding='utf-8') as f:
                    for text in unicode_texts:
                        f.write(text + '\n')
            
            # Should accept and process Unicode content
            validation_results = dataset_service.validate_dataset(temp_path)
            stats = dataset_service.analyze_statistics(temp_path)
            
            # Should have at least the expected number of samples
            # (allowing for minor variations in how formats handle empty lines)
            assert stats.num_samples >= len(unicode_texts), \
                f"Should correctly process Unicode content in {format_type} (got {stats.num_samples}, expected at least {len(unicode_texts)})"
            
            # Should not have too many extra samples (max 1 extra for potential blank lines)
            assert stats.num_samples <= len(unicode_texts) + 1, \
                f"Should not have excessive samples in {format_type} (got {stats.num_samples}, expected around {len(unicode_texts)})"
        
        finally:
            Path(temp_path).unlink(missing_ok=True)
