"""
Tests for backend performance optimizations.

Validates: Requirements 14.4, 14.5
"""

import pytest
import asyncio
import time
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import create_engine
from services.performance_service import (
    HTTPConnectionPool,
    LRUCache,
    DatabaseOptimizer,
    PerformanceMonitor,
    PerformanceService,
    get_http_pool,
    get_request_cache,
    get_db_optimizer,
    get_performance_monitor,
    get_performance_service,
    cache_result,
)


# ============================================================================
# HTTP Connection Pool Tests
# ============================================================================

@pytest.mark.asyncio
async def test_http_connection_pool_creation():
    """Test HTTP connection pool is created correctly."""
    pool = HTTPConnectionPool(max_connections=50, max_connections_per_host=5)
    
    assert pool.max_connections == 50
    assert pool.max_connections_per_host == 5
    assert pool._session is None
    
    # Get session
    session = await pool.get_session()
    assert session is not None
    assert not session.closed
    
    # Close pool
    await pool.close()
    assert session.closed


@pytest.mark.asyncio
async def test_http_connection_pool_reuse():
    """Test HTTP connections are reused."""
    pool = HTTPConnectionPool()
    
    # Get session twice
    session1 = await pool.get_session()
    session2 = await pool.get_session()
    
    # Should be the same session
    assert session1 is session2
    
    await pool.close()


@pytest.mark.asyncio
async def test_http_connection_pool_global():
    """Test global HTTP connection pool."""
    pool = get_http_pool()
    
    assert pool is not None
    assert isinstance(pool, HTTPConnectionPool)
    
    # Should return same instance
    pool2 = get_http_pool()
    assert pool is pool2


# ============================================================================
# LRU Cache Tests
# ============================================================================

@pytest.mark.asyncio
async def test_lru_cache_basic():
    """Test basic LRU cache operations."""
    cache = LRUCache(capacity=3, default_ttl=60)
    
    # Set values
    await cache.set("key1", "value1")
    await cache.set("key2", "value2")
    await cache.set("key3", "value3")
    
    # Get values
    assert await cache.get("key1") == "value1"
    assert await cache.get("key2") == "value2"
    assert await cache.get("key3") == "value3"
    
    # Non-existent key
    assert await cache.get("key4") is None


@pytest.mark.asyncio
async def test_lru_cache_eviction():
    """Test LRU cache evicts least recently used items."""
    cache = LRUCache(capacity=2, default_ttl=60)
    
    # Fill cache
    await cache.set("key1", "value1")
    await cache.set("key2", "value2")
    
    # Add third item (should evict key1)
    await cache.set("key3", "value3")
    
    # key1 should be evicted
    assert await cache.get("key1") is None
    assert await cache.get("key2") == "value2"
    assert await cache.get("key3") == "value3"


@pytest.mark.asyncio
async def test_lru_cache_ttl():
    """Test LRU cache respects TTL."""
    cache = LRUCache(capacity=10, default_ttl=1)
    
    # Set value with 1 second TTL
    await cache.set("key1", "value1", ttl=1)
    
    # Should be available immediately
    assert await cache.get("key1") == "value1"
    
    # Wait for expiry
    await asyncio.sleep(1.1)
    
    # Should be expired
    assert await cache.get("key1") is None


@pytest.mark.asyncio
async def test_lru_cache_stats():
    """Test LRU cache statistics."""
    cache = LRUCache(capacity=10, default_ttl=60)
    
    # Set some values
    await cache.set("key1", "value1")
    await cache.set("key2", "value2")
    
    # Generate hits and misses
    await cache.get("key1")  # hit
    await cache.get("key2")  # hit
    await cache.get("key3")  # miss
    await cache.get("key4")  # miss
    
    stats = cache.get_stats()
    
    assert stats["capacity"] == 10
    assert stats["size"] == 2
    assert stats["hits"] == 2
    assert stats["misses"] == 2
    assert stats["hit_rate"] == 0.5


@pytest.mark.asyncio
async def test_cache_result_decorator():
    """Test cache_result decorator."""
    call_count = 0
    
    @cache_result(ttl=60)
    async def expensive_function(x: int) -> int:
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.1)  # Simulate expensive operation
        return x * 2
    
    # First call should execute function
    result1 = await expensive_function(5)
    assert result1 == 10
    assert call_count == 1
    
    # Second call should use cache
    result2 = await expensive_function(5)
    assert result2 == 10
    assert call_count == 1  # Not incremented
    
    # Different argument should execute function
    result3 = await expensive_function(10)
    assert result3 == 20
    assert call_count == 2


# ============================================================================
# Database Optimizer Tests
# ============================================================================

