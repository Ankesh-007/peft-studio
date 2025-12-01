"""
Vast.ai connector for cloud GPU training.

This connector integrates with Vast.ai's API to search and rent GPU instances
from their marketplace, submit training jobs, stream logs, and download artifacts.

Vast.ai API Documentation: https://vast.ai/docs/
"""

from typing import Dict, List, AsyncIterator, Optional
import asyncio
import aiohttp
import json
from pathlib import Path
import sys
import paramiko
from io import BytesIO
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


class VastAIConnector(PlatformConnector):
    """
    Connector for Vast.ai GPU marketplace.
    
    Vast.ai provides a marketplace for renting GPU instances from various hosts
    at competitive prices. This connector handles:
    - Marketplace instance search and rental
    - Job submission and monitoring
    - SSH-based log streaming
    - Artifact download via SCP
    - Pricing comparison across hosts
    """
    
    # Connector metadata
    name = "vastai"
    display_name = "Vast.ai"
    description = "GPU marketplace with competitive pricing from multiple hosts"
    version = "1.0.0"
    
    # Supported features
    supports_training = True
    supports_inference = True
    supports_registry = False
    supports_tracking = False
    
    # API endpoints
    BASE_URL = "https://console.vast.ai/api/v0"
    
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
                "Accept": "application/json",
            }
        )
        
        # Verify connection by fetching user info
        try:
            async with self._session.get(
                f"{self.BASE_URL}/users/current/",
                params={"api_key": self._api_key}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "id" in data or "username" in data:
                        self._connected = True
                        return True
                    else:
                        raise ConnectionError("Invalid API response")
                elif response.status == 401:
                    raise ValueError("Invalid API key")
                else:
                    raise ConnectionError(f"Connection failed with status {response.status}")
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Failed to connect to Vast.ai: {str(e)}")
    
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
                f"{self.BASE_URL}/users/current/",
                params={"api_key": self._api_key}
            ) as response:
                return response.status == 200
        except:
            return False
    
    async def submit_job(self, config: TrainingConfig) -> str:
        """
        Submit a training job to Vast.ai.
        
        This searches for available instances, rents one, sets up the training
        environment, and starts the training job.
        
        Args:
            config: Training configuration
            
        Returns:
            Job ID (instance ID) for tracking
            
        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If job submission fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to Vast.ai")
        
        # Validate configuration
        self.validate_config(config)
        
        # Search for available instances
        search_params = {
            "api_key": self._api_key,
            "q": json.dumps({
                "verified": {"eq": True},
                "external": {"eq": False},
                "rentable": {"eq": True},
                "gpu_name": {"eq": config.resource_id} if config.resource_id else None,
                "num_gpus": {"gte": 1},
                "disk_space": {"gte": 50},  # At least 50GB disk
            }),
            "order": [["dph_total", "asc"]],  # Sort by price ascending
            "type": "on-demand"
        }
        
        # Remove None values
        search_params["q"] = json.dumps({k: v for k, v in json.loads(search_params["q"]).items() if v is not None})
        
        try:
            # Search for offers
            async with self._session.get(
                f"{self.BASE_URL}/bundles/",
                params=search_params
            ) as response:
                if response.status != 200:
                    raise RuntimeError(f"Failed to search instances: {response.status}")
                
                offers = await response.json()
                
                if not offers or len(offers.get("offers", [])) == 0:
                    raise RuntimeError("No available instances found matching criteria")
                
                # Select the cheapest available offer
                offer = offers["offers"][0]
                offer_id = offer["id"]
                
                # Rent the instance
                rent_params = {
                    "api_key": self._api_key,
                }
                
                rent_data = {
                    "client_id": "peft-studio",
                    "image": "pytorch/pytorch:2.1.0-cuda11.8-cudnn8-devel",
                    "disk": 50,
                    "label": f"peft-training-{config.project_name}",
                    "onstart": self._build_onstart_script(config),
                    "runtype": "ssh",  # SSH mode for interactive access
                }
                
                async with self._session.put(
                    f"{self.BASE_URL}/asks/{offer_id}/",
                    params=rent_params,
                    json=rent_data
                ) as response:
                    if response.status not in [200, 201]:
                        error_text = await response.text()
                        raise RuntimeError(f"Failed to rent instance: {response.status} - {error_text}")
                    
                    data = await response.json()
                    
                    if not data.get("success"):
                        raise RuntimeError(f"Failed to rent instance: {data.get('msg', 'Unknown error')}")
                    
                    instance_id = data.get("new_contract")
                    
                    if not instance_id:
                        raise RuntimeError("No instance ID returned")
                    
                    # Wait for instance to be ready
                    await self._wait_for_instance_ready(instance_id)
                    
                    # Get instance details including SSH info
                    instance_info = await self._get_instance_info(instance_id)
                    
                    # Store job info
                    self._jobs[str(instance_id)] = {
                        "config": config,
                        "status": JobStatus.PENDING,
                        "instance_id": instance_id,
                        "ssh_host": instance_info.get("ssh_host"),
                        "ssh_port": instance_info.get("ssh_port"),
                        "logs": [],
                    }
                    
                    # Setup training environment and start training
                    await self._setup_and_start_training(str(instance_id), config)
                    
                    return str(instance_id)
                    
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to submit job: {str(e)}")
    
    def _build_onstart_script(self, config: TrainingConfig) -> str:
        """Build onstart script that runs when instance boots."""
        script = f"""#!/bin/bash
