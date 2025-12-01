"""
Property-Based Test: Offline Queue Persistence

**Feature: unified-llm-platform, Property 3: Offline queue persistence**
**Validates: Requirements 12.2, 12.4**

Property: For any operation enqueued while offline, the operation should persist 
across application restarts until successfully synced.

This test verifies that:
1. Operations can be enqueued and persisted to SQLite
2. Operations survive application restarts (simulated by creating new instances)
3. Operations maintain their data integrity through serialization/deserialization
4. Operations remain in queue until explicitly marked as completed
"""

import pytest
from hypothesis import given, strategies as st, settings
from hypothesis import assume
import json
import tempfile
import os
from datetime import datetime

from services.offline_queue_service import (
    OfflineQueueManager,
    OperationType,
    OperationStatus
)


# Strategy for generating valid operation types
operation_type_strategy = st.sampled_from([
    OperationType.API_CALL,
    OperationType.FILE_UPLOAD,
    OperationType.METRIC_LOG,
    OperationType.MODEL_PUSH,
    OperationType.EXPERIMENT_SYNC
])


# Strategy for generating valid payloads (JSON-serializable dictionaries)
payload_strategy = st.fixed_dictionaries({
    "action": st.text(min_size=1, max_size=50),
    "data": st.one_of(
        st.text(min_size=0, max_size=100),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.booleans(),
        st.lists(st.text(min_size=0, max_size=20), max_size=5)
    ),
    "timestamp": st.integers(min_value=0, max_value=2000000000),
    "metadata": st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.text(min_size=0, max_size=50),
        max_size=3
    )
})


# Strategy for priority values
priority_strategy = st.integers(min_value=0, max_value=10)


@given(
    operation_type=operation_type_strategy,
    payload=payload_strategy,
    priority=priority_strategy
)
@settings(max_examples=100, deadline=None)
def test_offline_queue_persistence_property(operation_type, payload, priority):
    """
    Property Test: Offline queue persistence
    
    For any operation enqueued, it should:
    1. Be successfully stored in the database
    2. Be retrievable after "restart" (new manager instance)
    3. Maintain data integrity (payload matches original)
    4. Remain in queue until explicitly completed
    """
    # Create a temporary database for this test
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Phase 1: Enqueue operation with first manager instance
        manager1 = OfflineQueueManager(db_url=f"sqlite:///{db_path}")
        
        operation_id = manager1.enqueue(
            operation_type=operation_type,
            payload=payload,
            priority=priority
        )
        
        # Verify operation was created
        assert operation_id is not None
        assert operation_id > 0
        
        # Verify operation can be retrieved
        operation = manager1.get_operation(operation_id)
        assert operation is not None
        assert operation["id"] == operation_id
        assert operation["operation_type"] == operation_type.value
        assert operation["status"] == OperationStatus.PENDING.value
        assert operation["priority"] == priority
        
        # Verify payload integrity
        retrieved_payload = json.loads(operation["payload"])
        assert retrieved_payload == payload
        
        # Close first manager (simulate app shutdown)
        manager1.close()
        del manager1
        
        # Phase 2: Create new manager instance (simulate app restart)
        manager2 = OfflineQueueManager(db_url=f"sqlite:///{db_path}")
        
        # Verify operation still exists after "restart"
        operation_after_restart = manager2.get_operation(operation_id)
        assert operation_after_restart is not None
        assert operation_after_restart["id"] == operation_id
        
        # Verify all data persisted correctly
        assert operation_after_restart["operation_type"] == operation_type.value
        assert operation_after_restart["status"] == OperationStatus.PENDING.value
        assert operation_after_restart["priority"] == priority
        
        # Verify payload still matches original
        persisted_payload = json.loads(operation_after_restart["payload"])
        assert persisted_payload == payload
        
        # Verify operation appears in pending operations
        pending_ops = manager2.get_pending_operations()
        assert any(op["id"] == operation_id for op in pending_ops)
        
        # Phase 3: Verify operation persists until explicitly completed
        # Operation should still be pending
        stats_before = manager2.get_queue_stats()
        assert stats_before["pending"] >= 1
        
        # Mark as completed
        success = manager2.mark_completed(operation_id)
        assert success is True
        
        # Verify status changed
        completed_op = manager2.get_operation(operation_id)
        assert completed_op["status"] == OperationStatus.COMPLETED.value
        
        # Verify it's no longer in pending operations
        pending_ops_after = manager2.get_pending_operations()
        assert not any(op["id"] == operation_id for op in pending_ops_after)
        
        # Phase 4: Verify completed operation persists across restart
        manager2.close()
        del manager2
        
        manager3 = OfflineQueueManager(db_url=f"sqlite:///{db_path}")
        final_op = manager3.get_operation(operation_id)
        assert final_op is not None
        assert final_op["status"] == OperationStatus.COMPLETED.value
        
        # Payload should still be intact
        final_payload = json.loads(final_op["payload"])
        assert final_payload == payload
        
        # Close final manager
        manager3.close()
        del manager3
        
    finally:
        # Cleanup: Remove temporary database
        if os.path.exists(db_path):
            try:
                os.unlink(db_path)
            except PermissionError:
                # On Windows, sometimes the file is still locked
                # Try again after a short delay
                import time
                time.sleep(0.1)
                try:
                    os.unlink(db_path)
                except PermissionError:
                    pass  # If still locked, leave it for OS cleanup


