"""
Offline-First Architecture Integration Example

This example demonstrates how to use the offline-first architecture
in a real application scenario.
"""

import asyncio
from typing import Dict, Any

from services.offline_queue_service import get_queue_manager, OperationType
from services.network_service import get_network_monitor, NetworkStatus
from services.sync_engine import get_sync_engine, ConflictResolution


async def example_api_call_handler(payload: Dict[str, Any]) -> bool:
    """
    Example handler for API call operations.
    
    In a real application, this would make actual API calls.
    """
    print(f"Executing API call: {payload.get('endpoint')}")
    
    # Simulate API call
    await asyncio.sleep(0.1)
    
    # Return success
    return True


async def example_model_push_handler(payload: Dict[str, Any]) -> bool:
    """
    Example handler for model push operations.
    
    In a real application, this would upload models to registries.
    """
    print(f"Pushing model: {payload.get('model_name')} to {payload.get('registry')}")
    
    # Simulate upload
    await asyncio.sleep(0.2)
    
    return True


async def on_network_status_change(old_status: NetworkStatus, new_status: NetworkStatus):
    """
    Callback for network status changes.
    
    This is automatically called when network status changes.
    """
    print(f"Network status changed: {old_status.value} -> {new_status.value}")
    
    if new_status == NetworkStatus.ONLINE:
        print("Network restored! Sync will start automatically.")


async def main():
    """
    Main example demonstrating offline-first architecture.
    """
    print("=== Offline-First Architecture Example ===\n")
    
    # Get service instances
    queue_manager = get_queue_manager()
    network_monitor = get_network_monitor()
    sync_engine = get_sync_engine()
    
    # Register operation handlers
    print("1. Registering operation handlers...")
    sync_engine.register_handler(OperationType.API_CALL, example_api_call_handler)
    sync_engine.register_handler(OperationType.MODEL_PUSH, example_model_push_handler)
    
    # Set conflict resolution strategy
    sync_engine.set_conflict_strategy(ConflictResolution.LOCAL_WINS)
    print("   ✓ Handlers registered\n")
    
    # Register network status callback
    print("2. Setting up network monitoring...")
    network_monitor.add_callback(on_network_status_change)
    await network_monitor.start_monitoring()
    print("   ✓ Network monitoring started\n")
    
    # Check initial network status
    print("3. Checking network status...")
    await network_monitor.update_status()
    status_info = network_monitor.get_status_info()
    print(f"   Status: {status_info['status']}")
    print(f"   Is Online: {status_info['is_online']}\n")
    
    # Simulate offline scenario
    print("4. Simulating offline operations...")
    
    # Queue some operations (as if we were offline)
    operations = [
        {
            "type": OperationType.API_CALL,
            "payload": {
                "endpoint": "/api/models/list",
                "method": "GET"
            },
            "priority": 1
        },
        {
            "type": OperationType.MODEL_PUSH,
            "payload": {
                "model_name": "my-lora-adapter",
                "registry": "huggingface",
                "repo_name": "username/my-adapter"
            },
            "priority": 5  # Higher priority
        },
        {
            "type": OperationType.API_CALL,
            "payload": {
                "endpoint": "/api/experiments/log",
                "method": "POST",
                "data": {"loss": 0.5, "epoch": 1}
            },
            "priority": 3
        }
    ]
    
    for op in operations:
        op_id = queue_manager.enqueue(
            operation_type=op["type"],
            payload=op["payload"],
            priority=op["priority"]
        )
        print(f"   ✓ Queued operation {op_id}: {op['type'].value}")
    
    print()
    
    # Check queue stats
    print("5. Queue statistics:")
    stats = queue_manager.get_queue_stats()
    print(f"   Total: {stats['total']}")
    print(f"   Pending: {stats['pending']}")
    print(f"   Completed: {stats['completed']}")
    print(f"   Failed: {stats['failed']}\n")
    
    # Get pending operations (ordered by priority)
    print("6. Pending operations (ordered by priority):")
    pending = queue_manager.get_pending_operations()
    for op in pending:
        print(f"   - ID {op['id']}: {op['operation_type']} (priority: {op['priority']})")
    print()
    
    # Simulate going online and syncing
    print("7. Simulating sync when online...")
    if network_monitor.is_online:
        results = await sync_engine.sync()
        print(f"   Sync completed:")
        print(f"   - Processed: {results['processed']}")
        print(f"   - Succeeded: {results['succeeded']}")
        print(f"   - Failed: {results['failed']}")
        print(f"   - Cleaned: {results.get('cleaned', 0)} completed operations\n")
    else:
        print("   Currently offline - operations will sync when online\n")
    
    # Check final queue stats
    print("8. Final queue statistics:")
    final_stats = queue_manager.get_queue_stats()
    print(f"   Total: {final_stats['total']}")
    print(f"   Pending: {final_stats['pending']}")
    print(f"   Completed: {final_stats['completed']}")
    print(f"   Failed: {final_stats['failed']}\n")
    
    # Get sync status
    print("9. Sync engine status:")
    sync_status = sync_engine.get_sync_status()
    print(f"   Is Syncing: {sync_status['is_syncing']}")
    print(f"   Network Status: {sync_status['network_status']}")
    print(f"   Conflict Strategy: {sync_status['conflict_strategy']}\n")
    
    # Clean up
    print("10. Cleaning up...")
    await network_monitor.stop_monitoring()
    queue_manager.close()
    print("    ✓ Cleanup complete\n")
    
    print("=== Example Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
