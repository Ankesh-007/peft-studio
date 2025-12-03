# Predibase Connector

## Overview

The Predibase connector integrates with Predibase's LoRAX platform for deploying and serving fine-tuned adapters with hot-swapping capabilities. LoRAX enables serving multiple adapters on a shared base model without reloading, making it highly efficient for multi-tenant inference scenarios.

## Features

- **LoRAX Adapter Deployment**: Deploy adapters to managed LoRAX endpoints
- **Hot-Swap Serving**: Switch between adapters without reloading the base model
- **Inference Management**: Perform inference with adapter selection per request
- **Usage Tracking**: Monitor requests, tokens, and costs
- **Multi-Adapter Support**: Serve multiple adapters on the same base model

## Configuration

### Required Credentials

- `api_key`: Predibase API key (get from https://app.predibase.com/settings/api-keys)
- `tenant_id` (optional): Tenant identifier (auto-detected if not provided)

### Example Connection

```python
from plugins.connectors.predibase_connector import PredibaseConnector

connector = PredibaseConnector()

# Connect with credentials
await connector.connect({
    "api_key": "pb_your_api_key_here"
})

# Verify connection
is_connected = await connector.verify_connection()
print(f"Connected: {is_connected}")
```

## Usage

### Deploy an Adapter

```python
# Deploy adapter to LoRAX
deployment_id = await connector.deploy_adapter(
    adapter_path="./output/my-adapter",
    base_model="meta-llama/Llama-2-7b-hf",
    adapter_name="my-custom-adapter",
    deployment_config={
        "max_batch_size": 32,
        "max_concurrent_requests": 100,
        "gpu_type": "A100"
    }
)

print(f"Deployment ID: {deployment_id}")

# Wait for deployment to be ready
while True:
    status = await connector.get_deployment_status(deployment_id)
    print(f"Status: {status}")
    if status == "ready":
        break
    await asyncio.sleep(5)
```

### Perform Inference with Hot-Swapping

The key feature of Predibase/LoRAX is the ability to specify which adapter to use for each request without reloading the base model:

```python
# Inference with base model
result = await connector.inference(
    deployment_id=deployment_id,
    prompt="What is the capital of France?",
    generation_config={
        "max_new_tokens": 100,
        "temperature": 0.7
    }
)
print(f"Base model response: {result['text']}")

# Inference with adapter (hot-swap!)
result = await connector.inference(
    deployment_id=deployment_id,
    prompt="What is the capital of France?",
    adapter_name="my-custom-adapter",  # Specify adapter
    generation_config={
        "max_new_tokens": 100,
        "temperature": 0.7
    }
)
print(f"Adapter response: {result['text']}")
print(f"Latency: {result['latency_ms']:.2f}ms")

# Switch to different adapter (no reload needed!)
result = await connector.inference(
    deployment_id=deployment_id,
    prompt="Translate to Spanish: Hello world",
    adapter_name="translation-adapter",  # Different adapter
)
print(f"Translation: {result['text']}")
```

### List Deployments

```python
# Get all deployments
deployments = await connector.list_deployments()

for deployment in deployments:
    print(f"ID: {deployment['id']}")
    print(f"Name: {deployment['adapter_name']}")
    print(f"Base Model: {deployment['base_model']}")
    print(f"Status: {deployment['status']}")
    print(f"Endpoint: {deployment['endpoint']}")
    print("---")
```

### Upload Adapter to Registry

```python
# Upload adapter to Predibase registry
adapter_id = await connector.upload_artifact(
    path="./output/my-adapter",
    metadata={
        "name": "my-custom-adapter",
        "base_model": "meta-llama/Llama-2-7b-hf",
        "description": "Fine-tuned for customer support",
        "tags": ["customer-support", "llama-2"]
    }
)

print(f"Adapter ID: {adapter_id}")

# List all adapters
adapters = await connector.list_adapters()
for adapter in adapters:
    print(f"{adapter['name']}: {adapter['base_model']}")
```

### Track Usage and Billing

```python
# Get usage statistics
usage = await connector.get_usage_stats(
    deployment_id=deployment_id,
    start_date="2024-01-01",
    end_date="2024-01-31"
)

print(f"Total Requests: {usage['total_requests']}")
print(f"Total Tokens: {usage['total_tokens']}")
print(f"Total Cost: ${usage['total_cost_usd']:.2f}")

# Get usage for all deployments
all_usage = await connector.get_usage_stats()
print(f"Account Total: ${all_usage['total_cost_usd']:.2f}")
```

### Stop Deployment

```python
# Stop a deployment to save costs
success = await connector.stop_deployment(deployment_id)
print(f"Stopped: {success}")
```

## Hot-Swap Adapter Loading

The hot-swap feature is the core value proposition of Predibase/LoRAX. It allows you to:

1. **Deploy multiple adapters** on the same base model
2. **Switch between adapters** per request without reloading
3. **Reduce latency** by keeping the base model in memory
4. **Save costs** by sharing compute across adapters

### How It Works

```python
# Deploy base model with multiple adapters
deployment_id = await connector.deploy_adapter(
    adapter_path="./adapters/adapter-1",
    base_model="meta-llama/Llama-2-7b-hf",
    adapter_name="adapter-1"
)

# Upload additional adapters to the same deployment
await connector.upload_artifact(
    path="./adapters/adapter-2",
    metadata={
        "name": "adapter-2",
        "base_model": "meta-llama/Llama-2-7b-hf"
    }
)

# Now you can switch between adapters instantly:
result1 = await connector.inference(
    deployment_id=deployment_id,
    prompt="Summarize this text...",
    adapter_name="adapter-1"  # Use adapter-1
)

result2 = await connector.inference(
    deployment_id=deployment_id,
    prompt="Translate this text...",
    adapter_name="adapter-2"  # Switch to adapter-2 (no reload!)
)

# The base model stays loaded, only adapter weights are swapped
```

## API Reference

### `deploy_adapter(adapter_path, base_model, adapter_name, deployment_config)`

Deploy an adapter to LoRAX.

**Parameters:**
- `adapter_path` (str): Local path to adapter files
- `base_model` (str): Base model identifier
- `adapter_name` (str): Name for the deployed adapter
- `deployment_config` (dict, optional): Deployment configuration

**Returns:** Deployment ID (str)

### `inference(deployment_id, prompt, adapter_name, generation_config)`

Perform inference with optional adapter hot-swapping.

**Parameters:**
- `deployment_id` (str): Deployment identifier
- `prompt` (str): Input prompt
- `adapter_name` (str, optional): Adapter to use (enables hot-swapping)
- `generation_config` (dict, optional): Generation parameters

**Returns:** Dictionary with 'text', 'tokens', 'latency_ms', 'adapter_used'

### `get_deployment_status(deployment_id)`

Get the status of a deployment.

**Parameters:**
- `deployment_id` (str): Deployment identifier

**Returns:** Status string ("deploying", "ready", "failed", "stopped")

### `list_deployments()`

List all deployments for the tenant.

**Returns:** List of deployment dictionaries

### `stop_deployment(deployment_id)`

Stop a running deployment.

**Parameters:**
- `deployment_id` (str): Deployment identifier

**Returns:** Boolean indicating success

### `upload_artifact(path, metadata)`

Upload an adapter to Predibase registry.

**Parameters:**
- `path` (str): Local path to adapter directory
- `metadata` (dict): Adapter metadata (name, base_model, description, tags)

**Returns:** Adapter ID (str)

### `list_adapters()`

List all adapters in the registry.

**Returns:** List of adapter dictionaries

### `get_usage_stats(deployment_id, start_date, end_date)`

Get usage statistics and billing information.

**Parameters:**
- `deployment_id` (str, optional): Filter by deployment
- `start_date` (str, optional): Start date (ISO format)
- `end_date` (str, optional): End date (ISO format)

**Returns:** Dictionary with usage statistics

## Error Handling

```python
try:
    deployment_id = await connector.deploy_adapter(
        adapter_path="./my-adapter",
        base_model="meta-llama/Llama-2-7b-hf",
        adapter_name="my-adapter"
    )
except FileNotFoundError as e:
    print(f"Adapter files not found: {e}")
except RuntimeError as e:
    print(f"Deployment failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Best Practices

1. **Use Hot-Swapping**: Deploy multiple adapters on the same base model to maximize efficiency
2. **Monitor Usage**: Regularly check usage stats to optimize costs
3. **Stop Unused Deployments**: Stop deployments when not in use to save costs
4. **Batch Requests**: Use appropriate batch sizes for your workload
5. **Cache Adapters**: Upload adapters to the registry for reuse across deployments

## Limitations

- Training is not supported (use compute providers like RunPod for training)
- Adapters must be compatible with the base model
- Maximum adapter size depends on GPU memory
- Hot-swapping works best with adapters of similar rank

## Resources

- [Predibase Documentation](https://docs.predibase.com/)
- [LoRAX GitHub](https://github.com/predibase/lorax)
- [LoRAX Paper](https://arxiv.org/abs/2402.01291)
- [Predibase API Reference](https://docs.predibase.com/api-reference)
