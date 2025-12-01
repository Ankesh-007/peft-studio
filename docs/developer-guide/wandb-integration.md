# Weights & Biases Integration

## Overview

The Weights & Biases (WandB) integration provides comprehensive experiment tracking, automatic metric logging, and hyperparameter tracking for PEFT Studio training runs. This integration enables users to:

- Track all training experiments in a centralized dashboard
- Automatically log metrics in real-time
- Compare multiple training runs
- Track hyperparameters and configurations
- Store model artifacts and checkpoints
- Generate shareable experiment reports

## Features

### 1. Automatic Metric Logging

All training metrics are automatically logged to WandB without manual intervention:

- Training loss, learning rate, gradient norms
- Performance metrics (throughput, samples/sec)
- Resource utilization (GPU, CPU, RAM)
- Validation metrics (when available)
- Custom metrics from anomaly detection

### 2. Hyperparameter Tracking

Complete training configuration is tracked including:

- Model architecture parameters
- LoRA/PEFT settings (r, alpha, dropout, target modules)
- Training hyperparameters (learning rate, batch size, epochs)
- Optimization settings (optimizer, scheduler, weight decay)
- Precision and quantization settings

### 3. Experiment Comparison

Compare multiple training runs side-by-side:

- Generate comparison URLs for 2-5 runs
- View metrics across runs in unified dashboard
- Identify best performing configurations
- Track experiment evolution over time

### 4. Artifact Management

Store and version model artifacts:

- Checkpoint files
- Final trained models
- Configuration files
- Training metadata

## Installation

WandB is included in the requirements:

```bash
pip install wandb==0.16.0
```

## Configuration

### Basic Setup

```python
from services.wandb_integration_service import configure_wandb

# Configure WandB integration
wandb_service = configure_wandb(
    enabled=True,
    project_name="peft-studio-experiments",
    entity="your-team-name",  # Optional: WandB team/username
    api_key="your-api-key",   # Optional: Set via WANDB_API_KEY env var
    tags=["production", "llama-2"]  # Optional: Default tags
)
```

### Environment Variables

Set your WandB API key as an environment variable:

```bash
export WANDB_API_KEY=your_api_key_here
```

Or configure it programmatically:

```python
import os
os.environ['WANDB_API_KEY'] = 'your_api_key_here'
```

## Usage

### Integration with Training Orchestrator

The WandB service integrates seamlessly with the training orchestrator:

```python
from services.training_orchestration_service import (
    TrainingOrchestrator,
    TrainingConfig
)
from services.wandb_integration_example import (
    setup_wandb_for_training,
    finish_wandb_for_training
)

# Create orchestrator and config
orchestrator = TrainingOrchestrator()
config = TrainingConfig(
    job_id="experiment_001",
    model_name="meta-llama/Llama-2-7b-hf",
    dataset_path="./data/training.json",
    output_dir="./outputs/experiment_001",
    lora_r=16,
    lora_alpha=32,
    learning_rate=2e-4,
    batch_size=4,
    num_epochs=3
)

# Create job
job = orchestrator.create_job(config)

# Set up WandB tracking
setup_wandb_for_training(
    orchestrator=orchestrator,
    wandb_service=wandb_service,
    job_id=config.job_id,
    config=config
)

# Start training (metrics will be logged automatically)
orchestrator.start_training(config.job_id)

# ... training runs ...

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
```

### Manual Metric Logging

For custom metrics or manual logging:

```python
# Log custom metrics
wandb_service.log_metrics(
    job_id="experiment_001",
    metrics={
        'custom_metric': 0.95,
        'validation_accuracy': 0.87
    },
    step=100
)

# Update hyperparameters mid-training
wandb_service.log_hyperparameters(
    job_id="experiment_001",
    hyperparameters={
        'adjusted_learning_rate': 1e-4
    }
)
```

### Artifact Logging

Log model checkpoints and artifacts:

```python
from services.wandb_integration_example import log_checkpoint_to_wandb

log_checkpoint_to_wandb(
    wandb_service=wandb_service,
    job_id="experiment_001",
    checkpoint_path="./checkpoints/step_1000",
    step=1000,
    metrics={'loss': 0.5, 'learning_rate': 2e-4}
)
```

### Experiment Comparison

Generate comparison URLs for multiple runs:

```python
# Compare 3 training runs
comparison_url = wandb_service.compare_runs([
    "experiment_001",
    "experiment_002",
    "experiment_003"
])

print(f"Compare runs: {comparison_url}")
```

## API Endpoints

### Configure WandB

```http
POST /api/wandb/configure
Content-Type: application/json

{
  "enabled": true,
  "project_name": "peft-studio",
  "entity": "your-team",
  "api_key": "your-api-key",
  "tags": ["production"]
}
```

### Get WandB Status

```http
GET /api/wandb/status
```

Response:
```json
{
  "enabled": true,
  "available": true,
  "project_name": "peft-studio",
  "entity": "your-team",
  "active_runs": ["job_123", "job_456"]
}
```

### Start WandB Run

