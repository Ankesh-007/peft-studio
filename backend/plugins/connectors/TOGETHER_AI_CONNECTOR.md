# Together AI Connector

## Overview

The Together AI connector integrates with Together AI's serverless inference platform for deploying and serving models with pay-per-token pricing. Together AI provides a simple, scalable way to deploy fine-tuned adapters without managing infrastructure.

## Features

- **Serverless Endpoints**: Create inference endpoints without managing servers
- **Adapter Upload**: Upload and deploy fine-tuned adapters
- **Pay-Per-Token Pricing**: Only pay for tokens generated, no idle costs
- **Streaming Inference**: Support for streaming responses
- **Usage Monitoring**: Track requests, tokens, and costs
- **Multi-Model Support**: Deploy and serve multiple models

## Configuration

### Required Credentials

- `api_key`: Together AI API key (get from https://api.together.xyz/settings/api-keys)

### Example Connection

```python
from plugins.connectors.together_ai_connector import TogetherAIConnector

connector = TogetherAIConnector()

# Connect with credentials
await connector.connect({
    "api_key": "your_api_key_here"
})

# Verify connection
is_connected = await connector.verify_connection()
print(f"Connected: {is_connected}")
```

## Usage

### Create Serverless Endpoint

```python
# Create endpoint for a base model
endpoint_id = await connector.create_endpoint(
    model_name="meta-llama/Llama-2-7b-hf",
    endpoint_name="my-llama-endpoint",
    endpoint_config={
        "max_tokens": 2048,
        "temperature": 0.7,
        "top_p": 0.9
    }
)

print(f"Endpoint ID: {endpoint_id}")

# Check endpoint status
status = await connector.get_endpoint_status(endpoint_id)
print(f"Status: {status}")
```

### Deploy an Adapter

```python
# Upload and deploy adapter
deployment_id = await connector.deploy_adapter(
    adapter_path="./output/my-adapter",
    base_model="meta-llama/Llama-2-7b-hf",
    adapter_name="my-custom-adapter",
    deployment_config={
        "max_tokens": 1024,
        "temperature": 0.8
    }
)

print(f"Deployment ID: {deployment_id}")

# Wait for deployment to be ready
while True:
    status = await connector.get_endpoint_status(deployment_id)
    print(f"Status: {status}")
    if status == "ready":
        break
    await asyncio.sleep(5)
```

### Perform Inference (Pay-Per-Token)

The key feature of Together AI is pay-per-token pricing - you only pay for what you use:

```python
# Inference with pay-per-token pricing
result = await connector.inference(
    model="meta-llama/Llama-2-7b-hf",
    prompt="What is the capital of France?",
    generation_config={
        "max_tokens": 100,
        "temperature": 0.7
    }
)

print(f"Response: {result['text']}")
print(f"Tokens used: {result['tokens']['total']}")
print(f"Cost: ${result['cost_usd']:.6f}")
print(f"Latency: {result['latency_ms']:.2f}ms")

# Inference with deployed adapter
result = await connector.inference(
    model=deployment_id,  # Use your deployed adapter
    prompt="Translate to Spanish: Hello world",
    generation_config={
        "max_tokens": 50
    }
)

print(f"Translation: {result['text']}")
print(f"Cost: ${result['cost_usd']:.6f}")
```

### Streaming Inference

```python
# Stream responses for better UX
print("Streaming response: ", end="")

async for chunk in connector.inference_streaming(
    model="meta-llama/Llama-2-7b-hf",
    prompt="Write a short story about a robot:",
    generation_config={
        "max_tokens": 500,
        "temperature": 0.9
    }
):
    print(chunk['text'], end="", flush=True)
    
    if chunk['finish_reason']:
        print(f"\n\nFinished: {chunk['finish_reason']}")
        break
```

### List Available Models

```python
# Get all available models
models = await connector.list_available_models()

for model in models:
    print(f"ID: {model['id']}")
    print(f"Name: {model['name']}")
    print(f"Type: {model.get('type', 'base')}")
    print(f"Context Length: {model.get('context_length', 'N/A')}")
    print("---")
```

### List Endpoints

```python
# Get all your endpoints
endpoints = await connector.list_endpoints()

for endpoint in endpoints:
    print(f"ID: {endpoint['id']}")
    print(f"Name: {endpoint['name']}")
    print(f"Model: {endpoint['model']}")
    print(f"Status: {endpoint['status']}")
    print(f"URL: {endpoint['url']}")
    print("---")
```

### Upload Adapter

```python
# Upload adapter to Together AI
model_id = await connector.upload_artifact(
    path="./output/my-adapter",
    metadata={
        "name": "my-custom-adapter",
        "base_model": "meta-llama/Llama-2-7b-hf",
        "description": "Fine-tuned for customer support"
    }
)

print(f"Model ID: {model_id}")

# Now you can use this model_id for inference
result = await connector.inference(
    model=model_id,
    prompt="How can I help you today?"
)
```

### Track Usage and Billing

```python
# Get usage statistics
usage = await connector.get_usage_stats(
    start_date="2024-01-01",
    end_date="2024-01-31"
)

print(f"Total Requests: {usage['total_requests']}")
print(f"Total Tokens: {usage['total_tokens']}")
print(f"  Prompt Tokens: {usage['prompt_tokens']}")
print(f"  Completion Tokens: {usage['completion_tokens']}")
print(f"Total Cost: ${usage['total_cost_usd']:.2f}")

# Get current month usage
current_usage = await connector.get_usage_stats()
print(f"Current Month Cost: ${current_usage['total_cost_usd']:.2f}")
```

### Delete Endpoint

```python
# Delete endpoint to stop billing
success = await connector.delete_endpoint(endpoint_id)
print(f"Deleted: {success}")
```

## Pay-Per-Token Pricing

Together AI's pay-per-token model means:

1. **No Idle Costs**: You don't pay when the endpoint is not being used
2. **Automatic Scaling**: Handles traffic spikes automatically
3. **Cost Efficiency**: Only pay for actual token generation
4. **Transparent Pricing**: Each response includes token count and cost

### Pricing Example

```python
# Example: Generate 1000 tokens
result = await connector.inference(
    model="meta-llama/Llama-2-7b-hf",
    prompt="Write a detailed explanation of quantum computing",
    generation_config={"max_tokens": 1000}
)

# Typical pricing: ~$0.0002 per 1K tokens for Llama-2-7B
# Cost for 1000 tokens: ~$0.0002
print(f"Generated {result['tokens']['total']} tokens")
print(f"Cost: ${result['cost_usd']:.6f}")

# Compare to hourly pricing:
# - RunPod A100: $1.89/hour
# - Together AI: Only pay for tokens used
# - If you generate 1M tokens/hour: ~$0.20
# - Savings: ~90% for bursty workloads
```

## API Reference

### `create_endpoint(model_name, endpoint_name, endpoint_config)`

Create a serverless inference endpoint.

**Parameters:**
- `model_name` (str): Model identifier
- `endpoint_name` (str): Name for the endpoint
- `endpoint_config` (dict, optional): Endpoint configuration

**Returns:** Endpoint ID (str)

### `deploy_adapter(adapter_path, base_model, adapter_name, deployment_config)`

Deploy an adapter to Together AI.

**Parameters:**
- `adapter_path` (str): Local path to adapter files
- `base_model` (str): Base model identifier
- `adapter_name` (str): Name for the deployed adapter
- `deployment_config` (dict, optional): Deployment configuration

**Returns:** Deployment ID (str)

### `inference(model, prompt, generation_config)`

Perform inference with pay-per-token pricing.

**Parameters:**
- `model` (str): Model identifier or endpoint ID
- `prompt` (str): Input prompt
- `generation_config` (dict, optional): Generation parameters

**Returns:** Dictionary with 'text', 'tokens', 'latency_ms', 'cost_usd'

### `inference_streaming(model, prompt, generation_config)`

Perform streaming inference.

**Parameters:**
- `model` (str): Model identifier or endpoint ID
- `prompt` (str): Input prompt
- `generation_config` (dict, optional): Generation parameters

**Yields:** Dictionaries with streaming response chunks

### `get_endpoint_status(endpoint_id)`

Get the status of an endpoint.

**Parameters:**
- `endpoint_id` (str): Endpoint identifier

**Returns:** Status string ("creating", "ready", "failed", "stopped")

### `list_endpoints()`

List all endpoints.

**Returns:** List of endpoint dictionaries

### `delete_endpoint(endpoint_id)`

Delete an endpoint.

**Parameters:**
- `endpoint_id` (str): Endpoint identifier

**Returns:** Boolean indicating success

### `upload_artifact(path, metadata)`

Upload an adapter to Together AI.

**Parameters:**
- `path` (str): Local path to adapter directory
- `metadata` (dict): Adapter metadata (name, base_model, description)

**Returns:** Model ID (str)

### `list_available_models()`

List all available models on Together AI.

**Returns:** List of model dictionaries

### `get_usage_stats(start_date, end_date)`

Get usage statistics and billing information.

**Parameters:**
- `start_date` (str, optional): Start date (ISO format)
- `end_date` (str, optional): End date (ISO format)

**Returns:** Dictionary with usage statistics

## Error Handling

```python
try:
    result = await connector.inference(
        model="meta-llama/Llama-2-7b-hf",
        prompt="Hello world"
    )
except RuntimeError as e:
    print(f"Inference failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Best Practices

1. **Use Streaming**: For better UX, use streaming inference for long responses
2. **Monitor Costs**: Regularly check usage stats to track spending
3. **Delete Unused Endpoints**: Remove endpoints you're not using
4. **Optimize Prompts**: Shorter prompts = lower costs
5. **Set Max Tokens**: Always set reasonable max_tokens to control costs
6. **Batch Requests**: For high throughput, batch similar requests

## Cost Optimization Tips

1. **Use Smaller Models**: Start with 7B models, only use larger if needed
2. **Limit Max Tokens**: Set appropriate max_tokens for your use case
3. **Cache Responses**: Cache common queries to avoid redundant API calls
4. **Use Stop Sequences**: Define stop sequences to avoid generating unnecessary tokens
5. **Monitor Usage**: Set up alerts for unexpected usage spikes

## Comparison with Other Platforms

| Feature | Together AI | Predibase | Modal |
|---------|------------|-----------|-------|
| Pricing | Pay-per-token | Pay-per-token + base | Pay-per-second |
| Idle Cost | $0 | $0 | $0 |
| Hot-Swap | No | Yes (LoRAX) | No |
| Streaming | Yes | Yes | Yes |
| Best For | Bursty workloads | Multi-tenant | Custom functions |

## Limitations

- Training is not supported (use compute providers like RunPod for training)
- No hot-swapping between adapters (each adapter is a separate endpoint)
- Pricing varies by model (larger models cost more per token)
- Rate limits apply based on your plan

## Resources

- [Together AI Documentation](https://docs.together.ai/)
- [Together AI API Reference](https://docs.together.ai/reference)
- [Together AI Pricing](https://www.together.ai/pricing)
- [Together AI Models](https://docs.together.ai/docs/inference-models)
