"""
Offline Queue Service

Manages operations that need to be performed when online connectivity is restored.
Implements offline-first architecture with SQLite persistence.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import json
import asyncio
from sqlalchemy import Column, Integer, String, DateTime, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL

Base = declarative_base()


class OperationType(str, Enum):
    """Types of operations that can be queued"""
    API_CALL = "api_call"
    FILE_UPLOAD = "file_upload"
    METRIC_LOG = "metric_log"
    MODEL_PUSH = "model_push"
    EXPERIMENT_SYNC = "experiment_sync"


class OperationStatus(str, Enum):
    """Status of queued operations"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class OfflineOperation(Base):
    """Database model for offline operations"""
    __tablename__ = 'offline_operations'
    
    id = Column(Integer, primary_key=True)
    operation_type = Column(String, nullable=False)
    payload = Column(Text, nullable=False)  # JSON serialized
    status = Column(String, default=OperationStatus.PENDING.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    retry_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    priority = Column(Integer, default=0)  # Higher priority = executed first


class OfflineQueueManager:
    """
    Manages offline operations queue with SQLite persistence.
    
    Features:
    - Persistent queue across application restarts
    - Operation serialization/deserialization
    - Priority-based execution
    - Retry logic with exponential backoff
    - Conflict resolution
    """
    
    def __init__(self, db_url: str = DATABASE_URL):
        """Initialize the offline queue manager"""
        # Add check_same_thread=False for SQLite to work with multiple connections
        connect_args = {}
        if "sqlite" in db_url:
            connect_args = {"check_same_thread": False}
        
        self.engine = create_engine(db_url, connect_args=connect_args)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self._sync_task: Optional[asyncio.Task] = None
        self._is_syncing = False
        self.max_retries = 3
    
    def close(self):
        """Close all database connections"""
        self.engine.dispose()
    
    def enqueue(
        self,
        operation_type: OperationType,
        payload: Dict[str, Any],
        priority: int = 0
    ) -> int:
        """
        Add an operation to the queue.
        
        Args:
            operation_type: Type of operation
            payload: Operation data (must be JSON serializable)
            priority: Priority level (higher = executed first)
            
        Returns:
            Operation ID
        """
        db = self.SessionLocal()
        try:
            operation = OfflineOperation(
                operation_type=operation_type.value,
                payload=json.dumps(payload),
                priority=priority,
                status=OperationStatus.PENDING.value
            )
            db.add(operation)
            db.commit()
            db.refresh(operation)
            return operation.id
        finally:
            db.close()
    
    def get_pending_operations(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get pending operations ordered by priority and creation time.
        
        Args:
            limit: Maximum number of operations to return
            
        Returns:
            List of operation dictionaries
        """
        db = self.SessionLocal()
        try:
            query = db.query(OfflineOperation).filter(
                OfflineOperation.status == OperationStatus.PENDING.value
            ).order_by(
                OfflineOperation.priority.desc(),
                OfflineOperation.created_at.asc()
            )
            
            if limit:
                query = query.limit(limit)
            
            operations = query.all()
            return [self._operation_to_dict(op) for op in operations]
        finally:
            db.close()
    
    def get_operation(self, operation_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific operation by ID"""
        db = self.SessionLocal()
        try:
            operation = db.query(OfflineOperation).filter(
                OfflineOperation.id == operation_id
            ).first()
            return self._operation_to_dict(operation) if operation else None
        finally:
            db.close()
    
    def update_status(
        self,
        operation_id: int,
        status: OperationStatus,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Update the status of an operation.
        
        Args:
            operation_id: ID of the operation
            status: New status
            error_message: Error message if failed
            
        Returns:
            True if updated successfully
        """
        db = self.SessionLocal()
        try:
            operation = db.query(OfflineOperation).filter(
                OfflineOperation.id == operation_id
            ).first()
            
            if not operation:
                return False
            
            operation.status = status.value
            operation.updated_at = datetime.utcnow()
            
            if error_message:
                operation.error_message = error_message
            
            if status == OperationStatus.FAILED:
                operation.retry_count += 1
            
            db.commit()
            return True
        finally:
            db.close()
    
    def mark_completed(self, operation_id: int) -> bool:
        """Mark an operation as completed"""
        return self.update_status(operation_id, OperationStatus.COMPLETED)
    
    def mark_failed(self, operation_id: int, error_message: str) -> bool:
        """Mark an operation as failed"""
        return self.update_status(operation_id, OperationStatus.FAILED, error_message)
    
    def delete_operation(self, operation_id: int) -> bool:
        """Delete an operation from the queue"""
        db = self.SessionLocal()
        try:
            operation = db.query(OfflineOperation).filter(
                OfflineOperation.id == operation_id
            ).first()
            
            if not operation:
                return False
            
            db.delete(operation)
            db.commit()
            return True
        finally:
            db.close()
    
    def clear_completed(self) -> int:
        """
        Remove all completed operations from the queue.
        
        Returns:
            Number of operations deleted
        """
        db = self.SessionLocal()
        try:
            count = db.query(OfflineOperation).filter(
                OfflineOperation.status == OperationStatus.COMPLETED.value
            ).delete()
            db.commit()
            return count
        finally:
            db.close()
    
    def get_queue_stats(self) -> Dict[str, int]:
        """Get statistics about the queue"""
        db = self.SessionLocal()
        try:
            stats = {
                "total": db.query(OfflineOperation).count(),
                "pending": db.query(OfflineOperation).filter(
                    OfflineOperation.status == OperationStatus.PENDING.value
                ).count(),
                "in_progress": db.query(OfflineOperation).filter(
                    OfflineOperation.status == OperationStatus.IN_PROGRESS.value
                ).count(),
                "completed": db.query(OfflineOperation).filter(
                    OfflineOperation.status == OperationStatus.COMPLETED.value
                ).count(),
                "failed": db.query(OfflineOperation).filter(
                    OfflineOperation.status == OperationStatus.FAILED.value
                ).count()
            }
            return stats
        finally:
            db.close()
    
    def should_retry(self, operation_id: int) -> bool:
        """Check if an operation should be retried"""
        db = self.SessionLocal()
        try:
            operation = db.query(OfflineOperation).filter(
                OfflineOperation.id == operation_id
            ).first()
            
            if not operation:
                return False
            
            return (
                operation.status == OperationStatus.FAILED.value and
                operation.retry_count < self.max_retries
            )
        finally:
            db.close()
    
    def reset_for_retry(self, operation_id: int) -> bool:
        """Reset a failed operation for retry"""
        if not self.should_retry(operation_id):
            return False
        
        return self.update_status(operation_id, OperationStatus.PENDING)
    
    async def sync_all(self, executor_func) -> Dict[str, Any]:
        """
        Sync all pending operations using the provided executor function.
        
        Args:
            executor_func: Async function that executes an operation
                          Should accept (operation_type, payload) and return success bool
        
        Returns:
            Dictionary with sync results
        """
        if self._is_syncing:
            return {"status": "already_syncing"}
        
        self._is_syncing = True
        results = {
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            operations = self.get_pending_operations()
            
            for op in operations:
                results["processed"] += 1
                
                # Update to in_progress
                self.update_status(op["id"], OperationStatus.IN_PROGRESS)
                
                try:
                    # Execute the operation
                    success = await executor_func(
                        OperationType(op["operation_type"]),
                        json.loads(op["payload"])
                    )
                    
                    if success:
                        self.mark_completed(op["id"])
                        results["succeeded"] += 1
                    else:
                        self.mark_failed(op["id"], "Executor returned False")
                        results["failed"] += 1
                        results["errors"].append({
                            "id": op["id"],
                            "error": "Executor returned False"
                        })
                        
                except Exception as e:
                    error_msg = str(e)
                    self.mark_failed(op["id"], error_msg)
                    results["failed"] += 1
                    results["errors"].append({
                        "id": op["id"],
                        "error": error_msg
                    })
            
            return results
        finally:
            self._is_syncing = False
    
    def _operation_to_dict(self, operation: OfflineOperation) -> Dict[str, Any]:
        """Convert operation model to dictionary"""
        return {
            "id": operation.id,
            "operation_type": operation.operation_type,
            "payload": operation.payload,
            "status": operation.status,
            "created_at": operation.created_at.isoformat(),
            "updated_at": operation.updated_at.isoformat(),
            "retry_count": operation.retry_count,
            "error_message": operation.error_message,
            "priority": operation.priority
        }


# Global instance
_queue_manager: Optional[OfflineQueueManager] = None


def get_queue_manager() -> OfflineQueueManager:
    """Get or create the global queue manager instance"""
    global _queue_manager
    if _queue_manager is None:
        _queue_manager = OfflineQueueManager()
    return _queue_manager
