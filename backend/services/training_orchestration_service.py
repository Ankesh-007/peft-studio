"""
Training Orchestration Service for managing training lifecycle.
Handles job queue, state machine, checkpointing, pause/resume functionality,
multi-provider job submission, and artifact management.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
import json
import logging
import threading
import queue
from pathlib import Path
import shutil
import hashlib
import asyncio

# Lazy import torch to reduce startup memory usage
_torch = None

def _get_torch():
    """Lazy load torch module"""
    global _torch
    if _torch is None:
        import torch as _torch_module
        _torch = _torch_module
    return _torch

from backend.connectors.base import PlatformConnector, JobStatus as ConnectorJobStatus
from backend.connectors.connector_manager import get_connector_manager

from backend.services.quality_analysis_service import (
    analyze_training_quality,
    TrainingResult,
    QualityAnalysis,
    generate_quality_report
)
from backend.services.notification_service import (
    check_progress_milestone,
    create_error_notification,
    NotificationManager,
    ProgressUpdate,
    NotificationEvent
)

logger = logging.getLogger(__name__)


class TrainingState(str, Enum):
    """Training job states"""
    CREATED = "created"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass
class TrainingMetrics:
    """Real-time training metrics"""
    step: int
    epoch: int
    loss: float
    learning_rate: float
    grad_norm: float = 0.0
    
    # Performance
    throughput: float = 0.0  # steps/sec
    samples_per_second: float = 0.0
    
    # Resources
    gpu_utilization: List[float] = field(default_factory=list)
    gpu_memory_used: List[float] = field(default_factory=list)
    gpu_temperature: List[float] = field(default_factory=list)
    cpu_utilization: float = 0.0
    ram_used: float = 0.0
    
    # Validation (optional)
    val_loss: Optional[float] = None
    val_perplexity: Optional[float] = None
    
    # Timing
    timestamp: datetime = field(default_factory=datetime.now)
    elapsed_time: float = 0.0
    estimated_time_remaining: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class CheckpointData:
    """Complete checkpoint data for pause/resume"""
    # Training state
    step: int
    epoch: int
    loss: float
    learning_rate: float
    
    # Model state
    model_state_dict: Dict[str, Any]
    optimizer_state_dict: Dict[str, Any]
    scheduler_state_dict: Optional[Dict[str, Any]] = None
    
    # Metrics history
    metrics_history: List[Dict] = field(default_factory=list)
    
    # Configuration
    config: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    checkpoint_reason: str = "manual"  # manual, scheduled, anomaly
    
    def save(self, path: Path) -> None:
        """Save checkpoint to disk"""
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save model and optimizer states separately (they're large)
        _get_torch().save({
            'model_state_dict': self.model_state_dict,
            'optimizer_state_dict': self.optimizer_state_dict,
            'scheduler_state_dict': self.scheduler_state_dict,
        }, path / "model_checkpoint.pt")
        
        # Save metadata and metrics
        metadata = {
            'step': self.step,
            'epoch': self.epoch,
            'loss': self.loss,
            'learning_rate': self.learning_rate,
            'metrics_history': self.metrics_history,
            'config': self.config,
            'timestamp': self.timestamp.isoformat(),
            'checkpoint_reason': self.checkpoint_reason
        }
        
        with open(path / "checkpoint_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Checkpoint saved to {path}")
    
    @classmethod
    def load(cls, path: Path) -> 'CheckpointData':
        """Load checkpoint from disk"""
        # Load model and optimizer states
        checkpoint = _get_torch().load(path / "model_checkpoint.pt")
        
        # Load metadata
        with open(path / "checkpoint_metadata.json", 'r') as f:
            metadata = json.load(f)
        
        return cls(
            step=metadata['step'],
            epoch=metadata['epoch'],
            loss=metadata['loss'],
            learning_rate=metadata['learning_rate'],
            model_state_dict=checkpoint['model_state_dict'],
            optimizer_state_dict=checkpoint['optimizer_state_dict'],
            scheduler_state_dict=checkpoint.get('scheduler_state_dict'),
            metrics_history=metadata.get('metrics_history', []),
            config=metadata.get('config', {}),
            timestamp=datetime.fromisoformat(metadata['timestamp']),
            checkpoint_reason=metadata.get('checkpoint_reason', 'manual')
        )


@dataclass
class TrainingConfig:
    """Complete training configuration"""
    job_id: str
    model_name: str
    dataset_path: str
    output_dir: str
    
    # PEFT settings
    peft_method: str = "lora"
    lora_r: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.1
    target_modules: List[str] = field(default_factory=list)
    
    # Training hyperparameters
    learning_rate: float = 2e-4
    batch_size: int = 4
    gradient_accumulation_steps: int = 4
    num_epochs: int = 3
    max_steps: Optional[int] = None
    warmup_steps: int = 100
    
    # Optimization
    optimizer: str = "adamw"
    scheduler: str = "linear"
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0
    
    # Precision
    precision: str = "fp16"
    quantization: Optional[str] = None
    
    # Checkpointing
    save_steps: int = 500
    save_total_limit: int = 3
    
    # Validation
    eval_steps: int = 500
    eval_strategy: str = "steps"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class ArtifactInfo:
    """Information about a training artifact"""
    artifact_id: str
    job_id: str
    path: Path
    size_bytes: int
    hash_sha256: str
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'artifact_id': self.artifact_id,
            'job_id': self.job_id,
            'path': str(self.path),
            'size_bytes': self.size_bytes,
            'hash_sha256': self.hash_sha256,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class TrainingJob:
    """Training job with state and metadata"""
    job_id: str
    config: TrainingConfig
    state: TrainingState = TrainingState.CREATED
    current_metrics: Optional[TrainingMetrics] = None
    metrics_history: List[TrainingMetrics] = field(default_factory=list)
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    checkpoint_path: Optional[Path] = None
    quality_analysis: Optional[QualityAnalysis] = None
    notifications: List[NotificationEvent] = field(default_factory=list)
    
    # Multi-provider support
    provider: Optional[str] = None  # Provider name (runpod, lambda, vastai, local)
    provider_job_id: Optional[str] = None  # Job ID from the provider
    artifact_info: Optional[ArtifactInfo] = None  # Downloaded artifact information
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            'job_id': self.job_id,
            'config': self.config.to_dict(),
            'state': self.state.value,
            'current_metrics': self.current_metrics.to_dict() if self.current_metrics else None,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'paused_at': self.paused_at.isoformat() if self.paused_at else None,
            'checkpoint_path': str(self.checkpoint_path) if self.checkpoint_path else None,
            'provider': self.provider,
            'provider_job_id': self.provider_job_id,
            'artifact_info': self.artifact_info.to_dict() if self.artifact_info else None
        }


class TrainingOrchestrator:
    """
    Orchestrates training jobs with state management, checkpointing, pause/resume,
    multi-provider job submission, and artifact management.
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
    """
    
    def __init__(
        self,
        checkpoint_base_dir: str = "./checkpoints",
        artifacts_base_dir: str = "./artifacts"
    ):
        self.jobs: Dict[str, TrainingJob] = {}
        self.job_queue: queue.Queue = queue.Queue()
        self.checkpoint_base_dir = Path(checkpoint_base_dir)
        self.checkpoint_base_dir.mkdir(parents=True, exist_ok=True)
        
        # Artifacts storage
        self.artifacts_base_dir = Path(artifacts_base_dir)
        self.artifacts_base_dir.mkdir(parents=True, exist_ok=True)
        
        # Connector manager for multi-provider support
        self.connector_manager = get_connector_manager()
        
        # Training control
        self._training_threads: Dict[str, threading.Thread] = {}
        self._stop_flags: Dict[str, threading.Event] = {}
        self._pause_flags: Dict[str, threading.Event] = {}
        
        # Callbacks for metrics updates
        self._metrics_callbacks: Dict[str, List[Callable]] = {}
        
        # Notification managers per job
        self._notification_managers: Dict[str, NotificationManager] = {}
        
        # Callbacks for notifications
        self._notification_callbacks: Dict[str, List[Callable]] = {}
        
        logger.info("TrainingOrchestrator initialized with multi-provider support")
    
    def create_job(self, config: TrainingConfig) -> TrainingJob:
        """
        Create a new training job.
        
        Args:
            config: Training configuration
            
        Returns:
            Created TrainingJob
        """
        job = TrainingJob(
            job_id=config.job_id,
            config=config,
            state=TrainingState.CREATED
        )
        
        self.jobs[config.job_id] = job
        logger.info(f"Created training job: {config.job_id}")
        
        return job
    
    async def submit_job_to_provider(self, job_id: str, provider: str) -> str:
        """
        Submit a training job to a specific provider.
        
        Args:
            job_id: Job identifier
            provider: Provider name (runpod, lambda, vastai, local)
            
        Returns:
            Provider job ID
            
        Raises:
            ValueError: If job or provider not found
            RuntimeError: If submission fails
            
        Requirements: 5.1, 5.2
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job not found: {job_id}")
        
        job = self.jobs[job_id]
        
        # Get connector for provider
        connector = self.connector_manager.get(provider)
        if not connector:
            raise ValueError(f"Provider not found: {provider}")
        
        if not connector.supports_training:
            raise ValueError(f"Provider {provider} does not support training")
        
        # Convert our config to connector config
        from connectors.base import TrainingConfig as ConnectorConfig
        connector_config = ConnectorConfig(
            base_model=job.config.model_name,
            model_source="huggingface",  # Default
            algorithm=job.config.peft_method,
            rank=job.config.lora_r,
            alpha=job.config.lora_alpha,
            dropout=job.config.lora_dropout,
            target_modules=job.config.target_modules,
            quantization=job.config.quantization,
            learning_rate=job.config.learning_rate,
            batch_size=job.config.batch_size,
            gradient_accumulation_steps=job.config.gradient_accumulation_steps,
            num_epochs=job.config.num_epochs,
            warmup_steps=job.config.warmup_steps,
            provider=provider,
            dataset_path=job.config.dataset_path,
            output_dir=job.config.output_dir,
            project_name=job_id
        )
        
        # Submit job to provider
        try:
            provider_job_id = await connector.submit_job(connector_config)
            job.provider = provider
            job.provider_job_id = provider_job_id
            job.state = TrainingState.RUNNING
            job.started_at = datetime.now()
            
            logger.info(f"Submitted job {job_id} to {provider} as {provider_job_id}")
            
            # Start monitoring thread
            thread = threading.Thread(
                target=self._monitor_provider_job,
                args=(job_id,),
                daemon=True
            )
            self._training_threads[job_id] = thread
            thread.start()
            
            return provider_job_id
            
        except Exception as e:
            logger.error(f"Failed to submit job {job_id} to {provider}: {e}")
            job.state = TrainingState.FAILED
            job.error_message = f"Submission failed: {str(e)}"
            raise RuntimeError(f"Failed to submit job: {str(e)}")
    
    def start_training(self, job_id: str, provider: Optional[str] = None) -> None:
        """
        Start a training job (local or on a provider).
        
        Args:
            job_id: Job identifier
            provider: Optional provider name for cloud training
            
        Requirements: 5.1, 5.2
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job not found: {job_id}")
        
        job = self.jobs[job_id]
        
        if job.state not in [TrainingState.CREATED, TrainingState.PAUSED]:
            raise ValueError(f"Cannot start job in state: {job.state}")
        
        # If provider specified, submit to provider
        if provider and provider != "local":
            # Run async submission in thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.submit_job_to_provider(job_id, provider))
            finally:
                loop.close()
            return
        
        # Local training
        job.provider = "local"
        job.state = TrainingState.INITIALIZING
        if job.started_at is None:
            job.started_at = datetime.now()
        
        # Create control flags if they don't exist
        if job_id not in self._stop_flags:
            self._stop_flags[job_id] = threading.Event()
        if job_id not in self._pause_flags:
            self._pause_flags[job_id] = threading.Event()
        
        # Start training in a separate thread
        thread = threading.Thread(
            target=self._training_loop,
            args=(job_id,),
            daemon=True
        )
        self._training_threads[job_id] = thread
        thread.start()
        
        logger.info(f"Started local training job: {job_id}")
    
    def pause_training(self, job_id: str) -> CheckpointData:
        """
        Pause a running training job and save checkpoint.
        
        Args:
            job_id: Job identifier
            
        Returns:
            CheckpointData with saved state
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job not found: {job_id}")
        
        job = self.jobs[job_id]
        
        if job.state != TrainingState.RUNNING:
            raise ValueError(f"Cannot pause job in state: {job.state}")
        
        logger.info(f"Pausing training job: {job_id}")
        
        # Set pause flag
        self._pause_flags[job_id].set()
        
        # Wait for training loop to acknowledge pause (with timeout)
        import time
        timeout = 30  # seconds
        start_time = time.time()
        
        while job.state != TrainingState.PAUSED and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        if job.state != TrainingState.PAUSED:
            logger.warning(f"Pause timeout for job {job_id}")
            raise TimeoutError(f"Failed to pause job {job_id} within {timeout} seconds")
        
        job.paused_at = datetime.now()
        
        # Return the checkpoint data
        if job.checkpoint_path and job.checkpoint_path.exists():
            return CheckpointData.load(job.checkpoint_path)
        else:
            raise RuntimeError(f"Checkpoint not found for paused job {job_id}")
    
    def resume_training(self, job_id: str) -> None:
        """
        Resume a paused training job.
        
        Args:
            job_id: Job identifier
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job not found: {job_id}")
        
        job = self.jobs[job_id]
        
        if job.state != TrainingState.PAUSED:
            raise ValueError(f"Cannot resume job in state: {job.state}")
        
        logger.info(f"Resuming training job: {job_id}")
        
        # Clear pause flag if it exists
        if job_id in self._pause_flags:
            self._pause_flags[job_id].clear()
        
        # Remove old thread reference if it exists
        if job_id in self._training_threads:
            del self._training_threads[job_id]
        
        # Restart training (this will create new flags and thread)
        self.start_training(job_id)
    
    async def cancel_provider_job(self, job_id: str) -> bool:
        """
        Cancel a job running on a provider.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if cancellation successful
            
        Requirements: 5.4
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job not found: {job_id}")
        
        job = self.jobs[job_id]
        
        if not job.provider or job.provider == "local":
            raise ValueError(f"Job {job_id} is not running on a provider")
        
        if not job.provider_job_id:
            raise ValueError(f"Job {job_id} has no provider job ID")
        
        # Get connector
        connector = self.connector_manager.get(job.provider)
        if not connector:
            raise ValueError(f"Provider not found: {job.provider}")
        
        # Cancel job on provider
        try:
            success = await connector.cancel_job(job.provider_job_id)
            if success:
                logger.info(f"Cancelled job {job_id} on {job.provider}")
            return success
        except Exception as e:
            logger.error(f"Failed to cancel job {job_id} on {job.provider}: {e}")
            raise
    
    def stop_training(self, job_id: str) -> None:
        """
        Stop a training job permanently (local or provider).
        
        Args:
            job_id: Job identifier
            
        Requirements: 5.4
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job not found: {job_id}")
        
        job = self.jobs[job_id]
        
        if job.state not in [TrainingState.RUNNING, TrainingState.PAUSED, TrainingState.INITIALIZING]:
            raise ValueError(f"Cannot stop job in state: {job.state}")
        
        logger.info(f"Stopping training job: {job_id}")
        
        # If running on provider, cancel there
        if job.provider and job.provider != "local" and job.provider_job_id:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.cancel_provider_job(job_id))
            except Exception as e:
                logger.error(f"Error cancelling provider job: {e}")
            finally:
                loop.close()
        
        # Set stop flag if it exists (for local jobs)
        if job_id in self._stop_flags:
            self._stop_flags[job_id].set()
        
        # Wait for thread to finish
        if job_id in self._training_threads:
            self._training_threads[job_id].join(timeout=10)
        
        job.state = TrainingState.STOPPED
        job.completed_at = datetime.now()
        
        # Cleanup
        self._cleanup_job(job_id)
    
    def get_status(self, job_id: str) -> TrainingJob:
        """
        Get current status of a training job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            TrainingJob with current state
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job not found: {job_id}")
        
        return self.jobs[job_id]
    
    def get_metrics(self, job_id: str) -> Optional[TrainingMetrics]:
        """
        Get current metrics for a training job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Current TrainingMetrics or None
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job not found: {job_id}")
        
        return self.jobs[job_id].current_metrics
    
    def register_metrics_callback(self, job_id: str, callback: Callable[[TrainingMetrics], None]) -> None:
        """
        Register a callback for metrics updates.
        
        Args:
            job_id: Job identifier
            callback: Function to call with new metrics
        """
        if job_id not in self._metrics_callbacks:
            self._metrics_callbacks[job_id] = []
        
        self._metrics_callbacks[job_id].append(callback)
    
    def register_notification_callback(self, job_id: str, callback: Callable[[NotificationEvent], None]) -> None:
        """
        Register a callback for notification events.
        
        Args:
            job_id: Job identifier
            callback: Function to call with new notifications
        """
        if job_id not in self._notification_callbacks:
            self._notification_callbacks[job_id] = []
        
        self._notification_callbacks[job_id].append(callback)
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate SHA256 hash of a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Hex digest of SHA256 hash
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    async def download_artifact(self, job_id: str) -> ArtifactInfo:
        """
        Download training artifact from provider and store locally.
        
        Args:
            job_id: Job identifier
            
        Returns:
            ArtifactInfo with download details
            
        Raises:
            ValueError: If job not found or not on provider
            RuntimeError: If download fails
            
        Requirements: 5.5
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job not found: {job_id}")
        
        job = self.jobs[job_id]
        
        if not job.provider or job.provider == "local":
            raise ValueError(f"Job {job_id} is not running on a provider")
        
        if not job.provider_job_id:
            raise ValueError(f"Job {job_id} has no provider job ID")
        
        # Get connector
        connector = self.connector_manager.get(job.provider)
        if not connector:
            raise ValueError(f"Provider not found: {job.provider}")
        
        # Download artifact
        try:
            logger.info(f"Downloading artifact for job {job_id} from {job.provider}")
            artifact_data = await connector.fetch_artifact(job.provider_job_id)
            
            # Create artifact directory
            artifact_dir = self.artifacts_base_dir / job_id
            artifact_dir.mkdir(parents=True, exist_ok=True)
            
            # Save artifact
            artifact_path = artifact_dir / "adapter_model.safetensors"
            with open(artifact_path, 'wb') as f:
                f.write(artifact_data)
            
            # Calculate hash for integrity verification
            file_hash = self._calculate_file_hash(artifact_path)
            
            # Create artifact info
            artifact_info = ArtifactInfo(
                artifact_id=f"{job_id}_artifact",
                job_id=job_id,
                path=artifact_path,
                size_bytes=len(artifact_data),
                hash_sha256=file_hash,
                created_at=datetime.now(),
                metadata={
                    'provider': job.provider,
                    'provider_job_id': job.provider_job_id,
                    'model_name': job.config.model_name,
                    'peft_method': job.config.peft_method
                }
            )
            
            job.artifact_info = artifact_info
            
            logger.info(
                f"Downloaded artifact for job {job_id}: "
                f"{artifact_info.size_bytes} bytes, hash: {file_hash[:16]}..."
            )
            
            return artifact_info
            
        except Exception as e:
            logger.error(f"Failed to download artifact for job {job_id}: {e}")
            raise RuntimeError(f"Failed to download artifact: {str(e)}")
    
    def _send_notification(self, job_id: str, notification: NotificationEvent) -> None:
        """
        Send a notification for a job.
        
        Args:
            job_id: Job identifier
            notification: Notification to send
        """
        job = self.jobs[job_id]
        job.notifications.append(notification)
        
        # Call notification callbacks
        if job_id in self._notification_callbacks:
            for callback in self._notification_callbacks[job_id]:
                try:
                    callback(notification)
                except Exception as e:
                    logger.error(f"Error in notification callback: {e}")
        
        logger.info(f"Notification sent for job {job_id}: {notification.title}")
    
    def _monitor_provider_job(self, job_id: str) -> None:
        """
        Monitor a job running on a provider (runs in separate thread).
        
        Args:
            job_id: Job identifier
            
        Requirements: 5.3
        """
        job = self.jobs[job_id]
        
        if not job.provider or not job.provider_job_id:
            logger.error(f"Cannot monitor job {job_id}: missing provider info")
            return
        
        connector = self.connector_manager.get(job.provider)
        if not connector:
            logger.error(f"Cannot monitor job {job_id}: provider {job.provider} not found")
            return
        
        logger.info(f"Monitoring job {job_id} on {job.provider}")
        
        try:
            # Create event loop for async operations
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Stream logs
            async def stream_logs():
                try:
                    async for log_line in connector.stream_logs(job.provider_job_id):
                        logger.debug(f"[{job_id}] {log_line}")
                        # TODO: Parse logs for metrics
                except Exception as e:
                    logger.error(f"Error streaming logs for job {job_id}: {e}")
            
            # Monitor status
            async def monitor_status():
                while True:
                    try:
                        status = await connector.get_job_status(job.provider_job_id)
                        
                        if status == ConnectorJobStatus.COMPLETED:
                            job.state = TrainingState.COMPLETED
                            job.completed_at = datetime.now()
                            
                            # Download artifact
                            try:
                                artifact_info = await self.download_artifact(job_id)
                                logger.info(f"Artifact downloaded for job {job_id}")
                            except Exception as e:
                                logger.error(f"Failed to download artifact: {e}")
                            
                            # Send completion notification
                            from services.notification_service import NotificationEvent, NotificationType
                            completion_notification = NotificationEvent(
                                type=NotificationType.COMPLETION,
                                title="Training Complete! 🎉",
                                message=f"Your model training on {job.provider} has finished successfully.",
                                milestone=100,
                                sound=True,
                                urgency="normal"
                            )
                            self._send_notification(job_id, completion_notification)
                            
                            break
                            
                        elif status == ConnectorJobStatus.FAILED:
                            job.state = TrainingState.FAILED
                            job.error_message = "Training failed on provider"
                            job.completed_at = datetime.now()
                            
                            # Send error notification
                            error_notification = create_error_notification(
                                "Training failed on provider"
                            )
                            self._send_notification(job_id, error_notification)
                            
                            break
                            
                        elif status == ConnectorJobStatus.CANCELLED:
                            job.state = TrainingState.STOPPED
                            job.completed_at = datetime.now()
                            break
                        
                        # Still running, check again in 10 seconds
                        await asyncio.sleep(10)
                        
                    except Exception as e:
                        logger.error(f"Error checking status for job {job_id}: {e}")
                        await asyncio.sleep(10)
            
            # Run both tasks concurrently
            loop.run_until_complete(asyncio.gather(
                stream_logs(),
                monitor_status()
            ))
            
        except Exception as e:
            logger.error(f"Error monitoring job {job_id}: {e}")
            job.state = TrainingState.FAILED
            job.error_message = f"Monitoring error: {str(e)}"
            job.completed_at = datetime.now()
        
        finally:
            loop.close()
            self._cleanup_job(job_id)
    
    def _training_loop(self, job_id: str) -> None:
        """
        Main training loop for local training (runs in separate thread).
        
        Args:
            job_id: Job identifier
        """
        job = self.jobs[job_id]
        
        try:
            job.state = TrainingState.RUNNING
            
            # Initialize notification manager for this job
            if job_id not in self._notification_managers:
                self._notification_managers[job_id] = NotificationManager()
            notification_manager = self._notification_managers[job_id]
            
            # This is a simplified training loop
            # In a real implementation, this would integrate with Unsloth and transformers
            
            # Load checkpoint if resuming
            checkpoint = None
            if job.checkpoint_path and job.checkpoint_path.exists():
                checkpoint = CheckpointData.load(job.checkpoint_path)
                logger.info(f"Loaded checkpoint from {job.checkpoint_path}")
            
            # Initialize training state
            start_step = checkpoint.step if checkpoint else 0
            start_epoch = checkpoint.epoch if checkpoint else 0
            initial_loss = None
            loss_history = []
            
            # Simulate training loop
            config = job.config
            total_steps = config.max_steps if config.max_steps else (config.num_epochs * 1000)
            
            previous_step = start_step
            
            for step in range(start_step, total_steps):
                # Check for stop signal
                if self._stop_flags[job_id].is_set():
                    logger.info(f"Stop signal received for job {job_id}")
                    break
                
                # Check for pause signal
                if self._pause_flags[job_id].is_set():
                    logger.info(f"Pause signal received for job {job_id}")
                    self._save_checkpoint(job_id, step, step // 1000, 0.5, config.learning_rate, "pause")
                    job.state = TrainingState.PAUSED
                    return
                
                # Simulate training step
                epoch = step // 1000
                loss = 2.0 - (step / total_steps) * 1.5  # Simulated decreasing loss
                
                if initial_loss is None:
                    initial_loss = loss
                
                loss_history.append(loss)
                
                # Update metrics
                metrics = TrainingMetrics(
                    step=step,
                    epoch=epoch,
                    loss=loss,
                    learning_rate=config.learning_rate,
                    grad_norm=0.5,
                    throughput=10.0,
                    samples_per_second=40.0,
                    elapsed_time=step * 0.1,
                    estimated_time_remaining=(total_steps - step) * 0.1
                )
                
                job.current_metrics = metrics
                job.metrics_history.append(metrics)
                
                # Check for progress milestones and send notifications
                progress_update = ProgressUpdate(
                    current_step=step,
                    total_steps=total_steps,
                    previous_step=previous_step
                )
                
                notification = notification_manager.get_next_notification(progress_update)
                if notification:
                    self._send_notification(job_id, notification)
                
                previous_step = step
                
                # Call metrics callbacks
                if job_id in self._metrics_callbacks:
                    for callback in self._metrics_callbacks[job_id]:
                        try:
                            callback(metrics)
                        except Exception as e:
                            logger.error(f"Error in metrics callback: {e}")
                
                # Save checkpoint periodically
                if step > 0 and step % config.save_steps == 0:
                    self._save_checkpoint(job_id, step, epoch, loss, config.learning_rate, "scheduled")
                
                # Simulate step delay
                import time
                time.sleep(0.01)
            
            # Training completed - perform quality analysis
            job.state = TrainingState.COMPLETED
            job.completed_at = datetime.now()
            
            # Analyze training quality
            training_result = TrainingResult(
                final_loss=loss_history[-1] if loss_history else 0.5,
                initial_loss=initial_loss if initial_loss else 2.0,
                epochs_completed=config.num_epochs,
                total_steps=total_steps,
                best_val_loss=None,  # Would be calculated from validation
                convergence_achieved=loss_history[-1] < 0.5 if loss_history else False,
                gradient_norm_stable=True,
                loss_history=loss_history
            )
            
            quality_analysis = analyze_training_quality(training_result)
            job.quality_analysis = quality_analysis
            
            # Generate and log quality report
            quality_report = generate_quality_report(quality_analysis)
            logger.info(f"Quality Analysis for job {job_id}:\n{quality_report}")
            
            # Send completion notification with quality score
            from services.notification_service import NotificationEvent, NotificationType
            completion_notification = NotificationEvent(
                type=NotificationType.COMPLETION,
                title="Training Complete! 🎉",
                message=f"Your model training finished with a quality score of {quality_analysis.quality_score:.1f}/100. {quality_analysis.overall_assessment}",
                milestone=100,
                sound=True,
                urgency="normal"
            )
            self._send_notification(job_id, completion_notification)
            
            logger.info(f"Training completed for job {job_id}")
            
        except Exception as e:
            logger.error(f"Training failed for job {job_id}: {str(e)}")
            job.state = TrainingState.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()
            
            # Send error notification
            error_notification = create_error_notification(str(e))
            self._send_notification(job_id, error_notification)
        
        finally:
            self._cleanup_job(job_id)
    
    def _save_checkpoint(
        self,
        job_id: str,
        step: int,
        epoch: int,
        loss: float,
        learning_rate: float,
        reason: str = "scheduled"
    ) -> None:
        """
        Save a checkpoint for a training job.
        
        Args:
            job_id: Job identifier
            step: Current training step
            epoch: Current epoch
            loss: Current loss value
            learning_rate: Current learning rate
            reason: Reason for checkpoint (scheduled, pause, anomaly)
        """
        job = self.jobs[job_id]
        
        # Create checkpoint directory
        checkpoint_dir = self.checkpoint_base_dir / job_id / f"checkpoint-{step}"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # In a real implementation, we would save actual model and optimizer states
        # For now, we create dummy states
        checkpoint = CheckpointData(
            step=step,
            epoch=epoch,
            loss=loss,
            learning_rate=learning_rate,
            model_state_dict={},  # Would be actual model.state_dict()
            optimizer_state_dict={},  # Would be actual optimizer.state_dict()
            scheduler_state_dict=None,
            metrics_history=[m.to_dict() for m in job.metrics_history[-100:]],  # Last 100 metrics
            config=job.config.to_dict(),
            timestamp=datetime.now(),
            checkpoint_reason=reason
        )
        
        checkpoint.save(checkpoint_dir)
        job.checkpoint_path = checkpoint_dir
        
        logger.info(f"Saved checkpoint for job {job_id} at step {step} (reason: {reason})")
        
        # Cleanup old checkpoints
        self._cleanup_old_checkpoints(job_id, job.config.save_total_limit)
    
    def _cleanup_old_checkpoints(self, job_id: str, keep_latest: int) -> None:
        """
        Remove old checkpoints, keeping only the latest N.
        
        Args:
            job_id: Job identifier
            keep_latest: Number of checkpoints to keep
        """
        job_checkpoint_dir = self.checkpoint_base_dir / job_id
        
        if not job_checkpoint_dir.exists():
            return
        
        # Get all checkpoint directories
        checkpoints = sorted(
            [d for d in job_checkpoint_dir.iterdir() if d.is_dir() and d.name.startswith("checkpoint-")],
            key=lambda x: int(x.name.split("-")[1])
        )
        
        # Remove old checkpoints
        if len(checkpoints) > keep_latest:
            for checkpoint in checkpoints[:-keep_latest]:
                shutil.rmtree(checkpoint)
                logger.debug(f"Removed old checkpoint: {checkpoint}")
    
    def _cleanup_job(self, job_id: str) -> None:
        """
        Cleanup resources for a job.
        
        Args:
            job_id: Job identifier
        """
        # Remove from active threads
        if job_id in self._training_threads:
            del self._training_threads[job_id]
        
        # Remove control flags
        if job_id in self._stop_flags:
            del self._stop_flags[job_id]
        
        if job_id in self._pause_flags:
            del self._pause_flags[job_id]
        
        # Remove callbacks
        if job_id in self._metrics_callbacks:
            del self._metrics_callbacks[job_id]
        
        if job_id in self._notification_callbacks:
            del self._notification_callbacks[job_id]
        
        # Remove notification manager
        if job_id in self._notification_managers:
            del self._notification_managers[job_id]
        
        # Clear GPU memory
        if _get_torch().cuda.is_available():
            _get_torch().cuda.empty_cache()
        
        logger.debug(f"Cleaned up resources for job {job_id}")
    
    def list_jobs(self) -> List[TrainingJob]:
        """Get list of all training jobs"""
        return list(self.jobs.values())
    
    def delete_job(self, job_id: str) -> None:
        """
        Delete a job and its checkpoints.
        
        Args:
            job_id: Job identifier
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job not found: {job_id}")
        
        job = self.jobs[job_id]
        
        # Can only delete stopped, completed, or failed jobs
        if job.state in [TrainingState.RUNNING, TrainingState.INITIALIZING]:
            raise ValueError(f"Cannot delete job in state: {job.state}")
        
        # Delete checkpoints
        job_checkpoint_dir = self.checkpoint_base_dir / job_id
        if job_checkpoint_dir.exists():
            shutil.rmtree(job_checkpoint_dir)
        
        # Remove from jobs dict
        del self.jobs[job_id]
        
        logger.info(f"Deleted job: {job_id}")


# Singleton instance
_orchestrator_instance = None


def get_training_orchestrator() -> TrainingOrchestrator:
    """Get singleton instance of TrainingOrchestrator"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = TrainingOrchestrator()
    return _orchestrator_instance
