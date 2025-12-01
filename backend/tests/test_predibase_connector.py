"""
Tests for Predibase connector.

Tests cover:
- Connection and authentication
- Adapter deployment
- Inference with hot-swapping
- Usage tracking
- Error handling
"""

import pytest
import asyncio
from pathlib import Path
import sys
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from plugins.connectors.predibase_connector import PredibaseConnector
from connectors.base import TrainingConfig


@pytest.fixture
def connector():
    """Create a Predibase connector instance."""
    return PredibaseConnector()


@pytest.fixture
def mock_session():
    """Create a mock aiohttp session."""
    session = MagicMock()
    session.close = AsyncMock()
    return session


def create_mock_response(status=200, json_data=None):
    """Helper to create a properly mocked async response."""
    mock_response = AsyncMock()
    mock_response.status = status
    if json_data is not None:
        mock_response.json = AsyncMock(return_value=json_data)
    mock_response.text = AsyncMock(return_value="")
    mock_response.read = AsyncMock(return_value=b"")
    
    # Create async context manager
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_response
    mock_context.__aexit__.return_value = None
    
    return mock_context


@pytest.fixture
def valid_credentials():
    """Valid Predibase credentials."""
    return {
        "api_key": "pb_test_key_12345"
    }


@pytest.fixture
def adapter_path(tmp_path):
    """Create a temporary adapter directory with files."""
    adapter_dir = tmp_path / "test-adapter"
    adapter_dir.mkdir()
    
    # Create adapter files
    (adapter_dir / "adapter_model.safetensors").write_bytes(b"fake adapter weights")
    (adapter_dir / "adapter_config.json").write_text(json.dumps({
        "peft_type": "LORA",
        "r": 16,
        "lora_alpha": 32
    }))
    
    return str(adapter_dir)


class TestConnection:
    """Test connection and authentication."""
    
    @pytest.mark.asyncio
    async def test_connect_success(self, connector, mock_session, valid_credentials):
        """Test successful connection."""
        # Mock successful API response
        mock_session.get = MagicMock(return_value=create_mock_response(200, {"id": "tenant-123"}))
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await connector.connect(valid_credentials)
        
        assert result is True
        assert connector._connected is True
        assert connector._api_key == valid_credentials["api_key"]
        assert connector._tenant_id == "tenant-123"
    
    @pytest.mark.asyncio
    async def test_connect_missing_api_key(self, connector):
        """Test connection with missing API key."""
        with pytest.raises(ValueError, match="api_key is required"):
            await connector.connect({})
    
    @pytest.mark.asyncio
    async def test_connect_invalid_credentials(self, connector, mock_session, valid_credentials):
        """Test connection with invalid credentials."""
        # Mock 401 response
        mock_session.get = MagicMock(return_value=create_mock_response(401))
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with pytest.raises(ValueError, match="Invalid API key"):
                await connector.connect(valid_credentials)
    
    @pytest.mark.asyncio
    async def test_disconnect(self, connector, mock_session, valid_credentials):
        """Test disconnection."""
        # Connect first
        mock_session.get = MagicMock(return_value=create_mock_response(200, {"id": "tenant-123"}))
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            await connector.connect(valid_credentials)
        
        # Disconnect
        result = await connector.disconnect()
        
        assert result is True
        assert connector._connected is False
        assert connector._api_key is None
        assert connector._session is None
    
    @pytest.mark.asyncio
    async def test_verify_connection(self, connector, mock_session, valid_credentials):
        """Test connection verification."""
        # Connect first
        mock_session.get = MagicMock(return_value=create_mock_response(200, {"id": "tenant-123"}))
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            await connector.connect(valid_credentials)
        
        # Verify
        is_valid = await connector.verify_connection()
        assert is_valid is True


