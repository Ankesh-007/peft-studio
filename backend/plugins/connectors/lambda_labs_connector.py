"""
Lambda Labs connector for cloud GPU training.

This connector integrates with Lambda Labs' API to provision H100/A100 instances,
submit training jobs, stream logs via SSH, and download artifacts via SCP.

Lambda Labs API Documentation: https://docs.lambdalabs.com/
"""

from typing import Dict, List, AsyncIterator, Optional
import asyncio
import aiohttp
import json
from pathlib import Path
import sys
import paramiko
import scp as scp_module
from io import BytesIO
import tempfile
import os

sys.path.append(str(Path(__file__).parent.parent.parent))

from connectors.base import (
    PlatformConnector,
    Resource,
    ResourceType,
    PricingInfo,
    TrainingConfig,
    JobStatus,
)


class LambdaLabsConnector(PlatformConnector):
    """
    Connector for Lambda Labs cloud GPU platform.
    
    Lambda Labs provides high-performance H100/A100 GPU instances at competitive prices.
    This connector handles:
    - H100/A100 instance provisioning
    - Job submission and monitoring
    - SSH-based log streaming
    - Artifact download via SCP
    - Pricing and availability queries
    """
    
    # Connector metadata
    name = "lambda_labs"
    display_name = "Lambda Labs"
    description = "High-performance H100/A100 GPU training with Lambda Labs"
    version = "1.0.0"
    
    # Supported features
    supports_training = True
    supports_inference = True
    supports_registry = False
    supports_tracking = False
    
    # API endpoints
    BASE_URL = "https://cloud.lambdalabs.com/api/v1"
    
    def __init__(self):
        self._api_key: Optional[str] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        self._jobs: Dict[str, Dict] = {}
        self._ssh_clients: Dict[str, paramiko.SSHClient] = {}
    
    async def connect(self, credentials: Dict[str, str]) -> bool:
        """
        Verify connection and store credentials.
        
        Args:
            credentials: Dictionary with 'api_key' and optionally 'ssh_key_path'
            
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
        self._ssh_key_path = credentials.get("ssh_key_path")
        
        # Create session with headers
        self._session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            }
        )
        
        # Verify connection by fetching instance types
        try:
            async with self._session.get(
                f"{self.BASE_URL}/instance-types"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "data" in data:
                        self._connected = True
                        return True
                    else:
                        raise ConnectionError("Invalid API response")
                elif response.status == 401:
                    raise ValueError("Invalid API key")
                else:
                    raise ConnectionError(f"Connection failed with status {response.status}")
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Failed to connect to Lambda Labs: {str(e)}")
    
    async def disconnect(self) -> bool:
        """Disconnect and cleanup resources."""
        # Close all SSH connections
        for ssh_client in self._ssh_clients.values():
            ssh_client.close()
        self._ssh_clients.clear()
        
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
            async with self._session.get(
                f"{self.BASE_URL}/instance-types"
            ) as response:
                return response.status == 200
        except:
            return False
    
    async def submit_job(self, config: TrainingConfig) -> str:
        """
        Submit a training job to Lambda Labs.
        
        This provisions a GPU instance, sets up the training environment,
        and starts the training job.
        
        Args:
            config: Training configuration
            
        Returns:
            Job ID (instance ID) for tracking
            
        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If job submission fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to Lambda Labs")
        
        # Validate configuration
        self.validate_config(config)
        
        # Determine instance type based on resource_id or default to A100
        instance_type = config.resource_id or "gpu_1x_a100"
        
        # Build launch configuration
        launch_config = {
            "region_name": "us-west-2",  # Default region
            "instance_type_name": instance_type,
            "ssh_key_names": [],  # Will use API key for SSH
            "file_system_names": [],
            "quantity": 1,
            "name": f"peft-training-{config.project_name}"
        }
        
        # Launch instance
        try:
            async with self._session.post(
                f"{self.BASE_URL}/instance-operations/launch",
                json=launch_config
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Failed to launch instance: {response.status} - {error_text}")
                
                data = await response.json()
                
                if "data" not in data or "instance_ids" not in data["data"]:
                    raise RuntimeError(f"Invalid response: {data}")
                
                instance_ids = data["data"]["instance_ids"]
                if not instance_ids:
                    raise RuntimeError("No instance ID returned")
                
                job_id = instance_ids[0]
                
                # Wait for instance to be active
                await self._wait_for_instance_active(job_id)
                
                # Get instance details including IP
                instance_info = await self._get_instance_info(job_id)
                
                # Store job info
                self._jobs[job_id] = {
                    "config": config,
                    "status": JobStatus.PENDING,
                    "instance_id": job_id,
                    "ip_address": instance_info.get("ip"),
                    "logs": [],
                }
                
                # Setup training environment and start training
                await self._setup_and_start_training(job_id, config)
                
                return job_id
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to submit job: {str(e)}")
    
    async def _wait_for_instance_active(self, instance_id: str, timeout: int = 300):
        """Wait for instance to become active."""
        start_time = asyncio.get_event_loop().time()
        
        while True:
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise RuntimeError(f"Timeout waiting for instance {instance_id} to become active")
            
            status = await self.get_job_status(instance_id)
            if status == JobStatus.RUNNING:
                return
            elif status == JobStatus.FAILED:
                raise RuntimeError(f"Instance {instance_id} failed to start")
            
            await asyncio.sleep(5)
    
    async def _get_instance_info(self, instance_id: str) -> Dict:
        """Get detailed instance information."""
        try:
            async with self._session.get(
                f"{self.BASE_URL}/instances/{instance_id}"
            ) as response:
                if response.status != 200:
                    return {}
                
                data = await response.json()
                return data.get("data", {})
        except:
            return {}
    
    async def _setup_and_start_training(self, instance_id: str, config: TrainingConfig):
        """Setup training environment and start training via SSH."""
        instance_info = self._jobs[instance_id]
        ip_address = instance_info.get("ip_address")
        
        if not ip_address:
            raise RuntimeError(f"No IP address for instance {instance_id}")
        
        # Create SSH client
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # Connect via SSH (Lambda Labs uses ubuntu user)
            if self._ssh_key_path and os.path.exists(self._ssh_key_path):
                ssh_client.connect(
                    ip_address,
                    username="ubuntu",
                    key_filename=self._ssh_key_path,
                    timeout=30
                )
            else:
                # Try password-less connection (API key based)
                ssh_client.connect(
                    ip_address,
                    username="ubuntu",
                    timeout=30,
                    look_for_keys=True
                )
            
            self._ssh_clients[instance_id] = ssh_client
            
            # Build and execute training script
            training_script = self._build_training_script(config)
            
            # Upload training script
            sftp = ssh_client.open_sftp()
            with sftp.file('/tmp/train.py', 'w') as f:
                f.write(training_script)
            sftp.close()
            
            # Start training in background
            stdin, stdout, stderr = ssh_client.exec_command(
                'nohup python /tmp/train.py > /tmp/training.log 2>&1 &'
            )
            
            # Update job status
            self._jobs[instance_id]["status"] = JobStatus.RUNNING
            
        except Exception as e:
            raise RuntimeError(f"Failed to setup training: {str(e)}")
    
    def _build_training_script(self, config: TrainingConfig) -> str:
        """Build Python training script from configuration."""
        script = f"""#!/usr/bin/env python3
import os
import sys

# Install dependencies
print('Installing dependencies...')
os.system('pip install -q unsloth transformers datasets accelerate peft')

# Import libraries
from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments

print('Loading model: {config.base_model}')
# Load model
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name='{config.base_model}',
    max_seq_length=2048,
    dtype=None,
    load_in_4bit={str(config.quantization == 'int4').lower()},
)

print('Configuring PEFT...')
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

print('Loading dataset: {config.dataset_path}')
# Load dataset
dataset = load_dataset('json', data_files='{config.dataset_path}', split='train')

print('Setting up training arguments...')
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

print('Creating trainer...')
# Create trainer
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    args=training_args,
    max_seq_length=2048,
)

print('Starting training...')
# Train
trainer.train()

print('Saving adapter...')
# Save adapter
model.save_pretrained('{config.output_dir}/adapter')
tokenizer.save_pretrained('{config.output_dir}/adapter')

print('Training complete!')
"""
        return script
    
    async def get_job_status(self, job_id: str) -> JobStatus:
        """
        Get the current status of a training job.
        
        Args:
            job_id: Job identifier (instance ID)
            
        Returns:
            Current job status
        """
        if not self._connected:
            raise RuntimeError("Not connected to Lambda Labs")
        
        try:
            async with self._session.get(
                f"{self.BASE_URL}/instances/{job_id}"
            ) as response:
                if response.status != 200:
                    return JobStatus.FAILED
                
                data = await response.json()
                
                if "data" not in data:
                    return JobStatus.FAILED
                
                instance = data["data"]
                status = instance.get("status", "unknown")
                
                # Map Lambda Labs status to JobStatus
                status_map = {
                    "active": JobStatus.RUNNING,
                    "booting": JobStatus.PENDING,
                    "unhealthy": JobStatus.FAILED,
                    "terminated": JobStatus.COMPLETED,
                }
                
                return status_map.get(status, JobStatus.PENDING)
                
        except aiohttp.ClientError:
            return JobStatus.FAILED
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running training job by terminating the instance.
        
        Args:
            job_id: Job identifier (instance ID)
            
        Returns:
            True if cancellation successful
        """
        if not self._connected:
            raise RuntimeError("Not connected to Lambda Labs")
        
        try:
            async with self._session.post(
                f"{self.BASE_URL}/instance-operations/terminate",
                json={"instance_ids": [job_id]}
            ) as response:
                if response.status == 200:
                    # Close SSH connection if exists
                    if job_id in self._ssh_clients:
                        self._ssh_clients[job_id].close()
                        del self._ssh_clients[job_id]
                    
                    # Update job status
                    if job_id in self._jobs:
                        self._jobs[job_id]["status"] = JobStatus.CANCELLED
                    
                    return True
                return False
                
        except aiohttp.ClientError:
            return False
    
    async def stream_logs(self, job_id: str) -> AsyncIterator[str]:
        """
        Stream logs from a training job via SSH.
        
        Args:
            job_id: Job identifier (instance ID)
            
        Yields:
            Log lines as they become available
        """
        if not self._connected:
            raise RuntimeError("Not connected to Lambda Labs")
        
        # Get SSH client for this instance
        ssh_client = self._ssh_clients.get(job_id)
        
        if not ssh_client:
            # Try to reconnect
            instance_info = self._jobs.get(job_id, {})
            ip_address = instance_info.get("ip_address")
            
            if not ip_address:
                yield "Error: No SSH connection available for this instance"
                return
            
            try:
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                if self._ssh_key_path and os.path.exists(self._ssh_key_path):
                    ssh_client.connect(
                        ip_address,
                        username="ubuntu",
                        key_filename=self._ssh_key_path,
                        timeout=30
                    )
                else:
                    ssh_client.connect(
                        ip_address,
                        username="ubuntu",
                        timeout=30,
                        look_for_keys=True
                    )
                
                self._ssh_clients[job_id] = ssh_client
            except Exception as e:
                yield f"Error connecting via SSH: {str(e)}"
                return
        
        # Stream logs using tail -f
        try:
            stdin, stdout, stderr = ssh_client.exec_command(
                'tail -f /tmp/training.log 2>/dev/null || echo "Log file not found"'
            )
            
            # Read logs line by line
            while True:
                line = stdout.readline()
                if not line:
                    # Check if job is still running
                    status = await self.get_job_status(job_id)
                    if status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                        break
                    await asyncio.sleep(1)
                    continue
                
                yield line.strip()
                
        except Exception as e:
            yield f"Error streaming logs: {str(e)}"
    
    async def fetch_artifact(self, job_id: str) -> bytes:
        """
        Download the trained adapter artifact via SCP.
        
        Args:
            job_id: Job identifier (instance ID)
            
        Returns:
            Artifact data as bytes (tar.gz of adapter directory)
            
        Raises:
            FileNotFoundError: If artifact doesn't exist
            RuntimeError: If download fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to Lambda Labs")
        
        # Check job is completed
        status = await self.get_job_status(job_id)
        if status not in [JobStatus.COMPLETED, JobStatus.RUNNING]:
            raise RuntimeError(f"Job not ready for artifact download, status: {status.value}")
        
        # Get SSH client
        ssh_client = self._ssh_clients.get(job_id)
        
        if not ssh_client:
            # Try to reconnect
            instance_info = self._jobs.get(job_id, {})
            ip_address = instance_info.get("ip_address")
            
            if not ip_address:
                raise RuntimeError("No SSH connection available")
            
            try:
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                if self._ssh_key_path and os.path.exists(self._ssh_key_path):
                    ssh_client.connect(
                        ip_address,
                        username="ubuntu",
                        key_filename=self._ssh_key_path,
                        timeout=30
                    )
                else:
                    ssh_client.connect(
                        ip_address,
                        username="ubuntu",
                        timeout=30,
                        look_for_keys=True
                    )
                
                self._ssh_clients[job_id] = ssh_client
            except Exception as e:
                raise RuntimeError(f"Failed to connect via SSH: {str(e)}")
        
        # Get config to find output directory
        config = self._jobs[job_id]["config"]
        output_dir = config.output_dir
        
        try:
            # Create tar.gz of adapter directory on remote
            stdin, stdout, stderr = ssh_client.exec_command(
                f'cd {output_dir} && tar -czf /tmp/adapter.tar.gz adapter/'
            )
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status != 0:
                error = stderr.read().decode()
                raise FileNotFoundError(f"Adapter not found: {error}")
            
            # Download tar.gz via SCP
            scp_client = scp_module.SCPClient(ssh_client.get_transport())
            
            # Download to BytesIO
            artifact_data = BytesIO()
            scp_client.get('/tmp/adapter.tar.gz', artifact_data)
            scp_client.close()
            
            return artifact_data.getvalue()
            
        except Exception as e:
            raise RuntimeError(f"Failed to download artifact: {str(e)}")
    
    async def upload_artifact(self, path: str, metadata: Dict) -> str:
        """
        Upload an adapter to Lambda Labs storage (not directly supported).
        
        Lambda Labs doesn't have a built-in artifact registry, so this
        uploads to the instance's storage for later retrieval.
        
        Args:
            path: Local path to artifact
            metadata: Artifact metadata
            
        Returns:
            Artifact path on instance
            
        Raises:
            FileNotFoundError: If local file doesn't exist
            RuntimeError: If upload fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to Lambda Labs")
        
        # Check file exists
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        # Note: Lambda Labs doesn't have a central artifact storage
        # This would typically upload to an active instance
        # For now, return a placeholder
        return f"lambda-labs://{file_path.name}"
    
    async def list_resources(self) -> List[Resource]:
        """
        List available GPU resources on Lambda Labs.
        
        Returns:
            List of available GPU resources
        """
        if not self._connected:
            raise RuntimeError("Not connected to Lambda Labs")
        
        try:
            async with self._session.get(
                f"{self.BASE_URL}/instance-types"
            ) as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                
                if "data" not in data:
                    return []
                
                resources = []
                for instance_type_name, instance_type in data["data"].items():
                    specs = instance_type["instance_type"]
                    
                    # Parse GPU info
                    gpu_description = specs.get("description", "")
                    gpu_count = 1
                    
                    # Determine GPU type from name
                    if "H100" in instance_type_name or "H100" in gpu_description:
                        gpu_type = "H100"
                        vram_gb = 80
                    elif "A100" in instance_type_name or "A100" in gpu_description:
                        if "80GB" in gpu_description:
                            gpu_type = "A100 80GB"
                            vram_gb = 80
                        else:
                            gpu_type = "A100 40GB"
                            vram_gb = 40
                    elif "A10" in instance_type_name or "A10" in gpu_description:
                        gpu_type = "A10"
                        vram_gb = 24
                    elif "V100" in instance_type_name or "V100" in gpu_description:
                        gpu_type = "V100"
                        vram_gb = 16
                    elif "3090" in instance_type_name or "3090" in gpu_description:
                        gpu_type = "RTX 3090"
                        vram_gb = 24
                    else:
                        gpu_type = "Unknown"
                        vram_gb = 0
                    
                    # Extract GPU count from name (e.g., "gpu_8x_a100")
                    if "_" in instance_type_name:
                        parts = instance_type_name.split("_")
                        for part in parts:
                            if "x" in part:
                                try:
                                    gpu_count = int(part.replace("x", ""))
                                except:
                                    pass
                    
                    resources.append(Resource(
                        id=instance_type_name,
                        name=specs.get("description", instance_type_name),
                        type=ResourceType.GPU,
                        gpu_type=gpu_type,
                        gpu_count=gpu_count,
                        vram_gb=vram_gb,
                        cpu_cores=specs.get("specs", {}).get("vcpus", 0),
                        ram_gb=specs.get("specs", {}).get("memory_gib", 0),
                        available=len(instance_type.get("regions_with_capacity_available", [])) > 0,
                        region="lambda-labs-cloud",
                    ))
                
                return resources
                
        except aiohttp.ClientError:
            return []
    
    async def get_pricing(self, resource_id: str) -> PricingInfo:
        """
        Get pricing information for a specific GPU resource.
        
        Args:
            resource_id: Instance type name
            
        Returns:
            Pricing information
            
        Raises:
            ValueError: If resource_id is invalid
        """
        if not self._connected:
            raise RuntimeError("Not connected to Lambda Labs")
        
        try:
            async with self._session.get(
                f"{self.BASE_URL}/instance-types"
            ) as response:
                if response.status != 200:
                    raise ValueError(f"Invalid resource ID: {resource_id}")
                
                data = await response.json()
                
                if "data" not in data or resource_id not in data["data"]:
                    raise ValueError(f"Invalid resource ID: {resource_id}")
                
                instance_type = data["data"][resource_id]["instance_type"]
                price_cents_per_hour = instance_type.get("price_cents_per_hour", 0)
                
                return PricingInfo(
                    resource_id=resource_id,
                    price_per_hour=price_cents_per_hour / 100.0,  # Convert cents to dollars
                    currency="USD",
                    billing_increment_seconds=3600,  # Lambda Labs bills hourly
                    minimum_charge_seconds=3600,
                    spot_available=False,  # Lambda Labs doesn't have spot instances
                    spot_price_per_hour=None,
                )
                
        except aiohttp.ClientError as e:
            raise ValueError(f"Failed to get pricing: {str(e)}")
    
    def get_required_credentials(self) -> List[str]:
        """Get list of required credential keys."""
        return ["api_key"]
