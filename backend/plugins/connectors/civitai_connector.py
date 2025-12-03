"""
Civitai connector for model registry and community features.

This connector integrates with Civitai API to:
- Search and browse models
- Fetch model metadata
- Download models
- Upload adapters
- Interact with community features (likes, comments)

Civitai API Documentation: https://github.com/civitai/civitai/wiki/REST-API-Reference
"""

from typing import Dict, List, AsyncIterator, Optional, Any
import asyncio
import aiohttp
import json
from pathlib import Path
import hashlib
import time
from datetime import datetime, timedelta
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from connectors.base import (
    PlatformConnector,
    Resource,
    ResourceType,
    PricingInfo,
    TrainingConfig,
    JobStatus,
)


class CivitaiModelMetadata:
    """Model metadata for Civitai models."""
    
    def __init__(
        self,
        model_id: int,
        name: str,
        description: str,
        type: str,
        nsfw: bool,
        tags: List[str],
        creator: Dict[str, Any],
        stats: Dict[str, int],
        model_versions: List[Dict[str, Any]],
        created_at: str,
        updated_at: str,
    ):
        self.model_id = model_id
        self.name = name
        self.description = description
        self.type = type
        self.nsfw = nsfw
        self.tags = tags
        self.creator = creator
        self.stats = stats
        self.model_versions = model_versions
        self.created_at = created_at
        self.updated_at = updated_at
        self.cached_at = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "model_id": self.model_id,
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "nsfw": self.nsfw,
            "tags": self.tags,
            "creator": self.creator,
            "stats": self.stats,
            "model_versions": self.model_versions,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "cached_at": self.cached_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "CivitaiModelMetadata":
        """Create from dictionary."""
        cached_at_str = data.pop("cached_at", None)
        metadata = cls(**data)
        if cached_at_str:
            metadata.cached_at = datetime.fromisoformat(cached_at_str)
        return metadata
    
    def is_expired(self, ttl_hours: int = 24) -> bool:
        """Check if cache entry is expired."""
        expiry = self.cached_at + timedelta(hours=ttl_hours)
        return datetime.now() > expiry


