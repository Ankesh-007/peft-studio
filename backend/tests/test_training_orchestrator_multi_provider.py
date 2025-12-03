"""
Tests for Training Orchestrator Multi-Provider Support

Tests the enhanced training orchestrator with:
- Multi-provider job submission
- Job monitoring and status updates
- Artifact download and storage
- Job cancellation and cleanup

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
import tempfile
from pathlib import Path

from services.training_orchestration_service import (
    TrainingOrchestrator,
    TrainingJob,
    TrainingConfig,
    TrainingState,
    ArtifactInfo
)
from connectors.base import JobStatus as ConnectorJobStatus


@pytest.fixture
def orchestrator():
    """Create orchestrator with temporary directories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        checkpoint_dir = Path(temp_dir) / "checkpoints"
        artifacts_dir = Path(temp_dir) / "artifacts"
        
        orch = TrainingOrchestrator(
            checkpoint_base_dir=str(checkpoint_dir),
            artifacts_base_dir=str(artifacts_dir)
        )
        yield orch


@pytest.fixture
def test_config():
    """Create test training configuration."""
    return TrainingConfig(
        job_id="test_job_123",
        model_name="test-model",
        dataset_path="/tmp/dataset",
        output_dir="/tmp/output",
        peft_method="lora",
        lora_r=8,
        lora_alpha=16,
        lora_dropout=0.1,
        target_modules=["q_proj", "v_proj"]
    )


@pytest.fixture
def mock_connector():
    """Create mock connector."""
    connector = AsyncMock()
    connector.name = "test_provider"
    connector.display_name = "Test Provider"
    connector.supports_training = True
    connector.submit_job = AsyncMock(return_value="provider_job_456")
    connector.get_job_status = AsyncMock(return_value=ConnectorJobStatus.RUNNING)
    connector.cancel_job = AsyncMock(return_value=True)
    connector.fetch_artifact = AsyncMock(return_value=b"test artifact data")
    return connector


def test_create_job(orchestrator, test_config):
    """Test job creation."""
    job = orchestrator.create_job(test_config)
    
    assert job.job_id == test_config.job_id
    assert job.state == TrainingState.CREATED
    assert job.config == test_config
    assert job.provider is None
    assert job.provider_job_id is None


def test_submit_job_to_provider(orchestrator, test_config, mock_connector):
    """Test submitting job to a provider (Requirement 5.1, 5.2)."""
    job = orchestrator.create_job(test_config)
    
    # Patch connector manager
    with patch.object(
        orchestrator.connector_manager,
        'get',
        return_value=mock_connector
    ):
        # Submit job
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            provider_job_id = loop.run_until_complete(
                orchestrator.submit_job_to_provider(test_config.job_id, "test_provider")
            )
        finally:
            loop.close()
        
        # Verify submission
        assert provider_job_id == "provider_job_456"
        assert job.provider == "test_provider"
        assert job.provider_job_id == "provider_job_456"
        assert job.state == TrainingState.RUNNING
        assert job.started_at is not None
        
        # Verify connector was called
        mock_connector.submit_job.assert_called_once()


def test_submit_job_invalid_provider(orchestrator, test_config):
    """Test submitting job to invalid provider."""
    job = orchestrator.create_job(test_config)
    
    with patch.object(
        orchestrator.connector_manager,
        'get',
        return_value=None
    ):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            with pytest.raises(ValueError, match="Provider not found"):
                loop.run_until_complete(
                    orchestrator.submit_job_to_provider(test_config.job_id, "invalid_provider")
                )
        finally:
            loop.close()


def test_cancel_provider_job(orchestrator, test_config, mock_connector):
    """Test cancelling a job on a provider (Requirement 5.4)."""
    job = orchestrator.create_job(test_config)
    job.provider = "test_provider"
    job.provider_job_id = "provider_job_456"
    job.state = TrainingState.RUNNING
    
    with patch.object(
        orchestrator.connector_manager,
        'get',
        return_value=mock_connector
    ):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success = loop.run_until_complete(
                orchestrator.cancel_provider_job(test_config.job_id)
            )
        finally:
            loop.close()
        
        assert success is True
        mock_connector.cancel_job.assert_called_once_with("provider_job_456")


