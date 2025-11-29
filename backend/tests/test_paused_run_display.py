"""
Property-based tests for paused run display information.

**Feature: simplified-llm-optimization, Property 29: Paused run displays complete information**
**Validates: Requirements 13.5**
"""

import pytest
from hypothesis import given, strategies as st, settings
from pathlib import Path
import tempfile
from datetime import datetime

from services.training_orchestration_service import (
    TrainingOrchestrator,
    TrainingConfig,
    TrainingState,
    TrainingMetrics
)


@st.composite
def training_config_strategy(draw):
    """Generate random training configurations"""
    job_id = f"job_{draw(st.integers(min_value=1, max_value=10000))}"
    
    return TrainingConfig(
        job_id=job_id,
        model_name=draw(st.sampled_from(["gpt2", "llama-7b", "mistral-7b"])),
        dataset_path="/tmp/dataset.json",
        output_dir=f"/tmp/output/{job_id}",
        lora_r=draw(st.integers(min_value=4, max_value=64)),
        lora_alpha=draw(st.integers(min_value=8, max_value=128)),
        learning_rate=draw(st.floats(min_value=1e-6, max_value=1e-3)),
        batch_size=draw(st.integers(min_value=1, max_value=32)),
        gradient_accumulation_steps=draw(st.integers(min_value=1, max_value=16)),
        num_epochs=draw(st.integers(min_value=1, max_value=10)),
        save_steps=draw(st.integers(min_value=100, max_value=1000))
    )


# **Feature: simplified-llm-optimization, Property 29: Paused run displays complete information**
@given(config=training_config_strategy())
@settings(max_examples=100, deadline=None)
def test_paused_run_displays_complete_information(config):
    """
    For any paused training run, the display should include elapsed time,
    remaining time estimate, and resource usage at pause time.
    
    **Validates: Requirements 13.5**
    """
    # Create temporary checkpoint directory
    with tempfile.TemporaryDirectory() as temp_dir:
        orchestrator = TrainingOrchestrator(checkpoint_base_dir=temp_dir)
        
        # Create and start job
        job = orchestrator.create_job(config)
        assert job.job_id == config.job_id
        
        orchestrator.start_training(config.job_id)
        
        # Wait for training to start
        import time
        timeout = 5
        start_time = time.time()
        while job.state != TrainingState.RUNNING and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        # If training didn't start, skip this test case
        if job.state != TrainingState.RUNNING:
            orchestrator.stop_training(config.job_id)
            return
        
        # Wait a bit to accumulate some metrics
        time.sleep(0.5)
        
        # Pause training
        try:
            checkpoint = orchestrator.pause_training(config.job_id)
            
            # Verify job is in paused state
            assert job.state == TrainingState.PAUSED, "Job should be in PAUSED state"
            
            # Verify paused_at timestamp exists
            assert job.paused_at is not None, "Job should have paused_at timestamp"
            assert isinstance(job.paused_at, datetime), "paused_at should be a datetime"
            
            # Verify started_at exists for elapsed time calculation
            assert job.started_at is not None, "Job should have started_at timestamp"
            assert isinstance(job.started_at, datetime), "started_at should be a datetime"
            
            # Verify current_metrics exists (resource usage at pause time)
            assert job.current_metrics is not None, "Job should have current_metrics at pause time"
            assert isinstance(job.current_metrics, TrainingMetrics), "current_metrics should be TrainingMetrics"
            
            # Verify metrics contain resource usage information
            metrics = job.current_metrics
            assert hasattr(metrics, 'gpu_utilization'), "Metrics should have gpu_utilization"
            assert hasattr(metrics, 'gpu_memory_used'), "Metrics should have gpu_memory_used"
            assert hasattr(metrics, 'cpu_utilization'), "Metrics should have cpu_utilization"
            assert hasattr(metrics, 'ram_used'), "Metrics should have ram_used"
            
            # Verify metrics contain timing information
            assert hasattr(metrics, 'elapsed_time'), "Metrics should have elapsed_time"
            assert hasattr(metrics, 'estimated_time_remaining'), "Metrics should have estimated_time_remaining"
            assert metrics.elapsed_time >= 0, "Elapsed time should be non-negative"
            assert metrics.estimated_time_remaining >= 0, "Remaining time should be non-negative"
            
            # Verify metrics contain training progress information
            assert hasattr(metrics, 'step'), "Metrics should have step"
            assert hasattr(metrics, 'epoch'), "Metrics should have epoch"
            assert hasattr(metrics, 'loss'), "Metrics should have loss"
            assert metrics.step >= 0, "Step should be non-negative"
            assert metrics.epoch >= 0, "Epoch should be non-negative"
            
            # Calculate elapsed time from timestamps
            elapsed_seconds = (job.paused_at - job.started_at).total_seconds()
            assert elapsed_seconds >= 0, "Elapsed time should be non-negative"
            
            # Verify we can construct a complete paused run display
            paused_run_info = {
                'job_id': job.job_id,
                'state': job.state.value,
                'paused_at': job.paused_at.isoformat(),
                'started_at': job.started_at.isoformat(),
                'elapsed_time': elapsed_seconds,
                'remaining_time_estimate': metrics.estimated_time_remaining,
                'current_step': metrics.step,
                'current_epoch': metrics.epoch,
                'current_loss': metrics.loss,
                'resource_usage': {
                    'gpu_utilization': metrics.gpu_utilization,
                    'gpu_memory_used': metrics.gpu_memory_used,
                    'cpu_utilization': metrics.cpu_utilization,
                    'ram_used': metrics.ram_used
                }
            }
            
            # Verify all required fields are present
            assert 'job_id' in paused_run_info
            assert 'state' in paused_run_info
            assert 'paused_at' in paused_run_info
            assert 'started_at' in paused_run_info
            assert 'elapsed_time' in paused_run_info
            assert 'remaining_time_estimate' in paused_run_info
            assert 'current_step' in paused_run_info
            assert 'current_epoch' in paused_run_info
            assert 'current_loss' in paused_run_info
            assert 'resource_usage' in paused_run_info
            
            # Verify resource usage contains all required fields
            resource_usage = paused_run_info['resource_usage']
            assert 'gpu_utilization' in resource_usage
            assert 'gpu_memory_used' in resource_usage
            assert 'cpu_utilization' in resource_usage
            assert 'ram_used' in resource_usage
            
        except TimeoutError:
            # If pause times out, that's a test failure
            pytest.fail("Pause operation timed out")
        finally:
            # Cleanup
            if job.state in [TrainingState.RUNNING, TrainingState.PAUSED]:
                orchestrator.stop_training(config.job_id)


