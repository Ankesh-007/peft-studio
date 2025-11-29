"""
Property-based tests for profile estimates and smart defaults calculation.

**Feature: simplified-llm-optimization, Property 3: Smart defaults calculation**
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck

# Import services directly to avoid heavy dependencies
try:
    from services.profile_service import (
        ProfileService,
        UseCase,
        get_profile_service
    )
    from services.smart_config_service import (
        SmartConfigEngine,
        HardwareSpecs,
        ModelSpecs,
        DatasetSpecs,
        get_smart_config_engine
    )
except ImportError:
    # If imports fail, try importing directly
    import importlib.util
    
    # Import profile service
    spec = importlib.util.spec_from_file_location(
        "profile_service",
        backend_dir / "services" / "profile_service.py"
    )
    profile_service_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(profile_service_module)
    
    ProfileService = profile_service_module.ProfileService
    UseCase = profile_service_module.UseCase
    get_profile_service = profile_service_module.get_profile_service
    
    # Import smart config service
    spec = importlib.util.spec_from_file_location(
        "smart_config_service",
        backend_dir / "services" / "smart_config_service.py"
    )
    smart_config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(smart_config_module)
    
    SmartConfigEngine = smart_config_module.SmartConfigEngine
    HardwareSpecs = smart_config_module.HardwareSpecs
    ModelSpecs = smart_config_module.ModelSpecs
    DatasetSpecs = smart_config_module.DatasetSpecs
    get_smart_config_engine = smart_config_module.get_smart_config_engine


# Strategy for generating valid hardware specifications
hardware_specs_strategy = st.builds(
    HardwareSpecs,
    gpu_memory_mb=st.integers(min_value=4000, max_value=80000),
    cpu_cores=st.integers(min_value=4, max_value=128),
    ram_gb=st.integers(min_value=16, max_value=512),
    compute_capability=st.sampled_from([None, "7.0", "7.5", "8.0", "8.6", "8.9", "9.0"])
)

# Strategy for generating valid model specifications
model_specs_strategy = st.builds(
    ModelSpecs,
    model_size_mb=st.integers(min_value=1000, max_value=70000),
    num_parameters=st.one_of(st.none(), st.integers(min_value=1_000_000, max_value=70_000_000_000)),
    max_seq_length=st.integers(min_value=512, max_value=8192),
    architecture=st.one_of(st.none(), st.sampled_from(["llama", "mistral", "gpt", "phi"]))
)

# Strategy for generating valid dataset specifications
dataset_specs_strategy = st.builds(
    DatasetSpecs,
    num_samples=st.integers(min_value=100, max_value=1_000_000),
    avg_sequence_length=st.one_of(st.none(), st.integers(min_value=50, max_value=4096)),
    max_sequence_length=st.one_of(st.none(), st.integers(min_value=100, max_value=8192))
)

# Strategy for use cases
use_case_strategy = st.sampled_from([
    UseCase.CHATBOT,
    UseCase.CODE_GENERATION,
    UseCase.SUMMARIZATION,
    UseCase.QA,
    UseCase.CREATIVE_WRITING,
    UseCase.DOMAIN_ADAPTATION
])


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
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
    # Get the smart config engine
    config_engine = get_smart_config_engine()
    
    # Calculate smart defaults
    config = config_engine.calculate_smart_defaults(
        hardware=hardware,
        model=model,
        dataset=dataset,
        target_effective_batch_size=32
    )
    
    # Verify batch size is calculated and valid
    assert config.batch_size > 0, f"Batch size must be positive, got {config.batch_size}"
    assert config.batch_size <= 128, f"Batch size seems too large: {config.batch_size}"
    
    # Verify gradient accumulation is calculated and valid
    assert config.gradient_accumulation_steps > 0, \
        f"Gradient accumulation steps must be positive, got {config.gradient_accumulation_steps}"
    
    # Verify effective batch size is calculated
    assert config.effective_batch_size > 0, \
        f"Effective batch size must be positive, got {config.effective_batch_size}"
    assert config.effective_batch_size == config.batch_size * config.gradient_accumulation_steps, \
        f"Effective batch size calculation incorrect: {config.effective_batch_size} != {config.batch_size} * {config.gradient_accumulation_steps}"
    
    # Verify precision is set to a valid value
    assert config.precision.value in ["fp32", "fp16", "bf16"], \
        f"Invalid precision: {config.precision.value}"
    
    # Verify quantization is set to a valid value
    assert config.quantization.value in ["none", "8bit", "4bit"], \
        f"Invalid quantization: {config.quantization.value}"
    
    # Verify learning rate is calculated and valid
    assert config.learning_rate > 0, \
        f"Learning rate must be positive, got {config.learning_rate}"
    assert config.learning_rate <= 1.0, \
        f"Learning rate seems too high: {config.learning_rate}"
    
    # Verify epochs are calculated and valid
    assert config.num_epochs > 0, \
        f"Number of epochs must be positive, got {config.num_epochs}"
    assert config.num_epochs <= 100, \
        f"Number of epochs seems too high: {config.num_epochs}"
    
    # Verify max steps are calculated (optional field)
    if config.max_steps is not None:
        assert config.max_steps >= 0, \
            f"Max steps must be non-negative, got {config.max_steps}"
    
    # Verify memory estimates are calculated
    assert config.estimated_memory_mb > 0, \
        f"Estimated memory must be positive, got {config.estimated_memory_mb}"
    
    # Verify memory utilization is calculated and reasonable
    assert 0 <= config.memory_utilization_percent <= 100, \
        f"Memory utilization must be in [0, 100], got {config.memory_utilization_percent}"
    
    # Verify training time estimate is calculated (optional field)
    if config.estimated_training_time_hours is not None:
        assert config.estimated_training_time_hours >= 0, \
            f"Estimated training time must be non-negative, got {config.estimated_training_time_hours}"
    
    # Verify tokens per second is calculated (optional field)
    if config.tokens_per_second is not None:
        assert config.tokens_per_second >= 0, \
            f"Tokens per second must be non-negative, got {config.tokens_per_second}"
    
    # Verify explanations are provided
    assert config.explanations is not None, "Explanations must be provided"
    assert isinstance(config.explanations, dict), "Explanations must be a dictionary"


@settings(max_examples=100)
@given(
    use_case=use_case_strategy,
    hardware=hardware_specs_strategy,
    model=model_specs_strategy,
    dataset=dataset_specs_strategy
)
def test_profile_with_smart_defaults_integration(use_case, hardware, model, dataset):
    """
    **Feature: simplified-llm-optimization, Property 3: Smart defaults calculation**
    **Validates: Requirements 3.3**
    
    For any profile combined with hardware/dataset specs, the system should
    provide complete configuration with estimates.
    """
    # Get services
    profile_service = get_profile_service()
    config_engine = get_smart_config_engine()
    
    # Get profile for use case
    profile = profile_service.get_profile_by_use_case(use_case)
    assert profile is not None
    
    # Calculate smart defaults
    smart_config = config_engine.calculate_smart_defaults(
        hardware=hardware,
        model=model,
        dataset=dataset,
        target_effective_batch_size=32
    )
    
    # Verify profile config can be combined with smart defaults
    # Profile provides: LoRA params, learning rate, epochs
    # Smart config provides: batch size, precision, quantization
    
    # Profile parameters should be valid
    assert profile.config.lora_r > 0
    assert profile.config.lora_alpha > 0
    assert profile.config.learning_rate > 0
    assert profile.config.num_epochs > 0
    
    # Smart config parameters should be valid
    assert smart_config.batch_size > 0
    assert smart_config.precision.value in ["fp32", "fp16", "bf16"]
    assert smart_config.quantization.value in ["none", "8bit", "4bit"]
    
    # Combined configuration should have all required parameters
    combined_config = {
        # From profile
        "lora_r": profile.config.lora_r,
        "lora_alpha": profile.config.lora_alpha,
        "lora_dropout": profile.config.lora_dropout,
        "target_modules": profile.config.target_modules,
        "learning_rate": profile.config.learning_rate,
        "num_epochs": profile.config.num_epochs,
        "warmup_ratio": profile.config.warmup_ratio,
        "max_seq_length": profile.config.max_seq_length,
        # From smart config
        "batch_size": smart_config.batch_size,
        "gradient_accumulation_steps": smart_config.gradient_accumulation_steps,
        "precision": smart_config.precision.value,
        "quantization": smart_config.quantization.value,
    }
    
    # Verify all required parameters are present and valid
    for key, value in combined_config.items():
        assert value is not None, f"Parameter {key} is None"
        if isinstance(value, (int, float)):
            if key not in ["lora_dropout", "warmup_ratio"]:  # These can be 0
                assert value > 0, f"Parameter {key} must be positive, got {value}"


@settings(max_examples=100)
@given(
    hardware=hardware_specs_strategy,
    model=model_specs_strategy,
    dataset=dataset_specs_strategy
)
def test_quantization_enabled_when_memory_insufficient(hardware, model, dataset):
    """
    Verify that quantization is automatically enabled when GPU memory is insufficient.
    This is part of smart defaults calculation.
    """
    config_engine = get_smart_config_engine()
    
    # Calculate smart defaults
    config = config_engine.calculate_smart_defaults(
        hardware=hardware,
        model=model,
        dataset=dataset,
        target_effective_batch_size=32
    )
    
    # If memory utilization is very high, quantization should be enabled
    if config.memory_utilization_percent > 95:
        assert config.quantization.value in ["8bit", "4bit"], \
            f"Quantization should be enabled when memory utilization is {config.memory_utilization_percent}%"


@settings(max_examples=100)
@given(
    hardware=hardware_specs_strategy,
    model=model_specs_strategy,
    dataset=dataset_specs_strategy,
    target_batch_size=st.integers(min_value=8, max_value=128)
)
def test_effective_batch_size_respects_target(hardware, model, dataset, target_batch_size):
    """
    Verify that the effective batch size calculation respects the target batch size
    through gradient accumulation.
    """
    config_engine = get_smart_config_engine()
    
    # Calculate smart defaults with specific target
    config = config_engine.calculate_smart_defaults(
        hardware=hardware,
        model=model,
        dataset=dataset,
        target_effective_batch_size=target_batch_size
    )
    
    # The effective batch size should be close to the target
    # (may not be exact due to hardware constraints)
    assert config.effective_batch_size > 0
    
    # If we achieved the target, verify the calculation
    if config.effective_batch_size == target_batch_size:
        assert config.batch_size * config.gradient_accumulation_steps == target_batch_size


@settings(max_examples=100)
@given(
    use_case=use_case_strategy,
    gpu_memory_gb=st.floats(min_value=4.0, max_value=80.0),
    dataset_size=st.integers(min_value=100, max_value=100000)
)
def test_profile_estimates_include_time_and_requirements(use_case, gpu_memory_gb, dataset_size):
    """
    **Feature: simplified-llm-optimization, Property 3: Smart defaults calculation**
    **Validates: Requirements 3.3**
    
    For any profile, the estimates should include time and hardware requirements.
    """
    profile_service = get_profile_service()
    profile = profile_service.get_profile_by_use_case(use_case)
    
    # Verify profile has hardware requirements
    assert profile.requirements.min_gpu_memory_gb > 0
    assert profile.requirements.recommended_gpu_memory_gb > 0
    assert profile.requirements.min_dataset_size > 0
    assert profile.requirements.recommended_dataset_size > 0
    assert profile.requirements.estimated_time_per_epoch_minutes > 0
    
    # Verify compatibility check provides estimates
    result = profile_service.validate_profile_compatibility(
        profile_id=profile.id,
        gpu_memory_gb=gpu_memory_gb,
        dataset_size=dataset_size
    )
    
    assert "requirements" in result
    assert "estimated_time_per_epoch_minutes" in result["requirements"]
    assert result["requirements"]["estimated_time_per_epoch_minutes"] > 0


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
