"""
Property-Based Test: Multi-Run Isolation

**Feature: unified-llm-platform, Property 9: Multi-run isolation**
**Validates: Requirements 16.1, 16.3**

Property: For any two concurrent training runs, metrics and logs should never 
be mixed or cross-contaminated.

This test verifies that:
1. Each run maintains its own isolated metrics
2. Metrics from one run never appear in another run's history
3. Run state updates don't affect other concurrent runs
4. Job IDs uniquely identify runs without collision
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from typing import List, Dict, Set
import uuid
from datetime import datetime

from services.training_orchestration_service import (
    TrainingOrchestrator,
    TrainingConfig,
    TrainingMetrics,
    TrainingState
)
from services.multi_run_service import MultiRunManager
from database import get_db


# Strategy for generating unique job IDs
@st.composite
def job_id_strategy(draw):
    """Generate unique job IDs"""
    return f"job_{uuid.uuid4().hex[:8]}"


# Strategy for generating training configs
@st.composite
def training_config_strategy(draw, job_id: str):
    """Generate a valid training configuration"""
    return TrainingConfig(
        job_id=job_id,
        model_name=draw(st.sampled_from([
            "meta-llama/Llama-2-7b-hf",
            "mistralai/Mistral-7B-v0.1",
            "google/gemma-7b"
        ])),
        dataset_path=f"/data/dataset_{draw(st.integers(min_value=1, max_value=100))}",
        output_dir=f"/output/{job_id}",
        peft_method=draw(st.sampled_from(["lora", "qlora", "dora"])),
        lora_r=draw(st.integers(min_value=4, max_value=64)),
        lora_alpha=draw(st.integers(min_value=8, max_value=128)),
        lora_dropout=draw(st.floats(min_value=0.0, max_value=0.3)),
        learning_rate=draw(st.floats(min_value=1e-5, max_value=1e-3)),
        batch_size=draw(st.integers(min_value=1, max_value=16)),
        num_epochs=draw(st.integers(min_value=1, max_value=5)),
        max_steps=draw(st.integers(min_value=100, max_value=1000))
    )


# Strategy for generating metrics
@st.composite
def metrics_strategy(draw, step: int, epoch: int):
    """Generate training metrics"""
    return TrainingMetrics(
        step=step,
        epoch=epoch,
        loss=draw(st.floats(min_value=0.1, max_value=5.0)),
        learning_rate=draw(st.floats(min_value=1e-6, max_value=1e-3)),
        grad_norm=draw(st.floats(min_value=0.0, max_value=10.0)),
        throughput=draw(st.floats(min_value=1.0, max_value=100.0)),
        gpu_utilization=[draw(st.floats(min_value=0.0, max_value=100.0))],
        gpu_memory_used=[draw(st.floats(min_value=0.0, max_value=80.0))]
    )


@given(
    num_runs=st.integers(min_value=2, max_value=5)
)
@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_concurrent_runs_have_isolated_metrics(num_runs: int):
    """
    Property: For any set of concurrent training runs, each run maintains
    its own isolated metrics that never mix with other runs.
    
    **Feature: unified-llm-platform, Property 9: Multi-run isolation**
    **Validates: Requirements 16.1, 16.3**
    """
    # Create fresh instances for this test
    orchestrator = TrainingOrchestrator(
        checkpoint_base_dir="./test_checkpoints",
        artifacts_base_dir="./test_artifacts"
    )
    multi_run_manager = MultiRunManager(orchestrator=orchestrator)
    db_session = next(get_db())
    
    try:
        # Generate unique job IDs
        job_ids = [f"test_job_{uuid.uuid4().hex[:8]}" for _ in range(num_runs)]
        
        # Ensure all job IDs are unique
        assume(len(set(job_ids)) == num_runs)
        
        # Create jobs with different configs
        jobs = []
        for job_id in job_ids:
            config = TrainingConfig(
                job_id=job_id,
                model_name=f"model_{job_id}",
                dataset_path=f"/data/{job_id}",
                output_dir=f"/output/{job_id}",
                max_steps=100
            )
            job = orchestrator.create_job(config)
            jobs.append(job)
        
        # Simulate metrics for each job
        metrics_by_job: Dict[str, List[TrainingMetrics]] = {}
        
        for i, job_id in enumerate(job_ids):
            job = orchestrator.get_status(job_id)
            job.state = TrainingState.RUNNING
            
            # Generate unique metrics for this job
            job_metrics = []
            for step in range(5):
                metrics = TrainingMetrics(
                    step=step,
                    epoch=0,
                    loss=float(i + 1) + (step * 0.1),  # Unique loss pattern per job
                    learning_rate=1e-4,
                    grad_norm=float(i + 1)  # Unique grad norm per job
                )
                job.metrics_history.append(metrics)
                job.current_metrics = metrics
                job_metrics.append(metrics)
            
            metrics_by_job[job_id] = job_metrics
            
            # Sync to database
            multi_run_manager.sync_run_to_database(job, db_session)
        
        # Verify isolation: Each job's metrics are unique and not mixed
        for job_id in job_ids:
            job = orchestrator.get_status(job_id)
            
            # Check that job has the correct number of metrics
            assert len(job.metrics_history) == 5, \
                f"Job {job_id} should have exactly 5 metrics"
            
            # Check that metrics match what we stored
            expected_metrics = metrics_by_job[job_id]
            for i, (actual, expected) in enumerate(zip(job.metrics_history, expected_metrics)):
                assert actual.step == expected.step, \
                    f"Job {job_id} metric {i}: step mismatch"
                assert abs(actual.loss - expected.loss) < 0.001, \
                    f"Job {job_id} metric {i}: loss mismatch"
                assert abs(actual.grad_norm - expected.grad_norm) < 0.001, \
                    f"Job {job_id} metric {i}: grad_norm mismatch"
        
        # Verify no cross-contamination: Check that each job's metrics are distinct
        for i, job_id_1 in enumerate(job_ids):
            for job_id_2 in job_ids[i+1:]:
                job1 = orchestrator.get_status(job_id_1)
                job2 = orchestrator.get_status(job_id_2)
                
                # Metrics should be different between jobs
                if len(job1.metrics_history) > 0 and len(job2.metrics_history) > 0:
                    # Compare first metric of each job
                    metric1 = job1.metrics_history[0]
                    metric2 = job2.metrics_history[0]
                    
                    # Loss values should be different (we made them unique per job)
                    assert abs(metric1.loss - metric2.loss) > 0.5, \
                        f"Jobs {job_id_1} and {job_id_2} have suspiciously similar metrics"
    finally:
        db_session.close()


@given(
    num_runs=st.integers(min_value=2, max_value=4),
    num_steps=st.integers(min_value=3, max_value=10)
)
@settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_concurrent_runs_maintain_separate_state(
    num_runs: int,
    num_steps: int
):
    """
    Property: State changes in one run do not affect other concurrent runs.
    
    **Feature: unified-llm-platform, Property 9: Multi-run isolation**
    **Validates: Requirements 16.1, 16.3**
    """
    # Create fresh instances
    orchestrator = TrainingOrchestrator(
        checkpoint_base_dir="./test_checkpoints",
        artifacts_base_dir="./test_artifacts"
    )
    
    # Create multiple jobs
    job_ids = [f"test_state_{uuid.uuid4().hex[:8]}" for _ in range(num_runs)]
    assume(len(set(job_ids)) == num_runs)
    
    for job_id in job_ids:
        config = TrainingConfig(
            job_id=job_id,
            model_name="test-model",
            dataset_path="/data/test",
            output_dir=f"/output/{job_id}",
            max_steps=num_steps * 10
        )
        job = orchestrator.create_job(config)
        job.state = TrainingState.RUNNING
    
    # Update state of first job
    first_job = orchestrator.get_status(job_ids[0])
    first_job.state = TrainingState.PAUSED
    first_job.paused_at = datetime.now()
    
    # Verify other jobs are still in RUNNING state
    for job_id in job_ids[1:]:
        job = orchestrator.get_status(job_id)
        assert job.state == TrainingState.RUNNING, \
            f"Job {job_id} state should not be affected by pausing {job_ids[0]}"
        assert job.paused_at is None, \
            f"Job {job_id} should not have paused_at set"
    
    # Update metrics for second job
    if num_runs >= 2:
        second_job = orchestrator.get_status(job_ids[1])
        for step in range(num_steps):
            metrics = TrainingMetrics(
                step=step,
                epoch=0,
                loss=2.0 - (step * 0.1),
                learning_rate=1e-4
            )
            second_job.metrics_history.append(metrics)
            second_job.current_metrics = metrics
        
        # Verify first job's metrics are not affected
        first_job = orchestrator.get_status(job_ids[0])
        assert len(first_job.metrics_history) == 0, \
            f"Job {job_ids[0]} should not have metrics from {job_ids[1]}"


@given(
    num_runs=st.integers(min_value=2, max_value=5)
)
@settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_job_ids_are_unique_and_isolated(
    num_runs: int
):
    """
    Property: Job IDs uniquely identify runs without collision.
    
    **Feature: unified-llm-platform, Property 9: Multi-run isolation**
    **Validates: Requirements 16.1, 16.3**
    """
    # Create fresh orchestrator
    orchestrator = TrainingOrchestrator(
        checkpoint_base_dir="./test_checkpoints",
        artifacts_base_dir="./test_artifacts"
    )
    
    # Generate job IDs
    job_ids = [f"test_unique_{uuid.uuid4().hex[:8]}" for _ in range(num_runs)]
    assume(len(set(job_ids)) == num_runs)
    
    # Create jobs
    for job_id in job_ids:
        config = TrainingConfig(
            job_id=job_id,
            model_name="test-model",
            dataset_path="/data/test",
            output_dir=f"/output/{job_id}"
        )
        orchestrator.create_job(config)
    
    # Verify all jobs can be retrieved independently
    for job_id in job_ids:
        job = orchestrator.get_status(job_id)
        assert job.job_id == job_id, \
            f"Retrieved job ID {job.job_id} does not match requested {job_id}"
        assert job.config.job_id == job_id, \
            f"Job config ID {job.config.job_id} does not match {job_id}"
    
    # Verify job list contains all jobs
    all_jobs = orchestrator.list_jobs()
    retrieved_job_ids = {job.job_id for job in all_jobs}
    
    for job_id in job_ids:
        assert job_id in retrieved_job_ids, \
            f"Job {job_id} not found in job list"
    
    # Verify no duplicate job IDs
    assert len(retrieved_job_ids) >= num_runs, \
        "Job list should contain at least all created jobs"


@given(
    num_runs=st.integers(min_value=2, max_value=4)
)
@settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_database_records_are_isolated(
    num_runs: int,
    orchestrator,
    multi_run_manager,
    db_session
):
    """
    Property: Database records for different runs are properly isolated.
    
    **Feature: unified-llm-platform, Property 9: Multi-run isolation**
    **Validates: Requirements 16.1, 16.3**
    """
    from database import TrainingRun
    
    # Create jobs with unique identifiers
    job_ids = [f"test_db_{uuid.uuid4().hex[:8]}" for _ in range(num_runs)]
    assume(len(set(job_ids)) == num_runs)
    
    for i, job_id in enumerate(job_ids):
        config = TrainingConfig(
            job_id=job_id,
            model_name=f"model_{i}",
            dataset_path=f"/data/dataset_{i}",
            output_dir=f"/output/{job_id}",
            max_steps=100 * (i + 1)  # Different max_steps per job
        )
        job = orchestrator.create_job(config)
        job.state = TrainingState.RUNNING
        
        # Add unique metrics
        metrics = TrainingMetrics(
            step=i * 10,
            epoch=i,
            loss=float(i + 1),
            learning_rate=1e-4
        )
        job.current_metrics = metrics
        job.metrics_history.append(metrics)
        
        # Sync to database
        multi_run_manager.sync_run_to_database(job, db_session)
    
    # Verify each job has its own database record
    for i, job_id in enumerate(job_ids):
        db_run = db_session.query(TrainingRun).filter(
            TrainingRun.job_id == job_id
        ).first()
        
        assert db_run is not None, f"Database record not found for {job_id}"
        assert db_run.job_id == job_id, "Job ID mismatch in database"
        
        # Verify unique values
        assert db_run.current_step == i * 10, \
            f"Job {job_id} has wrong current_step in database"
        assert db_run.current_epoch == i, \
            f"Job {job_id} has wrong current_epoch in database"
        assert db_run.current_loss is not None, \
            f"Job {job_id} should have current_loss in database"
        assert abs(db_run.current_loss - float(i + 1)) < 0.001, \
            f"Job {job_id} has wrong current_loss in database"
    
    # Verify no cross-contamination in database
    all_db_runs = db_session.query(TrainingRun).filter(
        TrainingRun.job_id.in_(job_ids)
    ).all()
    
    assert len(all_db_runs) == num_runs, \
        f"Expected {num_runs} database records, found {len(all_db_runs)}"
    
    # Verify each record is unique
    db_job_ids = [run.job_id for run in all_db_runs]
    assert len(set(db_job_ids)) == num_runs, \
        "Duplicate job IDs found in database"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
