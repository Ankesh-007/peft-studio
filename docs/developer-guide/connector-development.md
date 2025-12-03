# Connector Development Guide

Learn how to create custom connectors for PEFT Studio.

## Overview

Connectors are pluggable modules that integrate external platforms with PEFT Studio. Each connector implements a standard interface for:
- Authentication and connection management
- Job submission and monitoring
- Artifact upload and download
- Resource listing and pricing

## Connector Architecture

```
┌─────────────────────────────────────┐
│     PEFT Studio Core                │
│  ┌──────────────────────────────┐   │
│  │   Connector Manager          │   │
│  │  - Discovery                 │   │
│  │  - Registration              │   │
│  │  - Lifecycle Management      │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
              │
    ┌─────────┴─────────┐
    │                   │
┌───▼────┐        ┌────▼────┐
│Custom  │        │Built-in │
│Connector│       │Connector│
└────────┘        └─────────┘
```

## Creating a Connector

### Step 1: Create Connector File

Create a new file in `backend/plugins/connectors/`:

```python
# backend/plugins/connectors/my_platform_connector.py
from typing import Dict, List, AsyncIterator, Optional
from connectors.base import (
    PlatformConnector, 
    Resource, 
    PricingInfo,
    TrainingConfig
)
import aiohttp

class MyPlatformConnector(PlatformConnector):
    """Connector for My Platform"""
    
    # Connector metadata
    name = "myplatform"
    display_name = "My Platform"
    description = "Integration with My Platform for training"
    version = "1.0.0"
    
    # Supported features
    supports_training = True
    supports_inference = True
    supports_registry = False
    
    def __init__(self):
        super().__init__()
        self.api_key: Optional[str] = None
        self.base_url = "https://api.myplatform.com/v1"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def connect(self, credentials: Dict[str, str]) -> bool:
        """
        Verify connection and store credentials.
        
        Args:
            credentials: Dictionary with 'api_key' and other required fields
            
        Returns:
            True if connection successful, False otherwise
        """
        self.api_key = credentials.get("api_key")
        
        if not self.api_key:
            raise ValueError("API key is required")
        
        # Create HTTP session
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        # Verify connection
        try:
            async with self.session.get(f"{self.base_url}/verify") as response:
                if response.status == 200:
                    return True
                else:
                    error = await response.text()
                    raise ConnectionError(f"Connection failed: {error}")
        except Exception as e:
            await self.disconnect()
            raise ConnectionError(f"Failed to connect: {str(e)}")
    
    async def disconnect(self) -> None:
        """Clean up resources"""
        if self.session:
            await self.session.close()
            self.session = None
        self.api_key = None
    
    async def submit_job(self, config: TrainingConfig) -> str:
        """
        Submit training job to platform.
        
        Args:
            config: Training configuration
            
        Returns:
            Job ID string
        """
        if not self.session:
            raise RuntimeError("Not connected")
        
        # Build job payload
        payload = {
            "model": config.base_model,
            "algorithm": config.algorithm,
            "rank": config.rank,
            "alpha": config.alpha,
            "learning_rate": config.learning_rate,
            "batch_size": config.batch_size,
            "num_epochs": config.num_epochs,
            "dataset": config.dataset_path,
        }
        
        # Submit job
        async with self.session.post(
            f"{self.base_url}/jobs",
            json=payload
        ) as response:
            if response.status == 201:
                data = await response.json()
                return data["job_id"]
            else:
                error = await response.text()
                raise RuntimeError(f"Job submission failed: {error}")
    
    async def get_job_status(self, job_id: str) -> str:
        """
        Get current job status.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Status string: 'pending', 'running', 'completed', 'failed'
        """
        if not self.session:
            raise RuntimeError("Not connected")
        
        async with self.session.get(
            f"{self.base_url}/jobs/{job_id}"
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data["status"]
            else:
                raise RuntimeError(f"Failed to get job status")
    
    async def stream_logs(self, job_id: str) -> AsyncIterator[str]:
        """
        Stream logs in real-time.
        
        Args:
            job_id: Job identifier
            
        Yields:
            Log lines as strings
        """
        if not self.session:
            raise RuntimeError("Not connected")
        
        # Connect to WebSocket for log streaming
        ws_url = f"wss://api.myplatform.com/v1/jobs/{job_id}/logs"
        
        async with self.session.ws_connect(ws_url) as ws:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    yield msg.data
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    break
    
    async def fetch_artifact(self, job_id: str) -> bytes:
        """
        Download trained adapter artifact.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Artifact bytes
        """
        if not self.session:
            raise RuntimeError("Not connected")
        
        async with self.session.get(
            f"{self.base_url}/jobs/{job_id}/artifact"
        ) as response:
            if response.status == 200:
                return await response.read()
            else:
                raise RuntimeError("Failed to download artifact")
    
    async def upload_artifact(
        self, 
        path: str, 
        metadata: Dict
    ) -> str:
        """
        Upload adapter to platform registry.
        
        Args:
            path: Local file path
            metadata: Model metadata
            
        Returns:
            Artifact ID or URL
        """
        if not self.session:
            raise RuntimeError("Not connected")
        
        # Read file
        with open(path, 'rb') as f:
            data = f.read()
        
        # Upload
        form = aiohttp.FormData()
        form.add_field('file', data, filename='adapter.safetensors')
        form.add_field('metadata', str(metadata))
        
        async with self.session.post(
            f"{self.base_url}/artifacts",
            data=form
        ) as response:
            if response.status == 201:
                result = await response.json()
                return result["artifact_id"]
            else:
                raise RuntimeError("Failed to upload artifact")
    
    async def list_resources(self) -> List[Resource]:
        """
        List available compute resources.
        
        Returns:
            List of Resource objects
        """
        if not self.session:
            raise RuntimeError("Not connected")
        
        async with self.session.get(
            f"{self.base_url}/resources"
        ) as response:
            if response.status == 200:
                data = await response.json()
                return [
                    Resource(
                        id=r["id"],
                        name=r["name"],
                        gpu_type=r["gpu_type"],
                        gpu_count=r["gpu_count"],
                        vram_gb=r["vram_gb"],
                        available=r["available"]
                    )
                    for r in data["resources"]
                ]
            else:
                raise RuntimeError("Failed to list resources")
    
    async def get_pricing(self, resource_id: str) -> PricingInfo:
        """
        Get pricing for specific resource.
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            PricingInfo object
        """
        if not self.session:
            raise RuntimeError("Not connected")
        
        async with self.session.get(
            f"{self.base_url}/resources/{resource_id}/pricing"
        ) as response:
            if response.status == 200:
                data = await response.json()
                return PricingInfo(
                    hourly_rate=data["hourly_rate"],
                    currency=data["currency"],
                    billing_increment=data.get("billing_increment", 60)
                )
            else:
                raise RuntimeError("Failed to get pricing")
```

