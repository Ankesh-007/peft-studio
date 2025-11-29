"""
Model Registry Service for HuggingFace Hub integration.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import logging
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
    """Metadata for a model from HuggingFace Hub"""
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


class ModelRegistryService:
    """Service for interacting with HuggingFace model registry"""
    
    def __init__(self):
        self.api = HfApi()
        self._model_cache: Dict[str, ModelMetadata] = {}
        logger.info("ModelRegistryService initialized")
    
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
    
    def clear_cache(self) -> None:
        """Clear the model metadata cache"""
        self._model_cache.clear()
        logger.info("Model metadata cache cleared")


# Singleton instance
_model_registry_service_instance = None


def get_model_registry_service() -> ModelRegistryService:
    """Get singleton instance of ModelRegistryService"""
    global _model_registry_service_instance
    if _model_registry_service_instance is None:
        _model_registry_service_instance = ModelRegistryService()
    return _model_registry_service_instance
