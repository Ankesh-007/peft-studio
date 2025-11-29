"""
Property-based tests for dataset format detection.
**Feature: simplified-llm-optimization, Property 7: Dataset format detection**
**Validates: Requirements 4.2**
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
get_dataset_service = dataset_service_module.get_dataset_service


def create_sample_csv(file_path: str, num_rows: int = 10):
    """Create a sample CSV file"""
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['text', 'label'])
        writer.writeheader()
        for i in range(num_rows):
            writer.writerow({'text': f'Sample text {i}', 'label': f'label_{i}'})


def create_sample_json(file_path: str, num_items: int = 10):
    """Create a sample JSON file"""
    data = [
        {'text': f'Sample text {i}', 'label': f'label_{i}'}
        for i in range(num_items)
    ]
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f)


def create_sample_jsonl(file_path: str, num_lines: int = 10):
    """Create a sample JSONL file"""
    with open(file_path, 'w', encoding='utf-8') as f:
        for i in range(num_lines):
            obj = {'text': f'Sample text {i}', 'label': f'label_{i}'}
            f.write(json.dumps(obj) + '\n')


def create_sample_txt(file_path: str, num_lines: int = 10):
    """Create a sample TXT file"""
    with open(file_path, 'w', encoding='utf-8') as f:
        for i in range(num_lines):
            f.write(f'Sample text line {i}\n')


# **Feature: simplified-llm-optimization, Property 7: Dataset format detection**
@given(st.sampled_from(['csv', 'json', 'jsonl', 'txt']))
@settings(max_examples=100, deadline=None)
def test_dataset_format_detection(format_type):
    """
    For any valid dataset format, detection should correctly identify it.
    
    This property ensures that the dataset service can accurately detect
    the format of files in CSV, JSON, JSONL, and TXT formats.
    """
    dataset_service = get_dataset_service()
    
    # Create a temporary file with the specified format
    with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{format_type}', delete=False, encoding='utf-8') as f:
        temp_path = f.name
    
    try:
        # Create sample data based on format
        if format_type == 'csv':
            create_sample_csv(temp_path)
        elif format_type == 'json':
            create_sample_json(temp_path)
        elif format_type == 'jsonl':
            create_sample_jsonl(temp_path)
        elif format_type == 'txt':
            create_sample_txt(temp_path)
        
        # Detect format
        detected_format = dataset_service.detect_format(temp_path)
        
        # Verify detection is correct
        assert detected_format == DatasetFormat(format_type), \
            f"Expected format {format_type}, but detected {detected_format.value}"
    
    finally:
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)


@given(
    format_type=st.sampled_from(['csv', 'json', 'jsonl', 'txt']),
    num_samples=st.integers(min_value=1, max_value=100)
)
@settings(max_examples=100, deadline=None)
def test_format_detection_with_varying_sizes(format_type, num_samples):
    """
    For any valid dataset format and sample count, detection should work correctly.
    
    This tests that format detection works regardless of dataset size.
    """
    dataset_service = get_dataset_service()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{format_type}', delete=False, encoding='utf-8') as f:
        temp_path = f.name
    
    try:
        # Create sample data with varying sizes
        if format_type == 'csv':
            create_sample_csv(temp_path, num_samples)
        elif format_type == 'json':
            create_sample_json(temp_path, num_samples)
        elif format_type == 'jsonl':
            create_sample_jsonl(temp_path, num_samples)
        elif format_type == 'txt':
            create_sample_txt(temp_path, num_samples)
        
        detected_format = dataset_service.detect_format(temp_path)
        
        assert detected_format == DatasetFormat(format_type), \
            f"Format detection failed for {format_type} with {num_samples} samples"
    
    finally:
        Path(temp_path).unlink(missing_ok=True)


@given(format_type=st.sampled_from(['csv', 'json', 'jsonl']))
@settings(max_examples=100, deadline=None)
def test_format_detection_without_extension(format_type):
    """
    For structured dataset formats, detection should work even without file extension.
    
    This tests content-based detection when extension hints are not available.
    Note: Plain TXT is excluded as it's ambiguous without extension.
    """
    dataset_service = get_dataset_service()
    
    # Create file without extension
    with tempfile.NamedTemporaryFile(mode='w', suffix='', delete=False, encoding='utf-8') as f:
        temp_path = f.name
    
    try:
        # Create sample data
        if format_type == 'csv':
            create_sample_csv(temp_path)
        elif format_type == 'json':
            create_sample_json(temp_path)
        elif format_type == 'jsonl':
            create_sample_jsonl(temp_path)
        
        detected_format = dataset_service.detect_format(temp_path)
        
        # Should still detect correctly based on content
        assert detected_format == DatasetFormat(format_type), \
            f"Content-based detection failed for {format_type}"
    
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_format_detection_nonexistent_file():
    """Test that detection handles nonexistent files gracefully"""
    dataset_service = get_dataset_service()
    
    detected_format = dataset_service.detect_format('/nonexistent/file.csv')
    
    assert detected_format == DatasetFormat.UNKNOWN, \
        "Should return UNKNOWN for nonexistent files"


def test_format_detection_empty_file():
    """Test that detection handles empty files"""
    dataset_service = get_dataset_service()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        temp_path = f.name
        # Write nothing - empty file
    
    try:
        detected_format = dataset_service.detect_format(temp_path)
        
        # Empty file should still be detected as TXT (since it's valid UTF-8)
        # or UNKNOWN depending on implementation
        assert detected_format in [DatasetFormat.TXT, DatasetFormat.UNKNOWN], \
            "Should handle empty files gracefully"
    
    finally:
        Path(temp_path).unlink(missing_ok=True)
