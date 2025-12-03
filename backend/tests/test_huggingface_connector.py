"""
Tests for HuggingFace Hub connector.

Tests the HuggingFace connector implementation including:
- Connection and authentication
- Model search and metadata fetching
- Model metadata caching
- Model download
- Adapter upload with model card generation
- License and compatibility checking
"""

import pytest
import asyncio
from pathlib import Path
import tempfile
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys

sys.path.append(str(Path(__file__).parent.parent))

from plugins.connectors.huggingface_connector import (
    HuggingFaceConnector,
    ModelMetadata,
    ModelCache,
)


class TestHuggingFaceConnector:
    """Test suite for HuggingFace connector."""
    
    @pytest.fixture
    def connector(self):
        """Create a connector instance with temporary cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = HuggingFaceConnector(cache_dir=Path(tmpdir))
            yield conn
            # Cleanup
            asyncio.run(conn.disconnect())
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock aiohttp session."""
        session = AsyncMock()
        return session
    
    def test_connector_metadata(self, connector):
        """Test connector has correct metadata."""
        assert connector.name == "huggingface"
        assert connector.display_name == "HuggingFace Hub"
        assert connector.supports_registry is True
        assert connector.supports_training is False
        assert connector.supports_inference is False
    
    def test_required_credentials(self, connector):
        """Test connector requires token credential."""
        required = connector.get_required_credentials()
        assert "token" in required
    
    @pytest.mark.asyncio
    async def test_connect_with_invalid_token_format(self, connector):
        """Test connection fails with invalid token format."""
        with pytest.raises(ValueError, match="Invalid HuggingFace token format"):
            await connector.connect({"token": "invalid_token"})
    
    @pytest.mark.asyncio
    async def test_connect_missing_token(self, connector):
        """Test connection fails without token."""
        with pytest.raises(ValueError, match="token is required"):
            await connector.connect({})
    
    @pytest.mark.asyncio
    async def test_connect_success(self, connector, mock_session):
        """Test successful connection."""
        # Mock successful API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"name": "test_user"})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        # Mock session.get to return the mock response
        mock_session.get = Mock(return_value=mock_response)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await connector.connect({"token": "hf_test_token_123"})
            assert result is True
            assert connector._connected is True
    
    @pytest.mark.asyncio
    async def test_disconnect(self, connector):
        """Test disconnection cleans up resources."""
        # Set up connected state
        connector._connected = True
        connector._token = "hf_test"
        connector._session = AsyncMock()
        
        result = await connector.disconnect()
        
        assert result is True
        assert connector._connected is False
        assert connector._token is None
        assert connector._session is None
    
    @pytest.mark.asyncio
    async def test_verify_connection_when_not_connected(self, connector):
        """Test verify_connection returns False when not connected."""
        result = await connector.verify_connection()
        assert result is False
    
    @pytest.mark.asyncio
    async def test_search_models_not_connected(self, connector):
        """Test search_models raises error when not connected."""
        with pytest.raises(RuntimeError, match="Not connected"):
            await connector.search_models()
    
    @pytest.mark.asyncio
    async def test_search_models_success(self, connector, mock_session):
        """Test successful model search."""
        # Set up connected state
        connector._connected = True
        connector._session = mock_session
        
        # Mock API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=[
            {
                "id": "meta-llama/Llama-2-7b-hf",
                "author": "meta-llama",
                "downloads": 1000000,
                "likes": 5000,
                "tags": ["text-generation", "pytorch"],
                "pipeline_tag": "text-generation",
                "library_name": "transformers",
                "license": "llama2",
                "createdAt": "2023-07-01T00:00:00Z",
                "lastModified": "2023-07-15T00:00:00Z",
                "siblings": [],
            }
        ])
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.get = Mock(return_value=mock_response)
        
        results = await connector.search_models(query="llama", limit=10)
        
        assert len(results) == 1
        assert results[0].model_id == "meta-llama/Llama-2-7b-hf"
        assert results[0].author == "meta-llama"
        assert results[0].downloads == 1000000
    
    @pytest.mark.asyncio
    async def test_get_model_metadata_from_cache(self, connector):
        """Test get_model_metadata returns cached data."""
        # Pre-populate cache
        metadata = ModelMetadata(
            model_id="test/model",
            author="test",
            downloads=100,
            likes=10,
            tags=["test"],
            pipeline_tag="text-generation",
            library_name="transformers",
            license="mit",
            model_size=1000,
            created_at="2023-01-01T00:00:00Z",
            last_modified="2023-01-02T00:00:00Z",
            siblings=[],
        )
        connector._cache.set(metadata)
        
        # Get metadata (should use cache)
        result = await connector.get_model_metadata("test/model", use_cache=True)
        
        assert result is not None
        assert result.model_id == "test/model"
        assert result.author == "test"
    
    @pytest.mark.asyncio
    async def test_get_model_metadata_not_in_cache_offline(self, connector):
        """Test get_model_metadata returns None when offline and not cached."""
        # Not connected, not in cache
        result = await connector.get_model_metadata("test/model", use_cache=True)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_model_metadata_fetch_from_api(self, connector, mock_session):
        """Test get_model_metadata fetches from API when not cached."""
        # Set up connected state
        connector._connected = True
        connector._session = mock_session
        
        # Mock API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "id": "test/model",
            "author": "test",
            "downloads": 100,
            "likes": 10,
            "tags": ["test"],
            "pipeline_tag": "text-generation",
            "library_name": "transformers",
            "license": "mit",
            "createdAt": "2023-01-01T00:00:00Z",
            "lastModified": "2023-01-02T00:00:00Z",
            "siblings": [],
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.get = Mock(return_value=mock_response)
        
        result = await connector.get_model_metadata("test/model", use_cache=False)
        
        assert result is not None
        assert result.model_id == "test/model"
        
        # Verify it was cached
        cached = connector._cache.get("test/model")
        assert cached is not None
    
    @pytest.mark.asyncio
    async def test_download_model_not_connected(self, connector):
        """Test download_model raises error when not connected."""
        with pytest.raises(RuntimeError, match="Not connected"):
            await connector.download_model("test/model")
    
    @pytest.mark.asyncio
    async def test_upload_artifact_not_connected(self, connector):
        """Test upload_artifact raises error when not connected."""
        with pytest.raises(RuntimeError, match="Not connected"):
            await connector.upload_artifact("/fake/path", {})
    
    @pytest.mark.asyncio
    async def test_upload_artifact_missing_repo_id(self, connector):
        """Test upload_artifact raises error without repo_id."""
        connector._connected = True
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="repo_id is required"):
                await connector.upload_artifact(tmpdir, {})
    
    @pytest.mark.asyncio
    async def test_upload_artifact_path_not_found(self, connector):
        """Test upload_artifact raises error for non-existent path."""
        connector._connected = True
        
        with pytest.raises(FileNotFoundError):
            await connector.upload_artifact("/nonexistent/path", {"repo_id": "test/model"})
    
    def test_generate_model_card(self, connector):
        """Test model card generation."""
        metadata = {
            "repo_id": "test/adapter",
            "base_model": "meta-llama/Llama-2-7b-hf",
            "dataset": "alpaca",
            "description": "Test adapter",
            "training_config": {
                "rank": 16,
                "alpha": 32,
                "learning_rate": 2e-4,
            },
            "metrics": {
                "loss": 0.5,
                "accuracy": 0.85,
            }
        }
        
        card = connector._generate_model_card(metadata)
        
        assert "test/adapter" in card
        assert "meta-llama/Llama-2-7b-hf" in card
        assert "alpaca" in card
        assert "Test adapter" in card
        assert "rank" in card
        assert "loss" in card
        assert "accuracy" in card
    
    @pytest.mark.asyncio
    async def test_check_license(self, connector):
        """Test license checking."""
        # Pre-populate cache with model
        metadata = ModelMetadata(
            model_id="test/model",
            author="test",
            downloads=100,
            likes=10,
            tags=[],
            pipeline_tag=None,
            library_name=None,
            license="apache-2.0",
            model_size=0,
            created_at="2023-01-01T00:00:00Z",
            last_modified="2023-01-02T00:00:00Z",
            siblings=[],
        )
        connector._cache.set(metadata)
        
        license_info = await connector.check_license("test/model")
        assert license_info == "apache-2.0"
    
    @pytest.mark.asyncio
    async def test_check_compatibility_success(self, connector):
        """Test compatibility checking for compatible model."""
        # Pre-populate cache with compatible model
        metadata = ModelMetadata(
            model_id="test/model",
            author="test",
            downloads=100,
            likes=10,
            tags=[],
            pipeline_tag=None,
            library_name="transformers",
            license=None,
            model_size=0,
            created_at="2023-01-01T00:00:00Z",
            last_modified="2023-01-02T00:00:00Z",
            siblings=[
                {"rfilename": "config.json"},
                {"rfilename": "model.safetensors"},
            ],
        )
        connector._cache.set(metadata)
        
        is_compatible = await connector.check_compatibility(
            "test/model",
            required_library="transformers"
        )
        assert is_compatible is True
    
    @pytest.mark.asyncio
    async def test_check_compatibility_wrong_library(self, connector):
        """Test compatibility checking fails for wrong library."""
        # Pre-populate cache with model using different library
        metadata = ModelMetadata(
            model_id="test/model",
            author="test",
            downloads=100,
            likes=10,
            tags=[],
            pipeline_tag=None,
            library_name="diffusers",
            license=None,
            model_size=0,
            created_at="2023-01-01T00:00:00Z",
            last_modified="2023-01-02T00:00:00Z",
            siblings=[
                {"rfilename": "config.json"},
                {"rfilename": "model.safetensors"},
            ],
        )
        connector._cache.set(metadata)
        
        is_compatible = await connector.check_compatibility(
            "test/model",
            required_library="transformers"
        )
        assert is_compatible is False
    
    @pytest.mark.asyncio
    async def test_check_compatibility_missing_files(self, connector):
        """Test compatibility checking fails for missing required files."""
        # Pre-populate cache with model missing config
        metadata = ModelMetadata(
            model_id="test/model",
            author="test",
            downloads=100,
            likes=10,
            tags=[],
            pipeline_tag=None,
            library_name="transformers",
            license=None,
            model_size=0,
            created_at="2023-01-01T00:00:00Z",
            last_modified="2023-01-02T00:00:00Z",
            siblings=[
                {"rfilename": "model.safetensors"},
            ],
        )
        connector._cache.set(metadata)
        
        is_compatible = await connector.check_compatibility("test/model")
        assert is_compatible is False
    
    @pytest.mark.asyncio
    async def test_unsupported_training_methods(self, connector):
        """Test that training-related methods raise NotImplementedError."""
        from connectors.base import TrainingConfig
        
        config = TrainingConfig(
            base_model="test/model",
            model_source="huggingface",
            algorithm="lora",
            rank=16,
            alpha=32,
            dropout=0.1,
            target_modules=["q_proj", "v_proj"],
        )
        
        with pytest.raises(NotImplementedError):
            await connector.submit_job(config)
        
        with pytest.raises(NotImplementedError):
            await connector.get_job_status("job_id")
        
        with pytest.raises(NotImplementedError):
            await connector.cancel_job("job_id")
        
        with pytest.raises(NotImplementedError):
            async for _ in connector.stream_logs("job_id"):
                pass
        
        with pytest.raises(NotImplementedError):
            await connector.fetch_artifact("job_id")
        
        with pytest.raises(NotImplementedError):
            await connector.get_pricing("resource_id")
    
    @pytest.mark.asyncio
    async def test_list_resources_returns_empty(self, connector):
        """Test list_resources returns empty list for registry connector."""
        resources = await connector.list_resources()
        assert resources == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
