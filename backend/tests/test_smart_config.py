"""
Property-based tests for smart configuration engine.

**Feature: simplified-llm-optimization, Property 3: Smart defaults calculation**
**Feature: simplified-llm-optimization, Property 5: Quantization auto-enable on insufficient memory**
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pytest
from hypothesis import given, strategies as st, settings, assume

# Import directly from smart_config_service to avoid torch dependency from __init__.py
import importlib.util
spec = importlib.util.spec_from_file_location(
    "smart_config_service",
    backend_dir / "services" / "smart_config_service.py"
)
smart_config_service = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smart_config_service)

SmartConfigEngine = smart_config_service.SmartConfigEngine
HardwareSpecs = smart_config_service.HardwareSpecs
ModelSpecs = smart_config_service.ModelSpecs
DatasetSpecs = smart_config_service.DatasetSpecs
PrecisionType = smart_config_service.PrecisionType
QuantizationType = smart_config_service.QuantizationType


# Strategies for generating test data
hardware_specs_strategy = st.builds(
    HardwareSpecs,
    gpu_memory_mb=st.integers(min_value=4000, max_value=80000),
    cpu_cores=st.integers(min_value=4, max_value=128),
    ram_gb=st.integers(min_value=16, max_value=512),
    compute_capability=st.sampled_from([None, "7.0", "7.5", "8.0", "8.6", "9.0"])
)

model_specs_strategy = st.builds(
    ModelSpecs,
    model_size_mb=st.integers(min_value=1000, max_value=70000),
    num_parameters=st.one_of(st.none(), st.integers(min_value=1000, max_value=70000)),
    max_seq_length=st.sampled_from([512, 1024, 2048, 4096]),
    architecture=st.one_of(st.none(), st.sampled_from(["llama", "mistral", "gpt"]))
)

dataset_specs_strategy = st.builds(
    DatasetSpecs,
    num_samples=st.integers(min_value=100, max_value=1000000),
    avg_sequence_length=st.one_of(st.none(), st.integers(min_value=50, max_value=4096)),
    max_sequence_length=st.one_of(st.none(), st.integers(min_value=100, max_value=8192))
)


@settings(max_examples=100)
@given(
    hardware=hardware_specs_strategy,
    model=model_specs_strategy,
    dataset=dataset_specs_strategy
)
def test_smart_defaults_calculation(hardware, model, dataset):
    """
    **Feature: simplified-llm-optimization, Property 3: Smart defaults calculation**
    **Validates: Requirements 1.5, 2.2, 2.5**
    
    For any combination of hardware specifications and dataset characteristics,
    when advanced settings are not specified, the system should calculate valid
    default values for all hyperparameters.
    """
    engine = SmartConfigEngine()
    
    # Calculate smart defaults
    config = engine.calculate_smart_defaults(
        hardware=hardware,
        model=model,
        dataset=dataset
    )
    
    # Verify all required fields are present and valid
    assert config is not None, "Config should not be None"
    
    # Batch configuration
    assert config.batch_size > 0, f"Batch size must be positive, got {config.batch_size}"
    assert config.batch_size <= 128, f"Batch size should be reasonable, got {config.batch_size}"
    assert config.gradient_accumulation_steps > 0, \
        f"Gradient accumulation must be positive, got {config.gradient_accumulation_steps}"
    assert config.effective_batch_size > 0, \
        f"Effective batch size must be positive, got {config.effective_batch_size}"
    assert config.effective_batch_size == config.batch_size * config.gradient_accumulation_steps, \
        f"Effective batch size should equal batch_size * grad_accum"
    
    # Precision and quantization
    assert config.precision in PrecisionType, \
        f"Invalid precision type: {config.precision}"
    assert config.quantization in QuantizationType, \
        f"Invalid quantization type: {config.quantization}"
    
    # Learning rate
    assert config.learning_rate > 0, \
        f"Learning rate must be positive, got {config.learning_rate}"
    assert 1e-6 <= config.learning_rate <= 1e-3, \
        f"Learning rate should be in reasonable range, got {config.learning_rate}"
    
    # Training duration
    assert config.num_epochs > 0, \
        f"Number of epochs must be positive, got {config.num_epochs}"
    assert config.num_epochs <= 100, \
        f"Number of epochs should be reasonable, got {config.num_epochs}"
    
    # Memory estimates
    assert config.estimated_memory_mb > 0, \
        f"Estimated memory must be positive, got {config.estimated_memory_mb}"
    assert 0 <= config.memory_utilization_percent <= 100, \
        f"Memory utilization should be in [0, 100], got {config.memory_utilization_percent}"
    
    # Time estimates (optional but should be valid if present)
    if config.estimated_training_time_hours is not None:
        assert config.estimated_training_time_hours > 0, \
            f"Training time estimate must be positive, got {config.estimated_training_time_hours}"
    
    # Explanations
    assert config.explanations is not None, "Explanations should be provided"
    assert isinstance(config.explanations, dict), "Explanations should be a dictionary"
    
    # Check that key explanations are present
    expected_keys = ["precision", "batch_size", "learning_rate", "memory", "epochs"]
    for key in expected_keys:
        assert key in config.explanations, f"Missing explanation for {key}"
        assert len(config.explanations[key]) > 0, f"Explanation for {key} should not be empty"


@settings(max_examples=100)
@given(
    gpu_memory_mb=st.integers(min_value=4000, max_value=80000),
    model_size_mb=st.integers(min_value=1000, max_value=70000),
    precision=st.sampled_from([PrecisionType.FP32, PrecisionType.FP16, PrecisionType.BF16])
)
def test_quantization_auto_enable_on_insufficient_memory(gpu_memory_mb, model_size_mb, precision):
    """
    **Feature: simplified-llm-optimization, Property 5: Quantization auto-enable on insufficient memory**
    **Validates: Requirements 2.3**
    
    For any model and GPU memory combination where model size exceeds available memory,
    the system should automatically enable quantization.
    """
    engine = SmartConfigEngine()
    
    quantization = engine.should_enable_quantization(
        gpu_memory_mb=gpu_memory_mb,
        model_size_mb=model_size_mb,
        precision=precision
    )
    
    # Verify quantization type is valid
    assert quantization in QuantizationType, f"Invalid quantization type: {quantization}"
    
    # Calculate if model fits in memory
    overhead_multiplier = engine.MEMORY_OVERHEAD_MULTIPLIER[precision]
    estimated_memory_needed = model_size_mb * overhead_multiplier
    usable_memory = gpu_memory_mb * engine.MEMORY_SAFETY_MARGIN
    
    # Verify quantization logic
    if estimated_memory_needed < usable_memory * 0.7:
        # Model fits comfortably - no quantization needed
        assert quantization == QuantizationType.NONE, \
            f"Should not quantize when model fits comfortably " \
            f"(needed: {estimated_memory_needed}MB, available: {usable_memory}MB)"
    
    elif estimated_memory_needed < usable_memory:
        # Model barely fits - should use 8-bit
        assert quantization == QuantizationType.INT8, \
            f"Should use 8-bit quantization when memory is tight " \
            f"(needed: {estimated_memory_needed}MB, available: {usable_memory}MB)"
    
    else:
        # Model doesn't fit - should use 4-bit
        assert quantization == QuantizationType.INT4, \
            f"Should use 4-bit quantization when model doesn't fit " \
            f"(needed: {estimated_memory_needed}MB, available: {usable_memory}MB)"


@settings(max_examples=100)
@given(
    gpu_memory_mb=st.integers(min_value=8000, max_value=80000),
    model_size_mb=st.integers(min_value=1000, max_value=30000),
    seq_length=st.sampled_from([512, 1024, 2048, 4096]),
    precision=st.sampled_from([PrecisionType.FP16, PrecisionType.BF16, PrecisionType.FP32])
)
def test_batch_size_calculation_validity(gpu_memory_mb, model_size_mb, seq_length, precision):
    """
    For any valid hardware and model configuration, batch size calculation
    should return a positive integer that fits in memory.
    """
    engine = SmartConfigEngine()
    
    batch_size = engine.calculate_batch_size(
        gpu_memory_mb=gpu_memory_mb,
        model_size_mb=model_size_mb,
        seq_length=seq_length,
        precision=precision
    )
    
    # Verify batch size is valid
    assert batch_size > 0, f"Batch size must be positive, got {batch_size}"
    assert batch_size <= 128, f"Batch size should be capped at 128, got {batch_size}"
    assert isinstance(batch_size, int), f"Batch size must be integer, got {type(batch_size)}"
    
    # Verify batch size is a power of 2 (for efficiency)
    import math
    if batch_size > 1:
        log2 = math.log2(batch_size)
        assert log2 == int(log2), f"Batch size should be power of 2, got {batch_size}"


@settings(max_examples=100)
@given(
    target_batch_size=st.integers(min_value=8, max_value=256),
    max_batch_size=st.integers(min_value=1, max_value=128)
)
def test_gradient_accumulation_calculation(target_batch_size, max_batch_size):
    """
    For any target and max batch size, gradient accumulation should be calculated
    to reach the target effective batch size.
    """
    engine = SmartConfigEngine()
    
    grad_accum = engine.calculate_gradient_accumulation(
        target_batch_size=target_batch_size,
        max_batch_size=max_batch_size
    )
    
    # Verify gradient accumulation is valid
    assert grad_accum > 0, f"Gradient accumulation must be positive, got {grad_accum}"
    assert isinstance(grad_accum, int), f"Gradient accumulation must be integer, got {type(grad_accum)}"
    
    # Verify it achieves at least the target batch size
    effective_batch_size = max_batch_size * grad_accum
    assert effective_batch_size >= target_batch_size, \
        f"Effective batch size ({effective_batch_size}) should be >= target ({target_batch_size})"
    
    # If max_batch_size >= target, grad_accum should be 1
    if max_batch_size >= target_batch_size:
        assert grad_accum == 1, \
            f"Gradient accumulation should be 1 when max_batch_size >= target, got {grad_accum}"


@settings(max_examples=100)
@given(
    compute_capability=st.sampled_from([None, "6.0", "7.0", "7.5", "8.0", "8.6", "9.0"])
)
def test_precision_recommendation_validity(compute_capability):
    """
    For any compute capability, precision recommendation should return a valid precision type.
    """
    engine = SmartConfigEngine()
    
    precision = engine.recommend_precision(compute_capability=compute_capability)
    
    # Verify precision is valid
    assert precision in PrecisionType, f"Invalid precision type: {precision}"
    
    # Verify logic based on compute capability
    if compute_capability is not None:
        try:
            major, minor = map(int, compute_capability.split('.'))
            cc_value = major * 10 + minor
            
            if cc_value >= 80:
                # Ampere and newer should recommend BF16
                assert precision == PrecisionType.BF16, \
                    f"Compute capability {compute_capability} should recommend BF16, got {precision.value}"
            elif cc_value >= 70:
                # Volta and Turing should recommend FP16
                assert precision == PrecisionType.FP16, \
                    f"Compute capability {compute_capability} should recommend FP16, got {precision.value}"
            else:
                # Older GPUs should use FP32
                assert precision == PrecisionType.FP32, \
                    f"Compute capability {compute_capability} should recommend FP32, got {precision.value}"
        except (ValueError, AttributeError):
            # Invalid compute capability should default to FP16
            assert precision == PrecisionType.FP16, \
                f"Invalid compute capability should default to FP16, got {precision.value}"
    else:
        # No compute capability should default to FP16
        assert precision == PrecisionType.FP16, \
            f"No compute capability should default to FP16, got {precision.value}"


@settings(max_examples=100)
@given(
    effective_batch_size=st.integers(min_value=1, max_value=256)
)
def test_learning_rate_calculation_validity(effective_batch_size):
    """
    For any effective batch size, learning rate calculation should return
    a valid learning rate in a reasonable range.
    """
    engine = SmartConfigEngine()
    
    learning_rate = engine.calculate_learning_rate(effective_batch_size)
    
    # Verify learning rate is valid
    assert learning_rate > 0, f"Learning rate must be positive, got {learning_rate}"
    assert 1e-6 <= learning_rate <= 1e-3, \
        f"Learning rate should be in [1e-6, 1e-3], got {learning_rate}"
    assert isinstance(learning_rate, float), \
        f"Learning rate must be float, got {type(learning_rate)}"


@settings(max_examples=100)
@given(
    num_samples=st.integers(min_value=100, max_value=100000),
    batch_size=st.integers(min_value=1, max_value=64),
    gradient_accumulation=st.integers(min_value=1, max_value=16),
    num_epochs=st.integers(min_value=1, max_value=10)
)
def test_training_time_estimation_validity(num_samples, batch_size, gradient_accumulation, num_epochs):
    """
    For any training configuration, time estimation should return valid
    min, expected, and max hours.
    """
    engine = SmartConfigEngine()
    
    min_hours, expected_hours, max_hours = engine.estimate_training_time(
        num_samples=num_samples,
        batch_size=batch_size,
        gradient_accumulation=gradient_accumulation,
        num_epochs=num_epochs
    )
    
    # Verify all estimates are positive
    assert min_hours > 0, f"Min hours must be positive, got {min_hours}"
    assert expected_hours > 0, f"Expected hours must be positive, got {expected_hours}"
    assert max_hours > 0, f"Max hours must be positive, got {max_hours}"
    
    # Verify ordering
    assert min_hours <= expected_hours, \
        f"Min hours ({min_hours}) should be <= expected hours ({expected_hours})"
    assert expected_hours <= max_hours, \
        f"Expected hours ({expected_hours}) should be <= max hours ({max_hours})"
    
    # Verify reasonable confidence interval (max should not be more than 3x min)
    assert max_hours <= min_hours * 3, \
        f"Confidence interval too wide: min={min_hours}, max={max_hours}"


@settings(max_examples=50)
@given(
    hardware=hardware_specs_strategy,
    model=model_specs_strategy,
    dataset=dataset_specs_strategy
)
def test_smart_config_memory_safety(hardware, model, dataset):
    """
    For any configuration, the estimated memory usage should not exceed
    available GPU memory (with safety margin).
    """
    engine = SmartConfigEngine()
    
    config = engine.calculate_smart_defaults(
        hardware=hardware,
        model=model,
        dataset=dataset
    )
    
    # Verify memory safety
    assert config.estimated_memory_mb <= hardware.gpu_memory_mb, \
        f"Estimated memory ({config.estimated_memory_mb}MB) exceeds available " \
        f"GPU memory ({hardware.gpu_memory_mb}MB)"
    
    # Verify memory utilization is within safety margin
    assert config.memory_utilization_percent <= 100, \
        f"Memory utilization ({config.memory_utilization_percent}%) exceeds 100%"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
