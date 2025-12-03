"""
HuggingFace Hub connector for model registry and adapter management.

This connector integrates with HuggingFace Hub API to:
- Search and browse models
- Fetch model metadata with caching
- Download models with caching
- Upload adapters with model card generation
- Manage repositories
- Check licenses and compatibility

HuggingFace Hub API Documentation: https://huggingface.co/docs/huggingface_hub
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


class ModelMetadata:
    """Model metadata with caching support."""
    
    def __init__(
        self,
        model_id: str,
        author: str,
        downloads: int,
        likes: int,
        tags: List[str],
        pipeline_tag: Optional[str],
        library_name: Optional[str],
        license: Optional[str],
        model_size: Optional[int],
        created_at: str,
        last_modified: str,
        siblings: List[Dict],
        card_data: Optional[Dict] = None,
    ):
        self.model_id = model_id
        self.author = author
        self.downloads = downloads
        self.likes = likes
        self.tags = tags
        self.pipeline_tag = pipeline_tag
        self.library_name = library_name
        self.license = license
        self.model_size = model_size
        self.created_at = created_at
        self.last_modified = last_modified
        self.siblings = siblings
        self.card_data = card_data or {}
        self.cached_at = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "model_id": self.model_id,
            "author": self.author,
            "downloads": self.downloads,
            "likes": self.likes,
            "tags": self.tags,
            "pipeline_tag": self.pipeline_tag,
            "library_name": self.library_name,
            "license": self.license,
            "model_size": self.model_size,
            "created_at": self.created_at,
            "last_modified": self.last_modified,
            "siblings": self.siblings,
            "card_data": self.card_data,
            "cached_at": self.cached_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ModelMetadata":
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


class ModelCache:
    """
    Cache for model metadata with TTL support.
    
    Implements Property 6: Model metadata caching
    - Stores metadata for offline access
    - Expires after 24 hours by default
    - Persists to disk for cross-session availability
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize model cache.
        
        Args:
            cache_dir: Directory for cache storage (default: ~/.peft-studio/cache/models)
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".peft-studio" / "cache" / "models"
        
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache
        self._cache: Dict[str, ModelMetadata] = {}
        
        # Load existing cache from disk
        self._load_cache()
    
    def _get_cache_file(self, model_id: str) -> Path:
        """Get cache file path for a model."""
        # Use hash to avoid filesystem issues with special characters
        model_hash = hashlib.md5(model_id.encode()).hexdigest()
        return self.cache_dir / f"{model_hash}.json"
    
    def _load_cache(self):
        """Load cache from disk."""
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    metadata = ModelMetadata.from_dict(data)
                    self._cache[metadata.model_id] = metadata
            except Exception:
                # Skip corrupted cache files
                pass
    
    def get(self, model_id: str, ttl_hours: int = 24) -> Optional[ModelMetadata]:
        """
        Get cached metadata for a model.
        
        Args:
            model_id: Model identifier
            ttl_hours: Time-to-live in hours (default: 24)
            
        Returns:
            ModelMetadata if cached and not expired, None otherwise
        """
        metadata = self._cache.get(model_id)
        
        if metadata is None:
            return None
        
        if metadata.is_expired(ttl_hours):
            # Remove expired entry
            self.remove(model_id)
            return None
        
        return metadata
    
    def set(self, metadata: ModelMetadata):
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
    
    def remove(self, model_id: str):
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
    
    def get_all_cached(self) -> List[ModelMetadata]:
        """Get all cached models (including expired)."""
        return list(self._cache.values())


