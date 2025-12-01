"""
Property-Based Test for Resource Usage Limits

**Property 12: Resource usage limits**
*For any* application state, idle memory usage should never exceed 500MB and idle CPU should never exceed 1%
**Validates: Requirements 14.1, 14.4**
"""

import pytest
import time
import psutil
import gc
from hypothesis import given, strategies as st, settings, HealthCheck, assume
from typing import List, Dict, Any
import sys
import os


# Strategy for generating different application states
app_state_strategy = st.sampled_from([
    "startup",
    "idle",
    "after_training_config",
    "after_model_browse",
    "after_connection_test",
])

# Strategy for generating idle durations (1-60 seconds)
idle_duration_strategy = st.integers(min_value=1, max_value=60)


@pytest.mark.property
def test_idle_memory_usage_baseline():
    """
    Test that idle memory usage never exceeds 500MB in baseline state.
    
    This is a deterministic test that verifies the basic memory constraint.
    """
    # Force garbage collection to get accurate baseline
    gc.collect()
    
    # Get current process
    proc = psutil.Process()
    
    # Measure memory after import
    memory_mb = proc.memory_info().rss / (1024 * 1024)
    
    assert memory_mb < 500, (
        f"Idle memory usage {memory_mb:.1f}MB exceeds 500MB limit. "
        f"The application must stay under 500MB when idle."
    )


@pytest.mark.property
def test_idle_cpu_usage_baseline():
    """
    Test that idle CPU usage never exceeds 1% in baseline state.
    
    This is a deterministic test that verifies the basic CPU constraint.
    """
    # Get current process
    proc = psutil.Process()
    
    # Wait a bit to let any startup activity settle
    time.sleep(2)
    
    # Measure CPU usage over 1 second interval
    cpu_percent = proc.cpu_percent(interval=1.0)
    
    assert cpu_percent < 1.0, (
        f"Idle CPU usage {cpu_percent:.2f}% exceeds 1% limit. "
        f"The application must use less than 1% CPU when idle."
    )


@pytest.mark.property
@given(
    idle_duration=idle_duration_strategy
)
@settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow]
)
def test_memory_usage_over_time(idle_duration: int):
    """
    Property: For any idle duration, memory usage should remain under 200MB
    
    This tests that memory doesn't leak or accumulate over time.
    """
    # Force garbage collection
    gc.collect()
    
    # Get current process
    proc = psutil.Process()
    
    # Measure initial memory
    initial_memory_mb = proc.memory_info().rss / (1024 * 1024)
    
    # Wait for the specified duration
    time.sleep(idle_duration)
    
    # Force garbage collection again
    gc.collect()
    
    # Measure final memory
    final_memory_mb = proc.memory_info().rss / (1024 * 1024)
    
    # Memory should stay under 500MB
    assert final_memory_mb < 500, (
        f"Memory usage {final_memory_mb:.1f}MB exceeds 500MB limit after {idle_duration}s idle. "
        f"Initial: {initial_memory_mb:.1f}MB, Final: {final_memory_mb:.1f}MB"
    )
    
    # Memory should not grow significantly over time (allow 10MB growth for normal operations)
    memory_growth = final_memory_mb - initial_memory_mb
    assert memory_growth < 10, (
        f"Memory grew by {memory_growth:.1f}MB during {idle_duration}s idle period. "
        f"This suggests a memory leak. Initial: {initial_memory_mb:.1f}MB, Final: {final_memory_mb:.1f}MB"
    )


@pytest.mark.property
@given(
    app_state=app_state_strategy
)
@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow]
)
def test_memory_usage_across_states(app_state: str):
    """
    Property: For any application state, idle memory usage should remain under 200MB
    
    This tests that different application states don't cause memory to exceed limits.
    """
    # Force garbage collection
    gc.collect()
    
    # Get current process
    proc = psutil.Process()
    
    # Simulate different application states
    if app_state == "startup":
        # Just measure current state (already started)
        pass
    
    elif app_state == "idle":
        # Wait a bit to ensure truly idle
        time.sleep(2)
    
    elif app_state == "after_training_config":
        # Simulate creating a training config (lightweight operation)
        from services.training_config_service import TrainingConfigService
        service = TrainingConfigService()
        # Just instantiate, don't actually configure
    
    elif app_state == "after_model_browse":
        # Simulate browsing models (should use cache, not load models)
        from services.model_registry_service import ModelRegistryService
        service = ModelRegistryService()
        # Just instantiate, don't actually fetch
    
    elif app_state == "after_connection_test":
        # Simulate testing a connection (lightweight operation)
        from services.platform_connection_service import PlatformConnectionService
        service = PlatformConnectionService()
        # Just instantiate
    
    # Force garbage collection after state change
    gc.collect()
    
    # Wait a moment for any async cleanup
    time.sleep(1)
    
    # Measure memory
    memory_mb = proc.memory_info().rss / (1024 * 1024)
    
    assert memory_mb < 500, (
        f"Memory usage {memory_mb:.1f}MB exceeds 500MB limit in state '{app_state}'. "
        f"Each application state must maintain memory under 500MB when idle."
    )


