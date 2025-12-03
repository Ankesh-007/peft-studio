"""
Integration tests for the unified model browser functionality.
"""

import pytest
from services.model_registry_service import ModelRegistryService, ModelMetadata


def test_model_registry_service_initialization():
    """Test that ModelRegistryService initializes correctly"""
    service = ModelRegistryService()
    assert service is not None
    assert service.api is not None


def test_search_multi_registry():
    """Test multi-registry search aggregation"""
    service = ModelRegistryService()
    
    # Search across registries
    results = service.search_multi_registry(
        query="llama",
        task="text-generation",
        registries=["huggingface"],
        limit=5
    )
    
    assert isinstance(results, list)
    # Results should have registry field
    for model in results:
        assert hasattr(model, 'registry')
        assert model.registry in ['huggingface', 'civitai', 'ollama']


def test_cache_model_metadata():
    """Test caching model metadata"""
    service = ModelRegistryService()
    
    # Create test metadata
    metadata = ModelMetadata(
        model_id="test/model",
        author="test",
        model_name="test-model",
        downloads=100,
        likes=10,
        tags=["test"],
        pipeline_tag="text-generation",
        library_name="transformers",
        size_mb=1000.0,
        parameters=7_000_000_000,
        architecture="llama",
        license="apache-2.0",
        created_at="2024-01-01",
        last_modified="2024-01-01",
        registry="huggingface"
    )
    
    # Cache the metadata
    service.cache_model_metadata("test/model", "huggingface", metadata, ttl_hours=1)
    
    # Retrieve from cache
    cached = service.get_cached_metadata("test/model", "huggingface")
    assert cached is not None
    assert cached.model_id == "test/model"
    assert cached.registry == "huggingface"
    
    # Clean up
    service.remove_from_cache("test/model", "huggingface")


def test_list_cached_models():
    """Test listing cached models"""
    service = ModelRegistryService()
    
    # Clear cache first
    service.clear_cache()
    
    # Add some test models to cache
    for i in range(3):
        metadata = ModelMetadata(
            model_id=f"test/model-{i}",
            author="test",
            model_name=f"test-model-{i}",
            downloads=100,
            likes=10,
            tags=["test"],
            pipeline_tag="text-generation",
            library_name="transformers",
            size_mb=1000.0,
            parameters=7_000_000_000,
            architecture="llama",
            license="apache-2.0",
            created_at="2024-01-01",
            last_modified="2024-01-01",
            registry="huggingface"
        )
        service.cache_model_metadata(f"test/model-{i}", "huggingface", metadata, ttl_hours=1)
    
    # List cached models
    cached_models = service.list_cached_models()
    assert len(cached_models) >= 3
    
    # Clean up
    service.clear_cache()


def test_remove_from_cache():
    """Test removing a model from cache"""
    service = ModelRegistryService()
    
    # Add a test model
    metadata = ModelMetadata(
        model_id="test/remove-model",
        author="test",
        model_name="remove-model",
        downloads=100,
        likes=10,
        tags=["test"],
        pipeline_tag="text-generation",
        library_name="transformers",
        size_mb=1000.0,
        parameters=7_000_000_000,
        architecture="llama",
        license="apache-2.0",
        created_at="2024-01-01",
        last_modified="2024-01-01",
        registry="huggingface"
    )
    service.cache_model_metadata("test/remove-model", "huggingface", metadata, ttl_hours=1)
    
    # Verify it's cached
    cached = service.get_cached_metadata("test/remove-model", "huggingface")
    assert cached is not None
    
    # Remove from cache
    success = service.remove_from_cache("test/remove-model", "huggingface")
    assert success is True
    
    # Verify it's removed
    cached = service.get_cached_metadata("test/remove-model", "huggingface")
    assert cached is None


def test_clear_cache():
    """Test clearing all cache"""
    service = ModelRegistryService()
    
    # Add some test models
    for i in range(2):
        metadata = ModelMetadata(
            model_id=f"test/clear-{i}",
            author="test",
            model_name=f"clear-{i}",
            downloads=100,
            likes=10,
            tags=["test"],
            pipeline_tag="text-generation",
            library_name="transformers",
            size_mb=1000.0,
            parameters=7_000_000_000,
            architecture="llama",
            license="apache-2.0",
            created_at="2024-01-01",
            last_modified="2024-01-01",
            registry="huggingface"
        )
        service.cache_model_metadata(f"test/clear-{i}", "huggingface", metadata, ttl_hours=1)
    
    # Clear cache
    service.clear_cache()
    
    # Verify cache is empty
    cached_models = service.list_cached_models()
    # Should be empty or only contain non-test models
    test_models = [m for m in cached_models if m.model_id.startswith("test/clear-")]
    assert len(test_models) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