# Install dependencies
pip install -q unsloth transformers datasets accelerate peft

# Create training script
cat > /workspace/train.py << 'EOFPYTHON'
{self._build_training_script(config)}
EOFPYTHON

# Start training in background
nohup python /workspace/train.py > /workspace/training.log 2>&1 &
"""
        return script
    
    def _build_training_script(self, config: TrainingConfig) -> str:
        """Build Python training script from configuration."""
        script = f"""#!/usr/bin/env python3
import os
import sys

print('Starting PEFT training...')

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
    
    async def _wait_for_instance_ready(self, instance_id: int, timeout: int = 300):
        """Wait for instance to become ready."""
        start_time = asyncio.get_event_loop().time()
        
        while True:
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise RuntimeError(f"Timeout waiting for instance {instance_id} to become ready")
            
            status = await self.get_job_status(str(instance_id))
            if status == JobStatus.RUNNING:
                return
            elif status == JobStatus.FAILED:
                raise RuntimeError(f"Instance {instance_id} failed to start")
            
            await asyncio.sleep(5)
    
    async def _get_instance_info(self, instance_id: int) -> Dict:
        """Get detailed instance information."""
        try:
            async with self._session.get(
                f"{self.BASE_URL}/instances/",
                params={"api_key": self._api_key, "id": instance_id}
            ) as response:
                if response.status != 200:
                    return {}
                
                data = await response.json()
                instances = data.get("instances", [])
                
                if not instances:
                    return {}
                
                instance = instances[0]
                
                return {
                    "ssh_host": instance.get("ssh_host"),
                    "ssh_port": instance.get("ssh_port", 22),
                    "status": instance.get("actual_status"),
                    "gpu_name": instance.get("gpu_name"),
                }
        except:
            return {}
    
    async def _setup_and_start_training(self, instance_id: str, config: TrainingConfig):
        """Setup training environment and start training via SSH."""
        instance_info = self._jobs[instance_id]
        ssh_host = instance_info.get("ssh_host")
        ssh_port = instance_info.get("ssh_port", 22)
        
        if not ssh_host:
            raise RuntimeError(f"No SSH host for instance {instance_id}")
        
        # Create SSH client
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # Connect via SSH (Vast.ai uses root user)
            ssh_client.connect(
                ssh_host,
                port=ssh_port,
                username="root",
                timeout=30,
                look_for_keys=True,
                allow_agent=True
            )
            
            self._ssh_clients[instance_id] = ssh_client
            
            # The onstart script should have already started training
            # Just verify it's running
            stdin, stdout, stderr = ssh_client.exec_command(
                'ps aux | grep train.py | grep -v grep'
            )
            
            output = stdout.read().decode()
            
            if not output:
                # Training not started, start it manually
                training_script = self._build_training_script(config)
                
                # Upload training script
                sftp = ssh_client.open_sftp()
                with sftp.file('/workspace/train.py', 'w') as f:
                    f.write(training_script)
                sftp.close()
                
                # Start training in background
                stdin, stdout, stderr = ssh_client.exec_command(
                    'nohup python /workspace/train.py > /workspace/training.log 2>&1 &'
                )
            
            # Update job status
            self._jobs[instance_id]["status"] = JobStatus.RUNNING
            
        except Exception as e:
            raise RuntimeError(f"Failed to setup training: {str(e)}")
    
    async def get_job_status(self, job_id: str) -> JobStatus:
        """
        Get the current status of a training job.
        
        Args:
            job_id: Job identifier (instance ID)
            
        Returns:
            Current job status
        """
        if not self._connected:
            raise RuntimeError("Not connected to Vast.ai")
        
        try:
            async with self._session.get(
                f"{self.BASE_URL}/instances/",
                params={"api_key": self._api_key, "id": int(job_id)}
            ) as response:
                if response.status != 200:
                    return JobStatus.FAILED
                
                data = await response.json()
                instances = data.get("instances", [])
                
                if not instances:
                    return JobStatus.FAILED
                
                instance = instances[0]
                status = instance.get("actual_status", "unknown")
                
                # Map Vast.ai status to JobStatus
                status_map = {
                    "running": JobStatus.RUNNING,
                    "loading": JobStatus.PENDING,
                    "created": JobStatus.PENDING,
                    "exited": JobStatus.COMPLETED,
                    "stopped": JobStatus.CANCELLED,
                }
                
                return status_map.get(status, JobStatus.PENDING)
                
        except aiohttp.ClientError:
            return JobStatus.FAILED
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running training job by destroying the instance.
        
        Args:
            job_id: Job identifier (instance ID)
            
        Returns:
            True if cancellation successful
        """
        if not self._connected:
            raise RuntimeError("Not connected to Vast.ai")
        
        try:
            async with self._session.delete(
                f"{self.BASE_URL}/instances/{job_id}/",
                params={"api_key": self._api_key}
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
            raise RuntimeError("Not connected to Vast.ai")
        
        # Get SSH client for this instance
        ssh_client = self._ssh_clients.get(job_id)
        
        if not ssh_client:
            # Try to reconnect
            instance_info = self._jobs.get(job_id, {})
            ssh_host = instance_info.get("ssh_host")
            ssh_port = instance_info.get("ssh_port", 22)
            
            if not ssh_host:
                yield "Error: No SSH connection available for this instance"
                return
            
            try:
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh_client.connect(
                    ssh_host,
                    port=ssh_port,
                    username="root",
                    timeout=30,
                    look_for_keys=True,
                    allow_agent=True
                )
                
                self._ssh_clients[job_id] = ssh_client
            except Exception as e:
                yield f"Error connecting via SSH: {str(e)}"
                return
        
        # Stream logs using tail -f
        try:
            stdin, stdout, stderr = ssh_client.exec_command(
                'tail -f /workspace/training.log 2>/dev/null || echo "Log file not found"'
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
            raise RuntimeError("Not connected to Vast.ai")
        
        # Check job is completed or running
        status = await self.get_job_status(job_id)
        if status not in [JobStatus.COMPLETED, JobStatus.RUNNING]:
            raise RuntimeError(f"Job not ready for artifact download, status: {status.value}")
        
        # Get SSH client
        ssh_client = self._ssh_clients.get(job_id)
        
        if not ssh_client:
            # Try to reconnect
            instance_info = self._jobs.get(job_id, {})
            ssh_host = instance_info.get("ssh_host")
            ssh_port = instance_info.get("ssh_port", 22)
            
            if not ssh_host:
                raise RuntimeError("No SSH connection available")
            
            try:
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh_client.connect(
                    ssh_host,
                    port=ssh_port,
                    username="root",
                    timeout=30,
                    look_for_keys=True,
                    allow_agent=True
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
            
            # Download tar.gz via SFTP
            sftp = ssh_client.open_sftp()
            
            # Download to BytesIO
            artifact_data = BytesIO()
            with sftp.file('/tmp/adapter.tar.gz', 'r') as remote_file:
                artifact_data.write(remote_file.read())
            
            sftp.close()
            
            return artifact_data.getvalue()
            
        except Exception as e:
            raise RuntimeError(f"Failed to download artifact: {str(e)}")
    
    async def upload_artifact(self, path: str, metadata: Dict) -> str:
        """
        Upload an adapter to Vast.ai storage (not directly supported).
        
        Vast.ai doesn't have a built-in artifact registry, so this
        uploads to an active instance's storage for later retrieval.
        
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
            raise RuntimeError("Not connected to Vast.ai")
        
        # Check file exists
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        # Note: Vast.ai doesn't have a central artifact storage
        # This would typically upload to an active instance
        # For now, return a placeholder
        return f"vastai://{file_path.name}"
    
    async def list_resources(self) -> List[Resource]:
        """
        List available GPU resources on Vast.ai marketplace.
        
        Returns:
            List of available GPU resources with pricing
        """
        if not self._connected:
            raise RuntimeError("Not connected to Vast.ai")
        
        try:
            # Search for all available offers
            search_params = {
                "api_key": self._api_key,
                "q": json.dumps({
                    "verified": {"eq": True},
                    "external": {"eq": False},
                    "rentable": {"eq": True},
                    "num_gpus": {"gte": 1},
                }),
                "order": [["dph_total", "asc"]],
                "type": "on-demand"
            }
            
            async with self._session.get(
                f"{self.BASE_URL}/bundles/",
                params=search_params
            ) as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                offers = data.get("offers", [])
                
                resources = []
                seen_gpu_types = set()
                
                for offer in offers[:50]:  # Limit to top 50 offers
                    gpu_name = offer.get("gpu_name", "Unknown")
                    
                    # Skip duplicates (show one example per GPU type)
                    if gpu_name in seen_gpu_types:
                        continue
                    seen_gpu_types.add(gpu_name)
                    
                    num_gpus = offer.get("num_gpus", 1)
                    gpu_ram = offer.get("gpu_ram", 0)
                    cpu_cores = offer.get("cpu_cores", 0)
                    cpu_ram = offer.get("cpu_ram", 0)
                    
                    resources.append(Resource(
                        id=gpu_name,
                        name=f"{num_gpus}x {gpu_name}",
                        type=ResourceType.GPU,
                        gpu_type=gpu_name,
                        gpu_count=num_gpus,
                        vram_gb=int(gpu_ram / 1024) if gpu_ram else 0,  # Convert MB to GB
                        cpu_cores=cpu_cores,
                        ram_gb=int(cpu_ram / 1024) if cpu_ram else 0,  # Convert MB to GB
                        available=True,
                        region="vastai-marketplace",
                    ))
                
                return resources
                
        except aiohttp.ClientError:
            return []
    
    async def get_pricing(self, resource_id: str) -> PricingInfo:
        """
        Get pricing information for a specific GPU type.
        
        This searches the marketplace for the cheapest available instance
        of the specified GPU type.
        
        Args:
            resource_id: GPU name (e.g., "RTX 4090", "A100")
            
        Returns:
            Pricing information for the cheapest available instance
            
        Raises:
            ValueError: If resource_id is invalid or no instances available
        """
        if not self._connected:
            raise RuntimeError("Not connected to Vast.ai")
        
        try:
            # Search for offers with this GPU type
            search_params = {
                "api_key": self._api_key,
                "q": json.dumps({
                    "verified": {"eq": True},
                    "external": {"eq": False},
                    "rentable": {"eq": True},
                    "gpu_name": {"eq": resource_id},
                }),
                "order": [["dph_total", "asc"]],
                "type": "on-demand"
            }
            
            async with self._session.get(
                f"{self.BASE_URL}/bundles/",
                params=search_params
            ) as response:
                if response.status != 200:
                    raise ValueError(f"Failed to get pricing for {resource_id}")
                
                data = await response.json()
                offers = data.get("offers", [])
                
                if not offers:
                    raise ValueError(f"No available instances for GPU type: {resource_id}")
                
                # Get the cheapest offer
                cheapest = offers[0]
                price_per_hour = cheapest.get("dph_total", 0)
                
                # Get price range (min and max from top 10 offers)
                prices = [offer.get("dph_total", 0) for offer in offers[:10]]
                min_price = min(prices) if prices else price_per_hour
                max_price = max(prices) if prices else price_per_hour
                
                return PricingInfo(
                    resource_id=resource_id,
                    price_per_hour=price_per_hour,
                    currency="USD",
                    billing_increment_seconds=60,  # Vast.ai bills per minute
                    minimum_charge_seconds=60,
                    spot_available=True,  # Vast.ai has interruptible instances
                    spot_price_per_hour=min_price,  # Lowest price in marketplace
                )
                
        except aiohttp.ClientError as e:
            raise ValueError(f"Failed to get pricing: {str(e)}")
    
    def get_required_credentials(self) -> List[str]:
        """Get list of required credential keys."""
        return ["api_key"]
