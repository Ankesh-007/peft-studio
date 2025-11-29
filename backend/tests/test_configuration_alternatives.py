"""
Property-based tests for configuration alternatives suggestion.

Tests Property 18: Configuration alternatives suggestion
Validates: Requirements 9.5
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pytest
from hypothesis import given, strategies as st, settings

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
SmartConfig = smart_config_service.SmartConfig
PrecisionType = smart_config_service.PrecisionType
QuantizationType = smart_config_service.QuantizationType
ConfigurationAlternative = smart_config_service.ConfigurationAlternative


# **Feature: simplified-llm-optimization, Property 18: Configuration alternatives suggestion**
@given(
    gpu_memory=st.integers(min_value=4000, max_value=80000),
    cpu_cores=st.integers(min_value=4, max_value=128),
    ram_gb=st.integers(min_value=16, max_value=512),
    model_size=st.integers(min_value=1000, max_value=70000),
    num_samples=st.integers(min_value=100, max_value=100000),
)
@settings(max_examples=100)
def test_configuration_alternatives_suggestion(
    gpu_memory, cpu_cores, ram_gb, model_size, num_samples
):
    """
    For any training configuration, the system should suggest at least one 
    alternative configuration that is either faster or more resource-efficient.
    
    Validates: Requirements 9.5
    """
    engine = SmartConfigEngine()
    
    # Create hardware, model, and dataset specs
    hardware = HardwareSpecs(
        gpu_memory_mb=gpu_memory,
        cpu_cores=cpu_cores,
        ram_gb=ram_gb,
        compute_capability="8.0"
    )
    
    model = ModelSpecs(
        model_size_mb=model_size,
        num_parameters=model_size // 2,  # Rough estimate
        max_seq_length=2048
    )
    
    dataset = DatasetSpecs(
        num_samples=num_samples,
        avg_sequence_length=1024
    )
    
    # Calculate base configuration
    base_config = engine.calculate_smart_defaults(hardware, model, dataset)
    
    # Get alternative configurations
    alternatives = engine.suggest_configuration_alternatives(
        base_config=base_config,
        hardware=hardware,
        model=model,
        dataset=dataset
    )
    
    # Property: Should return at least one alternative
    assert len(alternatives) >= 1, (
        f"Expected at least 1 alternative configuration, got {len(alternatives)}"
    )
    
    # Property: Each alternative should have a description
    for alt in alternatives:
        assert hasattr(alt, 'config'), "Alternative missing 'config' attribute"
        assert hasattr(alt, 'description'), "Alternative missing 'description' attribute"
        assert hasattr(alt, 'trade_offs'), "Alternative missing 'trade_offs' attribute"
        assert isinstance(alt.description, str), "Description should be a string"
        assert len(alt.description) > 0, "Description should not be empty"
        assert isinstance(alt.trade_offs, str), "Trade-offs should be a string"
        assert len(alt.trade_offs) > 0, "Trade-offs should not be empty"
    
    # Property: Each alternative should differ from base config in at least one parameter
    for alt in alternatives:
        differs = (
            alt.config.batch_size != base_config.batch_size or
            alt.config.gradient_accumulation_steps != base_config.gradient_accumulation_steps or
            alt.config.learning_rate != base_config.learning_rate or
            alt.config.num_epochs != base_config.num_epochs or
            alt.config.precision != base_config.precision or
            alt.config.quantization != base_config.quantization
        )
        assert differs, (
            f"Alternative configuration should differ from base config in at least one parameter"
        )
    
    # Property: Alternatives should be either faster or more efficient
    for alt in alternatives:
        # Check if it's faster (less training time)
        is_faster = (
            alt.config.estimated_training_time_hours is not None and
            base_config.estimated_training_time_hours is not None and
            alt.config.estimated_training_time_hours < base_config.estimated_training_time_hours
        )
        
        # Check if it's more memory efficient
        is_more_efficient = (
            alt.config.estimated_memory_mb < base_config.estimated_memory_mb or
            alt.config.memory_utilization_percent < base_config.memory_utilization_percent
        )
        
        # At least one should be true
        assert is_faster or is_more_efficient, (
            f"Alternative should be either faster or more resource-efficient. "
            f"Base time: {base_config.estimated_training_time_hours}h, "
            f"Alt time: {alt.config.estimated_training_time_hours}h, "
            f"Base memory: {base_config.estimated_memory_mb}MB, "
            f"Alt memory: {alt.config.estimated_memory_mb}MB"
        )


@given(
    gpu_memory=st.integers(min_value=8000, max_value=24000),
    model_size=st.integers(min_value=5000, max_value=15000),
    num_samples=st.integers(min_value=1000, max_value=50000),
)
@settings(max_examples=100)
def test_alternatives_include_quantization_option(gpu_memory, model_size, num_samples):
    """
    When memory is tight, alternatives should include quantization options.
    """
    engine = SmartConfigEngine()
    
    hardware = HardwareSpecs(
        gpu_memory_mb=gpu_memory,
        cpu_cores=8,
        ram_gb=32,
        compute_capability="8.0"
    )
    
    model = ModelSpecs(
        model_size_mb=model_size,
        max_seq_length=2048
    )
    
    dataset = DatasetSpecs(
        num_samples=num_samples,
        avg_sequence_length=1024
    )
    
    base_config = engine.calculate_smart_defaults(hardware, model, dataset)
    alternatives = engine.suggest_configuration_alternatives(
        base_config=base_config,
        hardware=hardware,
        model=model,
        dataset=dataset
    )
    
    # If base config doesn't use quantization and memory is tight, 
    # at least one alternative should suggest quantization
    if base_config.quantization == QuantizationType.NONE:
        memory_usage_percent = (base_config.estimated_memory_mb / gpu_memory) * 100
        if memory_usage_percent > 60:  # Memory is somewhat tight
            has_quantization_alternative = any(
                alt.config.quantization != QuantizationType.NONE
                for alt in alternatives
            )
            # This is a soft check - not all cases will have quantization alternatives
            # but when memory is tight, it's likely
            if memory_usage_percent > 80:
                assert has_quantization_alternative, (
                    f"When memory usage is {memory_usage_percent:.1f}%, "
                    f"expected at least one quantization alternative"
                )


@given(
    num_epochs=st.integers(min_value=1, max_value=10),
    num_samples=st.integers(min_value=1000, max_value=50000),
)
@settings(max_examples=100)
def test_alternatives_include_epoch_variations(num_epochs, num_samples):
    """
    Alternatives should include variations in training duration (epochs).
    """
    engine = SmartConfigEngine()
    
    hardware = HardwareSpecs(
        gpu_memory_mb=16000,
        cpu_cores=8,
        ram_gb=32,
        compute_capability="8.0"
    )
    
    model = ModelSpecs(
        model_size_mb=7000,
        max_seq_length=2048
    )
    
    dataset = DatasetSpecs(
        num_samples=num_samples,
        avg_sequence_length=1024
    )
    
    # Use custom target batch size to control epochs
    base_config = engine.calculate_smart_defaults(hardware, model, dataset)
    # Override epochs for testing
    base_config.num_epochs = num_epochs
    
    alternatives = engine.suggest_configuration_alternatives(
        base_config=base_config,
        hardware=hardware,
        model=model,
        dataset=dataset
    )
    
    # At least one alternative should have different number of epochs
    has_epoch_variation = any(
        alt.config.num_epochs != base_config.num_epochs
        for alt in alternatives
    )
    
    # This should be true in most cases, especially when epochs > 1
    if num_epochs > 1:
        assert has_epoch_variation, (
            f"Expected at least one alternative with different epoch count "
            f"(base: {num_epochs} epochs)"
        )


def test_alternatives_have_valid_configurations():
    """
    All suggested alternatives should have valid, executable configurations.
    """
    engine = SmartConfigEngine()
    
    hardware = HardwareSpecs(
        gpu_memory_mb=24000,
        cpu_cores=16,
        ram_gb=64,
        compute_capability="8.0"
    )
    
    model = ModelSpecs(
        model_size_mb=13000,
        max_seq_length=2048
    )
    
    dataset = DatasetSpecs(
        num_samples=10000,
        avg_sequence_length=1024
    )
    
    base_config = engine.calculate_smart_defaults(hardware, model, dataset)
    alternatives = engine.suggest_configuration_alternatives(
        base_config=base_config,
        hardware=hardware,
        model=model,
        dataset=dataset
    )
    
    for alt in alternatives:
        config = alt.config
        
        # Validate all required fields are present and valid
        assert config.batch_size > 0, "Batch size must be positive"
        assert config.gradient_accumulation_steps > 0, "Gradient accumulation must be positive"
        assert config.effective_batch_size > 0, "Effective batch size must be positive"
        assert config.learning_rate > 0, "Learning rate must be positive"
        assert config.num_epochs > 0, "Number of epochs must be positive"
        assert config.estimated_memory_mb > 0, "Estimated memory must be positive"
        assert 0 <= config.memory_utilization_percent <= 100, (
            f"Memory utilization must be between 0-100%, got {config.memory_utilization_percent}"
        )
        
        # Validate precision and quantization are valid enum values
        assert isinstance(config.precision, PrecisionType), "Precision must be PrecisionType enum"
        assert isinstance(config.quantization, QuantizationType), (
            "Quantization must be QuantizationType enum"
        )
        
        # Validate effective batch size calculation
        assert config.effective_batch_size == (
            config.batch_size * config.gradient_accumulation_steps
        ), "Effective batch size calculation is incorrect"
