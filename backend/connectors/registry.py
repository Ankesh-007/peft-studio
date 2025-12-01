"""
Connector registry for managing connector metadata and validation.

The registry maintains information about available connectors and
validates their implementations against the required interface.
"""

import inspect
from typing import Dict, List, Type, Optional
from dataclasses import dataclass
from .base import PlatformConnector


@dataclass
class ConnectorMetadata:
    """Metadata about a registered connector."""
    name: str
    display_name: str
    description: str
    version: str
    connector_class: Type[PlatformConnector]
    required_credentials: List[str]
    supports_training: bool
    supports_inference: bool
    supports_registry: bool
    supports_tracking: bool
    enabled: bool = True


class ConnectorRegistry:
    """
    Registry for managing connector metadata and validation.
    
    The registry maintains a catalog of available connectors and provides
    methods for registration, validation, and retrieval.
    """
    
    def __init__(self):
        self._connectors: Dict[str, ConnectorMetadata] = {}
        self._validation_errors: Dict[str, List[str]] = {}
    
    def register(self, connector_class: Type[PlatformConnector]) -> bool:
        """
        Register a connector class.
        
        Args:
            connector_class: Connector class to register
            
        Returns:
            True if registration successful, False otherwise
        """
        # Validate the connector implements required interface
        errors = self.validate_connector(connector_class)
        
        if errors:
            self._validation_errors[connector_class.name] = errors
            return False
        
        # Extract metadata
        metadata = ConnectorMetadata(
            name=connector_class.name,
            display_name=connector_class.display_name,
            description=connector_class.description,
            version=connector_class.version,
            connector_class=connector_class,
            required_credentials=connector_class().get_required_credentials(),
            supports_training=connector_class.supports_training,
            supports_inference=connector_class.supports_inference,
            supports_registry=connector_class.supports_registry,
            supports_tracking=connector_class.supports_tracking,
        )
        
        self._connectors[connector_class.name] = metadata
        return True
    
    def unregister(self, name: str) -> bool:
        """
        Unregister a connector.
        
        Args:
            name: Connector name
            
        Returns:
            True if unregistration successful
        """
        if name in self._connectors:
            del self._connectors[name]
            return True
        return False
    
    def get(self, name: str) -> Optional[ConnectorMetadata]:
        """
        Get connector metadata by name.
        
        Args:
            name: Connector name
            
        Returns:
            Connector metadata or None if not found
        """
        return self._connectors.get(name)
    
    def list_all(self) -> List[ConnectorMetadata]:
        """
        List all registered connectors.
        
        Returns:
            List of connector metadata
        """
        return list(self._connectors.values())
    
    def list_enabled(self) -> List[ConnectorMetadata]:
        """
        List enabled connectors only.
        
        Returns:
            List of enabled connector metadata
        """
        return [c for c in self._connectors.values() if c.enabled]
    
    def enable(self, name: str) -> bool:
        """
        Enable a connector.
        
        Args:
            name: Connector name
            
        Returns:
            True if successful
        """
        if name in self._connectors:
            self._connectors[name].enabled = True
            return True
        return False
    
    def disable(self, name: str) -> bool:
        """
        Disable a connector.
        
        Args:
            name: Connector name
            
        Returns:
            True if successful
        """
        if name in self._connectors:
            self._connectors[name].enabled = False
            return True
        return False
    
    def get_validation_errors(self, name: str) -> List[str]:
        """
        Get validation errors for a connector.
        
        Args:
            name: Connector name
            
        Returns:
            List of validation error messages
        """
        return self._validation_errors.get(name, [])
    
    @staticmethod
    def validate_connector(connector_class: Type[PlatformConnector]) -> List[str]:
        """
        Validate that a connector class implements the required interface.
        
        Args:
            connector_class: Connector class to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check if it's a subclass of PlatformConnector
        if not issubclass(connector_class, PlatformConnector):
            errors.append("Connector must inherit from PlatformConnector")
            return errors
        
        # Check required class attributes
        required_attrs = ['name', 'display_name', 'description', 'version']
        for attr in required_attrs:
            if not hasattr(connector_class, attr) or not getattr(connector_class, attr):
                errors.append(f"Missing or empty required attribute: {attr}")
        
        # Check required methods are implemented
        required_methods = [
            'connect',
            'disconnect',
            'verify_connection',
            'submit_job',
            'get_job_status',
            'cancel_job',
            'stream_logs',
            'fetch_artifact',
            'upload_artifact',
            'list_resources',
            'get_pricing',
        ]
        
        for method_name in required_methods:
            if not hasattr(connector_class, method_name):
                errors.append(f"Missing required method: {method_name}")
                continue
            
            method = getattr(connector_class, method_name)
            
            # Check if method is actually implemented (not just abstract)
            if hasattr(method, '__isabstractmethod__') and method.__isabstractmethod__:
                errors.append(f"Method {method_name} is not implemented (still abstract)")
        
        return errors
    
    def get_by_feature(self, feature: str) -> List[ConnectorMetadata]:
        """
        Get connectors that support a specific feature.
        
        Args:
            feature: Feature name (training, inference, registry, tracking)
            
        Returns:
            List of connectors supporting the feature
        """
        feature_map = {
            'training': lambda c: c.supports_training,
            'inference': lambda c: c.supports_inference,
            'registry': lambda c: c.supports_registry,
            'tracking': lambda c: c.supports_tracking,
        }
        
        if feature not in feature_map:
            return []
        
        return [c for c in self._connectors.values() 
                if c.enabled and feature_map[feature](c)]
