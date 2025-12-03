"""
Property-Based Test: Experiment Tracker Synchronization

**Feature: unified-llm-platform, Property 13: Experiment tracker synchronization**
**Validates: Requirements 6.2, 6.3**

Property: For any training run with experiment tracking enabled, all metrics 
should be logged to the tracker within 30 seconds of generation.

This test verifies that:
1. Metrics are batched and sent to the tracker efficiently
2. All metrics eventually reach the tracker (no data loss)
3. Synchronization happens within the required time window
4. The system handles network delays and retries gracefully
"""

import pytest
import pytest_asyncio
from hypothesis import given, strategies as st, settings, assume
from hypothesis import HealthCheck
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from plugins.connectors.wandb_connector import WandBConnector
from connectors.base import TrainingConfig


# Strategy for generating metric dictionaries
@st.composite
def metric_dict_strategy(draw):
    """Generate realistic training metrics."""
    num_metrics = draw(st.integers(min_value=1, max_value=10))
    metrics = {}
    
    # Common metric names
    metric_names = [
        "loss", "train_loss", "val_loss", "accuracy", "learning_rate",
        "grad_norm", "epoch", "perplexity", "f1_score", "precision"
    ]
    
    selected_names = draw(st.lists(
        st.sampled_from(metric_names),
        min_size=num_metrics,
        max_size=num_metrics,
        unique=True
    ))
    
    for name in selected_names:
        if name in ["epoch"]:
            # Integer metrics
            metrics[name] = draw(st.integers(min_value=0, max_value=100))
        else:
            # Float metrics
            metrics[name] = draw(st.floats(
                min_value=0.0,
                max_value=100.0,
                allow_nan=False,
                allow_infinity=False
            ))
    
    return metrics


# Strategy for generating training configurations
@st.composite
def training_config_strategy(draw):
    """Generate valid training configurations."""
    algorithms = ["lora", "qlora", "dora", "pissa", "rslora"]
    model_sources = ["huggingface", "civitai", "ollama"]
    
    return TrainingConfig(
        base_model=draw(st.sampled_from([
            "meta-llama/Llama-2-7b-hf",
            "mistralai/Mistral-7B-v0.1",
            "google/gemma-7b"
        ])),
        model_source=draw(st.sampled_from(model_sources)),
        algorithm=draw(st.sampled_from(algorithms)),
        rank=draw(st.integers(min_value=8, max_value=64)),
        alpha=draw(st.integers(min_value=16, max_value=128)),
        dropout=draw(st.floats(min_value=0.0, max_value=0.3)),
        target_modules=["q_proj", "v_proj"],
        quantization=draw(st.sampled_from([None, "int4", "int8", "nf4"])),
        learning_rate=draw(st.floats(min_value=1e-5, max_value=1e-3)),
        batch_size=draw(st.integers(min_value=1, max_value=32)),
        gradient_accumulation_steps=draw(st.integers(min_value=1, max_value=8)),
        num_epochs=draw(st.integers(min_value=1, max_value=10)),
        warmup_steps=draw(st.integers(min_value=0, max_value=500)),
        provider="wandb",
        dataset_path="/tmp/dataset.json",
        experiment_tracker="wandb",
        project_name=draw(st.text(
            alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'), whitelist_characters='-_'),
            min_size=3,
            max_size=20
        )),
    )


class MockWandBAPI:
    """Mock W&B API for testing without actual API calls."""
    
    def __init__(self):
        self.runs = {}
        self.metrics = {}  # run_id -> list of metric entries
        self.metric_timestamps = {}  # run_id -> list of (metric, timestamp)
        self.artifacts = {}
        self.connected = False
        self.api_key = None
        self.entity = "test-user"
    
    def connect(self, api_key: str) -> bool:
        """Simulate connection."""
        self.api_key = api_key
        self.connected = True
        return True
    
    def create_run(self, config: Dict) -> str:
        """Simulate run creation."""
        run_id = f"run_{len(self.runs)}"
        self.runs[run_id] = {
            "id": run_id,
            "config": config,
            "state": "running",
            "created_at": datetime.now().isoformat(),
        }
        self.metrics[run_id] = []
        self.metric_timestamps[run_id] = []
        return run_id
    
    def log_metrics(self, run_id: str, metrics: List[Dict], timestamp: datetime):
        """Simulate metric logging with timestamp tracking."""
        if run_id not in self.metrics:
            return
        
        for metric in metrics:
            self.metrics[run_id].append(metric)
            self.metric_timestamps[run_id].append((metric, timestamp))
    
    def get_metrics(self, run_id: str) -> List[Dict]:
        """Get all logged metrics for a run."""
        return self.metrics.get(run_id, [])
    
    def get_metric_timestamps(self, run_id: str) -> List[tuple]:
        """Get metrics with their logging timestamps."""
        return self.metric_timestamps.get(run_id, [])


