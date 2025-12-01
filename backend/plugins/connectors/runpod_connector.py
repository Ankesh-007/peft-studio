"""
RunPod connector for cloud GPU training.

This connector integrates with RunPod's API to provision GPU instances,
submit training jobs, stream logs, and download artifacts.

RunPod API Documentation: https://docs.runpod.io/
"""

from typing import Dict, List, AsyncIterator, Optional
import asyncio
import aiohttp
import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from connectors.base import (
    PlatformConnector,
    Resource,
    ResourceType,
    PricingInfo,
    TrainingConfig,
    JobStatus,
)


class RunPodConnector(PlatformConnector):
    """
    Connector for RunPod cloud GPU platform.
    
    RunPod provides on-demand GPU instances for ML training and inference.
    This connector handles:
    - GPU instance provisioning
    - Job submission and monitoring
    - Real-time log streaming via WebSocket
    - Artifact download
    - Pricing and availability queries
    """
    
    # Connector metadata
    name = "runpod"
    display_name = "RunPod"
    description = "Cloud GPU training on RunPod with on-demand instances"
    version = "1.0.0"
    
    # Supported features
    supports_training = True
    supports_inference = True
    supports_registry = False
    supports_tracking = False
    
    # API endpoints
    BASE_URL = "https://api.runpod.io/v2"
    GRAPHQL_URL = "https://api.runpod.io/graphql"
    
    def __init__(self):
        self._api_key: Optional[str] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        self._jobs: Dict[str, Dict] = {}
    
    async def connect(self, credentials: Dict[str, str]) -> bool:
        """
        Verify connection and store credentials.
        
        Args:
            credentials: Dictionary with 'api_key'
            
        Returns:
            True if connection successful
            
        Raises:
            ConnectionError: If connection fails
            ValueError: If credentials are invalid
        """
        api_key = credentials.get("api_key")
        if not api_key:
            raise ValueError("api_key is required")
        
        self._api_key = api_key
        
        # Create session with headers
        self._session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            }
        )
        
        # Verify connection by fetching user info
        try:
            async with self._session.post(
                self.GRAPHQL_URL,
                json={
                    "query": "query { myself { id } }"
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "data" in data and "myself" in data["data"]:
                        self._connected = True
                        return True
                    else:
                        raise ConnectionError("Invalid API response")
                elif response.status == 401:
                    raise ValueError("Invalid API key")
                else:
                    raise ConnectionError(f"Connection failed with status {response.status}")
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Failed to connect to RunPod: {str(e)}")
    
    async def disconnect(self) -> bool:
        """Disconnect and cleanup resources."""
        if self._session:
            await self._session.close()
            self._session = None
        
        self._connected = False
        self._api_key = None
        self._jobs.clear()
        return True
    
    async def verify_connection(self) -> bool:
        """Verify that the connection is still valid."""
        if not self._connected or not self._session:
            return False
        
        try:
            async with self._session.post(
                self.GRAPHQL_URL,
                json={
                    "query": "query { myself { id } }"
                }
            ) as response:
                return response.status == 200
        except:
            return False
    
    async def submit_job(self, config: TrainingConfig) -> str:
        """
        Submit a training job to RunPod.
        
        This provisions a GPU instance, sets up the training environment,
        and starts the training job.
        
        Args:
            config: Training configuration
            
        Returns:
            Job ID for tracking
            
        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If job submission fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to RunPod")
        
        # Validate configuration
        self.validate_config(config)
        
        # Build training script
        training_script = self._build_training_script(config)
        
        # Create pod configuration
        pod_config = {
            "cloudType": "SECURE",
            "gpuTypeId": config.resource_id or "NVIDIA RTX A4000",
            "name": f"peft-training-{config.project_name}",
            "dockerArgs": f"python -c '{training_script}'",
            "imageName": "runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel",
            "volumeInGb": 50,
            "containerDiskInGb": 20,
            "env": [
                {"key": "WANDB_API_KEY", "value": ""},  # Will be set if tracking enabled
                {"key": "HF_TOKEN", "value": ""},  # For model download
            ]
        }
        
        # Submit pod creation request
        try:
            async with self._session.post(
                self.GRAPHQL_URL,
                json={
                    "query": """
                        mutation($input: PodFindAndDeployOnDemandInput!) {
                            podFindAndDeployOnDemand(input: $input) {
                                id
                                desiredStatus
                                imageName
                                env
                                machineId
                                machine {
                                    gpuDisplayName
                                }
                            }
                        }
                    """,
                    "variables": {
                        "input": pod_config
                    }
                }
            ) as response:
                if response.status != 200:
                    raise RuntimeError(f"Failed to create pod: {response.status}")
                
                data = await response.json()
                
                if "errors" in data:
                    raise RuntimeError(f"GraphQL errors: {data['errors']}")
                
                pod_data = data["data"]["podFindAndDeployOnDemand"]
                job_id = pod_data["id"]
                
                # Store job info
                self._jobs[job_id] = {
                    "config": config,
                    "status": JobStatus.PENDING,
                    "pod_id": job_id,
                    "logs": [],
                }
                
                return job_id
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to submit job: {str(e)}")
    
    def _build_training_script(self, config: TrainingConfig) -> str:
        """Build Python training script from configuration."""
        script = f"""
import os
import sys

# Install dependencies
os.system('pip install -q unsloth transformers datasets accelerate peft')

# Import libraries
from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments

# Load model
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name='{config.base_model}',
    max_seq_length=2048,
    dtype=None,
    load_in_4bit={str(config.quantization == 'int4').lower()},
)

# Configure PEFT
model = FastLanguageModel.get_peft_model(
    model,
    r={config.rank},
    target_modules={config.target_modules},
    lora_alpha={config.alpha},
    lora_dropout={config.dropout},
    bias='none',
    use_gradient_checkpointing=True,
)

# Load dataset
dataset = load_dataset('json', data_files='{config.dataset_path}', split='train')

# Training arguments
training_args = TrainingArguments(
    output_dir='{config.output_dir}',
    per_device_train_batch_size={config.batch_size},
    gradient_accumulation_steps={config.gradient_accumulation_steps},
    warmup_steps={config.warmup_steps},
    num_train_epochs={config.num_epochs},
    learning_rate={config.learning_rate},
    fp16=True,
    logging_steps=10,
    save_steps={config.checkpoint_steps},
    save_total_limit=2,
)

# Create trainer
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    args=training_args,
    max_seq_length=2048,
)

