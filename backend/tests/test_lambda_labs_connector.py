"""
Tests for Lambda Labs Connector

Tests the Lambda Labs connector implementation including:
- Connection and authentication
- Instance provisioning
- Job submission and monitoring
- SSH-based log streaming
- Artifact download via SCP
- Pricing and availability queries
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from plugins.connectors.lambda_labs_connector import LambdaLabsConnector
from connectors.base import (
    TrainingConfig,
    JobStatus,
    ResourceType,
)


@pytest.fixture
def connector():
    """Create a Lambda Labs connector instance."""
    return LambdaLabsConnector()


@pytest.fixture
def mock_session():
    """Create a mock aiohttp session."""
    session = AsyncMock()
    return session


@pytest.fixture
def sample_config():
    """Create a sample training configuration."""
    return TrainingConfig(
        base_model="unsloth/llama-2-7b-bnb-4bit",
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
        provider="lambda_labs",
        resource_id="gpu_1x_a100",
        dataset_path="/data/train.json",
        validation_split=0.1,
        project_name="test-project",
        output_dir="/workspace/output",
        checkpoint_steps=500,
    )


class TestLambdaLabsConnectorMetadata:
    """Test connector metadata and configuration."""
    
    def test_connector_metadata(self, connector):
        """Test that connector has correct metadata."""
        assert connector.name == "lambda_labs"
        assert connector.display_name == "Lambda Labs"
        assert "H100/A100" in connector.description
        assert connector.version == "1.0.0"
    
    def test_connector_features(self, connector):
        """Test that connector declares correct features."""
        assert connector.supports_training is True
        assert connector.supports_inference is True
        assert connector.supports_registry is False
        assert connector.supports_tracking is False
    
    def test_required_credentials(self, connector):
        """Test that connector requires correct credentials."""
        required = connector.get_required_credentials()
        assert "api_key" in required


class TestLambdaLabsConnection:
    """Test connection and authentication."""
    
    @pytest.mark.asyncio
    async def test_connect_success(self, connector, mock_session):
        """Test successful connection."""
        # Mock successful API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "data": {
                "gpu_1x_a100": {
                    "instance_type": {
                        "name": "gpu_1x_a100",
                        "description": "1x A100 (40 GB)",
                        "price_cents_per_hour": 110
                    }
                }
            }
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.get = Mock(return_value=mock_response)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await connector.connect({"api_key": "test_key"})
        
        assert result is True
        assert connector._connected is True
        assert connector._api_key == "test_key"
    
    @pytest.mark.asyncio
    async def test_connect_invalid_api_key(self, connector, mock_session):
        """Test connection with invalid API key."""
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
        # Setup connected state
        connector._connected = True
        connector._session = mock_session
        connector._api_key = "test_key"
        
        # Mock SSH clients
        mock_ssh = Mock()
        connector._ssh_clients = {"instance_1": mock_ssh}
        
        result = await connector.disconnect()
        
        assert result is True
        assert connector._connected is False
        assert connector._api_key is None
        assert len(connector._ssh_clients) == 0
        mock_ssh.close.assert_called_once()
    
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


class TestLambdaLabsJobSubmission:
    """Test job submission and management."""
    
    @pytest.mark.asyncio
    async def test_submit_job_success(self, connector, mock_session, sample_config):
        """Test successful job submission."""
        connector._connected = True
        connector._session = mock_session
        
        # Mock launch response
        launch_response = AsyncMock()
        launch_response.status = 200
        launch_response.json = AsyncMock(return_value={
            "data": {
                "instance_ids": ["instance_123"]
            }
        })
        launch_response.__aenter__ = AsyncMock(return_value=launch_response)
        launch_response.__aexit__ = AsyncMock(return_value=None)
        
        # Mock instance info response
        info_response = AsyncMock()
        info_response.status = 200
        info_response.json = AsyncMock(return_value={
            "data": {
                "id": "instance_123",
                "status": "active",
                "ip": "192.168.1.100"
            }
        })
        info_response.__aenter__ = AsyncMock(return_value=info_response)
        info_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.post = Mock(return_value=launch_response)
        mock_session.get = Mock(return_value=info_response)
        
        # Mock SSH setup
        with patch.object(connector, '_setup_and_start_training', new_callable=AsyncMock):
            with patch.object(connector, '_wait_for_instance_active', new_callable=AsyncMock):
                job_id = await connector.submit_job(sample_config)
        
        assert job_id == "instance_123"
        assert job_id in connector._jobs
        assert connector._jobs[job_id]["config"] == sample_config
    
    @pytest.mark.asyncio
    async def test_submit_job_not_connected(self, connector, sample_config):
        """Test job submission when not connected."""
        with pytest.raises(RuntimeError, match="Not connected"):
            await connector.submit_job(sample_config)
    
    @pytest.mark.asyncio
    async def test_submit_job_invalid_config(self, connector, sample_config):
        """Test job submission with invalid configuration."""
        connector._connected = True
        
        # Make config invalid
        sample_config.base_model = ""
        
        with pytest.raises(ValueError):
            await connector.submit_job(sample_config)
    
    @pytest.mark.asyncio
    async def test_get_job_status_running(self, connector, mock_session):
        """Test getting job status for running job."""
        connector._connected = True
        connector._session = mock_session
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "data": {
                "id": "instance_123",
                "status": "active"
            }
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.get = Mock(return_value=mock_response)
        
        status = await connector.get_job_status("instance_123")
        assert status == JobStatus.RUNNING
    
    @pytest.mark.asyncio
    async def test_get_job_status_pending(self, connector, mock_session):
        """Test getting job status for pending job."""
        connector._connected = True
        connector._session = mock_session
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "data": {
                "id": "instance_123",
                "status": "booting"
            }
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.get = Mock(return_value=mock_response)
        
        status = await connector.get_job_status("instance_123")
        assert status == JobStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_cancel_job_success(self, connector, mock_session):
        """Test successful job cancellation."""
        connector._connected = True
        connector._session = mock_session
        
        # Setup job with SSH client
        mock_ssh = Mock()
        connector._ssh_clients = {"instance_123": mock_ssh}
        connector._jobs = {"instance_123": {"status": JobStatus.RUNNING}}
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.post = Mock(return_value=mock_response)
        
        result = await connector.cancel_job("instance_123")
        
        assert result is True
        assert "instance_123" not in connector._ssh_clients
        assert connector._jobs["instance_123"]["status"] == JobStatus.CANCELLED
        mock_ssh.close.assert_called_once()


class TestLambdaLabsLogStreaming:
    """Test SSH-based log streaming."""
    
    @pytest.mark.asyncio
    async def test_stream_logs_with_ssh_client(self, connector):
        """Test log streaming with existing SSH client."""
        connector._connected = True
        
        # Mock SSH client
        mock_ssh = Mock()
        mock_stdout = Mock()
        mock_stdout.readline = Mock(side_effect=[
            "Log line 1\n",
            "Log line 2\n",
            "Training complete\n",
            None  # End of stream
        ])
        
        mock_ssh.exec_command = Mock(return_value=(None, mock_stdout, None))
        connector._ssh_clients = {"instance_123": mock_ssh}
        connector._jobs = {"instance_123": {"status": JobStatus.RUNNING}}
        
        # Mock get_job_status to return completed
        with patch.object(connector, 'get_job_status', new_callable=AsyncMock) as mock_status:
            mock_status.return_value = JobStatus.COMPLETED
            
            logs = []
            async for log in connector.stream_logs("instance_123"):
                logs.append(log)
        
        assert len(logs) == 3
        assert "Log line 1" in logs[0]
        assert "Log line 2" in logs[1]
        assert "Training complete" in logs[2]
    
    @pytest.mark.asyncio
    async def test_stream_logs_no_ssh_client(self, connector):
        """Test log streaming without SSH client."""
        connector._connected = True
        connector._jobs = {}
        
        logs = []
        async for log in connector.stream_logs("instance_123"):
            logs.append(log)
            break  # Just get first error message
        
        assert len(logs) > 0
        assert "Error" in logs[0]


class TestLambdaLabsArtifacts:
    """Test artifact download via SCP."""
    
    @pytest.mark.asyncio
    async def test_fetch_artifact_success(self, connector, sample_config):
        """Test successful artifact download."""
        connector._connected = True
        
        # Setup job info
        connector._jobs = {
            "instance_123": {
                "config": sample_config,
                "status": JobStatus.COMPLETED,
                "ip_address": "192.168.1.100"
            }
        }
        
        # Mock SSH client
        mock_ssh = Mock()
        mock_stdout = Mock()
        mock_stdout.channel.recv_exit_status = Mock(return_value=0)
        mock_ssh.exec_command = Mock(return_value=(None, mock_stdout, Mock()))
        
        # Mock SCP client
        mock_scp = Mock()
        mock_scp.get = Mock()
        
        connector._ssh_clients = {"instance_123": mock_ssh}
        
        with patch.object(connector, 'get_job_status', new_callable=AsyncMock) as mock_status:
            mock_status.return_value = JobStatus.COMPLETED
            
            with patch('scp.SCPClient', return_value=mock_scp):
                artifact = await connector.fetch_artifact("instance_123")
        
        assert artifact is not None
        mock_scp.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fetch_artifact_not_completed(self, connector):
        """Test artifact download when job not completed."""
        connector._connected = True
        
        with patch.object(connector, 'get_job_status', new_callable=AsyncMock) as mock_status:
            mock_status.return_value = JobStatus.PENDING
            
            with pytest.raises(RuntimeError, match="not ready"):
                await connector.fetch_artifact("instance_123")
    
    @pytest.mark.asyncio
    async def test_upload_artifact(self, connector):
        """Test artifact upload (placeholder implementation)."""
        connector._connected = True
        
        # Create temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test data")
            temp_path = f.name
        
        try:
            result = await connector.upload_artifact(temp_path, {"name": "test"})
            assert "lambda-labs://" in result
        finally:
            Path(temp_path).unlink()


class TestLambdaLabsResources:
    """Test resource listing and pricing."""
    
    @pytest.mark.asyncio
    async def test_list_resources_success(self, connector, mock_session):
        """Test listing available resources."""
        connector._connected = True
        connector._session = mock_session
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "data": {
                "gpu_1x_a100": {
                    "instance_type": {
                        "name": "gpu_1x_a100",
                        "description": "1x A100 (40 GB)",
                        "price_cents_per_hour": 110,
                        "specs": {
                            "vcpus": 30,
                            "memory_gib": 200
                        }
                    },
                    "regions_with_capacity_available": ["us-west-2"]
                },
                "gpu_1x_h100": {
                    "instance_type": {
                        "name": "gpu_1x_h100",
                        "description": "1x H100 (80 GB)",
                        "price_cents_per_hour": 249,
                        "specs": {
                            "vcpus": 52,
                            "memory_gib": 200
                        }
                    },
                    "regions_with_capacity_available": ["us-west-2"]
                }
            }
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.get = Mock(return_value=mock_response)
        
        resources = await connector.list_resources()
        
        assert len(resources) == 2
        assert all(r.type == ResourceType.GPU for r in resources)
        assert any("A100" in r.gpu_type for r in resources)
        assert any("H100" in r.gpu_type for r in resources)
    
    @pytest.mark.asyncio
    async def test_list_resources_not_connected(self, connector):
        """Test listing resources when not connected."""
        with pytest.raises(RuntimeError, match="Not connected"):
            await connector.list_resources()
    
    @pytest.mark.asyncio
    async def test_get_pricing_success(self, connector, mock_session):
        """Test getting pricing information."""
        connector._connected = True
        connector._session = mock_session
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "data": {
                "gpu_1x_a100": {
                    "instance_type": {
                        "name": "gpu_1x_a100",
                        "description": "1x A100 (40 GB)",
                        "price_cents_per_hour": 110
                    }
                }
            }
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.get = Mock(return_value=mock_response)
        
        pricing = await connector.get_pricing("gpu_1x_a100")
        
        assert pricing.resource_id == "gpu_1x_a100"
        assert pricing.price_per_hour == 1.10  # 110 cents = $1.10
        assert pricing.currency == "USD"
        assert pricing.billing_increment_seconds == 3600  # Hourly billing
        assert pricing.spot_available is False
    
    @pytest.mark.asyncio
    async def test_get_pricing_invalid_resource(self, connector, mock_session):
        """Test getting pricing for invalid resource."""
        connector._connected = True
        connector._session = mock_session
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "data": {}
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.get = Mock(return_value=mock_response)
        
        with pytest.raises(ValueError, match="Invalid resource ID"):
            await connector.get_pricing("invalid_resource")


class TestLambdaLabsTrainingScript:
    """Test training script generation."""
    
    def test_build_training_script(self, connector, sample_config):
        """Test that training script is generated correctly."""
        script = connector._build_training_script(sample_config)
        
        # Check key components are in script
        assert sample_config.base_model in script
        assert str(sample_config.rank) in script
        assert str(sample_config.alpha) in script
        assert str(sample_config.dropout) in script
        assert str(sample_config.batch_size) in script
        assert str(sample_config.num_epochs) in script
        assert str(sample_config.learning_rate) in script
        
        # Check for required imports
        assert "from unsloth import FastLanguageModel" in script
        assert "from datasets import load_dataset" in script
        assert "from trl import SFTTrainer" in script
        
        # Check for training steps
        assert "trainer.train()" in script
        assert "save_pretrained" in script


class TestLambdaLabsConfigValidation:
    """Test configuration validation."""
    
    def test_validate_config_success(self, connector, sample_config):
        """Test validation of valid configuration."""
        result = connector.validate_config(sample_config)
        assert result is True
    
    def test_validate_config_missing_base_model(self, connector, sample_config):
        """Test validation fails with missing base model."""
        sample_config.base_model = ""
        
        with pytest.raises(ValueError, match="base_model is required"):
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
