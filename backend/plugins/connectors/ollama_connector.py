"""
Ollama connector for local model registry and deployment.

This connector integrates with Ollama API to:
- Browse model library
- Generate Modelfiles for custom models
- Package local models for Ollama
- Push models to Ollama library
- Manage local model instances

Ollama API Documentation: https://github.com/ollama/ollama/blob/main/docs/api.md
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


class OllamaModelMetadata:
    """Model metadata for Ollama models."""
    
    def __init__(
        self,
        name: str,
        model: str,
        modified_at: str,
        size: int,
        digest: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.model = model
        self.modified_at = modified_at
        self.size = size
        self.digest = digest
        self.details = details or {}
        self.cached_at = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "model": self.model,
            "modified_at": self.modified_at,
            "size": self.size,
            "digest": self.digest,
            "details": self.details,
            "cached_at": self.cached_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "OllamaModelMetadata":
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


class OllamaCache:
    """
    Cache for Ollama model metadata with TTL support.
    
    Similar to HuggingFace cache implementation.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize model cache.
        
        Args:
            cache_dir: Directory for cache storage
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".peft-studio" / "cache" / "ollama"
        
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache
        self._cache: Dict[str, OllamaModelMetadata] = {}
        
        # Load existing cache from disk
        self._load_cache()
    
    def _get_cache_file(self, model_name: str) -> Path:
        """Get cache file path for a model."""
        # Use hash to avoid filesystem issues with special characters
        model_hash = hashlib.md5(model_name.encode()).hexdigest()
        return self.cache_dir / f"{model_hash}.json"
    
    def _load_cache(self):
        """Load cache from disk."""
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    metadata = OllamaModelMetadata.from_dict(data)
                    self._cache[metadata.name] = metadata
            except Exception:
                # Skip corrupted cache files
                pass
    
    def get(self, model_name: str, ttl_hours: int = 24) -> Optional[OllamaModelMetadata]:
        """
        Get cached metadata for a model.
        
        Args:
            model_name: Model name
            ttl_hours: Time-to-live in hours (default: 24)
            
        Returns:
            OllamaModelMetadata if cached and not expired, None otherwise
        """
        metadata = self._cache.get(model_name)
        
        if metadata is None:
            return None
        
        if metadata.is_expired(ttl_hours):
            # Remove expired entry
            self.remove(model_name)
            return None
        
        return metadata
    
    def set(self, metadata: OllamaModelMetadata):
        """
        Cache model metadata.
        
        Args:
            metadata: Model metadata to cache
        """
        # Update in-memory cache
        self._cache[metadata.name] = metadata
        
        # Persist to disk
        cache_file = self._get_cache_file(metadata.name)
        try:
            with open(cache_file, 'w') as f:
                json.dump(metadata.to_dict(), f, indent=2)
        except Exception:
            # Cache write failure is non-fatal
            pass
    
    def remove(self, model_name: str):
        """
        Remove model from cache.
        
        Args:
            model_name: Model name
        """
        # Remove from memory
        self._cache.pop(model_name, None)
        
        # Remove from disk
        cache_file = self._get_cache_file(model_name)
        if cache_file.exists():
            cache_file.unlink()
    
    def clear(self):
        """Clear all cached metadata."""
        self._cache.clear()
        
        # Remove all cache files
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()


