# Training Orchestrator API Documentation

## Overview

The Training Orchestrator API provides endpoints for managing training jobs across multiple providers, including job submission, monitoring, artifact management, and cancellation.

**Requirements:** 5.1, 5.2, 5.3, 5.4, 5.5

## Endpoints

### Submit Job to Provider

Submit a training job to a specific cloud provider.

**Endpoint:** `POST /api/training/jobs/{job_id}/submit`

**Requirements:** 5.1, 5.2

**Request Body:**
```json
{
  "provider": "runpod"  // or "lambda", "vastai", "local"
}
```

**Response:**
```json
{
  "job_id": "job_123",
  "provider": "runpod",
  "provider_job_id": "runpod_job_456",
  "state": "running",
  "started_at": "2024-01-15T10:30:00Z"
}
```

**Status Codes:**
- `200 OK`: Job submitted successfully
- `404 Not Found`: Job not found
- `400 Bad Request`: Invalid provider or job state
- `500 Internal Server Error`: Submission failed

---

### Get Job Status

Get the current status of a training job.

**Endpoint:** `GET /api/training/jobs/{job_id}/status`

**Requirements:** 5.3

**Response:**
```json
{
  "job_id": "job_123",
  "state": "running",
  "provider": "runpod",
  "provider_job_id": "runpod_job_456",
  "current_metrics": {
    "step": 1000,
    "epoch": 1,
    "loss": 0.5,
    "learning_rate": 0.0002
  },
  "started_at": "2024-01-15T10:30:00Z",
  "artifact_info": null
}
```

---

### Cancel Job

Cancel a running training job.

**Endpoint:** `POST /api/training/jobs/{job_id}/cancel`

**Requirements:** 5.4

**Response:**
```json
{
  "job_id": "job_123",
  "state": "stopped",
  "completed_at": "2024-01-15T11:00:00Z",
  "message": "Job cancelled successfully"
}
```

**Status Codes:**
- `200 OK`: Job cancelled successfully
- `404 Not Found`: Job not found
- `400 Bad Request`: Job cannot be cancelled in current state
- `500 Internal Server Error`: Cancellation failed

---

### Download Artifact

Download the trained adapter artifact from a provider.

**Endpoint:** `POST /api/training/jobs/{job_id}/download-artifact`

**Requirements:** 5.5

**Response:**
```json
{
  "artifact_id": "job_123_artifact",
  "job_id": "job_123",
  "path": "/artifacts/job_123/adapter_model.safetensors",
  "size_bytes": 1048576,
  "hash_sha256": "abc123...",
  "created_at": "2024-01-15T11:00:00Z",
  "metadata": {
    "provider": "runpod",
    "provider_job_id": "runpod_job_456",
    "model_name": "llama-2-7b",
    "peft_method": "lora"
  }
}
```

**Status Codes:**
- `200 OK`: Artifact downloaded successfully
- `404 Not Found`: Job not found or artifact not available
- `400 Bad Request`: Job is not on a provider
- `500 Internal Server Error`: Download failed

---

### List Jobs

List all training jobs.

**Endpoint:** `GET /api/training/jobs`

**Query Parameters:**
- `provider` (optional): Filter by provider
- `state` (optional): Filter by state

**Response:**
```json
{
  "jobs": [
    {
      "job_id": "job_123",
      "state": "running",
      "provider": "runpod",
      "started_at": "2024-01-15T10:30:00Z"
    },
    {
      "job_id": "job_124",
      "state": "completed",
      "provider": "lambda",
      "completed_at": "2024-01-15T10:45:00Z"
    }
  ],
  "total": 2
}
```

---

## Usage Examples

### Submit a job to RunPod

```python
import requests

response = requests.post(
    "http://localhost:8000/api/training/jobs/my_job_123/submit",
    json={"provider": "runpod"}
)

if response.status_code == 200:
    data = response.json()
    print(f"Job submitted: {data['provider_job_id']}")
```

### Monitor job status

```python
import requests
import time

job_id = "my_job_123"

while True:
    response = requests.get(
        f"http://localhost:8000/api/training/jobs/{job_id}/status"
    )
    
    data = response.json()
    state = data['state']
    
    print(f"Job state: {state}")
    
    if state in ['completed', 'failed', 'stopped']:
        break
    
    time.sleep(10)
```

### Download artifact after completion

```python
import requests

job_id = "my_job_123"

response = requests.post(
    f"http://localhost:8000/api/training/jobs/{job_id}/download-artifact"
)

if response.status_code == 200:
    artifact_info = response.json()
    print(f"Artifact downloaded: {artifact_info['path']}")
    print(f"Hash: {artifact_info['hash_sha256']}")
```

### Cancel a running job

```python
import requests

job_id = "my_job_123"

response = requests.post(
    f"http://localhost:8000/api/training/jobs/{job_id}/cancel"
)

if response.status_code == 200:
    print("Job cancelled successfully")
```

## Error Handling

All endpoints return standard error responses:

```json
{
  "error": "Error message",
  "detail": "Detailed error information",
  "job_id": "job_123"
}
```

## WebSocket Support

For real-time updates, connect to the WebSocket endpoint:

**Endpoint:** `ws://localhost:8000/ws/training/jobs/{job_id}`

**Messages:**
```json
{
  "type": "metrics",
  "data": {
    "step": 1000,
    "loss": 0.5,
    "learning_rate": 0.0002
  }
}
```

```json
{
  "type": "status",
  "data": {
    "state": "completed",
    "completed_at": "2024-01-15T11:00:00Z"
  }
}
```

```json
{
  "type": "notification",
  "data": {
    "title": "Training Complete!",
    "message": "Your model training has finished successfully."
  }
}
```

## Integration with Connectors

The orchestrator automatically uses the appropriate connector based on the provider:

- `runpod` → RunPodConnector
- `lambda` → LambdaLabsConnector
- `vastai` → VastAIConnector
- `local` → Local training (no connector)

Each connector implements the standard interface for job submission, monitoring, and artifact management.

## Artifact Integrity

All downloaded artifacts are verified using SHA256 hashing to ensure integrity:

1. Artifact is downloaded from provider
2. SHA256 hash is calculated
3. Hash is stored in artifact metadata
4. Future verifications can compare against stored hash

**Property 7:** For any downloaded adapter, the file hash should match the hash provided by the training platform.

## Best Practices

1. **Always check job state** before performing operations
2. **Download artifacts immediately** after job completion
3. **Store artifact hashes** for integrity verification
4. **Handle provider failures** gracefully with retries
5. **Monitor job status** regularly during training
6. **Clean up completed jobs** to free resources

## Multi-Provider Support

The orchestrator supports running jobs on multiple providers simultaneously:

```python
# Submit jobs to different providers
orchestrator.start_training("job_1", provider="runpod")
orchestrator.start_training("job_2", provider="lambda")
orchestrator.start_training("job_3", provider="local")

# All jobs are tracked independently
jobs = orchestrator.list_jobs()
```

## State Machine

Job states:
- `created` → Initial state
- `initializing` → Setting up resources
- `running` → Training in progress
- `paused` → Temporarily paused (local only)
- `completed` → Successfully finished
- `failed` → Error occurred
- `stopped` → Manually cancelled

Valid transitions:
- `created` → `initializing` → `running`
- `running` → `completed` | `failed` | `stopped`
- `running` → `paused` → `running` (local only)
