"""
Local connector for running training on local GPU.

This is a reference implementation that demonstrates how to create
a connector that implements the PlatformConnector interface.
"""

from typing import Dict, List, AsyncIterator
import asyncio
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


class LocalConnector(PlatformConnector):
    """
    Connector for local GPU training.
    
    This connector allows training on the local machine's GPU without
    requiring any cloud platform credentials.
    """
    
    # Connector metadata
    name = "local"
    display_name = "Local GPU"
    description = "Train on your local GPU without cloud costs"
    version = "1.0.0"
    
    # Supported features
    supports_training = True
    supports_inference = True
    supports_registry = False
    supports_tracking = False
    
    def __init__(self):
        self._connected = False
        self._jobs: Dict[str, Dict] = {}
    
    async def connect(self, credentials: Dict[str, str]) -> bool:
        """
        Connect to local GPU (no credentials needed).
        
        Args:
            credentials: Empty dict (no credentials required)
            
        Returns:
            True if local GPU is available
        """
        # Check if GPU is available
        try:
            import torch
            self._connected = torch.cuda.is_available()
            return self._connected
        except ImportError:
            self._connected = False
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect (cleanup)."""
        self._connected = False
        self._jobs.clear()
        return True
    
    async def verify_connection(self) -> bool:
        """Verify GPU is still available."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    async def submit_job(self, config: TrainingConfig) -> str:
        """
        Submit a training job to run locally.
        
        Args:
            config: Training configuration
            
        Returns:
            Job ID
        """
        if not self._connected:
            raise RuntimeError("Not connected to local GPU")
        
        # Generate job ID
        job_id = f"local_{len(self._jobs)}"
        
        # Store job info
        self._jobs[job_id] = {
            "config": config,
            "status": JobStatus.PENDING,
            "logs": [],
        }
        
        # Simulate job starting
        asyncio.create_task(self._run_job(job_id))
        
        return job_id
    
    async def _run_job(self, job_id: str):
        """Simulate running a training job."""
        self._jobs[job_id]["status"] = JobStatus.RUNNING
        self._jobs[job_id]["logs"].append("Starting training...")
        
        # Simulate training time
        await asyncio.sleep(2)
        
        self._jobs[job_id]["logs"].append("Training complete!")
        self._jobs[job_id]["status"] = JobStatus.COMPLETED
    
    async def get_job_status(self, job_id: str) -> JobStatus:
        """Get job status."""
        if job_id not in self._jobs:
            raise ValueError(f"Job not found: {job_id}")
        return self._jobs[job_id]["status"]
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job."""
        if job_id not in self._jobs:
            return False
        
        self._jobs[job_id]["status"] = JobStatus.CANCELLED
        return True
    
    async def stream_logs(self, job_id: str) -> AsyncIterator[str]:
        """Stream logs from a job."""
        if job_id not in self._jobs:
            raise ValueError(f"Job not found: {job_id}")
        
        # Yield existing logs
        for log in self._jobs[job_id]["logs"]:
            yield log
        
        # Wait for job to complete and yield new logs
        while self._jobs[job_id]["status"] in [JobStatus.PENDING, JobStatus.RUNNING]:
            await asyncio.sleep(0.5)
            # Yield any new logs
            for log in self._jobs[job_id]["logs"]:
                yield log
    
    async def fetch_artifact(self, job_id: str) -> bytes:
        """Download trained adapter."""
        if job_id not in self._jobs:
            raise FileNotFoundError(f"Job not found: {job_id}")
        
        if self._jobs[job_id]["status"] != JobStatus.COMPLETED:
            raise RuntimeError("Job not completed")
        
        # Return dummy artifact
        return b"dummy_adapter_data"
    
    async def upload_artifact(self, path: str, metadata: Dict) -> str:
        """Upload artifact (not supported for local)."""
        raise NotImplementedError("Local connector does not support artifact upload")
    
    async def list_resources(self) -> List[Resource]:
        """List local GPU resources."""
        resources = []
        
        try:
            import torch
            if torch.cuda.is_available():
                for i in range(torch.cuda.device_count()):
                    props = torch.cuda.get_device_properties(i)
                    resources.append(Resource(
                        id=f"local_gpu_{i}",
                        name=props.name,
                        type=ResourceType.GPU,
                        gpu_type=props.name,
                        gpu_count=1,
                        vram_gb=props.total_memory // (1024**3),
                        available=True,
                        region="local",
                    ))
        except ImportError:
            pass
        
        return resources
    
    async def get_pricing(self, resource_id: str) -> PricingInfo:
        """Get pricing (free for local)."""
        return PricingInfo(
            resource_id=resource_id,
            price_per_hour=0.0,
            currency="USD",
        )
    
    def get_required_credentials(self) -> List[str]:
        """No credentials required for local."""
        return []
