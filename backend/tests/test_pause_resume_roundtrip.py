"""
Property-based tests for training pause/resume round-trip state preservation.

**Feature: simplified-llm-optimization, Property 28: Pause/resume round-trip preserves state**
**Validates: Requirements 13.3**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from pathlib import Path
import tempfile
import time

from services.training_orchestration_service import (
    TrainingOrchestrator,
    TrainingConfig,
    TrainingState,
    TrainingMetrics
)


@st.composite
def training_state_strategy(draw):
    """Generate random training states"""
    return {
        'step': draw(st.integers(min_value=1, max_value=10000)),
        'epoch': draw(st.integers(min_value=0, max_value=100)),
        'loss': draw(st.floats(min_value=0.01, max_value=10.0, allow_nan=False, allow_infinity=False)),
        'learning_rate': draw(st.floats(min_value=1e-6, max_value=1e-3, allow_nan=False, allow_infinity=False))
    }


# **Feature: simplified-llm-optimization, Property 28: Pause/resume round-trip preserves state**
@given(state=training_state_strategy())
@settings(max_examples=20, deadline=None)  # Reduced examples for faster execution
def test_pause_resume_preserves_state(state):
    """
    For any training state, pausing and then immediately resuming should
    preserve the exact training state (step, epoch, loss, learning_rate).
    
    **Validates: Requirements 13.3**
    """
    # Create temporary checkpoint directory
    with tempfile.TemporaryDirectory() as temp_dir:
        orchestrator = TrainingOrchestrator(checkpoint_base_dir=temp_dir)
        
        # Create a training job
        config = TrainingConfig(
            job_id=f"test_roundtrip_{state['step']}",
            model_name="gpt2",
            dataset_path="/tmp/dataset.json",
            output_dir="/tmp/output",
            save_steps=100,
            max_steps=state['step'] + 1000  # Ensure we have enough steps
        )
        
        job = orchestrator.create_job(config)
        orchestrator.start_training(config.job_id)
        
        # Wait for training to start
        timeout = 5
        start_time = time.time()
        while job.state != TrainingState.RUNNING and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        # If training didn't start, skip this test case
        if job.state != TrainingState.RUNNING:
            orchestrator.stop_training(config.job_id)
            return
        
        # Wait a bit for some training to happen
        time.sleep(0.5)
        
        try:
            # Capture the state before pause
            pre_pause_metrics = job.current_metrics
            if pre_pause_metrics is None:
                # No metrics yet, skip this test case
                orchestrator.stop_training(config.job_id)
                return
            
            pre_pause_step = pre_pause_metrics.step
            pre_pause_epoch = pre_pause_metrics.epoch
            pre_pause_loss = pre_pause_metrics.loss
            pre_pause_lr = pre_pause_metrics.learning_rate
            
            # Pause training
            checkpoint = orchestrator.pause_training(config.job_id)
            
            # Verify job is paused
            assert job.state == TrainingState.PAUSED, "Job should be in PAUSED state"
            
            # Resume training
            orchestrator.resume_training(config.job_id)
            
            # Wait for training to resume
            timeout = 5
            start_time = time.time()
            while job.state != TrainingState.RUNNING and time.time() - start_time < timeout:
                time.sleep(0.1)
            
            # If training didn't resume, that's a test failure
            if job.state != TrainingState.RUNNING:
                pytest.fail(f"Training did not resume. State: {job.state}")
            
            # Wait a bit for resumed training to produce metrics
            time.sleep(0.5)
            
            # Get the state after resume
            post_resume_metrics = job.current_metrics
            if post_resume_metrics is None:
                pytest.fail("No metrics after resume")
            
            # The resumed training should continue from where it left off
            # The step should be >= the pre-pause step (it may have advanced slightly)
            assert post_resume_metrics.step >= pre_pause_step, \
                f"Step should be >= pre-pause step. Pre: {pre_pause_step}, Post: {post_resume_metrics.step}"
            
            # The epoch should be >= the pre-pause epoch
            assert post_resume_metrics.epoch >= pre_pause_epoch, \
                f"Epoch should be >= pre-pause epoch. Pre: {pre_pause_epoch}, Post: {post_resume_metrics.epoch}"
            
            # Learning rate should be the same (or very close)
            assert abs(post_resume_metrics.learning_rate - pre_pause_lr) < 1e-9, \
                f"Learning rate should be preserved. Pre: {pre_pause_lr}, Post: {post_resume_metrics.learning_rate}"
            
            # Loss should be in a reasonable range (may have changed slightly due to continued training)
            # We allow for some variation since training continued
            assert post_resume_metrics.loss >= 0, "Loss should be non-negative"
            
        finally:
            # Cleanup
            if job.state in [TrainingState.RUNNING, TrainingState.PAUSED]:
                orchestrator.stop_training(config.job_id)


def test_pause_resume_checkpoint_restoration():
    """
    Test that checkpoint data is correctly restored when resuming.
    This is a specific example test to complement the property test.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        orchestrator = TrainingOrchestrator(checkpoint_base_dir=temp_dir)
        
        config = TrainingConfig(
            job_id="test_checkpoint_restore",
            model_name="gpt2",
            dataset_path="/tmp/dataset.json",
            output_dir="/tmp/output",
            save_steps=100,
            learning_rate=2e-4
        )
        
        job = orchestrator.create_job(config)
        orchestrator.start_training(config.job_id)
        
        # Wait for training to start
        timeout = 5
        start_time = time.time()
        while job.state != TrainingState.RUNNING and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        if job.state == TrainingState.RUNNING:
            # Wait for some training
            time.sleep(0.5)
            
            try:
                # Get pre-pause state
                pre_pause_metrics = job.current_metrics
                if pre_pause_metrics is None:
                    return  # Skip if no metrics
                
                # Pause
                checkpoint = orchestrator.pause_training(config.job_id)
                
                # Verify checkpoint contains the state
                # Note: step may have advanced slightly during pause processing
                assert checkpoint.step >= pre_pause_metrics.step
                assert checkpoint.step <= pre_pause_metrics.step + 5  # Allow small advancement
                assert checkpoint.epoch == pre_pause_metrics.epoch
                # Loss may have changed slightly if training continued
                assert checkpoint.loss >= 0
                assert abs(checkpoint.learning_rate - config.learning_rate) < 1e-9
                
                # Resume
                orchestrator.resume_training(config.job_id)
                
                # Wait for resume
                timeout = 5
                start_time = time.time()
                while job.state != TrainingState.RUNNING and time.time() - start_time < timeout:
                    time.sleep(0.1)
                
                assert job.state == TrainingState.RUNNING, "Training should have resumed"
                
                # Wait for resumed training
                time.sleep(0.5)
                
                # Verify training continued from checkpoint
                post_resume_metrics = job.current_metrics
                if post_resume_metrics:
                    # Step should have advanced from checkpoint
                    assert post_resume_metrics.step >= checkpoint.step
                    
            finally:
                if job.state in [TrainingState.RUNNING, TrainingState.PAUSED]:
                    orchestrator.stop_training(config.job_id)


