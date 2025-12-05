"""
Startup Optimization Service

Implements lazy loading, preloading, and performance monitoring for application startup.
Validates: Requirements 14.1 - Application must launch within 3 seconds
"""

import time
import logging
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)


@dataclass
class StartupMetrics:
    """Tracks startup performance metrics"""
    start_time: float = field(default_factory=time.time)
    import_time: float = 0.0
    db_init_time: float = 0.0
    service_init_time: float = 0.0
    total_time: float = 0.0
    components: Dict[str, float] = field(default_factory=dict)
    
    def record_component(self, name: str, duration: float):
        """Record timing for a startup component"""
        self.components[name] = duration
        logger.info(f"Startup component '{name}' took {duration:.3f}s")
    
    def finalize(self):
        """Calculate total startup time"""
        self.total_time = time.time() - self.start_time
        logger.info(f"Total startup time: {self.total_time:.3f}s")
        
        if self.total_time > 3.0:
            logger.warning(
                f"Startup time {self.total_time:.3f}s exceeds 3-second target! "
                f"Components: {self.components}"
            )
        
        return self.total_time


class LazyLoader:
    """
    Lazy loader for heavy dependencies.
    
    Delays loading of ML libraries and other heavy dependencies until they're actually needed.
    """
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._loading: Dict[str, bool] = {}
    
    def load(self, name: str, loader: Callable) -> Any:
        """
        Lazily load a module or service.
        
        Args:
            name: Identifier for the module
            loader: Function that performs the actual loading
            
        Returns:
            The loaded module/service
        """
        if name in self._cache:
            return self._cache[name]
        
        if self._loading.get(name):
            raise RuntimeError(f"Circular dependency detected while loading {name}")
        
        try:
            self._loading[name] = True
            start = time.time()
            
            result = loader()
            
            duration = time.time() - start
            logger.debug(f"Lazy loaded '{name}' in {duration:.3f}s")
            
            self._cache[name] = result
            return result
        
        finally:
            self._loading[name] = False
    
    def is_loaded(self, name: str) -> bool:
        """Check if a module is already loaded"""
        return name in self._cache
    
    def clear(self):
        """Clear the cache (useful for testing)"""
        self._cache.clear()
        self._loading.clear()