```http
POST /api/wandb/start-run
Content-Type: application/json

{
  "job_id": "experiment_001",
  "model_name": "meta-llama/Llama-2-7b-hf",
  "dataset_name": "training_data.json",
  "use_case": "chatbot",
  "run_name": "llama2-chatbot-v1",
  "config": {
    "learning_rate": 0.0002,
    "batch_size": 4,
    "lora_r": 16
  }
}
```

### Get Run URL

```http
GET /api/wandb/run-url/{job_id}
```

Response:
```json
{
  "job_id": "experiment_001",
  "run_url": "https://wandb.ai/your-team/peft-studio/runs/abc123"
}
```

### Finish WandB Run

```http
POST /api/wandb/finish-run/{job_id}?exit_code=0
Content-Type: application/json

{
  "final_loss": 0.5,
  "quality_score": 85.0,
  "total_steps": 1000
}
```

### Get Comparison URL

```http
GET /api/wandb/compare?job_ids=job1,job2,job3
```

Response:
```json
{
  "job_ids": ["job1", "job2", "job3"],
  "comparison_url": "https://wandb.ai/your-team/peft-studio/table?runSets=job1,job2,job3"
}
```

## Dashboard Features

### Metrics Visualization

The WandB dashboard automatically displays:

- **Loss Curves**: Training and validation loss over time
- **Learning Rate Schedule**: LR changes throughout training
- **Resource Utilization**: GPU/CPU/RAM usage graphs
- **Performance Metrics**: Throughput and samples/sec
- **Custom Metrics**: Any additional logged metrics

### Run Comparison

Compare multiple runs with:

- Side-by-side metric charts
- Configuration diff viewer
- Performance comparison tables
- Best run highlighting

### Hyperparameter Tracking

View all hyperparameters for each run:

- Model architecture settings
- Training configuration
- Optimization parameters
- Hardware specifications

## Best Practices

### 1. Consistent Naming

Use consistent naming conventions for runs:

```python
run_name = f"{model_name}_{use_case}_{timestamp}"
```

### 2. Meaningful Tags

Add descriptive tags to organize experiments:

```python
tags = [
    "production",
    "llama-2-7b",
    "chatbot",
    "lora-r16"
]
```

### 3. Regular Checkpointing

Log checkpoints at regular intervals:

```python
if step % 500 == 0:
    log_checkpoint_to_wandb(
        wandb_service, job_id, checkpoint_path, step, metrics
    )
```

### 4. Comprehensive Metadata

Include all relevant metadata in run summary:

```python
summary = {
    'final_loss': final_loss,
    'best_val_loss': best_val_loss,
    'total_steps': total_steps,
    'training_time_hours': training_time / 3600,
    'quality_score': quality_score,
    'hardware': gpu_name,
    'dataset_size': dataset_size
}
```

### 5. Error Handling

Always finish runs, even on errors:

```python
try:
    # Training code
    orchestrator.start_training(job_id)
except Exception as e:
    # Log error and finish run
    finish_wandb_for_training(
        wandb_service, job_id, {}, success=False
    )
    raise
```

## Troubleshooting

### WandB Not Available

If WandB is not installed:

```python
if not wandb_service.is_available:
    print("WandB not installed. Install with: pip install wandb")
```

### Authentication Issues

If authentication fails:

1. Check API key: `echo $WANDB_API_KEY`
2. Login manually: `wandb login`
3. Verify team/entity name

### Slow Logging

If logging is slow:

1. Reduce logging frequency
2. Batch metrics before logging
3. Use `commit=False` for intermediate logs

### Disk Space

WandB caches data locally. Clean up with:

```bash
wandb artifact cache cleanup
```

## Integration with Comparison Service

The WandB integration complements the built-in comparison service:

```python
from services.comparison_service import get_comparison_service

# Use both services together
comparison_service = get_comparison_service()

# Add runs to comparison cache
for job_id in ["job1", "job2", "job3"]:
    run_summary = create_run_summary(job_id)
    comparison_service.add_run(run_summary)

# Generate local comparison
local_comparison = comparison_service.compare_runs(
    ["job1", "job2", "job3"]
)

# Generate WandB comparison URL
wandb_url = wandb_service.compare_runs(
    ["job1", "job2", "job3"]
)

print(f"Local comparison: {local_comparison}")
print(f"WandB comparison: {wandb_url}")
```

## Requirements Validation

This implementation validates the following requirements:

- **Requirement 11.1**: Set up WandB integration for training runs ✓
- **Requirement 11.2**: Implement automatic metric logging and experiment comparison ✓

## Testing

Run the property-based tests:

```bash
cd backend
python -m pytest tests/test_wandb_integration.py -v
```

Tests cover:

- Automatic metric logging for all training runs
- Hyperparameter tracking completeness
- Run metadata completeness
- Comparison URL generation
- Run lifecycle management
- Disabled service behavior

## Future Enhancements

Potential improvements:

1. **Sweep Integration**: Hyperparameter search with WandB Sweeps
2. **Report Generation**: Automated experiment reports
3. **Model Registry**: Integration with WandB Model Registry
4. **Alerts**: Custom alerts for metric thresholds
5. **Team Collaboration**: Shared experiment workspaces

## References

- [WandB Documentation](https://docs.wandb.ai/)
- [WandB Python API](https://docs.wandb.ai/ref/python/)
- [WandB Best Practices](https://docs.wandb.ai/guides/track/best-practices)
