"""
Tests for Ollama connector.

Tests cover:
- Connection to local Ollama instance
- Model library browsing
- Modelfile generation
- Local model packaging
- Model push to Ollama library
"""

import pytest
import pytest_asyncio
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys

sys.path.append(str(Path(__file__).parent.parent))

from plugins.connectors.ollama_connector import (
    OllamaConnector,
    OllamaModelMetadata,
    OllamaCache,
)
from connectors.base import TrainingConfig


def create_mock_response(status=200, json_data=None, text_data=""):
    """Helper to create a mock aiohttp response."""
    mock_response = AsyncMock()
    mock_response.status = status
    mock_response.json = AsyncMock(return_value=json_data or {})
    mock_response.text = AsyncMock(return_value=text_data)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    return mock_response


class TestOllamaConnector:
    """Test suite for OllamaConnector."""
    
    @pytest_asyncio.fixture
    async def connector(self):
        """Create a connector instance for testing."""
        conn = OllamaConnector()
        yield conn
        # Cleanup
        if conn._session:
            await conn.disconnect()
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock aiohttp session."""
        session = AsyncMock()
        session.close = AsyncMock()
        return session
    
    @pytest.mark.asyncio
    async def test_connect_success(self, connector, mock_session):
        """Test successful connection to Ollama."""
        mock_response = create_mock_response(200, {"models": []})
        mock_session.get = AsyncMock(return_value=mock_response)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await connector.connect({})
            assert result is True
            assert connector._connected is True
    
    @pytest.mark.asyncio
    async def test_connect_with_custom_base_url(self, connector, mock_session):
        """Test connection with custom base URL."""
        custom_url = "http://custom-host:11434"
        
        mock_response = create_mock_response(200, {"models": []})
        mock_session.get = AsyncMock(return_value=mock_response)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await connector.connect({"base_url": custom_url})
            assert result is True
            assert connector._base_url == custom_url
    
    @pytest.mark.asyncio
    async def test_connect_failure(self, connector):
        """Test connection failure when Ollama is not running."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.get.side_effect = Exception("Connection refused")
            mock_session_class.return_value = mock_session
            
            with pytest.raises(ConnectionError, match="Failed to connect to Ollama"):
                await connector.connect({})
    
    @pytest.mark.asyncio
    async def test_disconnect(self, connector, mock_session):
        """Test disconnection."""
        connector._session = mock_session
        connector._connected = True
        
        result = await connector.disconnect()
        assert result is True
        assert connector._connected is False
        assert connector._session is None
        mock_session.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_verify_connection_success(self, connector, mock_session):
        """Test connection verification when connected."""
        connector._session = mock_session
        connector._connected = True
        
        mock_response = create_mock_response(200)
        mock_session.get = AsyncMock(return_value=mock_response)
        
        result = await connector.verify_connection()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_connection_not_connected(self, connector):
        """Test connection verification when not connected."""
        result = await connector.verify_connection()
        assert result is False
    
    @pytest.mark.asyncio
    async def test_list_models(self, connector, mock_session):
        """Test listing models from Ollama."""
        connector._session = mock_session
        connector._connected = True
        
        mock_models = {
            "models": [
                {
                    "name": "llama2:7b",
                    "model": "llama2:7b",
                    "modified_at": "2024-01-01T00:00:00Z",
                    "size": 3825819519,
                    "digest": "abc123",
                    "details": {
                        "format": "gguf",
                        "family": "llama",
                        "parameter_size": "7B",
                    }
                },
                {
                    "name": "mistral:7b",
                    "model": "mistral:7b",
                    "modified_at": "2024-01-02T00:00:00Z",
                    "size": 4109865159,
                    "digest": "def456",
                    "details": {
                        "format": "gguf",
                        "family": "mistral",
                        "parameter_size": "7B",
                    }
                }
            ]
        }
        
        mock_response = create_mock_response(200, mock_models)
        mock_session.get = AsyncMock(return_value=mock_response)
        
        models = await connector.list_models()
        
        assert len(models) == 2
        assert models[0].name == "llama2:7b"
        assert models[0].size == 3825819519
        assert models[1].name == "mistral:7b"
    
    @pytest.mark.asyncio
    async def test_get_model_metadata(self, connector, mock_session):
        """Test getting metadata for a specific model."""
        connector._session = mock_session
        connector._connected = True
        
        mock_models = {
            "models": [
                {
                    "name": "llama2:7b",
                    "model": "llama2:7b",
                    "modified_at": "2024-01-01T00:00:00Z",
                    "size": 3825819519,
                    "digest": "abc123",
                    "details": {}
                }
            ]
        }
        
        mock_response = create_mock_response(200, mock_models)
        mock_session.get = AsyncMock(return_value=mock_response)
        
        metadata = await connector.get_model_metadata("llama2:7b", use_cache=False)
        
        assert metadata is not None
        assert metadata.name == "llama2:7b"
        assert metadata.size == 3825819519
    
    @pytest.mark.asyncio
    async def test_get_model_metadata_not_found(self, connector, mock_session):
        """Test getting metadata for non-existent model."""
        connector._session = mock_session
        connector._connected = True
        
        mock_response = create_mock_response(200, {"models": []})
        mock_session.get = AsyncMock(return_value=mock_response)
        
        metadata = await connector.get_model_metadata("nonexistent:7b", use_cache=False)
        
        assert metadata is None
    
    def test_generate_modelfile_basic(self, connector):
        """Test basic Modelfile generation."""
        modelfile = connector.generate_modelfile(
            base_model="llama2:7b"
        )
        
        assert "FROM llama2:7b" in modelfile
        assert modelfile.strip().startswith("FROM llama2:7b")
    
    def test_generate_modelfile_with_adapter(self, connector):
        """Test Modelfile generation with adapter."""
        modelfile = connector.generate_modelfile(
            base_model="llama2:7b",
            adapter_path="/path/to/adapter.safetensors"
        )
        
        assert "FROM llama2:7b" in modelfile
        assert "ADAPTER /path/to/adapter.safetensors" in modelfile
    
    def test_generate_modelfile_with_system_prompt(self, connector):
        """Test Modelfile generation with system prompt."""
        system_prompt = "You are a helpful assistant."
        
        modelfile = connector.generate_modelfile(
            base_model="llama2:7b",
            system_prompt=system_prompt
        )
        
        assert "FROM llama2:7b" in modelfile
        assert "SYSTEM" in modelfile
        assert system_prompt in modelfile
    
    def test_generate_modelfile_with_template(self, connector):
        """Test Modelfile generation with template."""
        template = "{{ .System }}\n{{ .Prompt }}"
        
        modelfile = connector.generate_modelfile(
            base_model="llama2:7b",
            template=template
        )
        
        assert "FROM llama2:7b" in modelfile
        assert "TEMPLATE" in modelfile
    
    def test_generate_modelfile_with_parameters(self, connector):
        """Test Modelfile generation with parameters."""
        parameters = {
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
        }
        
        modelfile = connector.generate_modelfile(
            base_model="llama2:7b",
            parameters=parameters
        )
        
        assert "FROM llama2:7b" in modelfile
        assert "PARAMETER temperature 0.7" in modelfile
        assert "PARAMETER top_p 0.9" in modelfile
        assert "PARAMETER top_k 40" in modelfile
    
    def test_generate_modelfile_complete(self, connector):
        """Test Modelfile generation with all options."""
        modelfile = connector.generate_modelfile(
            base_model="llama2:7b",
            adapter_path="/path/to/adapter.safetensors",
            system_prompt="You are a helpful assistant.",
            template="{{ .System }}\n{{ .Prompt }}",
            parameters={"temperature": 0.7}
        )
        
        assert "FROM llama2:7b" in modelfile
        assert "ADAPTER /path/to/adapter.safetensors" in modelfile
        assert "SYSTEM" in modelfile
        assert "TEMPLATE" in modelfile
        assert "PARAMETER temperature 0.7" in modelfile
    
    @pytest.mark.asyncio
    async def test_create_model(self, connector, mock_session):
        """Test creating a model from Modelfile."""
        connector._session = mock_session
        connector._connected = True
        
        mock_response = create_mock_response(200)
        mock_session.post = AsyncMock(return_value=mock_response)
        
        modelfile = "FROM llama2:7b\nSYSTEM You are helpful."
        
        result = await connector.create_model(
            name="custom-model",
            modelfile=modelfile,
            stream=False
        )
        
        assert result is True
        mock_session.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_model(self, connector, mock_session):
        """Test deleting a model."""
        connector._session = mock_session
        connector._connected = True
        
        mock_response = create_mock_response(200)
        mock_session.delete = AsyncMock(return_value=mock_response)
        
        result = await connector.delete_model("custom-model")
        
        assert result is True
        mock_session.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_pull_model(self, connector, mock_session):
        """Test pulling a model from Ollama library."""
        connector._session = mock_session
        connector._connected = True
        
        mock_response = create_mock_response(200)
        mock_session.post = AsyncMock(return_value=mock_response)
        
        result = await connector.pull_model("llama2:7b", stream=False)
        
        assert result is True
        mock_session.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_push_model(self, connector, mock_session):
        """Test pushing a model to Ollama library."""
        connector._session = mock_session
        connector._connected = True
        
        mock_response = create_mock_response(200)
        mock_session.post = AsyncMock(return_value=mock_response)
        
        result = await connector.push_model("custom-model", stream=False)
        
        assert result is True
        mock_session.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate(self, connector, mock_session):
        """Test text generation."""
        connector._session = mock_session
        connector._connected = True
        
        mock_response = create_mock_response(200, {
            "response": "Hello! How can I help you today?"
        })
        mock_session.post = AsyncMock(return_value=mock_response)
        
        response = await connector.generate(
            model="llama2:7b",
            prompt="Hello",
            stream=False
        )
        
        assert response == "Hello! How can I help you today?"
            model="llama2:7b",
            prompt="Hello",
            stream=False
        )
        
        assert response == "Hello! How can I help you today?"
    
    @pytest.mark.asyncio
    async def test_upload_artifact(self, connector, mock_session, tmp_path):
        """Test uploading an adapter as Ollama model."""
        connector._session = mock_session
        connector._connected = True
        
        # Create a temporary adapter file
        adapter_file = tmp_path / "adapter.safetensors"
        adapter_file.write_text("fake adapter data")
        
        # Mock create_model response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_session.post = AsyncMock(return_value=mock_response)
        
        metadata = {
            "name": "custom-model",
            "base_model": "llama2:7b",
            "system_prompt": "You are helpful.",
            "push": False,
        }
        
        result = await connector.upload_artifact(str(adapter_file), metadata)
        
        assert result == "custom-model"
        # Should have called create_model
        assert mock_session.post.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_upload_artifact_with_push(self, connector, mock_session, tmp_path):
        """Test uploading and pushing an adapter."""
        connector._session = mock_session
        connector._connected = True
        
        # Create a temporary adapter file
        adapter_file = tmp_path / "adapter.safetensors"
        adapter_file.write_text("fake adapter data")
        
        # Mock responses
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_session.post = AsyncMock(return_value=mock_response)
        
        metadata = {
            "name": "custom-model",
            "base_model": "llama2:7b",
            "push": True,
        }
        
        result = await connector.upload_artifact(str(adapter_file), metadata)
        
        assert result == "custom-model"
        # Should have called create_model and push_model
        assert mock_session.post.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_upload_artifact_missing_file(self, connector):
        """Test uploading with non-existent file."""
        connector._connected = True
        
        metadata = {
            "name": "custom-model",
            "base_model": "llama2:7b",
        }
        
        with pytest.raises(FileNotFoundError):
            await connector.upload_artifact("/nonexistent/path", metadata)
    
    @pytest.mark.asyncio
    async def test_upload_artifact_missing_name(self, connector, tmp_path):
        """Test uploading without model name."""
        connector._connected = True
        
        adapter_file = tmp_path / "adapter.safetensors"
        adapter_file.write_text("fake adapter data")
        
        metadata = {
            "base_model": "llama2:7b",
        }
        
        with pytest.raises(ValueError, match="name is required"):
            await connector.upload_artifact(str(adapter_file), metadata)
    
    @pytest.mark.asyncio
    async def test_list_resources(self, connector):
        """Test listing local resources."""
        resources = await connector.list_resources()
        
        assert len(resources) == 1
        assert resources[0].id == "local"
        assert resources[0].name == "Local Machine"
    
    @pytest.mark.asyncio
    async def test_get_pricing(self, connector):
        """Test getting pricing (should be free for local)."""
        pricing = await connector.get_pricing("local")
        
        assert pricing.price_per_hour == 0.0
        assert pricing.currency == "USD"
    
    def test_get_required_credentials(self, connector):
        """Test getting required credentials."""
        creds = connector.get_required_credentials()
        assert creds == []
    
    @pytest.mark.asyncio
    async def test_not_implemented_methods(self, connector):
        """Test that training-related methods raise NotImplementedError."""
        config = TrainingConfig(
            base_model="llama2:7b",
            model_source="ollama",
            algorithm="lora",
            rank=8,
            alpha=16,
            dropout=0.1,
            target_modules=["q_proj", "v_proj"],
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


class TestOllamaCache:
    """Test suite for OllamaCache."""
    
    @pytest.fixture
    def cache(self, tmp_path):
        """Create a cache instance for testing."""
        cache_dir = tmp_path / "ollama_cache"
        return OllamaCache(cache_dir)
    
    @pytest.fixture
    def sample_metadata(self):
        """Create sample model metadata."""
        return OllamaModelMetadata(
            name="llama2:7b",
            model="llama2:7b",
            modified_at="2024-01-01T00:00:00Z",
            size=3825819519,
            digest="abc123",
            details={"format": "gguf"},
        )
    
    def test_cache_set_and_get(self, cache, sample_metadata):
        """Test caching and retrieving metadata."""
        cache.set(sample_metadata)
        
        retrieved = cache.get("llama2:7b")
        assert retrieved is not None
        assert retrieved.name == "llama2:7b"
        assert retrieved.size == 3825819519
    
    def test_cache_get_nonexistent(self, cache):
        """Test retrieving non-existent metadata."""
        retrieved = cache.get("nonexistent:7b")
        assert retrieved is None
    
    def test_cache_remove(self, cache, sample_metadata):
        """Test removing metadata from cache."""
        cache.set(sample_metadata)
        assert cache.get("llama2:7b") is not None
        
        cache.remove("llama2:7b")
        assert cache.get("llama2:7b") is None
    
    def test_cache_clear(self, cache, sample_metadata):
        """Test clearing all cache."""
        cache.set(sample_metadata)
        assert cache.get("llama2:7b") is not None
        
        cache.clear()
        assert cache.get("llama2:7b") is None
    
    def test_cache_persistence(self, tmp_path, sample_metadata):
        """Test that cache persists across instances."""
        cache_dir = tmp_path / "ollama_cache"
        
        # Create cache and add metadata
        cache1 = OllamaCache(cache_dir)
        cache1.set(sample_metadata)
        
        # Create new cache instance (should load from disk)
        cache2 = OllamaCache(cache_dir)
        retrieved = cache2.get("llama2:7b")
        
        assert retrieved is not None
        assert retrieved.name == "llama2:7b"
    
    def test_cache_expiry(self, cache, sample_metadata):
        """Test cache expiry."""
        # Set metadata with expired timestamp
        from datetime import datetime, timedelta
        sample_metadata.cached_at = datetime.now() - timedelta(hours=25)
        
        cache.set(sample_metadata)
        
        # Should return None due to expiry (default TTL is 24 hours)
        retrieved = cache.get("llama2:7b", ttl_hours=24)
        assert retrieved is None


class TestOllamaModelMetadata:
    """Test suite for OllamaModelMetadata."""
    
    def test_to_dict(self):
        """Test converting metadata to dictionary."""
        metadata = OllamaModelMetadata(
            name="llama2:7b",
            model="llama2:7b",
            modified_at="2024-01-01T00:00:00Z",
            size=3825819519,
            digest="abc123",
            details={"format": "gguf"},
        )
        
        data = metadata.to_dict()
        
        assert data["name"] == "llama2:7b"
        assert data["size"] == 3825819519
        assert "cached_at" in data
    
    def test_from_dict(self):
        """Test creating metadata from dictionary."""
        data = {
            "name": "llama2:7b",
            "model": "llama2:7b",
            "modified_at": "2024-01-01T00:00:00Z",
            "size": 3825819519,
            "digest": "abc123",
            "details": {"format": "gguf"},
        }
        
        metadata = OllamaModelMetadata.from_dict(data)
        
        assert metadata.name == "llama2:7b"
        assert metadata.size == 3825819519
    
    def test_is_expired(self):
        """Test expiry check."""
        from datetime import datetime, timedelta
        
        metadata = OllamaModelMetadata(
            name="llama2:7b",
            model="llama2:7b",
            modified_at="2024-01-01T00:00:00Z",
            size=3825819519,
            digest="abc123",
        )
        
        # Fresh metadata should not be expired
        assert not metadata.is_expired(ttl_hours=24)
        
        # Set to expired timestamp
        metadata.cached_at = datetime.now() - timedelta(hours=25)
        assert metadata.is_expired(ttl_hours=24)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
