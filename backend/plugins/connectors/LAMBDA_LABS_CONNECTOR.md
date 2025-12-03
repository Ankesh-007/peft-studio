# Lambda Labs Connector

## Overview

The Lambda Labs connector integrates PEFT Studio with Lambda Labs' cloud GPU platform, providing access to high-performance H100 and A100 GPU instances at competitive prices.

## Features

- **H100/A100 Instance Management**: Provision and manage high-performance GPU instances
- **Job Submission**: Submit training jobs with automatic environment setup
- **SSH-Based Log Streaming**: Real-time log streaming via SSH connection
- **Artifact Download via SCP**: Secure artifact download using SCP protocol
- **Pricing Queries**: Real-time pricing and availability information
- **Hourly Billing**: Lambda Labs bills by the hour with no per-minute charges

## Configuration

### Required Credentials

- `api_key`: Lambda Labs API key (required)
- `ssh_key_path`: Path to SSH private key (optional, for SSH connections)

### Getting API Key

1. Create an account at [lambdalabs.com](https://lambdalabs.com)
2. Navigate to API settings in your dashboard
3. Generate a new API key
4. Copy the API key for use in PEFT Studio

## Usage

### Connecting to Lambda Labs

```python
from plugins.connectors.lambda_labs_connector import LambdaLabsConnector

connector = LambdaLabsConnector()

# Connect with API key
await connector.connect({
    "api_key": "your_api_key_here",
    "ssh_key_path": "/path/to/ssh/key"  # Optional
})

# Verify connection
is_connected = await connector.verify_connection()
```

### Listing Available Resources

```python
# Get all available GPU instances
resources = await connector.list_resources()

for resource in resources:
    print(f"{resource.name}: {resource.gpu_type} - ${resource.hourly_rate}/hr")
    print(f"  VRAM: {resource.vram_gb}GB")
    print(f"  Available: {resource.available}")
```

### Getting Pricing Information

```python
# Get pricing for specific instance type
pricing = await connector.get_pricing("gpu_1x_a100")

print(f"Price: ${pricing.price_per_hour}/hr")
print(f"Billing: Every {pricing.billing_increment_seconds}s")
print(f"Minimum charge: {pricing.minimum_charge_seconds}s")
```

### Submitting Training Jobs

```python
from connectors.base import TrainingConfig

# Create training configuration
config = TrainingConfig(
    base_model="unsloth/llama-2-7b-bnb-4bit",
    model_source="huggingface",
    algorithm="lora",
    rank=16,
    alpha=32,
    dropout=0.1,
    target_modules=["q_proj", "v_proj"],
    quantization="int4",
    provider="lambda_labs",
    resource_id="gpu_1x_a100",
    dataset_path="/data/train.json",
    project_name="my-project",
    output_dir="/workspace/output"
)

# Submit job
job_id = await connector.submit_job(config)
print(f"Job submitted: {job_id}")
```

### Monitoring Job Status

```python
# Get job status
status = await connector.get_job_status(job_id)
print(f"Job status: {status.value}")

# Stream logs in real-time
async for log_line in connector.stream_logs(job_id):
    print(log_line)
```

### Downloading Artifacts

```python
# Download trained adapter
artifact_data = await connector.fetch_artifact(job_id)

# Save to file
with open("adapter.tar.gz", "wb") as f:
    f.write(artifact_data)
```

### Canceling Jobs

```python
# Cancel a running job
success = await connector.cancel_job(job_id)
if success:
    print("Job cancelled successfully")
```

## Available Instance Types

Lambda Labs offers various GPU instance types:

### H100 Instances
- **gpu_1x_h100**: 1x H100 (80GB) - ~$2.49/hr
- **gpu_8x_h100**: 8x H100 (80GB) - Higher performance for large models

### A100 Instances
- **gpu_1x_a100**: 1x A100 (40GB) - ~$1.10/hr
- **gpu_1x_a100_80gb**: 1x A100 (80GB) - ~$1.29/hr
- **gpu_8x_a100**: 8x A100 (40GB) - Multi-GPU training

### Other GPUs
- **gpu_1x_rtx3090**: 1x RTX 3090 (24GB) - ~$0.50/hr
- **gpu_1x_v100**: 1x V100 (16GB) - ~$0.50/hr
- **gpu_1x_a10**: 1x A10 (24GB) - Budget-friendly option

## SSH Connection

The Lambda Labs connector uses SSH for:
- Starting training jobs on provisioned instances
- Streaming logs in real-time
- Downloading artifacts via SCP

### SSH Key Setup

1. Generate SSH key pair if you don't have one:
   ```bash
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/lambda_labs_key
   ```

2. Add public key to Lambda Labs dashboard

3. Provide private key path when connecting:
   ```python
   await connector.connect({
       "api_key": "your_api_key",
       "ssh_key_path": "~/.ssh/lambda_labs_key"
   })
   ```

## Training Environment

When a job is submitted, the connector:

1. **Provisions Instance**: Launches the specified GPU instance
2. **Waits for Active**: Monitors until instance is ready
3. **Connects via SSH**: Establishes SSH connection to instance
4. **Installs Dependencies**: Installs required Python packages
   - unsloth
   - transformers
   - datasets
   - accelerate
   - peft
5. **Uploads Training Script**: Transfers generated training script
6. **Starts Training**: Executes training in background
7. **Streams Logs**: Provides real-time log streaming

## Pricing Comparison

Lambda Labs is known for competitive pricing:

| GPU Type | Lambda Labs | RunPod | Savings |
|----------|-------------|--------|---------|
| A100 80GB | $1.29/hr | $2.49/hr | 48% |
| H100 | $2.49/hr | $4.25/hr | 41% |
| RTX 3090 | $0.50/hr | $0.44/hr | -12% |

## Advantages

- **Lowest Prices**: Best pricing for A100/H100 GPUs
- **Fast NVMe Storage**: High-speed local storage
- **Pre-configured**: ML environments ready to use
- **Excellent Bandwidth**: Fast data transfer
- **Simple Billing**: Hourly billing, no hidden fees

## Limitations

- **Availability**: High demand can limit instance availability
- **Hourly Minimum**: Billed by the hour (no per-minute billing)
- **Wait Times**: May need to wait for popular instance types
- **No Spot Instances**: No spot/preemptible pricing available

## Error Handling

The connector handles various error scenarios:

### Connection Errors
- Invalid API key → `ValueError`
- Network timeout → `ConnectionError`
- API unavailable → `ConnectionError`

### Job Submission Errors
- Invalid configuration → `ValueError`
- No available instances → `RuntimeError`
- SSH connection failed → `RuntimeError`

### Artifact Errors
- Job not completed → `RuntimeError`
- Artifact not found → `FileNotFoundError`
- Download failed → `RuntimeError`

## Best Practices

1. **Check Availability**: Use `list_resources()` to check instance availability before submitting jobs

2. **Monitor Costs**: Lambda Labs bills hourly, so monitor job duration

3. **SSH Keys**: Use SSH keys for secure, password-less authentication

4. **Instance Selection**: Choose appropriate instance type for your model size:
   - 7B models: A100 40GB or RTX 3090
   - 13B models: A100 80GB
   - 70B+ models: H100 or multi-GPU A100

5. **Cleanup**: Always cancel jobs when done to avoid unnecessary charges

6. **Artifact Download**: Download artifacts promptly as instances are terminated after job completion

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to Lambda Labs API
```
ConnectionError: Failed to connect to Lambda Labs
```

**Solution**:
- Verify API key is correct
- Check internet connection
- Verify Lambda Labs API is operational

### SSH Connection Issues

**Problem**: Cannot establish SSH connection
```
RuntimeError: Failed to connect via SSH
```

**Solution**:
- Verify SSH key is added to Lambda Labs account
- Check SSH key path is correct
- Ensure instance is fully booted (wait a few minutes)

### Instance Availability

**Problem**: No instances available
```
RuntimeError: No instance ID returned
```

**Solution**:
- Try different instance type
- Wait and retry (instances become available frequently)
- Consider alternative GPU types

### Artifact Download Issues

**Problem**: Artifact not found
```
FileNotFoundError: Adapter not found
```

**Solution**:
- Verify training completed successfully
- Check logs for training errors
- Ensure output directory is correct in config

## Integration with PEFT Studio

The Lambda Labs connector integrates seamlessly with PEFT Studio:

1. **Platform Selection**: Available in compute provider dropdown
2. **Cost Comparison**: Automatically compared with other platforms
3. **Offline Queue**: Jobs queued when offline, submitted when online
4. **Credential Management**: API keys stored securely in OS keystore
5. **Experiment Tracking**: Integrates with W&B, Comet ML, etc.

## API Reference

### LambdaLabsConnector

Main connector class implementing the `PlatformConnector` interface.

#### Methods

- `connect(credentials)`: Authenticate with Lambda Labs
- `disconnect()`: Close connections and cleanup
- `verify_connection()`: Check if connection is still valid
- `submit_job(config)`: Submit training job
- `get_job_status(job_id)`: Get current job status
- `cancel_job(job_id)`: Cancel running job
- `stream_logs(job_id)`: Stream logs in real-time
- `fetch_artifact(job_id)`: Download trained adapter
- `upload_artifact(path, metadata)`: Upload artifact (placeholder)
- `list_resources()`: List available GPU instances
- `get_pricing(resource_id)`: Get pricing for instance type

## Testing

Comprehensive test suite included:

```bash
# Run all tests
pytest tests/test_lambda_labs_connector.py -v

# Run specific test class
pytest tests/test_lambda_labs_connector.py::TestLambdaLabsConnection -v

# Run with coverage
pytest tests/test_lambda_labs_connector.py --cov=plugins.connectors.lambda_labs_connector
```

## Dependencies

- `aiohttp`: Async HTTP client for API calls
- `paramiko`: SSH client for remote connections
- `scp`: SCP client for file transfers

Install dependencies:
```bash
pip install aiohttp paramiko scp
```

## Support

For Lambda Labs platform issues:
- Documentation: https://docs.lambdalabs.com/
- Support: support@lambdalabs.com
- Status: https://status.lambdalabs.com/

For connector issues:
- Check logs in PEFT Studio
- Review test suite for examples
- Consult PEFT Studio documentation
