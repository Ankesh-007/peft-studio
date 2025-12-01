# API Documentation

Complete reference for PEFT Studio's REST API and WebSocket endpoints.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All API requests require authentication via API key:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:8000/api/v1/jobs
```

## REST API Endpoints

### Platform Connections

#### List Platforms
```http
GET /platforms
```

**Response:**
```json
{
  "platforms": [
    {
      "name": "runpod",
      "display_name": "RunPod",
      "status": "connected",
      "features": ["training", "inference"],
      "last_verified": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### Connect Platform
```http
POST /platforms/{platform_name}/connect
```

**Request Body:**
```json
{
  "credentials": {
    "api_key": "your_api_key_here"
  }
}
```

**Response:**
```json
{
  "success": true,
  "platform": "runpod",
  "status": "connected"
}
```

#### Disconnect Platform
```http
DELETE /platforms/{platform_name}
```

**Response:**
```json
{
  "success": true,
  "message": "Platform disconnected"
}
```

### Models

#### Search Models
```http
GET /models/search?q={query}&source={source}&limit={limit}
```

**Parameters:**
- `q`: Search query
- `source`: Filter by source (huggingface, civitai, ollama)
- `limit`: Max results (default: 20)

**Response:**
```json
{
  "models": [
    {
      "id": "meta-llama/Llama-2-7b-hf",
      "name": "Llama 2 7B",
      "source": "huggingface",
      "size_gb": 13.5,
      "license": "llama2",
      "downloads": 1500000,
      "tags": ["text-generation", "llama"]
    }
  ],
  "total": 150,
  "page": 1
}
```

#### Get Model Details
```http
GET /models/{source}/{model_id}
```

**Response:**
```json
{
  "id": "meta-llama/Llama-2-7b-hf",
  "name": "Llama 2 7B",
  "source": "huggingface",
  "description": "Llama 2 7B parameter model",
  "size_gb": 13.5,
  "license": "llama2",
  "architecture": "LlamaForCausalLM",
  "context_length": 4096,
  "hardware_requirements": {
    "min_vram_gb": 16,
    "recommended_vram_gb": 24
  },
  "compatible_algorithms": ["lora", "qlora", "dora"]
}
```

### Training Jobs

#### Create Training Job
```http
POST /jobs
```

**Request Body:**
```json
{
  "config": {
    "base_model": "meta-llama/Llama-2-7b-hf",
    "model_source": "huggingface",
    "algorithm": "lora",
    "rank": 8,
    "alpha": 16,
    "dropout": 0.05,
    "target_modules": ["q_proj", "v_proj"],
    "quantization": "int4",
    "learning_rate": 2e-4,
    "batch_size": 4,
    "gradient_accumulation_steps": 4,
    "num_epochs": 3,
    "warmup_steps": 100,
    "provider": "runpod",
    "resource_id": "gpu-rtx4090",
    "dataset_path": "/path/to/dataset.json",
    "validation_split": 0.1,
    "experiment_tracker": "wandb",
    "project_name": "my-finetuning",
    "output_dir": "./output",
    "checkpoint_steps": 100
  }
}
```

**Response:**
```json
{
  "job_id": "job_abc123",
  "status": "pending",
  "created_at": "2024-01-15T10:30:00Z",
  "estimated_cost": 2.50,
  "estimated_duration_minutes": 45
}
```

#### List Jobs
```http
GET /jobs?status={status}&provider={provider}&limit={limit}
```

**Parameters:**
- `status`: Filter by status (pending, running, completed, failed)
- `provider`: Filter by provider
- `limit`: Max results (default: 20)

**Response:**
```json
{
  "jobs": [
    {
      "job_id": "job_abc123",
      "config": {...},
      "status": "running",
      "progress": 0.45,
      "created_at": "2024-01-15T10:30:00Z",
      "started_at": "2024-01-15T10:31:00Z",
      "metrics": {
        "loss": 0.523,
        "learning_rate": 0.0002,
        "epoch": 1.5
      }
    }
  ],
  "total": 10
}
```

#### Get Job Details
```http
GET /jobs/{job_id}
```

**Response:**
```json
{
  "job_id": "job_abc123",
  "config": {...},
  "status": "completed",
  "progress": 1.0,
  "created_at": "2024-01-15T10:30:00Z",
  "started_at": "2024-01-15T10:31:00Z",
  "completed_at": "2024-01-15T11:15:00Z",
  "duration_seconds": 2640,
  "cost": 2.45,
  "metrics": {
    "final_loss": 0.234,
    "best_loss": 0.221,
    "total_steps": 1000
  },
  "artifact": {
    "path": "/path/to/adapter.safetensors",
    "size_bytes": 16777216,
    "hash": "sha256:abc123..."
  }
}
```

#### Cancel Job
```http
POST /jobs/{job_id}/cancel
```

**Response:**
```json
{
  "success": true,
  "job_id": "job_abc123",
  "status": "cancelled"
}
```

#### Get Job Logs
```http
GET /jobs/{job_id}/logs?lines={lines}
```

**Parameters:**
- `lines`: Number of recent lines (default: 100)

**Response:**
```json
{
  "logs": [
    {
      "timestamp": "2024-01-15T10:31:05Z",
      "level": "INFO",
      "message": "Starting training..."
    },
    {
      "timestamp": "2024-01-15T10:31:10Z",
      "level": "INFO",
      "message": "Epoch 1/3, Step 10/1000, Loss: 0.523"
    }
  ]
}
```

### Compute Resources

#### List Resources
```http
GET /resources?provider={provider}&available={available}
```

**Parameters:**
- `provider`: Filter by provider
- `available`: Filter by availability (true/false)

**Response:**
```json
{
  "resources": [
    {
      "id": "gpu-rtx4090",
      "provider": "runpod",
      "name": "RTX 4090",
      "gpu_type": "RTX 4090",
      "gpu_count": 1,
      "vram_gb": 24,
      "cpu_cores": 16,
      "ram_gb": 64,
      "storage_gb": 500,
      "available": true,
      "pricing": {
        "hourly_rate": 0.69,
        "currency": "USD"
      }
    }
  ]
}
```

#### Get Resource Pricing
```http
GET /resources/{provider}/{resource_id}/pricing
```

**Response:**
```json
{
  "resource_id": "gpu-rtx4090",
  "provider": "runpod",
  "pricing": {
    "hourly_rate": 0.69,
    "currency": "USD",
    "billing_increment": 60,
    "minimum_charge": 0.69
  },
  "availability": {
    "available": true,
    "queue_length": 0,
    "estimated_wait_minutes": 0
  }
}
```

### Adapters

#### List Adapters
```http
GET /adapters?job_id={job_id}&limit={limit}
```

**Response:**
```json
{
  "adapters": [
    {
      "id": "adapter_xyz789",
      "job_id": "job_abc123",
      "name": "my-llama2-adapter",
      "base_model": "meta-llama/Llama-2-7b-hf",
      "algorithm": "lora",
      "path": "/path/to/adapter.safetensors",
      "size_bytes": 16777216,
      "created_at": "2024-01-15T11:15:00Z",
      "metadata": {
        "rank": 8,
        "alpha": 16,
        "target_modules": ["q_proj", "v_proj"]
      }
    }
  ]
}
```

#### Upload Adapter
```http
POST /adapters/upload
```

**Request Body (multipart/form-data):**
- `file`: Adapter file (.safetensors)
- `metadata`: JSON metadata

**Response:**
```json
{
  "adapter_id": "adapter_xyz789",
  "registry_url": "https://huggingface.co/user/model",
  "success": true
}
```

### Deployments

#### Create Deployment
```http
POST /deployments
```

**Request Body:**
```json
{
  "adapter_id": "adapter_xyz789",
  "platform": "predibase",
  "config": {
    "instance_type": "gpu-t4",
    "min_replicas": 1,
    "max_replicas": 3,
    "auto_scaling": true
  }
}
```

**Response:**
```json
{
  "deployment_id": "deploy_def456",
  "status": "deploying",
  "endpoint": null,
  "estimated_ready_time": "2024-01-15T11:20:00Z"
}
```

#### List Deployments
```http
GET /deployments?status={status}
```

**Response:**
```json
{
  "deployments": [
    {
      "deployment_id": "deploy_def456",
      "adapter_id": "adapter_xyz789",
      "platform": "predibase",
      "status": "running",
      "endpoint": "https://api.predibase.com/v1/deployments/deploy_def456",
      "created_at": "2024-01-15T11:15:00Z",
      "metrics": {
        "requests_per_minute": 45,
        "avg_latency_ms": 120,
        "cost_per_hour": 0.50
      }
    }
  ]
}
```

#### Test Deployment
```http
POST /deployments/{deployment_id}/test
```

**Request Body:**
```json
{
  "prompt": "Once upon a time",
  "max_tokens": 100,
  "temperature": 0.7
}
```

**Response:**
```json
{
  "response": "Once upon a time, in a land far away...",
  "latency_ms": 125,
  "tokens_generated": 50
}
```

### Experiments

#### List Experiments
```http
GET /experiments?tracker={tracker}&project={project}
```

**Response:**
```json
{
  "experiments": [
    {
      "id": "exp_ghi789",
      "tracker": "wandb",
      "project": "my-finetuning",
      "name": "llama2-lora-run1",
      "status": "completed",
      "metrics": {
        "final_loss": 0.234,
        "best_loss": 0.221,
        "accuracy": 0.89
      },
      "config": {...},
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### Compare Experiments
```http
POST /experiments/compare
```

**Request Body:**
```json
{
  "experiment_ids": ["exp_ghi789", "exp_jkl012"]
}
```

**Response:**
```json
{
  "comparison": {
    "metrics": {
      "loss": [0.234, 0.256],
      "accuracy": [0.89, 0.87]
    },
    "configs": [...],
    "best_performer": "exp_ghi789",
    "cost_analysis": {
      "total_costs": [2.45, 3.20],
      "cost_per_accuracy_point": [0.0275, 0.0368]
    }
  }
}
```

## WebSocket API

### Real-time Job Updates

Connect to WebSocket for real-time updates:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/jobs/{job_id}');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};
```

**Message Types:**

**Status Update:**
```json
{
  "type": "status",
  "job_id": "job_abc123",
  "status": "running",
  "timestamp": "2024-01-15T10:31:00Z"
}
```

**Metrics Update:**
```json
{
  "type": "metrics",
  "job_id": "job_abc123",
  "metrics": {
    "loss": 0.523,
    "learning_rate": 0.0002,
    "epoch": 1.5,
    "step": 150
  },
  "timestamp": "2024-01-15T10:35:00Z"
}
```

**Log Message:**
```json
{
  "type": "log",
  "job_id": "job_abc123",
  "level": "INFO",
  "message": "Epoch 1/3 completed",
  "timestamp": "2024-01-15T10:40:00Z"
}
```

**Error:**
```json
{
  "type": "error",
  "job_id": "job_abc123",
  "error": "Out of memory",
  "details": "GPU memory exceeded",
  "timestamp": "2024-01-15T10:45:00Z"
}
```

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "code": "INVALID_CONFIG",
    "message": "Training configuration is invalid",
    "details": {
      "field": "learning_rate",
      "issue": "Must be between 1e-6 and 1e-2"
    }
  }
}
```

### Error Codes

- `INVALID_CONFIG`: Configuration validation failed
- `PLATFORM_NOT_CONNECTED`: Platform not connected
- `INSUFFICIENT_CREDITS`: Insufficient credits on platform
- `RESOURCE_UNAVAILABLE`: Requested resource not available
- `JOB_NOT_FOUND`: Job ID not found
- `RATE_LIMIT_EXCEEDED`: API rate limit exceeded
- `AUTHENTICATION_FAILED`: Invalid API key
- `INTERNAL_ERROR`: Internal server error

## Rate Limits

- **REST API**: 100 requests per minute per API key
- **WebSocket**: 10 concurrent connections per API key

## SDK Examples

### Python

```python
import requests

class PEFTStudioClient:
    def __init__(self, api_key: str):
        self.base_url = "http://localhost:8000/api/v1"
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    def create_job(self, config: dict) -> str:
        response = requests.post(
            f"{self.base_url}/jobs",
            json={"config": config},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()["job_id"]
    
    def get_job_status(self, job_id: str) -> dict:
        response = requests.get(
            f"{self.base_url}/jobs/{job_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# Usage
client = PEFTStudioClient("your_api_key")
job_id = client.create_job({...})
status = client.get_job_status(job_id)
```

### JavaScript

```javascript
class PEFTStudioClient {
  constructor(apiKey) {
    this.baseUrl = 'http://localhost:8000/api/v1';
    this.apiKey = apiKey;
  }
  
  async createJob(config) {
    const response = await fetch(`${this.baseUrl}/jobs`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ config })
    });
    
    if (!response.ok) throw new Error('Job creation failed');
    const data = await response.json();
    return data.job_id;
  }
  
  async getJobStatus(jobId) {
    const response = await fetch(`${this.baseUrl}/jobs/${jobId}`, {
      headers: {
        'Authorization': `Bearer ${this.apiKey}`
      }
    });
    
    if (!response.ok) throw new Error('Failed to get job status');
    return await response.json();
  }
}

// Usage
const client = new PEFTStudioClient('your_api_key');
const jobId = await client.createJob({...});
const status = await client.getJobStatus(jobId);
```

## Changelog

### v1.0.0 (2024-01-15)
- Initial API release
- Support for all major platforms
- WebSocket real-time updates
- Comprehensive error handling