def test_download_artifact(orchestrator, test_config, mock_connector):
    """Test downloading artifact from provider (Requirement 5.5)."""
    job = orchestrator.create_job(test_config)
    job.provider = "test_provider"
    job.provider_job_id = "provider_job_456"
    
    with patch.object(
        orchestrator.connector_manager,
        'get',
        return_value=mock_connector
    ):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            artifact_info = loop.run_until_complete(
                orchestrator.download_artifact(test_config.job_id)
            )
        finally:
            loop.close()
        
        # Verify artifact info
        assert artifact_info is not None
        assert artifact_info.job_id == test_config.job_id
        assert artifact_info.size_bytes == len(b"test artifact data")
        assert artifact_info.path.exists()
        
        # Verify file contents
        with open(artifact_info.path, 'rb') as f:
            data = f.read()
        assert data == b"test artifact data"
        
        # Verify job has artifact info
        assert job.artifact_info == artifact_info
        
        # Verify connector was called
        mock_connector.fetch_artifact.assert_called_once_with("provider_job_456")


def test_download_artifact_local_job(orchestrator, test_config):
    """Test that downloading artifact fails for local jobs."""
    job = orchestrator.create_job(test_config)
    job.provider = "local"
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        with pytest.raises(ValueError, match="not running on a provider"):
            loop.run_until_complete(
                orchestrator.download_artifact(test_config.job_id)
            )
    finally:
        loop.close()


def test_stop_training_provider_job(orchestrator, test_config, mock_connector):
    """Test stopping a provider job (Requirement 5.4)."""
    job = orchestrator.create_job(test_config)
    job.provider = "test_provider"
    job.provider_job_id = "provider_job_456"
    job.state = TrainingState.RUNNING
    
    with patch.object(
        orchestrator.connector_manager,
        'get',
        return_value=mock_connector
    ):
        orchestrator.stop_training(test_config.job_id)
        
        # Verify job state
        assert job.state == TrainingState.STOPPED
        assert job.completed_at is not None
        
        # Verify connector was called
        mock_connector.cancel_job.assert_called_once()


def test_start_training_with_provider(orchestrator, test_config, mock_connector):
    """Test starting training with a provider."""
    job = orchestrator.create_job(test_config)
    
    with patch.object(
        orchestrator.connector_manager,
        'get',
        return_value=mock_connector
    ):
        orchestrator.start_training(test_config.job_id, provider="test_provider")
        
        # Verify job state
        assert job.provider == "test_provider"
        assert job.provider_job_id == "provider_job_456"
        assert job.state == TrainingState.RUNNING


def test_start_training_local(orchestrator, test_config):
    """Test starting local training."""
    job = orchestrator.create_job(test_config)
    
    orchestrator.start_training(test_config.job_id, provider="local")
    
    # Verify job state
    assert job.provider == "local"
    assert job.state in [TrainingState.INITIALIZING, TrainingState.RUNNING]
    
    # Cleanup
    orchestrator.stop_training(test_config.job_id)


def test_artifact_metadata(orchestrator, test_config, mock_connector):
    """Test that artifact metadata is properly stored."""
    job = orchestrator.create_job(test_config)
    job.provider = "test_provider"
    job.provider_job_id = "provider_job_456"
    
    with patch.object(
        orchestrator.connector_manager,
        'get',
        return_value=mock_connector
    ):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            artifact_info = loop.run_until_complete(
                orchestrator.download_artifact(test_config.job_id)
            )
        finally:
            loop.close()
        
        # Verify metadata
        assert artifact_info.metadata['provider'] == "test_provider"
        assert artifact_info.metadata['provider_job_id'] == "provider_job_456"
        assert artifact_info.metadata['model_name'] == test_config.model_name
        assert artifact_info.metadata['peft_method'] == test_config.peft_method


def test_job_to_dict_with_provider_info(orchestrator, test_config):
    """Test that job serialization includes provider info."""
    job = orchestrator.create_job(test_config)
    job.provider = "test_provider"
    job.provider_job_id = "provider_job_456"
    
    job_dict = job.to_dict()
    
    assert job_dict['provider'] == "test_provider"
    assert job_dict['provider_job_id'] == "provider_job_456"
    assert job_dict['artifact_info'] is None  # No artifact yet


def test_multiple_provider_jobs(orchestrator, mock_connector):
    """Test managing multiple jobs on different providers."""
    jobs = []
    
    for i in range(3):
        config = TrainingConfig(
            job_id=f"test_job_{i}",
            model_name=f"test-model-{i}",
            dataset_path="/tmp/dataset",
            output_dir="/tmp/output"
        )
        job = orchestrator.create_job(config)
        jobs.append(job)
    
    # Submit all jobs
    with patch.object(
        orchestrator.connector_manager,
        'get',
        return_value=mock_connector
    ):
        for i, job in enumerate(jobs):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    orchestrator.submit_job_to_provider(f"test_job_{i}", "test_provider")
                )
            finally:
                loop.close()
    
    # Verify all jobs are tracked
    assert len(orchestrator.jobs) == 3
    for i, job in enumerate(jobs):
        assert job.provider == "test_provider"
        assert job.state == TrainingState.RUNNING


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
