# Comet ML Connector

## Overview

The Comet ML connector integrates PEFT Studio with Comet ML's experiment tracking and model registry platform. It enables comprehensive experiment tracking, asset comparison, and model versioning.

## Features

- ✅ Experiment creation and management
- ✅ Real-time metric logging with batching
- ✅ Parameter and hyperparameter tracking
- ✅ Asset upload and management
- ✅ Experiment comparison
- ✅ Model registry integration
- ✅ Tag-based organization

## Configuration

### Required Credentials

- `api_key`: Your Comet ML API key (get from https://www.comet.com/api/my/settings/)
- `workspace` (optional): Workspace name (defaults to your default workspace)

### Getting API Key

1. Log in to Comet ML
2. Go to Settings → API Keys
3. Copy your API key
4. Add it to PEFT Studio's platform connections

## Usage

### Basic Setup

```python
from plugins.connectors.cometml_connector import CometMLConnector

# Initialize connector
connector = CometMLConnector()

# Connect with credentials
await connector.connect({
    "api_key": "your_api_key_here",
    "workspace": "your-workspace"  # optional
})
```

### Creating an Experiment

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
    experiment_tracker="cometml",
    project_name="my-project",
)

# Create experiment
job_id = await connector.submit_job(config)
print(f"Experiment created: {job_id}")
```

### Logging Metrics

```python
# Log metrics during training
await connector.log_metrics(
    job_id,
    {
        "loss": 1.5,
        "accuracy": 0.85,
        "learning_rate": 2e-4
    },
    step=100
)

# Metrics are batched automatically for efficiency
# Flush manually if needed
await connector._flush_metrics(job_id)
```

### Uploading Assets

```python
# Upload trained adapter
artifact_id = await connector.upload_artifact(
    path="/path/to/adapter_model.safetensors",
    metadata={
        "job_id": job_id,
        "name": "lora-adapter",
        "type": "model"
    }
)
```

### Comparing Experiments

```python
# Compare multiple experiments
comparison = await connector.compare_experiments([job_id1, job_id2, job_id3])

# Access comparison data
for exp in comparison["experiments"]:
    print(f"Experiment: {exp['name']}")
    print(f"Status: {exp['status']}")

# Compare metrics
for job_id, metrics in comparison["metrics"].items():
    print(f"Job {job_id} metrics: {metrics}")

# Compare parameters
for job_id, params in comparison["parameters"].items():
    print(f"Job {job_id} parameters: {params}")
```

### Model Registry Integration

```python
# Register model in Comet ML's model registry
model_id = await connector.register_model(
    job_id=job_id,
    model_name="my-lora-adapter",
    version="1.0.0"
)

print(f"Model registered with ID: {model_id}")
```

### Getting Experiment URL

```python
# Get dashboard URL for an experiment
url = connector.get_experiment_url(job_id)
print(f"View experiment at: {url}")
```

## API Endpoints Used

The connector uses the following Comet ML API v2 endpoints:

- `GET /workspaces` - List workspaces
- `POST /write/experiment/create` - Create experiment
- `POST /write/experiment/parameters` - Log parameters
- `POST /write/experiment/tags` - Add tags
- `POST /write/experiment/metrics` - Log metrics
- `POST /write/experiment/end` - End experiment
- `GET /experiment` - Get experiment details
- `GET /experiment/metrics` - Get metrics
- `GET /experiment/metrics/summary` - Get metrics summary
- `GET /experiment/assets` - List assets
- `GET /experiment/asset/download` - Download asset
- `POST /write/experiment/upload-asset` - Upload asset
- `POST /write/registry-model/create` - Register model

## Features

### Metric Batching

The connector automatically batches metrics to reduce API calls:

- Batch size: 100 metrics
- Batch interval: 5 seconds
- Automatic flush on disconnect

### Experiment Organization

Experiments are organized with:

- **Workspace**: Top-level organization
- **Project**: Group related experiments
- **Tags**: Algorithm, provider, model source
- **Parameters**: All hyperparameters logged automatically

### Asset Management

Upload and track various assets:

- Model checkpoints
- Adapter weights
- Training logs
- Configuration files
- Evaluation results

### Model Registry

Register models with:

- Version tracking
- Experiment linkage
- Metadata storage
- Easy deployment

## Error Handling

The connector handles common errors:

- **Invalid API key**: Raises `ValueError`
- **Connection failures**: Raises `ConnectionError`
- **Missing experiments**: Returns appropriate status
- **Upload failures**: Retries with exponential backoff

## Best Practices

1. **Use descriptive experiment names**: Include model and algorithm
2. **Tag experiments**: Use tags for easy filtering
3. **Batch metrics**: Let the connector handle batching automatically
4. **Register important models**: Use model registry for production models
5. **Compare experiments**: Use comparison features to identify best runs

## Limitations

- Comet ML doesn't provide compute resources (training only)
- Subscription-based pricing (not per-resource)
- API rate limits apply based on your plan
- Large asset uploads may take time

## Troubleshooting

### Connection Issues

```python
# Verify connection
is_valid = await connector.verify_connection()
if not is_valid:
    print("Connection failed - check API key")
```

### Missing Metrics

```python
# Manually flush metrics
await connector._flush_metrics(job_id)

# Check if experiment exists
status = await connector.get_job_status(job_id)
print(f"Experiment status: {status}")
```

### Asset Upload Failures

```python
try:
    artifact_id = await connector.upload_artifact(path, metadata)
except FileNotFoundError:
    print("File not found")
except RuntimeError as e:
    print(f"Upload failed: {e}")
```

## Integration with PEFT Studio

The connector integrates seamlessly with PEFT Studio:

1. **Automatic tracking**: Metrics logged automatically during training
2. **Dashboard integration**: View experiments in Comet ML dashboard
3. **Comparison tools**: Compare runs across different providers
4. **Model registry**: Register and version your adapters

## Example Workflow

```python
# 1. Connect
await connector.connect({"api_key": "your_key"})

# 2. Create experiment
job_id = await connector.submit_job(config)

# 3. Log metrics during training
for step in range(1000):
    await connector.log_metrics(job_id, {"loss": loss}, step=step)

# 4. Upload final adapter
await connector.upload_artifact(
    "/path/to/adapter.safetensors",
    {"job_id": job_id}
)

# 5. Register model
model_id = await connector.register_model(job_id, "my-adapter", "1.0.0")

# 6. Compare with other runs
comparison = await connector.compare_experiments([job_id, other_job_id])

# 7. Cleanup
await connector.disconnect()
```

## Resources

- [Comet ML Documentation](https://www.comet.com/docs/)
- [API Reference](https://www.comet.com/docs/v2/api-and-sdk/)
- [Python SDK](https://www.comet.com/docs/v2/api-and-sdk/python-sdk/)
- [Model Registry](https://www.comet.com/docs/v2/guides/model-management/)
