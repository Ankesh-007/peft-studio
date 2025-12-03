# Offline-First Architecture

## Overview

The offline-first architecture enables PEFT Studio to function seamlessly without internet connectivity. Operations are queued locally and automatically synchronized when connectivity is restored.

## Components

### 1. OfflineQueueManager (`offline_queue_service.py`)

Manages the persistent queue of operations that need to be executed when online.

**Features:**
- SQLite-based persistence across application restarts
- Priority-based operation ordering
- Operation serialization/deserialization
- Retry logic with configurable max attempts
- Status tracking (pending, in_progress, completed, failed)

**Usage:**

```python
from services.offline_queue_service import get_queue_manager, OperationType

queue_manager = get_queue_manager()

# Enqueue an operation
operation_id = queue_manager.enqueue(
    operation_type=OperationType.API_CALL,
    payload={
        "endpoint": "/api/models/upload",
        "method": "POST",
        "data": {"model_name": "my-adapter"}
    },
    priority=5  # Higher priority = executed first
)

# Get pending operations
pending = queue_manager.get_pending_operations()

# Mark operation as completed
queue_manager.mark_completed(operation_id)

# Get queue statistics
stats = queue_manager.get_queue_stats()
```

### 2. NetworkMonitor (`network_service.py`)

Monitors network connectivity status and notifies listeners of changes.

**Features:**
- Periodic connectivity checks
- Multiple endpoint testing for reliability
- Callback notifications on status changes
- Configurable check interval

**Usage:**

```python
from services.network_service import get_network_monitor, NetworkStatus

monitor = get_network_monitor()

# Check connectivity manually
is_online = await monitor.check_connectivity()

# Register a callback for status changes
async def on_status_change(old_status, new_status):
    if new_status == NetworkStatus.ONLINE:
        print("Network restored!")

monitor.add_callback(on_status_change)

# Start automatic monitoring
await monitor.start_monitoring()

# Get current status
status_info = monitor.get_status_info()
```

### 3. SyncEngine (`sync_engine.py`)

Handles synchronization of offline operations when connectivity is restored.

**Features:**
- Automatic sync when network is restored
- Conflict detection and resolution
- Batch processing for efficiency
- Progress tracking
- Configurable conflict resolution strategies

**Usage:**

```python
from services.sync_engine import get_sync_engine, ConflictResolution

sync_engine = get_sync_engine()

# Register operation handlers
async def handle_api_call(payload):
    # Execute the API call
    response = await make_api_call(payload)
    return response.success

sync_engine.register_handler(OperationType.API_CALL, handle_api_call)

# Set conflict resolution strategy
sync_engine.set_conflict_strategy(ConflictResolution.LOCAL_WINS)

# Start automatic synchronization
await sync_engine.start_auto_sync()

# Manual sync
results = await sync_engine.sync()
```

## Operation Types

The system supports the following operation types:

- `API_CALL`: Generic API calls to external services
- `FILE_UPLOAD`: File upload operations
- `METRIC_LOG`: Experiment tracking metrics
- `MODEL_PUSH`: Model/adapter uploads to registries
- `EXPERIMENT_SYNC`: Experiment data synchronization

## Conflict Resolution Strategies

When syncing operations, conflicts may occur if remote state has changed. The system supports multiple resolution strategies:

- `LOCAL_WINS`: Use local version (default)
- `REMOTE_WINS`: Use remote version
- `MERGE`: Attempt to merge changes
- `MANUAL`: Require manual resolution

## API Endpoints

### Network Status

```
GET /api/offline/network-status
```
Returns current network connectivity status.

```
POST /api/offline/check-connectivity
```
Manually trigger a connectivity check.

### Queue Management

```
POST /api/offline/queue
```
Add an operation to the offline queue.

Request body:
```json
{
  "operation_type": "api_call",
  "payload": {
    "endpoint": "/api/models",
    "method": "GET"
  },
  "priority": 0
}
```

```
GET /api/offline/queue
```
Get pending operations from the queue.

```
GET /api/offline/queue/{operation_id}
```
Get a specific operation.

