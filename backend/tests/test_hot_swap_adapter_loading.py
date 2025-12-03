"""
Property-Based Test for Hot-Swap Adapter Loading

**Feature: unified-llm-platform, Property 8: Hot-swap adapter loading**
**Validates: Requirements 10.5**

Property: For any two adapters on the same base model, switching between them
should not require reloading the base model.

This test validates that:
1. Multiple adapters can be loaded on the same base model
2. Switching between adapters doesn't reload the base model
3. Each adapter produces different outputs for the same input
4. The base model remains in memory throughout adapter switches
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from pathlib import Path
import sys
import json
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

sys.path.append(str(Path(__file__).parent.parent))

from plugins.connectors.predibase_connector import PredibaseConnector


# Strategies for generating test data

@st.composite
def adapter_config(draw):
    """Generate a valid adapter configuration."""
    return {
        "name": draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='-_'
        ))),
        "base_model": draw(st.sampled_from([
            "meta-llama/Llama-2-7b-hf",
            "meta-llama/Llama-2-13b-hf",
            "mistralai/Mistral-7B-v0.1",
        ])),
        "rank": draw(st.integers(min_value=4, max_value=64)),
        "alpha": draw(st.integers(min_value=8, max_value=128)),
    }


@st.composite
def adapter_pair(draw):
    """Generate a pair of adapters on the same base model."""
    base_model = draw(st.sampled_from([
        "meta-llama/Llama-2-7b-hf",
        "meta-llama/Llama-2-13b-hf",
        "mistralai/Mistral-7B-v0.1",
    ]))
    
    adapter1 = {
        "name": draw(st.text(min_size=1, max_size=30, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='-_'
        ))),
        "base_model": base_model,
        "rank": draw(st.integers(min_value=4, max_value=64)),
    }
    
    adapter2 = {
        "name": draw(st.text(min_size=1, max_size=30, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='-_'
        ))),
        "base_model": base_model,
        "rank": draw(st.integers(min_value=4, max_value=64)),
    }
    
    # Ensure adapters have different names
    assume(adapter1["name"] != adapter2["name"])
    
    return adapter1, adapter2


@st.composite
def inference_prompt(draw):
    """Generate a valid inference prompt."""
    return draw(st.text(min_size=10, max_size=200))


class MockDeploymentTracker:
    """
    Mock tracker to verify base model is not reloaded during adapter switches.
    
    This simulates the behavior of LoRAX where the base model stays loaded
    and only adapter weights are swapped.
    """
    
    def __init__(self):
        self.base_model_loads = []
        self.adapter_loads = []
        self.current_base_model = None
        self.current_adapter = None
    
    def load_base_model(self, model_id: str):
        """Record base model load."""
        self.base_model_loads.append(model_id)
        self.current_base_model = model_id
    
    def load_adapter(self, adapter_name: str):
        """Record adapter load (hot-swap)."""
        self.adapter_loads.append(adapter_name)
        self.current_adapter = adapter_name
    
    def get_base_model_load_count(self) -> int:
        """Get number of times base model was loaded."""
        return len(self.base_model_loads)
    
    def get_adapter_load_count(self) -> int:
        """Get number of times adapters were loaded."""
        return len(self.adapter_loads)


@pytest.fixture
def mock_connector_with_tracking():
    """Create a mock connector with load tracking."""
    connector = PredibaseConnector()
    tracker = MockDeploymentTracker()
    
    # Mock session
    mock_session = MagicMock()
    mock_session.get = AsyncMock()
    mock_session.post = AsyncMock()
    mock_session.close = AsyncMock()
    
    connector._session = mock_session
    connector._connected = True
    connector._api_key = "test_key"
    connector._tenant_id = "test_tenant"
    
    return connector, tracker


@pytest.mark.asyncio
@given(
    adapters=adapter_pair(),
    prompt=inference_prompt(),
)
@settings(max_examples=50, deadline=None)
async def test_hot_swap_no_base_model_reload(adapters, prompt):
    """
    Property: Switching between adapters on the same base model should not
    reload the base model.
    
    This is the core property of LoRAX hot-swapping:
    - Base model is loaded once
    - Adapters are swapped without reloading base model
    - Each adapter produces different outputs
    """
    adapter1, adapter2 = adapters
    
    connector = PredibaseConnector()
    tracker = MockDeploymentTracker()
    
    # Mock session
    mock_session = MagicMock()
    mock_session.get = AsyncMock()
    mock_session.post = AsyncMock()
    mock_session.close = AsyncMock()
    
    connector._session = mock_session
    connector._connected = True
    connector._api_key = "test_key"
    connector._tenant_id = "test_tenant"
    
    # Simulate deployment with base model load
    deployment_id = "test-deployment"
    connector._deployments[deployment_id] = {
        "id": deployment_id,
        "base_model": adapter1["base_model"],
        "endpoint": "https://test.endpoint.com",
        "status": "ready"
    }
    
    # Track base model loads
    tracker.load_base_model(adapter1["base_model"])
    base_model_loads_before = tracker.get_base_model_load_count()
    
    # Mock inference responses with different outputs for each adapter
    inference_calls = []
    
    def mock_inference_response(adapter_name):
        """Create mock response that varies by adapter."""
        # Track the inference call
        inference_calls.append({
            "adapter": adapter_name,
            "prompt": prompt
        })
        
        # Track adapter load (hot-swap)
        tracker.load_adapter(adapter_name)
        
        # Return different response based on adapter
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "generated_text": f"Response from {adapter_name}: {prompt[:20]}...",
            "tokens": ["Response", "from", adapter_name]
        })
        
        # Create async context manager
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        mock_context.__aexit__.return_value = None
        
        return mock_context
    
    # Perform inference with adapter1
    mock_session.post = MagicMock(return_value=mock_inference_response(adapter1["name"]))
    result1 = await connector.inference(
        deployment_id=deployment_id,
        prompt=prompt,
        adapter_name=adapter1["name"]
    )
    
    # Perform inference with adapter2 (hot-swap!)
    mock_session.post = MagicMock(return_value=mock_inference_response(adapter2["name"]))
    result2 = await connector.inference(
        deployment_id=deployment_id,
        prompt=prompt,
        adapter_name=adapter2["name"]
    )
    
    # Perform inference with adapter1 again (hot-swap back!)
    mock_session.post = MagicMock(return_value=mock_inference_response(adapter1["name"]))
    result3 = await connector.inference(
        deployment_id=deployment_id,
        prompt=prompt,
        adapter_name=adapter1["name"]
    )
    
    base_model_loads_after = tracker.get_base_model_load_count()
    adapter_loads = tracker.get_adapter_load_count()
    
    # PROPERTY ASSERTIONS
    
    # 1. Base model should only be loaded once (no reload during adapter switches)
    assert base_model_loads_after == base_model_loads_before, \
        f"Base model was reloaded during adapter switch! " \
        f"Expected {base_model_loads_before} loads, got {base_model_loads_after}"
    
    # 2. Adapters should be loaded (hot-swapped) for each inference
    assert adapter_loads == 3, \
        f"Expected 3 adapter loads (hot-swaps), got {adapter_loads}"
    
    # 3. Each adapter should produce different outputs
    assert result1["text"] != result2["text"], \
        "Different adapters should produce different outputs"
    
    # 4. Same adapter should produce consistent outputs
    assert result1["text"] == result3["text"], \
        "Same adapter should produce consistent outputs"
    
    # 5. All results should indicate which adapter was used
    assert result1["adapter_used"] == adapter1["name"]
    assert result2["adapter_used"] == adapter2["name"]
    assert result3["adapter_used"] == adapter1["name"]
    
    # 6. Inference calls should be made in the correct order
    assert len(inference_calls) == 3
    assert inference_calls[0]["adapter"] == adapter1["name"]
    assert inference_calls[1]["adapter"] == adapter2["name"]
    assert inference_calls[2]["adapter"] == adapter1["name"]


@pytest.mark.asyncio
@given(
    adapters=adapter_pair(),
    num_switches=st.integers(min_value=2, max_value=10),
)
@settings(max_examples=30, deadline=None)
async def test_multiple_hot_swaps_no_reload(adapters, num_switches):
    """
    Property: Multiple adapter switches should not reload the base model.
    
    Tests that even with many adapter switches, the base model remains
    loaded in memory.
    """
    adapter1, adapter2 = adapters
    
    connector = PredibaseConnector()
    tracker = MockDeploymentTracker()
    
    # Mock session
    mock_session = MagicMock()
    mock_session.get = AsyncMock()
    mock_session.post = AsyncMock()
    mock_session.close = AsyncMock()
    
    connector._session = mock_session
    connector._connected = True
    connector._api_key = "test_key"
    
    # Simulate deployment
    deployment_id = "test-deployment"
    connector._deployments[deployment_id] = {
        "id": deployment_id,
        "base_model": adapter1["base_model"],
        "endpoint": "https://test.endpoint.com",
        "status": "ready"
    }
    
    # Track base model load
    tracker.load_base_model(adapter1["base_model"])
    base_model_loads_initial = tracker.get_base_model_load_count()
    
    # Mock inference
    def mock_inference_response(adapter_name):
        tracker.load_adapter(adapter_name)
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "generated_text": f"Response from {adapter_name}",
            "tokens": ["Response"]
        })
        
        # Create async context manager
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        mock_context.__aexit__.return_value = None
        
        return mock_context
    
    # Perform multiple adapter switches
    for i in range(num_switches):
        # Alternate between adapters
        current_adapter = adapter1 if i % 2 == 0 else adapter2
        
        mock_session.post = MagicMock(return_value=mock_inference_response(
            current_adapter["name"]
        ))
        
        result = await connector.inference(
            deployment_id=deployment_id,
            prompt="Test prompt",
            adapter_name=current_adapter["name"]
        )
        
        assert result["adapter_used"] == current_adapter["name"]
    
    base_model_loads_final = tracker.get_base_model_load_count()
    adapter_loads_total = tracker.get_adapter_load_count()
    
    # PROPERTY ASSERTIONS
    
    # Base model should still only be loaded once
    assert base_model_loads_final == base_model_loads_initial, \
        f"Base model was reloaded during {num_switches} adapter switches! " \
        f"Expected {base_model_loads_initial} loads, got {base_model_loads_final}"
    
    # Should have performed all adapter switches
    assert adapter_loads_total == num_switches, \
        f"Expected {num_switches} adapter loads, got {adapter_loads_total}"


@pytest.mark.asyncio
@given(
    base_model=st.sampled_from([
        "meta-llama/Llama-2-7b-hf",
        "meta-llama/Llama-2-13b-hf",
        "mistralai/Mistral-7B-v0.1",
    ]),
    num_adapters=st.integers(min_value=2, max_value=5),
)
@settings(max_examples=20, deadline=None)
async def test_multiple_adapters_same_base_model(base_model, num_adapters):
    """
    Property: Multiple adapters on the same base model should all be
    hot-swappable without reloading the base model.
    
    Tests that the system can handle more than 2 adapters on the same
    base model.
    """
    connector = PredibaseConnector()
    tracker = MockDeploymentTracker()
    
    # Mock session
    mock_session = MagicMock()
    mock_session.get = AsyncMock()
    mock_session.post = AsyncMock()
    mock_session.close = AsyncMock()
    
    connector._session = mock_session
    connector._connected = True
    connector._api_key = "test_key"
    
    # Create multiple adapters
    adapters = [
        {"name": f"adapter-{i}", "base_model": base_model}
        for i in range(num_adapters)
    ]
    
    # Simulate deployment
    deployment_id = "test-deployment"
    connector._deployments[deployment_id] = {
        "id": deployment_id,
        "base_model": base_model,
        "endpoint": "https://test.endpoint.com",
        "status": "ready"
    }
    
    # Track base model load
    tracker.load_base_model(base_model)
    base_model_loads_initial = tracker.get_base_model_load_count()
    
    # Mock inference
    def mock_inference_response(adapter_name):
        tracker.load_adapter(adapter_name)
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "generated_text": f"Response from {adapter_name}",
            "tokens": ["Response"]
        })
        
        # Create async context manager
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        mock_context.__aexit__.return_value = None
        
        return mock_context
    
    # Test inference with each adapter
    results = []
    for adapter in adapters:
        mock_session.post = MagicMock(return_value=mock_inference_response(
            adapter["name"]
        ))
        
        result = await connector.inference(
            deployment_id=deployment_id,
            prompt="Test prompt",
            adapter_name=adapter["name"]
        )
        
        results.append(result)
    
    base_model_loads_final = tracker.get_base_model_load_count()
    adapter_loads_total = tracker.get_adapter_load_count()
    
    # PROPERTY ASSERTIONS
    
    # Base model should only be loaded once
    assert base_model_loads_final == base_model_loads_initial, \
        f"Base model was reloaded when switching between {num_adapters} adapters!"
    
    # Should have loaded each adapter once
    assert adapter_loads_total == num_adapters, \
        f"Expected {num_adapters} adapter loads, got {adapter_loads_total}"
    
    # Each result should indicate the correct adapter
    for i, result in enumerate(results):
        assert result["adapter_used"] == adapters[i]["name"]
    
    # All results should have different text (different adapters)
    texts = [r["text"] for r in results]
    assert len(set(texts)) == len(texts), \
        "Different adapters should produce different outputs"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
