# Replicate Connector

## Overview

The Replicate connector integrates with Replicate's model deployment and inference platform. It provides:

- **Model Deployment**: Deploy models with version management
- **Inference API**: Run predictions on deployed models
- **Version Management**: Create and manage multiple model versions
- **Usage Tracking**: Monitor predictions and costs

## Features

### Model Deployment
- Create models on Replicate
- Deploy adapters as model versions
- Configure hardware (T4, A40)
- Set visibility (public/private)

### Inference
- Create predictions (inference requests)
- Wait for prediction completion
- Cancel running predictions
- Stream results

### Version Management
- Create multiple versions per model
- Track version history
- Switch between versions
- Delete old versions

## Configuration

### Required Credentials

```python
credentials = {
    "api_token": "r8_..."  # Replicate API token
}
```

### Getting API Token

1. Sign up at https://replicate.com
2. Go to Account Settings
3. Navigate to API Tokens
4. Create a new token
5. Copy the token (starts with `r8_`)

## Usage Examples

### Basic Connection

```python
from plugins.connectors.replicate_connector import ReplicateConnector

connector = ReplicateConnector()

# Connect
await connector.connect({
    "api_token": "r8_your_token_here"
})

# Verify connection
is_connected = await connector.verify_connection()
print(f"Connected: {is_connected}")
```

### Deploy a Model

```python
# Create a model
model_id = await connector.create_model(
    owner="your-username",
    name="my-llama-adapter",
    visibility="public",
    hardware="gpu-t4",
    description="Fine-tuned Llama model"
)

print(f"Model created: {model_id}")

# Create a version with adapter
version_id = await connector.create_model_version(
    model_id=model_id,
    version="v1",
    weights_url="https://example.com/adapter.safetensors",
    config={"base_model": "meta-llama/Llama-2-7b-hf"}
)

print(f"Version created: {version_id}")
```

### Deploy with Adapter

```python
# Deploy model with adapter files
model_id = await connector.deploy_model(
    model_name="my-adapter",
    base_model="meta-llama/Llama-2-7b-hf",
    adapter_path="./output/adapter",
    deployment_config={
        "owner": "your-username",
        "visibility": "public",
        "hardware": "gpu-t4",
        "description": "My fine-tuned model"
    }
)

print(f"Model deployed: {model_id}")
```

### Run Inference

```python
# Simple inference
result = await connector.inference(
    model_id="your-username/my-adapter",
    prompt="What is the capital of France?",
    generation_config={
        "max_tokens": 256,
        "temperature": 0.7,
        "top_p": 0.9
    }
)

print(f"Generated text: {result['text']}")
print(f"Latency: {result['latency_ms']:.2f}ms")
```

### Create and Monitor Prediction

```python
# Create prediction
prediction_id = await connector.create_prediction(
    model_id="your-username/my-adapter",
    input_data={
        "prompt": "Tell me a story",
        "max_length": 500,
        "temperature": 0.8
    }
)

print(f"Prediction created: {prediction_id}")

# Wait for completion
prediction = await connector.wait_for_prediction(
    prediction_id=prediction_id,
    timeout=300
)

print(f"Status: {prediction['status']}")
print(f"Output: {prediction['output']}")
```

### Version Management

```python
# List all versions of a model
versions = await connector.list_model_versions("your-username/my-adapter")

for version in versions:
    print(f"Version: {version['id']}")
    print(f"Created: {version['created_at']}")
    print(f"Config: {version.get('config', {})}")

# Get specific version
version = await connector.get_model_version(
    model_id="your-username/my-adapter",
    version_id="abc123..."
)

print(f"Version details: {version}")

# Use specific version for inference
result = await connector.inference(
    model_id="your-username/my-adapter",
    version_id="abc123...",  # Specific version
    prompt="Hello, world!"
)
```

### Model Management

