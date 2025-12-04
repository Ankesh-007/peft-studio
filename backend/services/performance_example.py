"""
Example usage of performance optimizations in connectors and services.

This demonstrates how to use:
- HTTP connection pooling
- Request caching
- Performance monitoring
"""

import asyncio
from typing import Dict, Any
from services.performance_service import (
    get_http_pool,
    cache_result,
    monitor_performance
)


# ============================================================================
# Example 1: Using HTTP Connection Pool in Connectors
# ============================================================================

class OptimizedConnector:
    """Example connector using HTTP connection pooling."""
    
    def __init__(self):
        self.http_pool = get_http_pool()
        self.base_url = "https://api.example.com"
    
    async def fetch_data(self, endpoint: str) -> Dict[str, Any]:
        """Fetch data using pooled connection."""
        url = f"{self.base_url}/{endpoint}"
        
        # Use connection pool instead of creating new session
        async with await self.http_pool.get(url) as response:
            return await response.json()
    
    async def submit_job(self, payload: Dict[str, Any]) -> str:
        """Submit job using pooled connection."""
        url = f"{self.base_url}/jobs"
        
        # Use connection pool for POST request
        async with await self.http_pool.post(url, json=payload) as response:
            data = await response.json()
            return data["job_id"]


# ============================================================================
# Example 2: Using Request Caching
# ============================================================================

class CachedModelRegistry:
    """Example m