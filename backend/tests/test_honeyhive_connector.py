"""
Tests for HoneyHive connector.

Tests the HoneyHive connector implementation including:
- Connection and authentication
- Dataset management (CRUD operations)
- Model battle creation and execution
- Result visualization
- Evaluation job management
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from plugins.connectors.honeyhive_connector import HoneyHiveConnector
from connectors.base import TrainingConfig, JobStatus


@pytest.fixture
def connector():
    """Create a HoneyHive connector instance."""
    return HoneyHiveConnector()


def create_async_context_manager(response):
    """Helper to create async context manager for mocked responses."""
    class AsyncContextManager:
        async def __aenter__(self):
            return response
        async def __aexit__(self, *args):
            return None
    return AsyncContextManager()


@pytest.fixture
def mock_session():
    """Create a mock aiohttp session."""
    session = AsyncMock()
    return session


@pytest.fixture
def training_config():
    """Create a sample training configuration."""
    return TrainingConfig(
        base_model="meta-llama/Llama-2-7b-hf",
        model_source="huggingface",
        algorithm="lora",
        rank=16,
        alpha=32,
        dropout=0.1,
        target_modules=["q_proj", "v_proj"],
        dataset_path="./data/train.json",
        validation_split=0.1,
    )


class TestConnection:
    """Test connection and authentication."""
    
    @pytest.mark.asyncio
    async def test_connect_success(self, connector, mock_session):
        """Test successful connection."""
        # Mock successful API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "projects": [{"id": "test-project-123", "name": "Test Project"}]
        })
        
        mock_session.get = Mock(return_value=create_async_context_manager(mock_response))
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await connector.connect({"api_key": "test-key"})
        
        assert result is True
        assert connector._connected is True
        assert connector._api_key == "test-key"
        assert connector._project_id == "test-project-123"
    
    @pytest.mark.asyncio
    async def test_connect_invalid_api_key(self, connector, mock_session):
        """Test connection with invalid API key."""
        # Mock 401 response
        mock_response = AsyncMock()
        mock_response.status = 401
        
        mock_session.get = Mock(return_value=create_async_context_manager(mock_response))
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with pytest.raises(ValueError, match="Invalid API key"):
                await connector.connect({"api_key": "invalid-key"})
    
    @pytest.mark.asyncio
    async def test_connect_missing_api_key(self, connector):
        """Test connection without API key."""
        with pytest.raises(ValueError, match="api_key is required"):
            await connector.connect({})
    
    @pytest.mark.asyncio
    async def test_verify_connection(self, connector, mock_session):
        """Test connection verification."""
        # Setup connected state
        connector._connected = True
        connector._session = mock_session
        
        # Mock successful verification
        mock_response = AsyncMock()
        mock_response.status = 200
        
        mock_session.get = Mock(return_value=create_async_context_manager(mock_response))
        
        result = await connector.verify_connection()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_disconnect(self, connector, mock_session):
        """Test disconnection."""
        connector._connected = True
        connector._session = mock_session
        connector._api_key = "test-key"
        
        result = await connector.disconnect()
        
        assert result is True
        assert connector._connected is False
        assert connector._api_key is None


class TestDatasetManagement:
    """Test dataset management operations."""
    
    @pytest.mark.asyncio
    async def test_create_dataset(self, connector, mock_session):
        """Test dataset creation."""
        connector._connected = True
        connector._session = mock_session
        connector._project_id = "test-project"
        
        # Mock successful creation
        mock_response = AsyncMock()
        mock_response.status = 201
        
        mock_session.post = Mock(return_value=create_async_context_manager(mock_response))
        
        dataset_data = [
            {"input": "test", "output": "result"}
        ]
        
        dataset_id = await connector.create_dataset(
            name="test_dataset",
            data=dataset_data,
            description="Test dataset"
        )
        
        assert dataset_id is not None
        assert dataset_id in connector._datasets
        assert connector._datasets[dataset_id]["name"] == "test_dataset"
        assert connector._datasets[dataset_id]["size"] == 1
    
    @pytest.mark.asyncio
    async def test_get_dataset(self, connector, mock_session):
        """Test dataset retrieval."""
        connector._connected = True
        connector._session = mock_session
        
        dataset_id = "test-dataset-123"
        
        # Mock successful retrieval
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "name": "test_dataset",
            "data": [{"input": "test", "output": "result"}],
            "size": 1
        })
        
        mock_session.get = Mock(return_value=create_async_context_manager(mock_response))
        
        dataset = await connector.get_dataset(dataset_id)
        
        assert dataset["name"] == "test_dataset"
        assert dataset["size"] == 1
        assert dataset_id in connector._datasets
    
    @pytest.mark.asyncio
    async def test_update_dataset(self, connector, mock_session):
        """Test dataset update."""
        connector._connected = True
        connector._session = mock_session
        
        dataset_id = "test-dataset-123"
        connector._datasets[dataset_id] = {
            "name": "test_dataset",
            "data": [],
            "size": 0
        }
        
        # Mock successful update
        mock_response = AsyncMock()
        mock_response.status = 200
        
        mock_session.patch = Mock(return_value=create_async_context_manager(mock_response))
        
        new_data = [{"input": "updated", "output": "result"}]
        result = await connector.update_dataset(dataset_id, data=new_data)
        
        assert result is True
        assert connector._datasets[dataset_id]["size"] == 1
    
    @pytest.mark.asyncio
    async def test_delete_dataset(self, connector, mock_session):
        """Test dataset deletion."""
        connector._connected = True
        connector._session = mock_session
        
        dataset_id = "test-dataset-123"
        connector._datasets[dataset_id] = {"name": "test_dataset"}
        
        # Mock successful deletion
        mock_response = AsyncMock()
        mock_response.status = 204
        
        mock_session.delete = Mock(return_value=create_async_context_manager(mock_response))
        
        result = await connector.delete_dataset(dataset_id)
        
        assert result is True
        assert dataset_id not in connector._datasets
    
    @pytest.mark.asyncio
    async def test_list_datasets(self, connector, mock_session):
        """Test listing datasets."""
        connector._connected = True
        connector._session = mock_session
        connector._project_id = "test-project"
        
        # Mock successful listing
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "datasets": [
                {"dataset_id": "ds1", "name": "Dataset 1"},
                {"dataset_id": "ds2", "name": "Dataset 2"}
            ]
        })
        
        mock_session.get = Mock(return_value=create_async_context_manager(mock_response))
        
        datasets = await connector.list_datasets()
        
        assert len(datasets) == 2
        assert "ds1" in connector._datasets
        assert "ds2" in connector._datasets


class TestModelBattles:
    """Test model battle functionality."""
    
    @pytest.mark.asyncio
    async def test_create_model_battle(self, connector, mock_session):
        """Test model battle creation."""
        connector._connected = True
        connector._session = mock_session
        connector._project_id = "test-project"
        
        # Mock successful creation
        mock_response = AsyncMock()
        mock_response.status = 201
        
        mock_session.post = Mock(return_value=create_async_context_manager(mock_response))
        
        battle_id = await connector.create_model_battle(
            name="Test Battle",
            model_a_id="model_a",
            model_b_id="model_b",
            dataset_id="dataset_123",
            metrics=["accuracy", "bleu"]
        )
        
        assert battle_id is not None
        assert battle_id in connector._battles
        assert connector._battles[battle_id]["name"] == "Test Battle"
        assert connector._battles[battle_id]["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_run_model_battle(self, connector, mock_session):
        """Test running a model battle."""
        connector._connected = True
        connector._session = mock_session
        
        battle_id = "battle-123"
        connector._battles[battle_id] = {
            "name": "Test Battle",
            "status": "pending"
        }
        
        # Mock successful battle execution
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "results": {
                "model_a": {"accuracy": 0.95, "bleu": 0.82},
                "model_b": {"accuracy": 0.93, "bleu": 0.85},
                "winner": "model_a"
            }
        })
        
        mock_session.post = Mock(return_value=create_async_context_manager(mock_response))
        
        model_a_outputs = ["output1", "output2"]
        model_b_outputs = ["output3", "output4"]
        
        results = await connector.run_model_battle(
            battle_id,
            model_a_outputs,
            model_b_outputs
        )
        
        assert results["winner"] == "model_a"
        assert connector._battles[battle_id]["status"] == "completed"
        assert connector._battles[battle_id]["results"] is not None
    
    @pytest.mark.asyncio
    async def test_get_battle_results(self, connector, mock_session):
        """Test getting battle results."""
        connector._connected = True
        connector._session = mock_session
        
        battle_id = "battle-123"
        connector._battles[battle_id] = {
            "name": "Test Battle",
            "results": {
                "model_a": {"accuracy": 0.95},
                "model_b": {"accuracy": 0.93},
                "winner": "model_a"
            }
        }
        
        results = await connector.get_battle_results(battle_id)
        
        assert results["winner"] == "model_a"
        assert results["model_a"]["accuracy"] == 0.95
    
    @pytest.mark.asyncio
    async def test_get_battle_visualization(self, connector, mock_session):
        """Test getting battle visualization data."""
        connector._connected = True
        connector._session = mock_session
        
        battle_id = "battle-123"
        connector._battles[battle_id] = {"name": "Test Battle"}
        
        # Mock successful visualization retrieval
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "visualization": {
                "type": "bar_chart",
                "data": [
                    {"model": "A", "accuracy": 0.95},
                    {"model": "B", "accuracy": 0.93}
                ]
            }
        })
        
        mock_session.get = Mock(return_value=create_async_context_manager(mock_response))
        
        viz_data = await connector.get_battle_visualization(
            battle_id,
            viz_type="comparison"
        )
        
        assert viz_data["type"] == "bar_chart"
        assert len(viz_data["data"]) == 2


class TestEvaluationJobs:
    """Test evaluation job management."""
    
    @pytest.mark.asyncio
    async def test_submit_job(self, connector, mock_session, training_config):
        """Test evaluation job submission."""
        connector._connected = True
        connector._session = mock_session
        connector._project_id = "test-project"
        
        # Mock successful job creation
        mock_response = AsyncMock()
        mock_response.status = 201
        
        mock_session.post = Mock(return_value=create_async_context_manager(mock_response))
        
        job_id = await connector.submit_job(training_config)
        
        assert job_id is not None
        assert job_id in connector._evaluations
        assert connector._evaluations[job_id]["status"] == JobStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_get_job_status(self, connector, mock_session):
        """Test getting job status."""
        connector._connected = True
        connector._session = mock_session
        
        job_id = "eval_20240101_120000"
        connector._evaluations[job_id] = {
            "eval_id": "eval-123",
            "status": JobStatus.RUNNING
        }
        
        status = await connector.get_job_status(job_id)
        assert status == JobStatus.RUNNING
    
    @pytest.mark.asyncio
    async def test_cancel_job(self, connector, mock_session):
        """Test job cancellation."""
        connector._connected = True
        connector._session = mock_session
        
        job_id = "eval_20240101_120000"
        connector._evaluations[job_id] = {
            "eval_id": "eval-123",
            "status": JobStatus.RUNNING
        }
        
        # Mock successful cancellation
        mock_response = AsyncMock()
        mock_response.status = 200
        
        mock_session.post = Mock(return_value=create_async_context_manager(mock_response))
        
        result = await connector.cancel_job(job_id)
        
        assert result is True
        assert connector._evaluations[job_id]["status"] == JobStatus.CANCELLED
    
    @pytest.mark.asyncio
    async def test_fetch_artifact(self, connector, mock_session):
        """Test artifact download."""
        connector._connected = True
        connector._session = mock_session
        
        job_id = "eval_20240101_120000"
        connector._evaluations[job_id] = {
            "eval_id": "eval-123"
        }
        
        # Mock successful download
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b'{"results": "data"}')
        
        mock_session.get = Mock(return_value=create_async_context_manager(mock_response))
        
        artifact = await connector.fetch_artifact(job_id)
        
        assert artifact == b'{"results": "data"}'


class TestUtilityMethods:
    """Test utility methods."""
    
    def test_get_required_credentials(self, connector):
        """Test getting required credentials."""
        creds = connector.get_required_credentials()
        assert "api_key" in creds
    
    def test_get_dashboard_url(self, connector):
        """Test getting dashboard URL."""
        job_id = "eval_20240101_120000"
        connector._evaluations[job_id] = {
            "eval_id": "eval-123",
            "project_id": "project-456"
        }
        
        url = connector.get_dashboard_url(job_id)
        assert "honeyhive.ai" in url
        assert "eval-123" in url
    
    def test_get_battle_url(self, connector):
        """Test getting battle URL."""
        battle_id = "battle-123"
        connector._project_id = "project-456"
        connector._battles[battle_id] = {"name": "Test Battle"}
        
        url = connector.get_battle_url(battle_id)
        assert "honeyhive.ai" in url
        assert "battle-123" in url
    
    @pytest.mark.asyncio
    async def test_list_resources(self, connector):
        """Test listing resources (should be empty)."""
        resources = await connector.list_resources()
        assert resources == []
    
    @pytest.mark.asyncio
    async def test_get_pricing(self, connector):
        """Test getting pricing (should raise error)."""
        with pytest.raises(ValueError, match="subscription-based pricing"):
            await connector.get_pricing("resource-123")


class TestErrorHandling:
    """Test error handling."""
    
    @pytest.mark.asyncio
    async def test_operation_without_connection(self, connector):
        """Test operations without being connected."""
        with pytest.raises(RuntimeError, match="Not connected"):
            await connector.submit_job(TrainingConfig(
                base_model="test",
                model_source="test",
                algorithm="lora",
                rank=8,
                alpha=16,
                dropout=0.1,
                target_modules=[]
            ))
    
    @pytest.mark.asyncio
    async def test_invalid_job_id(self, connector):
        """Test operations with invalid job ID."""
        connector._connected = True
        
        status = await connector.get_job_status("invalid-job-id")
        assert status == JobStatus.FAILED
    
    @pytest.mark.asyncio
    async def test_invalid_battle_id(self, connector):
        """Test operations with invalid battle ID."""
        connector._connected = True
        
        with pytest.raises(ValueError, match="not found"):
            await connector.get_battle_results("invalid-battle-id")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
