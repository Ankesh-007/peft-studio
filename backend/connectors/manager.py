"""
Connector manager for lifecycle management and discovery.

The manager handles connector instantiation, lifecycle management,
and provides a unified interface for interacting with connectors.
"""

import os
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Type
import logging

from .base import PlatformConnector, TrainingConfig, Resource, PricingInfo
from .registry import ConnectorRegistry, ConnectorMetadata


logger = logging.getLogger(__name__)


class ConnectorManager:
    """
    Manager for connector lifecycle and discovery.
    
    The manager handles:
    - Auto-discovery of connectors from plugins directory
    - Connector instantiation and lifecycle
    - Credential management
    - Unified interface for connector operations
    """
    
    def __init__(self, plugins_dir: Optional[str] = None):
        """
        Initialize the connector manager.
        
        Args:
            plugins_dir: Path to plugins directory (default: ./plugins/connectors)
        """
        self.registry = ConnectorRegistry()
        self._instances: Dict[str, PlatformConnector] = {}
        self._credentials: Dict[str, Dict[str, str]] = {}
        
        # Set plugins directory
        if plugins_dir is None:
            # Default to backend/plugins/connectors
            backend_dir = Path(__file__).parent.parent
            plugins_dir = str(backend_dir / "plugins" / "connectors")
        
        self.plugins_dir = Path(plugins_dir)
        
        # Ensure plugins directory exists
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Connector manager initialized with plugins dir: {self.plugins_dir}")
    
    def discover_connectors(self) -> int:
        """
        Auto-discover and register connectors from plugins directory.
        
        Returns:
            Number of connectors discovered and registered
        """
        discovered = 0
        
        if not self.plugins_dir.exists():
            logger.warning(f"Plugins directory does not exist: {self.plugins_dir}")
            return 0
        
        # Scan for Python files in plugins directory
        for file_path in self.plugins_dir.glob("*_connector.py"):
            try:
                connector_class = self._load_connector_from_file(file_path)
                if connector_class and self.registry.register(connector_class):
                    discovered += 1
                    logger.info(f"Discovered and registered connector: {connector_class.name}")
                else:
                    errors = self.registry.get_validation_errors(
                        getattr(connector_class, 'name', 'unknown')
                    )
                    logger.error(f"Failed to register connector from {file_path}: {errors}")
            except Exception as e:
                logger.error(f"Error loading connector from {file_path}: {e}")
        
        logger.info(f"Discovered {discovered} connectors")
        return discovered
    
    def _load_connector_from_file(self, file_path: Path) -> Optional[Type[PlatformConnector]]:
        """
        Load a connector class from a Python file.
        
        Args:
            file_path: Path to connector Python file
            
        Returns:
            Connector class or None if not found
        """
        module_name = file_path.stem
        
        # Load module from file
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            return None
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find PlatformConnector subclass in module
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, PlatformConnector) and 
                attr is not PlatformConnector):
                return attr
        
        return None
    
    def register_connector(self, connector_class: Type[PlatformConnector]) -> bool:
        """
        Manually register a connector class.
        
        Args:
            connector_class: Connector class to register
            
        Returns:
            True if registration successful
        """
        return self.registry.register(connector_class)
    
    async def connect(self, name: str, credentials: Dict[str, str]) -> bool:
        """
        Connect to a platform using stored or provided credentials.
        
        Args:
            name: Connector name
            credentials: Credential dictionary
            
        Returns:
            True if connection successful
            
        Raises:
            ValueError: If connector not found or credentials invalid
            ConnectionError: If connection fails
        """
        metadata = self.registry.get(name)
        if not metadata:
            raise ValueError(f"Connector not found: {name}")
        
        if not metadata.enabled:
            raise ValueError(f"Connector is disabled: {name}")
        
        # Validate required credentials are provided
        for cred_key in metadata.required_credentials:
            if cred_key not in credentials:
                raise ValueError(f"Missing required credential: {cred_key}")
        
        # Create instance if not exists
        if name not in self._instances:
            self._instances[name] = metadata.connector_class()
        
        # Connect
        connector = self._instances[name]
        success = await connector.connect(credentials)
        
        if success:
            self._credentials[name] = credentials
            logger.info(f"Connected to {name}")
        else:
            logger.error(f"Failed to connect to {name}")
        
        return success
    
    async def disconnect(self, name: str) -> bool:
        """
        Disconnect from a platform.
        
        Args:
            name: Connector name
            
        Returns:
            True if disconnection successful
        """
        if name not in self._instances:
            return True
        
        connector = self._instances[name]
        success = await connector.disconnect()
        
        if success:
            del self._instances[name]
            if name in self._credentials:
                del self._credentials[name]
            logger.info(f"Disconnected from {name}")
        
        return success
    
    def get_connector(self, name: str) -> Optional[PlatformConnector]:
        """
        Get a connected connector instance.
        
        Args:
            name: Connector name
            
        Returns:
            Connector instance or None if not connected
        """
        return self._instances.get(name)
    
    def is_connected(self, name: str) -> bool:
        """
        Check if a connector is connected.
        
        Args:
            name: Connector name
            
        Returns:
            True if connected
        """
        return name in self._instances
    
    def list_connectors(self, enabled_only: bool = True) -> List[ConnectorMetadata]:
        """
        List available connectors.
        
        Args:
            enabled_only: Only return enabled connectors
            
        Returns:
            List of connector metadata
        """
        if enabled_only:
            return self.registry.list_enabled()
        return self.registry.list_all()
    
    def list_connected(self) -> List[str]:
        """
        List names of currently connected connectors.
        
        Returns:
            List of connector names
        """
        return list(self._instances.keys())
    
    async def submit_job(self, connector_name: str, config: TrainingConfig) -> str:
        """
        Submit a training job to a connector.
        
        Args:
            connector_name: Name of connector to use
            config: Training configuration
            
        Returns:
            Job ID
            
        Raises:
            ValueError: If connector not found or not connected
            RuntimeError: If job submission fails
        """
        connector = self.get_connector(connector_name)
        if not connector:
            raise ValueError(f"Connector not connected: {connector_name}")
        
        # Validate configuration
        connector.validate_config(config)
        
        # Submit job
        job_id = await connector.submit_job(config)
        logger.info(f"Submitted job {job_id} to {connector_name}")
        
        return job_id
    
    async def list_resources(self, connector_name: str) -> List[Resource]:
        """
        List available resources from a connector.
        
        Args:
            connector_name: Name of connector
            
        Returns:
            List of resources
            
        Raises:
            ValueError: If connector not found or not connected
        """
        connector = self.get_connector(connector_name)
        if not connector:
            raise ValueError(f"Connector not connected: {connector_name}")
        
        return await connector.list_resources()
    
    async def get_pricing(self, connector_name: str, resource_id: str) -> PricingInfo:
        """
        Get pricing information from a connector.
        
        Args:
            connector_name: Name of connector
            resource_id: Resource identifier
            
        Returns:
            Pricing information
            
        Raises:
            ValueError: If connector not found or not connected
        """
        connector = self.get_connector(connector_name)
        if not connector:
            raise ValueError(f"Connector not connected: {connector_name}")
        
        return await connector.get_pricing(resource_id)
    
    def get_connectors_by_feature(self, feature: str) -> List[ConnectorMetadata]:
        """
        Get connectors that support a specific feature.
        
        Args:
            feature: Feature name (training, inference, registry, tracking)
            
        Returns:
            List of connectors supporting the feature
        """
        return self.registry.get_by_feature(feature)
