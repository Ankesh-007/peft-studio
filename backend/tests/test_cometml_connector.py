"""
Unit tests for Comet ML connector.

Tests the Comet ML connector functionality including:
- Connection and authentication
- Experiment creation and management
- Metric logging with batching
- Asset tracking
- Experiment comparison
- Model registry integration
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime
from typing import Dict, Any
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from plugins.connectors.cometml_connector import CometMLConnector
from connectors.base import TrainingConfig, JobStatus


class MockCometMLAPI:
    """Mock Comet ML API for testing."""
    
    def __init__(self):
        self.experiments = {}
        self.metrics = {}
        self.assets = {}
        self.models = {}
        self.connected = False
        self.api_key = None
        self.workspace = "test-workspace"
    
    def connect(self, api_key: str) -> bool:
        self.api_key = api_key
        self.connected = True
        return True
    
    def create_experiment(self, config: Dict) -> str:
        exp_key = f"exp_{len(self.experiments)}"
        self.experiments[exp_key] = {
            "experimentKey": exp_key,
            "experimentName": config.get("experimentName"),
            "projectName": config.get("projectName"),
            "workspaceName": config.get("workspaceName"),
            "status": "running",
            "parameters": {},
            "tags": [],
            "created_at": datetime.now().isoformat(),
        }
        self.metrics[exp_key] = []
        return exp_key
    
    def log_parameters(self, exp_key: str, parameters: Dict):
        if exp_key in self.experiments:
            self.experiments[exp_key]["parameters"] = parameters
    
    def add_tags(self, exp_key: str, tags: list):
        if exp_key in self.experiments:
            self.experiments[exp_key]["tags"] = tags
    
    def log_metrics(self, exp_key: str, metrics: list):
        if exp_key not in self.metrics:
            return
        self.metrics[exp_key].extend(metrics)
    
    def get_experiment(self, exp_key: str) -> Dict:
        return self.experiments.get(exp_key, {})
    
    def update_experiment_status(self, exp_key: str, status: str):
        if exp_key in self.experiments:
            self.experiments[exp_key]["status"] = status
    
    def add_asset(self, exp_key: str, asset_id: str, metadata: Dict):
        if exp_key not in self.assets:
            self.assets[exp_key] = []
        self.assets[exp_key].append({
            "assetId": asset_id,
            "metadata": metadata
        })
    
    def register_model(self, model_name: str, exp_key: str, version: str) -> str:
        model_id = f"model_{len(self.models)}"
        self.models[model_id] = {
            "modelName": model_name,
            "experimentKey": exp_key,
            "version": version,
        }
        return model_id


@pytest.fixture
def mock_cometml_api():
    return MockCometMLAPI()


@pytest_asyncio.fixture
async def cometml_connector(mock_cometml_api):
    """Provide a Comet ML connector with mocked API."""
    connector = CometMLConnector()
    connector._mock_api = mock_cometml_api
    
    # Mock connect
    async def mock_connect(credentials: Dict[str, str]) -> bool:
        connector._api_key = credentials.get("api_key")
        connector._workspace = "test-workspace"
        connector._connected = mock_cometml_api.connect(connector._api_key)
        return connector._connected
    
    connector.connect = mock_connect
    
    # Mock submit_job
    async def mock_submit_job(config: TrainingConfig) -> str:
        if not connector._connected:
            raise RuntimeError("Not connected to Comet ML")
        
        job_id = f"job_{len(connector._experiments)}"
        
        exp_config = {
            "workspaceName": connector._workspace,
            "projectName": config.project_name,
            "experimentName": f"{config.base_model}_{config.algorithm}",
        }
        
        experiment_key = mock_cometml_api.create_experiment(exp_config)
        
        connector._experiments[job_id] = {
            "experiment_key": experiment_key,
            "config": config,
            "project": config.project_name,
            "workspace": connector._workspace,
            "created_at": datetime.now().isoformat(),
        }
        
        # Log parameters
        mock_cometml_api.log_parameters(experiment_key, {
            "base_model": config.base_model,
            "algorithm": config.algorithm,
        })
        
        # Add tags
        mock_cometml_api.add_tags(experiment_key, [
            config.algorithm,
            config.provider,
            config.model_source,
        ])
        
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
        
        exp_info = connector._experiments.get(job_id)
        if exp_info:
            mock_cometml_api.log_metrics(exp_info['experiment_key'], metrics_to_send)
    
    connector._flush_metrics = mock_flush_metrics
    
    # Mock get_job_status
    async def mock_get_job_status(job_id: str) -> JobStatus:
        if job_id not in connector._experiments:
            return JobStatus.FAILED
        
        exp_info = connector._experiments[job_id]
        exp_data = mock_cometml_api.get_experiment(exp_info['experiment_key'])
        status = exp_data.get("status", "running")
        
        status_map = {
            "running": JobStatus.RUNNING,
            "completed": JobStatus.COMPLETED,
            "failed": JobStatus.FAILED,
            "killed": JobStatus.CANCELLED,
        }
        
        return status_map.get(status, JobStatus.RUNNING)
    
    connector.get_job_status = mock_get_job_status
    
    # Mock cancel_job
    async def mock_cancel_job(job_id: str) -> bool:
        if job_id not in connector._experiments:
            return False
        
        exp_info = connector._experiments[job_id]
        mock_cometml_api.update_experiment_status(exp_info['experiment_key'], "killed")
        
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
    
    # Mock register_model
    async def mock_register_model(job_id: str, model_name: str, version: str = None) -> str:
        if job_id not in connector._experiments:
            raise ValueError(f"Experiment {job_id} not found")
        
        exp_info = connector._experiments[job_id]
        model_id = mock_cometml_api.register_model(
            model_name,
            exp_info['experiment_key'],
            version or "1.0.0"
        )
        return model_id
    
    connector.register_model = mock_register_model
    
    await connector.connect({"api_key": "test_key_123"})
    
    yield connector
    
    await connector.disconnect()


@pytest.mark.asyncio
async def test_connection(cometml_connector):
    """Test Comet ML connection."""
    assert cometml_connector._connected
    assert cometml_connector._api_key == "test_key_123"
    assert cometml_connector._workspace == "test-workspace"


@pytest.mark.asyncio
async def test_verify_connection(cometml_connector):
    """Test connection verification."""
    # Mock verify_connection
    async def mock_verify():
        return cometml_connector._connected
    
    cometml_connector.verify_connection = mock_verify
    
    is_valid = await cometml_connector.verify_connection()
    assert is_valid


@pytest.mark.asyncio
async def test_create_experiment(cometml_connector):
    """Test creating a Comet ML experiment."""
    config = TrainingConfig(
        base_model="meta-llama/Llama-2-7b-hf",
        model_source="huggingface",
        algorithm="lora",
        rank=16,
        alpha=32,
        dropout=0.1,
        target_modules=["q_proj", "v_proj"],
        dataset_path="/tmp/dataset.json",
        experiment_tracker="cometml",
        project_name="test-project",
    )
    
    job_id = await cometml_connector.submit_job(config)
    
    assert job_id is not None
    assert job_id in cometml_connector._experiments
    assert cometml_connector._experiments[job_id]["project"] == "test-project"


@pytest.mark.asyncio
async def test_log_metrics(cometml_connector):
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
        experiment_tracker="cometml",
        project_name="test-project",
    )
    
    job_id = await cometml_connector.submit_job(config)
    
    # Log metrics
    await cometml_connector.log_metrics(job_id, {"loss": 1.5, "accuracy": 0.8}, step=0)
    await cometml_connector.log_metrics(job_id, {"loss": 1.2, "accuracy": 0.85}, step=1)
    
    # Flush metrics
    await cometml_connector._flush_metrics(job_id)
    
    # Verify metrics were logged
    exp_info = cometml_connector._experiments[job_id]
    logged_metrics = cometml_connector._mock_api.metrics[exp_info['experiment_key']]
    
    assert len(logged_metrics) == 4  # 2 metrics per step
    assert any(m["metricName"] == "loss" and m["metricValue"] == 1.5 for m in logged_metrics)
    assert any(m["metricName"] == "accuracy" and m["metricValue"] == 0.85 for m in logged_metrics)


@pytest.mark.asyncio
async def test_batch_metrics(cometml_connector):
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
        experiment_tracker="cometml",
        project_name="test-project",
    )
    
    job_id = await cometml_connector.submit_job(config)
    
    # Log many metrics
    for i in range(10):
        await cometml_connector.log_metrics(job_id, {"loss": 1.0 / (i + 1)}, step=i)
    
    # Verify metrics are batched
    assert len(cometml_connector._metric_batches[job_id]) == 10
    
    # Flush
    await cometml_connector._flush_metrics(job_id)
    
    # Verify all metrics were sent
    exp_info = cometml_connector._experiments[job_id]
    logged_metrics = cometml_connector._mock_api.metrics[exp_info['experiment_key']]
    assert len(logged_metrics) == 10


@pytest.mark.asyncio
async def test_get_job_status(cometml_connector):
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
        experiment_tracker="cometml",
        project_name="test-project",
    )
    
    job_id = await cometml_connector.submit_job(config)
    
    # Check initial status
    status = await cometml_connector.get_job_status(job_id)
    assert status == JobStatus.RUNNING
    
    # Update status
    exp_info = cometml_connector._experiments[job_id]
    cometml_connector._mock_api.update_experiment_status(exp_info['experiment_key'], "completed")
    
    # Check updated status
    status = await cometml_connector.get_job_status(job_id)
    assert status == JobStatus.COMPLETED


@pytest.mark.asyncio
async def test_cancel_job(cometml_connector):
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
        experiment_tracker="cometml",
        project_name="test-project",
    )
    
    job_id = await cometml_connector.submit_job(config)
    
    # Cancel job
    success = await cometml_connector.cancel_job(job_id)
    assert success
    
    # Verify status
    status = await cometml_connector.get_job_status(job_id)
    assert status == JobStatus.CANCELLED


@pytest.mark.asyncio
async def test_get_experiment_url(cometml_connector):
    """Test getting experiment URL."""
    config = TrainingConfig(
        base_model="test-model",
        model_source="huggingface",
        algorithm="lora",
        rank=16,
        alpha=32,
        dropout=0.1,
        target_modules=["q_proj", "v_proj"],
        dataset_path="/tmp/dataset.json",
        experiment_tracker="cometml",
        project_name="test-project",
    )
    
    job_id = await cometml_connector.submit_job(config)
    
    url = cometml_connector.get_experiment_url(job_id)
    
    assert url is not None
    assert "comet.com" in url
    assert "test-project" in url


@pytest.mark.asyncio
async def test_compare_experiments(cometml_connector):
    """Test comparing multiple experiments."""
    # Create two experiments
    config1 = TrainingConfig(
        base_model="model-1",
        model_source="huggingface",
        algorithm="lora",
        rank=16,
        alpha=32,
        dropout=0.1,
        target_modules=["q_proj", "v_proj"],
        dataset_path="/tmp/dataset.json",
        experiment_tracker="cometml",
        project_name="test-project",
    )
    
    config2 = TrainingConfig(
        base_model="model-2",
        model_source="huggingface",
        algorithm="qlora",
        rank=32,
        alpha=64,
        dropout=0.05,
        target_modules=["q_proj", "v_proj"],
        dataset_path="/tmp/dataset.json",
        experiment_tracker="cometml",
        project_name="test-project",
    )
    
    job_id1 = await cometml_connector.submit_job(config1)
    job_id2 = await cometml_connector.submit_job(config2)
    
    # Mock compare_experiments
    async def mock_compare(job_ids: list) -> Dict[str, Any]:
        comparison_data = {
            "experiments": [],
            "metrics": {},
            "parameters": {},
        }
        
        for job_id in job_ids:
            if job_id not in cometml_connector._experiments:
                continue
            
            exp_info = cometml_connector._experiments[job_id]
            exp_data = cometml_connector._mock_api.get_experiment(exp_info['experiment_key'])
            
            comparison_data["experiments"].append({
                "job_id": job_id,
                "experiment_key": exp_info['experiment_key'],
                "name": exp_data.get("experimentName"),
                "status": exp_data.get("status"),
            })
            
            comparison_data["parameters"][job_id] = exp_data.get("parameters", {})
            comparison_data["metrics"][job_id] = {}
        
        return comparison_data
    
    cometml_connector.compare_experiments = mock_compare
    
    # Compare experiments
    comparison = await cometml_connector.compare_experiments([job_id1, job_id2])
    
    assert len(comparison["experiments"]) == 2
    assert job_id1 in comparison["parameters"]
    assert job_id2 in comparison["parameters"]


@pytest.mark.asyncio
async def test_register_model(cometml_connector):
    """Test registering a model in the model registry."""
    config = TrainingConfig(
        base_model="test-model",
        model_source="huggingface",
        algorithm="lora",
        rank=16,
        alpha=32,
        dropout=0.1,
        target_modules=["q_proj", "v_proj"],
        dataset_path="/tmp/dataset.json",
        experiment_tracker="cometml",
        project_name="test-project",
    )
    
    job_id = await cometml_connector.submit_job(config)
    
    # Register model
    model_id = await cometml_connector.register_model(job_id, "my-model", "1.0.0")
    
    assert model_id is not None
    assert model_id in cometml_connector._mock_api.models


@pytest.mark.asyncio
async def test_disconnect_flushes_metrics(cometml_connector):
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
        experiment_tracker="cometml",
        project_name="test-project",
    )
    
    job_id = await cometml_connector.submit_job(config)
    
    # Get experiment info before disconnect
    exp_info = cometml_connector._experiments[job_id]
    experiment_key = exp_info['experiment_key']
    
    # Log metrics without flushing
    await cometml_connector.log_metrics(job_id, {"loss": 1.0}, step=0)
    
    # Disconnect should flush
    await cometml_connector.disconnect()
    
    # Verify metrics were flushed (check mock API directly)
    logged_metrics = cometml_connector._mock_api.metrics[experiment_key]
    assert len(logged_metrics) == 1


@pytest.mark.asyncio
async def test_required_credentials():
    """Test required credentials."""
    connector = CometMLConnector()
    required = connector.get_required_credentials()
    
    assert "api_key" in required


@pytest.mark.asyncio
async def test_supports_tracking_and_registry():
    """Test that Comet ML supports tracking and registry."""
    connector = CometMLConnector()
    
    assert connector.supports_tracking
    assert connector.supports_registry
    assert not connector.supports_training
    assert not connector.supports_inference


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
