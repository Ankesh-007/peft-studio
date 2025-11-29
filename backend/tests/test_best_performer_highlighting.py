"""
Property-based tests for best performer highlighting in training run comparisons.

**Feature: simplified-llm-optimization, Property 23: Comparison highlights best performers**
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime

from services.comparison_service import (
    ComparisonService,
    TrainingRunSummary,
    BestPerformer
)


# Strategy for generating valid training runs
def training_run_strategy(job_id_prefix: str = "job"):
    """Generate a valid training run summary"""
    return st.builds(
        TrainingRunSummary,
        job_id=st.integers(min_value=1000, max_value=9999).map(lambda x: f"{job_id_prefix}_{x}"),
        model_name=st.sampled_from(["llama-7b", "mistral-7b", "phi-2", "gemma-7b"]),
        dataset_name=st.sampled_from(["alpaca", "dolly", "oasst", "custom"]),
        final_loss=st.floats(min_value=0.1, max_value=5.0),
        best_val_loss=st.one_of(st.none(), st.floats(min_value=0.1, max_value=5.0)),
        final_learning_rate=st.floats(min_value=1e-6, max_value=1e-3),
        total_steps=st.integers(min_value=100, max_value=10000),
        epochs_completed=st.integers(min_value=1, max_value=10),
        training_time_seconds=st.floats(min_value=60.0, max_value=86400.0),
        config=st.fixed_dictionaries({
            'learning_rate': st.floats(min_value=1e-6, max_value=1e-3),
            'batch_size': st.integers(min_value=1, max_value=32),
            'lora_r': st.integers(min_value=4, max_value=64)
        }),
        quality_score=st.one_of(st.none(), st.floats(min_value=0.0, max_value=100.0)),
        started_at=st.just(datetime(2024, 1, 1)),
        completed_at=st.just(datetime(2024, 1, 2))
    )


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    runs=st.lists(training_run_strategy(), min_size=2, max_size=5, unique_by=lambda r: r.job_id)
)
def test_comparison_highlights_best_performers(runs):
    """
    **Feature: simplified-llm-optimization, Property 23: Comparison highlights best performers**
    **Validates: Requirements 11.3**
    
    For any set of training runs being compared, the system should identify and
    highlight the best-performing run for each metric.
    """
    # Ensure runs have different values to avoid ties
    assume(len(set(run.final_loss for run in runs)) == len(runs))
    assume(len(set(run.training_time_seconds for run in runs)) == len(runs))
    
    # Create comparison service
    service = ComparisonService()
    
    # Add runs to service
    for run in runs:
        service.add_run(run)
    
    # Get job IDs
    job_ids = [run.job_id for run in runs]
    
    # Perform comparison
    result = service.compare_runs(job_ids, include_charts=False, include_config_diff=False)
    
    # Verify best performers were identified
    assert result.best_performers is not None, "Best performers should be identified"
    assert len(result.best_performers) > 0, "At least one best performer should be identified"
    
    # Verify each best performer has the correct structure
    for performer in result.best_performers:
        assert isinstance(performer, BestPerformer), \
            f"Best performer should be BestPerformer instance, got {type(performer)}"
        assert performer.metric_name is not None, "Metric name must be specified"
        assert performer.job_id is not None, "Job ID must be specified"
        assert performer.job_id in job_ids, f"Job ID {performer.job_id} not in comparison set"
        assert performer.value is not None, "Value must be specified"
        assert isinstance(performer.is_lower_better, bool), "is_lower_better must be boolean"
    
    # Verify best performers are actually the best for their metrics
    metric_names = [p.metric_name for p in result.best_performers]
    
    # Check final_loss best performer
    if 'final_loss' in metric_names:
        loss_performer = next(p for p in result.best_performers if p.metric_name == 'final_loss')
        assert loss_performer.is_lower_better is True, "Loss should be lower-is-better metric"
        
        # Verify this is actually the run with lowest loss
        best_loss_run = min(runs, key=lambda r: r.final_loss)
        assert loss_performer.job_id == best_loss_run.job_id, \
            f"Best loss performer should be {best_loss_run.job_id}, got {loss_performer.job_id}"
        assert abs(loss_performer.value - best_loss_run.final_loss) < 1e-6, \
            f"Best loss value should be {best_loss_run.final_loss}, got {loss_performer.value}"
    
    # Check training_time best performer
    if 'training_time' in metric_names:
        time_performer = next(p for p in result.best_performers if p.metric_name == 'training_time')
        assert time_performer.is_lower_better is True, "Training time should be lower-is-better metric"
        
        # Verify this is actually the run with shortest time
        best_time_run = min(runs, key=lambda r: r.training_time_seconds)
        assert time_performer.job_id == best_time_run.job_id, \
            f"Best time performer should be {best_time_run.job_id}, got {time_performer.job_id}"
        assert abs(time_performer.value - best_time_run.training_time_seconds) < 1e-6, \
            f"Best time value should be {best_time_run.training_time_seconds}, got {time_performer.value}"


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    runs=st.lists(training_run_strategy(), min_size=2, max_size=5, unique_by=lambda r: r.job_id)
)
def test_best_performer_quality_score_when_available(runs):
    """
    For any set of runs with quality scores, the best performer for quality
    should be the one with the highest score (higher is better).
    """
    # Filter to only runs with quality scores
    runs_with_quality = [r for r in runs if r.quality_score is not None]
    
    # Skip if no runs have quality scores
    assume(len(runs_with_quality) >= 2)
    assume(len(set(r.quality_score for r in runs_with_quality)) == len(runs_with_quality))
    
    service = ComparisonService()
    
    for run in runs_with_quality:
        service.add_run(run)
    
    job_ids = [run.job_id for run in runs_with_quality]
    result = service.compare_runs(job_ids, include_charts=False, include_config_diff=False)
    
    # Find quality score best performer
    quality_performers = [p for p in result.best_performers if p.metric_name == 'quality_score']
    
    if quality_performers:
        quality_performer = quality_performers[0]
        
        # Verify it's marked as higher-is-better
        assert quality_performer.is_lower_better is False, \
            "Quality score should be higher-is-better metric"
        
        # Verify this is actually the run with highest quality score
        best_quality_run = max(runs_with_quality, key=lambda r: r.quality_score)
        assert quality_performer.job_id == best_quality_run.job_id, \
            f"Best quality performer should be {best_quality_run.job_id}, got {quality_performer.job_id}"
        assert abs(quality_performer.value - best_quality_run.quality_score) < 1e-6, \
            f"Best quality value should be {best_quality_run.quality_score}, got {quality_performer.value}"


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    runs=st.lists(training_run_strategy(), min_size=2, max_size=5, unique_by=lambda r: r.job_id)
)
def test_best_performer_validation_loss_when_available(runs):
    """
    For any set of runs with validation loss, the best performer for validation
    should be the one with the lowest validation loss.
    """
    # Filter to only runs with validation loss
    runs_with_val = [r for r in runs if r.best_val_loss is not None]
    
    # Skip if no runs have validation loss
    assume(len(runs_with_val) >= 2)
    assume(len(set(r.best_val_loss for r in runs_with_val)) == len(runs_with_val))
    
    service = ComparisonService()
    
    for run in runs_with_val:
        service.add_run(run)
    
    job_ids = [run.job_id for run in runs_with_val]
    result = service.compare_runs(job_ids, include_charts=False, include_config_diff=False)
    
    # Find validation loss best performer
    val_performers = [p for p in result.best_performers if p.metric_name == 'best_val_loss']
    
    if val_performers:
        val_performer = val_performers[0]
        
        # Verify it's marked as lower-is-better
        assert val_performer.is_lower_better is True, \
            "Validation loss should be lower-is-better metric"
        
        # Verify this is actually the run with lowest validation loss
        best_val_run = min(runs_with_val, key=lambda r: r.best_val_loss)
        assert val_performer.job_id == best_val_run.job_id, \
            f"Best val loss performer should be {best_val_run.job_id}, got {val_performer.job_id}"
        assert abs(val_performer.value - best_val_run.best_val_loss) < 1e-6, \
            f"Best val loss value should be {best_val_run.best_val_loss}, got {val_performer.value}"


@settings(max_examples=100)
@given(
    num_runs=st.integers(min_value=2, max_value=5)
)
def test_best_performer_identifies_all_key_metrics(num_runs):
    """
    For any valid number of runs, the comparison should identify best performers
    for all key metrics (loss, time, and optionally quality/validation).
    """
    service = ComparisonService()
    
    # Generate runs with distinct values
    runs = []
    for i in range(num_runs):
        run = TrainingRunSummary(
            job_id=f"job_{i}",
            model_name="test-model",
            dataset_name="test-dataset",
            final_loss=1.0 + (i * 0.1),  # Increasing loss
            best_val_loss=0.8 + (i * 0.1),  # Increasing val loss
            total_steps=1000,
            epochs_completed=3,
            training_time_seconds=3600.0 + (i * 100),  # Increasing time
            quality_score=80.0 - (i * 5),  # Decreasing quality
            config={'learning_rate': 2e-4}
        )
        runs.append(run)
        service.add_run(run)
    
    job_ids = [run.job_id for run in runs]
    result = service.compare_runs(job_ids, include_charts=False, include_config_diff=False)
    
    # Get metric names
    metric_names = [p.metric_name for p in result.best_performers]
    
    # Verify essential metrics are present
    assert 'final_loss' in metric_names, "Best performer for final_loss should be identified"
    assert 'training_time' in metric_names, "Best performer for training_time should be identified"
    
    # Since all runs have val_loss and quality_score, they should be present
    assert 'best_val_loss' in metric_names, "Best performer for best_val_loss should be identified"
    assert 'quality_score' in metric_names, "Best performer for quality_score should be identified"
    
    # Verify the correct runs are identified as best
    loss_performer = next(p for p in result.best_performers if p.metric_name == 'final_loss')
    assert loss_performer.job_id == "job_0", "First run should have best (lowest) loss"
    
    time_performer = next(p for p in result.best_performers if p.metric_name == 'training_time')
    assert time_performer.job_id == "job_0", "First run should have best (shortest) time"
    
    quality_performer = next(p for p in result.best_performers if p.metric_name == 'quality_score')
    assert quality_performer.job_id == "job_0", "First run should have best (highest) quality"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
