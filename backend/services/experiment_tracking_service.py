"""
Unified Experiment Tracking Service

Provides a unified interface for experiment tracking across multiple platforms:
- Weights & Biases
- Comet ML
- Arize Phoenix

Features:
- Automatic metric logging with batching
- Hyperparameter tracking
- Artifact linking
- Experiment comparison
- Search and filtering
- Offline queue support

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
"""

from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging
import asyncio
from datetime import datetime
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class TrackerType(Enum):
    """Supported experiment tracker types"""
    WANDB = "wandb"
    COMETML = "cometml"
    PHOENIX = "phoenix"


@dataclass
class ExperimentConfig:
    """Configuration for experiment tracking"""
    enabled_trackers: List[TrackerType] = field(default_factory=list)
    project_name: str = "peft-studio"
    auto_log_metrics: bool = True
    batch_size: int = 10  # Batch metrics to minimize API calls
    batch_interval: float = 5.0  # Seconds between batch uploads
    offline_mode: bool = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['enabled_trackers'] = [t.value for t in self.enabled_trackers]
        return data


@dataclass
class ExperimentMetadata:
    """Metadata for an experiment"""
    job_id: str
    run_name: str
    model_name: str
    dataset_name: str
    use_case: str
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class MetricBatch:
    """Batch of metrics to log"""
    job_id: str
    metrics: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def add_metric(self, metrics: Dict[str, Any], step: Optional[int] = None):
        """Add metrics to batch"""
        self.metrics.append({
            'data': metrics,
            'step': step,
            'timestamp': datetime.now().isoformat()
        })
    
    def is_full(self, batch_size: int) -> bool:
        """Check if batch is full"""
        return len(self.metrics) >= batch_size
    
    def clear(self):
        """Clear batch"""
        self.metrics.clear()
        self.timestamp = datetime.now()


