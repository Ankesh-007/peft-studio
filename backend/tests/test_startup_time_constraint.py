"""
Property-Based Test for Startup Time Constraint

**Property 19: Startup time constraint**
*For any* application launch, the main UI should be interactive within 3 seconds
**Validates: Requirements 14.1**
"""

import pytest
import time
import subprocess
import sys
import os
from pathlib import Path
from hypothesis import given, strategies as st, settings, HealthCheck


@pytest.mark.property
def test_startup_time_constraint_single_launch():
    """
    Test that a single application launch meets the 3-second constraint.
    
    This is a deterministic test that verifies the basic startup time requirement.
    We measure the time to import and initialize the FastAPI app.
    """
    import time
    start_time = time.time()
    
    # Import the main module (this triggers all initialization)
    import main
    
    # Get the app (this should be fast since we use lazy loading)
    app = main.app
    
    startup_time = time.time() - start_time
    
    assert startup_time < 3.0, (
        f"Startup time {startup_time:.2f}s exceeds 3-second constraint. "
        f"The application must be interactive within 3 seconds."
    )


@pytest.mark.property
@given(
    launch_count=st.integers(min_value=1, max_value=3)
)
@settings(
    max_examples=3,  # Limited examples
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow]
)
def test_startup_time_constraint_multiple_launches(launch_count):
    """
    Property: For any number of application launches, each launch should meet the 3-second constraint.
    
    This tests that startup time is consistent across multiple imports,
    ensuring that initialization doesn't degrade or accumulate state.
    """
    import sys
    import importlib
    
    startup_times = []
    
    for i in range(launch_count):
        # Remove main from sys.modules to simulate fresh import
        if 'main' in sys.modules:
            del sys.modules['main']
        
        start = time.time()
        import main
        startup_time = time.time() - start
        startup_times.append(startup_time)
    
    # All launches should meet the constraint
    for i, startup_time in enumerate(startup_times):
        assert startup_time < 3.0, (
            f"Launch {i+1}/{launch_count}: Startup time {startup_time:.2f}s exceeds 3-second constraint"
        )
    
    # Average startup time should also be well under the constraint
    avg_startup = sum(startup_times) / len(startup_times)
    assert avg_startup < 2.5, (
        f"Average startup time {avg_startup:.2f}s is too close to the 3-second limit. "
        f"Individual times: {[f'{t:.2f}s' for t in startup_times]}"
    )


@pytest.mark.property
def test_startup_time_with_cold_cache():
    """
    Test startup time with a cold cache (first launch scenario).
    
    This simulates a user launching the application for the first time
    or after clearing cache.
    """
    import sys
    
    # Clear any cached data that might affect startup
    cache_dir = Path.home() / ".peft-studio" / "cache"
    if cache_dir.exists():
        import shutil
        shutil.rmtree(cache_dir, ignore_errors=True)
    
    # Remove main from cache to simulate cold start
    if 'main' in sys.modules:
        del sys.modules['main']
    
    start = time.time()
    import main
    startup_time = time.time() - start
    
    assert startup_time < 3.0, (
        f"Cold cache startup time {startup_time:.2f}s exceeds 3-second constraint. "
        f"First launch must also meet the performance requirement."
    )


@pytest.mark.property
def test_startup_time_components():
    """
    Test that individual startup components are optimized.
    
    This breaks down startup into measurable components to identify bottlenecks.
    """
    import importlib
    import time
    
    # Test 1: Import time for main module
    start = time.time()
    import main
    import_time = time.time() - start
    
    assert import_time < 1.0, (
        f"Main module import took {import_time:.2f}s, should be < 1s. "
        f"Consider lazy loading heavy dependencies."
    )
    
    # Test 2: Database initialization time
    start = time.time()
    from database import engine, Base
    Base.metadata.create_all(engine)
    db_init_time = time.time() - start
    
    assert db_init_time < 0.5, (
        f"Database initialization took {db_init_time:.2f}s, should be < 0.5s. "
        f"Consider optimizing schema creation or using connection pooling."
    )
    
    # Test 3: Service initialization time
    start = time.time()
    from services import (
        get_peft_service,
        get_hardware_service,
        get_model_registry_service
    )
    # Just import, don't actually initialize heavy services
    service_import_time = time.time() - start
    
    assert service_import_time < 0.5, (
        f"Service imports took {service_import_time:.2f}s, should be < 0.5s. "
        f"Heavy services should use lazy initialization."
    )


@pytest.mark.property
def test_startup_memory_footprint():
    """
    Test that startup memory usage is reasonable.
    
    While not directly part of the 3-second constraint, excessive memory
    usage during startup can slow down the application.
    """
    import psutil
    import sys
    
    # Get current process memory before import
    proc = psutil.Process()
    memory_before = proc.memory_info().rss / (1024 * 1024)
    
    # Remove main from cache
    if 'main' in sys.modules:
        del sys.modules['main']
    
    # Import main
    import main
    
    # Measure memory after import
    memory_after = proc.memory_info().rss / (1024 * 1024)
    memory_increase = memory_after - memory_before
    
    # The import itself should not add more than 100MB
    assert memory_increase < 100, (
        f"Startup memory increase {memory_increase:.1f}MB is too high. "
        f"Optimize memory usage during initialization. "
        f"Before: {memory_before:.1f}MB, After: {memory_after:.1f}MB"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "property"])
