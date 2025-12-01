# RunPod Connector Implementation

## Overview

The RunPod connector provides integration with RunPod's cloud GPU platform for training LLM adapters. It implements all required functionality from the PlatformConnector interface.

## Features Implemented

### ✅ GPU Instance Provisioning
- Automatic GPU instance provisioning via RunPod GraphQL API
- Support for secure cloud instances
- Configurable GPU types (RTX A4000, A100, etc.)
- Automatic environment setup with PyTorch and Unsloth

### ✅ Job Submission and Monitoring
- Submit training jobs with full PEFT configuration
- Track job status (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED)
- Automatic training script generation from TrainingConfig
- Support for LoRA, QLoRA, DoRA, and other PEFT algorithms

### ✅ Log Streaming via WebSocket
- Real-time log streaming using WebSocket connection
- Fallback to polling if WebSocket fails
- Continuous monitoring until job completion

### ✅ Artifact Download
- Download trained adapters after job completion
- Automatic verification of job completion status
- Support for .safetensors format

### ✅ Pricing and Availability Queries
- List available GPU resources with specifications
- Get real-time pricing information
- Support for spot pricing (interruptible instances)
- Filter by secure cloud availability

## API Integration

### Authentication
- Uses RunPod API key for authentication
- Secure credential storage via OS keystore
- Bearer token authentication for all requests

### Endpoints Used
- **GraphQL API**: `https://api.runpod.io/graphql`
  - User verification
  - Pod creation and management
  - GPU type queries
  - Pricing information
  
- **REST API**: `https://api.runpod.io/v2`
  - Log retrieval
  - Artifact download
  - File uploads

- **WebSocket**: `wss://api.runpod.io/v2/{pod_id}/logs`
  - Real-time log streaming

## Configuration

### Required Credentials
- `api_key`: RunPod API key (get from https://runpod.io/console/user/settings)

### Supported Features
- ✅ Training
- ✅ Inference
- ❌ Registry (not applicable)
- ❌ Tracking (handled by separate connectors)

## Training Script Generation

The connector automatically generates a complete training script that:
1. Installs required dependencies (unsloth, transformers, datasets, etc.)
2. Loads the base model with optional quantization
3. Configures PEFT (LoRA/QLoRA/etc.) with specified parameters
4. Loads and prepares the dataset
5. Sets up training arguments
6. Creates and runs the SFTTrainer
7. Saves the trained adapter

## Usage Example

```python
from connectors.manager import ConnectorManager

# Initialize manager
manager = ConnectorManager()
manager.discover_connectors()

# Connect to RunPod
await manager.connect("runpod", {"api_key": "your-api-key"})

# List available GPUs
resources = await manager.list_resources("runpod")
for resource in resources:
    print(f"{resource.name}: ${resource.price_per_hour}/hr")

# Get pricing for specific GPU
pricing = await manager.get_pricing("runpod", "NVIDIA RTX A4000")
print(f"Price: ${pricing.price_per_hour}/hr")
print(f"Spot price: ${pricing.spot_price_per_hour}/hr")

# Submit training job
config = TrainingConfig(
    base_model="meta-llama/Llama-2-7b-hf",
    model_source="huggingface",
    algorithm="lora",
    rank=16,
    alpha=32,
    dropout=0.1,
    target_modules=["q_proj", "v_proj"],
    quantization="int4",
    provider="runpod",
    resource_id="NVIDIA RTX A4000",
    dataset_path="/data/train.json",
    project_name="my-training",
)

job_id = await manager.submit_job("runpod", config)
print(f"Job submitted: {job_id}")

# Stream logs
async for log in connector.stream_logs(job_id):
    print(log)

# Download artifact when complete
artifact = await connector.fetch_artifact(job_id)
with open("adapter.safetensors", "wb") as f:
    f.write(artifact)
```

## Testing

### Interface Compliance
All connector interface compliance tests pass:
- ✅ Connector discovery
- ✅ Required attributes present
- ✅ All methods implemented
- ✅ No abstract methods remaining
- ✅ Correct return types
- ✅ Failure isolation

### Unit Tests
Comprehensive unit tests cover:
- Connection with valid/invalid credentials
- Job submission and monitoring
- Status tracking
- Log streaming
- Resource listing
- Pricing queries
- Artifact download
- Configuration validation
- Training script generation

Run tests:
```bash
cd backend
python -m pytest tests/test_connector_interface_compliance.py -v
python -m pytest tests/test_runpod_connector.py -v
```

## Requirements Validated

This implementation validates:
- **Requirement 3.1**: Display available compute options from RunPod
- **Requirement 3.2**: Show real-time pricing and availability
- **Requirement 5.1**: Provision compute resources within 60 seconds
- **Requirement 5.3**: Stream logs and metrics in real-time

## Error Handling

The connector implements robust error handling:
- **ConnectionError**: Raised when API connection fails
- **ValueError**: Raised for invalid credentials or configuration
- **RuntimeError**: Raised for job submission/execution failures
- **FileNotFoundError**: Raised when artifacts don't exist

All errors include descriptive messages to help with troubleshooting.

## Future Enhancements

Potential improvements for future versions:
- Support for community cloud instances
- Multi-GPU training support
- Custom Docker image support
- Volume mounting for large datasets
- SSH access to running pods
- Cost optimization recommendations
- Automatic retry on transient failures

## Dependencies

- `aiohttp>=3.9.1`: Async HTTP client for API calls
- `asyncio`: Async/await support
- Standard library: `json`, `pathlib`, `typing`

## References

- [RunPod API Documentation](https://docs.runpod.io/)
- [RunPod GraphQL API](https://graphql-spec.runpod.io/)
- [Connector Architecture](../../../backend/connectors/README.md)
