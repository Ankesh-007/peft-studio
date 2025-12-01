"""
Tests for Together AI connector.

Tests cover:
- Connection and authentication
- Endpoint creation and management
- Adapter deployment
- Inference with pay-per-token pricing
- Streaming inference
- Usage monitoring
- Model management
"""

import pytest
import asyncio
from pathlib import Path
import sys
import json
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp

sys.path.append(str(Path(__file__).parent.parent))

from plugins.connectors.together_ai_connector import TogetherAIConnector
from connectors.base import TrainingConfig


@pytest.fixture
def connector():
    """Create a Together AI connector instance."""
    return TogetherAIConnector()


@pytest.fixture
def mock_session():
    """Create a mock aiohttp session."""
    session = MagicMock()
    return session


@pytest.mark.asyncio
async def test_connect_success(connector):
    """Test successful connection to Together AI."""
    with patch('aiohttp.ClientSession') as mock_session_class:
        mock_session = AsyncMock()
        mock_session_class.return_value = mock_session
        
        # Mock successful auth response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"id": "user123", "email": "test@example.com"})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        mock_session.get.return_value = mock_response
        
        result = await connector.connect({"api_key": "test_key"})
        
        assert result is True
        assert connector._connected is True
        assert connector._api_key == "test_key"


@pytest.mark.asyncio
async def test_connect_invalid_credentials(connector):
    """Test connection with invalid credentials."""
    with patch('aiohttp.ClientSession') as mock_session_class:
        mock_session = AsyncMock()
        mock_session_class.return_value = mock_session
        
        # Mock 401 response
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        mock_session.get.return_value = mock_response
        
        with pytest.raises(ValueError, match="Invalid API key"):
            await connector.connect({"api_key": "invalid_key"})


@pytest.mark.asyncio
async def test_connect_missing_api_key(connector):
    """Test connection without API key."""
    with pytest.raises(ValueError, match="api_key is required"):
        await connector.connect({})


@pytest.mark.asyncio
async def test_disconnect(connector):
    """Test disconnection."""
    connector._connected = True
    connector._session = AsyncMock()
    connector._api_key = "test_key"
    
    result = await connector.disconnect()
    
    assert result is True
    assert connector._connected is False
    assert connector._api_key is None
    assert connector._session is None


@pytest.mark.asyncio
async def test_verify_connection_success(connector):
    """Test connection verification when connected."""
    connector._connected = True
    connector._session = AsyncMock()
    
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    connector._session.get.return_value = mock_response
    
    result = await connector.verify_connection()
    
    assert result is True


@pytest.mark.asyncio
async def test_verify_connection_not_connected(connector):
    """Test connection verification when not connected."""
    result = await connector.verify_connection()
    assert result is False


@pytest.mark.asyncio
async def test_create_endpoint(connector):
    """Test creating a serverless endpoint."""
    connector._connected = True
    connector._session = AsyncMock()
    
    mock_response = AsyncMock()
    mock_response.status = 201
    mock_response.json = AsyncMock(return_value={
        "id": "endpoint123",
        "url": "https://api.together.xyz/v1/endpoints/endpoint123"
    })
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    connector._session.post.return_value = mock_response
    
    endpoint_id = await connector.create_endpoint(
        model_name="meta-llama/Llama-2-7b-hf",
        endpoint_name="test-endpoint",
        endpoint_config={"max_tokens": 2048}
    )
    
    assert endpoint_id == "endpoint123"
    assert "endpoint123" in connector._endpoints
    assert connector._endpoints["endpoint123"]["name"] == "test-endpoint"


@pytest.mark.asyncio
async def test_create_endpoint_not_connected(connector):
    """Test creating endpoint when not connected."""
    with pytest.raises(RuntimeError, match="Not connected"):
        await connector.create_endpoint(
            model_name="meta-llama/Llama-2-7b-hf",
            endpoint_name="test-endpoint"
        )


@pytest.mark.asyncio
async def test_get_endpoint_status(connector):
    """Test getting endpoint status."""
    connector._connected = True
    connector._session = AsyncMock()
    
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "status": "ready",
        "url": "https://api.together.xyz/v1/endpoints/endpoint123"
    })
    connector._session.get = AsyncMock(return_value=mock_response)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    status = await connector.get_endpoint_status("endpoint123")
    
    assert status == "ready"


@pytest.mark.asyncio
async def test_list_endpoints(connector):
    """Test listing all endpoints."""
    connector._connected = True
    connector._session = AsyncMock()
    
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "endpoints": [
            {"id": "endpoint1", "name": "test1", "status": "ready"},
            {"id": "endpoint2", "name": "test2", "status": "creating"}
        ]
    })
    connector._session.get = AsyncMock(return_value=mock_response)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    endpoints = await connector.list_endpoints()
    
    assert len(endpoints) == 2
    assert endpoints[0]["id"] == "endpoint1"
    assert endpoints[1]["id"] == "endpoint2"