class ExperimentTrackingService:
    """
    Unified service for experiment tracking across multiple platforms.
    
    Provides automatic metric logging, hyperparameter tracking, and
    experiment comparison with support for offline queueing.
    """
    
    def __init__(self, config: Optional[ExperimentConfig] = None):
        self.config = config or ExperimentConfig()
        self.active_experiments: Dict[str, Dict[str, Any]] = {}  # job_id -> experiment info
        self.metric_batches: Dict[str, MetricBatch] = {}  # job_id -> batch
        self.offline_queue: List[Dict] = []
        self._batch_task: Optional[asyncio.Task] = None
        self._trackers: Dict[TrackerType, Any] = {}
        
        # Initialize trackers
        self._initialize_trackers()
        
        logger.info(f"ExperimentTrackingService initialized with trackers: {[t.value for t in self.config.enabled_trackers]}")
    
    def _initialize_trackers(self):
        """Initialize enabled experiment trackers"""
        for tracker_type in self.config.enabled_trackers:
            try:
                if tracker_type == TrackerType.WANDB:
                    from services.wandb_integration_service import get_wandb_service
                    self._trackers[tracker_type] = get_wandb_service()
                    logger.info("Initialized W&B tracker")
                
                elif tracker_type == TrackerType.COMETML:
                    # Import Comet ML service when available
                    logger.info("Comet ML tracker not yet implemented")
                
                elif tracker_type == TrackerType.PHOENIX:
                    # Import Phoenix service when available
                    logger.info("Phoenix tracker not yet implemented")
                
            except Exception as e:
                logger.error(f"Failed to initialize {tracker_type.value} tracker: {e}")
    
    def _start_batch_processing(self):
        """Start background task for batch processing"""
        try:
            loop = asyncio.get_running_loop()
            if self._batch_task is None or self._batch_task.done():
                self._batch_task = loop.create_task(self._process_batches())
                logger.info("Started batch processing task")
        except RuntimeError:
            # No event loop running, will start later when needed
            logger.debug("No event loop running, batch processing will start on first use")
    
    async def _process_batches(self):
        """Background task to process metric batches"""
        while True:
            try:
                await asyncio.sleep(self.config.batch_interval)
                
                # Process all batches
                for job_id, batch in list(self.metric_batches.items()):
                    if batch.metrics:
                        await self._flush_batch(job_id)
                
            except asyncio.CancelledError:
                logger.info("Batch processing task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in batch processing: {e}")
    
    async def _flush_batch(self, job_id: str):
        """Flush a metric batch to all trackers"""
        if job_id not in self.metric_batches:
            return
        
        batch = self.metric_batches[job_id]
        if not batch.metrics:
            return
        
        logger.debug(f"Flushing {len(batch.metrics)} metrics for job {job_id}")
        
        # Log to each enabled tracker
        for tracker_type, tracker in self._trackers.items():
            try:
                for metric_entry in batch.metrics:
                    await self._log_to_tracker(
                        tracker_type,
                        tracker,
                        job_id,
                        metric_entry['data'],
                        metric_entry['step']
                    )
            except Exception as e:
                logger.error(f"Failed to flush batch to {tracker_type.value}: {e}")
        
        # Clear batch
        batch.clear()
    
    async def _log_to_tracker(
        self,
        tracker_type: TrackerType,
        tracker: Any,
        job_id: str,
        metrics: Dict[str, Any],
        step: Optional[int]
    ):
        """Log metrics to a specific tracker"""
        if tracker_type == TrackerType.WANDB:
            tracker.log_metrics(job_id, metrics, step=step, commit=True)
        
        # Add other tracker implementations here
    
    async def start_experiment(
        self,
        job_id: str,
        metadata: ExperimentMetadata,
        config: Dict[str, Any],
        resume: bool = False
    ) -> bool:
        """
        Start a new experiment across all enabled trackers.
        
        Args:
            job_id: Unique job identifier
            metadata: Experiment metadata
            config: Training configuration (hyperparameters)
            resume: Whether to resume an existing experiment
            
        Returns:
            True if started successfully on at least one tracker
        """
        logger.info(f"Starting experiment for job {job_id}")
        
        # Start batch processing if not already running
        if self.config.auto_log_metrics:
            self._start_batch_processing()
        
        success_count = 0
        tracker_runs = {}
        
        # Start experiment on each tracker
        for tracker_type, tracker in self._trackers.items():
            try:
                if tracker_type == TrackerType.WANDB:
                    from services.wandb_integration_service import ExperimentMetadata as WandBMetadata
                    wandb_metadata = WandBMetadata(
                        job_id=job_id,
                        model_name=metadata.model_name,
                        dataset_name=metadata.dataset_name,
                        use_case=metadata.use_case,
                        run_name=metadata.run_name
                    )
                    success = tracker.start_run(job_id, wandb_metadata, config, resume)
                    if success:
                        success_count += 1
                        tracker_runs[tracker_type] = tracker.get_run_url(job_id)
                        logger.info(f"Started experiment on {tracker_type.value}")
                
            except Exception as e:
                logger.error(f"Failed to start experiment on {tracker_type.value}: {e}")
        
        if success_count > 0:
            self.active_experiments[job_id] = {
                'tracker_runs': tracker_runs,
                'started_at': datetime.now().isoformat(),
                'status': 'running'
            }
            
            # Initialize metric batch
            self.metric_batches[job_id] = MetricBatch(job_id=job_id)
            
            return True
        
        return False
    
    async def log_metrics(
        self,
        job_id: str,
        metrics: Dict[str, Any],
        step: Optional[int] = None,
        immediate: bool = False
    ) -> bool:
        """
        Log metrics for an experiment.
        
        Args:
            job_id: Job identifier
            metrics: Dictionary of metric name -> value
            step: Training step number
            immediate: If True, bypass batching and log immediately
            
        Returns:
            True if logged successfully
        """
        if job_id not in self.active_experiments:
            logger.warning(f"No active experiment for job {job_id}")
            return False
        
        if immediate or not self.config.auto_log_metrics:
            # Log immediately to all trackers
            success = False
            for tracker_type, tracker in self._trackers.items():
                try:
                    await self._log_to_tracker(tracker_type, tracker, job_id, metrics, step)
                    success = True
                except Exception as e:
                    logger.error(f"Failed to log metrics to {tracker_type.value}: {e}")
            return success
        
        else:
            # Add to batch
            if job_id not in self.metric_batches:
                self.metric_batches[job_id] = MetricBatch(job_id=job_id)
            
            batch = self.metric_batches[job_id]
            batch.add_metric(metrics, step)
            
            # Flush if batch is full
            if batch.is_full(self.config.batch_size):
                await self._flush_batch(job_id)
            
            return True
    
    async def log_hyperparameters(
        self,
        job_id: str,
        hyperparameters: Dict[str, Any]
    ) -> bool:
        """
        Log or update hyperparameters for an experiment.
        
        Args:
            job_id: Job identifier
            hyperparameters: Dictionary of hyperparameter name -> value
            
        Returns:
            True if logged successfully
        """
        if job_id not in self.active_experiments:
            logger.warning(f"No active experiment for job {job_id}")
            return False
        
        success = False
        for tracker_type, tracker in self._trackers.items():
            try:
                if tracker_type == TrackerType.WANDB:
                    tracker.log_hyperparameters(job_id, hyperparameters)
                    success = True
            except Exception as e:
                logger.error(f"Failed to log hyperparameters to {tracker_type.value}: {e}")
        
        return success
    
    async def log_artifact(
        self,
        job_id: str,
        artifact_path: str,
        artifact_type: str = "model",
        name: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Log an artifact (model checkpoint, dataset, etc.) to trackers.
        
        Args:
            job_id: Job identifier
            artifact_path: Path to the artifact file/directory
            artifact_type: Type of artifact (model, dataset, etc.)
            name: Artifact name
            metadata: Additional metadata
            
        Returns:
            True if logged successfully
        """
        if job_id not in self.active_experiments:
            logger.warning(f"No active experiment for job {job_id}")
            return False
        
        success = False
        for tracker_type, tracker in self._trackers.items():
            try:
                if tracker_type == TrackerType.WANDB:
                    tracker.log_artifact(job_id, artifact_path, artifact_type, name, metadata)
                    success = True
            except Exception as e:
                logger.error(f"Failed to log artifact to {tracker_type.value}: {e}")
        
        return success
    
    async def finish_experiment(
        self,
        job_id: str,
        exit_code: int = 0,
        summary: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Finish an experiment across all trackers.
        
        Args:
            job_id: Job identifier
            exit_code: Exit code (0 for success, non-zero for failure)
            summary: Final summary metrics
            
        Returns:
            True if finished successfully
        """
        if job_id not in self.active_experiments:
            logger.warning(f"No active experiment for job {job_id}")
            return False
        
        # Flush any remaining metrics
        if job_id in self.metric_batches:
            await self._flush_batch(job_id)
        
        # Finish on all trackers
        success = False
        for tracker_type, tracker in self._trackers.items():
            try:
                if tracker_type == TrackerType.WANDB:
                    tracker.finish_run(job_id, exit_code, summary)
                    success = True
            except Exception as e:
                logger.error(f"Failed to finish experiment on {tracker_type.value}: {e}")
        
        # Update experiment info
        if job_id in self.active_experiments:
            self.active_experiments[job_id]['status'] = 'completed' if exit_code == 0 else 'failed'
            self.active_experiments[job_id]['finished_at'] = datetime.now().isoformat()
        
        # Cleanup
        self.metric_batches.pop(job_id, None)
        
        logger.info(f"Finished experiment for job {job_id}")
        return success
    
    def get_experiment_urls(self, job_id: str) -> Dict[str, str]:
        """
        Get dashboard URLs for an experiment across all trackers.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Dictionary mapping tracker type to URL
        """
        if job_id not in self.active_experiments:
            return {}
        
        return self.active_experiments[job_id].get('tracker_runs', {})
    
    def list_active_experiments(self) -> List[str]:
        """Get list of active experiment job IDs"""
        return [
            job_id for job_id, info in self.active_experiments.items()
            if info.get('status') == 'running'
        ]
    
    def get_experiment_info(self, job_id: str) -> Optional[Dict]:
        """Get information about an experiment"""
        return self.active_experiments.get(job_id)
    
    async def search_experiments(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = 'started_at',
        limit: int = 100
    ) -> List[Dict]:
        """
        Search and filter experiments.
        
        Args:
            filters: Dictionary of filter criteria
            sort_by: Field to sort by
            limit: Maximum number of results
            
        Returns:
            List of matching experiments
        """
        results = list(self.active_experiments.values())
        
        # Apply filters
        if filters:
            for key, value in filters.items():
                if key == 'status':
                    results = [r for r in results if r.get('status') == value]
                elif key == 'model_name':
                    results = [r for r in results if r.get('metadata', {}).get('model_name') == value]
                elif key == 'use_case':
                    results = [r for r in results if r.get('metadata', {}).get('use_case') == value]
                elif key == 'tags':
                    # Filter by tags (any match)
                    tag_set = set(value) if isinstance(value, list) else {value}
                    results = [
                        r for r in results
                        if tag_set.intersection(set(r.get('metadata', {}).get('tags', [])))
                    ]
        
        # Sort results
        results.sort(key=lambda x: x.get(sort_by, ''), reverse=True)
        
        # Limit results
        return results[:limit]
    
    async def compare_experiments(
        self,
        job_ids: List[str],
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compare multiple experiments.
        
        Args:
            job_ids: List of job identifiers to compare
            metrics: Optional list of specific metrics to compare
            
        Returns:
            Comparison data including metrics, configs, and URLs
        """
        comparison = {
            'experiments': [],
            'comparison_urls': {},
            'metric_comparison': {},
        }
        
        # Gather experiment data
        for job_id in job_ids:
            if job_id in self.active_experiments:
                exp_info = self.active_experiments[job_id]
                comparison['experiments'].append({
                    'job_id': job_id,
                    'metadata': exp_info.get('metadata'),
                    'config': exp_info.get('config'),
                    'status': exp_info.get('status'),
                })
        
        # Get comparison URLs from trackers
        for tracker_type, tracker in self._trackers.items():
            try:
                if tracker_type == TrackerType.WANDB:
                    url = tracker.compare_runs(job_ids, metrics)
                    if url:
                        comparison['comparison_urls'][tracker_type.value] = url
            except Exception as e:
                logger.error(f"Failed to get comparison URL from {tracker_type.value}: {e}")
        
        return comparison
    
    async def shutdown(self):
        """Shutdown the service and cleanup resources"""
        logger.info("Shutting down experiment tracking service")
        
        # Cancel batch processing task
        if self._batch_task and not self._batch_task.done():
            self._batch_task.cancel()
            try:
                await self._batch_task
            except asyncio.CancelledError:
                pass
        
        # Flush all remaining batches
        for job_id in list(self.metric_batches.keys()):
            await self._flush_batch(job_id)
        
        # Finish all active experiments
        for job_id in list(self.active_experiments.keys()):
            if self.active_experiments[job_id].get('status') == 'running':
                await self.finish_experiment(job_id, exit_code=0)
        
        logger.info("Experiment tracking service shutdown complete")


# Singleton instance
_experiment_tracking_service = None


def get_experiment_tracking_service(
    config: Optional[ExperimentConfig] = None
) -> ExperimentTrackingService:
    """Get singleton instance of ExperimentTrackingService"""
    global _experiment_tracking_service
    if _experiment_tracking_service is None:
        _experiment_tracking_service = ExperimentTrackingService(config)
    return _experiment_tracking_service
