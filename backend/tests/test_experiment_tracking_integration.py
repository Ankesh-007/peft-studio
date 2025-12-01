"""
Tests for Experiment Tracking Integration

Tests the unified experiment tracking service across multiple platforms.

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from services.experiment_tracking_service import (
    ExperimentTrackingService,
    ExperimentConfig,
    ExperimentMetadata,
    get_experiment_tracking_service,
)
from connectors.base import JobStatus


@pytest.fixture
def mock_connector():
    """Create a mock connector for testing"""
    connector = AsyncMock()
    connector.name = "test_tracker"
    connector.supports_tracking = True
    connector.verify_connection = AsyncMock(return_value=True)
    connector.submit_job = AsyncMock(return_value="tracker_job_123")
    connector.log_metrics = AsyncMock()
    connector.log_hyperparameters = AsyncMock()
    connector.upload_artifact = AsyncMock(return_value="artifact_123")
    connector.cancel_job = AsyncMock(return_value=True)
    connector.compare_experiments = AsyncMock(return_value={
        "metrics": {
            "tracker_job_123": {"loss": 0.5, "accuracy": 0.95}
        }
    })
    return connector


@pytest.fixture
def mock_connector_manager(mock_connector):
    """Create a mock connector manager"""
    manager = Mock()
    manager.get = Mock(return_value=mock_connector)
    return manager


@pytest.fixture
def experiment_service(mock_connector_manager):
    """Create experiment tracking service with mocked dependencies"""
    with patch('services.experiment_tracking_service.get_connector_manager', return_value=mock_connector_manager):
        service = ExperimentTrackingService()
        return service


@pytest.fixture
def experiment_config():
    """Create test experiment configuration"""
    return ExperimentConfig(
        tracker_name="test_tracker",
        project_name="test_project",
        experiment_name="test_experiment",
        tags=["test", "integration"],
        notes="Test experiment",
    )


@pytest.fixture
def experiment_metadata():
    """Create test experiment metadata"""
    return ExperimentMetadata(
        job_id="job_123",
        model_name="test_model",
        dataset_name="test_dataset",
        use_case="training",
        provider="local",
        algorithm="lora",
    )


@pytest.fixture
def hyperparameters():
    """Create test hyperparameters"""
    return {
        "rank": 8,
        "alpha": 16,
        "dropout": 0.1,
        "learning_rate": 2e-4,
        "batch_size": 4,
        "num_epochs": 3,
    }


class TestExperimentTracking:
    """Test experiment tracking functionality"""
    
    @pytest.mark.asyncio
    async def test_start_experiment(
        self,
        experiment_service,
        experiment_config,
        experiment_metadata,
        hyperparameters,
        mock_connector
    ):
        """Test starting experiment tracking"""
        # Start experiment
        success = await experiment_service.start_experiment(
            job_id="job_123",
            config=experiment_config,
            metadata=experiment_metadata,
            hyperparameters=hyperparameters,
        )
        
        assert success is True
        assert "job_123" in experiment_service.active_experiments
        
        # Verify experiment info
        exp_info = experiment_service.active_experiments["job_123"]
        assert exp_info["tracker_name"] == "test_tracker"
        assert exp_info["tracker_job_id"] == "tracker_job_123"
        assert exp_info["status"] == "running"
        assert exp_info["hyperparameters"] == hyperparameters
        
        # Verify connector was called
        mock_connector.submit_job.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_log_metrics(
        self,
        experiment_service,
        experiment_config,
        experiment_metadata,
        hyperparameters,
        mock_connector
    ):
        """Test logging metrics with automatic batching"""
        # Start experiment
        await experiment_service.start_experiment(
            job_id="job_123",
            config=experiment_config,
            metadata=experiment_metadata,
            hyperparameters=hyperparameters,
        )
        
        # Log metrics immediately
        metrics = {"loss": 0.5, "accuracy": 0.95}
        success = await experiment_service.log_metrics(
            job_id="job_123",
            metrics=metrics,
            step=100,
            commit=True,
        )
        
        assert success is True
        mock_connector.log_metrics.assert_called_once()
        
        # Verify timestamp was added
        call_args = mock_connector.log_metrics.call_args
        logged_metrics = call_args[0][1]
        assert "_timestamp" in logged_metrics
        assert logged_metrics["loss"] == 0.5
        assert logged_metrics["accuracy"] == 0.95
    
    @pytest.mark.asyncio
    async def test_log_metrics_buffering(
        self,
        experiment_service,
        experiment_config,
        experiment_metadata,
        hyperparameters,
        mock_connector
    ):
        """Test metric buffering for efficiency"""
        # Start experiment
        await experiment_service.start_experiment(
            job_id="job_123",
            config=experiment_config,
            metadata=experiment_metadata,
            hyperparameters=hyperparameters,
        )
        
        # Log metrics without committing (buffered)
        for i in range(5):
            await experiment_service.log_metrics(
                job_id="job_123",
                metrics={"loss": 0.5 - i * 0.01},
                step=i,
                commit=False,
            )
        
        # Verify metrics are buffered
        assert len(experiment_service._metric_buffer["job_123"]) == 5
        
        # Flush should not have been called yet (buffer size is 10)
        assert mock_connector.log_metrics.call_count == 0
    
    @pytest.mark.asyncio
    async def test_log_hyperparameters(
        self,
        experiment_service,
        experiment_config,
        experiment_metadata,
        hyperparameters,
        mock_connector
    ):
        """Test logging hyperparameters"""
        # Start experiment
        await experiment_service.start_experiment(
            job_id="job_123",
            config=experiment_config,
            metadata=experiment_metadata,
            hyperparameters=hyperparameters,
        )
        
        # Update hyperparameters
        new_params = {"learning_rate": 1e-4}
        success = await experiment_service.log_hyperparameters(
            job_id="job_123",
            hyperparameters=new_params,
        )
        
        assert success is True
        
        # Verify hyperparameters were updated
        exp_info = experiment_service.active_experiments["job_123"]
        assert exp_info["hyperparameters"]["learning_rate"] == 1e-4
        assert exp_info["hyperparameters"]["rank"] == 8  # Original value preserved
    
    @pytest.mark.asyncio
    async def test_link_artifact(
        self,
        experiment_service,
        experiment_config,
        experiment_metadata,
        hyperparameters,
        mock_connector,
        tmp_path
    ):
        """Test linking artifacts to experiments"""
        # Create a test artifact file
        artifact_path = tmp_path / "model.safetensors"
        artifact_path.write_text("test artifact data")
        
        # Start experiment
        await experiment_service.start_experiment(
            job_id="job_123",
            config=experiment_config,
            metadata=experiment_metadata,
            hyperparameters=hyperparameters,
        )
        
        # Link artifact
        success = await experiment_service.link_artifact(
            job_id="job_123",
            artifact_path=str(artifact_path),
            artifact_type="model",
            artifact_name="test_model",
            metadata={"version": "1.0"},
        )
        
        assert success is True
        
        # Verify artifact was linked
        exp_info = experiment_service.active_experiments["job_123"]
        assert "artifacts" in exp_info
        assert len(exp_info["artifacts"]) == 1
        assert exp_info["artifacts"][0]["name"] == "test_model"
        assert exp_info["artifacts"][0]["type"] == "model"
        
        # Verify connector was called
        mock_connector.upload_artifact.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_finish_experiment(
        self,
        experiment_service,
        experiment_config,
        experiment_metadata,
        hyperparameters,
        mock_connector
    ):
        """Test finishing experiment tracking"""
        # Start experiment
        await experiment_service.start_experiment(
            job_id="job_123",
            config=experiment_config,
            metadata=experiment_metadata,
            hyperparameters=hyperparameters,
        )
        
        # Finish experiment
        summary = {"final_loss": 0.1, "final_accuracy": 0.98}
        success = await experiment_service.finish_experiment(
            job_id="job_123",
            status="completed",
            summary=summary,
        )
        
        assert success is True
        
        # Verify experiment status
        exp_info = experiment_service.active_experiments["job_123"]
        assert exp_info["status"] == "completed"
        assert exp_info["summary"] == summary
        assert "finished_at" in exp_info
        
        # Verify connector was called
        mock_connector.cancel_job.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_compare_experiments(
        self,
        experiment_service,
        experiment_config,
        experiment_metadata,
        hyperparameters,
        mock_connector
    ):
        """Test comparing multiple experiments"""
        # Start two experiments
        await experiment_service.start_experiment(
            job_id="job_123",
            config=experiment_config,
            metadata=experiment_metadata,
            hyperparameters=hyperparameters,
        )
        
        await experiment_service.start_experiment(
            job_id="job_456",
            config=experiment_config,
            metadata=experiment_metadata,
            hyperparameters={**hyperparameters, "rank": 16},
        )
        
        # Compare experiments
        comparison = await experiment_service.compare_experiments(
            job_ids=["job_123", "job_456"],
        )
        
        assert "experiments" in comparison
        assert "metrics" in comparison
        assert "hyperparameters" in comparison
        assert "statistics" in comparison
        
        # Verify comparison data
        assert len(comparison["experiments"]) == 2
        assert comparison["statistics"]["total_experiments"] == 2
        
        # Verify hyperparameters are different
        assert comparison["hyperparameters"]["job_123"]["rank"] == 8
        assert comparison["hyperparameters"]["job_456"]["rank"] == 16
    
    @pytest.mark.asyncio
    async def test_search_experiments(
        self,
        experiment_service,
        experiment_config,
        experiment_metadata,
        hyperparameters
    ):
        """Test searching and filtering experiments"""
        # Start multiple experiments with different attributes
        await experiment_service.start_experiment(
            job_id="job_123",
            config=experiment_config,
            metadata=experiment_metadata,
            hyperparameters=hyperparameters,
        )
        
        config2 = ExperimentConfig(
            tracker_name="test_tracker",
            project_name="other_project",
            tags=["test"],
        )
        await experiment_service.start_experiment(
            job_id="job_456",
            config=config2,
            metadata=experiment_metadata,
            hyperparameters=hyperparameters,
        )
        
        # Search by project
        results = await experiment_service.search_experiments(
            filters={"project": "test_project"},
        )
        
        assert len(results) == 1
        assert results[0]["job_id"] == "job_123"
        
        # Search by tags
        results = await experiment_service.search_experiments(
            filters={"tags": ["integration"]},
        )
        
        assert len(results) == 1
        assert results[0]["job_id"] == "job_123"
        
        # Search all
        results = await experiment_service.search_experiments()
        assert len(results) == 2
    
    @pytest.mark.asyncio
    async def test_get_experiment_url(
        self,
        experiment_service,
        experiment_config,
        experiment_metadata,
        hyperparameters,
        mock_connector
    ):
        """Test getting experiment tracker URL"""
        # Add get_run_url method to mock connector
        mock_connector.get_run_url = Mock(return_value="https://tracker.com/run/123")
        
        # Start experiment
        await experiment_service.start_experiment(
            job_id="job_123",
            config=experiment_config,
            metadata=experiment_metadata,
            hyperparameters=hyperparameters,
        )
        
        # Get URL
        url = experiment_service.get_experiment_url("job_123")
        
        assert url == "https://tracker.com/run/123"
        mock_connector.get_run_url.assert_called_once_with("tracker_job_123")
    
    @pytest.mark.asyncio
    async def test_get_active_experiments(
        self,
        experiment_service,
        experiment_config,
        experiment_metadata,
        hyperparameters
    ):
        """Test getting list of active experiments"""
        # Start experiments
        await experiment_service.start_experiment(
            job_id="job_123",
            config=experiment_config,
            metadata=experiment_metadata,
            hyperparameters=hyperparameters,
        )
        
        await experiment_service.start_experiment(
            job_id="job_456",
            config=experiment_config,
            metadata=experiment_metadata,
            hyperparameters=hyperparameters,
        )
        
        # Finish one experiment
        await experiment_service.finish_experiment("job_456", status="completed")
        
        # Get active experiments
        active = experiment_service.get_active_experiments()
        
        assert len(active) == 1
        assert "job_123" in active
        assert "job_456" not in active
    
    @pytest.mark.asyncio
    async def test_experiment_not_found(self, experiment_service):
        """Test operations on non-existent experiments"""
        # Try to log metrics for non-existent experiment
        success = await experiment_service.log_metrics(
            job_id="nonexistent",
            metrics={"loss": 0.5},
        )
        
        assert success is False
        
        # Try to finish non-existent experiment
        success = await experiment_service.finish_experiment("nonexistent")
        assert success is False
        
        # Try to get URL for non-existent experiment
        url = experiment_service.get_experiment_url("nonexistent")
        assert url is None
    
    @pytest.mark.asyncio
    async def test_tracker_not_connected(
        self,
        experiment_service,
        experiment_config,
        experiment_metadata,
        hyperparameters,
        mock_connector
    ):
        """Test handling of disconnected tracker"""
        # Make connector report as not connected
        mock_connector.verify_connection = AsyncMock(return_value=False)
        
        # Try to start experiment
        success = await experiment_service.start_experiment(
            job_id="job_123",
            config=experiment_config,
            metadata=experiment_metadata,
            hyperparameters=hyperparameters,
        )
        
        assert success is False
        assert "job_123" not in experiment_service.active_experiments


class TestExperimentComparison:
    """Test experiment comparison functionality"""
    
    @pytest.mark.asyncio
    async def test_comparison_statistics(
        self,
        experiment_service,
        experiment_config,
        experiment_metadata,
        hyperparameters
    ):
        """Test calculation of comparison statistics"""
        # Start multiple experiments
        for i in range(3):
            await experiment_service.start_experiment(
                job_id=f"job_{i}",
                config=experiment_config,
                metadata=experiment_metadata,
                hyperparameters=hyperparameters,
            )
        
        # Finish one experiment
        await experiment_service.finish_experiment("job_0", status="completed")
        
        # Compare all experiments
        comparison = await experiment_service.compare_experiments(
            job_ids=["job_0", "job_1", "job_2"],
        )
        
        stats = comparison["statistics"]
        assert stats["total_experiments"] == 3
        assert stats["status_counts"]["running"] == 2
        assert stats["status_counts"]["completed"] == 1


class TestMetricBuffering:
    """Test metric buffering and flushing"""
    
    @pytest.mark.asyncio
    async def test_buffer_flush_on_full(
        self,
        experiment_service,
        experiment_config,
        experiment_metadata,
        hyperparameters,
        mock_connector
    ):
        """Test that buffer flushes when full"""
        # Start experiment
        await experiment_service.start_experiment(
            job_id="job_123",
            config=experiment_config,
            metadata=experiment_metadata,
            hyperparameters=hyperparameters,
        )
        
        # Log metrics to fill buffer (buffer size is 10)
        for i in range(10):
            await experiment_service.log_metrics(
                job_id="job_123",
                metrics={"loss": 0.5 - i * 0.01},
                step=i,
                commit=False,
            )
        
        # Buffer should have flushed
        assert mock_connector.log_metrics.call_count == 10
        assert len(experiment_service._metric_buffer["job_123"]) == 0
    
    @pytest.mark.asyncio
    async def test_buffer_flush_on_finish(
        self,
        experiment_service,
        experiment_config,
        experiment_metadata,
        hyperparameters,
        mock_connector
    ):
        """Test that buffer flushes when experiment finishes"""
        # Start experiment
        await experiment_service.start_experiment(
            job_id="job_123",
            config=experiment_config,
            metadata=experiment_metadata,
            hyperparameters=hyperparameters,
        )
        
        # Log some buffered metrics
        for i in range(5):
            await experiment_service.log_metrics(
                job_id="job_123",
                metrics={"loss": 0.5 - i * 0.01},
                step=i,
                commit=False,
            )
        
        # Finish experiment
        await experiment_service.finish_experiment("job_123")
        
        # Buffer should have been flushed
        assert mock_connector.log_metrics.call_count == 5
        assert "job_123" not in experiment_service._metric_buffer


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