class TestAdapterDeployment:
    """Test adapter deployment functionality."""
    
    @pytest.mark.asyncio
    async def test_deploy_adapter_success(self, connector, mock_session, valid_credentials, adapter_path):
        """Test successful adapter deployment."""
        # Connect first
        mock_session.get = MagicMock(return_value=create_mock_response(200, {"id": "tenant-123"}))
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            await connector.connect(valid_credentials)
        
        # Mock upload_artifact
        connector.upload_artifact = AsyncMock(return_value="adapter-123")
        
        # Mock deployment creation
        mock_session.post = MagicMock(return_value=create_mock_response(201, {
            "id": "deployment-456",
            "endpoint": "https://api.predibase.com/v1/deployments/deployment-456"
        }))
        
        # Deploy adapter
        deployment_id = await connector.deploy_adapter(
            adapter_path=adapter_path,
            base_model="meta-llama/Llama-2-7b-hf",
            adapter_name="test-adapter"
        )
        
        assert deployment_id == "deployment-456"
        assert deployment_id in connector._deployments
        assert connector._deployments[deployment_id]["adapter_name"] == "test-adapter"
    
    @pytest.mark.asyncio
    async def test_deploy_adapter_not_connected(self, connector, adapter_path):
        """Test deployment without connection."""
        with pytest.raises(RuntimeError, match="Not connected"):
            await connector.deploy_adapter(
                adapter_path=adapter_path,
                base_model="meta-llama/Llama-2-7b-hf",
                adapter_name="test-adapter"
            )
    
    @pytest.mark.asyncio
    async def test_deploy_adapter_invalid_path(self, connector, mock_session, valid_credentials):
        """Test deployment with invalid adapter path."""
        # Connect first
        mock_session.get = MagicMock(return_value=create_mock_response(200, {"id": "tenant-123"}))
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            await connector.connect(valid_credentials)
        
        with pytest.raises(FileNotFoundError):
            await connector.deploy_adapter(
                adapter_path="/nonexistent/path",
                base_model="meta-llama/Llama-2-7b-hf",
                adapter_name="test-adapter"
            )
    
    @pytest.mark.asyncio
    async def test_get_deployment_status(self, connector, mock_session, valid_credentials):
        """Test getting deployment status."""
        # Connect first
        mock_session.get = MagicMock(return_value=create_mock_response(200, {"id": "tenant-123"}))
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            await connector.connect(valid_credentials)
        
        # Mock status response
        status_response = AsyncMock()
        status_response.status = 200
        status_response.json = AsyncMock(return_value={
            "status": "ready",
            "endpoint": "https://api.predibase.com/v1/deployments/deployment-456"
        })
        mock_session.get.return_value.__aenter__.return_value = status_response
        
        status = await connector.get_deployment_status("deployment-456")
        assert status == "ready"
    
    @pytest.mark.asyncio
    async def test_list_deployments(self, connector, mock_session, valid_credentials):
        """Test listing deployments."""
        # Connect first
        mock_session.get = MagicMock(return_value=create_mock_response(200, {"id": "tenant-123"}))
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            await connector.connect(valid_credentials)
        
        # Mock list response
        list_response = AsyncMock()
        list_response.status = 200
        list_response.json = AsyncMock(return_value={
            "deployments": [
                {"id": "deployment-1", "adapter_name": "adapter-1"},
                {"id": "deployment-2", "adapter_name": "adapter-2"}
            ]
        })
        mock_session.get.return_value.__aenter__.return_value = list_response
        
        deployments = await connector.list_deployments()
        assert len(deployments) == 2
        assert deployments[0]["id"] == "deployment-1"
    
    @pytest.mark.asyncio
    async def test_stop_deployment(self, connector, mock_session, valid_credentials):
        """Test stopping a deployment."""
        # Connect first
        mock_session.get = MagicMock(return_value=create_mock_response(200, {"id": "tenant-123"}))
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            await connector.connect(valid_credentials)
        
        # Mock stop response
        stop_response = AsyncMock()
        stop_response.status = 200
        mock_session.post.return_value.__aenter__.return_value = stop_response
        
        result = await connector.stop_deployment("deployment-456")
        assert result is True


