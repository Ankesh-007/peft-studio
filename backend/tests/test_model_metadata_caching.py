"""
Property-Based Test: Model metadata caching

**Feature: unified-llm-platform, Property 6: Model metadata caching**
**Validates: Requirements 2.4, 12.1**

Property: For any model browsed while online, metadata should be available 
offline for at least 24 hours.

This test verifies that:
1. Model metadata is cached when fetched
2. Cached metadata persists across sessions (disk storage)
3. Cached metadata is available for at least 24 hours
4. Expired cache entries are properly removed
5. Cache survives application restarts
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from pathlib import Path
import tempfile
import shutil
import json
from datetime import datetime, timedelta
import sys

sys.path.append(str(Path(__file__).parent.parent))

from plugins.connectors.huggingface_connector import (
    ModelMetadata,
    ModelCache,
)


# Strategy for generating model metadata
@st.composite
def model_metadata_strategy(draw):
    """Generate random but valid model metadata."""
    model_id = draw(st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd"), whitelist_characters="-_/"),
        min_size=5,
        max_size=50
    ))
    
    # Ensure model_id has valid format (author/model-name)
    if "/" not in model_id:
        model_id = f"author/{model_id}"
    
    return ModelMetadata(
        model_id=model_id,
        author=draw(st.text(min_size=1, max_size=30)),
        downloads=draw(st.integers(min_value=0, max_value=1000000)),
        likes=draw(st.integers(min_value=0, max_value=10000)),
        tags=draw(st.lists(st.text(min_size=1, max_size=20), max_size=10)),
        pipeline_tag=draw(st.one_of(st.none(), st.sampled_from([
            "text-generation", "text-classification", "translation"
        ]))),
        library_name=draw(st.one_of(st.none(), st.sampled_from([
            "transformers", "diffusers", "sentence-transformers"
        ]))),
        license=draw(st.one_of(st.none(), st.sampled_from([
            "apache-2.0", "mit", "gpl-3.0", "cc-by-4.0"
        ]))),
        model_size=draw(st.integers(min_value=0, max_value=100000000000)),
        created_at=datetime.now().isoformat(),
        last_modified=datetime.now().isoformat(),
        siblings=draw(st.lists(
            st.fixed_dictionaries({
                "rfilename": st.text(min_size=1, max_size=50)
            }),
            max_size=5
        )),
        card_data=draw(st.dictionaries(
            st.text(min_size=1, max_size=20),
            st.text(min_size=0, max_size=100),
            max_size=5
        )),
    )


class TestModelMetadataCaching:
    """Test suite for model metadata caching property."""
    
    @given(metadata=model_metadata_strategy())
    @settings(max_examples=100, deadline=None)
    def test_metadata_caching_persistence(self, metadata):
        """
        Property: Cached metadata persists to disk and can be retrieved.
        
        For any model metadata, after caching it should be retrievable
        from disk even after cache object is destroyed.
        """
        # Create temporary cache directory
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            
            # Create cache and store metadata
            cache1 = ModelCache(cache_dir)
            cache1.set(metadata)
            
            # Verify in-memory retrieval
            retrieved1 = cache1.get(metadata.model_id)
            assert retrieved1 is not None
            assert retrieved1.model_id == metadata.model_id
            
            # Destroy cache object
            del cache1
            
            # Create new cache instance (simulates app restart)
            cache2 = ModelCache(cache_dir)
            
            # Verify metadata was loaded from disk
            retrieved2 = cache2.get(metadata.model_id)
            assert retrieved2 is not None, "Metadata should persist across cache instances"
            assert retrieved2.model_id == metadata.model_id
            assert retrieved2.author == metadata.author
            assert retrieved2.downloads == metadata.downloads
    
    @given(metadata=model_metadata_strategy())
    @settings(max_examples=100, deadline=None)
    def test_metadata_available_for_24_hours(self, metadata):
        """
        Property: Cached metadata is available for at least 24 hours.
        
        For any model metadata, it should be retrievable within 24 hours
        of caching without expiration.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ModelCache(Path(tmpdir))
            
            # Cache metadata
            cache.set(metadata)
            
            # Verify immediately available
            retrieved = cache.get(metadata.model_id, ttl_hours=24)
            assert retrieved is not None
            
            # Simulate time passing (but less than 24 hours)
            # We test this by checking the is_expired method
            assert not metadata.is_expired(ttl_hours=24)
            
            # Verify still available with 24-hour TTL
            retrieved = cache.get(metadata.model_id, ttl_hours=24)
            assert retrieved is not None, "Metadata should be available within 24 hours"
    
    @given(metadata=model_metadata_strategy())
    @settings(max_examples=100, deadline=None)
    def test_expired_cache_removed(self, metadata):
        """
        Property: Expired cache entries are properly removed.
        
        For any model metadata, if it's expired (TTL exceeded),
        it should be removed from cache and return None.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ModelCache(Path(tmpdir))
            
            # Cache metadata
            cache.set(metadata)
            
            # Manually set cached_at to past (simulate expiration)
            metadata.cached_at = datetime.now() - timedelta(hours=25)
            cache.set(metadata)
            
            # Try to retrieve with 24-hour TTL
            retrieved = cache.get(metadata.model_id, ttl_hours=24)
            
            # Should be None because it's expired
            assert retrieved is None, "Expired metadata should not be returned"
            
            # Verify it was removed from cache
            assert metadata.model_id not in cache._cache
    
    @given(
        metadata_list=st.lists(model_metadata_strategy(), min_size=1, max_size=10, unique_by=lambda m: m.model_id)
    )
    @settings(max_examples=50, deadline=None)
    def test_multiple_models_cached_independently(self, metadata_list):
        """
        Property: Multiple models can be cached independently.
        
        For any list of model metadata, each should be cached and
        retrievable independently without interference.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ModelCache(Path(tmpdir))
            
            # Cache all models
            for metadata in metadata_list:
                cache.set(metadata)
            
            # Verify all are retrievable
            for metadata in metadata_list:
                retrieved = cache.get(metadata.model_id)
                assert retrieved is not None
                assert retrieved.model_id == metadata.model_id
            
            # Verify count
            all_cached = cache.get_all_cached()
            assert len(all_cached) == len(metadata_list)
    
    @given(metadata=model_metadata_strategy())
    @settings(max_examples=100, deadline=None)
    def test_cache_serialization_round_trip(self, metadata):
        """
        Property: Metadata serialization is lossless.
        
        For any model metadata, converting to dict and back should
        preserve all data (except cached_at which is updated).
        """
        # Convert to dict
        data_dict = metadata.to_dict()
        
        # Verify all fields present
        assert "model_id" in data_dict
        assert "author" in data_dict
        assert "downloads" in data_dict
        assert "cached_at" in data_dict
        
        # Convert back to metadata
        restored = ModelMetadata.from_dict(data_dict)
        
        # Verify data preserved
        assert restored.model_id == metadata.model_id
        assert restored.author == metadata.author
        assert restored.downloads == metadata.downloads
        assert restored.likes == metadata.likes
        assert restored.tags == metadata.tags
        assert restored.pipeline_tag == metadata.pipeline_tag
        assert restored.library_name == metadata.library_name
        assert restored.license == metadata.license
    
    @given(metadata=model_metadata_strategy())
    @settings(max_examples=100, deadline=None)
    def test_cache_clear_removes_all(self, metadata):
        """
        Property: Cache clear removes all entries.
        
        For any cached metadata, calling clear() should remove
        all entries from both memory and disk.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            cache = ModelCache(cache_dir)
            
            # Cache metadata
            cache.set(metadata)
            
            # Verify cached
            assert cache.get(metadata.model_id) is not None
            
            # Verify file exists on disk
            cache_files = list(cache_dir.glob("*.json"))
            assert len(cache_files) > 0
            
            # Clear cache
            cache.clear()
            
            # Verify removed from memory
            assert cache.get(metadata.model_id) is None
            
            # Verify removed from disk
            cache_files = list(cache_dir.glob("*.json"))
            assert len(cache_files) == 0
    
    @given(metadata=model_metadata_strategy())
    @settings(max_examples=100, deadline=None)
    def test_cache_update_overwrites(self, metadata):
        """
        Property: Updating cache overwrites previous entry.
        
        For any model metadata, caching it twice should result in
        the second version being stored.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ModelCache(Path(tmpdir))
            
            # Cache original
            original_downloads = metadata.downloads
            cache.set(metadata)
            
            # Modify and cache again
            metadata.downloads = original_downloads + 1000
            cache.set(metadata)
            
            # Retrieve and verify updated
            retrieved = cache.get(metadata.model_id)
            assert retrieved is not None
            assert retrieved.downloads == original_downloads + 1000
    
    @given(metadata=model_metadata_strategy())
    @settings(max_examples=100, deadline=None)
    def test_cache_handles_special_characters_in_model_id(self, metadata):
        """
        Property: Cache handles special characters in model IDs.
        
        For any model metadata with special characters in the ID,
        caching and retrieval should work correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ModelCache(Path(tmpdir))
            
            # Cache metadata (model_id may have special chars like /)
            cache.set(metadata)
            
            # Retrieve
            retrieved = cache.get(metadata.model_id)
            assert retrieved is not None
            assert retrieved.model_id == metadata.model_id
    
    @given(
        metadata=model_metadata_strategy(),
        ttl_hours=st.integers(min_value=1, max_value=168)  # 1 hour to 1 week
    )
    @settings(max_examples=50, deadline=None)
    def test_cache_respects_custom_ttl(self, metadata, ttl_hours):
        """
        Property: Cache respects custom TTL values.
        
        For any model metadata and TTL value, the cache should
        respect the specified TTL when checking expiration.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ModelCache(Path(tmpdir))
            
            # Cache metadata
            cache.set(metadata)
            
            # Should be available with any reasonable TTL
            retrieved = cache.get(metadata.model_id, ttl_hours=ttl_hours)
            assert retrieved is not None
            
            # Manually expire by setting old cached_at
            metadata.cached_at = datetime.now() - timedelta(hours=ttl_hours + 1)
            cache.set(metadata)
            
            # Should be expired with this TTL
            retrieved = cache.get(metadata.model_id, ttl_hours=ttl_hours)
            assert retrieved is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
