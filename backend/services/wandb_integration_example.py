"""
Example integration of WandB with Training Orchestration Service.
Shows how to automatically log metrics and track experiments.
"""

from services.training_orchestration_service import (
    TrainingOrchestrator,
    TrainingConfig,
    TrainingMetrics
)
from services.wandb_integration_service import (
    WandBIntegrationService,
    WandBConfig,
    ExperimentMetadata,
    configure_wandb
)
import logging

logger = logging.getLogger(__name__)


def setup_wandb_for_training(
    orchestrator: TrainingOrchestrator,
    wandb_service: WandBIntegrationService,
    job_id: str,
    config: TrainingConfig
) -> None:
    """
    Set up WandB integration for a training job.
    
    Args:
        orchestrator: Training orchestrator instance
        wandb_service: WandB service instance
        job_id: Job identifier
        config: Training configuration
    """
    if not wandb_service.is_enabled():
        logger.info("WandB integration disabled, skipping setup")
        return
    
    # Extract metadata
    metadata = ExperimentMetadata(
        job_id=job_id,
        model_name=config.model_name,
        dataset_name=config.dataset_path.split('/')[-1],  # Extract filename
        use_case=config.peft_method,
        run_name=f"{config.model_name}_{job_id[:8]}"
    )
    
    # Prepare hyperparameters for WandB
    hyperparameters = {
        # Model config
        'model_name': config.model_name,
        'peft_method': config.peft_method,
        
        # LoRA config
        'lora_r': config.lora_r,
        'lora_alpha': config.lora_alpha,
        'lora_dropout': config.lora_dropout,
        'target_modules': config.target_modules,
        
        # Training hyperparameters
        'learning_rate': config.learning_rate,
        'batch_size': config.batch_size,
        'gradient_accumulation_steps': config.gradient_accumulation_steps,
        'num_epochs': config.num_epochs,
        'max_steps': config.max_steps,
        'warmup_steps': config.warmup_steps,
        
        # Optimization
        'optimizer': config.optimizer,
        'scheduler': config.scheduler,
        'weight_decay': config.weight_decay,
        'max_grad_norm': config.max_grad_norm,
        
        # Precision
        'precision': config.precision,
        'quantization': config.quantization,
        
        # Checkpointing
        'save_steps': config.save_steps,
        'eval_steps': config.eval_steps
    }
    
    # Start WandB run
    success = wandb_service.start_run(
        job_id=job_id,
        metadata=metadata,
        config=hyperparameters
    )
    
    if success:
        logger.info(f"WandB tracking started for job {job_id}")
        
        # Register callback to log metrics automatically
        def metrics_callback(metrics: TrainingMetrics):
            """Callback to log metrics to WandB"""
            wandb_metrics = {
                # Training metrics
                'train/loss': metrics.loss,
                'train/learning_rate': metrics.learning_rate,
                'train/grad_norm': metrics.grad_norm,
                'train/epoch': metrics.epoch,
                
                # Performance metrics
                'performance/throughput': metrics.throughput,
                'performance/samples_per_second': metrics.samples_per_second,
                
                # Resource metrics
                'resources/cpu_utilization': metrics.cpu_utilization,
                'resources/ram_used_gb': metrics.ram_used / (1024**3),  # Convert to GB
                
                # Timing
                'timing/elapsed_time': metrics.elapsed_time,
                'timing/estimated_time_remaining': metrics.estimated_time_remaining
            }
            
            # Add GPU metrics if available
            if metrics.gpu_utilization:
                for i, util in enumerate(metrics.gpu_utilization):
                    wandb_metrics[f'resources/gpu_{i}_utilization'] = util
            
            if metrics.gpu_memory_used:
                for i, mem in enumerate(metrics.gpu_memory_used):
                    wandb_metrics[f'resources/gpu_{i}_memory_gb'] = mem / (1024**3)
            
            if metrics.gpu_temperature:
                for i, temp in enumerate(metrics.gpu_temperature):
                    wandb_metrics[f'resources/gpu_{i}_temperature'] = temp
            
            # Add validation metrics if available
            if metrics.val_loss is not None:
                wandb_metrics['val/loss'] = metrics.val_loss
            
            if metrics.val_perplexity is not None:
                wandb_metrics['val/perplexity'] = metrics.val_perplexity
            
            # Log to WandB
            wandb_service.log_metrics(
                job_id=job_id,
                metrics=wandb_metrics,
                step=metrics.step
            )
        
        # Register the callback with orchestrator
        orchestrator.register_metrics_callback(job_id, metrics_callback)
        
        # Get and log WandB URL
        run_url = wandb_service.get_run_url(job_id)
        if run_url:
            logger.info(f"WandB dashboard: {run_url}")
    else:
        logger.warning(f"Failed to start WandB tracking for job {job_id}")


