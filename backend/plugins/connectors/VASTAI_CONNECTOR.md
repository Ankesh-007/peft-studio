# Vast.ai Connector

## Overview

The Vast.ai connector integrates with the Vast.ai GPU marketplace to provide access to competitively priced GPU instances from multiple hosts worldwide. Vast.ai operates as a marketplace where GPU owners rent out their hardware, often at lower prices than traditional cloud providers.

## Features

- **Marketplace Search**: Search and compare GPU instances across multiple hosts
- **Flexible Pricing**: Access to competitive pricing with per-minute billing
- **Instance Rental**: Rent GPU instances on-demand
- **Job Submission**: Submit and monitor training jobs
- **SSH-based Access**: Direct SSH access to instances for log streaming and artifact download
- **Pricing Comparison**: Compare prices across different hosts for the same GPU type

## Supported GPU Types

Vast.ai marketplace typically offers:
- NVIDIA RTX 4090 (24GB)
- NVIDIA RTX 3090 (24GB)
- NVIDIA A100 (40GB/80GB)
- NVIDIA A6000 (48GB)
- NVIDIA V100 (16GB/32GB)
- And many more depending on marketplace availability

## Configuration

### Required Credentials

- `api_key`: Your Vast.ai API key

### Getting API Key

1. Sign up at [vast.ai](https://vast.ai/)
2. Go to Account Settings
3. Navigate to API Keys section
4. Generate a new API key
5. Copy the key for use in PEFT Studio

## Usage

### Connecting to Vast.ai

```python
from plugins.connectors.vastai_connector import VastAIConnector

connector = VastAIConnector()

# Connect with API key
await connector.connect({
    "api_key": "your_vastai_api_key_here"
})

# Verify connection
is_connected = await connector.verify_connection()
```

### Listing Available Resources

```python
# Get list of available GPU types
resources = await connector.list_resources()

for resource in resources:
    print(f"{resource.name}: {resource.gpu_count}x {resource.gpu_type}")
    print(f"  VRAM: {resource.vram_gb}GB")
    print(f"  Available: {resource.available}")
```

### Getting Pricing Information

```python
# Get pricing for specific GPU type
pricing = await connector.get_pricing("RTX 4090")

print(f"Price per hour: ${pricing.price_per_hour}")
print(f"Spot price: ${pricing.spot_price_per_hour}")
print(f"Billing increment: {pricing.billing_increment_seconds}s")
```

### Submitting Training Jobs

```python
from connectors.base import TrainingConfig

config = TrainingConfig(
    base_model="unsloth/llama-3-8b-bnb-4bit",
    model_source="huggingface",
    algorithm="lora",
    rank=16,
    alpha=16,
    dropout=0.1,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    quantization="int4",
    provider="vastai",
    resource_id="RTX 4090",  # Specify GPU type
    dataset_path="/data/train.json",
    project_name="my-training",
    output_dir="/workspace/output",
)

# Submit job
job_id = await connector.submit_job(config)
print(f"Job submitted: {job_id}")
```

### Monitoring Jobs

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

## Architecture

### Instance Lifecycle

1. **Search**: Query marketplace for available instances matching criteria
2. **Rent**: Rent the cheapest available instance
3. **Setup**: Instance boots with Docker image and onstart script
4. **Training**: Training script executes automatically
5. **Monitor**: SSH connection for log streaming
6. **Download**: Artifact retrieval via SCP
7. **Cleanup**: Instance destruction after completion

### SSH Access

Vast.ai provides direct SSH access to rented instances:
- Username: `root`
- Port: Assigned by Vast.ai (typically 22 or custom)
- Authentication: SSH key or password

The connector uses SSH for:
- Log streaming (`tail -f`)
- Artifact download (SFTP/SCP)
- Manual intervention if needed

## Pricing Model

Vast.ai uses a marketplace model:
- **Per-minute billing**: Charged by the minute, not hour
- **Variable pricing**: Prices vary by host and demand
- **No minimum commitment**: Pay only for what you use
- **Interruptible instances**: Lower prices for interruptible instances

### Cost Optimization Tips

1. **Search broadly**: Don't restrict to specific GPU models
2. **Use interruptible**: Save money with spot-like instances
3. **Monitor marketplace**: Prices fluctuate based on demand
4. **Destroy promptly**: Stop instances immediately after training
5. **Compare hosts**: Different hosts have different prices

## Limitations

1. **No central storage**: No built-in artifact registry
2. **Variable availability**: Marketplace-dependent availability
3. **Host reliability**: Quality varies by host
4. **Network speeds**: Upload/download speeds vary by host
5. **Instance stability**: Some hosts may be less reliable

## Error Handling

### Common Errors

**No instances available**
```
RuntimeError: No available instances found matching criteria
```
Solution: Broaden search criteria or try different GPU types

**SSH connection failed**
```
Error connecting via SSH: Connection refused
```
Solution: Wait for instance to fully boot, or check SSH credentials

**Artifact not found**
```
FileNotFoundError: Adapter not found
```
Solution: Ensure training completed successfully before downloading

**Instance failed to start**
```
RuntimeError: Instance 12345 failed to start
```
Solution: Check Vast.ai dashboard for instance status and logs

## Best Practices

1. **Verify instances**: Check host reliability ratings before renting
2. **Monitor costs**: Track spending in Vast.ai dashboard
3. **Test small**: Start with small jobs to test host performance
4. **Save frequently**: Use checkpointing for long training runs
5. **Clean up**: Always destroy instances after use

## Comparison with Other Providers

| Feature | Vast.ai | RunPod | Lambda Labs |
|---------|---------|--------|-------------|
| Pricing | Variable (marketplace) | Fixed | Fixed |
| Billing | Per-minute | Per-minute | Per-hour |
| Availability | Variable | High | Medium |
| Reliability | Variable | High | High |
| Setup Time | 2-5 min | 1-2 min | 3-5 min |
| SSH Access | Yes | Limited | Yes |
| Spot Instances | Yes (interruptible) | Yes | No |

## API Reference

### Vast.ai API Endpoints

- `GET /bundles/`: Search for available instances
- `PUT /asks/{id}/`: Rent an instance
- `GET /instances/`: Get instance information
- `DELETE /instances/{id}/`: Destroy an instance

### Rate Limits

Vast.ai API has rate limits:
- 100 requests per minute for search
- 10 requests per minute for instance operations

## Troubleshooting

### Instance won't start

1. Check Vast.ai balance
2. Verify GPU type availability
3. Try different hosts
4. Check Docker image compatibility

### Training fails immediately

1. Check onstart script syntax
2. Verify dataset path
3. Check GPU memory requirements
4. Review instance logs in Vast.ai dashboard

### Can't connect via SSH

1. Wait 2-3 minutes after instance creation
2. Check SSH port in instance details
3. Verify SSH keys are configured
4. Try password authentication if available

### Slow download speeds

1. Choose hosts with good network ratings
2. Use compression for large artifacts
3. Consider geographic location of host
4. Try different hosts if speeds are poor

## Support

For Vast.ai-specific issues:
- Documentation: https://vast.ai/docs/
- Discord: https://discord.gg/vastai
- Email: support@vast.ai

For connector issues:
- Check connector logs
- Verify API key is valid
- Test connection with `verify_connection()`
- Review error messages for details