class TestInference:
    """Test inference functionality."""
    
    @pytest.mark.asyncio
    async def test_inference_success(self, connector, mock_session, valid_credentials):
        """Test successful inference."""
        # Connect first
        mock_session.get = MagicMock(return_value=create_mock_response(200, {"id": "tenant-123"}))
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            await connector.connect(valid_credentials)
        
        # Add deployment to cache
        connector._deployments["deployment-456"] = {
            "id": "deployment-456",
            "endpoint": "https://api.predibase.com/v1/deployments/deployment-456"
        }
        
        # Mock inference response
        mock_session.post = MagicMock(return_value=create_mock_response(200, {
            "generated_text": "Paris is the capital of France.",
            "tokens": ["Paris", "is", "the", "capital", "of", "France", "."]
        }))
        
        result = await connector.inference(
            deployment_id="deployment-456",
            prompt="What is the capital of France?"
        )
        
        assert "text" in result
        assert result["text"] == "Paris is the capital of France."
        assert "latency_ms" in result
        assert result["adapter_used"] == "base"
    
    @pytest.mark.asyncio
    async def test_inference_with_adapter(self, connector, mock_session, valid_credentials):
        """Test inference with adapter hot-swapping."""
        # Connect first
        mock_session.get = MagicMock(return_value=create_mock_response(200, {"id": "tenant-123"}))
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            await connector.connect(valid_credentials)
        
        # Add deployment to cache
        connector._deployments["deployment-456"] = {
            "id": "deployment-456",
            "endpoint": "https://api.predibase.com/v1/deployments/deployment-456"
        }
        
        # Mock inference response
        mock_session.post = MagicMock(return_value=create_mock_response(200, {
            "generated_text": "Custom adapter response",
            "tokens": ["Custom", "adapter", "response"]
        }))
        
        result = await connector.inference(
            deployment_id="deployment-456",
            prompt="Test prompt",
            adapter_name="my-custom-adapter"
        )
        
        assert result["text"] == "Custom adapter response"
        assert result["adapter_used"] == "my-custom-adapter"
    
    @pytest.mark.asyncio
    async def test_inference_not_connected(self, connector):
        """Test inference without connection."""
        with pytest.raises(RuntimeError, match="Not connected"):
            await connector.inference(
                deployment_id="deployment-456",
                prompt="Test prompt"
            )


class TestUsageTracking:
    """Test usage tracking functionality."""
    
    @pytest.mark.asyncio
    async def test_get_usage_stats(self, connector, mock_session, valid_credentials):
        """Test getting usage statistics."""
        # Connect first
        mock_session.get = MagicMock(return_value=create_mock_response(200, {"id": "tenant-123"}))
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            await connector.connect(valid_credentials)
        
        # Mock usage response
        usage_response = AsyncMock()
        usage_response.status = 200
        usage_response.json = AsyncMock(return_value={
            "total_requests": 1000,
            "total_tokens": 50000,
            "total_cost_usd": 25.50,
            "deployments": [
                {"id": "deployment-1", "requests": 600},
                {"id": "deployment-2", "requests": 400}
            ],
            "start_date": "2024-01-01",
            "end_date": "2024-01-31"
        })
        mock_session.get.return_value.__aenter__.return_value = usage_response
        
        usage = await connector.get_usage_stats(
            start_date="2024-01-01",
            end_date="2024-01-31"
        )
        
        assert usage["total_requests"] == 1000
        assert usage["total_tokens"] == 50000
        assert usage["total_cost_usd"] == 25.50
        assert len(usage["deployments"]) == 2