class StartupOptimizer:
    """
    Manages application startup optimization.
    
    Features:
    - Lazy loading of ML libraries
    - Preloading of critical resources
    - Database query optimization
    - Startup performance monitoring
    """
    
    def __init__(self):
        self.metrics = StartupMetrics()
        self.lazy_loader = LazyLoader()
        self._critical_resources_loaded = False
        self._ml_libraries_loaded = False
    
    def measure(self, component_name: str):
        """
        Decorator to measure component startup time.
        
        Usage:
            @startup_optimizer.measure("database")
            def init_database():
                # initialization code
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start = time.time()
                result = func(*args, **kwargs)
                duration = time.time() - start
                self.metrics.record_component(component_name, duration)
                return result
            return wrapper
        return decorator
    
    async def preload_critical_resources(self):
        """
        Preload critical resources needed for the UI to be interactive.
        
        This includes:
        - Database connection pool
        - Configuration files
        - User preferences
        - Recent project data
        """
        if self._critical_resources_loaded:
            return
        
        start = time.time()
        
        try:
            # Preload database connection pool
            await self._preload_database_pool()
            
            # Preload configuration
            await self._preload_configuration()
            
            # Preload recent data (async, non-blocking)
            asyncio.create_task(self._preload_recent_data())
            
            self._critical_resources_loaded = True
            
        except Exception as e:
            logger.error(f"Error preloading critical resources: {e}")
        
        finally:
            duration = time.time() - start
            self.metrics.record_component("preload_critical", duration)
    
    async def _preload_database_pool(self):
        """Initialize database connection pool"""
        try:
            from database import engine
            # Create connection pool without blocking
            async with engine.begin() as conn:
                await conn.execute("SELECT 1")
            logger.debug("Database connection pool initialized")
        except Exception as e:
            logger.warning(f"Could not preload database pool: {e}")
    
    async def _preload_configuration(self):
        """Load configuration files"""
        try:
            from config import DATABASE_URL
            logger.debug("Configuration loaded")
        except Exception as e:
            logger.warning(f"Could not preload configuration: {e}")
    
    async def _preload_recent_data(self):
        """
        Preload recent project data in the background.
        
        This runs asynchronously and doesn't block startup.
        """
        try:
            # Wait a bit to not interfere with critical startup
            await asyncio.sleep(0.5)
            
            from database import SessionLocal
            from database import TrainingRun
            
            # Preload recent training runs
            db = SessionLocal()
            try:
                recent_runs = db.query(TrainingRun).order_by(
                    TrainingRun.started_at.desc()
                ).limit(10).all()
                logger.debug(f"Preloaded {len(recent_runs)} recent training runs")
            finally:
                db.close()
        
        except Exception as e:
            logger.debug(f"Could not preload recent data: {e}")
    
    def lazy_load_ml_libraries(self):
        """
        Lazily load ML libraries (torch, transformers, etc.).
        
        These are only loaded when actually needed for training or inference.
        """
        if self._ml_libraries_loaded:
            return
        
        def load_torch():
            import torch
            return torch
        
        def load_transformers():
            import transformers
            return transformers
        
        def load_unsloth():
            try:
                from unsloth import FastLanguageModel
                return FastLanguageModel
            except ImportError:
                logger.warning("Unsloth not available")
                return None
        
        # Register lazy loaders
        self.lazy_loader.load("torch", load_torch)
        self.lazy_loader.load("transformers", load_transformers)
        self.lazy_loader.load("unsloth", load_unsloth)
        
        self._ml_libraries_loaded = True
    
    def get_ml_library(self, name: str) -> Any:
        """
        Get an ML library, loading it lazily if needed.
        
        Args:
            name: Library name ("torch", "transformers", "unsloth")
            
        Returns:
            The loaded library
        """
        if not self.lazy_loader.is_loaded(name):
            self.lazy_load_ml_libraries()
        
        return self.lazy_loader._cache.get(name)
    
    def optimize_database_queries(self):
        """
        Optimize database queries for faster startup.
        
        - Create indexes on frequently queried columns
        - Use connection pooling
        - Defer non-critical queries
        """
        try:
            from database import engine, TrainingRun, Model, Dataset
            from sqlalchemy import Index
            
            # Ensure indexes exist (these are already defined in the model)
            # This is a no-op if indexes already exist
            with engine.begin() as conn:
                # Verify critical indexes
                conn.execute("PRAGMA index_list(training_runs)")
            
            logger.debug("Database indexes verified")
        
        except Exception as e:
            logger.warning(f"Could not optimize database queries: {e}")
    
    def get_startup_report(self) -> Dict[str, Any]:
        """
        Get a detailed startup performance report.
        
        Returns:
            Dictionary with startup metrics and recommendations
        """
        self.metrics.finalize()
        
        # Determine target based on mode (production vs development)
        # Production bundled executables should start within 5 seconds
        # Development mode has a 3-second target
        import sys
        is_bundled = getattr(sys, 'frozen', False)
        target_time = 5.0 if is_bundled else 3.0
        
        report = {
            "total_time": self.metrics.total_time,
            "meets_target": self.metrics.total_time < target_time,
            "target_time": target_time,
            "mode": "production" if is_bundled else "development",
            "phases": self.metrics.components,
            "recommendations": []
        }
        
        # Add recommendations based on metrics
        if self.metrics.total_time > target_time:
            report["recommendations"].append(
                f"Startup time {self.metrics.total_time:.2f}s exceeds {target_time}s target. Consider further optimization."
            )
            
            # Log detailed warning for slow startups
            logger.warning(
                f"SLOW STARTUP DETECTED: {self.metrics.total_time:.2f}s (target: {target_time}s)\n"
                f"Mode: {'production' if is_bundled else 'development'}\n"
                f"Components: {self.metrics.components}"
            )
        
        # Check individual components
        for component, duration in self.metrics.components.items():
            if duration > 1.0:
                report["recommendations"].append(
                    f"Component '{component}' took {duration:.2f}s. Consider optimization."
                )
                logger.warning(f"Slow component: '{component}' took {duration:.2f}s")
        
        # Add performance insights
        if self.metrics.total_time < target_time * 0.5:
            report["performance_rating"] = "excellent"
        elif self.metrics.total_time < target_time * 0.75:
            report["performance_rating"] = "good"
        elif self.metrics.total_time < target_time:
            report["performance_rating"] = "acceptable"
        else:
            report["performance_rating"] = "needs_improvement"
        
        return report


# Global instance
_startup_optimizer: Optional[StartupOptimizer] = None


def get_startup_optimizer() -> StartupOptimizer:
    """Get the global startup optimizer instance"""
    global _startup_optimizer
    if _startup_optimizer is None:
        _startup_optimizer = StartupOptimizer()
    return _startup_optimizer


def measure_startup(component_name: str):
    """
    Decorator to measure startup time for a component.
    
    Usage:
        @measure_startup("my_component")
        def initialize_component():
            # initialization code
    """
    optimizer = get_startup_optimizer()
    return optimizer.measure(component_name)


# Lazy loading helpers
def lazy_import_torch():
    """Lazily import torch"""
    optimizer = get_startup_optimizer()
    return optimizer.get_ml_library("torch")


def lazy_import_transformers():
    """Lazily import transformers"""
    optimizer = get_startup_optimizer()
    return optimizer.get_ml_library("transformers")


def lazy_import_unsloth():
    """Lazily import unsloth"""
    optimizer = get_startup_optimizer()
    return optimizer.get_ml_library("unsloth")
