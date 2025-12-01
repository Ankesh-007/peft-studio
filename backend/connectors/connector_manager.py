"""
Connector Manager

Manages the lifecycle of all platform connectors, including discovery,
registration, and retrieval.

Requirements: 13.1, 13.2, 13.3
"""

import logging
import importlib
import inspect
from typing import Dict, List, Optional
from pathlib import Path

from backend.connectors.base import PlatformConnector


logger = logging.getLogger(__name__)


class ConnectorManager:
    """
    Manages platform connectors.
    
    Provides functionality to discover, register, and retrieve connectors.
    Ensures connector isolation so failures don't affect other connectors.
    """
    
    def __init__(self):
        """Initialize connector manager."""
        self.connectors: Dict[str, PlatformConnector] = {}
        self._discover_connectors()
    
    def _discover_connectors(self):
        """
        Auto-discover connectors from the plugins directory.
        
        Scans the plugins/connectors directory for connector modules
        and automatically registers them.
        """
        try:
            plugins_dir = Path(__file__).parent.parent / 'plugins' / 'connectors'
            
            if not plugins_dir.exists():
                logger.warning(f"Plugins directory not found: {plugins_dir}")
                return
            
            # Scan for Python files
            for file_path in plugins_dir.glob('*_connector.py'):
                if file_path.name.startswith('_'):
                    continue
                
                try:
                    # Import module
                    module_name = file_path.stem
                    module = importlib.import_module(f'plugins.connectors.{module_name}')
                    
                    # Find connector classes
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (issubclass(obj, PlatformConnector) and 
                            obj is not PlatformConnector and
                            hasattr(obj, 'name') and obj.name):
                            
                            # Instantiate and register
                            connector = obj()
                            self.register(connector)
                            logger.info(f"Discovered connector: {connector.name}")
                
                except Exception as e:
                    logger.error(f"Error loading connector from {file_path}: {e}")
        
        except Exception as e:
            logger.error(f"Error discovering connectors: {e}")
    
    def register(self, connector: PlatformConnector):
        """
        Register a connector.
        
        Args:
            connector: Connector instance to register
            
        Raises:
            ValueError: If connector name is invalid or already registered
        """
        if not connector.name:
            raise ValueError("Connector must have a name")
        
        if connector.name in self.connectors:
            logger.warning(f"Connector {connector.name} is already registered, replacing")
        
        # Validate connector interface
        if not self._validate_connector(connector):
            raise ValueError(f"Connector {connector.name} does not implement required interface")
        
        self.connectors[connector.name] = connector
        logger.info(f"Registered connector: {connector.name}")
    
    def _validate_connector(self, connector: PlatformConnector) -> bool:
        """
        Validate that a connector implements the required interface.
        
        Args:
            connector: Connector to validate
            
        Returns:
            True if valid, False otherwise
        """
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
            'get_pricing'
        ]
        
        for method_name in required_methods:
            if not hasattr(connector, method_name):
                logger.error(f"Connector {connector.name} missing method: {method_name}")
                return False
            
            method = getattr(connector, method_name)
            if not callable(method):
                logger.error(f"Connector {connector.name} {method_name} is not callable")
                return False
        
        return True
    
    def get(self, name: str) -> Optional[PlatformConnector]:
        """
        Get a connector by name.
        
        Args:
            name: Connector name
            
        Returns:
            Connector instance or None if not found
        """
        return self.connectors.get(name)
    
    def list_connectors(self) -> List[str]:
        """
        List all registered connector names.
        
        Returns:
            List of connector names
        """
        return list(self.connectors.keys())
    
    def unregister(self, name: str) -> bool:
        """
        Unregister a connector.
        
        Args:
            name: Connector name
            
        Returns:
            True if unregistered, False if not found
        """
        if name in self.connectors:
            del self.connectors[name]
            logger.info(f"Unregistered connector: {name}")
            return True
        return False
    
    def get_connector_info(self, name: str) -> Optional[Dict]:
        """
        Get information about a connector.
        
        Args:
            name: Connector name
            
        Returns:
            Dictionary with connector information or None if not found
        """
        connector = self.get(name)
        if not connector:
            return None
        
        return {
            'name': connector.name,
            'display_name': connector.display_name,
            'description': connector.description,
            'version': connector.version,
            'supports_training': connector.supports_training,
            'supports_inference': connector.supports_inference,
            'supports_registry': connector.supports_registry,
            'supports_tracking': connector.supports_tracking,
            'required_credentials': connector.get_required_credentials()
        }
    
    def list_connectors_info(self) -> List[Dict]:
        """
        List information about all registered connectors.
        
        Returns:
            List of connector information dictionaries
        """
        return [
            self.get_connector_info(name)
            for name in self.list_connectors()
        ]


# Singleton instance
_connector_manager = None


def get_connector_manager() -> ConnectorManager:
    """Get singleton instance of connector manager."""
    global _connector_manager
    if _connector_manager is None:
        _connector_manager = ConnectorManager()
    return _connector_manager