def test_database_optimizer_creation():
    """Test database optimizer is created correctly."""
    optimizer = DatabaseOptimizer()
    
    assert optimizer.slow_query_threshold == 1.0
    assert len(optimizer.query_times) == 0
    assert len(optimizer.slow_queries) == 0


def test_database_optimizer_stats():
    """Test database optimizer statistics."""
    optimizer = DatabaseOptimizer()
    
    # Add some query times
    optimizer.query_times = [0.1, 0.2, 0.3, 0.5, 1.5]
    optimizer.slow_queries = [
        {"statement": "SELECT * FROM table", "time": 1.5}
    ]
    
    stats = optimizer.get_query_stats()
    
    assert stats["total_queries"] == 5
    assert stats["avg_time"] == 0.52
    assert stats["max_time"] == 1.5
    assert stats["min_time"] == 0.1
    assert stats["slow_queries"] == 1


def test_database_optimizer_connection_pool():
    """Test database connection pool configuration."""
    optimizer = DatabaseOptimizer()
    engine = create_engine("sqlite:///:memory:")
    
    # Setup connection pool
    optimizer.setup_connection_pool(engine)
    
    # Verify pool is configured
    assert engine.pool is not None
    assert hasattr(engine.pool, 'size')


# ============================================================================
# Performance Monitor Tests
# ============================================================================

def test_performance_monitor_creation():
    """Test performance monitor is created correctly."""
    monitor = PerformanceMonitor()
    
    assert len(monitor.request_times) == 0
    assert len(monitor.endpoint_times) == 0
    assert monitor.error_count == 0
    assert monitor.request_count == 0


def test_performance_monitor_record_request():
    """Test recording request metrics."""
    monitor = PerformanceMonitor()
    
    # Record some requests
    monitor.record_request("/api/test", 0.1, error=False)
    monitor.record_request("/api/test", 0.2, error=False)
    monitor.record_request("/api/other", 0.3, error=True)
    
    assert monitor.request_count == 3
    assert monitor.error_count == 1
    assert len(monitor.request_times) == 3
    assert len(monitor.endpoint_times["/api/test"]) == 2
    assert len(monitor.endpoint_times["/api/other"]) == 1


def test_performance_monitor_metrics():
    """Test performance metrics calculation."""
    monitor = PerformanceMonitor()
    
    # Record requests
    monitor.record_request("/api/test", 0.1, error=False)
    monitor.record_request("/api/test", 0.2, error=False)
    monitor.record_request("/api/test", 0.3, error=True)
    
    metrics = monitor.get_metrics()
    
    assert metrics["total_requests"] == 3
    assert abs(metrics["avg_response_time"] - 0.2) < 0.001  # Floating point tolerance
    assert metrics["max_response_time"] == 0.3
    assert metrics["min_response_time"] == 0.1
    assert abs(metrics["error_rate"] - 1/3) < 0.001
    assert metrics["error_count"] == 1


def test_performance_monitor_endpoint_metrics():
    """Test endpoint-specific metrics."""
    monitor = PerformanceMonitor()
    
    # Record requests for specific endpoint
    monitor.record_request("/api/test", 0.1)
    monitor.record_request("/api/test", 0.3)
    monitor.record_request("/api/test", 0.2)
    
    metrics = monitor.get_endpoint_metrics("/api/test")
    
    assert metrics["endpoint"] == "/api/test"
    assert metrics["total_requests"] == 3
    assert abs(metrics["avg_response_time"] - 0.2) < 0.001  # Floating point tolerance
    assert metrics["max_response_time"] == 0.3
    assert metrics["min_response_time"] == 0.1


def test_performance_monitor_slowest_endpoints():
    """Test identifying slowest endpoints."""
    monitor = PerformanceMonitor()
    
    # Record requests for multiple endpoints
    monitor.record_request("/api/fast", 0.1)
    monitor.record_request("/api/fast", 0.1)
    monitor.record_request("/api/slow", 1.0)
    monitor.record_request("/api/slow", 1.2)
    monitor.record_request("/api/medium", 0.5)
    
    slowest = monitor.get_slowest_endpoints(limit=3)
    
    assert len(slowest) == 3
    assert slowest[0]["endpoint"] == "/api/slow"
    assert slowest[0]["avg_time"] == 1.1
    assert slowest[1]["endpoint"] == "/api/medium"
    assert slowest[2]["endpoint"] == "/api/fast"


def test_performance_monitor_system_metrics():
    """Test system metrics collection."""
    monitor = PerformanceMonitor()
    
    metrics = monitor.get_system_metrics()
    
    assert "cpu_percent" in metrics
    assert "memory_percent" in metrics
    assert "memory_used_mb" in metrics
    assert "memory_available_mb" in metrics
    assert "disk_percent" in metrics
    assert "disk_used_gb" in metrics
    assert "disk_free_gb" in metrics
    
    # Verify values are reasonable
    assert 0 <= metrics["cpu_percent"] <= 100
    assert 0 <= metrics["memory_percent"] <= 100
    assert metrics["memory_used_mb"] > 0
    assert metrics["disk_free_gb"] > 0


