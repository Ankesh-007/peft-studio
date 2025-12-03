"""
Tests for Replicate connector.

Tests cover:
- Connection and authentication
- Model deployment
- Inference API
- Version management
- Error handling
"""

import pytest
import asyncio
from pathlib import Path
import sys
import tempfile
import json

sys.path.append(str(Path(__file__).parent.parent))

from plugins.connectors.replicate_connector import ReplicateConnector
from connectors.base import Resource, ResourceType, PricingInfo


@pytest.fixture
def connector():
    """Create a Replicate connector instance."""
    return ReplicateConnector()


@pytest.fixture
def mock_credentials():
    """Mock credentials for testing."""
    return {
        "api_token": "r8_test_token_12345"
    }


@pytest.fixture
def temp_adapter_dir():
    """Create a temporary adapter directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        adapter_path = Path(tmpdir)
        
        # Create mock adapter files
        (adapter_path / "adapter_model.safetensors").write_bytes(b"mock_weights")
        (adapter_path / "adapter_config.json").write_text(json.dumps({
            "base_model": "meta-llama/Llama-2-7b-hf",
            "r": 16,
            "lora_alpha": 32
        }))
        
        yield adapter_path


class TestReplicateConnectorBasics:
    """Test basic connector functionality."""
    
    def test_connector_metadata(self, connector):
        """Test connector has correct metadata."""
        assert connector.name == "replicate"
        assert connector.display_name == "Replicate"
        assert "version management" in connector.description.lower()
        assert connector.supports_inference is True
        assert connector.supports_training is False
        assert connector.supports_registry is True
    
    def test_required_credentials(self, connector):
        """Test required credentials list."""
        required = connector.get_required_credentials()
        assert "api_token" in required
        assert len(required) == 1
    
    @pytest.mark.asyncio
    async def test_connect_missing_credentials(self, connector):
        """Test connection fails with missing credentials."""
        with pytest.raises(ValueError, match="api_token is required"):
            await connector.connect({})
    
    @pytest.mark.asyncio
    async def test_disconnect(self, connector, mock_credentials):
        """Test disconnect cleans up resources."""
        # Mock connection
        connector._connected = True
        connector._api_token = "test"
        connector._models = {"test": {}}
        connector._versions = {"test": []}
        connector._predictions = {"test": {}}
        
        # Disconnect
        result = await connector.disconnect()
        
        assert result is True
        assert connector._connected is False
        assert connector._api_token is None
        assert len(connector._models) == 0
        assert len(connector._versions) == 0
        assert len(connector._predictions) == 0


class TestReplicateModelManagement:
    """Test model management functionality."""
    
    @pytest.mark.asyncio
    async def test_create_model_not_connected(self, connector):
        """Test create_model fails when not connected."""
        with pytest.raises(RuntimeError, match="Not connected"):
            await connector.create_model(
                owner="test-user",
                name="test-model"
            )
    
    @pytest.mark.asyncio
    async def test_get_model_not_connected(self, connector):
        """Test get_model fails when not connected."""
        with pytest.raises(RuntimeError, match="Not connected"):
            await connector.get_model("test-user/test-model")
    
    @pytest.mark.asyncio
    async def test_delete_model_not_connected(self, connector):
        """Test delete_model fails when not connected."""
        with pytest.raises(RuntimeError, match="Not connected"):
            await connector.delete_model("test-user/test-model")


class TestReplicateVersionManagement:
    """Test version management functionality."""
    
    @pytest.mark.asyncio
    async def test_create_version_not_connected(self, connector):
        """Test create_model_version fails when not connected."""
        with pytest.raises(RuntimeError, match="Not connected"):
            await connector.create_model_version(
                model_id="test-user/test-model",
                version="v1"
            )
    
    @pytest.mark.asyncio
    async def test_list_versions_not_connected(self, connector):
        """Test list_model_versions fails when not connected."""
        with pytest.raises(RuntimeError, match="Not connected"):
            await connector.list_model_versions("test-user/test-model")
    
    @pytest.mark.asyncio
    async def test_get_version_not_connected(self, connector):
        """Test get_model_version fails when not connected."""
        with pytest.raises(RuntimeError, match="Not connected"):
            await connector.get_model_version(
                model_id="test-user/test-model",
                version_id="abc123"
            )


class TestReplicateInference:
    """Test inference functionality."""
    
    @pytest.mark.asyncio
    async def test_create_prediction_not_connected(self, connector):
        """Test create_prediction fails when not connected."""
        with pytest.raises(RuntimeError, match="Not connected"):
            await connector.create_prediction(
                model_id="test-user/test-model",
                input_data={"prompt": "test"}
            )
    
    @pytest.mark.asyncio
    async def test_get_prediction_not_connected(self, connector):
        """Test get_prediction fails when not connected."""
        with pytest.raises(RuntimeError, match="Not connected"):
            await connector.get_prediction("pred_123")
    
    @pytest.mark.asyncio
    async def test_cancel_prediction_not_connected(self, connector):
        """Test cancel_prediction fails when not connected."""
        with pytest.raises(RuntimeError, match="Not connected"):
            await connector.cancel_prediction("pred_123")
    
    @pytest.mark.asyncio
    async def test_inference_not_connected(self, connector):
        """Test inference fails when not connected."""
        with pytest.raises(RuntimeError, match="Not connected"):
            await connector.inference(
                model_id="test-user/test-model",
                prompt="test"
            )
    
    @pytest.mark.asyncio
    async def test_wait_for_prediction_timeout(self, connector):
        """Test wait_for_prediction times out."""
        # Mock connected state
        connector._connected = True
        
        # Mock get_prediction to always return "processing"
        async def mock_get_prediction(pred_id):
            return {"status": "processing"}
        
        connector.get_prediction = mock_get_prediction
        
        # Should timeout quickly
        with pytest.raises(TimeoutError):
            await connector.wait_for_prediction(
                prediction_id="test_pred",
                timeout=0.1,
                poll_interval=0.05
            )


class TestReplicateDeployment:
    """Test deployment functionality."""
    
    @pytest.mark.asyncio
    async def test_deploy_model_not_connected(self, connector):
        """Test deploy_model fails when not connected."""
        with pytest.raises(RuntimeError, match="Not connected"):
            await connector.deploy_model(
                model_name="test-model",
                base_model="meta-llama/Llama-2-7b-hf"
            )
    
    @pytest.mark.asyncio
    async def test_upload_artifact_not_connected(self, connector):
        """Test upload_artifact fails when not connected."""
        with pytest.raises(RuntimeError, match="Not connected"):
            await connector.upload_artifact(
                path="/fake/path",
                metadata={"name": "test"}
            )
    
    @pytest.mark.asyncio
    async def test_upload_artifact_missing_path(self, connector):
        """Test upload_artifact fails with missing path."""
        connector._connected = True
        
        with pytest.raises(FileNotFoundError):
            await connector.upload_artifact(
                path="/nonexistent/path",
                metadata={"name": "test"}
            )
    
    @pytest.mark.asyncio
    async def test_upload_artifact_success(self, connector, temp_adapter_dir):
        """Test upload_artifact returns URL."""
        connector._connected = True
        
        url = await connector.upload_artifact(
            path=str(temp_adapter_dir),
            metadata={"name": "test-adapter"}
        )
        
        assert url.startswith("https://")
        assert "test-adapter" in url


class TestReplicateResources:
    """Test resource listing and pricing."""
    
    @pytest.mark.asyncio
    async def test_list_resources_disconnected(self, connector):
        """Test list_resources returns empty when disconnected."""
        resources = await connector.list_resources()
        assert resources == []
    
    @pytest.mark.asyncio
    async def test_list_resources_connected(self, connector):
        """Test list_resources returns GPU options."""
        connector._connected = True
        
        resources = await connector.list_resources()
        
        assert len(resources) > 0
        assert all(isinstance(r, Resource) for r in resources)
        assert all(r.type == ResourceType.GPU for r in resources)
        
        # Check for expected GPU types
        gpu_types = [r.gpu_type for r in resources]
        assert "T4" in gpu_types
        assert "A40" in gpu_types
    
    @pytest.mark.asyncio
    async def test_get_pricing_valid_resource(self, connector):
        """Test get_pricing returns valid pricing info."""
        pricing = await connector.get_pricing("replicate-t4")
        
        assert isinstance(pricing, PricingInfo)
        assert pricing.resource_id == "replicate-t4"
        assert pricing.price_per_hour > 0
        assert pricing.currency == "USD"
        assert pricing.billing_increment_seconds == 1
    
    @pytest.mark.asyncio
    async def test_get_pricing_invalid_resource(self, connector):
        """Test get_pricing fails with invalid resource."""
        with pytest.raises(ValueError, match="Invalid resource ID"):
            await connector.get_pricing("invalid-resource")


class TestReplicateNotImplemented:
    """Test methods that should not be implemented."""
    
    @pytest.mark.asyncio
    async def test_submit_job_not_implemented(self, connector):
        """Test submit_job raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await connector.submit_job(None)
    
    @pytest.mark.asyncio
    async def test_get_job_status_not_implemented(self, connector):
        """Test get_job_status raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await connector.get_job_status("job_123")
    
    @pytest.mark.asyncio
    async def test_cancel_job_not_implemented(self, connector):
        """Test cancel_job raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await connector.cancel_job("job_123")
    
    @pytest.mark.asyncio
    async def test_stream_logs_not_implemented(self, connector):
        """Test stream_logs raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            async for _ in connector.stream_logs("job_123"):
                pass
    
    @pytest.mark.asyncio
    async def test_fetch_artifact_not_implemented(self, connector):
        """Test fetch_artifact raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await connector.fetch_artifact("job_123")


