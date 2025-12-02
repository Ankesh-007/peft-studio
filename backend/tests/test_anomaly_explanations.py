"""
Property-based tests for anomaly detection explanations and actions.

**Feature: simplified-llm-optimization, Property 11: Anomaly detection provides explanations and actions**
**Validates: Requirements 5.4, 6.1, 6.2, 6.4**
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from services.anomaly_detection_service import (
    AnomalyDetectionService,
    AnomalyType,
    get_anomaly_detection_service
)


# Strategy for generating valid anomaly types
anomaly_types = st.sampled_from([
    AnomalyType.LOSS_DIVERGENCE,
    AnomalyType.GRADIENT_EXPLOSION,
    AnomalyType.OVERFITTING,
    AnomalyType.OOM,
    AnomalyType.MEMORY_LEAK
])


@given(
    anomaly_type=anomaly_types,
    job_id=st.text(min_size=1, max_size=50),
    step=st.integers(min_value=1, max_value=10000)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_anomaly_detection_provides_explanations_and_actions(anomaly_type, job_id, step):
    """
    **Feature: simplified-llm-optimization, Property 11: Anomaly detection provides explanations and actions**
    
    For any detected anomaly, the response should include:
    - A non-empty explanation message
    - Between 2 and 3 suggested actions
    - Each action should have a description
    """
    service = AnomalyDetectionService()
    
    # Create conditions that trigger each anomaly type
    anomaly = None
    
    if anomaly_type == AnomalyType.LOSS_DIVERGENCE:
        # Simulate diverging loss
        for i in range(5):
            service.loss_history[job_id] = service.loss_history.get(job_id, [])
            service.loss_history[job_id].append(0.5 + i * 0.1)
        
        # Trigger divergence with a large loss
        anomaly = service.detect_loss_divergence(job_id, 5.0, step)
    
    elif anomaly_type == AnomalyType.GRADIENT_EXPLOSION:
        # Simulate gradient explosion
        anomaly = service.detect_gradient_explosion(job_id, 15.0, step)
    
    elif anomaly_type == AnomalyType.OVERFITTING:
        # Simulate overfitting pattern
        for i in range(3):
            service.train_loss_history[job_id] = service.train_loss_history.get(job_id, [])
            service.val_loss_history[job_id] = service.val_loss_history.get(job_id, [])
            service.train_loss_history[job_id].append(1.0 - i * 0.1)
            service.val_loss_history[job_id].append(1.5 + i * 0.1)
        
        anomaly = service.detect_overfitting(job_id, 0.7, 1.8, step)
    
    elif anomaly_type == AnomalyType.OOM:
        # Simulate high memory usage
        gpu_memory_used = [9500.0]  # 9.5GB used
        gpu_memory_total = [10000.0]  # 10GB total (95% usage)
        anomaly = service.detect_memory_issue(job_id, gpu_memory_used, gpu_memory_total, step)
    
    elif anomaly_type == AnomalyType.MEMORY_LEAK:
        # Simulate memory leak pattern
        service.memory_history[job_id] = []
        for i in range(10):
            service.memory_history[job_id].append(0.5 + i * 0.03)
        
        # Check with high memory to trigger leak detection
        gpu_memory_used = [8000.0]
        gpu_memory_total = [10000.0]
        anomaly = service.detect_memory_issue(job_id, gpu_memory_used, gpu_memory_total, step)
    
    # Verify anomaly was detected
    assert anomaly is not None, f"Failed to detect {anomaly_type.value} anomaly"
    
    # Property 11: Anomaly must have explanation
    assert anomaly.message is not None, "Anomaly message should not be None"
    assert len(anomaly.message) > 0, "Anomaly message should not be empty"
    assert isinstance(anomaly.message, str), "Anomaly message should be a string"
    
    # Property 11: Anomaly must have 2-3 suggested actions
    assert anomaly.suggested_actions is not None, "Suggested actions should not be None"
    assert len(anomaly.suggested_actions) >= 2, f"Should have at least 2 actions, got {len(anomaly.suggested_actions)}"
    assert len(anomaly.suggested_actions) <= 3, f"Should have at most 3 actions, got {len(anomaly.suggested_actions)}"
    
    # Property 11: Each action must have a description
    for action in anomaly.suggested_actions:
        assert action.description is not None, "Action description should not be None"
        assert len(action.description) > 0, "Action description should not be empty"
        assert isinstance(action.description, str), "Action description should be a string"
        assert isinstance(action.automatic, bool), "Action automatic flag should be boolean"
    
    # Clean up
    service.clear_history(job_id)


@given(
    job_id=st.text(min_size=1, max_size=50),
    step=st.integers(min_value=1, max_value=10000),
    loss=st.floats(min_value=0.01, max_value=100.0, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=100)
def test_loss_divergence_detection_provides_complete_response(job_id, step, loss):
    """
    Test that loss divergence detection always provides complete anomaly information.
    """
    service = AnomalyDetectionService()
    
    # Build up loss history to trigger divergence
    service.loss_history[job_id] = [0.5, 0.6, 0.7, 0.8, 0.9]
    
    # Try to detect with a potentially diverging loss
    anomaly = service.detect_loss_divergence(job_id, loss * 3, step)
    
    # If anomaly detected, verify completeness
    if anomaly is not None:
        assert anomaly.type == AnomalyType.LOSS_DIVERGENCE
        assert len(anomaly.message) > 0
        assert 2 <= len(anomaly.suggested_actions) <= 3
        assert anomaly.severity is not None
        assert anomaly.detected_at is not None
        assert 'step' in anomaly.detected_at
        assert isinstance(anomaly.auto_recoverable, bool)
    
    service.clear_history(job_id)


@given(
    job_id=st.text(min_size=1, max_size=50),
    step=st.integers(min_value=1, max_value=10000),
    grad_norm=st.floats(min_value=0.1, max_value=100.0, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=100)
def test_gradient_explosion_detection_provides_complete_response(job_id, step, grad_norm):
    """
    Test that gradient explosion detection always provides complete anomaly information.
    """
    service = AnomalyDetectionService()
    
    # Detect gradient explosion
    anomaly = service.detect_gradient_explosion(job_id, grad_norm, step)
    
    # If anomaly detected, verify completeness
    if anomaly is not None:
        assert anomaly.type == AnomalyType.GRADIENT_EXPLOSION
        assert len(anomaly.message) > 0
        assert 2 <= len(anomaly.suggested_actions) <= 3
        assert anomaly.severity is not None
        assert anomaly.detected_at is not None
        assert 'step' in anomaly.detected_at
        assert isinstance(anomaly.auto_recoverable, bool)
    
    service.clear_history(job_id)


@given(
    job_id=st.text(min_size=1, max_size=50),
    step=st.integers(min_value=1, max_value=10000),
    train_loss=st.floats(min_value=0.01, max_value=5.0, allow_nan=False, allow_infinity=False),
    val_loss=st.floats(min_value=0.01, max_value=5.0, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=100)
def test_overfitting_detection_provides_complete_response(job_id, step, train_loss, val_loss):
    """
    Test that overfitting detection always provides complete anomaly information.
    """
    service = AnomalyDetectionService()
    
    # Build up history to enable overfitting detection
    service.train_loss_history[job_id] = [train_loss + 0.3, train_loss + 0.2, train_loss + 0.1]
    service.val_loss_history[job_id] = [val_loss - 0.1, val_loss, val_loss + 0.1]
    
    # Detect overfitting
    anomaly = service.detect_overfitting(job_id, train_loss, val_loss, step)
    
    # If anomaly detected, verify completeness
    if anomaly is not None:
        assert anomaly.type == AnomalyType.OVERFITTING
        assert len(anomaly.message) > 0
        assert 2 <= len(anomaly.suggested_actions) <= 3
        assert anomaly.severity is not None
        assert anomaly.detected_at is not None
        assert 'step' in anomaly.detected_at
        assert isinstance(anomaly.auto_recoverable, bool)
    
    service.clear_history(job_id)


def test_nan_loss_triggers_critical_anomaly():
    """
    Test that NaN loss triggers a critical anomaly with proper explanation.
    """
    service = AnomalyDetectionService()
    job_id = "test_job"
    step = 100
    
    # Build up some history
    service.loss_history[job_id] = [0.5, 0.6, 0.7, 0.8, 0.9]
    
    # Trigger with NaN
    anomaly = service.detect_loss_divergence(job_id, float('nan'), step)
    
    assert anomaly is not None
    assert anomaly.type == AnomalyType.LOSS_DIVERGENCE
    assert anomaly.severity.value == "critical"
    assert len(anomaly.message) > 0
    assert "NaN" in anomaly.message or "nan" in anomaly.message.lower()
    assert 2 <= len(anomaly.suggested_actions) <= 3
    
    service.clear_history(job_id)


def test_check_all_anomalies_returns_complete_responses():
    """
    Test that check_all_anomalies returns complete anomaly information for all detected issues.
    """
    service = AnomalyDetectionService()
    job_id = "test_job"
    step = 100
    
    # Set up conditions to trigger multiple anomalies
    service.loss_history[job_id] = [0.5, 0.6, 0.7, 0.8, 0.9]
    
    anomalies = service.check_all_anomalies(
        job_id=job_id,
        step=step,
        loss=5.0,  # High loss to trigger divergence
        grad_norm=15.0,  # High gradient to trigger explosion
        val_loss=None,
        gpu_memory_used=[9500.0],
        gpu_memory_total=[10000.0]  # High memory usage
    )
    
    # Should detect at least loss divergence and memory issue
    assert len(anomalies) >= 1
    
    # Verify all detected anomalies are complete
    for anomaly in anomalies:
        assert anomaly.message is not None
        assert len(anomaly.message) > 0
        assert anomaly.suggested_actions is not None
        assert 2 <= len(anomaly.suggested_actions) <= 3
        for action in anomaly.suggested_actions:
            assert len(action.description) > 0
    
    service.clear_history(job_id)
