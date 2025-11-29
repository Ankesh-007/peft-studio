"""
Weights & Biases Integration Service
Provides experiment tracking, automatic metric logging, and hyperparameter tracking.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging
import os

logger = logging.getLogger(__name__)

# Try to import wandb, but make it optional
try:
    import wandb
    WANDB_AVAILABLE = True
except ImportError:
    WANDB_AVAILABLE = False
    logger.warning("wandb not installed. WandB integration will be disabled.")


@dataclass
class WandBConfig:
    """Configuration for Weights & Biases integration"""
    enabled: bool = False
    project_name: str = "peft-studio"
    entity: Optional[str] = None  # WandB team/username
    api_key: Optional[str] = None
    tags: List[str] = None
    notes: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class ExperimentMetadata:
    """Metadata for an experiment run"""
    job_id: str
    model_name: str
    dataset_name: str
    use_case: str
    run_name: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


class WandBIntegrationService:
    """
    Service for integrating with Weights & Biases for experiment tracking.
    
    Features:
    - Automatic metric logging
    - Hyperparameter tracking
    - Experiment comparison
    - Artifact management
    """
    
    def __init__(self, config: Optional[WandBConfig] = None):
        self.config = config or WandBConfig()
        self.active_runs: Dict[str, Any] = {}  # job_id -> wandb.Run
        self.is_available = WANDB_AVAILABLE
        
        if not self.is_available:
            logger.warning("WandB not available. Integration disabled.")
        elif self.config.enabled:
            self._initialize_wandb()
        
        logger.info(f"WandBIntegrationService initialized (enabled={self.config.enabled}, available={self.is_available})")
    
    def _initialize_wandb(self) -> None:
        """Initialize WandB with API key if provided"""
        if not self.is_available:
            return
        
        if self.config.api_key:
            os.environ['WANDB_API_KEY'] = self.config.api_key
            logger.info("WandB API key configured")
        
        # Set WandB to silent mode to reduce console output
        os.environ['WANDB_SILENT'] = 'true'
    
    def start_run(
        self,
        job_id: str,
        metadata: ExperimentMetadata,
        config: Dict[str, Any],
        resume: bool = False
    ) -> bool:
        """
        Start a new WandB run for experiment tracking.
        
        Args:
            job_id: Unique job identifier
            metadata: Experiment metadata
            config: Training configuration (hyperparameters)
            resume: Whether to resume an existing run
            
        Returns:
            True if run started successfully, False otherwise
        """
        if not self.is_available or not self.config.enabled:
            logger.debug(f"WandB not available or disabled, skipping run start for {job_id}")
            return False
        
        try:
            # Generate run name
            run_name = metadata.run_name or f"{metadata.model_name}_{metadata.use_case}_{job_id[:8]}"
            
            # Prepare tags
            tags = self.config.tags + [
                metadata.use_case,
                metadata.model_name,
                f"job_{job_id[:8]}"
            ]
            
            # Initialize WandB run
            run = wandb.init(
                project=self.config.project_name,
                entity=self.config.entity,
                name=run_name,
                config=config,
                tags=tags,
                notes=self.config.notes,
                resume="allow" if resume else None,
                id=job_id if resume else None
            )
            
            # Store metadata as summary
            run.summary.update({
                'job_id': job_id,
                'model_name': metadata.model_name,
                'dataset_name': metadata.dataset_name,
                'use_case': metadata.use_case
            })
            
            self.active_runs[job_id] = run
            logger.info(f"Started WandB run for job {job_id}: {run_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start WandB run for job {job_id}: {e}")
            return False
    
    def log_metrics(
        self,
        job_id: str,
        metrics: Dict[str, Any],
        step: Optional[int] = None,
        commit: bool = True
    ) -> bool:
        """
        Log metrics to WandB for a specific job.
        
        Args:
            job_id: Job identifier
            metrics: Dictionary of metric name -> value
            step: Training step number
            commit: Whether to commit the metrics immediately
            
        Returns:
            True if logged successfully, False otherwise
        """
        if not self.is_available or not self.config.enabled:
            return False
        
        if job_id not in self.active_runs:
            logger.warning(f"No active WandB run for job {job_id}")
            return False
        
        try:
            run = self.active_runs[job_id]
            run.log(metrics, step=step, commit=commit)
            return True
            
        except Exception as e:
            logger.error(f"Failed to log metrics for job {job_id}: {e}")
            return False
    
    def log_hyperparameters(
        self,
        job_id: str,
        hyperparameters: Dict[str, Any]
    ) -> bool:
        """
        Log or update hyperparameters for a run.
        
        Args:
            job_id: Job identifier
            hyperparameters: Dictionary of hyperparameter name -> value
            
        Returns:
            True if logged successfully, False otherwise
        """
        if not self.is_available or not self.config.enabled:
            return False
        
        if job_id not in self.active_runs:
            logger.warning(f"No active WandB run for job {job_id}")
            return False
        
        try:
            run = self.active_runs[job_id]
            run.config.update(hyperparameters, allow_val_change=True)
            logger.debug(f"Updated hyperparameters for job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log hyperparameters for job {job_id}: {e}")
            return False
    
    def log_artifact(
        self,
        job_id: str,
        artifact_path: str,
        artifact_type: str = "model",
        name: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Log an artifact (model checkpoint, dataset, etc.) to WandB.
        
        Args:
            job_id: Job identifier
            artifact_path: Path to the artifact file/directory
            artifact_type: Type of artifact (model, dataset, etc.)
            name: Artifact name (defaults to job_id)
            metadata: Additional metadata for the artifact
            
        Returns:
            True if logged successfully, False otherwise
        """
        if not self.is_available or not self.config.enabled:
            return False
        
        if job_id not in self.active_runs:
            logger.warning(f"No active WandB run for job {job_id}")
            return False
        
        try:
            run = self.active_runs[job_id]
            
            artifact_name = name or f"{job_id}_checkpoint"
            artifact = wandb.Artifact(
                name=artifact_name,
                type=artifact_type,
                metadata=metadata or {}
            )
            
            artifact.add_dir(artifact_path) if os.path.isdir(artifact_path) else artifact.add_file(artifact_path)
            
            run.log_artifact(artifact)
            logger.info(f"Logged artifact {artifact_name} for job {job_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log artifact for job {job_id}: {e}")
            return False
    
    def finish_run(
        self,
        job_id: str,
        exit_code: int = 0,
        summary: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Finish a WandB run.
        
        Args:
            job_id: Job identifier
            exit_code: Exit code (0 for success, non-zero for failure)
            summary: Final summary metrics
            
        Returns:
            True if finished successfully, False otherwise
        """
        if not self.is_available or not self.config.enabled:
            return False
        
        if job_id not in self.active_runs:
            logger.warning(f"No active WandB run for job {job_id}")
            return False
        
        try:
            run = self.active_runs[job_id]
            
            # Update summary if provided
            if summary:
                run.summary.update(summary)
            
            # Finish the run
            run.finish(exit_code=exit_code)
            
            # Remove from active runs
            del self.active_runs[job_id]
            
            logger.info(f"Finished WandB run for job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to finish WandB run for job {job_id}: {e}")
            return False
    
    def get_run_url(self, job_id: str) -> Optional[str]:
        """
        Get the WandB dashboard URL for a run.
        
        Args:
            job_id: Job identifier
            
        Returns:
            URL string or None if not available
        """
        if not self.is_available or not self.config.enabled:
            return None
        
        if job_id not in self.active_runs:
            return None
        
        try:
            run = self.active_runs[job_id]
            return run.get_url()
        except Exception as e:
            logger.error(f"Failed to get run URL for job {job_id}: {e}")
            return None
    
    def compare_runs(
        self,
        job_ids: List[str],
        metrics: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Generate a comparison URL for multiple runs.
        
        Args:
            job_ids: List of job identifiers to compare
            metrics: Optional list of specific metrics to compare
            
        Returns:
            Comparison URL or None if not available
        """
        if not self.is_available or not self.config.enabled:
            return None
        
        try:
            # Build comparison URL
            # Format: https://wandb.ai/{entity}/{project}/reports
            if self.config.entity:
                base_url = f"https://wandb.ai/{self.config.entity}/{self.config.project_name}/table"
            else:
                base_url = f"https://wandb.ai/{self.config.project_name}/table"
            
            # Add run IDs as query parameters
            run_ids = ",".join(job_ids)
            comparison_url = f"{base_url}?runSets={run_ids}"
            
            logger.info(f"Generated comparison URL for {len(job_ids)} runs")
            return comparison_url
            
        except Exception as e:
            logger.error(f"Failed to generate comparison URL: {e}")
            return None
    
    def is_enabled(self) -> bool:
        """Check if WandB integration is enabled and available"""
        return self.is_available and self.config.enabled
    
    def get_active_runs(self) -> List[str]:
        """Get list of active run job IDs"""
        return list(self.active_runs.keys())


# Singleton instance
_wandb_service_instance = None


def get_wandb_service(config: Optional[WandBConfig] = None) -> WandBIntegrationService:
    """Get singleton instance of WandBIntegrationService"""
    global _wandb_service_instance
    if _wandb_service_instance is None:
        _wandb_service_instance = WandBIntegrationService(config)
    return _wandb_service_instance


def configure_wandb(
    enabled: bool = True,
    project_name: str = "peft-studio",
    entity: Optional[str] = None,
    api_key: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> WandBIntegrationService:
    """
    Configure and get WandB service instance.
    
    Args:
        enabled: Whether to enable WandB integration
        project_name: WandB project name
        entity: WandB entity (team/username)
        api_key: WandB API key
        tags: Default tags for all runs
        
    Returns:
        Configured WandBIntegrationService instance
    """
    config = WandBConfig(
        enabled=enabled,
        project_name=project_name,
        entity=entity,
        api_key=api_key,
        tags=tags or []
    )
    
    global _wandb_service_instance
    _wandb_service_instance = WandBIntegrationService(config)
    
    return _wandb_service_instance