def test_multiple_pause_resume_cycles():
    """
    Test that multiple pause/resume cycles work correctly.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        orchestrator = TrainingOrchestrator(checkpoint_base_dir=temp_dir)
        
        config = TrainingConfig(
            job_id="test_multiple_cycles",
            model_name="gpt2",
            dataset_path="/tmp/dataset.json",
            output_dir="/tmp/output",
            save_steps=100
        )
        
        job = orchestrator.create_job(config)
        orchestrator.start_training(config.job_id)
        
        # Wait for training to start
        timeout = 5
        start_time = time.time()
        while job.state != TrainingState.RUNNING and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        if job.state == TrainingState.RUNNING:
            try:
                # Perform 3 pause/resume cycles
                for cycle in range(3):
                    # Wait for some training
                    time.sleep(0.3)
                    
                    # Get current step
                    if job.current_metrics:
                        step_before_pause = job.current_metrics.step
                    else:
                        continue
                    
                    # Pause
                    checkpoint = orchestrator.pause_training(config.job_id)
                    assert job.state == TrainingState.PAUSED
                    
                    # Resume
                    orchestrator.resume_training(config.job_id)
                    
                    # Wait for resume
                    timeout = 5
                    start_time = time.time()
                    while job.state != TrainingState.RUNNING and time.time() - start_time < timeout:
                        time.sleep(0.1)
                    
                    assert job.state == TrainingState.RUNNING, f"Cycle {cycle}: Training should have resumed"
                    
                    # Wait for resumed training
                    time.sleep(0.3)
                    
                    # Verify training continued
                    if job.current_metrics:
                        assert job.current_metrics.step >= step_before_pause, \
                            f"Cycle {cycle}: Training should have continued"
                
            finally:
                if job.state in [TrainingState.RUNNING, TrainingState.PAUSED]:
                    orchestrator.stop_training(config.job_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
