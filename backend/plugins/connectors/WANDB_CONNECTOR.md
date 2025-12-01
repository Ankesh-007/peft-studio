# Weights & Biases Connector

## Overview

The Weights & Biases (W&B) connector integrates with W&B's experiment tracking platform to provide comprehensive tracking of training runs, metrics, hyperparameters, and artifacts.

## Features

- **Project and Run Creation**: Automatically create W&B projects and runs for training jobs
- **Metric Logging with Batching**: Efficiently log metrics with automatic batching to reduce API calls
- **Artifact Tracking**: Upload and download model artifacts, checkpoints, and datasets
- **Experiment Comparison**: Compare multiple runs and generate comparison URLs
- **Real-time Synchronization**: Metrics are synchronized within 30 seconds of generation

## Configuration

### Required Credentials

- `api_key`: Your W&B API key (get it from https://wandb.ai/authorize)
- `entity` (optional): Your W&B username or team name

### Example Configuration

```python
credentials = {
    "api_key": "your_wandb_api_key_here",
    "entity": "your_username_or_team"  # Optional
}

connector = WandBConnector()
await connector.connect(credentials)
```

## Usage

### Creating a Run

```python
from connectors.base import TrainingConfig

config = TrainingConfig(
    base_model="meta-llama/Llama-2-7b-hf",
    model_source="huggingface",
    algorithm="lora",
    rank=16,
    alpha=32,
    dropout=0.1,
    target_modules=["q_proj", "v_proj"],
    dataset_path="/path/to/dataset.json",
    experiment_tracker="wandb",
    project_name="my-peft-project",
)

# Create a run
job_id = await connector.submit_job(config)
print(f"Created run: {job_id}")
```

### Logging Metrics

```python
# Log metrics during training
await connector.log_metrics(
    job_id=job_id,
    metrics={
        "loss": 1.5,
        "accuracy": 0.85,
        "learning_rate": 2e-4
    },
    step=100
)

# Metrics are automatically batched and sent efficiently
```

### Getting Run Status

```python
from connectors.base import JobStatus

status = await connector.get_job_status(job_id)

if status == JobStatus.RUNNING:
    print("Run is still in progress")
elif status == JobStatus.COMPLETED:
    print("Run completed successfully")
```

### Uploading Artifacts

```python
# Upload a trained adapter
artifact_id = await connector.upload_artifact(
    path="/path/to/adapter_model.safetensors",
    metadata={
        "job_id": job_id,
        "name": "llama2-lora-adapter",
        "type": "model",
        "description": "LoRA adapter for Llama 2 7B"
    }
)
```

### Comparing Experiments

```python
# Compare multiple runs
comparison_data = await connector.compare_experiments(
    job_ids=["job_1", "job_2", "job_3"]
)

# Get comparison URL
for run in comparison_data["runs"]:
    print(f"Run: {run['name']}, Status: {run['state']}")
```

### Getting Run URL

```python
# Get the W&B dashboard URL for a run
url = connector.get_run_url(job_id)
print(f"View run at: {url}")
```

## Metric Batching

The connector implements intelligent metric batching to optimize API usage:

- **Batch Size**: Up to 100 metrics per batch
- **Batch Interval**: Metrics are sent every 5 seconds
- **Automatic Flushing**: Batches are automatically flushed when full or on disconnect
- **No Data Loss**: All metrics are guaranteed to be sent, even on disconnect

### Synchronization Guarantee

**Property**: All metrics are synchronized to W&B within 30 seconds of generation.

This is verified by property-based tests in `test_experiment_tracker_synchronization.py`.

## API Endpoints

The connector uses the following W&B API endpoints:

- `GET /viewer` - Verify authentication
- `POST /runs` - Create new runs
- `POST /runs/{run_id}/history` - Log metrics
- `GET /runs/{run_id}` - Get run status
- `PATCH /runs/{run_id}` - Update run state
- `GET /runs/{run_id}/artifacts` - List artifacts
- `POST /runs/{run_id}/artifacts` - Upload artifacts

## Error Handling

### Connection Errors

```python
try:
    await connector.connect(credentials)
except ValueError as e:
    print(f"Invalid credentials: {e}")
except ConnectionError as e:
    print(f"Failed to connect: {e}")
```

### Metric Logging Errors

If metric logging fails (e.g., network error), metrics are automatically re-queued and retried on the next flush.

### Artifact Upload Errors

```python
try:
    artifact_id = await connector.upload_artifact(path, metadata)
except FileNotFoundError:
    print("Artifact file not found")
except RuntimeError as e:
    print(f"Upload failed: {e}")
```

## Best Practices

1. **Use Descriptive Project Names**: Choose clear, descriptive names for your projects
2. **Tag Your Runs**: Use tags to organize runs by model, dataset, or experiment type
3. **Log Regularly**: Log metrics at consistent intervals for better visualization
4. **Flush Before Critical Operations**: Call `_flush_metrics()` before important operations
5. **Always Disconnect**: Call `disconnect()` to ensure all metrics are flushed

## Integration with Training

### Example: Full Training Loop

```python
# Connect to W&B
connector = WandBConnector()
await connector.connect({"api_key": "your_api_key"})

# Create run
config = TrainingConfig(...)
job_id = await connector.submit_job(config)

# Training loop
for epoch in range(num_epochs):
    for step, batch in enumerate(dataloader):
        # Train step
        loss = train_step(batch)
        
        # Log metrics
        await connector.log_metrics(
            job_id=job_id,
            metrics={"loss": loss, "epoch": epoch},
            step=step
        )
    
    # Checkpoint
    save_checkpoint(f"checkpoint_epoch_{epoch}.pt")
    await connector.upload_artifact(
        path=f"checkpoint_epoch_{epoch}.pt",
        metadata={"job_id": job_id, "epoch": epoch}
    )

# Complete run
await connector.cancel_job(job_id)  # Mark as finished
await connector.disconnect()
```

## Limitations

1. **No Compute Resources**: W&B is a tracking platform, not a compute provider
2. **Subscription-Based Pricing**: W&B uses subscription pricing, not per-resource pricing
3. **API Rate Limits**: Be mindful of W&B's API rate limits (batching helps with this)
4. **Internet Required**: W&B requires internet connectivity (use offline mode for local-only)

## Testing

The connector includes comprehensive tests:

- **Unit Tests**: `test_wandb_connector.py` - Tests basic functionality
- **Property Tests**: `test_experiment_tracker_synchronization.py` - Tests synchronization guarantees

Run tests:

```bash
# Unit tests
pytest backend/tests/test_wandb_connector.py -v

# Property tests
pytest backend/tests/test_experiment_tracker_synchronization.py -v
```

## Troubleshooting

### "Invalid API key" Error

- Verify your API key at https://wandb.ai/authorize
- Ensure the key is correctly copied (no extra spaces)

### Metrics Not Appearing

- Check that metrics are being flushed (call `_flush_metrics()`)
- Verify the run is still active (not cancelled or completed)
- Check W&B dashboard for any errors

### Slow Synchronization

- Increase batch size for more efficient uploads
- Reduce batch interval for faster synchronization
- Check network connectivity

## References

- [W&B Documentation](https://docs.wandb.ai/)
- [W&B Python API](https://docs.wandb.ai/ref/python/)
- [W&B Best Practices](https://docs.wandb.ai/guides/track/best-practices)