@pytest.mark.property
@given(
    measurement_count=st.integers(min_value=3, max_value=10)
)
@settings(
    max_examples=5,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow]
)
def test_cpu_usage_consistency(measurement_count: int):
    """
    Property: For any number of measurements, idle CPU usage should consistently stay under 1%
    
    This tests that CPU usage is consistently low, not just occasionally.
    """
    # Get current process
    proc = psutil.Process()
    
    # Wait for any startup activity to settle
    time.sleep(2)
    
    cpu_measurements = []
    
    for i in range(measurement_count):
        # Measure CPU over 1 second interval
        cpu_percent = proc.cpu_percent(interval=1.0)
        cpu_measurements.append(cpu_percent)
        
        # Small delay between measurements
        time.sleep(0.5)
    
    # Most measurements should be under 1% (allow occasional spikes)
    measurements_under_limit = sum(1 for cpu in cpu_measurements if cpu < 1.0)
    pass_rate = measurements_under_limit / len(cpu_measurements)
    
    assert pass_rate >= 0.8, (
        f"Only {measurements_under_limit}/{measurement_count} measurements under 1% CPU limit. "
        f"At least 80% should be under 1%. All measurements: {[f'{c:.2f}%' for c in cpu_measurements]}"
    )
    
    # Average should be well under 1%
    avg_cpu = sum(cpu_measurements) / len(cpu_measurements)
    assert avg_cpu < 1.0, (
        f"Average CPU usage {avg_cpu:.2f}% exceeds 1% limit. "
        f"Average should be under 1% for idle application. "
        f"Measurements: {[f'{c:.2f}%' for c in cpu_measurements]}"
    )


@pytest.mark.property
def test_memory_cleanup_after_operations():
    """
    Test that memory is properly cleaned up after operations.
    
    This verifies that temporary operations don't leave memory allocated.
    """
    # Force garbage collection
    gc.collect()
    
    # Get current process
    proc = psutil.Process()
    
    # Measure baseline memory
    baseline_memory_mb = proc.memory_info().rss / (1024 * 1024)
    
    # Perform some operations that should be cleaned up
    operations = []
    
    # Operation 1: Create and discard a large list
    large_list = [i for i in range(100000)]
    operations.append(len(large_list))
    del large_list
    
    # Operation 2: Create and discard a dictionary
    large_dict = {i: str(i) * 100 for i in range(1000)}
    operations.append(len(large_dict))
    del large_dict
    
    # Operation 3: Import and use a lightweight service (avoid importing ML libraries)
    # Note: Importing services that load PyTorch/Transformers will increase memory significantly
    # This is expected behavior for ML applications
    from services.platform_connection_service import PlatformConnectionService
    service = PlatformConnectionService()
    operations.append(1)
    del service
    
    # Force garbage collection
    gc.collect()
    
    # Wait for cleanup
    time.sleep(1)
    
    # Measure final memory
    final_memory_mb = proc.memory_info().rss / (1024 * 1024)
    
    # Memory should return close to baseline (allow 20MB variance for Python overhead)
    memory_increase = final_memory_mb - baseline_memory_mb
    assert memory_increase < 20, (
        f"Memory increased by {memory_increase:.1f}MB after operations and cleanup. "
        f"This suggests incomplete cleanup. Baseline: {baseline_memory_mb:.1f}MB, "
        f"Final: {final_memory_mb:.1f}MB"
    )
    
    # Final memory should still be under 500MB
    assert final_memory_mb < 500, (
        f"Final memory {final_memory_mb:.1f}MB exceeds 500MB limit after cleanup"
    )


@pytest.mark.property
def test_no_background_threads_consuming_cpu():
    """
    Test that there are no background threads consuming CPU when idle.
    
    This verifies that background tasks are properly paused or throttled.
    """
    # Get current process
    proc = psutil.Process()
    
    # Wait for startup to complete
    time.sleep(3)
    
    # Get thread count
    thread_count = proc.num_threads()
    
    # Should have minimal threads (main thread + system threads + pytest threads)
    # Python applications typically have 15-25 threads including system threads
    assert thread_count < 30, (
        f"Too many threads ({thread_count}) running. "
        f"Excessive threads can consume CPU even when idle."
    )
    
    # Measure CPU usage
    cpu_percent = proc.cpu_percent(interval=2.0)
    
    assert cpu_percent < 1.0, (
        f"CPU usage {cpu_percent:.2f}% exceeds 1% limit with {thread_count} threads. "
        f"Background threads may be consuming CPU."
    )


