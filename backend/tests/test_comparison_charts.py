"""
Property-based tests for training run comparison chart generation.

**Feature: simplified-llm-optimization, Property 22: Training run comparison generates charts**
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime, timedelta

from services.comparison_service import (
    ComparisonService,
    TrainingRunSummary,
    ComparisonChart
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
def test_comparison_generates_charts_for_all_runs(runs):
    """
    **Feature: simplified-llm-optimization, Property 22: Training run comparison generates charts**
    **Validates: Requirements 11.2**
    
    For any selection of 2-5 completed training runs, the comparison function should
    generate side-by-side charts for all key metrics.
    """
    # Create comparison service
    service = ComparisonService()
    
    # Add runs to service
    for run in runs:
        service.add_run(run)
    
    # Get job IDs
    job_ids = [run.job_id for run in runs]
    
    # Perform comparison
    result = service.compare_runs(job_ids, include_charts=True, include_config_diff=False)
    
    # Verify charts were generated
    assert result.charts is not None, "Charts should be generated"
    assert len(result.charts) > 0, "At least one chart should be generated"
    
    # Verify each chart has the correct structure
    for chart in result.charts:
        assert isinstance(chart, ComparisonChart), f"Chart should be ComparisonChart instance, got {type(chart)}"
        assert chart.chart_type is not None, "Chart type must be specified"
        assert chart.title is not None and len(chart.title) > 0, "Chart must have a title"
        assert chart.x_label is not None, "Chart must have x-axis label"
        assert chart.y_label is not None, "Chart must have y-axis label"
        assert chart.series is not None, "Chart must have series data"
        assert len(chart.series) > 0, "Chart must have at least one series"
        
        # Verify each series has data for all runs
        assert len(chart.series) == len(runs), \
            f"Chart should have series for all {len(runs)} runs, got {len(chart.series)}"
        
        # Verify each series has required fields
        for series in chart.series:
            assert 'job_id' in series, "Series must have job_id"
            assert 'label' in series, "Series must have label"
            assert 'data' in series, "Series must have data"
            assert len(series['data']) > 0, "Series data must not be empty"
            
            # Verify data points have x and y coordinates
            for point in series['data']:
                assert 'x' in point, "Data point must have x coordinate"
                assert 'y' in point, "Data point must have y coordinate"


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    runs=st.lists(training_run_strategy(), min_size=2, max_size=5, unique_by=lambda r: r.job_id)
)
def test_comparison_charts_include_key_metrics(runs):
    """
    For any set of training runs, comparison charts should include
    key metrics like loss, training time, and quality score.
    """
    service = ComparisonService()
    
    for run in runs:
        service.add_run(run)
    
    job_ids = [run.job_id for run in runs]
    result = service.compare_runs(job_ids, include_charts=True, include_config_diff=False)
    
    # Get chart types
    chart_types = [chart.chart_type for chart in result.charts]
    
    # Verify essential charts are present
    assert 'loss_curve' in chart_types, "Loss curve chart should be generated"
    assert 'bar' in chart_types, "Bar charts should be generated for comparisons"
    
    # Verify loss curve chart has correct structure
    loss_chart = next(c for c in result.charts if c.chart_type == 'loss_curve')
    assert 'loss' in loss_chart.title.lower() or 'loss' in loss_chart.y_label.lower(), \
        "Loss chart should reference loss in title or y-label"


@settings(max_examples=100)
@given(
    num_runs=st.integers(min_value=2, max_value=5)
)
def test_comparison_charts_scale_with_run_count(num_runs):
    """
    For any valid number of runs (2-5), the comparison should generate
    charts with series for each run.
    """
    service = ComparisonService()
    
    # Generate runs
    runs = []
    for i in range(num_runs):
        run = TrainingRunSummary(
            job_id=f"job_{i}",
            model_name="test-model",
            dataset_name="test-dataset",
            final_loss=1.0 - (i * 0.1),
            total_steps=1000,
            epochs_completed=3,
            training_time_seconds=3600.0,
            config={'learning_rate': 2e-4}
        )
        runs.append(run)
        service.add_run(run)
    
    job_ids = [run.job_id for run in runs]
    result = service.compare_runs(job_ids, include_charts=True, include_config_diff=False)
    
    # Verify all charts have series for all runs
    for chart in result.charts:
        assert len(chart.series) == num_runs, \
            f"Chart should have {num_runs} series, got {len(chart.series)}"


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    runs=st.lists(training_run_strategy(), min_size=2, max_size=5, unique_by=lambda r: r.job_id)
)
def test_comparison_validates_run_count(runs):
    """
    The comparison function should validate that 2-5 runs are provided.
    """
    service = ComparisonService()
    
    for run in runs:
        service.add_run(run)
    
    job_ids = [run.job_id for run in runs]
    
    # Valid comparison should succeed
    result = service.compare_runs(job_ids, include_charts=True, include_config_diff=False)
    assert result is not None
    assert len(result.runs) == len(runs)
    
    # Test with too few runs (1)
    if len(job_ids) > 1:
        with pytest.raises(ValueError, match="at least 2"):
            service.compare_runs([job_ids[0]], include_charts=True, include_config_diff=False)
    
    # Test with too many runs (6+)
    extra_runs = [
        TrainingRunSummary(
            job_id=f"extra_{i}",
            model_name="test",
            dataset_name="test",
            final_loss=1.0,
            total_steps=1000,
            epochs_completed=1,
            training_time_seconds=3600.0,
            config={}
        )
        for i in range(6)
    ]
    
    for run in extra_runs:
        service.add_run(run)
    
    extra_job_ids = [run.job_id for run in extra_runs]
    
    with pytest.raises(ValueError, match="more than 5"):
        service.compare_runs(extra_job_ids, include_charts=True, include_config_diff=False)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