class TestArtifactManagement:
    """Test artifact upload and management."""
    
    @pytest.mark.asyncio
    async def test_upload_artifact_success(self, connector, mock_session, valid_credentials, adapter_path):
        """Test successful artifact upload."""
        # Connect first
        mock_session.get = MagicMock(return_value=create_mock_response(200, {"id": "tenant-123"}))
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            await connector.connect(valid_credentials)
        
        # Mock adapter creation
        create_response = AsyncMock()
        create_response.status = 201
        create_response.json = AsyncMock(return_value={
            "id": "adapter-789",
            "upload_url": "https://upload.predibase.com/adapter-789"
        })
        
        # Mock file upload
        upload_response = AsyncMock()
        upload_response.status = 200
        
        # Mock completion
        complete_response = AsyncMock()
        complete_response.status = 200
        
        mock_session.post.return_value.__aenter__.side_effect = [
            create_response,
            upload_response,
            upload_response,
            complete_response
        ]
        
        adapter_id = await connector.upload_artifact(
            path=adapter_path,
            metadata={
                "name": "test-adapter",
                "base_model": "meta-llama/Llama-2-7b-hf"
            }
        )
        
        assert adapter_id == "adapter-789"
        assert adapter_id in connector._adapters
    
    @pytest.mark.asyncio
    async def test_upload_artifact_missing_metadata(self, connector, mock_session, valid_credentials, adapter_path):
        """Test upload with missing metadata."""
        # Connect first
        mock_session.get = MagicMock(return_value=create_mock_response(200, {"id": "tenant-123"}))
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            await connector.connect(valid_credentials)
        
        with pytest.raises(ValueError, match="'name' and 'base_model' are required"):
            await connector.upload_artifact(
                path=adapter_path,
                metadata={"name": "test-adapter"}  # Missing base_model
            )
    
    @pytest.mark.asyncio
    async def test_list_adapters(self, connector, mock_session, valid_credentials):
        """Test listing adapters."""
        # Connect first
        mock_session.get = MagicMock(return_value=create_mock_response(200, {"id": "tenant-123"}))
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            await connector.connect(valid_credentials)
        
        # Mock list response
        list_response = AsyncMock()
        list_response.status = 200
        list_response.json = AsyncMock(return_value={
            "adapters": [
                {"id": "adapter-1", "name": "adapter-1", "base_model": "llama-2-7b"},
                {"id": "adapter-2", "name": "adapter-2", "base_model": "llama-2-13b"}
            ]
        })
        mock_session.get.return_value.__aenter__.return_value = list_response
        
        adapters = await connector.list_adapters()
        assert len(adapters) == 2
        assert adapters[0]["name"] == "adapter-1"


class TestResourceManagement:
    """Test resource and pricing queries."""
    
    @pytest.mark.asyncio
    async def test_list_resources(self, connector, mock_session, valid_credentials):
        """Test listing available resources."""
        # Connect first
        mock_session.get = MagicMock(return_value=create_mock_response(200, {"id": "tenant-123"}))
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            await connector.connect(valid_credentials)
        
        resources = await connector.list_resources()
        assert len(resources) > 0
        assert any(r.gpu_type == "A100" for r in resources)
    
    @pytest.mark.asyncio
    async def test_get_pricing(self, connector):
        """Test getting pricing information."""
        pricing = await connector.get_pricing("predibase-a100")
        assert pricing.resource_id == "predibase-a100"
        assert pricing.price_per_hour > 0
        assert pricing.currency == "USD"
    
    @pytest.mark.asyncio
    async def test_get_pricing_invalid_resource(self, connector):
        """Test getting pricing for invalid resource."""
        with pytest.raises(ValueError, match="Invalid resource ID"):
            await connector.get_pricing("invalid-resource")


class TestNotImplementedMethods:
    """Test methods that are not supported."""
    
    @pytest.mark.asyncio
    async def test_submit_job_not_implemented(self, connector):
        """Test that submit_job raises NotImplementedError."""
        config = TrainingConfig(
            base_model="test-model",
            model_source="huggingface",
            algorithm="lora",
            rank=16,
            alpha=32,
            dropout=0.1,
            target_modules=["q_proj", "v_proj"]
        )
        
        with pytest.raises(NotImplementedError):
            await connector.submit_job(config)
    
    @pytest.mark.asyncio
    async def test_get_job_status_not_implemented(self, connector):
        """Test that get_job_status raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await connector.get_job_status("job-123")
    
    @pytest.mark.asyncio
    async def test_cancel_job_not_implemented(self, connector):
        """Test that cancel_job raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await connector.cancel_job("job-123")
    
    @pytest.mark.asyncio
    async def test_fetch_artifact_not_implemented(self, connector):
        """Test that fetch_artifact raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await connector.fetch_artifact("job-123")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