# Train
print('Starting training...')
trainer.train()

# Save adapter
print('Saving adapter...')
model.save_pretrained('{config.output_dir}/adapter')
tokenizer.save_pretrained('{config.output_dir}/adapter')

print('Training complete!')
"""
        return script.replace('\n', '\\n').replace('"', '\\"')
    
    async def get_job_status(self, job_id: str) -> JobStatus:
        """
        Get the current status of a training job.
        
        Args:
            job_id: Job identifier (pod ID)
            
        Returns:
            Current job status
        """
        if not self._connected:
            raise RuntimeError("Not connected to RunPod")
        
        try:
            async with self._session.post(
                self.GRAPHQL_URL,
                json={
                    "query": """
                        query($podId: String!) {
                            pod(input: {podId: $podId}) {
                                id
                                desiredStatus
                                runtime {
                                    uptimeInSeconds
                                }
                            }
                        }
                    """,
                    "variables": {
                        "podId": job_id
                    }
                }
            ) as response:
                if response.status != 200:
                    return JobStatus.FAILED
                
                data = await response.json()
                
                if "errors" in data:
                    return JobStatus.FAILED
                
                pod = data["data"]["pod"]
                status = pod["desiredStatus"]
                
                # Map RunPod status to JobStatus
                status_map = {
                    "RUNNING": JobStatus.RUNNING,
                    "EXITED": JobStatus.COMPLETED,
                    "FAILED": JobStatus.FAILED,
                    "STOPPED": JobStatus.CANCELLED,
                }
                
                return status_map.get(status, JobStatus.PENDING)
                
        except aiohttp.ClientError:
            return JobStatus.FAILED
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running training job.
        
        Args:
            job_id: Job identifier (pod ID)
            
        Returns:
            True if cancellation successful
        """
        if not self._connected:
            raise RuntimeError("Not connected to RunPod")
        
        try:
            async with self._session.post(
                self.GRAPHQL_URL,
                json={
                    "query": """
                        mutation($podId: String!) {
                            podStop(input: {podId: $podId}) {
                                id
                                desiredStatus
                            }
                        }
                    """,
                    "variables": {
                        "podId": job_id
                    }
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return "errors" not in data
                return False
                
        except aiohttp.ClientError:
            return False
    
    async def stream_logs(self, job_id: str) -> AsyncIterator[str]:
        """
        Stream logs from a training job in real-time via WebSocket.
        
        Args:
            job_id: Job identifier (pod ID)
            
        Yields:
            Log lines as they become available
        """
        if not self._connected:
            raise RuntimeError("Not connected to RunPod")
        
        # RunPod WebSocket endpoint for logs
        ws_url = f"wss://api.runpod.io/v2/{job_id}/logs"
        
        try:
            async with self._session.ws_connect(
                ws_url,
                headers={"Authorization": f"Bearer {self._api_key}"}
            ) as ws:
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        if "log" in data:
                            yield data["log"]
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        break
        except Exception as e:
            # Fallback to polling logs if WebSocket fails
            yield f"WebSocket connection failed, falling back to polling: {str(e)}"
            
            # Poll logs every 2 seconds
            while True:
                status = await self.get_job_status(job_id)
                if status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                    break
                
                # Fetch logs via REST API
                try:
                    async with self._session.get(
                        f"{self.BASE_URL}/{job_id}/logs"
                    ) as response:
                        if response.status == 200:
                            logs = await response.text()
                            for line in logs.split('\n'):
                                if line.strip():
                                    yield line
                except:
                    pass
                
                await asyncio.sleep(2)
    
    async def fetch_artifact(self, job_id: str) -> bytes:
        """
        Download the trained adapter artifact.
        
        Args:
            job_id: Job identifier (pod ID)
            
        Returns:
            Artifact data as bytes
            
        Raises:
            FileNotFoundError: If artifact doesn't exist
            RuntimeError: If download fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to RunPod")
        
        # Check job is completed
        status = await self.get_job_status(job_id)
        if status != JobStatus.COMPLETED:
            raise RuntimeError(f"Job not completed, status: {status.value}")
        
        # Download artifact from pod storage
        # RunPod stores outputs in /workspace/output by default
        artifact_url = f"{self.BASE_URL}/{job_id}/files/output/adapter"
        
        try:
            async with self._session.get(artifact_url) as response:
                if response.status == 404:
                    raise FileNotFoundError(f"Artifact not found for job {job_id}")
                elif response.status != 200:
                    raise RuntimeError(f"Failed to download artifact: {response.status}")
                
                return await response.read()
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to download artifact: {str(e)}")
    
    async def upload_artifact(self, path: str, metadata: Dict) -> str:
        """
        Upload an adapter to RunPod storage.
        
        Args:
            path: Local path to artifact
            metadata: Artifact metadata
            
        Returns:
            Artifact URL
            
        Raises:
            FileNotFoundError: If local file doesn't exist
            RuntimeError: If upload fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to RunPod")
        
        # Check file exists
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        # Upload to RunPod storage
        upload_url = f"{self.BASE_URL}/upload"
        
        try:
            with open(file_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename=file_path.name)
                data.add_field('metadata', json.dumps(metadata))
                
                async with self._session.post(upload_url, data=data) as response:
                    if response.status != 200:
                        raise RuntimeError(f"Upload failed: {response.status}")
                    
                    result = await response.json()
                    return result.get("url", "")
                    
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to upload artifact: {str(e)}")
    
    async def list_resources(self) -> List[Resource]:
        """
        List available GPU resources on RunPod.
        
        Returns:
            List of available GPU resources
        """
        if not self._connected:
            raise RuntimeError("Not connected to RunPod")
        
        try:
            async with self._session.post(
                self.GRAPHQL_URL,
                json={
                    "query": """
                        query {
                            gpuTypes {
                                id
                                displayName
                                memoryInGb
                                secureCloud
                                communityCloud
                                lowestPrice {
                                    minimumBidPrice
                                    uninterruptablePrice
                                }
                            }
                        }
                    """
                }
            ) as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                
                if "errors" in data:
                    return []
                
                resources = []
                for gpu in data["data"]["gpuTypes"]:
                    # Only include GPUs available in secure cloud
                    if gpu["secureCloud"]:
                        resources.append(Resource(
                            id=gpu["id"],
                            name=gpu["displayName"],
                            type=ResourceType.GPU,
                            gpu_type=gpu["displayName"],
                            gpu_count=1,
                            vram_gb=gpu["memoryInGb"],
                            available=True,
                            region="runpod-cloud",
                        ))
                
                return resources
                
        except aiohttp.ClientError:
            return []
    
    async def get_pricing(self, resource_id: str) -> PricingInfo:
        """
        Get pricing information for a specific GPU resource.
        
        Args:
            resource_id: GPU type ID
            
        Returns:
            Pricing information
            
        Raises:
            ValueError: If resource_id is invalid
        """
        if not self._connected:
            raise RuntimeError("Not connected to RunPod")
        
        try:
            async with self._session.post(
                self.GRAPHQL_URL,
                json={
                    "query": """
                        query($gpuTypeId: String!) {
                            gpuTypes(input: {id: $gpuTypeId}) {
                                id
                                displayName
                                lowestPrice {
                                    minimumBidPrice
                                    uninterruptablePrice
                                }
                            }
                        }
                    """,
                    "variables": {
                        "gpuTypeId": resource_id
                    }
                }
            ) as response:
                if response.status != 200:
                    raise ValueError(f"Invalid resource ID: {resource_id}")
                
                data = await response.json()
                
                if "errors" in data or not data["data"]["gpuTypes"]:
                    raise ValueError(f"Invalid resource ID: {resource_id}")
                
                gpu = data["data"]["gpuTypes"][0]
                pricing = gpu["lowestPrice"]
                
                return PricingInfo(
                    resource_id=resource_id,
                    price_per_hour=pricing["uninterruptablePrice"],
                    currency="USD",
                    billing_increment_seconds=60,
                    minimum_charge_seconds=60,
                    spot_available=True,
                    spot_price_per_hour=pricing["minimumBidPrice"],
                )
                
        except aiohttp.ClientError as e:
            raise ValueError(f"Failed to get pricing: {str(e)}")
    
    def get_required_credentials(self) -> List[str]:
        """Get list of required credential keys."""
        return ["api_key"]
