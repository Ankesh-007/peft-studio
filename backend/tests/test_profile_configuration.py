"""
Property-based tests for optimization profile configuration.

**Feature: simplified-llm-optimization, Property 1: Use case selection configures all parameters**
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pytest
from hypothesis import given, strategies as st, settings

# Import the profile service directly without going through __init__
# This avoids importing heavy dependencies like transformers
try:
    from services.profile_service import (
        ProfileService,
        UseCase,
        OptimizationProfile,
        get_profile_service
    )
except ImportError:
    # If imports fail, try importing directly
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "profile_service",
        backend_dir / "services" / "profile_service.py"
    )
    profile_service_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(profile_service_module)
    
    ProfileService = profile_service_module.ProfileService
    UseCase = profile_service_module.UseCase
    OptimizationProfile = profile_service_module.OptimizationProfile
    get_profile_service = profile_service_module.get_profile_service


# Strategy for generating valid use cases
use_case_strategy = st.sampled_from([
    UseCase.CHATBOT,
    UseCase.CODE_GENERATION,
    UseCase.SUMMARIZATION,
    UseCase.QA,
    UseCase.CREATIVE_WRITING,
    UseCase.DOMAIN_ADAPTATION
])


@settings(max_examples=100)
@given(use_case=use_case_strategy)
def test_use_case_selection_configures_all_parameters(use_case):
    """
    **Feature: simplified-llm-optimization, Property 1: Use case selection configures all parameters**
    **Validates: Requirements 1.2, 3.2**
    
    For any optimization profile selection (use case), the system should automatically populate
    all required technical parameters (LoRA settings, learning rate, batch size, epochs, target modules).
    """
    # Get the profile service
    profile_service = get_profile_service()
    
    # Get profile for the use case
    profile = profile_service.get_profile_by_use_case(use_case)
    
    # Verify profile exists
    assert profile is not None, f"Profile not found for use case: {use_case}"
    
    # Verify all required LoRA parameters are configured
    assert profile.config.lora_r > 0, f"LoRA rank (r) must be positive, got {profile.config.lora_r}"
    assert profile.config.lora_alpha > 0, f"LoRA alpha must be positive, got {profile.config.lora_alpha}"
    assert 0.0 <= profile.config.lora_dropout <= 1.0, \
        f"LoRA dropout must be in [0, 1], got {profile.config.lora_dropout}"
    
    # Verify target modules are configured
    assert profile.config.target_modules is not None, "Target modules must be configured"
    assert len(profile.config.target_modules) > 0, "Target modules list must not be empty"
    
    # Verify all target modules are valid projection names
    valid_projections = {"q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"}
    for module in profile.config.target_modules:
        assert module in valid_projections, f"Invalid target module: {module}"
    
    # Verify learning rate is configured
    assert profile.config.learning_rate > 0, \
        f"Learning rate must be positive, got {profile.config.learning_rate}"
    assert profile.config.learning_rate <= 1.0, \
        f"Learning rate seems too high: {profile.config.learning_rate}"
    
    # Verify epochs are configured
    assert profile.config.num_epochs > 0, \
        f"Number of epochs must be positive, got {profile.config.num_epochs}"
    
    # Verify warmup ratio is configured
    assert 0.0 <= profile.config.warmup_ratio <= 1.0, \
        f"Warmup ratio must be in [0, 1], got {profile.config.warmup_ratio}"
    
    # Verify max sequence length is configured
    assert profile.config.max_seq_length > 0, \
        f"Max sequence length must be positive, got {profile.config.max_seq_length}"
    
    # Verify weight decay is configured
    assert profile.config.weight_decay >= 0, \
        f"Weight decay must be non-negative, got {profile.config.weight_decay}"
    
    # Verify max grad norm is configured
    assert profile.config.max_grad_norm > 0, \
        f"Max grad norm must be positive, got {profile.config.max_grad_norm}"
    
    # Verify scheduler is configured
    assert profile.config.scheduler is not None, "Scheduler must be configured"
    assert profile.config.scheduler in ["linear", "cosine", "constant"], \
        f"Invalid scheduler: {profile.config.scheduler}"
    
    # Verify hardware requirements are configured
    assert profile.requirements.min_gpu_memory_gb > 0, \
        "Minimum GPU memory must be positive"
    assert profile.requirements.recommended_gpu_memory_gb >= profile.requirements.min_gpu_memory_gb, \
        "Recommended GPU memory must be >= minimum"
    assert profile.requirements.min_dataset_size > 0, \
        "Minimum dataset size must be positive"
    assert profile.requirements.recommended_dataset_size >= profile.requirements.min_dataset_size, \
        "Recommended dataset size must be >= minimum"
    assert profile.requirements.estimated_time_per_epoch_minutes > 0, \
        "Estimated time per epoch must be positive"
    
    # Verify metadata is configured
    assert profile.id is not None and len(profile.id) > 0, "Profile ID must be configured"
    assert profile.name is not None and len(profile.name) > 0, "Profile name must be configured"
    assert profile.description is not None and len(profile.description) > 0, \
        "Profile description must be configured"
    assert profile.icon is not None and len(profile.icon) > 0, "Profile icon must be configured"
    assert profile.example_use_cases is not None and len(profile.example_use_cases) > 0, \
        "Example use cases must be configured"


@settings(max_examples=100)
@given(use_case=use_case_strategy)
def test_profile_id_matches_use_case(use_case):
    """
    For any use case, the profile ID should be consistent and retrievable.
    """
    profile_service = get_profile_service()
    
    # Get profile by use case
    profile = profile_service.get_profile_by_use_case(use_case)
    assert profile is not None
    
    # Get profile by ID
    profile_by_id = profile_service.get_profile(profile.id)
    assert profile_by_id is not None
    
    # Verify they are the same profile
    assert profile.id == profile_by_id.id
    assert profile.use_case == profile_by_id.use_case
    assert profile.name == profile_by_id.name


@settings(max_examples=100)
@given(use_case=use_case_strategy)
def test_profile_to_dict_contains_all_fields(use_case):
    """
    For any profile, the to_dict() method should return all required fields.
    """
    profile_service = get_profile_service()
    profile = profile_service.get_profile_by_use_case(use_case)
    
    profile_dict = profile.to_dict()
    
    # Verify top-level fields
    assert "id" in profile_dict
    assert "name" in profile_dict
    assert "description" in profile_dict
    assert "use_case" in profile_dict
    assert "icon" in profile_dict
    assert "example_use_cases" in profile_dict
    assert "config" in profile_dict
    assert "requirements" in profile_dict
    assert "tags" in profile_dict
    
    # Verify config fields
    config = profile_dict["config"]
    assert "lora_r" in config
    assert "lora_alpha" in config
    assert "lora_dropout" in config
    assert "target_modules" in config
    assert "learning_rate" in config
    assert "num_epochs" in config
    assert "warmup_ratio" in config
    assert "max_seq_length" in config
    assert "weight_decay" in config
    assert "max_grad_norm" in config
    assert "scheduler" in config
    
    # Verify requirements fields
    requirements = profile_dict["requirements"]
    assert "min_gpu_memory_gb" in requirements
    assert "recommended_gpu_memory_gb" in requirements
    assert "min_dataset_size" in requirements
    assert "recommended_dataset_size" in requirements
    assert "estimated_time_per_epoch_minutes" in requirements


@settings(max_examples=100)
@given(
    use_case=use_case_strategy,
    override_lr=st.floats(min_value=1e-6, max_value=1e-3),
    override_epochs=st.integers(min_value=1, max_value=10)
)
def test_apply_profile_config_with_overrides(use_case, override_lr, override_epochs):
    """
    For any profile with parameter overrides, the applied configuration should
    preserve overrides while keeping other parameters from the profile.
    """
    profile_service = get_profile_service()
    profile = profile_service.get_profile_by_use_case(use_case)
    
    # Apply config with overrides
    overrides = {
        "learning_rate": override_lr,
        "num_epochs": override_epochs
    }
    
    config = profile_service.apply_profile_config(
        profile_id=profile.id,
        overrides=overrides
    )
    
    # Verify overrides were applied
    assert abs(config["learning_rate"] - override_lr) < 1e-9, \
        f"Learning rate override not applied: expected {override_lr}, got {config['learning_rate']}"
    assert config["num_epochs"] == override_epochs, \
        f"Epochs override not applied: expected {override_epochs}, got {config['num_epochs']}"
    
    # Verify other parameters remain from profile
    assert config["lora_r"] == profile.config.lora_r
    assert config["lora_alpha"] == profile.config.lora_alpha
    assert abs(config["lora_dropout"] - profile.config.lora_dropout) < 1e-9
    assert config["target_modules"] == profile.config.target_modules


@settings(max_examples=100)
@given(
    use_case=use_case_strategy,
    gpu_memory=st.floats(min_value=4.0, max_value=80.0),
    dataset_size=st.integers(min_value=100, max_value=100000)
)
def test_validate_profile_compatibility(use_case, gpu_memory, dataset_size):
    """
    For any profile and hardware/dataset combination, the compatibility validation
    should return a valid result with appropriate warnings.
    """
    profile_service = get_profile_service()
    profile = profile_service.get_profile_by_use_case(use_case)
    
    result = profile_service.validate_profile_compatibility(
        profile_id=profile.id,
        gpu_memory_gb=gpu_memory,
        dataset_size=dataset_size
    )
    
    # Verify result structure
    assert "compatible" in result
    assert "warnings" in result
    assert "profile_name" in result
    assert "requirements" in result
    
    # Verify compatibility logic
    if gpu_memory < profile.requirements.min_gpu_memory_gb:
        assert result["compatible"] is False, \
            "Should be incompatible when GPU memory is below minimum"
        assert any("GPU memory" in w for w in result["warnings"]), \
            "Should have GPU memory warning"
    
    if dataset_size < profile.requirements.min_dataset_size:
        assert result["compatible"] is False, \
            "Should be incompatible when dataset size is below minimum"
        assert any("dataset size" in w for w in result["warnings"]), \
            "Should have dataset size warning"
    
    # Verify warnings are strings
    assert isinstance(result["warnings"], list)
    for warning in result["warnings"]:
        assert isinstance(warning, str)
        assert len(warning) > 0


def test_all_use_cases_have_profiles():
    """
    Verify that all defined use cases have corresponding profiles.
    """
    profile_service = get_profile_service()
    
    for use_case in UseCase:
        profile = profile_service.get_profile_by_use_case(use_case)
        assert profile is not None, f"No profile found for use case: {use_case}"


def test_profile_service_has_six_profiles():
    """
    Verify that the profile service has exactly 6 built-in profiles.
    """
    profile_service = get_profile_service()
    profiles = profile_service.list_profiles()
    
    assert len(profiles) == 6, f"Expected 6 profiles, got {len(profiles)}"
    
    # Verify all expected use cases are present
    use_cases = {profile.use_case for profile in profiles}
    expected_use_cases = {
        UseCase.CHATBOT,
        UseCase.CODE_GENERATION,
        UseCase.SUMMARIZATION,
        UseCase.QA,
        UseCase.CREATIVE_WRITING,
        UseCase.DOMAIN_ADAPTATION
    }
    
    assert use_cases == expected_use_cases, \
        f"Profile use cases don't match expected: {use_cases} vs {expected_use_cases}"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
