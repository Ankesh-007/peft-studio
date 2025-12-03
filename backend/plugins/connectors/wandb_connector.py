"""
Weights & Biases connector for experiment tracking.

This connector integrates with W&B's API to create projects, log metrics,
track artifacts, and compare experiments.

W&B API Documentation: https://docs.wandb.ai/ref/python/
"""

from typing import Dict, List, AsyncIterator, Optional, Any
import asyncio
import aiohttp
import json
from pathlib import Path
import sys
import os
from datetime import datetime
from collections import deque

sys.path.append(str(Path(__file__).parent.parent.parent))

from connectors.base import (
    PlatformConnector,
    Resource,
    ResourceType,
    PricingInfo,
    TrainingConfig,
    JobStatus,
)


class WandBConnector(PlatformConnector):
    """
    Connector for Weights & Biases experiment tracking platform.
    
    W&B provides experiment tracking, hyperparameter optimization,
    and model versioning. This connector handles:
    - Project and run creation
    - Metric logging with batching
    - Artifact tracking
    - Experiment comparison queries
    """
    
    # Connector metadata
    name = "wandb"
    display_name = "Weights & Biases"
    description = "Experiment tracking and model versioning with W&B"
    version = "1.0.0"
    
    # Supported features
    supports_training = False  # W&B doesn't provide compute
    supports_inference = False
    supports_registry = False
    supports_tracking = True  # Primary feature
    
    # API endpoints
    BASE_URL = "https://api.wandb.ai"
    
    def __init__(self):
        self._api_key: Optional[str] = None
        self._entity: Optional[str] = None  # Username or team name
        self._session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        self._runs: Dict[str, Dict] = {}  # job_id -> run info
        self._metric_batches: Dict[str, deque] = {}  # job_id -> metric queue
        self._batch_size = 100  # Batch metrics for efficiency
        self._batch_interval = 5.0  # Seconds between batch uploads
        self._batch_tasks: Dict[str, asyncio.Task] = {}  # Background batch tasks
    
    async def connect(self, credentials: Dict[str, str]) -> bool:
        """
        Verify connection and store credentials.
        
        Args:
            credentials: Dictionary with 'api_key' and optionally 'entity'
            
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
        self._entity = credentials.get("entity")  # Optional
        
        # Create session with headers
        self._session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            }
        )
        
        # Verify connection by fetching user info
        try:
            async with self._session.get(
                f"{self.BASE_URL}/viewer"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "data" in data and "viewer" in data["data"]:
                        viewer = data["data"]["viewer"]
                        # Use entity from credentials or default to username
                        if not self._entity:
                            self._entity = viewer.get("username")
                        self._connected = True
                        return True
                    else:
                        raise ConnectionError("Invalid API response")
                elif response.status == 401:
                    raise ValueError("Invalid API key")
                else:
                    raise ConnectionError(f"Connection failed with status {response.status}")
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Failed to connect to W&B: {str(e)}")
    
    async def disconnect(self) -> bool:
        """Disconnect and cleanup resources."""
        # Cancel all batch tasks
        for task in self._batch_tasks.values():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Flush remaining metrics
        for job_id in list(self._metric_batches.keys()):
            await self._flush_metrics(job_id)
        
        if self._session:
            await self._session.close()
            self._session = None
        
        self._connected = False
        self._api_key = None
        self._entity = None
        self._runs.clear()
        self._metric_batches.clear()
        self._batch_tasks.clear()
        return True
    
    async def verify_connection(self) -> bool:
        """Verify that the connection is still valid."""
        if not self._connected or not self._session:
            return False
        
        try:
            async with self._session.get(
                f"{self.BASE_URL}/viewer"
            ) as response:
                return response.status == 200
        except:
            return False
    
    async def submit_job(self, config: TrainingConfig) -> str:
        """
        Create a new W&B run for tracking a training job.
        
        Args:
            config: Training configuration
            
        Returns:
            Run ID for tracking
            
        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If run creation fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to W&B")
        
        # Generate run ID (W&B will assign actual ID)
        job_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Prepare run configuration
        run_config = {
            "entity": self._entity,
            "project": config.project_name,
            "name": f"{config.base_model}_{config.algorithm}",
            "config": {
                "base_model": config.base_model,
                "model_source": config.model_source,
                "algorithm": config.algorithm,
                "rank": config.rank,
                "alpha": config.alpha,
                "dropout": config.dropout,
                "target_modules": config.target_modules,
                "quantization": config.quantization,
                "learning_rate": config.learning_rate,
                "batch_size": config.batch_size,
                "gradient_accumulation_steps": config.gradient_accumulation_steps,
                "num_epochs": config.num_epochs,
                "warmup_steps": config.warmup_steps,
                "provider": config.provider,
                "dataset_path": config.dataset_path,
                "validation_split": config.validation_split,
            },
            "tags": [config.algorithm, config.provider, config.model_source],
        }
        
        # Create run via API
        try:
            async with self._session.post(
                f"{self.BASE_URL}/runs",
                json=run_config
            ) as response:
                if response.status not in [200, 201]:
                    raise RuntimeError(f"Failed to create run: {response.status}")
                
                data = await response.json()
                
                # Extract run ID from response
                if "data" in data and "run" in data["data"]:
                    wandb_run_id = data["data"]["run"]["id"]
                else:
                    # Fallback to generated ID
                    wandb_run_id = job_id
                
                # Store run info
                self._runs[job_id] = {
                    "wandb_id": wandb_run_id,
                    "config": config,
                    "status": JobStatus.RUNNING,
                    "project": config.project_name,
                    "entity": self._entity,
                    "created_at": datetime.now().isoformat(),
                }
                
                # Initialize metric batch queue
                self._metric_batches[job_id] = deque()
                
                # Start background batch task
                self._batch_tasks[job_id] = asyncio.create_task(
                    self._batch_upload_loop(job_id)
                )
                
                return job_id
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to create run: {str(e)}")
    
    async def _batch_upload_loop(self, job_id: str):
        """Background task to periodically upload batched metrics."""
        try:
            while job_id in self._runs:
                await asyncio.sleep(self._batch_interval)
                await self._flush_metrics(job_id)
        except asyncio.CancelledError:
            # Final flush on cancellation
            await self._flush_metrics(job_id)
            raise
    
    async def _flush_metrics(self, job_id: str):
        """Flush batched metrics to W&B."""
        if job_id not in self._metric_batches:
            return
        
        batch = self._metric_batches[job_id]
        if not batch:
            return
        
        # Collect all metrics from batch
        metrics_to_send = []
        while batch:
            metrics_to_send.append(batch.popleft())
        
        if not metrics_to_send:
            return
        
        # Send batch to W&B
        run_info = self._runs.get(job_id)
        if not run_info:
            return
        
        try:
            async with self._session.post(
                f"{self.BASE_URL}/runs/{run_info['wandb_id']}/history",
                json={"history": metrics_to_send}
            ) as response:
                if response.status not in [200, 201]:
                    # Re-queue metrics on failure
                    for metric in metrics_to_send:
                        batch.append(metric)
        except aiohttp.ClientError:
            # Re-queue metrics on error
            for metric in metrics_to_send:
                batch.append(metric)
    
    async def log_metrics(self, job_id: str, metrics: Dict[str, Any], step: Optional[int] = None):
        """
        Log metrics for a training run with batching.
        
        Args:
            job_id: Job identifier
            metrics: Dictionary of metric name -> value
            step: Training step number
        """
        if job_id not in self._metric_batches:
            return
        
        # Add to batch queue
        metric_entry = {
            "_step": step if step is not None else 0,
            "_timestamp": datetime.now().timestamp(),
            **metrics
        }
        
        self._metric_batches[job_id].append(metric_entry)
        
        # Flush if batch is full
        if len(self._metric_batches[job_id]) >= self._batch_size:
            await self._flush_metrics(job_id)
    
    async def get_job_status(self, job_id: str) -> JobStatus:
        """
        Get the current status of a W&B run.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Current job status
        """
        if not self._connected:
            raise RuntimeError("Not connected to W&B")
        
        if job_id not in self._runs:
            return JobStatus.FAILED
        
        run_info = self._runs[job_id]
        
        try:
            async with self._session.get(
                f"{self.BASE_URL}/runs/{run_info['wandb_id']}"
            ) as response:
                if response.status != 200:
                    return JobStatus.FAILED
                
                data = await response.json()
                
                if "data" in data and "run" in data["data"]:
                    run = data["data"]["run"]
                    state = run.get("state", "running")
                    
                    # Map W&B state to JobStatus
                    status_map = {
                        "running": JobStatus.RUNNING,
                        "finished": JobStatus.COMPLETED,
                        "failed": JobStatus.FAILED,
                        "crashed": JobStatus.FAILED,
                        "killed": JobStatus.CANCELLED,
                    }
                    
                    return status_map.get(state, JobStatus.RUNNING)
                
                return JobStatus.RUNNING
                
        except aiohttp.ClientError:
            return JobStatus.FAILED
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        Mark a W&B run as stopped.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if cancellation successful
        """
        if not self._connected:
            raise RuntimeError("Not connected to W&B")
        
        if job_id not in self._runs:
            return False
        
        run_info = self._runs[job_id]
        
        try:
            # Update run state to stopped
            async with self._session.patch(
                f"{self.BASE_URL}/runs/{run_info['wandb_id']}",
                json={"state": "killed"}
            ) as response:
                success = response.status in [200, 204]
                
                if success:
                    # Cancel batch task
                    if job_id in self._batch_tasks:
                        self._batch_tasks[job_id].cancel()
                        try:
                            await self._batch_tasks[job_id]
                        except asyncio.CancelledError:
                            pass
                        del self._batch_tasks[job_id]
                    
                    # Final flush
                    await self._flush_metrics(job_id)
                    
                    # Update status
                    run_info["status"] = JobStatus.CANCELLED
                
                return success
                
        except aiohttp.ClientError:
            return False
    
    async def stream_logs(self, job_id: str) -> AsyncIterator[str]:
        """
        Stream metrics as log entries (W&B doesn't provide traditional logs).
        
        Args:
            job_id: Job identifier
            
        Yields:
            Metric updates as log lines
        """
        if not self._connected:
            raise RuntimeError("Not connected to W&B")
        
        if job_id not in self._runs:
            yield f"Run {job_id} not found"
            return
        
        run_info = self._runs[job_id]
        last_step = 0
        
        # Poll for new metrics
        while True:
            status = await self.get_job_status(job_id)
            if status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                yield f"Run completed with status: {status.value}"
                break
            
            try:
                # Fetch recent metrics
                async with self._session.get(
                    f"{self.BASE_URL}/runs/{run_info['wandb_id']}/history",
                    params={"minStep": last_step}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if "data" in data and "history" in data["data"]:
                            for entry in data["data"]["history"]:
                                step = entry.get("_step", 0)
                                if step > last_step:
                                    last_step = step
                                    # Format metrics as log line
                                    metrics_str = ", ".join(
                                        f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}"
                                        for k, v in entry.items()
                                        if not k.startswith("_")
                                    )
                                    yield f"Step {step}: {metrics_str}"
            except:
                pass
            
            await asyncio.sleep(2)
    
    async def fetch_artifact(self, job_id: str) -> bytes:
        """
        Download artifacts from a W&B run.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Artifact data as bytes
            
        Raises:
            FileNotFoundError: If artifact doesn't exist
            RuntimeError: If download fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to W&B")
        
        if job_id not in self._runs:
            raise FileNotFoundError(f"Run {job_id} not found")
        
        run_info = self._runs[job_id]
        
        try:
            # List artifacts for the run
            async with self._session.get(
                f"{self.BASE_URL}/runs/{run_info['wandb_id']}/artifacts"
            ) as response:
                if response.status != 200:
                    raise RuntimeError(f"Failed to list artifacts: {response.status}")
                
                data = await response.json()
                
                if "data" in data and "artifacts" in data["data"]:
                    artifacts = data["data"]["artifacts"]
                    if not artifacts:
                        raise FileNotFoundError("No artifacts found for this run")
                    
                    # Download first artifact
                    artifact = artifacts[0]
                    artifact_url = artifact.get("url")
                    
                    if not artifact_url:
                        raise RuntimeError("Artifact URL not found")
                    
                    # Download artifact
                    async with self._session.get(artifact_url) as artifact_response:
                        if artifact_response.status != 200:
                            raise RuntimeError(f"Failed to download artifact: {artifact_response.status}")
                        
                        return await artifact_response.read()
                else:
                    raise FileNotFoundError("No artifacts found for this run")
                    
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to fetch artifact: {str(e)}")
    
    async def upload_artifact(self, path: str, metadata: Dict) -> str:
        """
        Upload an artifact to W&B.
        
        Args:
            path: Local path to artifact
            metadata: Artifact metadata (must include 'job_id')
            
        Returns:
            Artifact ID
            
        Raises:
            FileNotFoundError: If local file doesn't exist
            RuntimeError: If upload fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to W&B")
        
        # Check file exists
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        job_id = metadata.get("job_id")
        if not job_id or job_id not in self._runs:
            raise ValueError("Valid job_id required in metadata")
        
        run_info = self._runs[job_id]
        
        try:
            # Create artifact
            artifact_name = metadata.get("name", file_path.name)
            artifact_type = metadata.get("type", "model")
            
            # Upload file
            with open(file_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename=file_path.name)
                data.add_field('name', artifact_name)
                data.add_field('type', artifact_type)
                data.add_field('metadata', json.dumps(metadata))
                
                async with self._session.post(
                    f"{self.BASE_URL}/runs/{run_info['wandb_id']}/artifacts",
                    data=data
                ) as response:
                    if response.status not in [200, 201]:
                        raise RuntimeError(f"Upload failed: {response.status}")
                    
                    result = await response.json()
                    
                    if "data" in result and "artifact" in result["data"]:
                        return result["data"]["artifact"]["id"]
                    else:
                        return artifact_name
                    
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to upload artifact: {str(e)}")
    
    async def list_resources(self) -> List[Resource]:
        """
        W&B doesn't provide compute resources.
        
        Returns:
            Empty list
        """
        return []
    
    async def get_pricing(self, resource_id: str) -> PricingInfo:
        """
        W&B pricing is subscription-based, not per-resource.
        
        Args:
            resource_id: Not used
            
        Returns:
            Default pricing info indicating free tier
            
        Raises:
            ValueError: Always, as W&B doesn't have per-resource pricing
        """
        raise ValueError("W&B uses subscription-based pricing, not per-resource pricing")
    
    def get_required_credentials(self) -> List[str]:
        """Get list of required credential keys."""
        return ["api_key"]
    
    async def compare_experiments(self, job_ids: List[str]) -> Dict[str, Any]:
        """
        Compare multiple experiments and return comparison data.
        
        Args:
            job_ids: List of job identifiers to compare
            
        Returns:
            Dictionary with comparison data including metrics, configs, and summary
        """
        if not self._connected:
            raise RuntimeError("Not connected to W&B")
        
        comparison_data = {
            "runs": [],
            "metrics": {},
            "configs": {},
        }
        
        for job_id in job_ids:
            if job_id not in self._runs:
                continue
            
            run_info = self._runs[job_id]
            
            try:
                # Fetch run details
                async with self._session.get(
                    f"{self.BASE_URL}/runs/{run_info['wandb_id']}"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if "data" in data and "run" in data["data"]:
                            run = data["data"]["run"]
                            
                            comparison_data["runs"].append({
                                "job_id": job_id,
                                "wandb_id": run_info["wandb_id"],
                                "name": run.get("name"),
                                "state": run.get("state"),
                                "created_at": run_info["created_at"],
                            })
                            
                            # Store config
                            comparison_data["configs"][job_id] = run.get("config", {})
                            
                            # Fetch summary metrics
                            summary = run.get("summary", {})
                            comparison_data["metrics"][job_id] = summary
                            
            except aiohttp.ClientError:
                continue
        
        return comparison_data
    
    def get_run_url(self, job_id: str) -> Optional[str]:
        """
        Get the W&B dashboard URL for a run.
        
        Args:
            job_id: Job identifier
            
        Returns:
            URL string or None if not available
        """
        if job_id not in self._runs:
            return None
        
        run_info = self._runs[job_id]
        entity = run_info["entity"]
        project = run_info["project"]
        wandb_id = run_info["wandb_id"]
        
        return f"https://wandb.ai/{entity}/{project}/runs/{wandb_id}"
