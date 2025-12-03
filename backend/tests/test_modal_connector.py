"""
Tests for Modal connector.

Tests cover:
- Connection and authentication
- Function deployment with cold-start optimization
- Inference invocation
- Usage tracking
- Container caching
- Error handling
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from plugins.connectors.modal_connector import ModalConnector
from connectors.base import ResourceType


@pytest.fixture
def connector():
    """Create a Modal connector instance."""
    return ModalConnector()


@pytest.fixture
def mock_session():
    """Create a mock aiohttp session."""
    session = MagicMock()
    
    # Create async context manager mocks
    def create_response_mock(status=200, json_data=None):
        mock_response = AsyncMock()
        mock_response.status = status
        mock_response.json = AsyncMock(return_value=json_data or {})
        mock_response.text = AsyncMock(return_value="")
        mock_response.headers = {}
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        return mock_response
    
    session.get = MagicMock(return_value=create_response_mock())
    session.post = MagicMock(return_value=create_response_mock())
    session.delete = MagicMock(return_value=create_response_mock())
    session.close = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_connect_success(connector, mock_session):
    """Test successful connection to Modal."""
    # Mock successful workspace response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"id": "workspace-123"})
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        mock_session.get = MagicMock(return_value=mock_response)
        
        result = await connector.connect({
            "token_id": "test-token-id",
            "token_secret": "test-token-secret"
        })
        
        assert result is True
        assert connector._connected is True
        assert connector._token_id == "test-token-id"
        assert connector._token_secret == "test-token-secret"


@pytest.mark.asyncio
async def test_connect_invalid_credentials(connector, mock_session):
    """Test connection with invalid credentials."""
    # Mock 401 response
    mock_response = AsyncMock()
    mock_response.status = 401
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        mock_session.get = MagicMock(return_value=mock_response)
        
        with pytest.raises(ValueError, match="Invalid credentials"):
            await connector.connect({
                "token_id": "invalid",
                "token_secret": "invalid"
            })


@pytest.mark.asyncio
async def test_connect_missing_credentials(connector):
    """Test connection with missing credentials."""
    with pytest.raises(ValueError, match="token_id and token_secret are required"):
        await connector.connect({"token_id": "test"})
    
    with pytest.raises(ValueError, match="token_id and token_secret are required"):
        await connector.connect({"token_secret": "test"})


@pytest.mark.asyncio
async def test_disconnect(connector, mock_session):
    """Test disconnection and cleanup."""
    connector._session = mock_session
    connector._connected = True
    connector._token_id = "test"
    connector._token_secret = "test"
    connector._functions = {"func1": {}}
    connector._container_cache = {"cache1": "image1"}
    
    result = await connector.disconnect()
    
    assert result is True
    assert connector._connected is False
    assert connector._token_id is None
    assert connector._token_secret is None
    assert len(connector._functions) == 0
    assert len(connector._container_cache) == 0
    mock_session.close.assert_called_once()


@pytest.mark.asyncio
async def test_verify_connection(connector, mock_session):
    """Test connection verification."""
    connector._session = mock_session
    connector._connected = True
    
    # Mock successful verification
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = MagicMock(return_value=mock_response)
    
    result = await connector.verify_connection()
    assert result is True
    
    # Mock failed verification
    mock_response.status = 401
    result = await connector.verify_connection()
    assert result is False


def test_generate_container_id(connector):
    """Test container ID generation for caching."""
    # Same inputs should produce same ID
    id1 = connector._generate_container_id(
        "meta-llama/Llama-2-7b-hf",
        ["torch", "transformers"]
    )
    id2 = connector._generate_container_id(
        "meta-llama/Llama-2-7b-hf",
        ["torch", "transformers"]
    )
    assert id1 == id2
    
    # Different order of dependencies should produce same ID (sorted)
    id3 = connector._generate_container_id(
        "meta-llama/Llama-2-7b-hf",
        ["transformers", "torch"]
    )
    assert id1 == id3
    
    # Different model should produce different ID
    id4 = connector._generate_container_id(
        "meta-llama/Llama-2-13b-hf",
        ["torch", "transformers"]
    )
    assert id1 != id4
    
    # Different dependencies should produce different ID
    id5 = connector._generate_container_id(
        "meta-llama/Llama-2-7b-hf",
        ["torch", "transformers", "bitsandbytes"]
    )
    assert id1 != id5


@pytest.mark.asyncio
async def test_deploy_function(connector, mock_session):
    """Test function deployment."""
    connector._session = mock_session
    connector._connected = True
    
    # Mock successful deployment
    mock_response = AsyncMock()
    mock_response.status = 201
    mock_response.json = AsyncMock(return_value={
        "id": "func-123",
        "url": "https://test.modal.run/func-123",
        "image_id": "img-456"
    })
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    mock_session.post = MagicMock(return_value=mock_response)
    
    function_id = await connector.deploy_function(
        function_name="test-function",
        base_model="meta-llama/Llama-2-7b-hf",
        deployment_config={
            "gpu_type": "A10G",
            "keep_warm": 2,
        }
    )
    
    assert function_id == "func-123"
    assert function_id in connector._functions
    assert connector._functions[function_id]["name"] == "test-function"
    assert connector._functions[function_id]["base_model"] == "meta-llama/Llama-2-7b-hf"
    
    # Check that container image was cached
    container_id = connector._functions[function_id]["container_id"]
    assert container_id in connector._container_cache
    assert connector._container_cache[container_id] == "img-456"


@pytest.mark.asyncio
async def test_deploy_function_with_adapter(connector, mock_session, tmp_path):
    """Test function deployment with adapter."""
    connector._session = mock_session
    connector._connected = True
    
    # Create temporary adapter files
    adapter_dir = tmp_path / "adapter"
    adapter_dir.mkdir()
    (adapter_dir / "adapter_model.safetensors").write_text("fake adapter")
    (adapter_dir / "adapter_config.json").write_text("{}")
    
    # Mock successful deployment
    mock_response = AsyncMock()
    mock_response.status = 201
    mock_response.json = AsyncMock(return_value={
        "id": "func-456",
        "url": "https://test.modal.run/func-456",
        "image_id": "img-789"
    })
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    mock_session.post = MagicMock(return_value=mock_response)
    
    function_id = await connector.deploy_function(
        function_name="adapter-function",
        base_model="meta-llama/Llama-2-7b-hf",
        adapter_path=str(adapter_dir),
    )
    
    assert function_id == "func-456"
    assert connector._functions[function_id]["adapter_path"] == str(adapter_dir)


@pytest.mark.asyncio
async def test_deploy_function_not_connected(connector):
    """Test function deployment when not connected."""
    with pytest.raises(RuntimeError, match="Not connected to Modal"):
        await connector.deploy_function(
            function_name="test",
            base_model="test-model"
        )


@pytest.mark.asyncio
async def test_get_function_status(connector, mock_session):
    """Test getting function status."""
    connector._session = mock_session
    connector._connected = True
    connector._functions["func-123"] = {"id": "func-123"}
    
    # Mock successful status response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "status": "ready",
        "url": "https://test.modal.run/func-123"
    })
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = MagicMock(return_value=mock_response)
    
    status = await connector.get_function_status("func-123")
    
    assert status == "ready"
    assert connector._functions["func-123"]["status"] == "ready"
    assert connector._functions["func-123"]["url"] == "https://test.modal.run/func-123"


@pytest.mark.asyncio
async def test_list_functions(connector, mock_session):
    """Test listing functions."""
    connector._session = mock_session
    connector._connected = True
    
    # Mock successful list response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "functions": [
            {"id": "func-1", "name": "function-1"},
            {"id": "func-2", "name": "function-2"},
        ]
    })
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = MagicMock(return_value=mock_response)
    
    functions = await connector.list_functions()
    
    assert len(functions) == 2
    assert functions[0]["id"] == "func-1"
    assert functions[1]["id"] == "func-2"
    # Check cache was updated
    assert "func-1" in connector._functions
    assert "func-2" in connector._functions


@pytest.mark.asyncio
async def test_delete_function(connector, mock_session):
    """Test deleting a function."""
    connector._session = mock_session
    connector._connected = True
    connector._functions["func-123"] = {"id": "func-123"}
    
    # Mock successful deletion
    mock_response = AsyncMock()
    mock_response.status = 204
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    mock_session.delete = MagicMock(return_value=mock_response)
    
    result = await connector.delete_function("func-123")
    
    assert result is True
    assert "func-123" not in connector._functions


@pytest.mark.asyncio
async def test_invoke_function(connector, mock_session):
    """Test function invocation."""
    connector._session = mock_session
    connector._connected = True
    connector._functions["func-123"] = {
        "id": "func-123",
        "url": "https://test.modal.run/func-123"
    }
    
    # Mock successful invocation
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "text": "Paris is the capital of France.",
        "prompt_tokens": 10,
        "completion_tokens": 8,
    })
    mock_response.headers = {"X-Modal-Cold-Start": "false"}
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    mock_session.post = MagicMock(return_value=mock_response)
    
    result = await connector.invoke_function(
        function_id="func-123",
        prompt="What is the capital of France?",
        generation_config={"max_tokens": 256}
    )
    
    assert result["text"] == "Paris is the capital of France."
    assert result["tokens"]["prompt"] == 10
    assert result["tokens"]["completion"] == 8
    assert result["tokens"]["total"] == 18
    assert result["cold_start"] is False
    assert result["latency_ms"] > 0


@pytest.mark.asyncio
async def test_invoke_function_cold_start(connector, mock_session):
    """Test function invocation with cold start."""
    connector._session = mock_session
    connector._connected = True
    connector._functions["func-123"] = {
        "id": "func-123",
        "url": "https://test.modal.run/func-123"
    }
    
    # Mock invocation with cold start
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "text": "Response",
        "prompt_tokens": 5,
        "completion_tokens": 3,
    })
    mock_response.headers = {"X-Modal-Cold-Start": "true"}
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    mock_session.post = MagicMock(return_value=mock_response)
    
    result = await connector.invoke_function(
        function_id="func-123",
        prompt="Test"
    )
    
    assert result["cold_start"] is True


@pytest.mark.asyncio
async def test_get_usage_stats(connector, mock_session):
    """Test getting usage statistics."""
    connector._session = mock_session
    connector._connected = True
    
    # Mock successful usage response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "total_invocations": 1000,
        "total_compute_seconds": 500,
        "cold_starts": 50,
        "warm_starts": 950,
        "avg_cold_start_ms": 2000,
        "avg_warm_start_ms": 50,
        "total_cost_usd": 25.50,
        "functions": [],
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
    })
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = MagicMock(return_value=mock_response)
    
    stats = await connector.get_usage_stats()
    
    assert stats["total_invocations"] == 1000
    assert stats["cold_starts"] == 50
    assert stats["warm_starts"] == 950
    assert stats["avg_cold_start_ms"] == 2000
    assert stats["avg_warm_start_ms"] == 50
    assert stats["total_cost_usd"] == 25.50


@pytest.mark.asyncio
async def test_get_cold_start_metrics(connector, mock_session):
    """Test getting cold-start metrics."""
    connector._session = mock_session
    connector._connected = True
    
    # Mock successful metrics response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "container_cache_hit_rate": 0.85,
        "avg_cold_start_ms": 1800,
        "avg_warm_start_ms": 45,
        "p50_cold_start_ms": 1500,
        "p95_cold_start_ms": 2500,
        "p99_cold_start_ms": 3000,
        "warm_containers": 2,
        "total_containers": 5,
    })
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = MagicMock(return_value=mock_response)
    
    metrics = await connector.get_cold_start_metrics("func-123")
    
    assert metrics["container_cache_hit_rate"] == 0.85
    assert metrics["avg_cold_start_ms"] == 1800
    assert metrics["avg_warm_start_ms"] == 45
    assert metrics["p95_cold_start_ms"] == 2500
    assert metrics["warm_containers"] == 2


@pytest.mark.asyncio
async def test_list_resources(connector):
    """Test listing available resources."""
    connector._connected = True
    
    resources = await connector.list_resources()
    
    assert len(resources) == 3
    assert any(r.id == "modal-a10g" for r in resources)
    assert any(r.id == "modal-a100" for r in resources)
    assert any(r.id == "modal-t4" for r in resources)
    
    # Check A10G details
    a10g = next(r for r in resources if r.id == "modal-a10g")
    assert a10g.gpu_type == "A10G"
    assert a10g.vram_gb == 24
    assert a10g.type == ResourceType.GPU


@pytest.mark.asyncio
async def test_get_pricing(connector):
    """Test getting pricing information."""
    connector._connected = True
    
    # Test A10G pricing
    pricing = await connector.get_pricing("modal-a10g")
    assert pricing.resource_id == "modal-a10g"
    assert pricing.price_per_hour == 1.10
    assert pricing.currency == "USD"
    assert pricing.billing_increment_seconds == 1
    
    # Test A100 pricing
    pricing = await connector.get_pricing("modal-a100")
    assert pricing.price_per_hour == 4.00
    
    # Test invalid resource
    with pytest.raises(ValueError, match="Invalid resource ID"):
        await connector.get_pricing("invalid-resource")


def test_get_required_credentials(connector):
    """Test getting required credentials."""
    creds = connector.get_required_credentials()
    assert "token_id" in creds
    assert "token_secret" in creds
    assert len(creds) == 2


def test_connector_metadata(connector):
    """Test connector metadata."""
    assert connector.name == "modal"
    assert connector.display_name == "Modal"
    assert connector.supports_inference is True
    assert connector.supports_training is False
    assert connector.supports_registry is False


@pytest.mark.asyncio
async def test_not_implemented_methods(connector):
    """Test that training-related methods raise NotImplementedError."""
    from connectors.base import TrainingConfig
    
    config = TrainingConfig(
        base_model="test",
        model_source="huggingface",
        algorithm="lora",
        rank=8,
        alpha=16,
        dropout=0.1,
        target_modules=["q_proj", "v_proj"]
    )
    
    with pytest.raises(NotImplementedError):
        await connector.submit_job(config)
    
    with pytest.raises(NotImplementedError):
        await connector.get_job_status("job-123")
    
    with pytest.raises(NotImplementedError):
        await connector.cancel_job("job-123")
    
    with pytest.raises(NotImplementedError):
        await connector.fetch_artifact("job-123")
    
    with pytest.raises(NotImplementedError):
        await connector.upload_artifact("/path", {})
    
    # stream_logs should be a generator
    gen = connector.stream_logs("job-123")
    with pytest.raises(NotImplementedError):
        await gen.__anext__()


def test_generate_inference_code(connector):
    """Test inference code generation."""
    code = connector._generate_inference_code(
        base_model="meta-llama/Llama-2-7b-hf",
        adapter_path="/path/to/adapter"
    )
    
    # Check that code contains expected elements
    assert "meta-llama/Llama-2-7b-hf" in code
    assert "/path/to/adapter" in code
    assert "def load_model()" in code
    assert "def generate(" in code
    assert "AutoModelForCausalLM" in code
    assert "AutoTokenizer" in code
    assert "PeftModel" in code
    assert "@method()" in code


@pytest.mark.asyncio
async def test_container_caching_workflow(connector, mock_session):
    """Test complete container caching workflow."""
    connector._session = mock_session
    connector._connected = True
    
    # First deployment - no cache
    mock_response = AsyncMock()
    mock_response.status = 201
    mock_response.json = AsyncMock(return_value={
        "id": "func-1",
        "url": "https://test.modal.run/func-1",
        "image_id": "img-abc"
    })
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    mock_session.post = MagicMock(return_value=mock_response)
    
    function_id_1 = await connector.deploy_function(
        function_name="function-1",
        base_model="meta-llama/Llama-2-7b-hf",
    )
    
    # Check container was cached
    container_id = connector._functions[function_id_1]["container_id"]
    assert container_id in connector._container_cache
    assert connector._container_cache[container_id] == "img-abc"
    
    # Second deployment with same model - should use cache
    mock_response.json = AsyncMock(return_value={
        "id": "func-2",
        "url": "https://test.modal.run/func-2",
        "image_id": "img-abc"  # Same image
    })
    
    function_id_2 = await connector.deploy_function(
        function_name="function-2",
        base_model="meta-llama/Llama-2-7b-hf",  # Same model
    )
    
    # Both functions should have same container ID
    container_id_2 = connector._functions[function_id_2]["container_id"]
    assert container_id == container_id_2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
