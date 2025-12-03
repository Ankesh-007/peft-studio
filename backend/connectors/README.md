# Connector Architecture

This directory contains the pluggable connector system for integrating with external platforms.

## Overview

The connector architecture provides a modular, extensible system for integrating with:
- Cloud GPU providers (RunPod, Lambda Labs, Vast.ai)
- Model registries (HuggingFace, Civitai, Ollama)
- Experiment trackers (Weights & Biases, Comet ML, Arize Phoenix)
- Deployment platforms (Predibase, Together AI, Modal, Replicate)

## Architecture

### Core Components

1. **PlatformConnector** (`base.py`): Abstract base class that all connectors must implement
2. **ConnectorRegistry** (`registry.py`): Manages connector metadata and validation
3. **ConnectorManager** (`manager.py`): Handles connector lifecycle and discovery
4. **Configuration Schema** (`config_schema.py`): Defines connector configuration structure

### Directory Structure

```
backend/
├── connectors/
│   ├── __init__.py           # Package exports
│   ├── base.py               # Base connector interface
│   ├── registry.py           # Connector registry
│   ├── manager.py            # Connector manager
│   ├── config_schema.py      # Configuration schema
│   └── README.md             # This file
└── plugins/
    └── connectors/
        ├── local_connector.py      # Example: Local GPU connector
        ├── runpod_connector.py     # RunPod integration
        └── ...                     # Other connectors
```

## Creating a New Connector

### Step 1: Implement the Interface

Create a new file in `backend/plugins/connectors/` named `{platform}_connector.py`:

```python
from connectors.base import PlatformConnector, Resource, PricingInfo, TrainingConfig, JobStatus
from typing import Dict, List, AsyncIterator

class MyPlatformConnector(PlatformConnector):
    # Metadata
    name = "myplatform"
    display_name = "My Platform"
    description = "Integration with My Platform"
    version = "1.0.0"
    
    # Features
    supports_training = True
    supports_inference = True
    supports_registry = False
    supports_tracking = False
    
    async def connect(self, credentials: Dict[str, str]) -> bool:
        # Implement connection logic
        pass
    
    async def disconnect(self) -> bool:
        # Implement disconnection logic
        pass
    
    async def verify_connection(self) -> bool:
        # Verify connection is still valid
        pass
    
    async def submit_job(self, config: TrainingConfig) -> str:
        # Submit training job
        pass
    
    async def get_job_status(self, job_id: str) -> JobStatus:
        # Get job status
        pass
    
    async def cancel_job(self, job_id: str) -> bool:
        # Cancel job
        pass
    
    async def stream_logs(self, job_id: str) -> AsyncIterator[str]:
        # Stream logs
        pass
    
    async def fetch_artifact(self, job_id: str) -> bytes:
        # Download artifact
        pass
    
    async def upload_artifact(self, path: str, metadata: Dict) -> str:
        # Upload artifact
        pass
    
    async def list_resources(self) -> List[Resource]:
        # List available resources
        pass
    
    async def get_pricing(self, resource_id: str) -> PricingInfo:
        # Get pricing info
        pass
    
    def get_required_credentials(self) -> List[str]:
        return ["api_key"]  # List required credential keys
```

### Step 2: Test Your Connector

The connector will be automatically discovered and validated by the test suite:

```bash
cd backend
python -m pytest tests/test_connector_interface_compliance.py -v
```

### Step 3: Add Configuration (Optional)

Create a configuration entry in your connector config file:

```json
{
  "myplatform": {
    "name": "myplatform",
    "display_name": "My Platform",
    "description": "Integration with My Platform",
    "enabled": true,
    "credentials": [
      {
        "key": "api_key",
        "display_name": "API Key",
        "description": "Your platform API key",
        "required": true,
        "secret": true
      }
    ],
    "features": {
      "training": true,
      "inference": true,
      "registry": false,
      "tracking": false
    }
  }
}
```

## Using Connectors

### Basic Usage

```python
from connectors.manager import ConnectorManager

# Initialize manager
manager = ConnectorManager()

# Discover connectors
manager.discover_connectors()

# List available connectors
connectors = manager.list_connectors()

# Connect to a platform
await manager.connect("myplatform", {"api_key": "your-key"})

# Submit a training job
job_id = await manager.submit_job("myplatform", training_config)

# Get connector instance
connector = manager.get_connector("myplatform")
```

### Advanced Usage

```python
# Get connectors by feature
training_connectors = manager.get_connectors_by_feature("training")

# List resources from a connector
resources = await manager.list_resources("myplatform")

# Get pricing information
pricing = await manager.get_pricing("myplatform", "resource-id")

# Disconnect
await manager.disconnect("myplatform")
```

## Validation

All connectors are automatically validated to ensure they:

1. Inherit from `PlatformConnector`
2. Have required metadata (name, display_name, description, version)
3. Implement all required methods
4. Don't have abstract methods remaining
5. Return correct types from methods

The validation happens automatically during:
- Connector registration
- Test execution
- Runtime discovery

## Error Handling

Connectors should follow these error handling guidelines:

1. **Connection Errors**: Raise `ConnectionError` for connection failures
2. **Invalid Credentials**: Raise `ValueError` for invalid credentials
3. **Invalid Configuration**: Raise `ValueError` for invalid training configs
4. **Missing Resources**: Raise `FileNotFoundError` for missing artifacts
5. **Runtime Errors**: Raise `RuntimeError` for other failures

## Testing

The connector system includes comprehensive property-based tests:

- **Property 1: Connector interface compliance** - Validates all connectors implement the required interface
- Tests verify methods don't raise `NotImplementedError`
- Tests verify correct return types
- Tests verify validation catches incomplete connectors
- Tests verify failure isolation

Run tests:
```bash
cd backend
python -m pytest tests/test_connector_interface_compliance.py -v
```

## Requirements Validation

This implementation validates:

- **Requirement 13.1**: Standard interface implementation
- **Requirement 13.2**: Automatic discovery and registration
- **Requirement 13.3**: Failure isolation between connectors

## Example: Local Connector

See `backend/plugins/connectors/local_connector.py` for a complete reference implementation.

## Next Steps

1. Implement specific platform connectors (RunPod, HuggingFace, etc.)
2. Add credential management with OS keystore
3. Implement offline queue for operations
4. Add connector configuration UI
5. Implement connector health monitoring
