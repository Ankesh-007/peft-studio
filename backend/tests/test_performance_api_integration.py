"""
Integration tests for performance API endpoints.

Validates: Requirements 14.4, 14.5
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_performance_metrics_endpoint():
    """Test GET /api/performance/metrics endpoint."""
    response = client.get("/api/performance/metrics")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "cache" in data
    assert "database" in data
    assert "requests" in data
    assert "system" in data
    assert "timestamp" in data


def test_cache_stats_endpoint():
    """Test GET /api/performance/cache/stats endpoint."""
    response = client.get("/api/performance/cache/stats")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "capacity" in data
    assert "size" in data
    assert "hits" in data
    assert "misses" in data
    assert "hit_rate" in data


def test_clear_cache_endpoint():
    """Test DELETE /api/performance/cache/clear endpoint."""
    response = client.delete("/api/performance/cache/clear")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "message" in data
    assert "cleared" in data["message"].lower()


def test_database_stats_endpoint():
    """Test GET /api/performance/database/stats endpoint."""
    response = client.get("/api/performance/database/stats")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "total_queries" in data
    assert "avg_time" in data
    assert "slow_queries" in data


def test_slow_queries_endpoint():
    """Test GET /api/performance/database/slow-queries endpoint."""
    response = client.get("/api/performance/database/slow-queries?limit=5")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "slow_queries" in data
    assert "count" in data
    assert isinstance(data["slow_queries"], list)


def test_endpoint_performance():
    """Test GET /api/performance/endpoints endpoint."""
    response = client.get("/api/performance/endpoints")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "slowest_endpoints" in data
    assert isinstance(data["slowest_endpoints"], list)


def test_system_metrics_endpoint():
    """Test GET /api/performance/system endpoint."""
    response = client.get("/api/performance/system")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "cpu_percent" in data
    assert "memory_percent" in data
    assert "disk_percent" in data


def test_optimization_recommendations_endpoint():
    """Test GET /api/performance/recommendations endpoint."""
    response = client.get("/api/performance/recommendations")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "recommendations" in data
    assert "count" in data
    assert isinstance(data["recommendations"], list)


def test_health_check_fast_response():
    """Test that health check responds quickly without loading heavy services."""
    import time
    
    start = time.time()
    response = client.get("/api/health")
    duration = time.time() - start
    
    assert response.status_code == 200
    assert duration < 0.1  # Should respond in less than 100ms
    assert response.json()["status"] == "healthy"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
