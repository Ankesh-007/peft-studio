# Modal Connector

## Overview

The Modal connector integrates with Modal's serverless platform to deploy and manage inference functions with advanced cold-start optimization.

## Features

- **Serverless Function Deployment**: Deploy inference functions without managing infrastructure
- **Cold-Start Optimization**: Container caching and model preloading for fast response times
- **Usage Tracking**: Monitor invocations, compute time, and cold-start metrics
- **Multiple GPU Types**: Support for T4, A10G, and A100 GPUs
- **Per-Second Billing**: Pay only for actual compute time used

## Cold-Start Optimization

Modal connector implements several strategies to minimize cold starts:

1. **Container Caching**: Containers with the same base model and dependencies are cached and reused
2. **Model Preloading**: Models are loaded once when the container starts and cached for subsequent invocations
3. **Keep-Warm Containers**: Configurable number of warm containers to handle requests immediately
4. **Deterministic Container IDs**: Same model + dependencies = same container, enabling cache hits

## Configuration

### Required Credentials

- `token_id`: Modal token ID
- `token_secret`: Modal token secret

### Deployment Configuration

```python
deployment_config = {
    "gpu_type": "A10G",           # GPU type: T4, A10G, A100
    "memory_mb": 16384,            # Memory allocation
    "cpu_count": 4,                # CPU cores
    "quantization": "int8",        # Optional: int8, int4
    "max_batch_size": 8,           # Maximum batch size
    "keep_warm": 1,                # Number of warm containers
    "max_containers": 10,          # Maximum concurrent containers
}
```

## Usage Examples

### Connect to Modal

```python
from plugins.connectors.modal_connector import ModalConnector

connector = ModalConnector()
await connector.connect({
    "token_id": "your-token-id",
    "token_secret": "your-token-secret"
})
```

### Deploy a Function

```python
# Deploy function with base model
function_id = await connector.deploy_function(
    function_name="llama-inference",
    base_model="meta-llama/Llama-2-7b-hf",
    deployment_config={
        "gpu_type": "A10G",
        "keep_warm": 2,  # Keep 2 containers warm
        "quantization": "int8",
    }
)

# Deploy function with adapter
function_id = await connector.deploy_function(
    function_name="custom-adapter",
    base_model="meta-llama/Llama-2-7b-hf",
    adapter_path="/path/to/adapter",
    deployment_config={
        "gpu_type": "A100",
        "keep_warm": 1,
    }
)
```

### Invoke Function

```python
# Perform inference
result = await connector.invoke_function(
    function_id=function_id,
    prompt="What is the capital of France?",
    generation_config={
        "max_tokens": 256,
        "temperature": 0.7,
    }
)

print(f"Generated text: {result['text']}")
print(f"Latency: {result['latency_ms']}ms")
print(f"Cold start: {result['cold_start']}")
print(f"Tokens: {result['tokens']}")
```

### Get Usage Statistics

```python
# Get overall usage
stats = await connector.get_usage_stats()
print(f"Total invocations: {stats['total_invocations']}")
print(f"Cold starts: {stats['cold_starts']}")
print(f"Warm starts: {stats['warm_starts']}")
print(f"Total cost: ${stats['total_cost_usd']}")

# Get function-specific usage
stats = await connector.get_usage_stats(function_id=function_id)

# Get cold-start metrics
metrics = await connector.get_cold_start_metrics(function_id)
print(f"Cache hit rate: {metrics['container_cache_hit_rate']}%")
print(f"Avg cold start: {metrics['avg_cold_start_ms']}ms")
print(f"Avg warm start: {metrics['avg_warm_start_ms']}ms")
```

### List and Manage Functions

```python
# List all functions
functions = await connector.list_functions()
for func in functions:
    print(f"{func['name']}: {func['status']}")

# Check function status
status = await connector.get_function_status(function_id)
print(f"Status: {status}")

# Delete function
await connector.delete_function(function_id)
```

## Cold-Start Optimization Details

### Container Caching

The connector generates a deterministic container ID based on:
- Base model identifier
- Python dependencies list

When deploying a function, if a container with the same ID exists, it's reused, resulting in:
- Faster deployment times
- Reduced cold-start latency
- Lower costs (no redundant container builds)

### Model Preloading

The generated inference code:
1. Loads the model once when the container starts
2. Caches the model in global variables
3. Reuses the cached model for all subsequent invocations

This means:
- First invocation: Cold start (model loading time)
- Subsequent invocations: Warm start (instant model access)

### Keep-Warm Strategy

Configure `keep_warm` to maintain warm containers:
- `keep_warm: 0` - No warm containers (maximum cost savings, higher latency)
- `keep_warm: 1` - One warm container (balanced)
- `keep_warm: N` - N warm containers (lowest latency, higher cost)

## Pricing

Modal charges per second of compute time:

| GPU Type | Price per Hour | Price per Second |
|----------|---------------|------------------|
| T4       | $0.60         | ~$0.000167       |
| A10G     | $1.10         | ~$0.000305       |
| A100     | $4.00         | ~$0.00111        |

**Note**: You only pay for actual compute time. Warm containers incur minimal costs when idle.

## Performance Metrics

Track cold-start optimization effectiveness:

- **Container Cache Hit Rate**: Percentage of deployments using cached containers
- **Cold Start Latency**: Time to start a new container and load the model
- **Warm Start Latency**: Time to process a request with a warm container
- **P50/P95/P99 Latencies**: Percentile latencies for cold starts

## Best Practices

1. **Reuse Containers**: Deploy functions with the same base model and dependencies to maximize cache hits
2. **Keep-Warm Configuration**: Balance cost and latency based on traffic patterns
3. **Quantization**: Use int8/int4 quantization for faster loading and lower memory usage
4. **Batch Requests**: Configure appropriate `max_batch_size` for throughput optimization
5. **Monitor Metrics**: Track cold-start rates and adjust `keep_warm` accordingly

## Limitations

- Training jobs not supported (inference only)
- Artifact uploads not supported (use for inference, not model hosting)
- Maximum function execution time: 15 minutes
- Maximum container memory: 64GB

## Error Handling

The connector handles common errors:

- **Connection Errors**: Invalid credentials, network issues
- **Deployment Errors**: Invalid configuration, resource unavailable
- **Invocation Errors**: Function not ready, timeout, out of memory
- **Rate Limiting**: Automatic retry with exponential backoff

## Requirements Mapping

This connector satisfies the following requirements:

- **9.1**: Deploy adapters for inference on Modal platform
- **9.2**: Create serverless endpoints with function deployment
- **9.4**: Provide API endpoints for inference via function invocation
- **Cold-Start Optimization**: Container caching, model preloading, keep-warm strategy
- **Usage Tracking**: Comprehensive metrics including cold-start statistics