@pytest.mark.asyncio
async def test_delete_endpoint(connector):
    """Test deleting an endpoint."""
    connector._connected = True
    connector._session = AsyncMock()
    connector._endpoints["endpoint123"] = {"id": "endpoint123"}
    
    mock_response = AsyncMock()
    mock_response.status = 204
    connector._session.delete = AsyncMock(return_value=mock_response)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    result = await connector.delete_endpoint("endpoint123")
    
    assert result is True
    assert "endpoint123" not in connector._endpoints


@pytest.mark.asyncio
async def test_inference_pay_per_token(connector):
    """Test inference with pay-per-token pricing."""
    connector._connected = True
    connector._session = AsyncMock()
    
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "choices": [{"text": "Paris is the capital of France."}],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 8,
            "total_tokens": 18
        }
    })
    connector._session.post = AsyncMock(return_value=mock_response)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    result = await connector.inference(
        model="meta-llama/Llama-2-7b-hf",
        prompt="What is the capital of France?",
        generation_config={"max_tokens": 100}
    )
    
    assert result["text"] == "Paris is the capital of France."
    assert result["tokens"]["total"] == 18
    assert result["tokens"]["prompt"] == 10
    assert result["tokens"]["completion"] == 8
    assert "cost_usd" in result
    assert result["cost_usd"] > 0
    assert "latency_ms" in result


@pytest.mark.asyncio
async def test_inference_streaming(connector):
    """Test streaming inference."""
    connector._connected = True
    connector._session = AsyncMock()
    
    # Mock streaming response
    mock_response = AsyncMock()
    mock_response.status = 200
    
    # Simulate streaming chunks
    chunks = [
        b'data: {"choices": [{"text": "Paris", "finish_reason": null}]}\n',
        b'data: {"choices": [{"text": " is", "finish_reason": null}]}\n',
        b'data: {"choices": [{"text": " the", "finish_reason": null}]}\n',
        b'data: {"choices": [{"text": " capital", "finish_reason": "stop"}]}\n',
        b'data: [DONE]\n'
    ]
    
    async def mock_content_iter():
        for chunk in chunks:
            yield chunk
    
    mock_response.content = mock_content_iter()
    connector._session.post = AsyncMock(return_value=mock_response)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    collected_text = []
    async for chunk in connector.inference_streaming(
        model="meta-llama/Llama-2-7b-hf",
        prompt="What is the capital of France?"
    ):
        collected_text.append(chunk["text"])
        if chunk["finish_reason"]:
            break
    
    assert len(collected_text) == 4
    assert collected_text[0] == "Paris"
    assert collected_text[-1] == " capital"


@pytest.mark.asyncio
async def test_get_usage_stats(connector):
    """Test getting usage statistics."""
    connector._connected = True
    connector._session = AsyncMock()
    
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "total_requests": 150,
        "total_tokens": 50000,
        "prompt_tokens": 20000,
        "completion_tokens": 30000,
        "total_cost_usd": 10.50,
        "start_date": "2024-01-01",
        "end_date": "2024-01-31"
    })
    connector._session.get = AsyncMock(return_value=mock_response)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    usage = await connector.get_usage_stats(
        start_date="2024-01-01",
        end_date="2024-01-31"
    )
    
    assert usage["total_requests"] == 150
    assert usage["total_tokens"] == 50000
    assert usage["prompt_tokens"] == 20000
    assert usage["completion_tokens"] == 30000
    assert usage["total_cost_usd"] == 10.50


@pytest.mark.asyncio
async def test_list_available_models(connector):
    """Test listing available models."""
    connector._connected = True
    connector._session = AsyncMock()
    
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "models": [
            {"id": "meta-llama/Llama-2-7b-hf", "name": "Llama 2 7B", "context_length": 4096},
            {"id": "meta-llama/Llama-2-13b-hf", "name": "Llama 2 13B", "context_length": 4096}
        ]
    })
    connector._session.get = AsyncMock(return_value=mock_response)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    models = await connector.list_available_models()
    
    assert len(models) == 2
    assert models[0]["id"] == "meta-llama/Llama-2-7b-hf"
    assert models[1]["id"] == "meta-llama/Llama-2-13b-hf"


