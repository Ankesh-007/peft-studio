"""
Tests for RunPod connector implementation.

This test suite verifies the RunPod connector implements all required
functionality including GPU provisioning, job submission, log streaming,
and artifact management.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from connectors.base import TrainingConfig, JobStatus, ResourceType
from plugins.connectors.runpod_connector import RunPodConnector


class TestRunPodConnector:
    """Test suite for RunPod connector."""
    
    @pytest.fixture
    def connector(self):
        """Create a RunPod connector instance."""
        return RunPodConnector()
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock aiohttp session."""
        session = AsyncMock()
        return session
    
    @pytest.fixture
    def training_config(self):
        """Create a sample training configuration."""
        return TrainingConfig(
            base_model="meta-llama/Llama-2-7b-hf",
            model_source="huggingface",
            algorithm="lora",
            rank=16,
            alpha=32,
            dropout=0.1,
            target_modules=["q_proj", "v_proj"],
            quantization="int4",
            learning_rate=2e-4,
            batch_size=4,
            gradient_accumulation_steps=4,
            num_epochs=3,
            warmup_steps=100,
            provider="runpod",
            resource_id="NVIDIA RTX A4000",
            dataset_path="/data/train.json",
            validation_split=0.1,
            project_name="test-training",
            output_dir="/output",
            checkpoint_steps=500,
        )
    
    def test_connector_metadata(self, connector):
        """Test connector has correct metadata."""
        assert connector.name == "runpod"
        assert connector.display_name == "RunPod"
        assert connector.description
        assert connector.version == "1.0.0"
        assert connector.supports_training is True
        assert connector.supports_inference is True
    
    def test_required_credentials(self, connector):
        """Test connector requires API key."""
        creds = connector.get_required_credentials()
        assert "api_key" in creds
        assert len(creds) == 1
    
    @pytest.mark.asyncio
    async def test_connect_missing_api_key(self, connector):
        """Test connection fails without API key."""
        with pytest.raises(ValueError, match="api_key is required"):
            await connector.connect({})
    
    @pytest.mark.asyncio
    async def test_connect_success(self, connector, mock_session):
        """Test successful connection."""
        # Mock successful API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "data": {"myself": {"id": "user123"}}
        })
        
        mock_session.post = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        # Patch aiohttp.ClientSession
        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await connector.connect({"api_key": "test_key"})
            assert result is True
            assert connector._connected is True
            assert connector._api_key == "test_key"
    
    @pytest.mark.asyncio
    async def test_connect_invalid_api_key(self, connector, mock_session):
        """Test connection fails with invalid API key."""
        # Mock 401 response
        mock_response = AsyncMock()
        mock_response.status = 401
        
        mock_session.post = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with pytest.raises(ValueError, match="Invalid API key"):
                await connector.connect({"api_key": "invalid_key"})
    
    @pytest.mark.asyncio
    async def test_disconnect(self, connector, mock_session):
        """Test disconnection."""
        # Setup connected state
        connector._connected = True
        connector._session = mock_session
        connector._api_key = "test_key"
        
        result = await connector.disconnect()
        
        assert result is True
        assert connector._connected is False
        assert connector._api_key is None
        assert connector._session is None
    
    @pytest.mark.asyncio
    async def test_verify_connection_when_connected(self, connector, mock_session):
        """Test verify connection when connected."""
        connector._connected = True
        connector._session = mock_session
        
        # Mock successful verification
        mock_response = AsyncMock()
        mock_response.status = 200
        
        mock_session.post = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        result = await connector.verify_connection()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_connection_when_not_connected(self, connector):
        """Test verify connection when not connected."""
        result = await connector.verify_connection()
        assert result is False
    
    @pytest.mark.asyncio
    async def test_submit_job_not_connected(self, connector, training_config):
        """Test job submission fails when not connected."""
        with pytest.raises(RuntimeError, match="Not connected"):
            await connector.submit_job(training_config)
    
    @pytest.mark.asyncio
    async def test_submit_job_success(self, connector, mock_session, training_config):
        """Test successful job submission."""
        connector._connected = True
        connector._session = mock_session
        connector._api_key = "test_key"
        
        # Mock successful pod creation
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "data": {
                "podFindAndDeployOnDemand": {
                    "id": "pod123",
                    "desiredStatus": "RUNNING",
                    "imageName": "runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel",
                    "env": [],
                    "machineId": "machine123",
                    "machine": {
                        "gpuDisplayName": "NVIDIA RTX A4000"
                    }
                }
            }
        })
        
        mock_session.post = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        job_id = await connector.submit_job(training_config)
        
        assert job_id == "pod123"
        assert job_id in connector._jobs
        assert connector._jobs[job_id]["status"] == JobStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_get_job_status(self, connector, mock_session):
        """Test getting job status."""
        connector._connected = True
        connector._session = mock_session
        
        # Mock status response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "data": {
                "pod": {
                    "id": "pod123",
                    "desiredStatus": "RUNNING",
                    "runtime": {
                        "uptimeInSeconds": 120
                    }
                }
            }
        })
        
        mock_session.post = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        status = await connector.get_job_status("pod123")
        assert status == JobStatus.RUNNING
    
    @pytest.mark.asyncio
    async def test_cancel_job(self, connector, mock_session):
        """Test job cancellation."""
        connector._connected = True
        connector._session = mock_session
        
        # Mock successful cancellation
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "data": {
                "podStop": {
                    "id": "pod123",
                    "desiredStatus": "STOPPED"
                }
            }
        })
        
        mock_session.post = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        result = await connector.cancel_job("pod123")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_list_resources(self, connector, mock_session):
        """Test listing available GPU resources."""
        connector._connected = True
        connector._session = mock_session
        
        # Mock GPU types response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "data": {
                "gpuTypes": [
                    {
                        "id": "NVIDIA RTX A4000",
                        "displayName": "RTX A4000",
                        "memoryInGb": 16,
                        "secureCloud": True,
                        "communityCloud": False,
                        "lowestPrice": {
                            "minimumBidPrice": 0.30,
                            "uninterruptablePrice": 0.45
                        }
                    },
                    {
                        "id": "NVIDIA A100",
                        "displayName": "A100 80GB",
                        "memoryInGb": 80,
                        "secureCloud": True,
                        "communityCloud": True,
                        "lowestPrice": {
                            "minimumBidPrice": 1.20,
                            "uninterruptablePrice": 1.89
                        }
                    }
                ]
            }
        })
        
        mock_session.post = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        resources = await connector.list_resources()
        
        assert len(resources) == 2
        assert resources[0].id == "NVIDIA RTX A4000"
        assert resources[0].name == "RTX A4000"
        assert resources[0].type == ResourceType.GPU
        assert resources[0].vram_gb == 16
        assert resources[0].available is True
    
    @pytest.mark.asyncio
    async def test_get_pricing(self, connector, mock_session):
        """Test getting pricing information."""
        connector._connected = True
        connector._session = mock_session
        
        # Mock pricing response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "data": {
                "gpuTypes": [
                    {
                        "id": "NVIDIA RTX A4000",
                        "displayName": "RTX A4000",
                        "lowestPrice": {
                            "minimumBidPrice": 0.30,
                            "uninterruptablePrice": 0.45
                        }
                    }
                ]
            }
        })
        
        mock_session.post = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        pricing = await connector.get_pricing("NVIDIA RTX A4000")
        
        assert pricing.resource_id == "NVIDIA RTX A4000"
        assert pricing.price_per_hour == 0.45
        assert pricing.currency == "USD"
        assert pricing.spot_available is True
        assert pricing.spot_price_per_hour == 0.30
    
    @pytest.mark.asyncio
    async def test_fetch_artifact_not_completed(self, connector, mock_session):
        """Test artifact fetch fails when job not completed."""
        connector._connected = True
        connector._session = mock_session
        
        # Mock job status as running
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "data": {
                "pod": {
                    "id": "pod123",
                    "desiredStatus": "RUNNING",
                    "runtime": {"uptimeInSeconds": 60}
                }
            }
        })
        
        mock_session.post = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with pytest.raises(RuntimeError, match="Job not completed"):
            await connector.fetch_artifact("pod123")
    
    @pytest.mark.asyncio
    async def test_validate_config(self, connector, training_config):
        """Test configuration validation."""
        # Valid config should pass
        assert connector.validate_config(training_config) is True
        
        # Invalid config should raise ValueError
        invalid_config = TrainingConfig(
            base_model="",  # Empty model
            model_source="huggingface",
            algorithm="lora",
            rank=16,
            alpha=32,
            dropout=0.1,
            target_modules=["q_proj"],
            dataset_path="/data/train.json",
        )
        
        with pytest.raises(ValueError, match="base_model is required"):
            connector.validate_config(invalid_config)
    
    def test_build_training_script(self, connector, training_config):
        """Test training script generation."""
        script = connector._build_training_script(training_config)
        
        # Verify script contains key elements
        assert "meta-llama/Llama-2-7b-hf" in script
        assert "r=16" in script  # rank parameter
        assert "lora_alpha=32" in script
        assert "lora_dropout=0.1" in script
        assert "load_in_4bit=true" in script  # quantization
        assert "per_device_train_batch_size=4" in script
        assert "num_train_epochs=3" in script


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