class HuggingFaceConnector(PlatformConnector):
    """
    Connector for HuggingFace Hub model registry.
    
    HuggingFace Hub is the primary model registry for open-source LLMs.
    This connector handles:
    - Model search and metadata fetching with caching
    - Model download with caching
    - Adapter upload with model card generation
    - Repository management
    - License and compatibility checking
    """
    
    # Connector metadata
    name = "huggingface"
    display_name = "HuggingFace Hub"
    description = "Model registry and adapter hosting on HuggingFace Hub"
    version = "1.0.0"
    
    # Supported features
    supports_training = False
    supports_inference = False
    supports_registry = True
    supports_tracking = False
    
    # API endpoints
    BASE_URL = "https://huggingface.co"
    API_URL = "https://huggingface.co/api"
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self._token: Optional[str] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        self._cache = ModelCache(cache_dir)
    
    async def connect(self, credentials: Dict[str, str]) -> bool:
        """
        Verify connection and store credentials.
        
        Args:
            credentials: Dictionary with 'token' (HuggingFace API token)
            
        Returns:
            True if connection successful
            
        Raises:
            ConnectionError: If connection fails
            ValueError: If credentials are invalid
        """
        token = credentials.get("token") or credentials.get("api_key")
        if not token:
            raise ValueError("token is required")
        
        # Validate token format (HF tokens start with "hf_")
        if not token.startswith("hf_"):
            raise ValueError("Invalid HuggingFace token format (should start with 'hf_')")
        
        self._token = token
        
        # Create session with headers
        self._session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
            }
        )
        
        # Verify connection by fetching user info
        try:
            async with self._session.get(f"{self.API_URL}/whoami-v2") as response:
                if response.status == 200:
                    data = await response.json()
                    if "name" in data:
                        self._connected = True
                        return True
                    else:
                        raise ConnectionError("Invalid API response")
                elif response.status == 401:
                    raise ValueError("Invalid API token")
                else:
                    raise ConnectionError(f"Connection failed with status {response.status}")
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Failed to connect to HuggingFace: {str(e)}")
    
    async def disconnect(self) -> bool:
        """Disconnect and cleanup resources."""
        if self._session:
            await self._session.close()
            self._session = None
        
        self._connected = False
        self._token = None
        return True
    
    async def verify_connection(self) -> bool:
        """Verify that the connection is still valid."""
        if not self._connected or not self._session:
            return False
        
        try:
            async with self._session.get(f"{self.API_URL}/whoami-v2") as response:
                return response.status == 200
        except:
            return False
    
    async def search_models(
        self,
        query: Optional[str] = None,
        filter_tags: Optional[List[str]] = None,
        sort: str = "downloads",
        limit: int = 20,
    ) -> List[ModelMetadata]:
        """
        Search for models on HuggingFace Hub.
        
        Args:
            query: Search query string
            filter_tags: Filter by tags (e.g., ["text-generation", "pytorch"])
            sort: Sort by "downloads", "likes", "trending", or "updated"
            limit: Maximum number of results
            
        Returns:
            List of model metadata
        """
        if not self._connected:
            raise RuntimeError("Not connected to HuggingFace")
        
        # Build query parameters
        params = {
            "limit": limit,
            "sort": sort,
            "direction": -1,  # Descending
        }
        
        if query:
            params["search"] = query
        
        if filter_tags:
            params["filter"] = ",".join(filter_tags)
        
        try:
            async with self._session.get(
                f"{self.API_URL}/models",
                params=params
            ) as response:
                if response.status != 200:
                    return []
                
                models_data = await response.json()
                
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
        model_id: str,
        use_cache: bool = True,
    ) -> Optional[ModelMetadata]:
        """
        Get metadata for a specific model.
        
        Implements Property 6: Model metadata caching
        - Checks cache first if use_cache=True
        - Falls back to API if not cached or expired
        - Caches result for offline access
        
        Args:
            model_id: Model identifier (e.g., "meta-llama/Llama-2-7b-hf")
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
    
    def _parse_model_metadata(self, data: Dict) -> ModelMetadata:
        """Parse API response into ModelMetadata."""
        return ModelMetadata(
            model_id=data.get("id", data.get("modelId", "")),
            author=data.get("author", ""),
            downloads=data.get("downloads", 0),
            likes=data.get("likes", 0),
            tags=data.get("tags", []),
            pipeline_tag=data.get("pipeline_tag"),
            library_name=data.get("library_name"),
            license=data.get("license"),
            model_size=data.get("safetensors", {}).get("total", 0),
            created_at=data.get("createdAt", ""),
            last_modified=data.get("lastModified", ""),
            siblings=data.get("siblings", []),
            card_data=data.get("cardData", {}),
        )
    
    async def download_model(
        self,
        model_id: str,
        cache_dir: Optional[Path] = None,
    ) -> Path:
        """
        Download a model with caching.
        
        Args:
            model_id: Model identifier
            cache_dir: Directory for model cache (default: ~/.cache/huggingface)
            
        Returns:
            Path to downloaded model directory
            
        Raises:
            FileNotFoundError: If model doesn't exist
            RuntimeError: If download fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to HuggingFace")
        
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
        
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Use huggingface_hub library for efficient downloading
        try:
            from huggingface_hub import snapshot_download
            
            model_path = snapshot_download(
                repo_id=model_id,
                cache_dir=str(cache_dir),
                token=self._token,
            )
            
            return Path(model_path)
            
        except ImportError:
            raise RuntimeError("huggingface_hub library not installed")
        except Exception as e:
            raise RuntimeError(f"Failed to download model: {str(e)}")
    
    async def upload_artifact(
        self,
        path: str,
        metadata: Dict,
    ) -> str:
        """
        Upload an adapter to HuggingFace Hub with model card generation.
        
        Args:
            path: Local path to adapter directory
            metadata: Adapter metadata including:
                - repo_id: Repository ID (e.g., "username/model-name")
                - base_model: Base model used for training
                - dataset: Dataset used
                - training_config: Training configuration
                - metrics: Evaluation metrics
                - description: Model description
                
        Returns:
            Repository URL
            
        Raises:
            FileNotFoundError: If local path doesn't exist
            RuntimeError: If upload fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to HuggingFace")
        
        adapter_path = Path(path)
        if not adapter_path.exists():
            raise FileNotFoundError(f"Adapter path not found: {path}")
        
        repo_id = metadata.get("repo_id")
        if not repo_id:
            raise ValueError("repo_id is required in metadata")
        
        try:
            from huggingface_hub import HfApi, create_repo
            
            api = HfApi(token=self._token)
            
            # Create repository if it doesn't exist
            try:
                create_repo(
                    repo_id=repo_id,
                    token=self._token,
                    exist_ok=True,
                )
            except Exception:
                pass  # Repo might already exist
            
            # Generate model card
            model_card = self._generate_model_card(metadata)
            
            # Write model card to adapter directory
            card_path = adapter_path / "README.md"
            with open(card_path, 'w') as f:
                f.write(model_card)
            
            # Upload all files in the adapter directory
            api.upload_folder(
                folder_path=str(adapter_path),
                repo_id=repo_id,
                token=self._token,
            )
            
            return f"{self.BASE_URL}/{repo_id}"
            
        except ImportError:
            raise RuntimeError("huggingface_hub library not installed")
        except Exception as e:
            raise RuntimeError(f"Failed to upload adapter: {str(e)}")
    
    def _generate_model_card(self, metadata: Dict) -> str:
        """
        Generate a model card for the adapter.
        
        Args:
            metadata: Adapter metadata
            
        Returns:
            Model card content in Markdown
        """
        base_model = metadata.get("base_model", "Unknown")
        dataset = metadata.get("dataset", "Unknown")
        description = metadata.get("description", "")
        training_config = metadata.get("training_config", {})
        metrics = metadata.get("metrics", {})
        
        card = f"""---
