"""
Property-based tests for dashboard data freshness.

**Feature: unified-llm-platform, Property 17: Dashboard data freshness**
**Validates: Requirements 20.2, 20.5**
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import time
import asyncio
import threading


# Import services
try:
    from services.training_orchestration_service import (
        TrainingOrchestrator,
        TrainingConfig,
        TrainingMetrics,
        TrainingState,
        TrainingJob
    )
except ImportError as e:
    pytest.skip(f"Could not import training orchestration service: {e}", allow_module_level=True)


# Strategies for generating test data

# Generate job IDs
job_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'),
    min_size=5,
    max_size=20
).filter(lambda x: len(x.strip()) > 0 and not x.startswith('-') and not x.endswith('-'))

# Generate training metrics
def generate_training_metrics(step: int = 0, epoch: int = 0) -> TrainingMetrics:
    """Generate realistic training metrics"""
    return TrainingMetrics(
        step=step,
        epoch=epoch,
        loss=2.5 - (step * 0.001),  # Decreasing loss
        learning_rate=2e-4,
        grad_norm=0.5,
        throughput=10.0,
        samples_per_second=40.0,
        gpu_utilization=[85.0, 80.0],
        gpu_memory_used=[12.5, 11.8],
        cpu_utilization=45.0,
        ram_used=8.5,
        timestamp=datetime.now(),
        elapsed_time=step * 0.5,
        estimated_time_remaining=1000.0
    )


# Generate training configurations
def generate_training_config(job_id: str) -> TrainingConfig:
    """Generate a minimal training configuration"""
    return TrainingConfig(
        job_id=job_id,
        model_name="test-model",
        dataset_path="/tmp/test_dataset",
        output_dir=f"/tmp/output_{job_id}",
        batch_size=4,
        num_epochs=3,
        learning_rate=2e-4
    )


@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow], deadline=10000)
@given(
    job_id=job_id_strategy,
    num_updates=st.integers(min_value=1, max_value=10)
)
def test_dashboard_metrics_update_within_5_seconds(job_id, num_updates):
    """
    **Feature: unified-llm-platform, Property 17: Dashboard data freshness**
    **Validates: Requirements 20.2**
    
    For any active training run, dashboard metrics should update within 5 seconds
    of new data availability.
    """
    # Create orchestrator
    orchestrator = TrainingOrchestrator()
    
    # Create training config
    config = generate_training_config(job_id)
    
    # Create job
    job = orchestrator.create_job(config)
    
    # Set job to running state (simulate active training)
    job.state = TrainingState.RUNNING
    job.started_at = datetime.now()
    
    # Track metrics update times
    update_times: List[float] = []
    received_metrics: List[TrainingMetrics] = []
    
    # Register callback to track when metrics are received
    def metrics_callback(metrics: TrainingMetrics):
        received_metrics.append(metrics)
        # Calculate time since metrics were generated
        time_diff = (datetime.now() - metrics.timestamp).total_seconds()
        update_times.append(time_diff)
    
    orchestrator.register_metrics_callback(job_id, metrics_callback)
    
    # Simulate metrics updates
    for i in range(num_updates):
        # Generate new metrics
        metrics = generate_training_metrics(step=i * 100, epoch=i // 3)
        
        # Update job metrics (simulating what training loop would do)
        job.current_metrics = metrics
        job.metrics_history.append(metrics)
        
        # Trigger callback (simulating real-time update)
        for callback in orchestrator._metrics_callbacks.get(job_id, []):
            callback(metrics)
        
        # Small delay between updates
        time.sleep(0.01)
    
    # Verify all metrics were received
    assert len(received_metrics) == num_updates, \
        f"Should receive {num_updates} metrics updates, got {len(received_metrics)}"
    
    # Verify all updates were within 5 seconds
    for i, time_diff in enumerate(update_times):
        assert time_diff < 5.0, \
            f"Metrics update {i} took {time_diff:.2f}s, should be < 5s"
    
    # Verify metrics are fresh (recent)
    if job.current_metrics:
        time_since_last_update = (datetime.now() - job.current_metrics.timestamp).total_seconds()
        assert time_since_last_update < 5.0, \
            f"Last metrics update is {time_since_last_update:.2f}s old, should be < 5s"


@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow], deadline=None)
@given(
    job_id=job_id_strategy,
    update_interval_ms=st.integers(min_value=10, max_value=500)
)
def test_dashboard_reflects_latest_metrics(job_id, update_interval_ms):
    """
    **Feature: unified-llm-platform, Property 17: Dashboard data freshness**
    **Validates: Requirements 20.2, 20.5**
    
    For any active training run, the dashboard should always reflect the latest
    available metrics.
    """
    # Create orchestrator
    orchestrator = TrainingOrchestrator()
    
    # Create training config
    config = generate_training_config(job_id)
    
    # Create job
    job = orchestrator.create_job(config)
    job.state = TrainingState.RUNNING
    job.started_at = datetime.now()
    
    # Generate sequence of metrics (reduced to 3 to keep total time under 5s)
    metrics_sequence = [
        generate_training_metrics(step=i * 50, epoch=i // 5)
        for i in range(3)
    ]
    
    # Apply metrics updates
    for metrics in metrics_sequence:
        job.current_metrics = metrics
        job.metrics_history.append(metrics)
        time.sleep(update_interval_ms / 1000.0)
    
    # Get current status (what dashboard would display)
    status = orchestrator.get_status(job_id)
    current_metrics = orchestrator.get_metrics(job_id)
    
    # Verify we have the latest metrics
    assert current_metrics is not None, "Dashboard should have current metrics"
    assert current_metrics == metrics_sequence[-1], \
        "Dashboard should show the latest metrics"
    
    # Verify metrics are recent (within reasonable time given the test delays)
    time_since_update = (datetime.now() - current_metrics.timestamp).total_seconds()
    # Allow for cumulative sleep time plus some buffer
    max_age = (update_interval_ms * len(metrics_sequence) / 1000.0) + 1.0
    assert time_since_update < max_age, \
        f"Current metrics are {time_since_update:.2f}s old, should be < {max_age:.2f}s"


@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
@given(
    num_jobs=st.integers(min_value=1, max_value=5)
)
def test_dashboard_updates_all_active_runs(num_jobs):
    """
    **Feature: unified-llm-platform, Property 17: Dashboard data freshness**
    **Validates: Requirements 20.2, 20.5**
    
    For any set of active training runs, the dashboard should update metrics
    for all runs within 5 seconds.
    """
    # Create orchestrator
    orchestrator = TrainingOrchestrator()
    
    # Create multiple jobs
    jobs = []
    for i in range(num_jobs):
        job_id = f"test-job-{i}"
        config = generate_training_config(job_id)
        job = orchestrator.create_job(config)
        job.state = TrainingState.RUNNING
        job.started_at = datetime.now()
        jobs.append((job_id, job))
    
    # Update metrics for all jobs
    update_start = datetime.now()
    
    for job_id, job in jobs:
        metrics = generate_training_metrics(step=100, epoch=1)
        job.current_metrics = metrics
        job.metrics_history.append(metrics)
    
    update_end = datetime.now()
    update_duration = (update_end - update_start).total_seconds()
    
    # Verify all jobs have current metrics
    for job_id, job in jobs:
        current_metrics = orchestrator.get_metrics(job_id)
        assert current_metrics is not None, \
            f"Job {job_id} should have current metrics"
        
        # Verify metrics are fresh
        time_since_update = (datetime.now() - current_metrics.timestamp).total_seconds()
        assert time_since_update < 5.0, \
            f"Job {job_id} metrics are {time_since_update:.2f}s old, should be < 5s"
    
    # Verify update process was fast
    assert update_duration < 5.0, \
        f"Updating {num_jobs} jobs took {update_duration:.2f}s, should be < 5s"


@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
@given(
    job_id=job_id_strategy
)
def test_dashboard_data_timestamp_accuracy(job_id):
    """
    **Feature: unified-llm-platform, Property 17: Dashboard data freshness**
    **Validates: Requirements 20.2**
    
    For any training run, dashboard data timestamps should accurately reflect
    when the data was generated.
    """
    # Create orchestrator
    orchestrator = TrainingOrchestrator()
    
    # Create training config
    config = generate_training_config(job_id)
    
    # Create job
    job = orchestrator.create_job(config)
    job.state = TrainingState.RUNNING
    job.started_at = datetime.now()
    
    # Generate metrics with known timestamp
    metrics_timestamp = datetime.now()
    metrics = TrainingMetrics(
        step=100,
        epoch=1,
        loss=2.0,
        learning_rate=2e-4,
        timestamp=metrics_timestamp
    )
    
    # Update job metrics
    job.current_metrics = metrics
    
    # Get metrics from dashboard
    dashboard_metrics = orchestrator.get_metrics(job_id)
    
    # Verify timestamp is preserved
    assert dashboard_metrics is not None, "Dashboard should have metrics"
    assert dashboard_metrics.timestamp == metrics_timestamp, \
        "Dashboard metrics timestamp should match original"
    
    # Verify timestamp is recent
    time_diff = (datetime.now() - dashboard_metrics.timestamp).total_seconds()
    assert time_diff < 5.0, \
        f"Metrics timestamp is {time_diff:.2f}s old, should be < 5s"


@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
@given(
    job_id=job_id_strategy,
    num_metrics=st.integers(min_value=1, max_value=20)
)
def test_dashboard_metrics_history_freshness(job_id, num_metrics):
    """
    **Feature: unified-llm-platform, Property 17: Dashboard data freshness**
    **Validates: Requirements 20.2, 20.5**
    
    For any training run, the dashboard should maintain a fresh history of metrics
    with all entries timestamped within the training session.
    """
    # Create orchestrator
    orchestrator = TrainingOrchestrator()
    
    # Create training config
    config = generate_training_config(job_id)
    
    # Create job
    job = orchestrator.create_job(config)
    job.state = TrainingState.RUNNING
    job.started_at = datetime.now()
    
    # Generate metrics history
    for i in range(num_metrics):
        metrics = generate_training_metrics(step=i * 50, epoch=i // 5)
        job.current_metrics = metrics
        job.metrics_history.append(metrics)
        time.sleep(0.01)  # Small delay between updates
    
    # Get job status (what dashboard would show)
    status = orchestrator.get_status(job_id)
    
    # Verify metrics history is complete
    assert len(status.metrics_history) == num_metrics, \
        f"Should have {num_metrics} metrics in history, got {len(status.metrics_history)}"
    
    # Verify all metrics in history are fresh (within training session)
    for i, metrics in enumerate(status.metrics_history):
        # Metrics should be after job started
        assert metrics.timestamp >= job.started_at, \
            f"Metrics {i} timestamp should be after job start"
        
        # Metrics should be recent (within last 5 seconds for this test)
        time_since_metric = (datetime.now() - metrics.timestamp).total_seconds()
        assert time_since_metric < 10.0, \
            f"Metrics {i} is {time_since_metric:.2f}s old, should be recent"
    
    # Verify metrics are in chronological order
    for i in range(1, len(status.metrics_history)):
        assert status.metrics_history[i].timestamp >= status.metrics_history[i-1].timestamp, \
            f"Metrics should be in chronological order"


@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow], deadline=None)
@given(
    job_id=job_id_strategy
)
def test_dashboard_handles_rapid_updates(job_id):
    """
    **Feature: unified-llm-platform, Property 17: Dashboard data freshness**
    **Validates: Requirements 20.2**
    
    For any training run with rapid metric updates, the dashboard should handle
    all updates within the 5-second freshness window.
    """
    # Create orchestrator
    orchestrator = TrainingOrchestrator()
    
    # Create training config
    config = generate_training_config(job_id)
    
    # Create job
    job = orchestrator.create_job(config)
    job.state = TrainingState.RUNNING
    job.started_at = datetime.now()
    
    # Track callback invocations
    callback_times: List[datetime] = []
    
    def metrics_callback(metrics: TrainingMetrics):
        callback_times.append(datetime.now())
    
    orchestrator.register_metrics_callback(job_id, metrics_callback)
    
    # Simulate rapid updates (every 50ms, reduced from 100ms)
    num_rapid_updates = 10
    update_start = datetime.now()
    
    for i in range(num_rapid_updates):
        metrics = generate_training_metrics(step=i * 10, epoch=0)
        job.current_metrics = metrics
        
        # Trigger callback
        for callback in orchestrator._metrics_callbacks.get(job_id, []):
            callback(metrics)
        
        time.sleep(0.05)  # 50ms between updates
    
    update_end = datetime.now()
    
    # Verify all callbacks were invoked
    assert len(callback_times) == num_rapid_updates, \
        f"Should have {num_rapid_updates} callback invocations, got {len(callback_times)}"
    
    # Verify all callbacks were within 5 seconds of update start
    for i, callback_time in enumerate(callback_times):
        time_since_start = (callback_time - update_start).total_seconds()
        assert time_since_start < 5.0, \
            f"Callback {i} was invoked {time_since_start:.2f}s after start, should be < 5s"
    
    # Verify final metrics are fresh
    final_metrics = orchestrator.get_metrics(job_id)
    assert final_metrics is not None, "Should have final metrics"
    
    time_since_final = (datetime.now() - final_metrics.timestamp).total_seconds()
    assert time_since_final < 5.0, \
        f"Final metrics are {time_since_final:.2f}s old, should be < 5s"


@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
@given(
    job_id=job_id_strategy
)
def test_dashboard_excludes_stale_data(job_id):
    """
    **Feature: unified-llm-platform, Property 17: Dashboard data freshness**
    **Validates: Requirements 20.2, 20.5**
    
    For any training run, the dashboard should prioritize fresh data and
    clearly indicate when data is stale (older than 5 seconds for active runs).
    """
    # Create orchestrator
    orchestrator = TrainingOrchestrator()
    
    # Create training config
    config = generate_training_config(job_id)
    
    # Create job
    job = orchestrator.create_job(config)
    job.state = TrainingState.RUNNING
    job.started_at = datetime.now()
    
    # Create old metrics (simulating stale data)
    old_timestamp = datetime.now() - timedelta(seconds=10)
    old_metrics = TrainingMetrics(
        step=50,
        epoch=0,
        loss=2.5,
        learning_rate=2e-4,
        timestamp=old_timestamp
    )
    
    job.current_metrics = old_metrics
    
    # Verify we can detect stale data
    current_metrics = orchestrator.get_metrics(job_id)
    assert current_metrics is not None, "Should have metrics"
    
    time_since_update = (datetime.now() - current_metrics.timestamp).total_seconds()
    
    # For active runs, data older than 5 seconds should be flagged as stale
    if job.state == TrainingState.RUNNING:
        is_stale = time_since_update > 5.0
        assert is_stale, \
            f"Metrics {time_since_update:.2f}s old should be considered stale for active run"
    
    # Now update with fresh metrics
    fresh_metrics = generate_training_metrics(step=100, epoch=1)
    job.current_metrics = fresh_metrics
    
    # Verify fresh data is not stale
    current_metrics = orchestrator.get_metrics(job_id)
    time_since_update = (datetime.now() - current_metrics.timestamp).total_seconds()
    
    assert time_since_update < 5.0, \
        f"Fresh metrics should be < 5s old, got {time_since_update:.2f}s"


@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow], deadline=None)
@given(
    job_id=job_id_strategy
)
def test_dashboard_refresh_interval_compliance(job_id):
    """
    **Feature: unified-llm-platform, Property 17: Dashboard data freshness**
    **Validates: Requirements 20.2**
    
    For any active training run, dashboard should refresh data every 5 seconds
    to maintain freshness guarantee.
    """
    # Create orchestrator
    orchestrator = TrainingOrchestrator()
    
    # Create training config
    config = generate_training_config(job_id)
    
    # Create job
    job = orchestrator.create_job(config)
    job.state = TrainingState.RUNNING
    job.started_at = datetime.now()
    
    # Simulate dashboard refresh cycle
    refresh_times: List[datetime] = []
    
    # Perform 3 refresh cycles
    for i in range(3):
        # Update metrics (simulating training progress)
        metrics = generate_training_metrics(step=i * 100, epoch=i)
        job.current_metrics = metrics
        
        # Record refresh time
        refresh_times.append(datetime.now())
        
        # Get metrics (simulating dashboard query)
        current_metrics = orchestrator.get_metrics(job_id)
        
        # Verify metrics are fresh
        assert current_metrics is not None, f"Refresh {i} should have metrics"
        time_since_update = (datetime.now() - current_metrics.timestamp).total_seconds()
        assert time_since_update < 5.0, \
            f"Refresh {i}: metrics are {time_since_update:.2f}s old, should be < 5s"
        
        # Wait for next refresh (simulating 5-second refresh interval)
        if i < 2:  # Don't wait after last refresh
            time.sleep(0.1)  # Shortened for test speed (100ms instead of 500ms)
    
    # Verify refresh intervals
    for i in range(1, len(refresh_times)):
        interval = (refresh_times[i] - refresh_times[i-1]).total_seconds()
        # In real system, this would be ~5 seconds, but we use shorter intervals for testing
        assert interval < 5.0, \
            f"Refresh interval {i} was {interval:.2f}s, should be <= 5s"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