class TestReplicateIntegration:
    """Integration tests (require real API credentials)."""
    
    @pytest.mark.skip(reason="Requires real Replicate API credentials")
    @pytest.mark.asyncio
    async def test_real_connection(self, connector):
        """Test real connection to Replicate API."""
        # This test requires a real API token
        credentials = {
            "api_token": "r8_your_real_token_here"
        }
        
        result = await connector.connect(credentials)
        assert result is True
        
        # Verify connection
        is_valid = await connector.verify_connection()
        assert is_valid is True
        
        # Cleanup
        await connector.disconnect()
    
    @pytest.mark.skip(reason="Requires real Replicate API credentials")
    @pytest.mark.asyncio
    async def test_real_list_resources(self, connector):
        """Test listing real resources."""
        credentials = {
            "api_token": "r8_your_real_token_here"
        }
        
        await connector.connect(credentials)
        
        resources = await connector.list_resources()
        assert len(resources) > 0
        
        for resource in resources:
            print(f"Resource: {resource.name}")
            print(f"GPU: {resource.gpu_type}")
            print(f"VRAM: {resource.vram_gb}GB")
            
            pricing = await connector.get_pricing(resource.id)
            print(f"Price: ${pricing.price_per_hour}/hour")
        
        await connector.disconnect()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