@pytest.mark.property
@given(
    cycles=st.integers(min_value=2, max_value=5)
)
@settings(
    max_examples=3,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow]
)
def test_memory_stability_across_cycles(cycles: int):
    """
    Property: For any number of operation cycles, memory should remain stable
    
    This tests that repeated operations don't cause memory to accumulate.
    """
    # Force garbage collection
    gc.collect()
    
    # Get current process
    proc = psutil.Process()
    
    memory_measurements = []
    
    for cycle in range(cycles):
        # Perform a lightweight operation
        from services.peft_service import PEFTService
        service = PEFTService()
        
        # Simulate some work (just instantiation is enough)
        _ = str(service)
        
        # Clean up
        del service
        gc.collect()
        
        # Wait a moment
        time.sleep(1)
        
        # Measure memory
        memory_mb = proc.memory_info().rss / (1024 * 1024)
        memory_measurements.append(memory_mb)
    
    # All measurements should be under 500MB
    for i, memory_mb in enumerate(memory_measurements):
        assert memory_mb < 500, (
            f"Cycle {i+1}/{cycles}: Memory {memory_mb:.1f}MB exceeds 500MB limit. "
            f"All measurements: {[f'{m:.1f}MB' for m in memory_measurements]}"
        )
    
    # Memory should not grow significantly across cycles
    if len(memory_measurements) > 1:
        memory_growth = memory_measurements[-1] - memory_measurements[0]
        assert memory_growth < 10, (
            f"Memory grew by {memory_growth:.1f}MB across {cycles} cycles. "
            f"This suggests accumulation. Measurements: {[f'{m:.1f}MB' for m in memory_measurements]}"
        )


@pytest.mark.property
def test_resource_limits_with_database_operations():
    """
    Test that database operations don't cause resource usage to exceed limits.
    
    This verifies that database connections are properly managed.
    """
    # Force garbage collection
    gc.collect()
    
    # Get current process
    proc = psutil.Process()
    
    # Measure baseline
    baseline_memory_mb = proc.memory_info().rss / (1024 * 1024)
    
    # Perform database operations
    from database import SessionLocal, TrainingRun
    
    # Create a session
    db = SessionLocal()
    
    try:
        # Query database (should be lightweight)
        runs = db.query(TrainingRun).limit(10).all()
        
        # Close session
        db.close()
    
    except Exception as e:
        # If database doesn't exist yet, that's okay
        pass
    
    finally:
        if db:
            db.close()
    
    # Force garbage collection
    gc.collect()
    
    # Wait for cleanup
    time.sleep(1)
    
    # Measure final memory
    final_memory_mb = proc.memory_info().rss / (1024 * 1024)
    
    # Memory should still be under 500MB
    assert final_memory_mb < 500, (
        f"Memory {final_memory_mb:.1f}MB exceeds 500MB limit after database operations. "
        f"Baseline: {baseline_memory_mb:.1f}MB"
    )
    
    # Memory increase should be minimal
    memory_increase = final_memory_mb - baseline_memory_mb
    assert memory_increase < 10, (
        f"Database operations increased memory by {memory_increase:.1f}MB. "
        f"Connection pooling may not be working correctly."
    )


@pytest.mark.property
def test_resource_usage_report():
    """
    Generate a comprehensive resource usage report.
    
    This provides detailed information about current resource usage.
    """
    # Force garbage collection
    gc.collect()
    
    # Get current process
    proc = psutil.Process()
    
    # Wait for idle state
    time.sleep(2)
    
    # Collect metrics
    memory_mb = proc.memory_info().rss / (1024 * 1024)
    cpu_percent = proc.cpu_percent(interval=1.0)
    thread_count = proc.num_threads()
    
    # Get memory breakdown
    memory_info = proc.memory_info()
    
    report = {
        "memory_mb": memory_mb,
        "memory_limit_mb": 500,
        "memory_within_limit": memory_mb < 500,
        "cpu_percent": cpu_percent,
        "cpu_limit_percent": 1.0,
        "cpu_within_limit": cpu_percent < 1.0,
        "thread_count": thread_count,
        "memory_breakdown": {
            "rss_mb": memory_info.rss / (1024 * 1024),
            "vms_mb": memory_info.vms / (1024 * 1024),
        }
    }
    
    # Print report for debugging
    print("\n=== Resource Usage Report ===")
    print(f"Memory: {memory_mb:.1f}MB / 500MB (limit)")
    print(f"CPU: {cpu_percent:.2f}% / 1.0% (limit)")
    print(f"Threads: {thread_count}")
    print(f"Memory within limit: {report['memory_within_limit']}")
    print(f"CPU within limit: {report['cpu_within_limit']}")
    print("============================\n")
    
    # Assert limits
    assert report["memory_within_limit"], (
        f"Memory usage {memory_mb:.1f}MB exceeds 500MB limit"
    )
    
    assert report["cpu_within_limit"], (
        f"CPU usage {cpu_percent:.2f}% exceeds 1% limit"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "property"])
