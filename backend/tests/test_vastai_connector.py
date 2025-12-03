"""
Tests for Vast.ai connector.

These tests verify the Vast.ai connector implementation against the
PlatformConnector interface requirements.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from plugins.connectors.vastai_connector import VastAIConnector
from connectors.base import TrainingConfig, JobStatus, ResourceType


@pytest.fixture
def connector():
    """Create a VastAIConnector instance."""
    return VastAIConnector()


@pytest.fixture
def mock_session():
    """Create a mock aiohttp session."""
    session = AsyncMock()
    return session


@pytest.fixture
def sample_config():
    """Create a sample training configuration."""
    return TrainingConfig(
        base_model="unsloth/llama-3-8b-bnb-4bit",
        model_source="huggingface",
        algorithm="lora",
        rank=16,
        alpha=16,
        dropout=0.1,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        quantization="int4",
        learning_rate=2e-4,
        batch_size=4,
        gradient_accumulation_steps=4,
        num_epochs=3,
        warmup_steps=100,
        provider="vastai",
        resource_id="RTX 4090",
        dataset_path="/data/train.json",
        validation_split=0.1,
        project_name="test-project",
        output_dir="/workspace/output",
        checkpoint_steps=500,
    )


class TestVastAIConnectorInterface:
    """Test that VastAIConnector implements the PlatformConnector interface."""
    
    def test_connector_metadata(self, connector):
        """Test connector has required metadata."""
        assert connector.name == "vastai"
        assert connector.display_name == "Vast.ai"
        assert connector.description
        assert connector.version
    
    def test_connector_features(self, connector):
        """Test connector declares supported features."""
        assert connector.supports_training is True
        assert connector.supports_inference is True
        assert connector.supports_registry is False
        assert connector.supports_tracking is False
    
    def test_required_credentials(self, connector):
        """Test connector declares required credentials."""
        creds = connector.get_required_credentials()
        assert "api_key" in creds


class TestConnection:
    """Test connection management."""
    
    @pytest.mark.asyncio
    async def test_connect_success(self, connector, mock_session):
        """Test successful connection."""
        # Mock successful API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"id": 123, "username": "test"})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.get = Mock(return_value=mock_response)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await connector.connect({"api_key": "test_key"})
            assert result is True
            assert connector._connected is True
    
    @pytest.mark.asyncio
    async def test_connect_invalid_credentials(self, connector, mock_session):
        """Test connection with invalid credentials."""
        # Mock 401 response
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.get = Mock(return_value=mock_response)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with pytest.raises(ValueError, match="Invalid API key"):
                await connector.connect({"api_key": "invalid_key"})
    
    @pytest.mark.asyncio
    async def test_connect_missing_api_key(self, connector):
        """Test connection without API key."""
        with pytest.raises(ValueError, match="api_key is required"):
            await connector.connect({})
    
    @pytest.mark.asyncio
    async def test_disconnect(self, connector, mock_session):
        """Test disconnection."""
        connector._session = mock_session
        connector._connected = True
        connector._api_key = "test_key"
        
        result = await connector.disconnect()
        
        assert result is True
        assert connector._connected is False
        assert connector._api_key is None
        mock_session.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_verify_connection_success(self, connector, mock_session):
        """Test connection verification when connected."""
        connector._connected = True
        connector._session = mock_session
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.get = Mock(return_value=mock_response)
        
        result = await connector.verify_connection()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_connection_not_connected(self, connector):
        """Test connection verification when not connected."""
        result = await connector.verify_connection()
        assert result is False


class TestJobManagement:
    """Test job submission and management."""
    
    @pytest.mark.asyncio
    async def test_submit_job_not_connected(self, connector, sample_config):
        """Test job submission when not connected."""
        with pytest.raises(RuntimeError, match="Not connected"):
            await connector.submit_job(sample_config)
    
    @pytest.mark.asyncio
    async def test_get_job_status_not_connected(self, connector):
        """Test getting job status when not connected."""
        with pytest.raises(RuntimeError, match="Not connected"):
            await connector.get_job_status("123")
    
    @pytest.mark.asyncio
    async def test_cancel_job_not_connected(self, connector):
        """Test canceling job when not connected."""
        with pytest.raises(RuntimeError, match="Not connected"):
            await connector.cancel_job("123")


class TestResourceManagement:
    """Test resource listing and pricing."""
    
    @pytest.mark.asyncio
    async def test_list_resources_not_connected(self, connector):
        """Test listing resources when not connected."""
        with pytest.raises(RuntimeError, match="Not connected"):
            await connector.list_resources()
    
    @pytest.mark.asyncio
    async def test_list_resources_success(self, connector, mock_session):
        """Test successful resource listing."""
        connector._connected = True
        connector._session = mock_session
        connector._api_key = "test_key"
        
        # Mock API response with offers
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "offers": [
                {
                    "id": 1,
                    "gpu_name": "RTX 4090",
                    "num_gpus": 1,
                    "gpu_ram": 24576,  # 24GB in MB
                    "cpu_cores": 16,
                    "cpu_ram": 65536,  # 64GB in MB
                    "dph_total": 0.50,
                },
                {
                    "id": 2,
                    "gpu_name": "A100",
                    "num_gpus": 1,
                    "gpu_ram": 40960,  # 40GB in MB
                    "cpu_cores": 32,
                    "cpu_ram": 131072,  # 128GB in MB
                    "dph_total": 1.20,
                },
            ]
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.get = Mock(return_value=mock_response)
        
        resources = await connector.list_resources()
        
        assert len(resources) == 2
        assert resources[0].gpu_type == "RTX 4090"
        assert resources[0].vram_gb == 24
        assert resources[1].gpu_type == "A100"
        assert resources[1].vram_gb == 40
    
    @pytest.mark.asyncio
    async def test_get_pricing_not_connected(self, connector):
        """Test getting pricing when not connected."""
        with pytest.raises(RuntimeError, match="Not connected"):
            await connector.get_pricing("RTX 4090")
    
    @pytest.mark.asyncio
    async def test_get_pricing_success(self, connector, mock_session):
        """Test successful pricing retrieval."""
        connector._connected = True
        connector._session = mock_session
        connector._api_key = "test_key"
        
        # Mock API response with pricing
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "offers": [
                {"dph_total": 0.45},
                {"dph_total": 0.50},
                {"dph_total": 0.55},
            ]
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.get = Mock(return_value=mock_response)
        
        pricing = await connector.get_pricing("RTX 4090")
        
        assert pricing.resource_id == "RTX 4090"
        assert pricing.price_per_hour == 0.45  # Cheapest
        assert pricing.spot_price_per_hour == 0.45  # Min price
        assert pricing.currency == "USD"
    
    @pytest.mark.asyncio
    async def test_get_pricing_no_offers(self, connector, mock_session):
        """Test pricing retrieval when no offers available."""
        connector._connected = True
        connector._session = mock_session
        connector._api_key = "test_key"
        
        # Mock API response with no offers
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"offers": []})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.get = Mock(return_value=mock_response)
        
        with pytest.raises(ValueError, match="No available instances"):
            await connector.get_pricing("NonexistentGPU")


class TestArtifactManagement:
    """Test artifact upload and download."""
    
    @pytest.mark.asyncio
    async def test_fetch_artifact_not_connected(self, connector):
        """Test fetching artifact when not connected."""
        with pytest.raises(RuntimeError, match="Not connected"):
            await connector.fetch_artifact("123")
    
    @pytest.mark.asyncio
    async def test_upload_artifact_not_connected(self, connector):
        """Test uploading artifact when not connected."""
        with pytest.raises(RuntimeError, match="Not connected"):
            await connector.upload_artifact("/path/to/file", {})
    
    @pytest.mark.asyncio
    async def test_upload_artifact_file_not_found(self, connector):
        """Test uploading non-existent file."""
        connector._connected = True
        
        with pytest.raises(FileNotFoundError):
            await connector.upload_artifact("/nonexistent/file.tar.gz", {})


class TestConfigurationValidation:
    """Test training configuration validation."""
    
    def test_validate_config_success(self, connector, sample_config):
        """Test validation of valid configuration."""
        assert connector.validate_config(sample_config) is True
    
    def test_validate_config_missing_base_model(self, connector, sample_config):
        """Test validation fails without base model."""
        sample_config.base_model = ""
        
        with pytest.raises(ValueError, match="base_model is required"):
            connector.validate_config(sample_config)
    
    def test_validate_config_missing_dataset(self, connector, sample_config):
        """Test validation fails without dataset."""
        sample_config.dataset_path = ""
        
        with pytest.raises(ValueError, match="dataset_path is required"):
            connector.validate_config(sample_config)
    
    def test_validate_config_invalid_rank(self, connector, sample_config):
        """Test validation fails with invalid rank."""
        sample_config.rank = 0
        
        with pytest.raises(ValueError, match="rank must be positive"):
            connector.validate_config(sample_config)
    
    def test_validate_config_invalid_dropout(self, connector, sample_config):
        """Test validation fails with invalid dropout."""
        sample_config.dropout = 1.5
        
        with pytest.raises(ValueError, match="dropout must be between 0 and 1"):
            connector.validate_config(sample_config)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
