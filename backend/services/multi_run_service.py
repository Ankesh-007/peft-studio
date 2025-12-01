"""
Multi-Run Management Service

Provides concurrent run monitoring, run history tracking, filtering,
and run cancellation/cleanup functionality.

Requirements: 16.1, 16.2, 16.3, 16.4, 16.5
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from backend.database import TrainingRun, get_db
from backend.services.training_orchestration_service import (
    TrainingOrchestrator,
    TrainingJob,
    TrainingState,
    get_training_orchestrator
)

logger = logging.getLogger(__name__)


class RunStatus(str, Enum):
    """Run status values"""
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass
class RunFilter:
    """Filter criteria for run queries"""
    status: Optional[List[str]] = None
    provider: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    model_name: Optional[str] = None
    job_ids: Optional[List[str]] = None


@dataclass
class RunSummary:
    """Summary information for a training run"""
    job_id: str
    name: Optional[str]
    status: str
    provider: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    current_step: int
    total_steps: Optional[int]
    progress_percent: float
    current_loss: Optional[float]
    final_loss: Optional[float]
    error_message: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'job_id': self.job_id,
            'name': self.name,
            'status': self.status,
            'provider': self.provider,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': self.duration_seconds,
            'current_step': self.current_step,
            'total_steps': self.total_steps,
            'progress_percent': self.progress_percent,
            'current_loss': self.current_loss,
            'final_loss': self.final_loss,
            'error_message': self.error_message
        }


@dataclass
class ConcurrentRunStats:
    """Statistics for concurrent runs"""
    total_active: int
    running: int
    paused: int
    total_completed: int
    total_failed: int
    active_providers: Dict[str, int]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'total_active': self.total_active,
            'running': self.running,
            'paused': self.paused,
            'total_completed': self.total_completed,
            'total_failed': self.total_failed,
            'active_providers': self.active_providers
        }


class MultiRunManager:
    """
    Manages multiple concurrent training runs with tracking, monitoring,
    filtering, and cleanup capabilities.
    
    Requirements: 16.1, 16.2, 16.3, 16.4, 16.5
    """
    
    def __init__(self, orchestrator: Optional[TrainingOrchestrator] = None):
        """
        Initialize multi-run manager.
        
        Args:
            orchestrator: Training orchestrator instance (uses singleton if None)
        """
        self.orchestrator = orchestrator or get_training_orchestrator()
        logger.info("MultiRunManager initialized")
    
    def sync_run_to_database(self, job: TrainingJob, db: Session) -> TrainingRun:
        """
        Sync a training job to the database.
        
        Args:
            job: Training job to sync
            db: Database session
            
        Returns:
            TrainingRun database record
            
        Requirements: 16.1
        """
        # Check if run already exists
        db_run = db.query(TrainingRun).filter(
            TrainingRun.job_id == job.job_id
        ).first()
        
        if db_run is None:
            # Create new run
            db_run = TrainingRun(
                job_id=job.job_id,
                name=job.config.job_id,
                status=job.state.value,
                config=job.config.to_dict(),
                started_at=job.started_at,
                provider=job.provider
            )
            db.add(db_run)
        else:
            # Update existing run
            db_run.status = job.state.value
            db_run.completed_at = job.completed_at
            db_run.paused_at = job.paused_at
            db_run.error_message = job.error_message
            db_run.provider_job_id = job.provider_job_id
        
        # Update metrics if available (for both new and existing runs)
        if job.current_metrics:
            db_run.current_step = job.current_metrics.step
            db_run.current_epoch = job.current_metrics.epoch
            db_run.current_loss = job.current_metrics.loss
            db_run.gpu_utilization = (
                sum(job.current_metrics.gpu_utilization) / len(job.current_metrics.gpu_utilization)
                if job.current_metrics.gpu_utilization else None
            )
            db_run.memory_used = (
                sum(job.current_metrics.gpu_memory_used) / len(job.current_metrics.gpu_memory_used)
                if job.current_metrics.gpu_memory_used else None
            )
        
        # Update artifact info if available
        if job.artifact_info:
            db_run.artifact_path = str(job.artifact_info.path)
            db_run.artifact_hash = job.artifact_info.hash_sha256
        
        # Set total steps from config
        if job.config.max_steps:
            db_run.total_steps = job.config.max_steps
        elif job.config.num_epochs:
            # Estimate total steps (rough estimate)
            db_run.total_steps = job.config.num_epochs * 1000
        
        db.commit()
        db.refresh(db_run)
        
        return db_run
    
    def get_active_runs(self, db: Session) -> List[RunSummary]:
        """
        Get all active (running or paused) training runs.
        
        Args:
            db: Database session
            
        Returns:
            List of active run summaries
            
        Requirements: 16.2
        """
        # Sync all jobs from orchestrator to database
        for job in self.orchestrator.list_jobs():
            self.sync_run_to_database(job, db)
        
        # Query active runs
        active_runs = db.query(TrainingRun).filter(
            TrainingRun.status.in_([RunStatus.RUNNING.value, RunStatus.PAUSED.value])
        ).order_by(desc(TrainingRun.started_at)).all()
        
        return [self._run_to_summary(run) for run in active_runs]
    
    def get_run_history(
        self,
        db: Session,
        filter_criteria: Optional[RunFilter] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[RunSummary]:
        """
        Get run history with optional filtering.
        
        Args:
            db: Database session
            filter_criteria: Optional filter criteria
            limit: Maximum number of runs to return
            offset: Number of runs to skip
            
        Returns:
            List of run summaries
            
        Requirements: 16.4
        """
        # Build query
        query = db.query(TrainingRun)
        
        # Apply filters
        if filter_criteria:
            conditions = []
            
            if filter_criteria.status:
                conditions.append(TrainingRun.status.in_(filter_criteria.status))
            
            if filter_criteria.provider:
                conditions.append(TrainingRun.provider.in_(filter_criteria.provider))
            
            if filter_criteria.date_from:
                conditions.append(TrainingRun.started_at >= filter_criteria.date_from)
            
            if filter_criteria.date_to:
                conditions.append(TrainingRun.started_at <= filter_criteria.date_to)
            
            if filter_criteria.model_name:
                # Search in config JSON
                conditions.append(
                    TrainingRun.config.contains(filter_criteria.model_name)
                )
            
            if filter_criteria.job_ids:
                conditions.append(TrainingRun.job_id.in_(filter_criteria.job_ids))
            
            if conditions:
                query = query.filter(and_(*conditions))
        
        # Order by most recent first
        query = query.order_by(desc(TrainingRun.started_at))
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        runs = query.all()
        
        return [self._run_to_summary(run) for run in runs]
    
    def get_concurrent_stats(self, db: Session) -> ConcurrentRunStats:
        """
        Get statistics about concurrent runs.
        
        Args:
            db: Database session
            
        Returns:
            Concurrent run statistics
            
        Requirements: 16.2
        """
        # Sync all jobs first
        for job in self.orchestrator.list_jobs():
            self.sync_run_to_database(job, db)
        
        # Count active runs
        active_runs = db.query(TrainingRun).filter(
            TrainingRun.status.in_([RunStatus.RUNNING.value, RunStatus.PAUSED.value])
        ).all()
        
        running_count = sum(1 for r in active_runs if r.status == RunStatus.RUNNING.value)
        paused_count = sum(1 for r in active_runs if r.status == RunStatus.PAUSED.value)
        
        # Count completed and failed
        completed_count = db.query(TrainingRun).filter(
            TrainingRun.status == RunStatus.COMPLETED.value
        ).count()
        
        failed_count = db.query(TrainingRun).filter(
            TrainingRun.status == RunStatus.FAILED.value
        ).count()
        
        # Count by provider
        provider_counts = {}
        for run in active_runs:
            if run.provider:
                provider_counts[run.provider] = provider_counts.get(run.provider, 0) + 1
        
        return ConcurrentRunStats(
            total_active=len(active_runs),
            running=running_count,
            paused=paused_count,
            total_completed=completed_count,
            total_failed=failed_count,
            active_providers=provider_counts
        )
    
    def cancel_run(self, job_id: str, db: Session) -> bool:
        """
        Cancel a running or paused training run.
        
        Args:
            job_id: Job identifier
            db: Database session
            
        Returns:
            True if cancellation successful
            
        Requirements: 16.5
        """
        try:
            # Stop the job in orchestrator
            self.orchestrator.stop_training(job_id)
            
            # Update database
            db_run = db.query(TrainingRun).filter(
                TrainingRun.job_id == job_id
            ).first()
            
            if db_run:
                db_run.status = RunStatus.STOPPED.value
                db_run.completed_at = datetime.now()
                db.commit()
            
            logger.info(f"Cancelled run: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel run {job_id}: {e}")
            return False
    
    def cleanup_run(self, job_id: str, db: Session) -> bool:
        """
        Cleanup resources for a completed/failed/stopped run.
        
        Args:
            job_id: Job identifier
            db: Database session
            
        Returns:
            True if cleanup successful
            
        Requirements: 16.5
        """
        try:
            # Delete job from orchestrator
            self.orchestrator.delete_job(job_id)
            
            # Keep database record for history
            logger.info(f"Cleaned up run: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup run {job_id}: {e}")
            return False
    
    def get_run_details(self, job_id: str, db: Session) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific run.
        
        Args:
            job_id: Job identifier
            db: Database session
            
        Returns:
            Run details dictionary or None if not found
            
        Requirements: 16.3
        """
        # Try to get from orchestrator first (for active runs)
        try:
            job = self.orchestrator.get_status(job_id)
            self.sync_run_to_database(job, db)
        except ValueError:
            # Job not in orchestrator, will get from database
            pass
        
        # Get from database
        db_run = db.query(TrainingRun).filter(
            TrainingRun.job_id == job_id
        ).first()
        
        if not db_run:
            return None
        
        summary = self._run_to_summary(db_run)
        
        return {
            **summary.to_dict(),
            'config': db_run.config,
            'provider_job_id': db_run.provider_job_id,
            'artifact_path': db_run.artifact_path,
            'artifact_hash': db_run.artifact_hash,
            'gpu_utilization': db_run.gpu_utilization,
            'memory_used': db_run.memory_used
        }
    
    def _run_to_summary(self, run: TrainingRun) -> RunSummary:
        """
        Convert database run to summary.
        
        Args:
            run: Database run record
            
        Returns:
            RunSummary
        """
        # Calculate duration
        duration_seconds = None
        if run.started_at:
            end_time = run.completed_at or datetime.now()
            duration_seconds = (end_time - run.started_at).total_seconds()
        
        # Calculate progress
        progress_percent = 0.0
        if run.total_steps and run.total_steps > 0:
            progress_percent = (run.current_step / run.total_steps) * 100
        
        return RunSummary(
            job_id=run.job_id,
            name=run.name,
            status=run.status,
            provider=run.provider,
            started_at=run.started_at,
            completed_at=run.completed_at,
            duration_seconds=duration_seconds,
            current_step=run.current_step or 0,
            total_steps=run.total_steps,
            progress_percent=progress_percent,
            current_loss=run.current_loss,
            final_loss=run.final_loss,
            error_message=run.error_message
        )


# Singleton instance
_multi_run_manager_instance = None


def get_multi_run_manager() -> MultiRunManager:
    """Get singleton instance of MultiRunManager"""
    global _multi_run_manager_instance
    if _multi_run_manager_instance is None:
        _multi_run_manager_instance = MultiRunManager()
    return _multi_run_manager_instance