```
DELETE /api/offline/queue/{operation_id}
```
Delete an operation from the queue.

```
GET /api/offline/queue/stats
```
Get queue statistics.

```
POST /api/offline/queue/clear-completed
```
Clear all completed operations.

### Synchronization

```
POST /api/offline/sync
```
Manually trigger synchronization.

```
GET /api/offline/sync/status
```
Get current synchronization status.

```
POST /api/offline/sync/start-auto
```
Start automatic synchronization.

```
POST /api/offline/sync/stop-auto
```
Stop automatic synchronization.

```
POST /api/offline/sync/conflict-strategy
```
Set the conflict resolution strategy.

Request body:
```json
{
  "strategy": "local_wins"
}
```

## UI Components

### OfflineIndicator Component

A React component that displays network status and offline queue information.

**Features:**
- Visual indicator of online/offline status
- Pending operations count
- Expandable details panel
- Manual sync trigger
- Queue statistics display

**Usage:**

```tsx
import { OfflineIndicator } from './components/OfflineIndicator';

function App() {
  return (
    <div>
      {/* Your app content */}
      <OfflineIndicator />
    </div>
  );
}
```

## Database Schema

### offline_operations Table

```sql
CREATE TABLE offline_operations (
    id INTEGER PRIMARY KEY,
    operation_type TEXT NOT NULL,
    payload TEXT NOT NULL,  -- JSON serialized
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    priority INTEGER DEFAULT 0
);
```

## Testing

The offline-first architecture includes comprehensive property-based tests:

### Property 3: Offline Queue Persistence

**Validates Requirements 12.2, 12.4**

Tests that operations persist correctly across application restarts:

```bash
cd backend
python -m pytest tests/test_offline_queue_persistence.py -v
```

The test verifies:
1. Operations can be enqueued and persisted to SQLite
2. Operations survive application restarts
3. Operations maintain data integrity through serialization/deserialization
4. Operations remain in queue until explicitly marked as completed

## Best Practices

### 1. Always Use the Queue for External Operations

When offline, queue all operations that require network connectivity:

```python
if not network_monitor.is_online:
    queue_manager.enqueue(
        operation_type=OperationType.API_CALL,
        payload=operation_data
    )
else:
    # Execute immediately
    await execute_operation(operation_data)
```

### 2. Register Operation Handlers

Register handlers for all operation types you use:

```python
sync_engine.register_handler(
    OperationType.MODEL_PUSH,
    handle_model_push
)
```

### 3. Handle Sync Results

Check sync results and handle failures appropriately:

```python
results = await sync_engine.sync()
if results["failed"] > 0:
    for error in results["errors"]:
        logger.error(f"Operation {error['id']} failed: {error['error']}")
```

### 4. Clean Up Completed Operations

Periodically clean up completed operations to prevent database bloat:

```python
# Clean up operations older than 7 days
queue_manager.clear_completed()
```

### 5. Monitor Queue Size

Monitor queue size and alert users if it grows too large:

```python
stats = queue_manager.get_queue_stats()
if stats["pending"] > 100:
    notify_user("Large number of pending operations")
```

## Troubleshooting

### Operations Not Syncing

1. Check network status: `GET /api/offline/network-status`
2. Check sync status: `GET /api/offline/sync/status`
3. Verify operation handlers are registered
4. Check operation error messages in the queue

### Database Locked Errors

On Windows, ensure connections are properly closed:

```python
manager = OfflineQueueManager()
# ... use manager ...
manager.close()  # Important on Windows
```

### High Memory Usage

If the queue grows very large, consider:
1. Clearing completed operations more frequently
2. Implementing queue size limits
3. Batching operations more aggressively

## Future Enhancements

- [ ] Implement operation batching for efficiency
- [ ] Add operation expiration/TTL
- [ ] Implement more sophisticated conflict resolution
- [ ] Add operation dependencies (execute in specific order)
- [ ] Implement operation cancellation
- [ ] Add compression for large payloads
- [ ] Implement queue size limits with overflow handling
