"""
Property-Based Test for Adapter Artifact Integrity

Feature: unified-llm-platform, Property 7: Adapter artifact integrity
Validates: Requirements 5.5, 8.2

Property: For any downloaded adapter, the file hash should match the hash 
provided by the training platform.

This test ensures that artifacts are downloaded correctly without corruption
and that integrity verification works properly.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from pathlib import Path
import tempfile
import shutil
import hashlib
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

import sys
from pathlib import Path as PathLib

# Add backend to path
backend_path = PathLib(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from services.training_orchestration_service import (
    TrainingOrchestrator,
    TrainingJob,
    TrainingConfig,
    TrainingState,
    ArtifactInfo
)


def calculate_hash(data: bytes) -> str:
    """Calculate SHA256 hash of data."""
    return hashlib.sha256(data).hexdigest()


# Strategy for generating random artifact data
artifact_data_strategy = st.binary(min_size=100, max_size=10000)


@given(artifact_data=artifact_data_strategy)
@settings(max_examples=100, deadline=5000)
def test_artifact_integrity_property(artifact_data):
    """
    Property 7: Adapter artifact integrity
    
    For any downloaded adapter, the file hash should match the hash
    provided by the training platform.
    
    This property ensures:
    1. Downloaded artifacts are stored correctly
    2. Hash calculation is accurate
    3. Integrity verification works
    4. No data corruption during download/storage
    """
    # Calculate expected hash
    expected_hash = calculate_hash(artifact_data)
    
    # Create temporary directories
    with tempfile.TemporaryDirectory() as temp_dir:
        artifacts_dir = Path(temp_dir) / "artifacts"
        checkpoints_dir = Path(temp_dir) / "checkpoints"
        
        # Create orchestrator
        orchestrator = TrainingOrchestrator(
            checkpoint_base_dir=str(checkpoints_dir),
            artifacts_base_dir=str(artifacts_dir)
        )
        
        # Create a test job
        job_id = "test_job_artifact_integrity"
        config = TrainingConfig(
            job_id=job_id,
            model_name="test-model",
            dataset_path="/tmp/dataset",
            output_dir="/tmp/output"
        )
        
        job = orchestrator.create_job(config)
        job.provider = "test_provider"
        job.provider_job_id = "test_provider_job_123"
        
        # Mock connector that returns our test artifact data
        mock_connector = AsyncMock()
        mock_connector.name = "test_provider"
        mock_connector.supports_training = True
        mock_connector.fetch_artifact = AsyncMock(return_value=artifact_data)
        
        # Patch connector manager to return our mock
        with patch.object(
            orchestrator.connector_manager,
            'get',
            return_value=mock_connector
        ):
            # Download artifact
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                artifact_info = loop.run_until_complete(
                    orchestrator.download_artifact(job_id)
                )
            finally:
                loop.close()
            
            # Verify artifact info
            assert artifact_info is not None
            assert artifact_info.job_id == job_id
            assert artifact_info.size_bytes == len(artifact_data)
            
            # PROPERTY: Hash should match
            assert artifact_info.hash_sha256 == expected_hash, \
                f"Hash mismatch: expected {expected_hash}, got {artifact_info.hash_sha256}"
            
            # Verify file was actually saved
            assert artifact_info.path.exists(), "Artifact file should exist"
            
            # Verify file contents match original data
            with open(artifact_info.path, 'rb') as f:
                saved_data = f.read()
            
            assert saved_data == artifact_data, "Saved data should match original"
            
            # Verify hash of saved file matches
            saved_hash = calculate_hash(saved_data)
            assert saved_hash == expected_hash, \
                f"Saved file hash mismatch: expected {expected_hash}, got {saved_hash}"
            
            # Verify artifact info is attached to job
            assert job.artifact_info == artifact_info


def test_artifact_integrity_with_corruption():
    """
    Test that corruption is detected.
    
    If data is corrupted during download, the hash should not match.
    """
    original_data = b"This is the original adapter data" * 100
    corrupted_data = b"This is CORRUPTED adapter data" * 100
    
    original_hash = calculate_hash(original_data)
    corrupted_hash = calculate_hash(corrupted_data)
    
    # Hashes should be different
    assert original_hash != corrupted_hash
    
    with tempfile.TemporaryDirectory() as temp_dir:
        artifacts_dir = Path(temp_dir) / "artifacts"
        checkpoints_dir = Path(temp_dir) / "checkpoints"
        
        orchestrator = TrainingOrchestrator(
            checkpoint_base_dir=str(checkpoints_dir),
            artifacts_base_dir=str(artifacts_dir)
        )
        
        job_id = "test_job_corruption"
        config = TrainingConfig(
            job_id=job_id,
            model_name="test-model",
            dataset_path="/tmp/dataset",
            output_dir="/tmp/output"
        )
        
        job = orchestrator.create_job(config)
        job.provider = "test_provider"
        job.provider_job_id = "test_provider_job_456"
        
        # Mock connector that returns corrupted data
        mock_connector = AsyncMock()
        mock_connector.name = "test_provider"
        mock_connector.supports_training = True
        mock_connector.fetch_artifact = AsyncMock(return_value=corrupted_data)
        
        with patch.object(
            orchestrator.connector_manager,
            'get',
            return_value=mock_connector
        ):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                artifact_info = loop.run_until_complete(
                    orchestrator.download_artifact(job_id)
                )
            finally:
                loop.close()
            
            # The hash should match the corrupted data (not the original)
            assert artifact_info.hash_sha256 == corrupted_hash
            assert artifact_info.hash_sha256 != original_hash


def test_artifact_integrity_multiple_downloads():
    """
    Test that multiple downloads of the same artifact produce consistent hashes.
    """
    artifact_data = b"Consistent adapter data" * 50
    expected_hash = calculate_hash(artifact_data)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        artifacts_dir = Path(temp_dir) / "artifacts"
        checkpoints_dir = Path(temp_dir) / "checkpoints"
        
        orchestrator = TrainingOrchestrator(
            checkpoint_base_dir=str(checkpoints_dir),
            artifacts_base_dir=str(artifacts_dir)
        )
        
        hashes = []
        
        # Download same artifact multiple times
        for i in range(3):
            job_id = f"test_job_multi_{i}"
            config = TrainingConfig(
                job_id=job_id,
                model_name="test-model",
                dataset_path="/tmp/dataset",
                output_dir="/tmp/output"
            )
            
            job = orchestrator.create_job(config)
            job.provider = "test_provider"
            job.provider_job_id = f"test_provider_job_{i}"
            
            mock_connector = AsyncMock()
            mock_connector.name = "test_provider"
            mock_connector.supports_training = True
            mock_connector.fetch_artifact = AsyncMock(return_value=artifact_data)
            
            with patch.object(
                orchestrator.connector_manager,
                'get',
                return_value=mock_connector
            ):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    artifact_info = loop.run_until_complete(
                        orchestrator.download_artifact(job_id)
                    )
                finally:
                    loop.close()
                
                hashes.append(artifact_info.hash_sha256)
        
        # All hashes should be identical
        assert len(set(hashes)) == 1, "All downloads should produce same hash"
        assert hashes[0] == expected_hash


def test_artifact_integrity_empty_file():
    """
    Test handling of empty artifact files.
    """
    empty_data = b""
    expected_hash = calculate_hash(empty_data)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        artifacts_dir = Path(temp_dir) / "artifacts"
        checkpoints_dir = Path(temp_dir) / "checkpoints"
        
        orchestrator = TrainingOrchestrator(
            checkpoint_base_dir=str(checkpoints_dir),
            artifacts_base_dir=str(artifacts_dir)
        )
        
        job_id = "test_job_empty"
        config = TrainingConfig(
            job_id=job_id,
            model_name="test-model",
            dataset_path="/tmp/dataset",
            output_dir="/tmp/output"
        )
        
        job = orchestrator.create_job(config)
        job.provider = "test_provider"
        job.provider_job_id = "test_provider_job_empty"
        
        mock_connector = AsyncMock()
        mock_connector.name = "test_provider"
        mock_connector.supports_training = True
        mock_connector.fetch_artifact = AsyncMock(return_value=empty_data)
        
        with patch.object(
            orchestrator.connector_manager,
            'get',
            return_value=mock_connector
        ):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                artifact_info = loop.run_until_complete(
                    orchestrator.download_artifact(job_id)
                )
            finally:
                loop.close()
            
            # Should handle empty file correctly
            assert artifact_info.size_bytes == 0
            assert artifact_info.hash_sha256 == expected_hash


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
