"""
Property-based tests for model version creation.

**Feature: simplified-llm-optimization, Property 30: Model versioning on completion**
**Validates: Requirements 14.1, 14.2**
"""

import pytest
from hypothesis import given, strategies as st, settings
from pathlib import Path
import tempfile
import shutil
import json
from datetime import datetime
from contextlib import contextmanager

from services.model_versioning_service import (
    ModelVersioningService,
    ModelVersion
)


# Strategy for generating valid training configurations
config_strategy = st.fixed_dictionaries({
    'model_name': st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')),
    'learning_rate': st.floats(min_value=1e-6, max_value=1e-2, allow_nan=False, allow_infinity=False),
    'batch_size': st.integers(min_value=1, max_value=128),
    'epochs': st.integers(min_value=1, max_value=100),
    'lora_r': st.integers(min_value=1, max_value=256),
    'lora_alpha': st.integers(min_value=1, max_value=512)
})


# Strategy for generating valid training metrics
metrics_strategy = st.fixed_dictionaries({
    'final_loss': st.floats(min_value=0.01, max_value=10.0, allow_nan=False, allow_infinity=False),
    'final_accuracy': st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    'training_time': st.floats(min_value=1.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
    'steps': st.integers(min_value=1, max_value=100000)
})


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
    temp_file.write("dummy checkpoint data")
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
    temp_file.write("dummy checkpoint data")
    temp_file.close()
    yield temp_file.name
    # Cleanup
    Path(temp_file.name).unlink(missing_ok=True)


# **Feature: simplified-llm-optimization, Property 30: Model versioning on completion**
@given(
    model_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')),
    config=config_strategy,
    metrics=metrics_strategy
)
@settings(max_examples=100, deadline=None)
def test_version_creation_includes_all_metadata(model_name, config, metrics):
    """
    Property: For any completed training run, the system should automatically create
    a model version with version number, timestamp, configuration, and metrics.
    
    This test verifies that version creation stores all required metadata.
    """
    with temp_service_context() as temp_service, temp_checkpoint_context() as temp_checkpoint:
        # Create a version
        version = temp_service.create_version(
            model_name=model_name,
            checkpoint_path=temp_checkpoint,
            config=config,
            metrics=metrics
        )
        
        # Verify all required fields are present and valid
        assert version.id is not None
        assert len(version.id) > 0
        
        assert version.model_name == model_name
        
        # Version should follow semantic versioning format
        assert version.version is not None
        assert version.version.startswith('v')
        assert len(version.version.split('.')) == 3  # v1.0.0 format
        
        # Timestamp should be valid ISO format
        assert version.timestamp is not None
        try:
            datetime.fromisoformat(version.timestamp)
        except ValueError:
            pytest.fail(f"Invalid timestamp format: {version.timestamp}")
        
        # Configuration should be stored completely
        assert version.config is not None
        assert isinstance(version.config, dict)
        for key, value in config.items():
            assert key in version.config
            assert version.config[key] == value
        
        # Metrics should be stored completely
        assert version.metrics is not None
        assert isinstance(version.metrics, dict)
        for key, value in metrics.items():
            assert key in version.metrics
            assert version.metrics[key] == value
        
        # Checkpoint path should be valid
        assert version.checkpoint_path is not None
        assert len(version.checkpoint_path) > 0
        assert Path(version.checkpoint_path).exists()
        
        # Size should be positive
        assert version.size_bytes > 0


# **Feature: simplified-llm-optimization, Property 30: Model versioning on completion**
@given(
    model_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')),
    num_versions=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=50, deadline=None)
def test_version_numbers_increment_correctly(model_name, num_versions):
    """
    Property: For any model, creating multiple versions should result in
    incrementing version numbers following semantic versioning.
    """
    with temp_service_context() as temp_service, temp_checkpoint_context() as temp_checkpoint:
        versions = []
        
        for i in range(num_versions):
            version = temp_service.create_version(
                model_name=model_name,
                checkpoint_path=temp_checkpoint,
                config={'iteration': i},
                metrics={'loss': 1.0 / (i + 1)}
            )
            versions.append(version)
        
        # Verify versions increment
        for i in range(len(versions) - 1):
            v1 = versions[i].version.lstrip('v')
            v2 = versions[i + 1].version.lstrip('v')
            
            # Parse version numbers
            parts1 = [int(x) for x in v1.split('.')]
            parts2 = [int(x) for x in v2.split('.')]
            
            # Version should increment (at least one component should be greater)
            assert (parts2[0] > parts1[0] or 
                    (parts2[0] == parts1[0] and parts2[1] > parts1[1]) or
                    (parts2[0] == parts1[0] and parts2[1] == parts1[1] and parts2[2] > parts1[2]))


# **Feature: simplified-llm-optimization, Property 30: Model versioning on completion**
@given(
    model_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')),
    config=config_strategy,
    metrics=metrics_strategy
)
@settings(max_examples=100, deadline=None)
def test_version_persists_across_service_restarts(model_name, config, metrics):
    """
    Property: For any created version, the version data should persist
    across service restarts (saved to disk).
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        with temp_checkpoint_context() as temp_checkpoint:
            # Create version with first service instance
            service1 = ModelVersioningService(base_path=temp_dir)
            version1 = service1.create_version(
                model_name=model_name,
                checkpoint_path=temp_checkpoint,
                config=config,
                metrics=metrics
            )
            
            # Create new service instance (simulating restart)
            service2 = ModelVersioningService(base_path=temp_dir)
            
            # Retrieve the version
            version2 = service2.get_version(model_name, version1.version)
            
            # Verify version was persisted
            assert version2 is not None
            assert version2.id == version1.id
            assert version2.model_name == version1.model_name
            assert version2.version == version1.version
            assert version2.config == version1.config
            assert version2.metrics == version1.metrics
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# **Feature: simplified-llm-optimization, Property 30: Model versioning on completion**
def test_version_creation_with_invalid_checkpoint_fails(temp_service):
    """
    Property: Version creation should fail gracefully when given
    an invalid checkpoint path.
    """
    with pytest.raises(ValueError):
        temp_service.create_version(
            model_name="test_model",
            checkpoint_path="/nonexistent/path/checkpoint.pt",
            config={'test': 'config'},
            metrics={'loss': 1.0}
        )


# **Feature: simplified-llm-optimization, Property 30: Model versioning on completion**
@given(
    model_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')),
    config=config_strategy,
    metrics=metrics_strategy
)
@settings(max_examples=100, deadline=None)
def test_list_versions_returns_all_created_versions(model_name, config, metrics):
    """
    Property: For any model with created versions, list_versions should
    return all versions sorted by timestamp (newest first).
    """
    with temp_service_context() as temp_service, temp_checkpoint_context() as temp_checkpoint:
        # Create multiple versions
        num_versions = 3
        created_versions = []
        
        for i in range(num_versions):
            version = temp_service.create_version(
                model_name=model_name,
                checkpoint_path=temp_checkpoint,
                config={**config, 'iteration': i},
                metrics={**metrics, 'iteration': i}
            )
            created_versions.append(version)
        
        # List versions
        listed_versions = temp_service.list_versions(model_name)
        
        # Verify all versions are returned
        assert len(listed_versions) == num_versions
        
        # Verify they are sorted by timestamp (newest first)
        for i in range(len(listed_versions) - 1):
            t1 = datetime.fromisoformat(listed_versions[i].timestamp)
            t2 = datetime.fromisoformat(listed_versions[i + 1].timestamp)
            assert t1 >= t2


# **Feature: simplified-llm-optimization, Property 30: Model versioning on completion**
@given(
    model_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')),
    config=config_strategy,
    metrics=metrics_strategy
)
@settings(max_examples=100, deadline=None)
def test_get_latest_version_returns_most_recent(model_name, config, metrics):
    """
    Property: For any model with multiple versions, get_latest_version
    should return the most recently created version.
    """
    with temp_service_context() as temp_service, temp_checkpoint_context() as temp_checkpoint:
        # Create multiple versions
        versions = []
        for i in range(3):
            version = temp_service.create_version(
                model_name=model_name,
                checkpoint_path=temp_checkpoint,
                config={**config, 'iteration': i},
                metrics={**metrics, 'iteration': i}
            )
            versions.append(version)
        
        # Get latest version
        latest = temp_service.get_latest_version(model_name)
        
        # Verify it's the last created version
        assert latest is not None
        assert latest.id == versions[-1].id
        assert latest.version == versions[-1].version
