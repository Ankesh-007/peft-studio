# HoneyHive Connector

## Overview

The HoneyHive connector integrates with HoneyHive's LLM evaluation platform to provide:
- Evaluation dataset management
- Model battle comparisons (A/B testing)
- Result visualization and reporting
- Quality metrics tracking

## Features

- ✅ Evaluation dataset creation and management
- ✅ Model battle comparisons
- ✅ Result visualization
- ✅ Multiple evaluation metrics
- ✅ Real-time progress tracking
- ✅ Dashboard integration

## Configuration

### Required Credentials

- `api_key`: HoneyHive API key (required)
- `project_id`: Project identifier (optional, will use default if not provided)

### Getting API Key

1. Sign up at [HoneyHive](https://honeyhive.ai)
2. Navigate to Settings → API Keys
3. Create a new API key
4. Copy the key for use in PEFT Studio

## Usage

### Connecting to HoneyHive

```python
from connectors.honeyhive_connector import HoneyHiveConnector

connector = HoneyHiveConnector()
await connector.connect({
    "api_key": "your-api-key-here",
    "project_id": "optional-project-id"
})
```

### Creating an Evaluation Dataset

```python
# Create a dataset for evaluation
dataset_data = [
    {
        "input": "What is the capital of France?",
        "expected_output": "Paris",
        "context": "Geography question"
    },
    {
        "input": "Explain quantum computing",
        "expected_output": "Quantum computing uses quantum mechanics...",
        "context": "Technical explanation"
    }
]

dataset_id = await connector.create_dataset(
    name="my_evaluation_dataset",
    data=dataset_data,
    description="Dataset for model evaluation"
)
```

### Managing Datasets

```python
# List all datasets
datasets = await connector.list_datasets()

# Get a specific dataset
dataset = await connector.get_dataset(dataset_id)

# Update a dataset
await connector.update_dataset(
    dataset_id,
    data=updated_data,
    metadata={"version": "2.0"}
)

# Delete a dataset
await connector.delete_dataset(dataset_id)
```

### Creating a Model Battle

```python
# Create a battle to compare two models
battle_id = await connector.create_model_battle(
    name="LoRA vs QLoRA Comparison",
    model_a_id="lora_model_v1",
    model_b_id="qlora_model_v1",
    dataset_id=dataset_id,
    metrics=["accuracy", "bleu", "rouge", "latency"]
)
```

### Running a Model Battle

```python
# Get model outputs for comparison
model_a_outputs = ["Paris", "Quantum computing uses..."]
model_b_outputs = ["Paris", "Quantum computing leverages..."]

# Run the battle
results = await connector.run_model_battle(
    battle_id,
    model_a_outputs,
    model_b_outputs
)

# Results include:
# - Metric scores for each model
# - Winner determination
# - Statistical significance
# - Detailed comparisons
```

### Getting Battle Results

```python
# Get complete battle results
results = await connector.get_battle_results(battle_id)

# Results structure:
{
    "model_a": {
        "accuracy": 0.95,
        "bleu": 0.82,
        "rouge": 0.88,
        "latency": 120
    },
    "model_b": {
        "accuracy": 0.93,
        "bleu": 0.85,
        "rouge": 0.86,
        "latency": 95
    },
    "winner": "model_b",
    "statistical_significance": {
        "accuracy": 0.12,
        "bleu": 0.03,
        "rouge": 0.08,
        "latency": 0.001
    }
}
```

### Getting Visualizations

```python
# Get visualization data for charts
viz_data = await connector.get_battle_visualization(
    battle_id,
    viz_type="comparison"  # or "metrics", "distribution"
)

# Visualization data includes:
# - Chart data in JSON format
# - Axis labels and titles
# - Color schemes
# - Recommended chart types
```

### Creating an Evaluation Job

```python
# Create evaluation job from training config
job_id = await connector.submit_job(training_config)

# Stream evaluation progress
async for log in connector.stream_logs(job_id):
    print(log)

# Get job status
status = await connector.get_job_status(job_id)

# Download results
results = await connector.fetch_artifact(job_id)
```

## Supported Metrics

The HoneyHive connector supports the following evaluation metrics:

- **accuracy**: Classification accuracy
- **precision**: Precision score
- **recall**: Recall score
- **f1_score**: F1 score
- **bleu**: BLEU score for text generation
- **rouge**: ROUGE score for summarization
- **meteor**: METEOR score for translation
- **bertscore**: BERTScore for semantic similarity
- **perplexity**: Language model perplexity
- **latency**: Response time in milliseconds
- **cost**: Inference cost estimation
- **human_preference**: Human evaluation scores

## Dashboard Integration

### Viewing Evaluations

```python
# Get dashboard URL for an evaluation
url = connector.get_dashboard_url(job_id)
# Opens: https://app.honeyhive.ai/projects/{project_id}/evaluations/{eval_id}
```

### Viewing Battles

```python
# Get dashboard URL for a battle
url = connector.get_battle_url(battle_id)
# Opens: https://app.honeyhive.ai/projects/{project_id}/battles/{battle_id}
```

## Best Practices

### Dataset Management

1. **Organize datasets by task type**: Create separate datasets for different evaluation tasks
2. **Version your datasets**: Use metadata to track dataset versions
3. **Include diverse examples**: Ensure datasets cover edge cases and common scenarios
4. **Document expected outputs**: Provide clear reference outputs for comparison

### Model Battles

1. **Use consistent datasets**: Compare models on the same evaluation data
2. **Select relevant metrics**: Choose metrics that align with your use case
3. **Run multiple battles**: Test models on different datasets for comprehensive comparison
4. **Consider statistical significance**: Don't rely on small differences without significance testing

### Result Interpretation

1. **Look beyond single metrics**: Consider multiple metrics for holistic evaluation
2. **Check for trade-offs**: A model might excel in one metric but lag in others
3. **Consider latency and cost**: Balance quality with practical constraints
4. **Use visualizations**: Charts help identify patterns and outliers

## Error Handling

The connector provides detailed error messages for common issues:

```python
try:
    await connector.create_dataset(name="test", data=[])
except RuntimeError as e:
    print(f"Dataset creation failed: {e}")

try:
    await connector.run_model_battle(battle_id, [], [])
except ValueError as e:
    print(f"Invalid battle configuration: {e}")
```

## Limitations

- HoneyHive doesn't provide compute resources (training/inference)
- Pricing is subscription-based, not per-resource
- API rate limits apply based on subscription tier
- Large datasets may take time to upload

## API Reference

### Dataset Methods

- `create_dataset(name, data, description, metadata)`: Create new dataset
- `get_dataset(dataset_id)`: Retrieve dataset
- `update_dataset(dataset_id, data, metadata)`: Update dataset
- `delete_dataset(dataset_id)`: Delete dataset
- `list_datasets()`: List all datasets

### Battle Methods

- `create_model_battle(name, model_a_id, model_b_id, dataset_id, metrics)`: Create battle
- `run_model_battle(battle_id, model_a_outputs, model_b_outputs)`: Execute battle
- `get_battle_results(battle_id)`: Get battle results
- `get_battle_visualization(battle_id, viz_type)`: Get visualization data

### Evaluation Methods

- `submit_job(config)`: Create evaluation job
- `get_job_status(job_id)`: Get job status
- `cancel_job(job_id)`: Cancel job
- `stream_logs(job_id)`: Stream progress logs
- `fetch_artifact(job_id)`: Download results
- `upload_artifact(path, metadata)`: Upload results

## Support

For issues or questions:
- HoneyHive Documentation: https://docs.honeyhive.ai/
- HoneyHive Support: support@honeyhive.ai
- PEFT Studio Issues: GitHub Issues

## Version History

- **1.0.0** (2024): Initial release
  - Dataset management
  - Model battle comparisons
  - Result visualization
  - Dashboard integration