class CivitaiCache:
    """
    Cache for Civitai model metadata with TTL support.
    
    Similar to HuggingFace cache implementation.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize model cache.
        
        Args:
            cache_dir: Directory for cache storage
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".peft-studio" / "cache" / "civitai"
        
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache
        self._cache: Dict[int, CivitaiModelMetadata] = {}
        
        # Load existing cache from disk
        self._load_cache()
    
    def _get_cache_file(self, model_id: int) -> Path:
        """Get cache file path for a model."""
        return self.cache_dir / f"{model_id}.json"
    
    def _load_cache(self):
        """Load cache from disk."""
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    metadata = CivitaiModelMetadata.from_dict(data)
                    self._cache[metadata.model_id] = metadata
            except Exception:
                # Skip corrupted cache files
                pass
    
    def get(self, model_id: int, ttl_hours: int = 24) -> Optional[CivitaiModelMetadata]:
        """
        Get cached metadata for a model.
        
        Args:
            model_id: Model identifier
            ttl_hours: Time-to-live in hours (default: 24)
            
        Returns:
            CivitaiModelMetadata if cached and not expired, None otherwise
        """
        metadata = self._cache.get(model_id)
        
        if metadata is None:
            return None
        
        if metadata.is_expired(ttl_hours):
            # Remove expired entry
            self.remove(model_id)
            return None
        
        return metadata
    
    def set(self, metadata: CivitaiModelMetadata):
        """
        Cache model metadata.
        
        Args:
            metadata: Model metadata to cache
        """
        # Update in-memory cache
        self._cache[metadata.model_id] = metadata
        
        # Persist to disk
        cache_file = self._get_cache_file(metadata.model_id)
        try:
            with open(cache_file, 'w') as f:
                json.dump(metadata.to_dict(), f, indent=2)
        except Exception:
            # Cache write failure is non-fatal
            pass
    
    def remove(self, model_id: int):
        """
        Remove model from cache.
        
        Args:
            model_id: Model identifier
        """
        # Remove from memory
        self._cache.pop(model_id, None)
        
        # Remove from disk
        cache_file = self._get_cache_file(model_id)
        if cache_file.exists():
            cache_file.unlink()
    
    def clear(self):
        """Clear all cached metadata."""
        self._cache.clear()
        
        # Remove all cache files
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()


class CivitaiConnector(PlatformConnector):
    """
    Connector for Civitai model registry and community.
    
    Civitai is a popular platform for sharing AI models, particularly
    for image generation and fine-tuned models. This connector handles:
    - Model search and browsing
    - Model metadata fetching
    - Model download
    - Adapter upload
    - Community features (likes, comments)
    """
    
    # Connector metadata
    name = "civitai"
    display_name = "Civitai"
    description = "Model registry and community platform for AI models"
    version = "1.0.0"
    
    # Supported features
    supports_training = False
    supports_inference = False
    supports_registry = True
    supports_tracking = False
    
    # API endpoints
    BASE_URL = "https://civitai.com"
    API_URL = "https://civitai.com/api/v1"
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self._api_key: Optional[str] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        self._cache = CivitaiCache(cache_dir)
    
    async def connect(self, credentials: Dict[str, str]) -> bool:
        """
        Verify connection and store credentials.
        
        Args:
            credentials: Dictionary with 'api_key' (Civitai API key)
            
        Returns:
            True if connection successful
            
        Raises:
            ConnectionError: If connection fails
            ValueError: If credentials are invalid
        """
        api_key = credentials.get("api_key") or credentials.get("token")
        if not api_key:
            raise ValueError("api_key is required")
        
        self._api_key = api_key
        
        # Create session with headers
        headers = {
            "Content-Type": "application/json",
        }
        
        # Add API key to headers if provided
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        
        self._session = aiohttp.ClientSession(headers=headers)
        
        # Verify connection by making a test API call
        try:
            async with self._session.get(f"{self.API_URL}/models") as response:
                if response.status == 200:
                    self._connected = True
                    return True
                elif response.status == 401:
                    raise ValueError("Invalid API key")
                else:
                    raise ConnectionError(f"Connection failed with status {response.status}")
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Failed to connect to Civitai: {str(e)}")
    
    async def disconnect(self) -> bool:
        """Disconnect and cleanup resources."""
        if self._session:
            await self._session.close()
            self._session = None
        
        self._connected = False
        self._api_key = None
        return True
    
    async def verify_connection(self) -> bool:
        """Verify that the connection is still valid."""
        if not self._connected or not self._session:
            return False
        
        try:
            async with self._session.get(f"{self.API_URL}/models", params={"limit": 1}) as response:
                return response.status == 200
        except:
            return False
    
    async def search_models(
        self,
        query: Optional[str] = None,
        types: Optional[List[str]] = None,
        sort: str = "Highest Rated",
        limit: int = 20,
        nsfw: bool = False,
    ) -> List[CivitaiModelMetadata]:
        """
        Search for models on Civitai.
        
        Args:
            query: Search query string
            types: Filter by model types (e.g., ["Checkpoint", "LORA", "TextualInversion"])
            sort: Sort by "Highest Rated", "Most Downloaded", "Newest"
            limit: Maximum number of results
            nsfw: Include NSFW content
            
        Returns:
            List of model metadata
        """
        if not self._connected:
            raise RuntimeError("Not connected to Civitai")
        
        # Build query parameters
        params = {
            "limit": limit,
            "sort": sort,
            "nsfw": str(nsfw).lower(),
        }
        
        if query:
            params["query"] = query
        
        if types:
            params["types"] = ",".join(types)
        
        try:
            async with self._session.get(
                f"{self.API_URL}/models",
                params=params
            ) as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                models_data = data.get("items", [])
                
                results = []
                for model_data in models_data:
                    metadata = self._parse_model_metadata(model_data)
                    # Cache the metadata
                    self._cache.set(metadata)
                    results.append(metadata)
                
                return results
                
        except aiohttp.ClientError:
            return []
    
    async def get_model_metadata(
        self,
        model_id: int,
        use_cache: bool = True,
    ) -> Optional[CivitaiModelMetadata]:
        """
        Get metadata for a specific model.
        
        Args:
            model_id: Model identifier (numeric ID)
            use_cache: Whether to use cached data if available
            
        Returns:
            Model metadata or None if not found
        """
        # Check cache first
        if use_cache:
            cached = self._cache.get(model_id)
            if cached is not None:
                return cached
        
        # Fetch from API
        if not self._connected:
            # If offline and not in cache, return None
            return None
        
        try:
            async with self._session.get(
                f"{self.API_URL}/models/{model_id}"
            ) as response:
                if response.status == 404:
                    return None
                elif response.status != 200:
                    return None
                
                model_data = await response.json()
                metadata = self._parse_model_metadata(model_data)
                
                # Cache the metadata
                self._cache.set(metadata)
                
                return metadata
                
        except aiohttp.ClientError:
            return None
    
    def _parse_model_metadata(self, data: Dict) -> CivitaiModelMetadata:
        """Parse API response into CivitaiModelMetadata."""
        return CivitaiModelMetadata(
            model_id=data.get("id", 0),
            name=data.get("name", ""),
            description=data.get("description", ""),
            type=data.get("type", ""),
            nsfw=data.get("nsfw", False),
            tags=data.get("tags", []),
            creator=data.get("creator", {}),
            stats=data.get("stats", {}),
            model_versions=data.get("modelVersions", []),
            created_at=data.get("createdAt", ""),
            updated_at=data.get("updatedAt", ""),
        )
    
    async def download_model(
        self,
        model_id: int,
        version_id: Optional[int] = None,
        cache_dir: Optional[Path] = None,
    ) -> Path:
        """
        Download a model from Civitai.
        
        Args:
            model_id: Model identifier
            version_id: Specific version to download (uses latest if None)
            cache_dir: Directory for model cache
            
        Returns:
            Path to downloaded model file
            
        Raises:
            FileNotFoundError: If model doesn't exist
            RuntimeError: If download fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to Civitai")
        
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "civitai" / "models"
        
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Get model metadata to find download URL
        metadata = await self.get_model_metadata(model_id, use_cache=False)
        if not metadata:
            raise FileNotFoundError(f"Model {model_id} not found")
        
        # Find the version to download
        if version_id:
            version = next(
                (v for v in metadata.model_versions if v.get("id") == version_id),
                None
            )
        else:
            # Use the first (latest) version
            version = metadata.model_versions[0] if metadata.model_versions else None
        
        if not version:
            raise FileNotFoundError(f"No version found for model {model_id}")
        
        # Get download URL from version files
        files = version.get("files", [])
        if not files:
            raise FileNotFoundError(f"No files found for model version")
        
        # Use the primary file
        primary_file = files[0]
        download_url = primary_file.get("downloadUrl")
        filename = primary_file.get("name", f"model_{model_id}.safetensors")
        
        if not download_url:
            raise RuntimeError("No download URL found")
        
        # Download the file
        output_path = cache_dir / filename
        
        try:
            async with self._session.get(download_url) as response:
                if response.status != 200:
                    raise RuntimeError(f"Download failed with status {response.status}")
                
                # Stream download to file
                with open(output_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                
                return output_path
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to download model: {str(e)}")
    
    async def upload_artifact(
        self,
        path: str,
        metadata: Dict,
    ) -> str:
        """
        Upload an adapter to Civitai.
        
        Args:
            path: Local path to adapter file
            metadata: Adapter metadata including:
                - name: Model name
                - description: Model description
                - type: Model type (e.g., "LORA")
                - base_model: Base model used
                - tags: List of tags
                - nsfw: Whether content is NSFW
                
        Returns:
            Model URL on Civitai
            
        Raises:
            FileNotFoundError: If local file doesn't exist
            RuntimeError: If upload fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to Civitai")
        
        if not self._api_key:
            raise RuntimeError("API key required for uploads")
        
        adapter_path = Path(path)
        if not adapter_path.exists():
            raise FileNotFoundError(f"Adapter path not found: {path}")
        
        # Prepare model data
        model_data = {
            "name": metadata.get("name", "Untitled Model"),
            "description": metadata.get("description", ""),
            "type": metadata.get("type", "LORA"),
            "nsfw": metadata.get("nsfw", False),
            "tags": metadata.get("tags", []),
        }
        
        try:
            # Create model entry
            async with self._session.post(
                f"{self.API_URL}/models",
                json=model_data
            ) as response:
                if response.status not in [200, 201]:
                    error_text = await response.text()
                    raise RuntimeError(f"Failed to create model: {error_text}")
                
                result = await response.json()
                model_id = result.get("id")
                
                if not model_id:
                    raise RuntimeError("No model ID returned")
            
            # Upload file as a version
            version_data = {
                "modelId": model_id,
                "name": "v1.0",
                "baseModel": metadata.get("base_model", ""),
                "description": metadata.get("version_description", "Initial release"),
            }
            
            # Create multipart form data
            form = aiohttp.FormData()
            form.add_field('data', json.dumps(version_data), content_type='application/json')
            
            # Add file
            with open(adapter_path, 'rb') as f:
                form.add_field(
                    'file',
                    f,
                    filename=adapter_path.name,
                    content_type='application/octet-stream'
                )
                
                async with self._session.post(
                    f"{self.API_URL}/model-versions",
                    data=form
                ) as response:
                    if response.status not in [200, 201]:
                        error_text = await response.text()
                        raise RuntimeError(f"Failed to upload version: {error_text}")
            
            return f"{self.BASE_URL}/models/{model_id}"
            
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to upload adapter: {str(e)}")
    
    async def like_model(self, model_id: int) -> bool:
        """
        Like a model on Civitai.
        
        Args:
            model_id: Model identifier
            
        Returns:
            True if successful
        """
        if not self._connected or not self._api_key:
            raise RuntimeError("Authentication required for likes")
        
        try:
            async with self._session.post(
                f"{self.API_URL}/models/{model_id}/like"
            ) as response:
                return response.status in [200, 201]
        except aiohttp.ClientError:
            return False
    
    async def unlike_model(self, model_id: int) -> bool:
        """
        Remove like from a model on Civitai.
        
        Args:
            model_id: Model identifier
            
        Returns:
            True if successful
        """
        if not self._connected or not self._api_key:
            raise RuntimeError("Authentication required for likes")
        
        try:
            async with self._session.delete(
                f"{self.API_URL}/models/{model_id}/like"
            ) as response:
                return response.status in [200, 204]
        except aiohttp.ClientError:
            return False
    
    async def get_comments(self, model_id: int, limit: int = 20) -> List[Dict]:
        """
        Get comments for a model.
        
        Args:
            model_id: Model identifier
            limit: Maximum number of comments to retrieve
            
        Returns:
            List of comment dictionaries
        """
        if not self._connected:
            raise RuntimeError("Not connected to Civitai")
        
        try:
            async with self._session.get(
                f"{self.API_URL}/models/{model_id}/comments",
                params={"limit": limit}
            ) as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                return data.get("comments", [])
                
        except aiohttp.ClientError:
            return []
    
    async def post_comment(self, model_id: int, content: str) -> bool:
        """
        Post a comment on a model.
        
        Args:
            model_id: Model identifier
            content: Comment text
            
        Returns:
            True if successful
        """
        if not self._connected or not self._api_key:
            raise RuntimeError("Authentication required for comments")
        
        try:
            async with self._session.post(
                f"{self.API_URL}/models/{model_id}/comments",
                json={"content": content}
            ) as response:
                return response.status in [200, 201]
        except aiohttp.ClientError:
            return False
    
    # Required abstract methods (not applicable for registry connector)
    
    async def submit_job(self, config: TrainingConfig) -> str:
        """Not supported for registry connector."""
        raise NotImplementedError("Civitai connector does not support training jobs")
    
    async def get_job_status(self, job_id: str) -> JobStatus:
        """Not supported for registry connector."""
        raise NotImplementedError("Civitai connector does not support training jobs")
    
    async def cancel_job(self, job_id: str) -> bool:
        """Not supported for registry connector."""
        raise NotImplementedError("Civitai connector does not support training jobs")
    
    async def stream_logs(self, job_id: str) -> AsyncIterator[str]:
        """Not supported for registry connector."""
        raise NotImplementedError("Civitai connector does not support training jobs")
        yield  # Make it a generator
    
    async def fetch_artifact(self, job_id: str) -> bytes:
        """Not supported for registry connector."""
        raise NotImplementedError("Civitai connector does not support training jobs")
    
    async def list_resources(self) -> List[Resource]:
        """Not supported for registry connector."""
        return []
    
    async def get_pricing(self, resource_id: str) -> PricingInfo:
        """Not supported for registry connector."""
        raise NotImplementedError("Civitai connector does not provide compute resources")
    
    def get_required_credentials(self) -> List[str]:
        """Get list of required credential keys."""
        return ["api_key"]