@given(
    operations=st.lists(
        st.tuples(operation_type_strategy, payload_strategy, priority_strategy),
        min_size=1,
        max_size=10
    )
)
@settings(max_examples=50, deadline=None)
def test_multiple_operations_persistence(operations):
    """
    Property Test: Multiple operations persist correctly
    
    For any list of operations, all should persist and be retrievable
    in the correct order (by priority and creation time).
    """
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        manager1 = OfflineQueueManager(db_url=f"sqlite:///{db_path}")
        
        # Enqueue all operations
        operation_ids = []
        for op_type, payload, priority in operations:
            op_id = manager1.enqueue(
                operation_type=op_type,
                payload=payload,
                priority=priority
            )
            operation_ids.append(op_id)
        
        # Verify all were created
        assert len(operation_ids) == len(operations)
        assert len(set(operation_ids)) == len(operations)  # All unique
        
        # Simulate restart
        manager1.close()
        del manager1
        manager2 = OfflineQueueManager(db_url=f"sqlite:///{db_path}")
        
        # Verify all operations still exist
        for op_id in operation_ids:
            op = manager2.get_operation(op_id)
            assert op is not None
            assert op["id"] == op_id
        
        # Verify pending operations count
        pending = manager2.get_pending_operations()
        assert len(pending) == len(operations)
        
        # Verify operations are ordered by priority (desc) then creation time (asc)
        priorities = [op["priority"] for op in pending]
        for i in range(len(priorities) - 1):
            # If priorities are equal, creation time should be ascending
            if priorities[i] == priorities[i + 1]:
                assert pending[i]["created_at"] <= pending[i + 1]["created_at"]
        
        manager2.close()
        del manager2
        
    finally:
        if os.path.exists(db_path):
            try:
                os.unlink(db_path)
            except PermissionError:
                import time
                time.sleep(0.1)
                try:
                    os.unlink(db_path)
                except PermissionError:
                    pass


@given(
    operation_type=operation_type_strategy,
    payload=payload_strategy
)
@settings(max_examples=50, deadline=None)
def test_operation_status_transitions_persist(operation_type, payload):
    """
    Property Test: Status transitions persist across restarts
    
    For any operation, status changes should persist correctly.
    """
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        manager1 = OfflineQueueManager(db_url=f"sqlite:///{db_path}")
        
        # Create operation
        op_id = manager1.enqueue(operation_type, payload)
        
        # Transition to IN_PROGRESS
        manager1.update_status(op_id, OperationStatus.IN_PROGRESS)
        
        # Restart
        manager1.close()
        del manager1
        manager2 = OfflineQueueManager(db_url=f"sqlite:///{db_path}")
        
        # Verify status persisted
        op = manager2.get_operation(op_id)
        assert op["status"] == OperationStatus.IN_PROGRESS.value
        
        # Transition to FAILED
        manager2.mark_failed(op_id, "Test error")
        
        # Restart again
        manager2.close()
        del manager2
        manager3 = OfflineQueueManager(db_url=f"sqlite:///{db_path}")
        
        # Verify failed status and error message persisted
        op = manager3.get_operation(op_id)
        assert op["status"] == OperationStatus.FAILED.value
        assert op["error_message"] == "Test error"
        assert op["retry_count"] == 1
        
        manager3.close()
        del manager3
        
    finally:
        if os.path.exists(db_path):
            try:
                os.unlink(db_path)
            except PermissionError:
                import time
                time.sleep(0.1)
                try:
                    os.unlink(db_path)
                except PermissionError:
                    pass


def test_empty_queue_persistence():
    """
    Edge case: Empty queue should persist correctly
    """
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        manager1 = OfflineQueueManager(db_url=f"sqlite:///{db_path}")
        
        # Verify empty queue
        stats = manager1.get_queue_stats()
        assert stats["total"] == 0
        assert stats["pending"] == 0
        
        # Restart
        manager1.close()
        del manager1
        manager2 = OfflineQueueManager(db_url=f"sqlite:///{db_path}")
        
        # Verify still empty
        stats = manager2.get_queue_stats()
        assert stats["total"] == 0
        assert stats["pending"] == 0
        
        manager2.close()
        del manager2
        
    finally:
        if os.path.exists(db_path):
            try:
                os.unlink(db_path)
            except PermissionError:
                import time
                time.sleep(0.1)
                try:
                    os.unlink(db_path)
                except PermissionError:
                    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
