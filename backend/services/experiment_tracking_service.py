"""
Experiment Tracking Service

Unified service for experiment tracking across multiple platforms (W&B, Comet ML, Phoenix).
Provides automatic metric logging, hyperparameter tracking, artifact linking, and experiment comparison.

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import asyncio
from pathlib import Path

from connectors.connector_manager import get_connector_manager
from connectors.base import JobStatus

logger = logging.getLogger(__name__)


@dataclass
class ExperimentConfig:
    """Configuration for experiment tracking"""
    tracker_name: str  # wandb, cometml, phoenix
    project_name: str
    experiment_name: Optional[str] = None
    tags: List[str] = None
    notes: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class ExperimentMetadata:
    """Metadata for an experiment"""
    job_id: str
    model_name: str
    dataset_name: str
    use_case: str
    provider: str
    algorithm: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class ExperimentTrackingService:
    """
    Unified service for experiment tracking across multiple platforms.
    
    Features:
    - Automatic metric logging with batching
    - Hyperparameter tracking
    - Artifact linking and management
    - Multi-platform experiment comparison
    - Experiment search and filtering
    """
    
    def __init__(self):
        self.connector_manager = get_connector_manager()
        self.active_experiments: Dict[str, Dict] = {}  # job_id -> experiment info
        self._metric_buffer: Dict[str, List[Dict]] = {}  # job_id -> buffered metrics
        self._buffer_size = 10  # Buffer metrics before logging
        
        logger.info("ExperimentTrackingService initialized")
    
    async def start_experiment(
        self,
        job_id: str,
        config: ExperimentConfig,
        metadata: ExperimentMetadata,
        hyperparameters: Dict[str, Any]
    ) -> bool:
        """
        Start experiment tracking for a training job.
        
        Args:
            job_id: Unique job identifier
            config: Experiment tracking configuration
            metadata: Experiment metadata
            hyperparameters: Training hyperparameters
            
        Returns:
            True if experiment started successfully
        """
        try:
            # Get tracker connector
            connector = self.connector_manager.get(config.tracker_name)
            if not connector:
                logger.error(f"Tracker {config.tracker_name} not found")
                return False
            
            if not connector.supports_tracking:
                logger.error(f"Connector {config.tracker_name} doesn't support tracking")
                return False
            
            # Verify connection
            if not await connector.verify_connection():
                logger.error(f"Tracker {config.tracker_name} not connected")
                return False
            
            # Create training config for connector
            from connectors.base import TrainingConfig
            training_config = TrainingConfig(
                base_model=metadata.model_name,
                model_source="huggingface",  # Default
                algorithm=metadata.algorithm,
                rank=hyperparameters.get("rank", 8),
                alpha=hyperparameters.get("alpha", 16),
                dropout=hyperparameters.get("dropout", 0.1),
                target_modules=hyperparameters.get("target_modules", ["q_proj", "v_proj"]),
                quantization=hyperparameters.get("quantization"),
                learning_rate=hyperparameters.get("learning_rate", 2e-4),
                batch_size=hyperparameters.get("batch_size", 4),
                gradient_accumulation_steps=hyperparameters.get("gradient_accumulation_steps", 4),
                num_epochs=hyperparameters.get("num_epochs", 3),
                warmup_steps=hyperparameters.get("warmup_steps", 100),
                provider=metadata.provider,
                resource_id="",
                dataset_path=metadata.dataset_name,
                validation_split=hyperparameters.get("validation_split", 0.1),
                project_name=config.project_name,
                experiment_tracker=config.tracker_name,
                output_dir="",
                checkpoint_steps=hyperparameters.get("checkpoint_steps", 500),
            )
            
            # Submit job to tracker (creates experiment/run)
            tracker_job_id = await connector.submit_job(training_config)
            
            # Store experiment info
            self.active_experiments[job_id] = {
                "tracker_name": config.tracker_name,
                "tracker_job_id": tracker_job_id,
                "config": config,
                "metadata": metadata,
                "hyperparameters": hyperparameters,
                "connector": connector,
                "started_at": datetime.now().isoformat(),
                "status": "running",
            }
            
            # Initialize metric buffer
            self._metric_buffer[job_id] = []
            
            logger.info(f"Started experiment tracking for job {job_id} on {config.tracker_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start experiment tracking for job {job_id}: {e}")
            return False
    
    async def log_metrics(
        self,
        job_id: str,
        metrics: Dict[str, Any],
        step: Optional[int] = None,
        commit: bool = True
    ) -> bool:
        """
        Log metrics for an experiment with automatic batching.
        
        Args:
            job_id: Job identifier
            metrics: Dictionary of metric name -> value
            step: Training step number
            commit: Whether to commit immediately or buffer
            
        Returns:
            True if logged successfully
        """
        if job_id not in self.active_experiments:
            logger.warning(f"No active experiment for job {job_id}")
            return False
        
        try:
            exp_info = self.active_experiments[job_id]
            connector = exp_info["connector"]
            tracker_job_id = exp_info["tracker_job_id"]
            
            # Add timestamp
            metrics_with_timestamp = {
                **metrics,
                "_timestamp": datetime.now().isoformat(),
            }
            
            if commit:
                # Log immediately
                await connector.log_metrics(tracker_job_id, metrics_with_timestamp, step)
            else:
                # Buffer metrics
                self._metric_buffer[job_id].append({
                    "metrics": metrics_with_timestamp,
                    "step": step,
                })
                
                # Flush buffer if full
                if len(self._metric_buffer[job_id]) >= self._buffer_size:
                    await self._flush_metrics(job_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log metrics for job {job_id}: {e}")
            return False
    
    async def _flush_metrics(self, job_id: str):
        """Flush buffered metrics to tracker."""
        if job_id not in self._metric_buffer:
            return
        
        buffer = self._metric_buffer[job_id]
        if not buffer:
            return
        
        exp_info = self.active_experiments.get(job_id)
        if not exp_info:
            return
        
        connector = exp_info["connector"]
        tracker_job_id = exp_info["tracker_job_id"]
        
        try:
            # Log all buffered metrics
            for entry in buffer:
                await connector.log_metrics(
                    tracker_job_id,
                    entry["metrics"],
                    entry["step"]
                )
            
            # Clear buffer
            buffer.clear()
            
        except Exception as e:
            logger.error(f"Failed to flush metrics for job {job_id}: {e}")
    
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
        
        try:
            exp_info = self.active_experiments[job_id]
            
            # Update stored hyperparameters
            exp_info["hyperparameters"].update(hyperparameters)
            
            # Log to tracker if connector supports it
            connector = exp_info["connector"]
            if hasattr(connector, "log_hyperparameters"):
                tracker_job_id = exp_info["tracker_job_id"]
                await connector.log_hyperparameters(tracker_job_id, hyperparameters)
            
            logger.debug(f"Logged hyperparameters for job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log hyperparameters for job {job_id}: {e}")
            return False
    
    async def link_artifact(
        self,
        job_id: str,
        artifact_path: str,
        artifact_type: str = "model",
        artifact_name: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Link an artifact (model checkpoint, dataset, etc.) to an experiment.
        
        Args:
            job_id: Job identifier
            artifact_path: Path to the artifact file/directory
            artifact_type: Type of artifact (model, dataset, etc.)
            artifact_name: Artifact name (defaults to filename)
            metadata: Additional metadata for the artifact
            
        Returns:
            True if linked successfully
        """
        if job_id not in self.active_experiments:
            logger.warning(f"No active experiment for job {job_id}")
            return False
        
        try:
            # Verify artifact exists
            path = Path(artifact_path)
            if not path.exists():
                logger.error(f"Artifact not found: {artifact_path}")
                return False
            
            exp_info = self.active_experiments[job_id]
            connector = exp_info["connector"]
            tracker_job_id = exp_info["tracker_job_id"]
            
            # Prepare metadata
            artifact_metadata = {
                "job_id": tracker_job_id,
                "type": artifact_type,
                "name": artifact_name or path.name,
                "linked_at": datetime.now().isoformat(),
                **(metadata or {})
            }
            
            # Upload artifact to tracker
            artifact_id = await connector.upload_artifact(
                str(artifact_path),
                artifact_metadata
            )
            
            # Store artifact reference
            if "artifacts" not in exp_info:
                exp_info["artifacts"] = []
            
            exp_info["artifacts"].append({
                "id": artifact_id,
                "path": str(artifact_path),
                "type": artifact_type,
                "name": artifact_name or path.name,
                "linked_at": datetime.now().isoformat(),
            })
            
            logger.info(f"Linked artifact {artifact_name or path.name} to job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to link artifact for job {job_id}: {e}")
            return False
    
    async def finish_experiment(
        self,
        job_id: str,
        status: str = "completed",
        summary: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Finish experiment tracking for a job.
        
        Args:
            job_id: Job identifier
            status: Final status (completed, failed, cancelled)
            summary: Final summary metrics
            
        Returns:
            True if finished successfully
        """
        if job_id not in self.active_experiments:
            logger.warning(f"No active experiment for job {job_id}")
            return False
        
        try:
            # Flush any remaining metrics
            await self._flush_metrics(job_id)
            
            exp_info = self.active_experiments[job_id]
            connector = exp_info["connector"]
            tracker_job_id = exp_info["tracker_job_id"]
            
            # Cancel job on tracker (marks as complete)
            await connector.cancel_job(tracker_job_id)
            
            # Update status
            exp_info["status"] = status
            exp_info["finished_at"] = datetime.now().isoformat()
            if summary:
                exp_info["summary"] = summary
            
            # Clean up
            if job_id in self._metric_buffer:
                del self._metric_buffer[job_id]
            
            logger.info(f"Finished experiment tracking for job {job_id} with status {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to finish experiment for job {job_id}: {e}")
            return False
    
    async def compare_experiments(
        self,
        job_ids: List[str],
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compare multiple experiments across different trackers.
        
        Args:
            job_ids: List of job identifiers to compare
            metrics: Optional list of specific metrics to compare
            
        Returns:
            Dictionary with comparison data
        """
        comparison_data = {
            "experiments": [],
            "metrics": {},
            "hyperparameters": {},
            "artifacts": {},
            "summary": {},
        }
        
        for job_id in job_ids:
            if job_id not in self.active_experiments:
                logger.warning(f"Experiment {job_id} not found")
                continue
            
            try:
                exp_info = self.active_experiments[job_id]
                connector = exp_info["connector"]
                tracker_job_id = exp_info["tracker_job_id"]
                
                # Add experiment info
                comparison_data["experiments"].append({
                    "job_id": job_id,
                    "tracker": exp_info["tracker_name"],
                    "project": exp_info["config"].project_name,
                    "name": exp_info["config"].experiment_name,
                    "status": exp_info["status"],
                    "started_at": exp_info["started_at"],
                    "metadata": exp_info["metadata"].to_dict(),
                })
                
                # Add hyperparameters
                comparison_data["hyperparameters"][job_id] = exp_info["hyperparameters"]
                
                # Add artifacts
                comparison_data["artifacts"][job_id] = exp_info.get("artifacts", [])
                
                # Fetch metrics from tracker if connector supports comparison
                if hasattr(connector, "compare_experiments"):
                    tracker_comparison = await connector.compare_experiments([tracker_job_id])
                    if tracker_job_id in tracker_comparison.get("metrics", {}):
                        comparison_data["metrics"][job_id] = tracker_comparison["metrics"][tracker_job_id]
                
                # Add summary if available
                if "summary" in exp_info:
                    comparison_data["summary"][job_id] = exp_info["summary"]
                
            except Exception as e:
                logger.error(f"Failed to get comparison data for job {job_id}: {e}")
                continue
        
        # Calculate comparison statistics
        comparison_data["statistics"] = self._calculate_comparison_stats(comparison_data)
        
        return comparison_data
    
    def _calculate_comparison_stats(self, comparison_data: Dict) -> Dict:
        """Calculate statistics for experiment comparison."""
        stats = {
            "total_experiments": len(comparison_data["experiments"]),
            "trackers_used": list(set(exp["tracker"] for exp in comparison_data["experiments"])),
            "status_counts": {},
        }
        
        # Count by status
        for exp in comparison_data["experiments"]:
            status = exp["status"]
            stats["status_counts"][status] = stats["status_counts"].get(status, 0) + 1
        
        # Find best performing experiment (if metrics available)
        if comparison_data["metrics"]:
            # Look for common metrics like loss, accuracy
            for metric_name in ["loss", "eval_loss", "accuracy", "eval_accuracy"]:
                metric_values = {}
                for job_id, metrics in comparison_data["metrics"].items():
                    if metric_name in metrics:
                        metric_values[job_id] = metrics[metric_name]
                
                if metric_values:
                    # For loss, lower is better; for accuracy, higher is better
                    if "loss" in metric_name:
                        best_job_id = min(metric_values, key=metric_values.get)
                    else:
                        best_job_id = max(metric_values, key=metric_values.get)
                    
                    stats[f"best_{metric_name}"] = {
                        "job_id": best_job_id,
                        "value": metric_values[best_job_id],
                    }
        
        return stats
    
    async def search_experiments(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
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
        results = []
        
        for job_id, exp_info in self.active_experiments.items():
            # Apply filters
            if filters:
                match = True
                
                # Filter by tracker
                if "tracker" in filters and exp_info["tracker_name"] != filters["tracker"]:
                    match = False
                
                # Filter by status
                if "status" in filters and exp_info["status"] != filters["status"]:
                    match = False
                
                # Filter by project
                if "project" in filters and exp_info["config"].project_name != filters["project"]:
                    match = False
                
                # Filter by tags
                if "tags" in filters:
                    required_tags = set(filters["tags"])
                    exp_tags = set(exp_info["config"].tags)
                    if not required_tags.issubset(exp_tags):
                        match = False
                
                # Filter by date range
                if "start_date" in filters:
                    if exp_info["started_at"] < filters["start_date"]:
                        match = False
                
                if "end_date" in filters:
                    if exp_info["started_at"] > filters["end_date"]:
                        match = False
                
                # Filter by metadata
                if "metadata" in filters:
                    for key, value in filters["metadata"].items():
                        if not hasattr(exp_info["metadata"], key):
                            match = False
                            break
                        if getattr(exp_info["metadata"], key) != value:
                            match = False
                            break
                
                if not match:
                    continue
            
            # Add to results
            results.append({
                "job_id": job_id,
                "tracker": exp_info["tracker_name"],
                "project": exp_info["config"].project_name,
                "name": exp_info["config"].experiment_name,
                "status": exp_info["status"],
                "started_at": exp_info["started_at"],
                "metadata": exp_info["metadata"].to_dict(),
                "hyperparameters": exp_info["hyperparameters"],
                "tags": exp_info["config"].tags,
            })
        
        # Sort results
        if sort_by:
            reverse = sort_by.startswith("-")
            sort_field = sort_by.lstrip("-")
            results.sort(key=lambda x: x.get(sort_field, ""), reverse=reverse)
        
        # Limit results
        return results[:limit]
    
    def get_experiment_url(self, job_id: str) -> Optional[str]:
        """
        Get the tracker dashboard URL for an experiment.
        
        Args:
            job_id: Job identifier
            
        Returns:
            URL string or None if not available
        """
        if job_id not in self.active_experiments:
            return None
        
        exp_info = self.active_experiments[job_id]
        connector = exp_info["connector"]
        tracker_job_id = exp_info["tracker_job_id"]
        
        # Try to get URL from connector
        if hasattr(connector, "get_run_url"):
            return connector.get_run_url(tracker_job_id)
        elif hasattr(connector, "get_experiment_url"):
            return connector.get_experiment_url(tracker_job_id)
        elif hasattr(connector, "get_trace_url"):
            return connector.get_trace_url(tracker_job_id)
        
        return None
    
    def get_active_experiments(self) -> List[str]:
        """Get list of active experiment job IDs."""
        return [
            job_id for job_id, exp_info in self.active_experiments.items()
            if exp_info["status"] == "running"
        ]
    
    def get_experiment_info(self, job_id: str) -> Optional[Dict]:
        """Get detailed information about an experiment."""
        if job_id not in self.active_experiments:
            return None
        
        exp_info = self.active_experiments[job_id]
        
        return {
            "job_id": job_id,
            "tracker": exp_info["tracker_name"],
            "tracker_job_id": exp_info["tracker_job_id"],
            "project": exp_info["config"].project_name,
            "name": exp_info["config"].experiment_name,
            "status": exp_info["status"],
            "started_at": exp_info["started_at"],
            "finished_at": exp_info.get("finished_at"),
            "metadata": exp_info["metadata"].to_dict(),
            "hyperparameters": exp_info["hyperparameters"],
            "tags": exp_info["config"].tags,
            "artifacts": exp_info.get("artifacts", []),
            "summary": exp_info.get("summary", {}),
            "url": self.get_experiment_url(job_id),
        }


# Singleton instance
_experiment_tracking_service = None


def get_experiment_tracking_service() -> ExperimentTrackingService:
    """Get singleton instance of ExperimentTrackingService."""
    global _experiment_tracking_service
    if _experiment_tracking_service is None:
        _experiment_tracking_service = ExperimentTrackingService()
    return _experiment_tracking_service
