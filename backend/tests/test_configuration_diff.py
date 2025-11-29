"""
Property-based tests for configuration diff calculation in training run comparisons.

**Feature: simplified-llm-optimization, Property 24: Configuration diff calculation**
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime

from services.comparison_service import (
    ComparisonService,
    TrainingRunSummary,
    ConfigDiff
)


# Strategy for generating configuration dictionaries
def config_strategy():
    """Generate a valid training configuration"""
    return st.fixed_dictionaries({
        'learning_rate': st.floats(min_value=1e-6, max_value=1e-3),
        'batch_size': st.integers(min_value=1, max_value=32),
        'lora_r': st.integers(min_value=4, max_value=64),
        'lora_alpha': st.integers(min_value=8, max_value=128),
        'lora_dropout': st.floats(min_value=0.0, max_value=0.5),
        'epochs': st.integers(min_value=1, max_value=10),
        'warmup_steps': st.integers(min_value=0, max_value=1000),
        'max_grad_norm': st.floats(min_value=0.1, max_value=10.0),
        'weight_decay': st.floats(min_value=0.0, max_value=0.1),
        'optimizer': st.sampled_from(['adamw', 'sgd', 'adam']),
        'scheduler': st.sampled_from(['linear', 'cosine', 'constant']),
        'precision': st.sampled_from(['fp16', 'bf16', 'fp32'])
    })


# Strategy for generating training runs with configs
def training_run_with_config_strategy(job_id: str, config: dict):
    """Generate a training run with specific config"""
    return TrainingRunSummary(
        job_id=job_id,
        model_name="test-model",
        dataset_name="test-dataset",
        final_loss=1.0,
        total_steps=1000,
        epochs_completed=3,
        training_time_seconds=3600.0,
        config=config,
        started_at=datetime(2024, 1, 1),
        completed_at=datetime(2024, 1, 2)
    )


@settings(max_examples=100)
@given(
    config1=config_strategy(),
    config2=config_strategy()
)
def test_configuration_diff_calculation(config1, config2):
    """
    **Feature: simplified-llm-optimization, Property 24: Configuration diff calculation**
    **Validates: Requirements 11.4**
    
    For any pair of training configurations, the diff function should identify
    and return all parameter differences.
    """
    # Create comparison service
    service = ComparisonService()
    
    # Create two runs with different configs
    run1 = training_run_with_config_strategy("job_1", config1)
    run2 = training_run_with_config_strategy("job_2", config2)
    
    service.add_run(run1)
    service.add_run(run2)
    
    # Perform comparison with config diff
    result = service.compare_runs(
        ["job_1", "job_2"],
        include_charts=False,
        include_config_diff=True
    )
    
    # Verify config diffs were calculated
    assert result.config_diffs is not None, "Config diffs should be calculated"
    assert len(result.config_diffs) > 0, "At least one config diff should be present"
    
    # Verify each diff has the correct structure
    for diff in result.config_diffs:
        assert isinstance(diff, ConfigDiff), \
            f"Diff should be ConfigDiff instance, got {type(diff)}"
        assert diff.parameter is not None, "Parameter name must be specified"
        assert diff.run1_value is not None or diff.run2_value is not None, \
            "At least one value must be present"
        assert isinstance(diff.is_different, bool), "is_different must be boolean"
    
    # Verify all parameters from both configs are in the diff
    all_params = set(config1.keys()) | set(config2.keys())
    diff_params = {diff.parameter for diff in result.config_diffs}
    
    assert diff_params == all_params, \
        f"Diff should include all parameters. Expected {all_params}, got {diff_params}"
    
    # Verify is_different flag is correct for each parameter
    for diff in result.config_diffs:
        param = diff.parameter
        value1 = config1.get(param)
        value2 = config2.get(param)
        
        expected_different = value1 != value2
        assert diff.is_different == expected_different, \
            f"Parameter {param}: is_different should be {expected_different}, got {diff.is_different}"
        
        # Verify values match the configs
        assert diff.run1_value == value1, \
            f"Parameter {param}: run1_value should be {value1}, got {diff.run1_value}"
        assert diff.run2_value == value2, \
            f"Parameter {param}: run2_value should be {value2}, got {diff.run2_value}"


@settings(max_examples=100)
@given(
    config=config_strategy()
)
def test_identical_configs_have_no_differences(config):
    """
    For any configuration, comparing it with itself should show no differences
    (all is_different flags should be False).
    """
    service = ComparisonService()
    
    # Create two runs with identical configs
    run1 = training_run_with_config_strategy("job_1", config)
    run2 = training_run_with_config_strategy("job_2", config.copy())
    
    service.add_run(run1)
    service.add_run(run2)
    
    result = service.compare_runs(
        ["job_1", "job_2"],
        include_charts=False,
        include_config_diff=True
    )
    
    # Verify all diffs show no difference
    assert result.config_diffs is not None
    
    for diff in result.config_diffs:
        assert diff.is_different is False, \
            f"Parameter {diff.parameter} should not be different for identical configs"
        assert diff.run1_value == diff.run2_value, \
            f"Parameter {diff.parameter}: values should be equal"


@settings(max_examples=100)
@given(
    base_config=config_strategy(),
    param_to_change=st.sampled_from([
        'learning_rate', 'batch_size', 'lora_r', 'lora_alpha',
        'optimizer', 'scheduler', 'precision'
    ])
)
def test_single_parameter_difference_detected(base_config, param_to_change):
    """
    For any configuration with a single parameter changed, the diff should
    correctly identify exactly that parameter as different.
    """
    service = ComparisonService()
    
    # Create modified config with one parameter changed
    modified_config = base_config.copy()
    
    # Change the parameter to a different value
    if param_to_change == 'learning_rate':
        modified_config[param_to_change] = base_config[param_to_change] * 2
    elif param_to_change in ['batch_size', 'lora_r', 'lora_alpha']:
        modified_config[param_to_change] = base_config[param_to_change] + 1
    elif param_to_change in ['optimizer', 'scheduler', 'precision']:
        # Change to a different value from the same set
        current_value = base_config[param_to_change]
        if param_to_change == 'optimizer':
            options = ['adamw', 'sgd', 'adam']
        elif param_to_change == 'scheduler':
            options = ['linear', 'cosine', 'constant']
        else:  # precision
            options = ['fp16', 'bf16', 'fp32']
        
        # Pick a different value
        modified_config[param_to_change] = next(v for v in options if v != current_value)
    
    run1 = training_run_with_config_strategy("job_1", base_config)
    run2 = training_run_with_config_strategy("job_2", modified_config)
    
    service.add_run(run1)
    service.add_run(run2)
    
    result = service.compare_runs(
        ["job_1", "job_2"],
        include_charts=False,
        include_config_diff=True
    )
    
    # Find the diff for the changed parameter
    changed_diff = next(d for d in result.config_diffs if d.parameter == param_to_change)
    
    # Verify it's marked as different
    assert changed_diff.is_different is True, \
        f"Parameter {param_to_change} should be marked as different"
    
    # Verify the values are actually different
    assert changed_diff.run1_value != changed_diff.run2_value, \
        f"Parameter {param_to_change} values should be different"
    
    # Verify all other parameters are not marked as different
    other_diffs = [d for d in result.config_diffs if d.parameter != param_to_change]
    for diff in other_diffs:
        assert diff.is_different is False, \
            f"Parameter {diff.parameter} should not be marked as different"


@settings(max_examples=100)
@given(
    config1=config_strategy(),
    config2=config_strategy()
)
def test_config_diff_only_for_two_runs(config1, config2):
    """
    Configuration diff should only be calculated when comparing exactly 2 runs.
    For more than 2 runs, config_diffs should be None.
    """
    service = ComparisonService()
    
    # Create 3 runs
    run1 = training_run_with_config_strategy("job_1", config1)
    run2 = training_run_with_config_strategy("job_2", config2)
    run3 = training_run_with_config_strategy("job_3", config1.copy())
    
    service.add_run(run1)
    service.add_run(run2)
    service.add_run(run3)
    
    # Compare 2 runs - should have config diff
    result_2 = service.compare_runs(
        ["job_1", "job_2"],
        include_charts=False,
        include_config_diff=True
    )
    assert result_2.config_diffs is not None, \
        "Config diff should be calculated for 2 runs"
    
    # Compare 3 runs - should not have config diff
    result_3 = service.compare_runs(
        ["job_1", "job_2", "job_3"],
        include_charts=False,
        include_config_diff=True
    )
    assert result_3.config_diffs is None, \
        "Config diff should not be calculated for more than 2 runs"


@settings(max_examples=100)
@given(
    config1=config_strategy()
)
def test_config_diff_handles_missing_parameters(config1):
    """
    Configuration diff should handle cases where one config has parameters
    that the other doesn't have.
    """
    service = ComparisonService()
    
    # Create a config with an extra parameter
    config2 = config1.copy()
    config2['extra_param'] = 'extra_value'
    
    # Also remove a parameter from config2
    if 'warmup_steps' in config2:
        del config2['warmup_steps']
    
    run1 = training_run_with_config_strategy("job_1", config1)
    run2 = training_run_with_config_strategy("job_2", config2)
    
    service.add_run(run1)
    service.add_run(run2)
    
    result = service.compare_runs(
        ["job_1", "job_2"],
        include_charts=False,
        include_config_diff=True
    )
    
    # Verify extra_param is in the diff
    extra_param_diff = next((d for d in result.config_diffs if d.parameter == 'extra_param'), None)
    assert extra_param_diff is not None, "Extra parameter should be in diff"
    assert extra_param_diff.run1_value is None, "Run1 should not have extra_param"
    assert extra_param_diff.run2_value == 'extra_value', "Run2 should have extra_param"
    assert extra_param_diff.is_different is True, "Extra parameter should be marked as different"
    
    # Verify warmup_steps is in the diff (if it was in config1)
    if 'warmup_steps' in config1:
        warmup_diff = next((d for d in result.config_diffs if d.parameter == 'warmup_steps'), None)
        assert warmup_diff is not None, "Missing parameter should be in diff"
        assert warmup_diff.run1_value is not None, "Run1 should have warmup_steps"
        assert warmup_diff.run2_value is None, "Run2 should not have warmup_steps"
        assert warmup_diff.is_different is True, "Missing parameter should be marked as different"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
