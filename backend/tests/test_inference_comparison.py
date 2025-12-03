"""
Property-based tests for inference comparison functionality.
Tests that comparisons include both fine-tuned and base model outputs.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck

from services.inference_service import InferenceService


# Strategy for generating valid prompts
prompt_strategy = st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cs',)))

# Strategy for generating model IDs
model_id_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_',
    min_size=5,
    max_size=30
)


# **Feature: simplified-llm-optimization, Property 15: Inference comparison includes both outputs**
@settings(suppress_health_check=[HealthCheck.too_slow])
@given(
    prompt=prompt_strategy,
    fine_tuned_model_id=model_id_strategy,
    base_model_id=model_id_strategy
)
def test_inference_comparison_includes_both_outputs(
    prompt: str,
    fine_tuned_model_id: str,
    base_model_id: str
):
    """
    For any inference request, the comparison function should return
    both the fine-tuned model output and the base model output.
    
    Validates: Requirements 7.4
    """
    service = InferenceService()
    
    # Generate comparison
    result = service.compare_with_base_model(
        prompt=prompt,
        fine_tuned_model_id=fine_tuned_model_id,
        base_model_id=base_model_id
    )
    
    # Property 1: Result should have the original prompt
    assert hasattr(result, 'prompt'), "Result missing 'prompt' attribute"
    assert result.prompt == prompt, "Prompt in result doesn't match input"
    
    # Property 2: Result should have fine-tuned output
    assert hasattr(result, 'fine_tuned_output'), "Result missing 'fine_tuned_output' attribute"
    assert isinstance(result.fine_tuned_output, str), "fine_tuned_output is not a string"
    assert len(result.fine_tuned_output) > 0, "fine_tuned_output is empty"
    
    # Property 3: Result should have base model output
    assert hasattr(result, 'base_model_output'), "Result missing 'base_model_output' attribute"
    assert isinstance(result.base_model_output, str), "base_model_output is not a string"
    assert len(result.base_model_output) > 0, "base_model_output is empty"
    
    # Property 4: Result should have fine-tuned model ID
    assert hasattr(result, 'fine_tuned_model_id'), "Result missing 'fine_tuned_model_id' attribute"
    assert result.fine_tuned_model_id == fine_tuned_model_id, "fine_tuned_model_id doesn't match"
    
    # Property 5: Result should have base model ID
    assert hasattr(result, 'base_model_id'), "Result missing 'base_model_id' attribute"
    assert result.base_model_id == base_model_id, "base_model_id doesn't match"
    
    # Property 6: Result should have timestamp
    assert hasattr(result, 'timestamp'), "Result missing 'timestamp' attribute"
    assert result.timestamp is not None, "timestamp is None"
    
    # Property 7: Both outputs should be present (not None)
    assert result.fine_tuned_output is not None, "fine_tuned_output is None"
    assert result.base_model_output is not None, "base_model_output is None"


@given(
    prompt=prompt_strategy,
    model_id=model_id_strategy
)
def test_comparison_with_same_model_ids(prompt: str, model_id: str):
    """
    Test comparison when fine-tuned and base model IDs are the same.
    This is an edge case that should still work.
    """
    service = InferenceService()
    
    result = service.compare_with_base_model(
        prompt=prompt,
        fine_tuned_model_id=model_id,
        base_model_id=model_id
    )
    
    # Should still return both outputs even if model IDs are the same
    assert result.fine_tuned_output is not None
    assert result.base_model_output is not None
    assert result.fine_tuned_model_id == model_id
    assert result.base_model_id == model_id


def test_comparison_result_structure():
    """
    Test that comparison result has all required fields.
    """
    service = InferenceService()
    
    result = service.compare_with_base_model(
        prompt="Test prompt",
        fine_tuned_model_id="model-v1",
        base_model_id="base-model"
    )
    
    # Check all required attributes exist
    required_attrs = [
        'prompt',
        'fine_tuned_output',
        'base_model_output',
        'fine_tuned_model_id',
        'base_model_id',
        'timestamp'
    ]
    
    for attr in required_attrs:
        assert hasattr(result, attr), f"Result missing required attribute: {attr}"


def test_comparison_outputs_are_distinct():
    """
    Test that fine-tuned and base outputs are stored separately.
    """
    service = InferenceService()
    
    result = service.compare_with_base_model(
        prompt="Test prompt",
        fine_tuned_model_id="fine-tuned-v1",
        base_model_id="base-v1"
    )
    
    # Outputs should be distinct (not the same object reference)
    assert result.fine_tuned_output is not result.base_model_output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