# ============================================================================
# Performance Service Tests
# ============================================================================

@pytest.mark.asyncio
async def test_performance_service_creation():
    """Test performance service is created correctly."""
    service = PerformanceService()
    
    assert service.http_pool is not None
    assert service.cache is not None
    assert service.db_optimizer is not None
    assert service.monitor is not None


@pytest.mark.asyncio
async def test_performance_service_initialize():
    """Test performance service initialization."""
    service = PerformanceService()
    engine = create_engine("sqlite:///:memory:")
    
    # Initialize service
    await service.initialize(engine)
    
    # Verify initialization
    assert engine.pool is not None


@pytest.mark.asyncio
async def test_performance_service_get_all_metrics():
    """Test getting all performance metrics."""
    service = PerformanceService()
    
    # Record some activity
    service.monitor.record_request("/api/test", 0.1)
    await service.cache.set("test_key", "test_value")
    
    metrics = service.get_all_metrics()
    
    assert "cache" in metrics
    assert "database" in metrics
    assert "requests" in metrics
    assert "system" in metrics
    assert "timestamp" in metrics


@pytest.mark.asyncio
async def test_performance_service_recommendations():
    """Test optimization recommendations."""
    service = PerformanceService()
    
    # Create conditions for recommendations
    # Low cache hit rate
    for i in range(10):
        await service.cache.get(f"missing_key_{i}")  # All misses
    
    # Slow queries - need to also add to query_times for stats
    service.db_optimizer.slow_queries = [
        {"statement": f"SELECT * FROM table{i}", "time": 1.5}
        for i in range(15)
    ]
    service.db_optimizer.query_times = [1.5] * 15  # Add query times
    
    # High response times
    for i in range(10):
        service.monitor.record_request("/api/slow", 2.0)
    
    recommendations = service.get_optimization_recommendations()
    
    assert len(recommendations) > 0
    assert any("cache" in r.lower() for r in recommendations)
    # Check for slow query recommendation
    assert any(("slow" in r.lower() and "quer" in r.lower()) or "index" in r.lower() for r in recommendations)
    assert any("response time" in r.lower() for r in recommendations)


@pytest.mark.asyncio
async def test_performance_service_cleanup():
    """Test performance service cleanup."""
    service = PerformanceService()
    
    # Add some data
    await service.cache.set("test_key", "test_value")
    
    # Cleanup
    await service.cleanup()
    
    # Verify cleanup
    stats = service.cache.get_stats()
    assert stats["size"] == 0


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_global_services():
    """Test global service instances."""
    # Get global instances
    http_pool = get_http_pool()
    cache = get_request_cache()
    db_optimizer = get_db_optimizer()
    monitor = get_performance_monitor()
    service = get_performance_service()
    
    # Verify they are singletons
    assert get_http_pool() is http_pool
    assert get_request_cache() is cache
    assert get_db_optimizer() is db_optimizer
    assert get_performance_monitor() is monitor
    assert get_performance_service() is service


@pytest.mark.asyncio
async def test_end_to_end_performance_optimization():
    """Test end-to-end performance optimization flow."""
    # Create a fresh service instance for this test
    from services.performance_service import (
        PerformanceService,
        PerformanceMonitor,
        LRUCache,
        DatabaseOptimizer
    )
    
    # Create fresh instances
    monitor = PerformanceMonitor()
    cache = LRUCache()
    db_optimizer = DatabaseOptimizer()
    
    service = PerformanceService()
    service.monitor = monitor
    service.cache = cache
    service.db_optimizer = db_optimizer
    
    engine = create_engine("sqlite:///:memory:")
    
    # Initialize
    await service.initialize(engine)
    
    # Simulate API requests
    for i in range(5):
        service.monitor.record_request("/api/test", 0.1 + i * 0.1)
    
    # Use cache directly on the service's cache instance
    await service.cache.set("test_key", "test_value")
    value1 = await service.cache.get("test_key")  # hit
    value2 = await service.cache.get("test_key")  # hit
    
    assert value1 == value2 == "test_value"
    
    # Get metrics
    metrics = service.get_all_metrics()
    
    assert metrics["requests"]["total_requests"] == 5
    assert metrics["cache"]["hits"] >= 2  # At least 2 hits from our cache operations
    
    # Get recommendations
    recommendations = service.get_optimization_recommendations()
    assert isinstance(recommendations, list)
    
    # Cleanup
    await service.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
