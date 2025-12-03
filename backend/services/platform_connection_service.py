"""
Platform Connection Service

Manages platform connections, credentials, and connection verification.
Integrates with the connector system and credential service.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
"""

import logging
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from services.credential_service import CredentialService
from connectors.connector_manager import ConnectorManager


logger = logging.getLogger(__name__)


@dataclass
class PlatformConnection:
    """Represents a platform connection."""
    platform_name: str
    display_name: str
    status: str  # connected, disconnected, error, verifying
    connected_at: Optional[str] = None
    last_verified: Optional[str] = None
    error_message: Optional[str] = None
    features: List[str] = None
    metadata: Dict = None
    
    def __post_init__(self):
        if self.features is None:
            self.features = []
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


class PlatformConnectionService:
    """
    Service for managing platform connections.
    
    Provides functionality to connect, disconnect, verify, and manage
    connections to external platforms.
    """
    
    def __init__(self):
        """Initialize platform connection service."""
        self.credential_service = CredentialService()
        self.connector_manager = ConnectorManager()
        self._connections: Dict[str, PlatformConnection] = {}
        self._verification_tasks: Dict[str, asyncio.Task] = {}
    
    def list_available_platforms(self) -> List[Dict]:
        """
        List all available platforms that can be connected.
        
        Returns:
            List of platform information dictionaries
        """
        platforms = []
        
        for connector_name, connector in self.connector_manager.connectors.items():
            platforms.append({
                "name": connector_name,
                "display_name": connector.display_name,
                "description": connector.description,
                "version": connector.version,
                "supports_training": connector.supports_training,
                "supports_inference": connector.supports_inference,
                "supports_registry": connector.supports_registry,
                "supports_tracking": connector.supports_tracking,
                "required_credentials": connector.get_required_credentials(),
                "connected": connector_name in self._connections and 
                           self._connections[connector_name].status == "connected"
            })
        
        return platforms
    
    async def connect_platform(
        self,
        platform_name: str,
        credentials: Dict[str, str]
    ) -> PlatformConnection:
        """
        Connect to a platform with provided credentials.
        
        Args:
            platform_name: Name of the platform to connect
            credentials: Dictionary of credential key-value pairs
            
        Returns:
            PlatformConnection object with connection status
            
        Raises:
            ValueError: If platform not found or credentials invalid
            ConnectionError: If connection fails
        """
        try:
            # Get connector
            connector = self.connector_manager.get(platform_name)
            if not connector:
                raise ValueError(f"Platform not found: {platform_name}")
            
            # Validate credentials
            required_creds = connector.get_required_credentials()
            for cred in required_creds:
                if cred not in credentials:
                    raise ValueError(f"Missing required credential: {cred}")
            
            # Update connection status to verifying
            connection = PlatformConnection(
                platform_name=platform_name,
                display_name=connector.display_name,
                status="verifying",
                features=self._get_connector_features(connector)
            )
            self._connections[platform_name] = connection
            
            # Attempt connection
            logger.info(f"Connecting to platform: {platform_name}")
            success = await connector.connect(credentials)
            
            if not success:
                connection.status = "error"
                connection.error_message = "Connection failed"
                raise ConnectionError(f"Failed to connect to {platform_name}")
            
            # Store credentials securely
            for cred_key, cred_value in credentials.items():
                self.credential_service.store_credential(
                    platform=platform_name,
                    credential_value=cred_value,
                    credential_type=cred_key
                )
            
            # Update connection status
            connection.status = "connected"
            connection.connected_at = datetime.now().isoformat()
            connection.last_verified = datetime.now().isoformat()
            
            logger.info(f"Successfully connected to platform: {platform_name}")
            return connection
            
        except Exception as e:
            logger.error(f"Error connecting to {platform_name}: {e}")
            if platform_name in self._connections:
                self._connections[platform_name].status = "error"
                self._connections[platform_name].error_message = str(e)
            raise
    
    async def disconnect_platform(self, platform_name: str) -> bool:
        """
        Disconnect from a platform.
        
        Args:
            platform_name: Name of the platform to disconnect
            
        Returns:
            True if disconnection successful
        """
        try:
            # Get connector
            connector = self.connector_manager.get(platform_name)
            if not connector:
                raise ValueError(f"Platform not found: {platform_name}")
            
            # Disconnect
            await connector.disconnect()
            
            # Delete credentials
            self.credential_service.delete_credential(platform_name)
            
            # Remove connection
            if platform_name in self._connections:
                del self._connections[platform_name]
            
            # Cancel verification task if running
            if platform_name in self._verification_tasks:
                self._verification_tasks[platform_name].cancel()
                del self._verification_tasks[platform_name]
            
            logger.info(f"Disconnected from platform: {platform_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting from {platform_name}: {e}")
            return False
    
    async def verify_connection(
        self,
        platform_name: str,
        timeout_seconds: int = 5
    ) -> Dict:
        """
        Verify that a platform connection is still valid.
        
        Args:
            platform_name: Name of the platform to verify
            timeout_seconds: Maximum time to wait for verification
            
        Returns:
            Dictionary with verification result
        """
        try:
            # Get connector
            connector = self.connector_manager.get(platform_name)
            if not connector:
                return {
                    "platform": platform_name,
                    "valid": False,
                    "error": "Platform not found",
                    "verified_at": datetime.now().isoformat()
                }
            
            # Check if connection exists
            if platform_name not in self._connections:
                return {
                    "platform": platform_name,
                    "valid": False,
                    "error": "Not connected",
                    "verified_at": datetime.now().isoformat()
                }
            
            # Verify with timeout
            start_time = datetime.now()
            try:
                valid = await asyncio.wait_for(
                    connector.verify_connection(),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                valid = False
                error = f"Verification timed out after {timeout_seconds} seconds"
            except Exception as e:
                valid = False
                error = str(e)
            else:
                error = None if valid else "Connection verification failed"
            
            # Update connection
            connection = self._connections[platform_name]
            if valid:
                connection.status = "connected"
                connection.last_verified = datetime.now().isoformat()
                connection.error_message = None
            else:
                connection.status = "error"
                connection.error_message = error
            
            verification_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "platform": platform_name,
                "valid": valid,
                "error": error,
                "verified_at": datetime.now().isoformat(),
                "verification_time_seconds": verification_time
            }
            
        except Exception as e:
            logger.error(f"Error verifying connection to {platform_name}: {e}")
            return {
                "platform": platform_name,
                "valid": False,
                "error": str(e),
                "verified_at": datetime.now().isoformat()
            }
    
    def get_connection(self, platform_name: str) -> Optional[PlatformConnection]:
        """
        Get connection information for a platform.
        
        Args:
            platform_name: Name of the platform
            
        Returns:
            PlatformConnection object or None if not connected
        """
        return self._connections.get(platform_name)
    
    def list_connections(self) -> List[PlatformConnection]:
        """
        List all active platform connections.
        
        Returns:
            List of PlatformConnection objects
        """
        return list(self._connections.values())
    
    async def test_connection(
        self,
        platform_name: str,
        credentials: Dict[str, str]
    ) -> Dict:
        """
        Test a connection without storing credentials.
        
        Args:
            platform_name: Name of the platform to test
            credentials: Dictionary of credential key-value pairs
            
        Returns:
            Dictionary with test result
        """
        try:
            # Get connector
            connector = self.connector_manager.get(platform_name)
            if not connector:
                return {
                    "success": False,
                    "error": f"Platform not found: {platform_name}",
                    "tested_at": datetime.now().isoformat()
                }
            
            # Test connection
            start_time = datetime.now()
            success = await connector.connect(credentials)
            test_time = (datetime.now() - start_time).total_seconds()
            
            # Disconnect immediately
            if success:
                await connector.disconnect()
            
            return {
                "success": success,
                "error": None if success else "Connection test failed",
                "tested_at": datetime.now().isoformat(),
                "test_time_seconds": test_time
            }
            
        except Exception as e:
            logger.error(f"Error testing connection to {platform_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "tested_at": datetime.now().isoformat()
            }
    
    async def update_credentials(
        self,
        platform_name: str,
        credentials: Dict[str, str]
    ) -> bool:
        """
        Update credentials for an existing connection.
        
        Args:
            platform_name: Name of the platform
            credentials: New credentials
            
        Returns:
            True if update successful
        """
        try:
            # Disconnect first
            await self.disconnect_platform(platform_name)
            
            # Reconnect with new credentials
            await self.connect_platform(platform_name, credentials)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating credentials for {platform_name}: {e}")
            return False
    
    def _get_connector_features(self, connector) -> List[str]:
        """
        Get list of features supported by a connector.
        
        Args:
            connector: Connector instance
            
        Returns:
            List of feature names
        """
        features = []
        if connector.supports_training:
            features.append("training")
        if connector.supports_inference:
            features.append("inference")
        if connector.supports_registry:
            features.append("registry")
        if connector.supports_tracking:
            features.append("tracking")
        return features
    
    async def verify_all_connections(self) -> Dict[str, Dict]:
        """
        Verify all active connections.
        
        Returns:
            Dictionary mapping platform names to verification results
        """
        results = {}
        
        for platform_name in self._connections.keys():
            results[platform_name] = await self.verify_connection(platform_name)
        
        return results
    
    def get_connection_stats(self) -> Dict:
        """
        Get statistics about platform connections.
        
        Returns:
            Dictionary with connection statistics
        """
        total = len(self._connections)
        connected = sum(1 for c in self._connections.values() if c.status == "connected")
        error = sum(1 for c in self._connections.values() if c.status == "error")
        
        return {
            "total_connections": total,
            "connected": connected,
            "error": error,
            "disconnected": total - connected - error
        }


# Singleton instance
_platform_connection_service = None


def get_platform_connection_service() -> PlatformConnectionService:
    """Get singleton instance of platform connection service."""
    global _platform_connection_service
    if _platform_connection_service is None:
        _platform_connection_service = PlatformConnectionService()
    return _platform_connection_service
