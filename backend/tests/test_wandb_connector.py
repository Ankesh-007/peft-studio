"""
Unit tests for Weights & Biases connector.

Tests the W&B connector functionality including:
- Connection and authentication
- Run creation and management
- Metric logging with batching
- Artifact tracking
- Experiment comparison
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime
from typing import Dict, Any
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from plugins.connectors.wandb_connector import WandBConnector
from connectors.base import TrainingConfig, JobStatus


class MockWandBAPI:
    """Mock W&B API for testing."""
    
    def __init__(self):
        self.runs = {}
        self.metrics = {}
        self.artifacts = {}
        self.connected = False
        self.api_key = None
        self.entity = "test-user"
    
    def connect(self, api_key: str) -> bool:
        self.api_key = api_key
        self.connected = True
        return True
    
    def create_run(self, config: Dict) -> str:
        run_id = f"run_{len(self.runs)}"
        self.runs[run_id] = {
            "id": run_id,
            "config": config,
            "state": "running",
            "created_at": datetime.now().isoformat(),
        }
        self.metrics[run_id] = []
        return run_id
    
    def log_metrics(self, run_id: str, metrics: list):
        if run_id not in self.metrics:
            return
        self.metrics[run_id].extend(metrics)
    
    def get_run(self, run_id: str) -> Dict:
        return self.runs.get(run_id, {})
    
    def update_run_state(self, run_id: str, state: str):
        if run_id in self.runs:
            self.runs[run_id]["state"] = state
    
    def add_artifact(self, run_id: str, artifact_id: str, metadata: Dict):
        if run_id not in self.artifacts:
            self.artifacts[run_id] = []
        self.artifacts[run_id].append({
            "id": artifact_id,
            "metadata": metadata
        })


@pytest.fixture
def mock_wandb_api():
    return MockWandBAPI()


@pytest_asyncio.fixture
async def wandb_connector(mock_wandb_api):
    """Provide a W&B connector with mocked API."""
    connector = WandBConnector()
    connector._mock_api = mock_wandb_api
    
    # Mock connect
    async def mock_connect(credentials: Dict[str, str]) -> bool:
        connector._api_key = credentials.get("api_key")
        connector._entity = "test-user"
        connector._connected = mock_wandb_api.connect(connector._api_key)
        return connector._connected
    
    connector.connect = mock_connect
    
    # Mock submit_job
    async def mock_submit_job(config: TrainingConfig) -> str:
        if not connector._connected:
            raise RuntimeError("Not connected to W&B")
        
        job_id = f"job_{len(connector._runs)}"
        
        run_config = {
            "entity": connector._entity,
            "project": config.project_name,
            "config": {"base_model": config.base_model}
        }
        
        wandb_run_id = mock_wandb_api.create_run(run_config)
        
        connector._runs[job_id] = {
            "wandb_id": wandb_run_id,
            "config": config,
            "project": config.project_name,
            "entity": connector._entity,
            "created_at": datetime.now().isoformat(),
        }
        
        from collections import deque
        connector._metric_batches[job_id] = deque()
        
        return job_id
    
    connector.submit_job = mock_submit_job
    
    # Mock _flush_metrics
    async def mock_flush_metrics(job_id: str):
        if job_id not in connector._metric_batches:
            return
        
        batch = connector._metric_batches[job_id]
        metrics_to_send = []
        while batch:
            metrics_to_send.append(batch.popleft())
        
        if not metrics_to_send:
            return
        
        run_info = connector._runs.get(job_id)
        if run_info:
            mock_wandb_api.log_metrics(run_info['wandb_id'], metrics_to_send)
    
    connector._flush_metrics = mock_flush_metrics
    
    # Mock get_job_status
    async def mock_get_job_status(job_id: str) -> JobStatus:
        if job_id not in connector._runs:
            return JobStatus.FAILED
        
        run_info = connector._runs[job_id]
        run_data = mock_wandb_api.get_run(run_info['wandb_id'])
        state = run_data.get("state", "running")
        
        status_map = {
            "running": JobStatus.RUNNING,
            "finished": JobStatus.COMPLETED,
            "failed": JobStatus.FAILED,
            "killed": JobStatus.CANCELLED,
        }
        
        return status_map.get(state, JobStatus.RUNNING)
    
    connector.get_job_status = mock_get_job_status
    
    # Mock cancel_job
    async def mock_cancel_job(job_id: str) -> bool:
        if job_id not in connector._runs:
            return False
        
        run_info = connector._runs[job_id]
        mock_wandb_api.update_run_state(run_info['wandb_id'], "killed")
        
        if job_id in connector._batch_tasks:
            connector._batch_tasks[job_id].cancel()
            try:
                await connector._batch_tasks[job_id]
            except asyncio.CancelledError:
                pass
            del connector._batch_tasks[job_id]
        
        await connector._flush_metrics(job_id)
        return True
    
    connector.cancel_job = mock_cancel_job
    
    await connector.connect({"api_key": "test_key_123"})
    
    yield connector
    
    await connector.disconnect()


@pytest.mark.asyncio
async def test_connection(wandb_connector):
    """Test W&B connection."""
    assert wandb_connector._connected
    assert wandb_connector._api_key == "test_key_123"
    assert wandb_connector._entity == "test-user"


@pytest.mark.asyncio
async def test_verify_connection(wandb_connector):
    """Test connection verification."""
    # Mock verify_connection
    async def mock_verify():
        return wandb_connector._connected
    
    wandb_connector.verify_connection = mock_verify
    
    is_valid = await wandb_connector.verify_connection()
    assert is_valid


@pytest.mark.asyncio
async def test_create_run(wandb_connector):
    """Test creating a W&B run."""
    config = TrainingConfig(
        base_model="meta-llama/Llama-2-7b-hf",
        model_source="huggingface",
        algorithm="lora",
        rank=16,
        alpha=32,
        dropout=0.1,
        target_modules=["q_proj", "v_proj"],
        dataset_path="/tmp/dataset.json",
        experiment_tracker="wandb",
        project_name="test-project",
    )
    
    job_id = await wandb_connector.submit_job(config)
    
    assert job_id is not None
    assert job_id in wandb_connector._runs
    assert wandb_connector._runs[job_id]["project"] == "test-project"


@pytest.mark.asyncio
async def test_log_metrics(wandb_connector):
    """Test logging metrics with batching."""
    config = TrainingConfig(
        base_model="test-model",
        model_source="huggingface",
        algorithm="lora",
        rank=16,
        alpha=32,
        dropout=0.1,
        target_modules=["q_proj", "v_proj"],
        dataset_path="/tmp/dataset.json",
        experiment_tracker="wandb",
        project_name="test-project",
    )
    
    job_id = await wandb_connector.submit_job(config)
    
    # Log metrics
    await wandb_connector.log_metrics(job_id, {"loss": 1.5, "accuracy": 0.8}, step=0)
    await wandb_connector.log_metrics(job_id, {"loss": 1.2, "accuracy": 0.85}, step=1)
    
    # Flush metrics
    await wandb_connector._flush_metrics(job_id)
    
    # Verify metrics were logged
    run_info = wandb_connector._runs[job_id]
    logged_metrics = wandb_connector._mock_api.metrics[run_info['wandb_id']]
    
    assert len(logged_metrics) == 2
    assert logged_metrics[0]["loss"] == 1.5
    assert logged_metrics[1]["accuracy"] == 0.85


@pytest.mark.asyncio
async def test_batch_metrics(wandb_connector):
    """Test metric batching."""
    config = TrainingConfig(
        base_model="test-model",
        model_source="huggingface",
        algorithm="lora",
        rank=16,
        alpha=32,
        dropout=0.1,
        target_modules=["q_proj", "v_proj"],
        dataset_path="/tmp/dataset.json",
        experiment_tracker="wandb",
        project_name="test-project",
    )
    
    job_id = await wandb_connector.submit_job(config)
    
    # Log many metrics
    for i in range(10):
        await wandb_connector.log_metrics(job_id, {"loss": 1.0 / (i + 1)}, step=i)
    
    # Verify metrics are batched
    assert len(wandb_connector._metric_batches[job_id]) == 10
    
    # Flush
    await wandb_connector._flush_metrics(job_id)
    
    # Verify all metrics were sent
    run_info = wandb_connector._runs[job_id]
    logged_metrics = wandb_connector._mock_api.metrics[run_info['wandb_id']]
    assert len(logged_metrics) == 10


@pytest.mark.asyncio
async def test_get_job_status(wandb_connector):
    """Test getting job status."""
    config = TrainingConfig(
        base_model="test-model",
        model_source="huggingface",
        algorithm="lora",
        rank=16,
        alpha=32,
        dropout=0.1,
        target_modules=["q_proj", "v_proj"],
        dataset_path="/tmp/dataset.json",
        experiment_tracker="wandb",
        project_name="test-project",
    )
    
    job_id = await wandb_connector.submit_job(config)
    
    # Check initial status
    status = await wandb_connector.get_job_status(job_id)
    assert status == JobStatus.RUNNING
    
    # Update status
    run_info = wandb_connector._runs[job_id]
    wandb_connector._mock_api.update_run_state(run_info['wandb_id'], "finished")
    
    # Check updated status
    status = await wandb_connector.get_job_status(job_id)
    assert status == JobStatus.COMPLETED


@pytest.mark.asyncio
async def test_cancel_job(wandb_connector):
    """Test cancelling a job."""
    config = TrainingConfig(
        base_model="test-model",
        model_source="huggingface",
        algorithm="lora",
        rank=16,
        alpha=32,
        dropout=0.1,
        target_modules=["q_proj", "v_proj"],
        dataset_path="/tmp/dataset.json",
        experiment_tracker="wandb",
        project_name="test-project",
    )
    
    job_id = await wandb_connector.submit_job(config)
    
    # Cancel job
    success = await wandb_connector.cancel_job(job_id)
    assert success
    
    # Verify status
    status = await wandb_connector.get_job_status(job_id)
    assert status == JobStatus.CANCELLED


@pytest.mark.asyncio
async def test_get_run_url(wandb_connector):
    """Test getting run URL."""
    config = TrainingConfig(
        base_model="test-model",
        model_source="huggingface",
        algorithm="lora",
        rank=16,
        alpha=32,
        dropout=0.1,
        target_modules=["q_proj", "v_proj"],
        dataset_path="/tmp/dataset.json",
        experiment_tracker="wandb",
        project_name="test-project",
    )
    
    job_id = await wandb_connector.submit_job(config)
    
    url = wandb_connector.get_run_url(job_id)
    
    assert url is not None
    assert "wandb.ai" in url
    assert "test-project" in url


@pytest.mark.asyncio
async def test_disconnect_flushes_metrics(wandb_connector):
    """Test that disconnect flushes pending metrics."""
    config = TrainingConfig(
        base_model="test-model",
        model_source="huggingface",
        algorithm="lora",
        rank=16,
        alpha=32,
        dropout=0.1,
        target_modules=["q_proj", "v_proj"],
        dataset_path="/tmp/dataset.json",
        experiment_tracker="wandb",
        project_name="test-project",
    )
    
    job_id = await wandb_connector.submit_job(config)
    
    # Get run info before disconnect
    run_info = wandb_connector._runs[job_id]
    wandb_run_id = run_info['wandb_id']
    
    # Log metrics without flushing
    await wandb_connector.log_metrics(job_id, {"loss": 1.0}, step=0)
    
    # Disconnect should flush
    await wandb_connector.disconnect()
    
    # Verify metrics were flushed (check mock API directly)
    logged_metrics = wandb_connector._mock_api.metrics[wandb_run_id]
    assert len(logged_metrics) == 1


@pytest.mark.asyncio
async def test_required_credentials():
    """Test required credentials."""
    connector = WandBConnector()
    required = connector.get_required_credentials()
    
    assert "api_key" in required


@pytest.mark.asyncio
async def test_supports_tracking():
    """Test that W&B supports tracking."""
    connector = WandBConnector()
    
    assert connector.supports_tracking
    assert not connector.supports_training
    assert not connector.supports_inference
    assert not connector.supports_registry


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