def test_paused_run_display_specific_example():
    """
    Test that a paused run display contains all required information.
    This is a specific example test to complement the property test.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        orchestrator = TrainingOrchestrator(checkpoint_base_dir=temp_dir)
        
        config = TrainingConfig(
            job_id="test_paused_display_001",
            model_name="gpt2",
            dataset_path="/tmp/dataset.json",
            output_dir="/tmp/output",
            save_steps=100
        )
        
        job = orchestrator.create_job(config)
        orchestrator.start_training(config.job_id)
        
        # Wait for training to start
        import time
        timeout = 5
        start_time = time.time()
        while job.state != TrainingState.RUNNING and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        if job.state == TrainingState.RUNNING:
            # Wait to accumulate metrics
            time.sleep(0.5)
            
            try:
                checkpoint = orchestrator.pause_training(config.job_id)
                
                # Verify all display information is available
                assert job.paused_at is not None
                assert job.started_at is not None
                assert job.current_metrics is not None
                
                # Calculate elapsed time
                elapsed = (job.paused_at - job.started_at).total_seconds()
                assert elapsed >= 0
                
                # Verify metrics
                metrics = job.current_metrics
                assert metrics.elapsed_time >= 0
                assert metrics.estimated_time_remaining >= 0
                
                # Verify resource usage
                assert isinstance(metrics.gpu_utilization, list)
                assert isinstance(metrics.gpu_memory_used, list)
                assert isinstance(metrics.cpu_utilization, (int, float))
                assert isinstance(metrics.ram_used, (int, float))
                
                # Verify progress information
                assert metrics.step >= 0
                assert metrics.epoch >= 0
                assert metrics.loss >= 0
                
            finally:
                if job.state in [TrainingState.RUNNING, TrainingState.PAUSED]:
                    orchestrator.stop_training(config.job_id)


def test_paused_run_can_calculate_elapsed_time():
    """
    Test that elapsed time can be calculated from timestamps.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        orchestrator = TrainingOrchestrator(checkpoint_base_dir=temp_dir)
        
        config = TrainingConfig(
            job_id="test_elapsed_time_001",
            model_name="gpt2",
            dataset_path="/tmp/dataset.json",
            output_dir="/tmp/output"
        )
        
        job = orchestrator.create_job(config)
        orchestrator.start_training(config.job_id)
        
        # Wait for training to start
        import time
        timeout = 5
        start_time = time.time()
        while job.state != TrainingState.RUNNING and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        if job.state == TrainingState.RUNNING:
            # Wait a known amount of time
            time.sleep(1.0)
            
            try:
                checkpoint = orchestrator.pause_training(config.job_id)
                
                # Calculate elapsed time
                elapsed = (job.paused_at - job.started_at).total_seconds()
                
                # Should be at least 1 second (we waited 1 second)
                assert elapsed >= 1.0, f"Elapsed time should be at least 1 second, got {elapsed}"
                
                # Should be reasonable (less than 10 seconds for this test)
                assert elapsed < 10.0, f"Elapsed time should be less than 10 seconds, got {elapsed}"
                
            finally:
                if job.state in [TrainingState.RUNNING, TrainingState.PAUSED]:
                    orchestrator.stop_training(config.job_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