class OllamaConnector(PlatformConnector):
    """
    Connector for Ollama local model registry and deployment.
    
    Ollama is a tool for running large language models locally.
    This connector handles:
    - Model library browsing
    - Modelfile generation for custom models
    - Local model packaging
    - Model push to Ollama library
    - Local model management
    """
    
    # Connector metadata
    name = "ollama"
    display_name = "Ollama"
    description = "Local model registry and deployment with Ollama"
    version = "1.0.0"
    
    # Supported features
    supports_training = False
    supports_inference = True
    supports_registry = True
    supports_tracking = False
    
    # Default API endpoint (local Ollama instance)
    DEFAULT_BASE_URL = "http://localhost:11434"
    
    def __init__(self, base_url: Optional[str] = None, cache_dir: Optional[Path] = None):
        """
        Initialize Ollama connector.
        
        Args:
            base_url: Ollama API base URL (default: http://localhost:11434)
            cache_dir: Directory for cache storage
        """
        self._base_url = base_url or self.DEFAULT_BASE_URL
        self._session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        self._cache = OllamaCache(cache_dir)
    
    async def connect(self, credentials: Dict[str, str]) -> bool:
        """
        Verify connection to Ollama instance.
        
        Ollama typically runs locally without authentication,
        but this method verifies the service is accessible.
        
        Args:
            credentials: Dictionary (may contain 'base_url' to override default)
            
        Returns:
            True if connection successful
            
        Raises:
            ConnectionError: If connection fails
        """
        # Allow overriding base URL via credentials
        if "base_url" in credentials:
            self._base_url = credentials["base_url"]
        
        # Create session
        self._session = aiohttp.ClientSession(
            headers={"Content-Type": "application/json"}
        )
        
        # Verify connection by listing models
        try:
            async with self._session.get(f"{self._base_url}/api/tags") as response:
                if response.status == 200:
                    self._connected = True
                    return True
                else:
                    raise ConnectionError(
                        f"Ollama service not accessible (status {response.status}). "
                        f"Make sure Ollama is running at {self._base_url}"
                    )
        except aiohttp.ClientError as e:
            raise ConnectionError(
                f"Failed to connect to Ollama at {self._base_url}: {str(e)}. "
                f"Make sure Ollama is installed and running."
            )
    
    async def disconnect(self) -> bool:
        """Disconnect and cleanup resources."""
        if self._session:
            await self._session.close()
            self._session = None
        
        self._connected = False
        return True
    
    async def verify_connection(self) -> bool:
        """Verify that the connection is still valid."""
        if not self._connected or not self._session:
            return False
        
        try:
            async with self._session.get(f"{self._base_url}/api/tags") as response:
                return response.status == 200
        except:
            return False
    
    async def list_models(self) -> List[OllamaModelMetadata]:
        """
        List all models available in local Ollama instance.
        
        Returns:
            List of model metadata
        """
        if not self._connected:
            raise RuntimeError("Not connected to Ollama")
        
        try:
            async with self._session.get(f"{self._base_url}/api/tags") as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                models_data = data.get("models", [])
                
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
        model_name: str,
        use_cache: bool = True,
    ) -> Optional[OllamaModelMetadata]:
        """
        Get metadata for a specific model.
        
        Args:
            model_name: Model name (e.g., "llama2:7b")
            use_cache: Whether to use cached data if available
            
        Returns:
            Model metadata or None if not found
        """
        # Check cache first
        if use_cache:
            cached = self._cache.get(model_name)
            if cached is not None:
                return cached
        
        # Fetch from API by listing all models and finding the match
        if not self._connected:
            # If offline and not in cache, return None
            return None
        
        try:
            models = await self.list_models()
            for model in models:
                if model.name == model_name:
                    return model
            
            return None
                
        except Exception:
            return None
    
    def _parse_model_metadata(self, data: Dict) -> OllamaModelMetadata:
        """Parse API response into OllamaModelMetadata."""
        return OllamaModelMetadata(
            name=data.get("name", ""),
            model=data.get("model", data.get("name", "")),
            modified_at=data.get("modified_at", ""),
            size=data.get("size", 0),
            digest=data.get("digest", ""),
            details=data.get("details", {}),
        )
    
    def generate_modelfile(
        self,
        base_model: str,
        adapter_path: Optional[str] = None,
        system_prompt: Optional[str] = None,
        template: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate a Modelfile for creating a custom Ollama model.
        
        A Modelfile is similar to a Dockerfile but for AI models.
        It defines how to build a model from a base model and adapters.
        
        Args:
            base_model: Base model to use (e.g., "llama2:7b")
            adapter_path: Path to adapter weights (.safetensors or .gguf)
            system_prompt: System prompt to use
            template: Prompt template
            parameters: Model parameters (temperature, top_p, etc.)
            
        Returns:
            Modelfile content as string
        """
        modelfile_lines = []
        
        # FROM instruction (required)
        modelfile_lines.append(f"FROM {base_model}")
        modelfile_lines.append("")
        
        # ADAPTER instruction (if adapter provided)
        if adapter_path:
            modelfile_lines.append(f"ADAPTER {adapter_path}")
            modelfile_lines.append("")
        
        # SYSTEM instruction (if system prompt provided)
        if system_prompt:
            # Escape quotes in system prompt
            escaped_prompt = system_prompt.replace('"', '\\"')
            modelfile_lines.append(f'SYSTEM """{escaped_prompt}"""')
            modelfile_lines.append("")
        
        # TEMPLATE instruction (if template provided)
        if template:
            # Escape quotes in template
            escaped_template = template.replace('"', '\\"')
            modelfile_lines.append(f'TEMPLATE """{escaped_template}"""')
            modelfile_lines.append("")
        
        # PARAMETER instructions (if parameters provided)
        if parameters:
            for param_name, param_value in parameters.items():
                modelfile_lines.append(f"PARAMETER {param_name} {param_value}")
            modelfile_lines.append("")
        
        return "\n".join(modelfile_lines)
    
    async def create_model(
        self,
        name: str,
        modelfile: str,
        stream: bool = False,
    ) -> bool:
        """
        Create a model from a Modelfile.
        
        Args:
            name: Name for the new model
            modelfile: Modelfile content
            stream: Whether to stream progress
            
        Returns:
            True if successful
            
        Raises:
            RuntimeError: If model creation fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to Ollama")
        
        try:
            payload = {
                "name": name,
                "modelfile": modelfile,
                "stream": stream,
            }
            
            async with self._session.post(
                f"{self._base_url}/api/create",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Failed to create model: {error_text}")
                
                if stream:
                    # Stream progress updates
                    async for line in response.content:
                        if line:
                            try:
                                progress = json.loads(line)
                                status = progress.get("status", "")
                                print(f"Progress: {status}")
                            except json.JSONDecodeError:
                                pass
                
                return True
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to create model: {str(e)}")
    
    async def delete_model(self, name: str) -> bool:
        """
        Delete a model from local Ollama instance.
        
        Args:
            name: Model name to delete
            
        Returns:
            True if successful
        """
        if not self._connected:
            raise RuntimeError("Not connected to Ollama")
        
        try:
            async with self._session.delete(
                f"{self._base_url}/api/delete",
                json={"name": name}
            ) as response:
                return response.status == 200
                
        except aiohttp.ClientError:
            return False
    
    async def pull_model(self, name: str, stream: bool = False) -> bool:
        """
        Pull a model from Ollama library.
        
        Args:
            name: Model name to pull (e.g., "llama2:7b")
            stream: Whether to stream progress
            
        Returns:
            True if successful
        """
        if not self._connected:
            raise RuntimeError("Not connected to Ollama")
        
        try:
            payload = {
                "name": name,
                "stream": stream,
            }
            
            async with self._session.post(
                f"{self._base_url}/api/pull",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Failed to pull model: {error_text}")
                
                if stream:
                    # Stream progress updates
                    async for line in response.content:
                        if line:
                            try:
                                progress = json.loads(line)
                                status = progress.get("status", "")
                                print(f"Progress: {status}")
                            except json.JSONDecodeError:
                                pass
                
                return True
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to pull model: {str(e)}")
    
    async def push_model(self, name: str, stream: bool = False) -> bool:
        """
        Push a model to Ollama library.
        
        Note: Requires authentication and proper permissions.
        
        Args:
            name: Model name to push
            stream: Whether to stream progress
            
        Returns:
            True if successful
        """
        if not self._connected:
            raise RuntimeError("Not connected to Ollama")
        
        try:
            payload = {
                "name": name,
                "stream": stream,
            }
            
            async with self._session.post(
                f"{self._base_url}/api/push",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Failed to push model: {error_text}")
                
                if stream:
                    # Stream progress updates
                    async for line in response.content:
                        if line:
                            try:
                                progress = json.loads(line)
                                status = progress.get("status", "")
                                print(f"Progress: {status}")
                            except json.JSONDecodeError:
                                pass
                
                return True
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to push model: {str(e)}")
    
    async def generate(
        self,
        model: str,
        prompt: str,
        stream: bool = False,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate text using a model.
        
        Args:
            model: Model name to use
            prompt: Input prompt
            stream: Whether to stream response
            options: Generation options (temperature, top_p, etc.)
            
        Returns:
            Generated text
        """
        if not self._connected:
            raise RuntimeError("Not connected to Ollama")
        
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": stream,
            }
            
            if options:
                payload["options"] = options
            
            async with self._session.post(
                f"{self._base_url}/api/generate",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Failed to generate: {error_text}")
                
                if stream:
                    # Stream response
                    full_response = []
                    async for line in response.content:
                        if line:
                            try:
                                chunk = json.loads(line)
                                text = chunk.get("response", "")
                                full_response.append(text)
                                print(text, end="", flush=True)
                            except json.JSONDecodeError:
                                pass
                    print()  # New line after streaming
                    return "".join(full_response)
                else:
                    # Non-streaming response
                    data = await response.json()
                    return data.get("response", "")
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to generate: {str(e)}")
    
    async def upload_artifact(
        self,
        path: str,
        metadata: Dict,
    ) -> str:
        """
        Package and upload an adapter as an Ollama model.
        
        This creates a Modelfile, builds the model locally,
        and optionally pushes it to Ollama library.
        
        Args:
            path: Local path to adapter directory or file
            metadata: Adapter metadata including:
                - name: Model name for Ollama
                - base_model: Base model to use
                - system_prompt: Optional system prompt
                - template: Optional prompt template
                - parameters: Optional model parameters
                - push: Whether to push to Ollama library (default: False)
                
        Returns:
            Model name in Ollama
            
        Raises:
            FileNotFoundError: If local path doesn't exist
            RuntimeError: If packaging fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to Ollama")
        
        adapter_path = Path(path)
        if not adapter_path.exists():
            raise FileNotFoundError(f"Adapter path not found: {path}")
        
        model_name = metadata.get("name")
        if not model_name:
            raise ValueError("name is required in metadata")
        
        base_model = metadata.get("base_model")
        if not base_model:
            raise ValueError("base_model is required in metadata")
        
        # Generate Modelfile
        modelfile = self.generate_modelfile(
            base_model=base_model,
            adapter_path=str(adapter_path) if adapter_path.is_file() else None,
            system_prompt=metadata.get("system_prompt"),
            template=metadata.get("template"),
            parameters=metadata.get("parameters"),
        )
        
        # Create model locally
        await self.create_model(
            name=model_name,
            modelfile=modelfile,
            stream=True,
        )
        
        # Optionally push to Ollama library
        if metadata.get("push", False):
            await self.push_model(model_name, stream=True)
        
        return model_name
    
    # Required abstract methods (not applicable for local registry connector)
    
    async def submit_job(self, config: TrainingConfig) -> str:
        """Not supported for local registry connector."""
        raise NotImplementedError("Ollama connector does not support training jobs")
    
    async def get_job_status(self, job_id: str) -> JobStatus:
        """Not supported for local registry connector."""
        raise NotImplementedError("Ollama connector does not support training jobs")
    
    async def cancel_job(self, job_id: str) -> bool:
        """Not supported for local registry connector."""
        raise NotImplementedError("Ollama connector does not support training jobs")
    
    async def stream_logs(self, job_id: str) -> AsyncIterator[str]:
        """Not supported for local registry connector."""
        raise NotImplementedError("Ollama connector does not support training jobs")
        yield  # Make it a generator
    
    async def fetch_artifact(self, job_id: str) -> bytes:
        """Not supported for local registry connector."""
        raise NotImplementedError("Ollama connector does not support training jobs")
    
    async def list_resources(self) -> List[Resource]:
        """
        List local compute resources.
        
        For Ollama, this returns the local machine as a resource.
        """
        return [
            Resource(
                id="local",
                name="Local Machine",
                type=ResourceType.GPU,
                gpu_type="Local GPU",
                gpu_count=1,
                available=True,
                region="local",
            )
        ]
    
    async def get_pricing(self, resource_id: str) -> PricingInfo:
        """
        Get pricing information.
        
        Ollama runs locally, so pricing is $0.
        """
        return PricingInfo(
            resource_id=resource_id,
            price_per_hour=0.0,
            currency="USD",
        )
    
    def get_required_credentials(self) -> List[str]:
        """
        Get list of required credential keys.
        
        Ollama typically doesn't require credentials for local use.
        """
        return []