def finish_wandb_for_training(
    wandb_service: WandBIntegrationService,
    job_id: str,
    final_metrics: dict,
    success: bool = True
) -> None:
    """
    Finish WandB tracking for a training job.
    
    Args:
        wandb_service: WandB service instance
        job_id: Job identifier
        final_metrics: Final summary metrics
        success: Whether training completed successfully
    """
    if not wandb_service.is_enabled():
        return
    
    # Prepare summary
    summary = {
        'final_loss': final_metrics.get('final_loss'),
        'best_val_loss': final_metrics.get('best_val_loss'),
        'total_steps': final_metrics.get('total_steps'),
        'epochs_completed': final_metrics.get('epochs_completed'),
        'training_time_seconds': final_metrics.get('training_time_seconds'),
        'quality_score': final_metrics.get('quality_score'),
        'success': success
    }
    
    # Finish the run
    exit_code = 0 if success else 1
    wandb_service.finish_run(
        job_id=job_id,
        exit_code=exit_code,
        summary=summary
    )
    
    logger.info(f"WandB tracking finished for job {job_id}")


def log_checkpoint_to_wandb(
    wandb_service: WandBIntegrationService,
    job_id: str,
    checkpoint_path: str,
    step: int,
    metrics: dict
) -> None:
    """
    Log a checkpoint as an artifact to WandB.
    
    Args:
        wandb_service: WandB service instance
        job_id: Job identifier
        checkpoint_path: Path to checkpoint directory
        step: Training step number
        metrics: Checkpoint metrics
    """
    if not wandb_service.is_enabled():
        return
    
    metadata = {
        'step': step,
        'loss': metrics.get('loss'),
        'learning_rate': metrics.get('learning_rate'),
        'epoch': metrics.get('epoch')
    }
    
    wandb_service.log_artifact(
        job_id=job_id,
        artifact_path=checkpoint_path,
        artifact_type='model',
        name=f"checkpoint_step_{step}",
        metadata=metadata
    )
    
    logger.info(f"Logged checkpoint at step {step} to WandB for job {job_id}")


# Example usage
if __name__ == "__main__":
    # Configure WandB
    wandb_service = configure_wandb(
        enabled=True,
        project_name="peft-studio-experiments",
        entity=None,  # Set to your WandB username/team
        api_key=None,  # Set via environment variable WANDB_API_KEY
        tags=["example", "test"]
    )
    
    # Create orchestrator
    orchestrator = TrainingOrchestrator()
    
    # Create training config
    config = TrainingConfig(
        job_id="test_job_123",
        model_name="meta-llama/Llama-2-7b-hf",
        dataset_path="./data/training_data.json",
        output_dir="./outputs/test_job_123",
        lora_r=16,
        lora_alpha=32,
        learning_rate=2e-4,
        batch_size=4,
        num_epochs=3
    )
    
    # Create job
    job = orchestrator.create_job(config)
    
    # Set up WandB integration
    setup_wandb_for_training(
        orchestrator=orchestrator,
        wandb_service=wandb_service,
        job_id=config.job_id,
        config=config
    )
    
    # Start training
    orchestrator.start_training(config.job_id)
    
    print(f"Training started with WandB tracking")
    print(f"Dashboard: {wandb_service.get_run_url(config.job_id)}")
    
    # Wait for training to complete (in real usage)
    # ...
    
    # Finish WandB tracking
    final_metrics = {
        'final_loss': 0.5,
        'total_steps': 1000,
        'epochs_completed': 3,
        'training_time_seconds': 3600,
        'quality_score': 85.0
    }
    
    finish_wandb_for_training(
        wandb_service=wandb_service,
        job_id=config.job_id,
        final_metrics=final_metrics,
        success=True
    )