@pytest.fixture
def mock_wandb_api():
    """Provide a mock W&B API."""
    return MockWandBAPI()


@pytest_asyncio.fixture
async def wandb_connector_with_mock(mock_wandb_api):
    """Provide a W&B connector with mocked API."""
    connector = WandBConnector()
    
    # Replace API calls with mock
    connector._mock_api = mock_wandb_api
    
    # Mock the connect method
    original_connect = connector.connect
    
    async def mock_connect(credentials: Dict[str, str]) -> bool:
        connector._api_key = credentials.get("api_key")
        connector._entity = "test-user"
        connector._connected = mock_wandb_api.connect(connector._api_key)
        return connector._connected
    
    connector.connect = mock_connect
    
    # Mock the submit_job method to use mock API
    original_submit_job = connector.submit_job
    
    async def mock_submit_job(config: TrainingConfig) -> str:
        if not connector._connected:
            raise RuntimeError("Not connected to W&B")
        
        job_id = f"job_{len(connector._runs)}"
        
        run_config = {
            "entity": connector._entity,
            "project": config.project_name,
            "config": {
                "base_model": config.base_model,
                "algorithm": config.algorithm,
                "rank": config.rank,
            }
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
    
    # Mock the _flush_metrics method to use mock API
    original_flush = connector._flush_metrics
    
    async def mock_flush_metrics(job_id: str):
        if job_id not in connector._metric_batches:
            return
        
        batch = connector._metric_batches[job_id]
        if not batch:
            return
        
        metrics_to_send = []
        while batch:
            metrics_to_send.append(batch.popleft())
        
        if not metrics_to_send:
            return
        
        run_info = connector._runs.get(job_id)
        if not run_info:
            return
        
        # Log to mock API with current timestamp
        mock_wandb_api.log_metrics(
            run_info['wandb_id'],
            metrics_to_send,
            datetime.now()
        )
    
    connector._flush_metrics = mock_flush_metrics
    
    # Connect
    await connector.connect({"api_key": "test_key_123"})
    
    yield connector
    
    # Cleanup
    await connector.disconnect()


@pytest.mark.asyncio
@given(
    config=training_config_strategy(),
    metrics_list=st.lists(
        metric_dict_strategy(),
        min_size=1,
        max_size=50  # Test with up to 50 metric updates
    )
)
@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_metrics_synchronized_within_time_window(
    wandb_connector_with_mock,
    config,
    metrics_list
):
    """
    Property: For any training run with experiment tracking enabled,
    all metrics should be logged to the tracker within 30 seconds of generation.
    
    This test:
    1. Creates a run
    2. Logs multiple metrics at different times
    3. Verifies all metrics are synchronized within 30 seconds
    4. Checks no metrics are lost
    """
    connector = wandb_connector_with_mock
    mock_api = connector._mock_api
    
    # Create a run
    job_id = await connector.submit_job(config)
    run_info = connector._runs[job_id]
    wandb_run_id = run_info['wandb_id']
    
    # Track when each metric was generated
    metric_generation_times = []
    
    # Log metrics with timestamps
    for step, metrics in enumerate(metrics_list):
        generation_time = datetime.now()
        metric_generation_times.append((metrics, generation_time))
        
        # Log metrics
        await connector.log_metrics(job_id, metrics, step)
        
        # Small delay between metrics to simulate real training
        await asyncio.sleep(0.01)
    
    # Force final flush
    await connector._flush_metrics(job_id)
    
    # Wait a bit for any pending operations
    await asyncio.sleep(0.1)
    
    # Verify all metrics were logged
    logged_metrics = mock_api.get_metrics(wandb_run_id)
    logged_with_timestamps = mock_api.get_metric_timestamps(wandb_run_id)
    
    # Property 1: No metrics should be lost
    assert len(logged_metrics) == len(metrics_list), \
        f"Expected {len(metrics_list)} metrics, but {len(logged_metrics)} were logged"
    
    # Property 2: All metrics should be synchronized within 30 seconds
    max_sync_delay = timedelta(seconds=30)
    
    for i, (original_metrics, generation_time) in enumerate(metric_generation_times):
        # Find corresponding logged metric
        if i < len(logged_with_timestamps):
            logged_metric, log_time = logged_with_timestamps[i]
            
            # Calculate synchronization delay
            sync_delay = log_time - generation_time
            
            # Verify delay is within acceptable window
            assert sync_delay <= max_sync_delay, \
                f"Metric {i} took {sync_delay.total_seconds():.2f}s to sync (max: 30s)"
            
            # Verify delay is non-negative (logged after generation)
            assert sync_delay >= timedelta(0), \
                f"Metric {i} has negative sync delay: {sync_delay.total_seconds():.2f}s"
    
    # Property 3: Metrics should maintain order
    for i in range(len(logged_metrics)):
        logged_step = logged_metrics[i].get("_step", 0)
        assert logged_step == i, \
            f"Metric at index {i} has incorrect step {logged_step}"


@pytest.mark.asyncio
@given(
    config=training_config_strategy(),
    num_metrics=st.integers(min_value=10, max_value=200)
)
@settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_batching_efficiency(
    wandb_connector_with_mock,
    config,
    num_metrics
):
    """
    Property: Batching should reduce API calls while maintaining synchronization.
    
    This test verifies that:
    1. Multiple metrics are batched together
    2. Batches are sent efficiently
    3. All metrics still arrive within the time window
    """
    connector = wandb_connector_with_mock
    mock_api = connector._mock_api
    
    # Create a run
    job_id = await connector.submit_job(config)
    run_info = connector._runs[job_id]
    wandb_run_id = run_info['wandb_id']
    
    start_time = datetime.now()
    
    # Log many metrics rapidly
    for step in range(num_metrics):
        metrics = {
            "loss": 1.0 / (step + 1),
            "accuracy": step / num_metrics,
        }
        await connector.log_metrics(job_id, metrics, step)
    
    # Force flush
    await connector._flush_metrics(job_id)
    
    end_time = datetime.now()
    total_time = (end_time - start_time).total_seconds()
    
    # Verify all metrics were logged
    logged_metrics = mock_api.get_metrics(wandb_run_id)
    assert len(logged_metrics) == num_metrics, \
        f"Expected {num_metrics} metrics, but {len(logged_metrics)} were logged"
    
    # Verify synchronization was fast (batching should make it efficient)
    assert total_time < 30, \
        f"Synchronization took {total_time:.2f}s (should be < 30s)"


@pytest.mark.asyncio
async def test_synchronization_with_network_delay(wandb_connector_with_mock):
    """
    Test that synchronization handles simulated network delays gracefully.
    """
    connector = wandb_connector_with_mock
    mock_api = connector._mock_api
    
    config = TrainingConfig(
        base_model="test-model",
        model_source="huggingface",
        algorithm="lora",
        rank=16,
        alpha=32,
        dropout=0.1,
        target_modules=["q_proj", "v_proj"],
        dataset_path="/tmp/test.json",
        experiment_tracker="wandb",
        project_name="test-project",
    )
    
    job_id = await connector.submit_job(config)
    run_info = connector._runs[job_id]
    wandb_run_id = run_info['wandb_id']
    
    # Log metrics
    for step in range(10):
        metrics = {"loss": 1.0 / (step + 1)}
        await connector.log_metrics(job_id, metrics, step)
        
        # Simulate network delay
        await asyncio.sleep(0.05)
    
    # Flush
    await connector._flush_metrics(job_id)
    
    # Verify all metrics arrived
    logged_metrics = mock_api.get_metrics(wandb_run_id)
    assert len(logged_metrics) == 10


@pytest.mark.asyncio
async def test_no_data_loss_on_disconnect(wandb_connector_with_mock):
    """
    Test that metrics are flushed before disconnect to prevent data loss.
    """
    connector = wandb_connector_with_mock
    mock_api = connector._mock_api
    
    config = TrainingConfig(
        base_model="test-model",
        model_source="huggingface",
        algorithm="lora",
        rank=16,
        alpha=32,
        dropout=0.1,
        target_modules=["q_proj", "v_proj"],
        dataset_path="/tmp/test.json",
        experiment_tracker="wandb",
        project_name="test-project",
    )
    
    job_id = await connector.submit_job(config)
    run_info = connector._runs[job_id]
    wandb_run_id = run_info['wandb_id']
    
    # Log metrics without flushing
    for step in range(5):
        metrics = {"loss": 1.0 / (step + 1)}
        await connector.log_metrics(job_id, metrics, step)
    
    # Disconnect (should trigger flush)
    await connector.disconnect()
    
    # Verify all metrics were flushed before disconnect
    logged_metrics = mock_api.get_metrics(wandb_run_id)
    assert len(logged_metrics) == 5, \
        "Metrics should be flushed before disconnect to prevent data loss"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