```python
# Get model information
model = await connector.get_model("your-username/my-adapter")

print(f"Model: {model['name']}")
print(f"Owner: {model['owner']}")
print(f"Visibility: {model['visibility']}")
print(f"Hardware: {model['hardware']}")

# Delete model
deleted = await connector.delete_model("your-username/my-adapter")
print(f"Model deleted: {deleted}")
```

### List Available Resources

```python
# Get available GPU resources
resources = await connector.list_resources()

for resource in resources:
    print(f"Resource: {resource.name}")
    print(f"GPU: {resource.gpu_type}")
    print(f"VRAM: {resource.vram_gb}GB")
    
    # Get pricing
    pricing = await connector.get_pricing(resource.id)
    print(f"Price: ${pricing.price_per_hour}/hour")
```

## Hardware Options

Replicate offers various GPU types:

- **T4**: Entry-level GPU, 16GB VRAM (~$0.23/hour)
- **A40 Small**: Mid-range GPU, 48GB VRAM (~$1.40/hour)
- **A40 Large**: High-end GPU, 48GB VRAM (~$2.80/hour)

## Pricing

Replicate charges per second of compute time:

- Billing is per-second with 1-second increments
- No minimum charge
- Prices vary by GPU type
- Predictions are billed for actual runtime

## Version Management

Replicate supports multiple versions per model:

1. **Create Model**: Define the model container
2. **Create Versions**: Upload different weights/configs
3. **Switch Versions**: Use specific versions for inference
4. **Track History**: View all versions and their configs

## Best Practices

### Model Deployment

1. **Use Descriptive Names**: Make models easy to find
2. **Set Visibility**: Choose public or private appropriately
3. **Document Versions**: Add clear version descriptions
4. **Test Before Public**: Test with private visibility first

### Inference

1. **Handle Timeouts**: Set appropriate timeout values
2. **Monitor Latency**: Track prediction times
3. **Cancel Unused**: Cancel predictions you don't need
4. **Batch Requests**: Group similar requests when possible

### Version Management

1. **Semantic Versioning**: Use clear version numbers (v1, v2, etc.)
2. **Keep History**: Don't delete old versions immediately
3. **Document Changes**: Note what changed between versions
4. **Test Versions**: Verify each version before promoting

## Error Handling

```python
try:
    result = await connector.inference(
        model_id="your-username/my-adapter",
        prompt="Hello"
    )
except RuntimeError as e:
    print(f"Inference failed: {e}")
except TimeoutError as e:
    print(f"Prediction timed out: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Limitations

1. **Model Packaging**: Requires Cog for full model packaging
2. **Upload Size**: Large models may take time to upload
3. **Cold Starts**: First prediction may be slower
4. **Rate Limits**: API has rate limits (check Replicate docs)

## Integration with PEFT Studio

The Replicate connector integrates with PEFT Studio to:

1. Deploy fine-tuned adapters
2. Create inference endpoints
3. Test models before sharing
4. Manage multiple model versions
5. Track deployment costs

## API Reference

### Connection Methods

- `connect(credentials)`: Connect to Replicate
- `disconnect()`: Disconnect and cleanup
- `verify_connection()`: Check connection status

### Model Methods

- `create_model(owner, name, ...)`: Create new model
- `get_model(model_id)`: Get model information
- `delete_model(model_id)`: Delete model

### Version Methods

- `create_model_version(model_id, version, ...)`: Create version
- `list_model_versions(model_id)`: List all versions
- `get_model_version(model_id, version_id)`: Get version details

### Inference Methods

- `create_prediction(model_id, ...)`: Create prediction
- `get_prediction(prediction_id)`: Get prediction status
- `wait_for_prediction(prediction_id)`: Wait for completion
- `cancel_prediction(prediction_id)`: Cancel prediction
- `inference(model_id, prompt, ...)`: Run inference

### Deployment Methods

- `deploy_model(model_name, base_model, ...)`: Deploy model
- `upload_artifact(path, metadata)`: Upload adapter

## Support

For issues or questions:

1. Check Replicate documentation: https://replicate.com/docs
2. Review API reference: https://replicate.com/docs/reference/http
3. Contact Replicate support: https://replicate.com/support
