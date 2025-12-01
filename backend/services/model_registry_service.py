"""
Model Registry Service for multi-registry integration (HuggingFace, Civitai, Ollama).
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging
import json
import sqlite3
from pathlib import Path
from huggingface_hub import HfApi, list_models
try:
    from huggingface_hub import ModelFilter
except ImportError:
    # ModelFilter might not be available in all versions
    ModelFilter = None
from huggingface_hub.utils import RepositoryNotFoundError

logger = logging.getLogger(__name__)


@dataclass
class ModelMetadata:
    """Metadata for a model from any registry"""
    model_id: str
    author: str
    model_name: str
    downloads: int
    likes: int
    tags: List[str]
    pipeline_tag: Optional[str]
    library_name: Optional[str]
    size_mb: Optional[float]
    parameters: Optional[int]
    architecture: Optional[str]
    license: Optional[str]
    created_at: Optional[str]
    last_modified: Optional[str]
    registry: str = "huggingface"  # huggingface, civitai, ollama


@dataclass
class CachedModel:
    """Cached model metadata"""
    model_id: str
    registry: str
    cached_at: str
    expires_at: str
    metadata: Dict


class ModelRegistryService:
    """Service for interacting with multiple model registries"""
    
    def __init__(self, db_path: str = "~/.peft-studio/data/peft_studio.db"):
        self.api = HfApi()
        self._model_cache: Dict[str, ModelMetadata] = {}
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_cache_db()
        logger.info("ModelRegistryService initialized with multi-registry support")
    
    def _init_cache_db(self):
        """Initialize the cache database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_cache (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                model_id TEXT NOT NULL,
                metadata TEXT NOT NULL,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
        """)
        conn.commit()
        conn.close()
    
    def search_models(
        self,
        query: Optional[str] = None,
        task: Optional[str] = None,
        library: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 20,
        sort: str = "downloads"
    ) -> List[ModelMetadata]:
        """
        Search for models on HuggingFace Hub.
        
        Args:
            query: Search query string
            task: Filter by task (e.g., "text-generation")
            library: Filter by library (e.g., "transformers")
            tags: Filter by tags
            limit: Maximum number of results
            sort: Sort by "downloads", "likes", or "trending"
            
        Returns:
            List of ModelMetadata objects
        """
        try:
            logger.info(f"Searching models: query={query}, task={task}, limit={limit}")
            
            # Build filter
            model_filter = ModelFilter()
            if task:
                model_filter = ModelFilter(task=task)
            if library:
                model_filter.library = library
            if tags:
                model_filter.tags = tags
            
            # Search models
            models = list_models(
                filter=model_filter,
                search=query,
                sort=sort,
                direction=-1,  # Descending
                limit=limit
            )
            
            results = []
            for model in models:
                metadata = self._convert_to_metadata(model)
                results.append(metadata)
                # Cache the result
                self._model_cache[model.modelId] = metadata
            
            logger.info(f"Found {len(results)} models")
            return results
            
        except Exception as e:
            logger.error(f"Error searching models: {str(e)}")
            return []
    
    def get_model_info(self, model_id: str, use_cache: bool = True) -> Optional[ModelMetadata]:
        """
        Get detailed information about a specific model.
        
        Args:
            model_id: HuggingFace model ID (e.g., "meta-llama/Llama-2-7b-hf")
            use_cache: Whether to use cached data if available
            
        Returns:
            ModelMetadata object or None if not found
        """
        # Check cache
        if use_cache and model_id in self._model_cache:
            logger.debug(f"Returning cached info for {model_id}")
            return self._model_cache[model_id]
        
        try:
            logger.info(f"Fetching model info for {model_id}")
            model_info = self.api.model_info(model_id)
            metadata = self._convert_to_metadata(model_info)
            
            # Cache the result
            self._model_cache[model_id] = metadata
            
            return metadata
            
        except RepositoryNotFoundError:
            logger.warning(f"Model not found: {model_id}")
            return None
        except Exception as e:
            logger.error(f"Error fetching model info for {model_id}: {str(e)}")
            return None
    
    def get_popular_models(
        self,
        task: str = "text-generation",
        limit: int = 10
    ) -> List[ModelMetadata]:
        """
        Get popular models for a specific task.
        
        Args:
            task: Task type (e.g., "text-generation")
            limit: Maximum number of results
            
        Returns:
            List of ModelMetadata objects
        """
        return self.search_models(
            task=task,
            library="transformers",
            limit=limit,
            sort="downloads"
        )
    
    def get_compatible_models(
        self,
        min_parameters: Optional[int] = None,
        max_parameters: Optional[int] = None,
        architectures: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[ModelMetadata]:
        """
        Get models compatible with specific criteria.
        
        Args:
            min_parameters: Minimum number of parameters
            max_parameters: Maximum number of parameters
            architectures: List of compatible architectures
            limit: Maximum number of results
            
        Returns:
            List of ModelMetadata objects
        """
        # Get all text-generation models
        all_models = self.search_models(
            task="text-generation",
            library="transformers",
            limit=limit * 2  # Get more to filter
        )
        
        # Filter by criteria
        filtered = []
        for model in all_models:
            # Check parameters
            if min_parameters and model.parameters:
                if model.parameters < min_parameters:
                    continue
            if max_parameters and model.parameters:
                if model.parameters > max_parameters:
                    continue
            
            # Check architecture
            if architectures and model.architecture:
                if model.architecture not in architectures:
                    continue
            
            filtered.append(model)
            
            if len(filtered) >= limit:
                break
        
        return filtered
    
    def validate_model_exists(self, model_id: str) -> bool:
        """
        Check if a model exists on HuggingFace Hub.
        
        Args:
            model_id: HuggingFace model ID
            
        Returns:
            True if model exists, False otherwise
        """
        try:
            self.api.model_info(model_id)
            return True
        except RepositoryNotFoundError:
            return False
        except Exception as e:
            logger.error(f"Error validating model {model_id}: {str(e)}")
            return False
    
    def _convert_to_metadata(self, model_info) -> ModelMetadata:
        """Convert HuggingFace model info to ModelMetadata"""
        # Extract model name from ID
        model_id = model_info.modelId
        parts = model_id.split("/")
        author = parts[0] if len(parts) > 1 else "unknown"
        model_name = parts[-1]
        
        # Extract parameters from tags or config
        parameters = None
        architecture = None
        size_mb = None
        
        # Try to extract from tags
        for tag in (model_info.tags or []):
            if "parameters" in tag.lower() or "b" in tag.lower():
                # Try to parse parameter count (e.g., "7b", "13b")
                try:
                    if "b" in tag.lower():
                        num = float(tag.lower().replace("b", "").strip())
                        parameters = int(num * 1_000_000_000)
                except:
                    pass
            
            # Extract architecture
            if any(arch in tag.lower() for arch in ["llama", "mistral", "gpt", "falcon", "mpt"]):
                architecture = tag
        
        # Try to get size from siblings (files)
        try:
            if hasattr(model_info, 'siblings') and model_info.siblings:
                total_size = sum(
                    file.size for file in model_info.siblings 
                    if hasattr(file, 'size') and file.size
                )
                size_mb = total_size / (1024 * 1024) if total_size > 0 else None
        except:
            pass
        
        return ModelMetadata(
            model_id=model_id,
            author=author,
            model_name=model_name,
            downloads=getattr(model_info, 'downloads', 0) or 0,
            likes=getattr(model_info, 'likes', 0) or 0,
            tags=model_info.tags or [],
            pipeline_tag=getattr(model_info, 'pipeline_tag', None),
            library_name=getattr(model_info, 'library_name', None),
            size_mb=size_mb,
            parameters=parameters,
            architecture=architecture,
            license=getattr(model_info, 'license', None),
            created_at=str(getattr(model_info, 'created_at', None)),
            last_modified=str(getattr(model_info, 'last_modified', None))
        )
    
    def search_multi_registry(
        self,
        query: Optional[str] = None,
        task: Optional[str] = None,
        registries: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[ModelMetadata]:
        """
        Search across multiple registries and aggregate results.
        
        Args:
            query: Search query string
            task: Filter by task
            registries: List of registries to search (default: all)
            limit: Maximum number of results per registry
            
        Returns:
            Aggregated list of ModelMetadata objects from all registries
        """
        if registries is None:
            registries = ["huggingface"]  # Add "civitai", "ollama" when implemented
        
        all_results = []
        
        # Search HuggingFace
        if "huggingface" in registries:
            try:
                hf_results = self.search_models(query=query, task=task, limit=limit)
                for model in hf_results:
                    model.registry = "huggingface"
                all_results.extend(hf_results)
            except Exception as e:
                logger.error(f"Error searching HuggingFace: {str(e)}")
        
        # TODO: Add Civitai search when connector is implemented
        # TODO: Add Ollama search when connector is implemented
        
        # Sort by downloads (descending)
        all_results.sort(key=lambda m: m.downloads, reverse=True)
        
        return all_results[:limit * len(registries)]
    
    def cache_model_metadata(
        self,
        model_id: str,
        registry: str,
        metadata: ModelMetadata,
        ttl_hours: int = 24
    ) -> None:
        """
        Cache model metadata to database.
        
        Args:
            model_id: Model identifier
            registry: Registry name
            metadata: Model metadata to cache
            ttl_hours: Time to live in hours
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cache_id = f"{registry}:{model_id}"
            cached_at = datetime.now().isoformat()
            expires_at = (datetime.now() + timedelta(hours=ttl_hours)).isoformat()
            metadata_json = json.dumps(asdict(metadata))
            
            cursor.execute("""
                INSERT OR REPLACE INTO model_cache 
                (id, source, model_id, metadata, cached_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (cache_id, registry, model_id, metadata_json, cached_at, expires_at))
            
            conn.commit()
            conn.close()
            logger.debug(f"Cached metadata for {cache_id}")
        except Exception as e:
            logger.error(f"Error caching model metadata: {str(e)}")
    
    def get_cached_metadata(
        self,
        model_id: str,
        registry: str
    ) -> Optional[ModelMetadata]:
        """
        Get cached model metadata if available and not expired.
        
        Args:
            model_id: Model identifier
            registry: Registry name
            
        Returns:
            ModelMetadata if cached and valid, None otherwise
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cache_id = f"{registry}:{model_id}"
            cursor.execute("""
                SELECT metadata, expires_at FROM model_cache
                WHERE id = ?
            """, (cache_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                metadata_json, expires_at = row
                expires_dt = datetime.fromisoformat(expires_at)
                
                if datetime.now() < expires_dt:
                    metadata_dict = json.loads(metadata_json)
                    return ModelMetadata(**metadata_dict)
                else:
                    # Expired, remove from cache
                    self.remove_from_cache(model_id, registry)
            
            return None
        except Exception as e:
            logger.error(f"Error getting cached metadata: {str(e)}")
            return None
    
    def list_cached_models(self) -> List[CachedModel]:
        """
        List all cached models.
        
        Returns:
            List of CachedModel objects
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT model_id, source, cached_at, expires_at, metadata
                FROM model_cache
                WHERE expires_at > ?
                ORDER BY cached_at DESC
            """, (datetime.now().isoformat(),))
            
            rows = cursor.fetchall()
            conn.close()
            
            cached_models = []
            for row in rows:
                model_id, registry, cached_at, expires_at, metadata_json = row
                metadata = json.loads(metadata_json)
                cached_models.append(CachedModel(
                    model_id=model_id,
                    registry=registry,
                    cached_at=cached_at,
                    expires_at=expires_at,
                    metadata=metadata
                ))
            
            return cached_models
        except Exception as e:
            logger.error(f"Error listing cached models: {str(e)}")
            return []
    
    def remove_from_cache(
        self,
        model_id: str,
        registry: str
    ) -> bool:
        """
        Remove a model from cache.
        
        Args:
            model_id: Model identifier
            registry: Registry name
            
        Returns:
            True if removed, False otherwise
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cache_id = f"{registry}:{model_id}"
            cursor.execute("DELETE FROM model_cache WHERE id = ?", (cache_id,))
            
            conn.commit()
            rows_deleted = cursor.rowcount
            conn.close()
            
            if rows_deleted > 0:
                logger.info(f"Removed {cache_id} from cache")
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing from cache: {str(e)}")
            return False
    
    def clear_cache(self) -> None:
        """Clear all model metadata cache"""
        try:
            # Clear in-memory cache
            self._model_cache.clear()
            
            # Clear database cache
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("DELETE FROM model_cache")
            conn.commit()
            conn.close()
            
            logger.info("Model metadata cache cleared")
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
    
    def clear_expired_cache(self) -> int:
        """
        Clear expired cache entries.
        
        Returns:
            Number of entries removed
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM model_cache
                WHERE expires_at < ?
            """, (datetime.now().isoformat(),))
            
            conn.commit()
            rows_deleted = cursor.rowcount
            conn.close()
            
            logger.info(f"Cleared {rows_deleted} expired cache entries")
            return rows_deleted
        except Exception as e:
            logger.error(f"Error clearing expired cache: {str(e)}")
            return 0


# Singleton instance
_model_registry_service_instance = None


def get_model_registry_service() -> ModelRegistryService:
    """Get singleton instance of ModelRegistryService"""
    global _model_registry_service_instance
    if _model_registry_service_instance is None:
        _model_registry_service_instance = ModelRegistryService()
    return _model_registry_service_instance