### Step 2: Register Connector

The connector is automatically discovered if placed in `backend/plugins/connectors/`. Alternatively, register manually:

```python
# backend/connectors/__init__.py
from plugins.connectors.my_platform_connector import MyPlatformConnector

CONNECTORS = [
    MyPlatformConnector,
    # ... other connectors
]
```

### Step 3: Add Configuration

Create connector configuration:

```json
// config/connectors.json
{
  "myplatform": {
    "enabled": true,
    "credentials_required": ["api_key"],
    "features": ["training", "inference"],
    "documentation_url": "https://docs.myplatform.com",
    "rate_limits": {
      "requests_per_minute": 60,
      "concurrent_jobs": 5
    }
  }
}
```

## Testing Your Connector

### Unit Tests

```python
# backend/tests/test_my_platform_connector.py
import pytest
from plugins.connectors.my_platform_connector import MyPlatformConnector
from connectors.base import TrainingConfig

@pytest.fixture
async def connector():
    """Create and connect connector"""
    conn = MyPlatformConnector()
    await conn.connect({"api_key": "test_key"})
    yield conn
    await conn.disconnect()

@pytest.mark.asyncio
async def test_connection():
    """Test connection verification"""
    conn = MyPlatformConnector()
    result = await conn.connect({"api_key": "valid_key"})
    assert result is True
    await conn.disconnect()

@pytest.mark.asyncio
async def test_submit_job(connector):
    """Test job submission"""
    config = TrainingConfig(
        base_model="test-model",
        algorithm="lora",
        rank=8,
        alpha=16,
        learning_rate=2e-4,
        batch_size=4,
        num_epochs=3,
        dataset_path="/path/to/dataset"
    )
    
    job_id = await connector.submit_job(config)
    assert job_id is not None
    assert isinstance(job_id, str)

@pytest.mark.asyncio
async def test_stream_logs(connector):
    """Test log streaming"""
    logs = []
    async for log in connector.stream_logs("test_job_id"):
        logs.append(log)
        if len(logs) >= 10:
            break
    
    assert len(logs) > 0

@pytest.mark.asyncio
async def test_list_resources(connector):
    """Test resource listing"""
    resources = await connector.list_resources()
    assert len(resources) > 0
    assert all(hasattr(r, 'gpu_type') for r in resources)
```