@pytest.mark.asyncio
async def test_upload_artifact(connector, tmp_path):
    """Test uploading an adapter."""
    connector._connected = True
    connector._session = AsyncMock()
    
    # Create temporary adapter files
    adapter_dir = tmp_path / "adapter"
    adapter_dir.mkdir()
    (adapter_dir / "adapter_model.safetensors").write_bytes(b"fake adapter data")
    (adapter_dir / "adapter_config.json").write_text('{"rank": 8}')
    
    # Mock model creation response
    mock_create_response = AsyncMock()
    mock_create_response.status = 201
    mock_create_response.json = AsyncMock(return_value={
        "id": "model123",
        "upload_url": "https://upload.together.xyz/model123"
    })
    
    # Mock upload responses
    mock_upload_response = AsyncMock()
    mock_upload_response.status = 200
    
    # Mock complete response
    mock_complete_response = AsyncMock()
    mock_complete_response.status = 200
    
    # Setup mock responses
    post_responses = [mock_create_response, mock_upload_response, mock_upload_response, mock_complete_response]
    connector._session.post = AsyncMock(side_effect=post_responses)
    
    for response in post_responses:
        response.__aenter__ = AsyncMock(return_value=response)
        response.__aexit__ = AsyncMock(return_value=None)
    
    model_id = await connector.upload_artifact(
        path=str(adapter_dir),
        metadata={
            "name": "test-adapter",
            "base_model": "meta-llama/Llama-2-7b-hf",
            "description": "Test adapter"
        }
    )
    
    assert model_id == "model123"
    assert "model123" in connector._models


@pytest.mark.asyncio
async def test_upload_artifact_missing_files(connector, tmp_path):
    """Test uploading adapter with missing files."""
    connector._connected = True
    connector._session = AsyncMock()
    
    # Create empty adapter directory
    adapter_dir = tmp_path / "adapter"
    adapter_dir.mkdir()
    
    # Mock model creation response
    mock_response = AsyncMock()
    mock_response.status = 201
    mock_response.json = AsyncMock(return_value={
        "id": "model123",
        "upload_url": "https://upload.together.xyz/model123"
    })
    connector._session.post = AsyncMock(return_value=mock_response)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    with pytest.raises(FileNotFoundError, match="No adapter files found"):
        await connector.upload_artifact(
            path=str(adapter_dir),
            metadata={
                "name": "test-adapter",
                "base_model": "meta-llama/Llama-2-7b-hf"
            }
        )


@pytest.mark.asyncio
async def test_deploy_adapter(connector, tmp_path):
    """Test deploying an adapter."""
    connector._connected = True
    connector._session = AsyncMock()
    
    # Create temporary adapter files
    adapter_dir = tmp_path / "adapter"
    adapter_dir.mkdir()
    (adapter_dir / "adapter_model.safetensors").write_bytes(b"fake adapter data")
    (adapter_dir / "adapter_config.json").write_text('{"rank": 8}')
    
    # Mock upload_artifact
    with patch.object(connector, 'upload_artifact', return_value="model123"):
        # Mock create_endpoint
        with patch.object(connector, 'create_endpoint', return_value="endpoint123"):
            deployment_id = await connector.deploy_adapter(
                adapter_path=str(adapter_dir),
                base_model="meta-llama/Llama-2-7b-hf",
                adapter_name="test-adapter"
            )
            
            assert deployment_id == "endpoint123"


@pytest.mark.asyncio
async def test_list_resources(connector):
    """Test listing available resources."""
    connector._connected = True
    
    resources = await connector.list_resources()
    
    assert len(resources) == 1
    assert resources[0].id == "together-serverless"
    assert resources[0].name == "Serverless Inference"


@pytest.mark.asyncio
async def test_get_pricing(connector):
    """Test getting pricing information."""
    pricing = await connector.get_pricing("together-serverless")
    
    assert pricing.resource_id == "together-serverless"
    assert pricing.price_per_hour == 0.0  # Pay-per-token
    assert pricing.currency == "USD"


@pytest.mark.asyncio
async def test_training_not_supported(connector):
    """Test that training operations are not supported."""
    config = TrainingConfig(
        base_model="meta-llama/Llama-2-7b-hf",
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
        await connector.get_job_status("job123")
    
    with pytest.raises(NotImplementedError):
        await connector.cancel_job("job123")
    
    with pytest.raises(NotImplementedError):
        async for _ in connector.stream_logs("job123"):
            pass
    
    with pytest.raises(NotImplementedError):
        await connector.fetch_artifact("job123")


@pytest.mark.asyncio
async def test_get_required_credentials(connector):
    """Test getting required credentials."""
    credentials = connector.get_required_credentials()
    
    assert credentials == ["api_key"]


@pytest.mark.asyncio
async def test_connector_metadata(connector):
    """Test connector metadata."""
    assert connector.name == "together_ai"
    assert connector.display_name == "Together AI"
    assert connector.description == "Serverless inference with pay-per-token pricing"
    assert connector.version == "1.0.0"
    assert connector.supports_training is False
    assert connector.supports_inference is True
    assert connector.supports_registry is True
    assert connector.supports_tracking is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
