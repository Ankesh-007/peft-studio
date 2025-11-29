"""
Property-based tests for hardware detection.

**Feature: simplified-llm-optimization, Property 4: Hardware detection completeness**
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pytest
from hypothesis import given, strategies as st, settings, assume

# Import directly from hardware_service to avoid torch dependency from __init__.py
import importlib.util
spec = importlib.util.spec_from_file_location(
    "hardware_service",
    backend_dir / "services" / "hardware_service.py"
)
hardware_service = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hardware_service)

HardwareService = hardware_service.HardwareService
GPUInfo = hardware_service.GPUInfo
CPUInfo = hardware_service.CPUInfo
RAMInfo = hardware_service.RAMInfo
HardwareProfile = hardware_service.HardwareProfile


@settings(max_examples=100)
@given(st.just(None))  # We don't need random input, just run the test multiple times
def test_hardware_detection_completeness(dummy):
    """
    **Feature: simplified-llm-optimization, Property 4: Hardware detection completeness**
    **Validates: Requirements 2.1**
    
    For any system initialization, the hardware detection should return valid values
    for GPU memory, CPU cores, and RAM capacity.
    """
    service = HardwareService()
    
    # Get hardware profile
    profile = service.get_hardware_profile(use_cache=False)
    
    # Verify profile is not None
    assert profile is not None, "Hardware profile should not be None"
    
    # Verify timestamp is set
    assert profile.timestamp is not None, "Profile timestamp should be set"
    
    # Verify platform information
    assert profile.platform is not None, "Platform should be detected"
    assert len(profile.platform) > 0, "Platform should not be empty"
    
    assert profile.python_version is not None, "Python version should be detected"
    assert len(profile.python_version) > 0, "Python version should not be empty"
    
    assert profile.torch_version is not None, "Torch version should be detected"
    assert len(profile.torch_version) > 0, "Torch version should not be empty"
    
    # Verify CUDA availability is a boolean
    assert isinstance(profile.cuda_available, bool), "CUDA availability should be boolean"
    
    # Verify CPU detection
    assert profile.cpu is not None, "CPU info should be detected"
    assert profile.cpu.cores_physical > 0, f"Physical cores should be positive, got {profile.cpu.cores_physical}"
    assert profile.cpu.cores_logical > 0, f"Logical cores should be positive, got {profile.cpu.cores_logical}"
    assert profile.cpu.cores_logical >= profile.cpu.cores_physical, \
        "Logical cores should be >= physical cores"
    assert profile.cpu.frequency_mhz >= 0, f"CPU frequency should be non-negative, got {profile.cpu.frequency_mhz}"
    assert profile.cpu.architecture is not None, "CPU architecture should be detected"
    assert len(profile.cpu.architecture) > 0, "CPU architecture should not be empty"
    assert 0 <= profile.cpu.utilization <= 100, \
        f"CPU utilization should be in [0, 100], got {profile.cpu.utilization}"
    
    # Verify RAM detection
    assert profile.ram is not None, "RAM info should be detected"
    assert profile.ram.total > 0, f"Total RAM should be positive, got {profile.ram.total}"
    assert profile.ram.available >= 0, f"Available RAM should be non-negative, got {profile.ram.available}"
    assert profile.ram.used >= 0, f"Used RAM should be non-negative, got {profile.ram.used}"
    assert profile.ram.available <= profile.ram.total, \
        f"Available RAM ({profile.ram.available}) should be <= total RAM ({profile.ram.total})"
    assert 0 <= profile.ram.percent_used <= 100, \
        f"RAM percent used should be in [0, 100], got {profile.ram.percent_used}"
    
    # Verify GPU detection (if CUDA is available)
    assert profile.gpus is not None, "GPU list should not be None (can be empty)"
    assert isinstance(profile.gpus, list), "GPUs should be a list"
    
    if profile.cuda_available:
        # If CUDA is available, we should have at least one GPU
        assert len(profile.gpus) > 0, "Should detect at least one GPU when CUDA is available"
        
        for i, gpu in enumerate(profile.gpus):
            assert gpu.id >= 0, f"GPU {i} ID should be non-negative, got {gpu.id}"
            assert gpu.name is not None, f"GPU {i} name should be set"
            assert len(gpu.name) > 0, f"GPU {i} name should not be empty"
            assert gpu.memory_total > 0, f"GPU {i} total memory should be positive, got {gpu.memory_total}"
            assert gpu.memory_available >= 0, \
                f"GPU {i} available memory should be non-negative, got {gpu.memory_available}"
            assert gpu.memory_used >= 0, \
                f"GPU {i} used memory should be non-negative, got {gpu.memory_used}"
            assert gpu.memory_available <= gpu.memory_total, \
                f"GPU {i} available memory should be <= total memory"
            assert gpu.compute_capability is not None, f"GPU {i} compute capability should be set"
            assert len(gpu.compute_capability) > 0, f"GPU {i} compute capability should not be empty"
            # Compute capability should be in format "X.Y"
            assert "." in gpu.compute_capability, \
                f"GPU {i} compute capability should be in format 'X.Y', got {gpu.compute_capability}"
            assert gpu.cuda_version is not None, f"GPU {i} CUDA version should be set"
            assert len(gpu.cuda_version) > 0, f"GPU {i} CUDA version should not be empty"
    else:
        # If CUDA is not available, GPU list should be empty
        assert len(profile.gpus) == 0, "GPU list should be empty when CUDA is not available"


@settings(max_examples=100)
@given(st.just(None))
def test_hardware_detection_caching(dummy):
    """
    For any hardware service, requesting the profile twice within the cache duration
    should return the same cached instance.
    """
    service = HardwareService()
    
    # Clear any existing cache
    service.clear_cache()
    
    # Get profile twice
    profile1 = service.get_hardware_profile(use_cache=True)
    profile2 = service.get_hardware_profile(use_cache=True)
    
    # Should return the same cached instance
    assert profile1 is profile2, "Should return cached profile on second call"
    assert profile1.timestamp == profile2.timestamp, "Timestamps should match for cached profile"


@settings(max_examples=100)
@given(st.just(None))
def test_hardware_detection_cache_refresh(dummy):
    """
    For any hardware service, requesting the profile with use_cache=False
    should always return a fresh profile.
    """
    service = HardwareService()
    
    # Get profile twice without cache
    profile1 = service.get_hardware_profile(use_cache=False)
    profile2 = service.get_hardware_profile(use_cache=False)
    
    # Should return different instances
    assert profile1 is not profile2, "Should return fresh profile when cache is disabled"
    
    # Timestamps might be very close but should be different instances
    assert profile1.timestamp is not None
    assert profile2.timestamp is not None


@settings(max_examples=50)
@given(st.integers(min_value=0, max_value=7))
def test_gpu_available_memory_detection(device_id):
    """
    For any valid GPU device ID, the available memory detection should return
    a non-negative value.
    """
    import torch
    
    # Skip entire test if CUDA is not available
    if not torch.cuda.is_available():
        pytest.skip("CUDA not available - skipping GPU memory test")
    
    service = HardwareService()
    
    # Only test valid device IDs
    num_gpus = torch.cuda.device_count()
    assume(device_id < num_gpus)
    
    available_memory = service.get_available_memory(device_id)
    
    assert available_memory >= 0, \
        f"Available memory for GPU {device_id} should be non-negative, got {available_memory}"


@settings(max_examples=100)
@given(st.just(None))
def test_cuda_environment_validation(dummy):
    """
    For any system, CUDA environment validation should return a complete
    validation dictionary with all required fields.
    """
    service = HardwareService()
    
    validation = service.validate_cuda_environment()
    
    # Verify all required fields are present
    assert "cuda_available" in validation, "Should include cuda_available field"
    assert "cuda_version" in validation, "Should include cuda_version field"
    assert "cudnn_available" in validation, "Should include cudnn_available field"
    assert "cudnn_version" in validation, "Should include cudnn_version field"
    assert "gpu_count" in validation, "Should include gpu_count field"
    assert "torch_version" in validation, "Should include torch_version field"
    assert "errors" in validation, "Should include errors field"
    
    # Verify field types
    assert isinstance(validation["cuda_available"], bool), "cuda_available should be boolean"
    assert isinstance(validation["cudnn_available"], bool), "cudnn_available should be boolean"
    assert isinstance(validation["gpu_count"], int), "gpu_count should be integer"
    assert validation["gpu_count"] >= 0, "gpu_count should be non-negative"
    assert isinstance(validation["errors"], list), "errors should be a list"
    assert isinstance(validation["torch_version"], str), "torch_version should be string"
    
    # Verify logical consistency
    if not validation["cuda_available"]:
        assert validation["gpu_count"] == 0, \
            "GPU count should be 0 when CUDA is not available"
        assert len(validation["errors"]) > 0, \
            "Should have at least one error when CUDA is not available"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
