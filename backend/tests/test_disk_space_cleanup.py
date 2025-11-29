"""
Property-based tests for disk space monitoring and cleanup prompts.

**Feature: simplified-llm-optimization, Property 31: Low disk space triggers cleanup prompt**
**Validates: Requirements 14.5**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from pathlib import Path
import tempfile
import shutil
from contextlib import contextmanager

from backend.services.model_versioning_service import (
    ModelVersioningService,
    DiskSpaceInfo
)


@contextmanager
def temp_service_context():
    """Context manager for temporary model versioning service"""
    temp_dir = tempfile.mkdtemp()
    try:
        service = ModelVersioningService(base_path=temp_dir)
        yield service
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@contextmanager
def temp_checkpoint_context():
    """Context manager for temporary checkpoint file"""
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pt')
    # Write some data to make it non-zero size
    temp_file.write("dummy checkpoint data" * 1000)
    temp_file.close()
    try:
        yield temp_file.name
    finally:
        Path(temp_file.name).unlink(missing_ok=True)


@pytest.fixture
def temp_service():
    """Create a temporary model versioning service for testing"""
    temp_dir = tempfile.mkdtemp()
    service = ModelVersioningService(base_path=temp_dir)
    yield service
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_checkpoint():
    """Create a temporary checkpoint file for testing"""
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pt')
    # Write some data to make it non-zero size
    temp_file.write("dummy checkpoint data" * 1000)
    temp_file.close()
    yield temp_file.name
    # Cleanup
    Path(temp_file.name).unlink(missing_ok=True)


# **Feature: simplified-llm-optimization, Property 31: Low disk space triggers cleanup prompt**
def test_disk_space_info_includes_all_fields():
    """
    Property: For any system state, disk space info should include
    total, used, available bytes, percent used, and versions total size.
    """
    with temp_service_context() as temp_service:
        disk_info = temp_service.get_disk_space_info()
        
        # Verify all required fields are present
        assert hasattr(disk_info, 'total_bytes')
        assert hasattr(disk_info, 'used_bytes')
        assert hasattr(disk_info, 'available_bytes')
        assert hasattr(disk_info, 'percent_used')
        assert hasattr(disk_info, 'versions_total_size')
        
        # Verify values are valid
        assert disk_info.total_bytes > 0
        assert disk_info.used_bytes >= 0
        assert disk_info.available_bytes >= 0
        assert 0 <= disk_info.percent_used <= 100
        assert disk_info.versions_total_size >= 0
        
        # Verify basic disk space math
        assert disk_info.used_bytes + disk_info.available_bytes <= disk_info.total_bytes * 1.1  # Allow 10% margin


# **Feature: simplified-llm-optimization, Property 31: Low disk space triggers cleanup prompt**
@given(
    num_versions=st.integers(min_value=1, max_value=20)
)
@settings(max_examples=50, deadline=None)
def test_versions_total_size_reflects_all_versions(num_versions):
    """
    Property: For any number of created versions, the versions_total_size
    should reflect the sum of all version sizes.
    """
    with temp_service_context() as temp_service, temp_checkpoint_context() as temp_checkpoint:
        model_name = "test_model"
        
        # Create multiple versions
        expected_total = 0
        for i in range(num_versions):
            version = temp_service.create_version(
                model_name=model_name,
                checkpoint_path=temp_checkpoint,
                config={'iteration': i},
                metrics={'loss': 1.0}
            )
            expected_total += version.size_bytes
        
        # Get disk space info
        disk_info = temp_service.get_disk_space_info()
        
        # Verify total size matches sum of all versions
        assert disk_info.versions_total_size == expected_total


# **Feature: simplified-llm-optimization, Property 31: Low disk space triggers cleanup prompt**
def test_should_prompt_cleanup_when_space_low():
    """
    Property: When available disk space falls below threshold,
    should_prompt_cleanup should return True.
    """
    with temp_service_context() as temp_service:
        # Get current disk info
        disk_info = temp_service.get_disk_space_info()
        
        # Check if cleanup should be prompted
        should_prompt = temp_service.should_prompt_cleanup()
        
        # Verify logic: should prompt if available < threshold
        threshold = disk_info.low_space_threshold
        expected_prompt = disk_info.available_bytes < threshold
        
        assert should_prompt == expected_prompt


# **Feature: simplified-llm-optimization, Property 31: Low disk space triggers cleanup prompt**
@given(
    num_versions=st.integers(min_value=5, max_value=20),
    keep_latest=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=50, deadline=None)
def test_cleanup_candidates_excludes_latest_versions(num_versions, keep_latest):
    """
    Property: For any model with N versions, get_cleanup_candidates with
    keep_latest=K should return N-K versions (the older ones).
    """
    assume(num_versions > keep_latest)
    
    with temp_service_context() as temp_service, temp_checkpoint_context() as temp_checkpoint:
        model_name = "test_model"
        
        # Create versions
        for i in range(num_versions):
            temp_service.create_version(
                model_name=model_name,
                checkpoint_path=temp_checkpoint,
                config={'iteration': i},
                metrics={'loss': 1.0}
            )
        
        # Get cleanup candidates
        candidates = temp_service.get_cleanup_candidates(
            model_name=model_name,
            keep_latest=keep_latest
        )
        
        # Verify correct number of candidates
        expected_candidates = num_versions - keep_latest
        assert len(candidates) == expected_candidates
        
        # Verify candidates are the older versions
        all_versions = temp_service.list_versions(model_name)
        latest_versions = all_versions[:keep_latest]
        
        # None of the latest versions should be in candidates
        latest_ids = {v.id for v in latest_versions}
        candidate_ids = {v.id for v in candidates}
        
        assert len(latest_ids & candidate_ids) == 0  # No overlap


# **Feature: simplified-llm-optimization, Property 31: Low disk space triggers cleanup prompt**
@given(
    num_versions=st.integers(min_value=3, max_value=10),
    keep_latest=st.integers(min_value=1, max_value=3)
)
@settings(max_examples=50, deadline=None)
def test_cleanup_candidates_include_size_information(num_versions, keep_latest):
    """
    Property: For any cleanup candidates, each should include size information
    so users can make informed decisions about what to delete.
    """
    assume(num_versions > keep_latest)
    
    with temp_service_context() as temp_service, temp_checkpoint_context() as temp_checkpoint:
        model_name = "test_model"
        
        # Create versions
        for i in range(num_versions):
            temp_service.create_version(
                model_name=model_name,
                checkpoint_path=temp_checkpoint,
                config={'iteration': i},
                metrics={'loss': 1.0}
            )
        
        # Get cleanup candidates
        candidates = temp_service.get_cleanup_candidates(
            model_name=model_name,
            keep_latest=keep_latest
        )
        
        # Verify all candidates have size information
        for candidate in candidates:
            assert hasattr(candidate, 'size_bytes')
            assert candidate.size_bytes > 0


# **Feature: simplified-llm-optimization, Property 31: Low disk space triggers cleanup prompt**
@given(
    num_versions=st.integers(min_value=3, max_value=10)
)
@settings(max_examples=50, deadline=None)
def test_delete_version_reduces_total_size(num_versions):
    """
    Property: For any version deletion, the versions_total_size should
    decrease by the size of the deleted version.
    """
    with temp_service_context() as temp_service, temp_checkpoint_context() as temp_checkpoint:
        model_name = "test_model"
        
        # Create versions
        for i in range(num_versions):
            temp_service.create_version(
                model_name=model_name,
                checkpoint_path=temp_checkpoint,
                config={'iteration': i},
                metrics={'loss': 1.0}
            )
        
        # Get initial disk info
        initial_info = temp_service.get_disk_space_info()
        initial_size = initial_info.versions_total_size
        
        # Get a version to delete
        versions = temp_service.list_versions(model_name)
        version_to_delete = versions[-1]  # Delete oldest
        deleted_size = version_to_delete.size_bytes
        
        # Delete the version
        success = temp_service.delete_version(model_name, version_to_delete.version)
        assert success
        
        # Get new disk info
        new_info = temp_service.get_disk_space_info()
        new_size = new_info.versions_total_size
        
        # Verify size decreased by deleted version size
        assert new_size == initial_size - deleted_size


# **Feature: simplified-llm-optimization, Property 31: Low disk space triggers cleanup prompt**
@given(
    num_models=st.integers(min_value=2, max_value=5),
    versions_per_model=st.integers(min_value=3, max_value=8),
    keep_latest=st.integers(min_value=1, max_value=3)
)
@settings(max_examples=30, deadline=None)
def test_cleanup_candidates_across_multiple_models(num_models, versions_per_model, keep_latest):
    """
    Property: For any set of models with versions, get_cleanup_candidates
    without model_name filter should return candidates from all models.
    """
    assume(versions_per_model > keep_latest)
    
    with temp_service_context() as temp_service, temp_checkpoint_context() as temp_checkpoint:
        # Create multiple models with versions
        model_names = [f"model_{i}" for i in range(num_models)]
        
        for model_name in model_names:
            for i in range(versions_per_model):
                temp_service.create_version(
                    model_name=model_name,
                    checkpoint_path=temp_checkpoint,
                    config={'iteration': i},
                    metrics={'loss': 1.0}
                )
        
        # Get cleanup candidates for all models
        candidates = temp_service.get_cleanup_candidates(keep_latest=keep_latest)
        
        # Verify we get candidates from all models
        expected_total = num_models * (versions_per_model - keep_latest)
        assert len(candidates) == expected_total
        
        # Verify candidates come from all models
        candidate_models = {c.model_name for c in candidates}
        assert candidate_models == set(model_names)


# **Feature: simplified-llm-optimization, Property 31: Low disk space triggers cleanup prompt**
@given(
    num_versions=st.integers(min_value=3, max_value=10)
)
@settings(max_examples=50, deadline=None)
def test_archive_versions_preserves_metadata(num_versions):
    """
    Property: For any versions that are archived, their metadata should
    be preserved (only checkpoint location changes).
    """
    with temp_service_context() as temp_service, temp_checkpoint_context() as temp_checkpoint:
        model_name = "test_model"
        
        # Create versions
        original_versions = []
        for i in range(num_versions):
            version = temp_service.create_version(
                model_name=model_name,
                checkpoint_path=temp_checkpoint,
                config={'iteration': i},
                metrics={'loss': 1.0}
            )
            original_versions.append(version)
        
        # Get versions to archive (all but latest 2)
        versions_to_archive = temp_service.get_cleanup_candidates(
            model_name=model_name,
            keep_latest=2
        )
        
        if len(versions_to_archive) == 0:
            return  # Skip if no versions to archive
        
        # Archive versions
        success = temp_service.archive_versions(versions_to_archive)
        assert success
        
        # Verify metadata is preserved
        for archived_version in versions_to_archive:
            # Find original version
            original = next(v for v in original_versions if v.id == archived_version.id)
            
            # Verify metadata unchanged (except checkpoint_path)
            assert archived_version.id == original.id
            assert archived_version.model_name == original.model_name
            assert archived_version.version == original.version
            assert archived_version.config == original.config
            assert archived_version.metrics == original.metrics
            assert archived_version.size_bytes == original.size_bytes
            
            # Checkpoint path should have changed to archive location
            assert 'archive' in archived_version.checkpoint_path


# **Feature: simplified-llm-optimization, Property 31: Low disk space triggers cleanup prompt**
def test_get_cleanup_candidates_with_no_versions_returns_empty():
    """
    Property: For any model with no versions, get_cleanup_candidates
    should return an empty list.
    """
    with temp_service_context() as temp_service:
        candidates = temp_service.get_cleanup_candidates(
            model_name="nonexistent_model",
            keep_latest=3
        )
        
        assert len(candidates) == 0


# **Feature: simplified-llm-optimization, Property 31: Low disk space triggers cleanup prompt**
@given(
    num_versions=st.integers(min_value=1, max_value=5),
    keep_latest=st.integers(min_value=5, max_value=10)
)
@settings(max_examples=50, deadline=None)
def test_cleanup_candidates_when_keep_latest_exceeds_total(num_versions, keep_latest):
    """
    Property: For any model where keep_latest >= total versions,
    get_cleanup_candidates should return an empty list.
    """
    assume(keep_latest >= num_versions)
    
    with temp_service_context() as temp_service, temp_checkpoint_context() as temp_checkpoint:
        model_name = "test_model"
        
        # Create versions
        for i in range(num_versions):
            temp_service.create_version(
                model_name=model_name,
                checkpoint_path=temp_checkpoint,
                config={'iteration': i},
                metrics={'loss': 1.0}
            )
        
        # Get cleanup candidates
        candidates = temp_service.get_cleanup_candidates(
            model_name=model_name,
            keep_latest=keep_latest
        )
        
        # Should return empty list since we want to keep more than we have
        assert len(candidates) == 0
