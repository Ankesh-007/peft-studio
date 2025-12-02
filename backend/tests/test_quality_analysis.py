"""
Property-based tests for training completion quality analysis.

**Feature: simplified-llm-optimization, Property 13: Training completion triggers quality analysis**
**Validates: Requirements 6.5**
"""

import pytest
from hypothesis import given, strategies as st
from services.quality_analysis_service import (
    analyze_training_quality,
    TrainingResult,
    QualityAnalysis
)


@given(
    final_loss=st.floats(min_value=0.01, max_value=10.0, allow_nan=False, allow_infinity=False),
    initial_loss=st.floats(min_value=0.1, max_value=20.0, allow_nan=False, allow_infinity=False),
    epochs_completed=st.integers(min_value=1, max_value=100),
    total_steps=st.integers(min_value=100, max_value=100000),
    best_val_loss=st.one_of(
        st.none(),
        st.floats(min_value=0.01, max_value=10.0, allow_nan=False, allow_infinity=False)
    ),
    convergence_achieved=st.booleans(),
    gradient_norm_stable=st.booleans()
)
def test_training_completion_triggers_quality_analysis(
    final_loss,
    initial_loss,
    epochs_completed,
    total_steps,
    best_val_loss,
    convergence_achieved,
    gradient_norm_stable
):
    """
    Property 13: Training completion triggers quality analysis
    
    For any completed training run, the system should generate a quality score
    and specific improvement suggestions.
    
    Validates: Requirements 6.5
    """
    # Ensure initial loss is greater than final loss for valid training
    if initial_loss <= final_loss:
        initial_loss = final_loss + 0.5
    
    # Create training result
    training_result = TrainingResult(
        final_loss=final_loss,
        initial_loss=initial_loss,
        epochs_completed=epochs_completed,
        total_steps=total_steps,
        best_val_loss=best_val_loss,
        convergence_achieved=convergence_achieved,
        gradient_norm_stable=gradient_norm_stable
    )
    
    # Analyze quality
    analysis = analyze_training_quality(training_result)
    
    # Property: Analysis should always be returned
    assert analysis is not None
    assert isinstance(analysis, QualityAnalysis)
    
    # Property: Quality score should be between 0 and 100
    assert 0 <= analysis.quality_score <= 100
    
    # Property: Should provide improvement suggestions (list, can be empty if perfect)
    assert isinstance(analysis.improvement_suggestions, list)
    
    # Property: If quality score is not perfect, should have suggestions
    if analysis.quality_score < 95:
        assert len(analysis.improvement_suggestions) > 0
    
    # Property: Each suggestion should have required fields
    for suggestion in analysis.improvement_suggestions:
        assert hasattr(suggestion, 'category')
        assert hasattr(suggestion, 'description')
        assert hasattr(suggestion, 'priority')
        assert suggestion.category in ['convergence', 'overfitting', 'underfitting', 'efficiency', 'stability']
        assert suggestion.priority in ['high', 'medium', 'low']
        assert len(suggestion.description) > 0
    
    # Property: Analysis should include metrics summary
    assert hasattr(analysis, 'metrics_summary')
    assert 'loss_reduction' in analysis.metrics_summary
    assert 'convergence_status' in analysis.metrics_summary


@given(
    st.lists(
        st.floats(min_value=0.01, max_value=10.0, allow_nan=False, allow_infinity=False),
        min_size=10,
        max_size=1000
    )
)
def test_quality_analysis_handles_loss_history(loss_history):
    """
    Test that quality analysis can process loss history for convergence detection.
    """
    training_result = TrainingResult(
        final_loss=loss_history[-1],
        initial_loss=loss_history[0],
        epochs_completed=len(loss_history) // 100 + 1,
        total_steps=len(loss_history),
        loss_history=loss_history,
        best_val_loss=None,
        convergence_achieved=False,
        gradient_norm_stable=True
    )
    
    analysis = analyze_training_quality(training_result)
    
    # Should analyze convergence from history
    assert 'convergence_status' in analysis.metrics_summary
    
    # If loss is decreasing consistently, should have good quality
    if all(loss_history[i] >= loss_history[i+1] for i in range(len(loss_history)-1)):
        assert analysis.quality_score >= 70


def test_quality_analysis_minimal_training():
    """
    Test quality analysis with minimal valid training result.
    """
    training_result = TrainingResult(
        final_loss=0.5,
        initial_loss=2.0,
        epochs_completed=1,
        total_steps=100,
        best_val_loss=None,
        convergence_achieved=False,
        gradient_norm_stable=True
    )
    
    analysis = analyze_training_quality(training_result)
    
    assert analysis is not None
    assert 0 <= analysis.quality_score <= 100
    assert isinstance(analysis.improvement_suggestions, list)
