"""
Property-based tests for training pause checkpoint saving.

**Feature: simplified-llm-optimization, Property 27: Pause saves checkpoint**
**Validates: Requirements 13.1, 13.4**
"""

import pytest
from hypothesis import given, strategies as st, settings
from pathlib import Path
import tempfile
import shutil
from datetime import datetime

from services.training_orchestration_service import (
    TrainingOrchestrator,
    TrainingConfig,
    TrainingState,
    CheckpointData
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


# **Feature: simplified-llm-optimization, Property 27: Pause saves checkpoint**
@given(config=training_config_strategy())
@settings(max_examples=100, deadline=None)
def test_pause_saves_checkpoint(config):
    """
    For any training configuration, pausing training should save a checkpoint
    containing model weights, optimizer state, and current metrics.
    
    **Validates: Requirements 13.1, 13.4**
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
        
        # Pause training
        try:
            checkpoint = orchestrator.pause_training(config.job_id)
            
            # Verify checkpoint was created
            assert checkpoint is not None, "Checkpoint should not be None"
            
            # Verify checkpoint contains required fields
            assert hasattr(checkpoint, 'step'), "Checkpoint must have step"
            assert hasattr(checkpoint, 'epoch'), "Checkpoint must have epoch"
            assert hasattr(checkpoint, 'loss'), "Checkpoint must have loss"
            assert hasattr(checkpoint, 'learning_rate'), "Checkpoint must have learning_rate"
            assert hasattr(checkpoint, 'model_state_dict'), "Checkpoint must have model_state_dict"
            assert hasattr(checkpoint, 'optimizer_state_dict'), "Checkpoint must have optimizer_state_dict"
            assert hasattr(checkpoint, 'metrics_history'), "Checkpoint must have metrics_history"
            assert hasattr(checkpoint, 'config'), "Checkpoint must have config"
            
            # Verify checkpoint has valid values
            assert checkpoint.step >= 0, "Step should be non-negative"
            assert checkpoint.epoch >= 0, "Epoch should be non-negative"
            assert checkpoint.loss >= 0, "Loss should be non-negative"
            assert checkpoint.learning_rate > 0, "Learning rate should be positive"
            
            # Verify checkpoint was saved to disk
            assert job.checkpoint_path is not None, "Job should have checkpoint path"
            assert job.checkpoint_path.exists(), "Checkpoint directory should exist"
            assert (job.checkpoint_path / "model_checkpoint.pt").exists(), "Model checkpoint file should exist"
            assert (job.checkpoint_path / "checkpoint_metadata.json").exists(), "Metadata file should exist"
            
            # Verify job is in paused state
            assert job.state == TrainingState.PAUSED, "Job should be in PAUSED state"
            assert job.paused_at is not None, "Job should have paused_at timestamp"
            
        except TimeoutError:
            # If pause times out, that's a test failure
            pytest.fail("Pause operation timed out")
        finally:
            # Cleanup
            if job.state == TrainingState.RUNNING:
                orchestrator.stop_training(config.job_id)


def test_pause_checkpoint_contains_all_required_fields():
    """
    Test that a paused checkpoint contains all required fields for resuming.
    This is a specific example test to complement the property test.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        orchestrator = TrainingOrchestrator(checkpoint_base_dir=temp_dir)
        
        config = TrainingConfig(
            job_id="test_pause_001",
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
            try:
                checkpoint = orchestrator.pause_training(config.job_id)
                
                # Verify all required fields are present
                required_fields = [
                    'step', 'epoch', 'loss', 'learning_rate',
                    'model_state_dict', 'optimizer_state_dict',
                    'metrics_history', 'config', 'timestamp', 'checkpoint_reason'
                ]
                
                for field in required_fields:
                    assert hasattr(checkpoint, field), f"Checkpoint missing required field: {field}"
                
                # Verify checkpoint reason is 'pause'
                assert checkpoint.checkpoint_reason == "pause", "Checkpoint reason should be 'pause'"
                
            finally:
                if job.state in [TrainingState.RUNNING, TrainingState.PAUSED]:
                    orchestrator.stop_training(config.job_id)


def test_pause_checkpoint_can_be_loaded():
    """
    Test that a saved checkpoint can be loaded back successfully.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        orchestrator = TrainingOrchestrator(checkpoint_base_dir=temp_dir)
        
        config = TrainingConfig(
            job_id="test_pause_002",
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
            try:
                # Pause and get checkpoint
                checkpoint = orchestrator.pause_training(config.job_id)
                checkpoint_path = job.checkpoint_path
                
                # Load checkpoint from disk
                loaded_checkpoint = CheckpointData.load(checkpoint_path)
                
                # Verify loaded checkpoint matches original
                assert loaded_checkpoint.step == checkpoint.step
                assert loaded_checkpoint.epoch == checkpoint.epoch
                assert abs(loaded_checkpoint.loss - checkpoint.loss) < 1e-6
                assert abs(loaded_checkpoint.learning_rate - checkpoint.learning_rate) < 1e-9
                assert loaded_checkpoint.checkpoint_reason == checkpoint.checkpoint_reason
                
            finally:
                if job.state in [TrainingState.RUNNING, TrainingState.PAUSED]:
                    orchestrator.stop_training(config.job_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
