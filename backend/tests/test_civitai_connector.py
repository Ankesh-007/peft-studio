"""
Tests for Civitai connector.

Tests cover:
- Connection and authentication
- Model search and browsing
- Model metadata fetching with caching
- Model download
- Adapter upload
- Community features (likes, comments)
"""

import pytest
import asyncio
from pathlib import Path
import json
import tempfile
import shutil
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys

sys.path.append(str(Path(__file__).parent.parent))

from plugins.connectors.civitai_connector import (
    CivitaiConnector,
    CivitaiModelMetadata,
    CivitaiCache,
)
from connectors.base import TrainingConfig


@pytest.fixture
def temp_cache_dir():
    """Create a temporary cache directory."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def connector(temp_cache_dir):
    """Create a Civitai connector instance."""
    return CivitaiConnector(cache_dir=temp_cache_dir)


@pytest.fixture
def mock_session():
    """Create a mock aiohttp session."""
    session = AsyncMock()
    return session


@pytest.fixture
def sample_model_data():
    """Sample model data from Civitai API."""
    return {
        "id": 12345,
        "name": "Test LoRA Model",
        "description": "A test model for unit testing",
        "type": "LORA",
        "nsfw": False,
        "tags": ["test", "lora", "character"],
        "creator": {
            "username": "testuser",
            "image": "https://example.com/avatar.jpg"
        },
        "stats": {
            "downloadCount": 1000,
            "favoriteCount": 50,
            "commentCount": 10,
            "ratingCount": 25,
            "rating": 4.5
        },
        "modelVersions": [
            {
                "id": 67890,
                "name": "v1.0",
                "createdAt": "2024-01-01T00:00:00Z",
                "downloadUrl": "https://civitai.com/api/download/models/67890",
                "files": [
                    {
                        "name": "test_model.safetensors",
                        "downloadUrl": "https://civitai.com/api/download/models/67890",
                        "sizeKB": 144000
                    }
                ]
            }
        ],
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-15T00:00:00Z"
    }


class TestCivitaiCache:
    """Test Civitai cache functionality."""
    
    def test_cache_initialization(self, temp_cache_dir):
        """Test cache initialization."""
        cache = CivitaiCache(temp_cache_dir)
        assert cache.cache_dir == temp_cache_dir
        assert cache.cache_dir.exists()
    
    def test_cache_set_and_get(self, temp_cache_dir, sample_model_data):
        """Test caching and retrieving metadata."""
        cache = CivitaiCache(temp_cache_dir)
        
        # Create metadata
        metadata = CivitaiModelMetadata(
            model_id=sample_model_data["id"],
            name=sample_model_data["name"],
            description=sample_model_data["description"],
            type=sample_model_data["type"],
            nsfw=sample_model_data["nsfw"],
            tags=sample_model_data["tags"],
            creator=sample_model_data["creator"],
            stats=sample_model_data["stats"],
            model_versions=sample_model_data["modelVersions"],
            created_at=sample_model_data["createdAt"],
            updated_at=sample_model_data["updatedAt"],
        )
        
        # Cache it
        cache.set(metadata)
        
        # Retrieve it
        cached = cache.get(sample_model_data["id"])
        assert cached is not None
        assert cached.model_id == sample_model_data["id"]
        assert cached.name == sample_model_data["name"]
    
    def test_cache_persistence(self, temp_cache_dir, sample_model_data):
        """Test that cache persists across instances."""
        # Create first cache instance and store data
        cache1 = CivitaiCache(temp_cache_dir)
        metadata = CivitaiModelMetadata(
            model_id=sample_model_data["id"],
            name=sample_model_data["name"],
            description=sample_model_data["description"],
            type=sample_model_data["type"],
            nsfw=sample_model_data["nsfw"],
            tags=sample_model_data["tags"],
            creator=sample_model_data["creator"],
            stats=sample_model_data["stats"],
            model_versions=sample_model_data["modelVersions"],
            created_at=sample_model_data["createdAt"],
            updated_at=sample_model_data["updatedAt"],
        )
        cache1.set(metadata)
        
        # Create second cache instance
        cache2 = CivitaiCache(temp_cache_dir)
        
        # Should load from disk
        cached = cache2.get(sample_model_data["id"])
        assert cached is not None
        assert cached.model_id == sample_model_data["id"]
    
    def test_cache_expiry(self, temp_cache_dir, sample_model_data):
        """Test cache expiry."""
        cache = CivitaiCache(temp_cache_dir)
        
        metadata = CivitaiModelMetadata(
            model_id=sample_model_data["id"],
            name=sample_model_data["name"],
            description=sample_model_data["description"],
            type=sample_model_data["type"],
            nsfw=sample_model_data["nsfw"],
            tags=sample_model_data["tags"],
            creator=sample_model_data["creator"],
            stats=sample_model_data["stats"],
            model_versions=sample_model_data["modelVersions"],
            created_at=sample_model_data["createdAt"],
            updated_at=sample_model_data["updatedAt"],
        )
        
        cache.set(metadata)
        
        # Should not be expired with 24 hour TTL
        cached = cache.get(sample_model_data["id"], ttl_hours=24)
        assert cached is not None
        
        # Should be expired with 0 hour TTL
        cached = cache.get(sample_model_data["id"], ttl_hours=0)
        assert cached is None


class TestCivitaiConnector:
    """Test Civitai connector functionality."""
    
    @pytest.mark.asyncio
    async def test_connect_success(self, connector, mock_session):
        """Test successful connection."""
        # Mock successful API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"items": []})
        mock_session.get = AsyncMock(return_value=mock_response)
        
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
        mock_session.get = AsyncMock(return_value=mock_response)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with pytest.raises(ValueError, match="Invalid API key"):
                await connector.connect({"api_key": "invalid_key"})
    
    @pytest.mark.asyncio
    async def test_connect_missing_credentials(self, connector):
        """Test connection with missing credentials."""
        with pytest.raises(ValueError, match="api_key is required"):
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
    
    @pytest.mark.asyncio
    async def test_verify_connection(self, connector, mock_session):
        """Test connection verification."""
        connector._session = mock_session
        connector._connected = True
        
        # Mock successful verification
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_session.get = AsyncMock(return_value=mock_response)
        
        result = await connector.verify_connection()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_search_models(self, connector, mock_session, sample_model_data):
        """Test model search."""
        connector._session = mock_session
        connector._connected = True
        
        # Mock search response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "items": [sample_model_data],
            "metadata": {"totalItems": 1}
        })
        mock_session.get = AsyncMock(return_value=mock_response)
        
        results = await connector.search_models(query="test", limit=10)
        
        assert len(results) == 1
        assert results[0].model_id == sample_model_data["id"]
        assert results[0].name == sample_model_data["name"]
    
    @pytest.mark.asyncio
    async def test_get_model_metadata_from_api(self, connector, mock_session, sample_model_data):
        """Test fetching model metadata from API."""
        connector._session = mock_session
        connector._connected = True
        
        # Mock API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=sample_model_data)
        mock_session.get = AsyncMock(return_value=mock_response)
        
        metadata = await connector.get_model_metadata(sample_model_data["id"], use_cache=False)
        
        assert metadata is not None
        assert metadata.model_id == sample_model_data["id"]
        assert metadata.name == sample_model_data["name"]
    
    @pytest.mark.asyncio
    async def test_get_model_metadata_from_cache(self, connector, sample_model_data):
        """Test fetching model metadata from cache."""
        # Pre-populate cache
        metadata = CivitaiModelMetadata(
            model_id=sample_model_data["id"],
            name=sample_model_data["name"],
            description=sample_model_data["description"],
            type=sample_model_data["type"],
            nsfw=sample_model_data["nsfw"],
            tags=sample_model_data["tags"],
            creator=sample_model_data["creator"],
            stats=sample_model_data["stats"],
            model_versions=sample_model_data["modelVersions"],
            created_at=sample_model_data["createdAt"],
            updated_at=sample_model_data["updatedAt"],
        )
        connector._cache.set(metadata)
        
        # Should return from cache without API call
        cached_metadata = await connector.get_model_metadata(sample_model_data["id"], use_cache=True)
        
        assert cached_metadata is not None
        assert cached_metadata.model_id == sample_model_data["id"]
    
    @pytest.mark.asyncio
    async def test_download_model(self, connector, mock_session, sample_model_data, temp_cache_dir):
        """Test model download."""
        connector._session = mock_session
        connector._connected = True
        
        # Mock metadata response
        mock_metadata_response = AsyncMock()
        mock_metadata_response.status = 200
        mock_metadata_response.json = AsyncMock(return_value=sample_model_data)
        
        # Mock download response
        mock_download_response = AsyncMock()
        mock_download_response.status = 200
        mock_download_response.content.iter_chunked = AsyncMock(
            return_value=[b"test_data"]
        )
        
        async def mock_get(url, **kwargs):
            if "models/" in url and "/download" not in url:
                return mock_metadata_response
            else:
                return mock_download_response
        
        mock_session.get = mock_get
        
        download_path = await connector.download_model(
            sample_model_data["id"],
            cache_dir=temp_cache_dir
        )
        
        assert download_path.exists()
        assert download_path.name == "test_model.safetensors"
    
    @pytest.mark.asyncio
    async def test_upload_artifact(self, connector, mock_session, temp_cache_dir):
        """Test adapter upload."""
        connector._session = mock_session
        connector._connected = True
        connector._api_key = "test_key"
        
        # Create a test file
        test_file = temp_cache_dir / "test_adapter.safetensors"
        test_file.write_bytes(b"test_adapter_data")
        
        # Mock create model response
        mock_create_response = AsyncMock()
        mock_create_response.status = 201
        mock_create_response.json = AsyncMock(return_value={"id": 12345})
        
        # Mock upload version response
        mock_upload_response = AsyncMock()
        mock_upload_response.status = 201
        
        call_count = [0]
        
        async def mock_post(url, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_create_response
            else:
                return mock_upload_response
        
        mock_session.post = mock_post
        
        metadata = {
            "name": "Test Adapter",
            "description": "Test description",
            "type": "LORA",
            "base_model": "test-model",
            "tags": ["test"],
        }
        
        result_url = await connector.upload_artifact(str(test_file), metadata)
        
        assert "civitai.com/models/12345" in result_url
    
    @pytest.mark.asyncio
    async def test_like_model(self, connector, mock_session):
        """Test liking a model."""
        connector._session = mock_session
        connector._connected = True
        connector._api_key = "test_key"
        
        # Mock like response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_session.post = AsyncMock(return_value=mock_response)
        
        result = await connector.like_model(12345)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_unlike_model(self, connector, mock_session):
        """Test unliking a model."""
        connector._session = mock_session
        connector._connected = True
        connector._api_key = "test_key"
        
        # Mock unlike response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_session.delete = AsyncMock(return_value=mock_response)
        
        result = await connector.unlike_model(12345)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_get_comments(self, connector, mock_session):
        """Test getting model comments."""
        connector._session = mock_session
        connector._connected = True
        
        # Mock comments response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "comments": [
                {"id": 1, "content": "Great model!", "user": "user1"},
                {"id": 2, "content": "Works well", "user": "user2"}
            ]
        })
        mock_session.get = AsyncMock(return_value=mock_response)
        
        comments = await connector.get_comments(12345)
        
        assert len(comments) == 2
        assert comments[0]["content"] == "Great model!"
    
    @pytest.mark.asyncio
    async def test_post_comment(self, connector, mock_session):
        """Test posting a comment."""
        connector._session = mock_session
        connector._connected = True
        connector._api_key = "test_key"
        
        # Mock post comment response
        mock_response = AsyncMock()
        mock_response.status = 201
        mock_session.post = AsyncMock(return_value=mock_response)
        
        result = await connector.post_comment(12345, "Test comment")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_not_implemented_methods(self, connector):
        """Test that training-related methods raise NotImplementedError."""
        config = TrainingConfig(
            base_model="test",
            model_source="civitai",
            algorithm="lora",
            rank=8,
            alpha=16,
            dropout=0.1,
            target_modules=["q_proj", "v_proj"]
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
        """Test that list_resources returns empty list."""
        resources = await connector.list_resources()
        assert resources == []
    
    def test_get_required_credentials(self, connector):
        """Test getting required credentials."""
        creds = connector.get_required_credentials()
        assert "api_key" in creds


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
