"""
Backend Performance Optimization Service

Implements:
- Connection pooling for HTTP clients
- Request caching with TTL
- Database query optimization
- Performance monitoring
- Resource management

Validates: Requirements 14.4, 14.5
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
from functools import wraps
from collections import OrderedDict
import aiohttp
from sqlalchemy import event, Index
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool
import psutil

logger = logging.getLogger(__name__)


# ============================================================================
# Connection Pooling
# ============================================================================

class HTTPConnectionPool:
    """
    Manages HTTP connection pooling for external API calls.
    Reuses connections to reduce overhead and improve performance.
    """
    
    def __init__(
        self,
        max_connections: int = 100,
        max_connections_per_host: int = 10,
        timeout: int = 30
    ):
        self.max_connections = max_connections
        self.max_connections_per_host = max_connections_per_host
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None
        self._lock = asyncio.Lock()
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with connection pooling."""
        if self._session is None or self._session.closed:
            async with self._lock:
                if self._session is None or self._session.closed:
                    connector = aiohttp.TCPConnector(
                        limit=self.max_connections,
                        limit_per_host=self.max_connections_per_host,
                        ttl_dns_cache=300,  # Cache DNS for 5 minutes
                        enable_cleanup_closed=True
                    )
                    self._session = aiohttp.ClientSession(
                        connector=connector,
                        timeout=self.timeout
                    )
                    logger.info(
                        f"Created HTTP connection pool: "
                        f"max_connections={self.max_connections}, "
                        f"max_per_host={self.max_connections_per_host}"
                    )
        return self._session
    
    async def close(self):
        """Close the HTTP session and cleanup connections."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("Closed HTTP connection pool")
    
    async def get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make GET request using pooled connection."""
        session = await self.get_session()
        return await session.get(url, **kwargs)
    
    async def post(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make POST request using pooled connection."""
        session = await self.get_session()
        return await session.post(url, **kwargs)
    
    async def put(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make PUT request using pooled connection."""
        session = await self.get_session()
        return await session.put(url, **kwargs)
    
    async def delete(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make DELETE request using pooled connection."""
        session = await self.get_session()
        return await session.delete(url, **kwargs)


# Global HTTP connection pool
_http_pool: Optional[HTTPConnectionPool] = None


def get_http_pool() -> HTTPConnectionPool:
    """Get the global HTTP connection pool."""
    global _http_pool
    if _http_pool is None:
        _http_pool = HTTPConnectionPool()
    return _http_pool


async def close_http_pool():
    """Close the global HTTP connection pool."""
    global _http_pool
    if _http_pool:
        await _http_pool.close()
        _http_pool = None


# ============================================================================
# Request Caching
# ============================================================================

class LRUCache:
    """
    Least Recently Used (LRU) cache with TTL support.
    Automatically evicts least recently used items when capacity is reached.
    """
    
    def __init__(self, capacity: int = 1000, default_ttl: int = 300):
        self.capacity = capacity
        self.default_ttl = default_ttl
        self.cache: OrderedDict = OrderedDict()
        self.expiry: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        async with self._lock:
            if key not in self.cache:
                self._misses += 1
                return None
            
            # Check if expired
            if key in self.expiry and datetime.now() > self.expiry[key]:
                del self.cache[key]
                del self.expiry[key]
                self._misses += 1
                return None
            
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self._hits += 1
            return self.cache[key]
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache with optional TTL."""
        async with self._lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            else:
                if len(self.cache) >= self.capacity:
                    # Remove least recently used item
                    oldest_key = next(iter(self.cache))
                    del self.cache[oldest_key]
                    if oldest_key in self.expiry:
                        del self.expiry[oldest_key]
            
            self.cache[key] = value
            
            # Set expiry
            ttl = ttl or self.default_ttl
            self.expiry[key] = datetime.now() + timedelta(seconds=ttl)
    
    async def delete(self, key: str):
        """Delete value from cache."""
        async with self._lock:
            if key in self.cache:
                del self.cache[key]
            if key in self.expiry:
                del self.expiry[key]
    
    async def clear(self):
        """Clear all cache entries."""
        async with self._lock:
            self.cache.clear()
            self.expiry.clear()
            self._hits = 0
            self._misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0
        
        return {
            "capacity": self.capacity,
            "size": len(self.cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "utilization": len(self.cache) / self.capacity
        }


# Global request cache
_request_cache: Optional[LRUCache] = None


def get_request_cache() -> LRUCache:
    """Get the global request cache."""
    global _request_cache
    if _request_cache is None:
        _request_cache = LRUCache(capacity=1000, default_ttl=300)
    return _request_cache


def cache_result(ttl: int = 300, key_func: Optional[Callable] = None):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time to live in seconds
        key_func: Optional function to generate cache key from args
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cache = get_request_cache()
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache.set(cache_key, result, ttl=ttl)
            logger.debug(f"Cache miss for {cache_key}, stored result")
            
            return result
        return wrapper
    return decorator


# ============================================================================
# Database Query Optimization
# ============================================================================

class DatabaseOptimizer:
    """
    Optimizes database queries and manages connection pooling.
    """
    
    def __init__(self):
        self.query_times: List[float] = []
        self.slow_query_threshold = 1.0  # seconds
        self.slow_queries: List[Dict[str, Any]] = []
    
    def setup_connection_pool(self, engine: Engine):
        """
        Configure database connection pooling.
        
        Args:
            engine: SQLAlchemy engine
        """
        # Configure pool
        engine.pool = QueuePool(
            engine.pool._creator,
            pool_size=20,  # Number of connections to maintain
            max_overflow=10,  # Additional connections when pool is full
            timeout=30,  # Timeout for getting connection
            recycle=3600,  # Recycle connections after 1 hour
            pre_ping=True  # Verify connections before using
        )
        logger.info(
            "Configured database connection pool: "
            "pool_size=20, max_overflow=10"
        )
    
    def add_indexes(self, engine: Engine):
        """
        Add database indexes for frequently queried columns.
        
        Args:
            engine: SQLAlchemy engine
        """
        from database import Base, TrainingRun
        
        # Add indexes if they don't exist
        indexes = [
            Index('idx_training_runs_job_id', TrainingRun.job_id),
            Index('idx_training_runs_status', TrainingRun.status),
            Index('idx_training_runs_started_at', TrainingRun.started_at),
        ]
        
        for index in indexes:
            try:
                index.create(engine, checkfirst=True)
                logger.info(f"Created index: {index.name}")
            except Exception as e:
                logger.warning(f"Could not create index {index.name}: {e}")
    
    def setup_query_logging(self, engine: Engine):
        """
        Set up query performance logging.
        
        Args:
            engine: SQLAlchemy engine
        """
        @event.listens_for(engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            conn.info.setdefault('query_start_time', []).append(time.time())
        
        @event.listens_for(engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total_time = time.time() - conn.info['query_start_time'].pop()
            self.query_times.append(total_time)
            
            # Log slow queries
            if total_time > self.slow_query_threshold:
                self.slow_queries.append({
                    'statement': statement,
                    'parameters': parameters,
                    'time': total_time,
                    'timestamp': datetime.now()
                })
                logger.warning(
                    f"Slow query detected ({total_time:.3f}s): "
                    f"{statement[:100]}..."
                )
        
        logger.info("Set up database query performance logging")
    
    def get_query_stats(self) -> Dict[str, Any]:
        """Get database query statistics."""
        if not self.query_times:
            return {
                "total_queries": 0,
                "avg_time": 0,
                "max_time": 0,
                "min_time": 0,
                "slow_queries": 0
            }
        
        return {
            "total_queries": len(self.query_times),
            "avg_time": sum(self.query_times) / len(self.query_times),
            "max_time": max(self.query_times),
            "min_time": min(self.query_times),
            "slow_queries": len(self.slow_queries)
        }
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent slow queries."""
        return sorted(
            self.slow_queries,
            key=lambda x: x['time'],
            reverse=True
        )[:limit]


# Global database optimizer
_db_optimizer: Optional[DatabaseOptimizer] = None


def get_db_optimizer() -> DatabaseOptimizer:
    """Get the global database optimizer."""
    global _db_optimizer
    if _db_optimizer is None:
        _db_optimizer = DatabaseOptimizer()
    return _db_optimizer


# ============================================================================
# Performance Monitoring
# ============================================================================

class PerformanceMonitor:
    """
    Monitors backend performance metrics.
    """
    
    def __init__(self):
        self.request_times: List[float] = []
        self.endpoint_times: Dict[str, List[float]] = {}
        self.error_count = 0
        self.request_count = 0
    
    def record_request(self, endpoint: str, duration: float, error: bool = False):
        """Record request metrics."""
        self.request_count += 1
        self.request_times.append(duration)
        
        if endpoint not in self.endpoint_times:
            self.endpoint_times[endpoint] = []
        self.endpoint_times[endpoint].append(duration)
        
        if error:
            self.error_count += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        if not self.request_times:
            return {
                "total_requests": 0,
                "avg_response_time": 0,
                "max_response_time": 0,
                "min_response_time": 0,
                "error_rate": 0,
                "requests_per_second": 0
            }
        
        return {
            "total_requests": self.request_count,
            "avg_response_time": sum(self.request_times) / len(self.request_times),
            "max_response_time": max(self.request_times),
            "min_response_time": min(self.request_times),
            "error_rate": self.error_count / self.request_count,
            "error_count": self.error_count
        }
    
    def get_endpoint_metrics(self, endpoint: str) -> Dict[str, Any]:
        """Get metrics for specific endpoint."""
        if endpoint not in self.endpoint_times:
            return {
                "endpoint": endpoint,
                "total_requests": 0,
                "avg_response_time": 0
            }
        
        times = self.endpoint_times[endpoint]
        return {
            "endpoint": endpoint,
            "total_requests": len(times),
            "avg_response_time": sum(times) / len(times),
            "max_response_time": max(times),
            "min_response_time": min(times)
        }
    
    def get_slowest_endpoints(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get slowest endpoints by average response time."""
        endpoint_stats = []
        for endpoint, times in self.endpoint_times.items():
            if times:
                endpoint_stats.append({
                    "endpoint": endpoint,
                    "avg_time": sum(times) / len(times),
                    "request_count": len(times)
                })
        
        return sorted(
            endpoint_stats,
            key=lambda x: x['avg_time'],
            reverse=True
        )[:limit]
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system resource metrics."""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_mb": memory.used / (1024 * 1024),
            "memory_available_mb": memory.available / (1024 * 1024),
            "disk_percent": disk.percent,
            "disk_used_gb": disk.used / (1024 * 1024 * 1024),
            "disk_free_gb": disk.free / (1024 * 1024 * 1024)
        }


# Global performance monitor
_perf_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor."""
    global _perf_monitor
    if _perf_monitor is None:
        _perf_monitor = PerformanceMonitor()
    return _perf_monitor


def monitor_performance(endpoint: str):
    """
    Decorator to monitor endpoint performance.
    
    Args:
        endpoint: Endpoint name
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            error = False
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                error = True
                raise
            finally:
                duration = time.time() - start_time
                monitor = get_performance_monitor()
                monitor.record_request(endpoint, duration, error)
        
        return wrapper
    return decorator


# ============================================================================
# Service Interface
# ============================================================================

class PerformanceService:
    """
    Main service for backend performance optimization.
    """
    
    def __init__(self):
        self.http_pool = get_http_pool()
        self.cache = get_request_cache()
        self.db_optimizer = get_db_optimizer()
        self.monitor = get_performance_monitor()
    
    async def initialize(self, engine: Engine):
        """
        Initialize performance optimizations.
        
        Args:
            engine: SQLAlchemy database engine
        """
        # Setup database optimizations
        self.db_optimizer.setup_connection_pool(engine)
        self.db_optimizer.add_indexes(engine)
        self.db_optimizer.setup_query_logging(engine)
        
        logger.info("Performance service initialized")
    
    async def cleanup(self):
        """Cleanup resources."""
        await self.http_pool.close()
        await self.cache.clear()
        logger.info("Performance service cleaned up")
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all performance metrics."""
        return {
            "cache": self.cache.get_stats(),
            "database": self.db_optimizer.get_query_stats(),
            "requests": self.monitor.get_metrics(),
            "system": self.monitor.get_system_metrics(),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_optimization_recommendations(self) -> List[str]:
        """Get performance optimization recommendations."""
        recommendations = []
        
        # Check cache hit rate
        cache_stats = self.cache.get_stats()
        if cache_stats['hit_rate'] < 0.5:
            recommendations.append(
                "Cache hit rate is low. Consider increasing cache TTL or capacity."
            )
        
        # Check slow queries
        db_stats = self.db_optimizer.get_query_stats()
        if db_stats['slow_queries'] > 10:
            recommendations.append(
                f"Detected {db_stats['slow_queries']} slow queries. "
                "Consider adding indexes or optimizing queries."
            )
        
        # Check response times
        request_stats = self.monitor.get_metrics()
        if request_stats['avg_response_time'] > 1.0:
            recommendations.append(
                "Average response time is high. Consider optimizing slow endpoints."
            )
        
        # Check error rate
        if request_stats['error_rate'] > 0.05:
            recommendations.append(
                f"Error rate is {request_stats['error_rate']:.1%}. "
                "Investigate failing requests."
            )
        
        # Check system resources
        system_stats = self.monitor.get_system_metrics()
        if system_stats['memory_percent'] > 80:
            recommendations.append(
                "Memory usage is high. Consider implementing memory cleanup."
            )
        
        if system_stats['cpu_percent'] > 80:
            recommendations.append(
                "CPU usage is high. Consider optimizing compute-intensive operations."
            )
        
        return recommendations


# Global performance service
_performance_service: Optional[PerformanceService] = None


def get_performance_service() -> PerformanceService:
    """Get the global performance service."""
    global _performance_service
    if _performance_service is None:
        _performance_service = PerformanceService()
    return _performance_service
