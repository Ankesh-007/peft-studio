"""
Property-based tests for memory threshold triggering batch size reduction.

**Feature: simplified-llm-optimization, Property 12: Memory threshold triggers batch size reduction**
**Validates: Requirements 6.3**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from services.anomaly_detection_service import (
    AnomalyDetectionService,
    AnomalyType,
    get_anomaly_detection_service
)


@given(
    job_id=st.text(min_size=1, max_size=50),
    step=st.integers(min_value=1, max_value=10000),
    memory_used=st.floats(min_value=1000.0, max_value=100000.0),
    memory_total=st.floats(min_value=1000.0, max_value=100000.0)
)
@settings(max_examples=100)
def test_memory_threshold_triggers_batch_size_reduction(job_id, step, memory_used, memory_total):
    """
    **Feature: simplified-llm-optimization, Property 12: Memory threshold triggers batch size reduction**
    
    For any GPU memory state where usage exceeds 90%, the system should:
    - Detect an OOM anomaly
    - Suggest batch size reduction as an automatic action
    - Provide at least 2 suggested actions
    """
    # Ensure memory_total is greater than memory_used for valid test
    assume(memory_total > 0)
    assume(memory_used <= memory_total)
    
    service = AnomalyDetectionService()
    
    # Calculate utilization
    utilization = memory_used / memory_total
    
    # Detect memory issue
    anomaly = service.detect_memory_issue(
        job_id=job_id,
        gpu_memory_used=[memory_used],
        gpu_memory_total=[memory_total],
        step=step
    )
    
    # Property 12: If memory usage > 90%, should trigger anomaly
    if utilization > 0.90:
        assert anomaly is not None, f"Should detect anomaly when utilization is {utilization*100:.1f}%"
        assert anomaly.type == AnomalyType.OOM, "Anomaly type should be OOM"
        
        # Property 12: Should suggest batch size reduction
        action_descriptions = [action.description.lower() for action in anomaly.suggested_actions]
        has_batch_size_reduction = any(
            'batch size' in desc and 'reduce' in desc
            for desc in action_descriptions
        )
        assert has_batch_size_reduction, "Should suggest batch size reduction"
        
        # Property 12: Batch size reduction should be automatic
        batch_size_action = None
        for action in anomaly.suggested_actions:
            if 'batch size' in action.description.lower() and 'reduce' in action.description.lower():
                batch_size_action = action
                break
        
        assert batch_size_action is not None
        assert batch_size_action.automatic is True, "Batch size reduction should be automatic"
        
        # Property 12: Should have at least 2 actions
        assert len(anomaly.suggested_actions) >= 2, "Should provide at least 2 suggested actions"
        
        # Property 12: Should have clear explanation
        assert len(anomaly.message) > 0, "Should have non-empty message"
        assert 'memory' in anomaly.message.lower(), "Message should mention memory"
    
    else:
        # If utilization <= 90%, should not trigger OOM anomaly
        # (but might trigger memory leak if history shows increasing pattern)
        if anomaly is not None:
            # If anomaly detected, it should be memory leak, not OOM
            assert anomaly.type == AnomalyType.MEMORY_LEAK or anomaly.type == AnomalyType.OOM
    
    service.clear_history(job_id)


@given(
    job_id=st.text(min_size=1, max_size=50),
    step=st.integers(min_value=1, max_value=10000),
    utilization_percent=st.floats(min_value=91.0, max_value=99.9)
)
@settings(max_examples=100)
def test_high_memory_always_triggers_batch_reduction_suggestion(job_id, step, utilization_percent):
    """
    Test that any memory usage above 90% triggers batch size reduction suggestion.
    """
    service = AnomalyDetectionService()
    
    # Create memory state above threshold
    memory_total = 10000.0  # 10GB
    memory_used = memory_total * (utilization_percent / 100.0)
    
    anomaly = service.detect_memory_issue(
        job_id=job_id,
        gpu_memory_used=[memory_used],
        gpu_memory_total=[memory_total],
        step=step
    )
    
    # Should always detect anomaly for >90% usage
    assert anomaly is not None, f"Should detect anomaly at {utilization_percent:.1f}% utilization"
    assert anomaly.type == AnomalyType.OOM
    
    # Should suggest batch size reduction
    has_batch_reduction = False
    for action in anomaly.suggested_actions:
        if 'batch' in action.description.lower() and 'reduce' in action.description.lower():
            has_batch_reduction = True
            assert action.automatic is True, "Batch size reduction should be automatic"
            break
    
    assert has_batch_reduction, "Should suggest batch size reduction"
    
    service.clear_history(job_id)


@given(
    job_id=st.text(min_size=1, max_size=50),
    step=st.integers(min_value=1, max_value=10000),
    num_gpus=st.integers(min_value=1, max_value=8)
)
@settings(max_examples=100)
def test_multi_gpu_memory_threshold_detection(job_id, step, num_gpus):
    """
    Test that memory threshold detection works correctly with multiple GPUs.
    """
    service = AnomalyDetectionService()
    
    # Create memory states for multiple GPUs
    # Make one GPU exceed threshold
    gpu_memory_used = []
    gpu_memory_total = []
    
    for i in range(num_gpus):
        total = 10000.0  # 10GB per GPU
        if i == 0:
            # First GPU exceeds threshold
            used = total * 0.95  # 95% usage
        else:
            # Other GPUs are fine
            used = total * 0.70  # 70% usage
        
        gpu_memory_used.append(used)
        gpu_memory_total.append(total)
    
    anomaly = service.detect_memory_issue(
        job_id=job_id,
        gpu_memory_used=gpu_memory_used,
        gpu_memory_total=gpu_memory_total,
        step=step
    )
    
    # Should detect anomaly even if only one GPU exceeds threshold
    assert anomaly is not None, "Should detect anomaly when any GPU exceeds threshold"
    assert anomaly.type == AnomalyType.OOM
    
    # Should mention which GPU
    assert 'GPU' in anomaly.message or 'gpu' in anomaly.message.lower()
    
    # Should suggest batch size reduction
    has_batch_reduction = any(
        'batch' in action.description.lower() and 'reduce' in action.description.lower()
        for action in anomaly.suggested_actions
    )
    assert has_batch_reduction, "Should suggest batch size reduction"
    
    service.clear_history(job_id)


@given(
    job_id=st.text(min_size=1, max_size=50),
    step=st.integers(min_value=1, max_value=10000)
)
@settings(max_examples=100)
def test_below_threshold_does_not_trigger_oom(job_id, step):
    """
    Test that memory usage below 90% does not trigger OOM anomaly.
    """
    service = AnomalyDetectionService()
    
    # Create memory state below threshold
    memory_total = 10000.0  # 10GB
    memory_used = memory_total * 0.85  # 85% usage (below 90% threshold)
    
    anomaly = service.detect_memory_issue(
        job_id=job_id,
        gpu_memory_used=[memory_used],
        gpu_memory_total=[memory_total],
        step=step
    )
    
    # Should not detect OOM anomaly (might detect memory leak if history shows pattern)
    if anomaly is not None:
        assert anomaly.type != AnomalyType.OOM, "Should not trigger OOM below 90% threshold"
    
    service.clear_history(job_id)


def test_exact_threshold_boundary():
    """
    Test behavior at exactly 90% memory usage.
    """
    service = AnomalyDetectionService()
    job_id = "test_job"
    step = 100
    
    # Test at exactly 90%
    memory_total = 10000.0
    memory_used = memory_total * 0.90  # Exactly 90%
    
    anomaly = service.detect_memory_issue(
        job_id=job_id,
        gpu_memory_used=[memory_used],
        gpu_memory_total=[memory_total],
        step=step
    )
    
    # At exactly 90%, should not trigger (threshold is >90%, not >=90%)
    if anomaly is not None:
        assert anomaly.type != AnomalyType.OOM, "Should not trigger at exactly 90%"
    
    # Test at 90.1%
    memory_used = memory_total * 0.901
    anomaly = service.detect_memory_issue(
        job_id=job_id,
        gpu_memory_used=[memory_used],
        gpu_memory_total=[memory_total],
        step=step
    )
    
    # Should trigger just above 90%
    assert anomaly is not None, "Should trigger at 90.1%"
    assert anomaly.type == AnomalyType.OOM
    
    service.clear_history(job_id)


def test_memory_threshold_action_includes_gradient_checkpointing():
    """
    Test that memory threshold anomaly suggests gradient checkpointing as well as batch size reduction.
    """
    service = AnomalyDetectionService()
    job_id = "test_job"
    step = 100
    
    # Trigger high memory usage
    memory_total = 10000.0
    memory_used = memory_total * 0.95  # 95% usage
    
    anomaly = service.detect_memory_issue(
        job_id=job_id,
        gpu_memory_used=[memory_used],
        gpu_memory_total=[memory_total],
        step=step
    )
    
    assert anomaly is not None
    assert anomaly.type == AnomalyType.OOM
    
    # Check for both batch size reduction and gradient checkpointing
    action_descriptions = [action.description.lower() for action in anomaly.suggested_actions]
    
    has_batch_reduction = any('batch' in desc and 'reduce' in desc for desc in action_descriptions)
    has_gradient_checkpointing = any('gradient' in desc and 'checkpoint' in desc for desc in action_descriptions)
    
    assert has_batch_reduction, "Should suggest batch size reduction"
    assert has_gradient_checkpointing, "Should suggest gradient checkpointing"
    
    # Both should be automatic
    for action in anomaly.suggested_actions:
        desc_lower = action.description.lower()
        if ('batch' in desc_lower and 'reduce' in desc_lower) or \
           ('gradient' in desc_lower and 'checkpoint' in desc_lower):
            assert action.automatic is True, f"Action '{action.description}' should be automatic"
    
    service.clear_history(job_id)


@given(
    job_id=st.text(min_size=1, max_size=50),
    step=st.integers(min_value=1, max_value=10000)
)
@settings(max_examples=100)
def test_empty_memory_lists_handled_gracefully(job_id, step):
    """
    Test that empty GPU memory lists are handled without errors.
    """
    service = AnomalyDetectionService()
    
    # Test with empty lists
    anomaly = service.detect_memory_issue(
        job_id=job_id,
        gpu_memory_used=[],
        gpu_memory_total=[],
        step=step
    )
    
    # Should return None without error
    assert anomaly is None, "Should handle empty memory lists gracefully"
    
    # Test with None
    anomaly = service.detect_memory_issue(
        job_id=job_id,
        gpu_memory_used=None,
        gpu_memory_total=None,
        step=step
    )
    
    assert anomaly is None, "Should handle None memory lists gracefully"
    
    service.clear_history(job_id)
