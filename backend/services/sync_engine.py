"""
Sync Engine

Handles synchronization of offline operations when connectivity is restored.
Includes conflict resolution strategies.
"""

import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum

from services.offline_queue_service import (
    get_queue_manager,
    OperationType,
    OperationStatus
)
from services.network_service import get_network_monitor, NetworkStatus


class ConflictResolution(str, Enum):
    """Conflict resolution strategies"""
    LOCAL_WINS = "local_wins"  # Use local version
    REMOTE_WINS = "remote_wins"  # Use remote version
    MERGE = "merge"  # Attempt to merge changes
    MANUAL = "manual"  # Require manual resolution


class SyncEngine:
    """
    Synchronization engine for offline operations.
    
    Features:
    - Automatic sync when network is restored
    - Conflict detection and resolution
    - Batch processing for efficiency
    - Progress tracking
    """
    
    def __init__(self):
        """Initialize sync engine"""
        self.queue_manager = get_queue_manager()
        self.network_monitor = get_network_monitor()
        self._is_syncing = False
        self._sync_task: Optional[asyncio.Task] = None
        self._operation_handlers: Dict[OperationType, Callable] = {}
        self._conflict_strategy = ConflictResolution.LOCAL_WINS
        
        # Register network status callback
        self.network_monitor.add_callback(self._on_network_status_change)
    
    def register_handler(
        self,
        operation_type: OperationType,
        handler: Callable
    ) -> None:
        """
        Register a handler for an operation type.
        
        Args:
            operation_type: Type of operation
            handler: Async function(payload) -> bool
        """
        self._operation_handlers[operation_type] = handler
    
    def set_conflict_strategy(self, strategy: ConflictResolution) -> None:
        """Set the conflict resolution strategy"""
        self._conflict_strategy = strategy
    
    async def _on_network_status_change(
        self,
        old_status: NetworkStatus,
        new_status: NetworkStatus
    ) -> None:
        """Handle network status changes"""
        if old_status == NetworkStatus.OFFLINE and new_status == NetworkStatus.ONLINE:
            # Network restored, start sync
            await self.sync()
    
    async def sync(self, force: bool = False) -> Dict[str, Any]:
        """
        Synchronize all pending operations.
        
        Args:
            force: Force sync even if already syncing
            
        Returns:
            Sync results dictionary
        """
        if self._is_syncing and not force:
            return {
                "status": "already_syncing",
                "message": "Sync already in progress"
            }
        
        if not self.network_monitor.is_online:
            return {
                "status": "offline",
                "message": "Cannot sync while offline"
            }
        
        self._is_syncing = True
        
        try:
            results = await self.queue_manager.sync_all(self._execute_operation)
            
            # Clean up completed operations
            cleaned = self.queue_manager.clear_completed()
            results["cleaned"] = cleaned
            
            return {
                "status": "completed",
                **results
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
        finally:
            self._is_syncing = False
    
    async def _execute_operation(
        self,
        operation_type: OperationType,
        payload: Dict[str, Any]
    ) -> bool:
        """
        Execute a single operation.
        
        Args:
            operation_type: Type of operation
            payload: Operation data
            
        Returns:
            True if successful, False otherwise
        """
        handler = self._operation_handlers.get(operation_type)
        
        if not handler:
            print(f"No handler registered for operation type: {operation_type}")
            return False
        
        try:
            # Check for conflicts
            conflict = await self._detect_conflict(operation_type, payload)
            
            if conflict:
                resolved_payload = await self._resolve_conflict(
                    operation_type,
                    payload,
                    conflict
                )
                if resolved_payload is None:
                    return False
                payload = resolved_payload
            
            # Execute the handler
            result = await handler(payload)
            return result
            
        except Exception as e:
            print(f"Error executing operation {operation_type}: {e}")
            return False
    
    async def _detect_conflict(
        self,
        operation_type: OperationType,
        payload: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Detect if there's a conflict with remote state.
        
        Args:
            operation_type: Type of operation
            payload: Local operation data
            
        Returns:
            Conflict information if detected, None otherwise
        """
        # This is a simplified conflict detection
        # In a real implementation, you would check against remote state
        
        # For now, we'll assume no conflicts
        # Real implementation would:
        # 1. Fetch current remote state
        # 2. Compare timestamps
        # 3. Check for data differences
        
        return None
    
    async def _resolve_conflict(
        self,
        operation_type: OperationType,
        local_payload: Dict[str, Any],
        conflict: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Resolve a conflict based on the configured strategy.
        
        Args:
            operation_type: Type of operation
            local_payload: Local version of data
            conflict: Conflict information including remote data
            
        Returns:
            Resolved payload or None if manual resolution required
        """
        if self._conflict_strategy == ConflictResolution.LOCAL_WINS:
            return local_payload
        
        elif self._conflict_strategy == ConflictResolution.REMOTE_WINS:
            return conflict.get("remote_payload")
        
        elif self._conflict_strategy == ConflictResolution.MERGE:
            # Attempt to merge changes
            return self._merge_payloads(local_payload, conflict.get("remote_payload", {}))
        
        elif self._conflict_strategy == ConflictResolution.MANUAL:
            # Require manual resolution
            return None
        
        return local_payload
    
    def _merge_payloads(
        self,
        local: Dict[str, Any],
        remote: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge local and remote payloads.
        
        Simple merge strategy:
        - Use local values for keys that exist in local
        - Add remote values for keys that don't exist in local
        
        Args:
            local: Local payload
            remote: Remote payload
            
        Returns:
            Merged payload
        """
        merged = remote.copy()
        merged.update(local)
        return merged
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status"""
        queue_stats = self.queue_manager.get_queue_stats()
        network_info = self.network_monitor.get_status_info()
        
        return {
            "is_syncing": self._is_syncing,
            "network_status": network_info["status"],
            "is_online": network_info["is_online"],
            "queue_stats": queue_stats,
            "conflict_strategy": self._conflict_strategy.value
        }
    
    async def start_auto_sync(self) -> None:
        """Start automatic synchronization when network is available"""
        await self.network_monitor.start_monitoring()
    
    async def stop_auto_sync(self) -> None:
        """Stop automatic synchronization"""
        await self.network_monitor.stop_monitoring()


# Global instance
_sync_engine: Optional[SyncEngine] = None


def get_sync_engine() -> SyncEngine:
    """Get or create the global sync engine instance"""
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = SyncEngine()
    return _sync_engine