base_model: {base_model}
tags:
- peft
- lora
- adapter
license: apache-2.0
---

# {metadata.get('repo_id', 'Model Adapter')}

{description}

## Model Details

- **Base Model:** {base_model}
- **Training Dataset:** {dataset}
- **Adapter Type:** LoRA
- **Created with:** PEFT Studio

## Training Configuration

"""
        
        if training_config:
            card += "```json\n"
            card += json.dumps(training_config, indent=2)
            card += "\n```\n\n"
        
        if metrics:
            card += "## Evaluation Metrics\n\n"
            for metric_name, metric_value in metrics.items():
                card += f"- **{metric_name}:** {metric_value}\n"
            card += "\n"
        
        card += """## Usage

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Load base model
base_model = AutoModelForCausalLM.from_pretrained("{base_model}")
tokenizer = AutoTokenizer.from_pretrained("{base_model}")

# Load adapter
model = PeftModel.from_pretrained(base_model, "{repo_id}")

# Generate
inputs = tokenizer("Your prompt here", return_tensors="pt")
outputs = model.generate(**inputs)
print(tokenizer.decode(outputs[0]))
```

## License

This adapter is released under the Apache 2.0 license.
""".format(base_model=base_model, repo_id=metadata.get('repo_id', ''))
        
        return card
    
    async def check_license(self, model_id: str) -> Optional[str]:
        """
        Check the license of a model.
        
        Args:
            model_id: Model identifier
            
        Returns:
            License identifier (e.g., "apache-2.0", "mit") or None
        """
        metadata = await self.get_model_metadata(model_id)
        return metadata.license if metadata else None
    
    async def check_compatibility(
        self,
        model_id: str,
        required_library: Optional[str] = None,
    ) -> bool:
        """
        Check if a model is compatible with requirements.
        
        Args:
            model_id: Model identifier
            required_library: Required library (e.g., "transformers", "diffusers")
            
        Returns:
            True if compatible, False otherwise
        """
        metadata = await self.get_model_metadata(model_id)
        
        if metadata is None:
            return False
        
        # Check library compatibility
        if required_library:
            if metadata.library_name != required_library:
                return False
        
        # Check if model has required files
        has_config = any(
            s.get("rfilename") == "config.json"
            for s in metadata.siblings
        )
        
        has_weights = any(
            s.get("rfilename", "").endswith((".safetensors", ".bin"))
            for s in metadata.siblings
        )
        
        return has_config and has_weights
    
    # Required abstract methods (not applicable for registry connector)
    
    async def submit_job(self, config: TrainingConfig) -> str:
        """Not supported for registry connector."""
        raise NotImplementedError("HuggingFace connector does not support training jobs")
    
    async def get_job_status(self, job_id: str) -> JobStatus:
        """Not supported for registry connector."""
        raise NotImplementedError("HuggingFace connector does not support training jobs")
    
    async def cancel_job(self, job_id: str) -> bool:
        """Not supported for registry connector."""
        raise NotImplementedError("HuggingFace connector does not support training jobs")
    
    async def stream_logs(self, job_id: str) -> AsyncIterator[str]:
        """Not supported for registry connector."""
        raise NotImplementedError("HuggingFace connector does not support training jobs")
        yield  # Make it a generator
    
    async def fetch_artifact(self, job_id: str) -> bytes:
        """Not supported for registry connector."""
        raise NotImplementedError("HuggingFace connector does not support training jobs")
    
    async def list_resources(self) -> List[Resource]:
        """Not supported for registry connector."""
        return []
    
    async def get_pricing(self, resource_id: str) -> PricingInfo:
        """Not supported for registry connector."""
        raise NotImplementedError("HuggingFace connector does not provide compute resources")
    
    def get_required_credentials(self) -> List[str]:
        """Get list of required credential keys."""
        return ["token"]