### Integration Tests

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_training_workflow():
    """Test complete training workflow"""
    connector = MyPlatformConnector()
    
    # Connect
    await connector.connect({"api_key": os.getenv("MY_PLATFORM_API_KEY")})
    
    # Submit job
    config = TrainingConfig(...)
    job_id = await connector.submit_job(config)
    
    # Monitor until complete
    while True:
        status = await connector.get_job_status(job_id)
        if status in ['completed', 'failed']:
            break
        await asyncio.sleep(10)
    
    assert status == 'completed'
    
    # Download artifact
    artifact = await connector.fetch_artifact(job_id)
    assert len(artifact) > 0
    
    await connector.disconnect()
```

## Best Practices

### Error Handling

```python
async def submit_job(self, config: TrainingConfig) -> str:
    """Submit job with proper error handling"""
    try:
        # Validate config
        self._validate_config(config)
        
        # Submit job
        response = await self._make_request("/jobs", method="POST", json=payload)
        
        # Handle response
        if response.status == 201:
            return response.json()["job_id"]
        elif response.status == 429:
            raise RateLimitError("Rate limit exceeded")
        elif response.status == 402:
            raise InsufficientCreditsError("Insufficient credits")
        else:
            raise RuntimeError(f"Unexpected error: {response.status}")
            
    except aiohttp.ClientError as e:
        raise ConnectionError(f"Network error: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Job submission failed: {str(e)}")
```

### Rate Limiting

```python
from asyncio import Semaphore
from time import time

class MyPlatformConnector(PlatformConnector):
    def __init__(self):
        super().__init__()
        self.rate_limiter = Semaphore(10)  # Max 10 concurrent requests
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
    
    async def _make_request(self, endpoint: str, **kwargs):
        """Make rate-limited request"""
        async with self.rate_limiter:
            # Enforce minimum interval
            now = time()
            elapsed = now - self.last_request_time
            if elapsed < self.min_request_interval:
                await asyncio.sleep(self.min_request_interval - elapsed)
            
            # Make request
            response = await self.session.request(
                url=f"{self.base_url}{endpoint}",
                **kwargs
            )
            
            self.last_request_time = time()
            return response
```

### Retry Logic

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

class MyPlatformConnector(PlatformConnector):
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(aiohttp.ClientError)
    )
    async def submit_job(self, config: TrainingConfig) -> str:
        """Submit job with automatic retry"""
        # Implementation
        pass
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

class MyPlatformConnector(PlatformConnector):
    async def submit_job(self, config: TrainingConfig) -> str:
        """Submit job with logging"""
        logger.info(f"Submitting job for model {config.base_model}")
        
        try:
            job_id = await self._submit_job_impl(config)
            logger.info(f"Job submitted successfully: {job_id}")
            return job_id
        except Exception as e:
            logger.error(f"Job submission failed: {str(e)}", exc_info=True)
            raise
```

## Connector Interface Reference

### Required Methods

All connectors must implement:

- `connect(credentials)`: Verify and establish connection
- `disconnect()`: Clean up resources
- `submit_job(config)`: Submit training job
- `get_job_status(job_id)`: Get job status
- `stream_logs(job_id)`: Stream real-time logs
- `fetch_artifact(job_id)`: Download trained adapter
- `upload_artifact(path, metadata)`: Upload to registry
- `list_resources()`: List available compute
- `get_pricing(resource_id)`: Get pricing info

### Optional Methods

Connectors may implement:

- `cancel_job(job_id)`: Cancel running job
- `pause_job(job_id)`: Pause job execution
- `resume_job(job_id)`: Resume paused job
- `get_metrics(job_id)`: Get training metrics
- `search_models(query)`: Search model registry
- `get_model_metadata(model_id)`: Get model details

## Publishing Your Connector

1. **Test Thoroughly**: Ensure all tests pass
2. **Document**: Add README with usage examples
3. **Version**: Follow semantic versioning
4. **Submit PR**: Create pull request to main repository
5. **Review**: Address feedback from maintainers

## Examples

See existing connectors for reference:
- [RunPod Connector](../../backend/plugins/connectors/runpod_connector.py)
- [HuggingFace Connector](../../backend/plugins/connectors/huggingface_connector.py)
- [Weights & Biases Connector](../../backend/plugins/connectors/wandb_connector.py)

## Support

- **Questions**: Open a discussion on GitHub
- **Bugs**: Report issues with connector template
- **Feature Requests**: Suggest improvements to connector API
