"""
Comet ML connector for experiment tracking.

This connector integrates with Comet ML's API to create experiments, log metrics,
track assets, and compare experiments with model registry integration.

Comet ML API Documentation: https://www.comet.com/docs/v2/api-and-sdk/
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


class CometMLConnector(PlatformConnector):
    """
    Connector for Comet ML experiment tracking platform.
    
    Comet ML provides experiment tracking, model registry, and asset comparison.
    This connector handles:
    - Experiment creation and logging
    - Metric and parameter tracking
    - Asset comparison features
    - Model registry integration
    """
    
    # Connector metadata
    name = "cometml"
    display_name = "Comet ML"
    description = "Experiment tracking and model registry with Comet ML"
    version = "1.0.0"
    
    # Supported features
    supports_training = False  # Comet ML doesn't provide compute
    supports_inference = False
    supports_registry = True  # Model registry support
    supports_tracking = True  # Primary feature
    
    # API endpoints
    BASE_URL = "https://www.comet.com/api/rest/v2"
    
    def __init__(self):
        self._api_key: Optional[str] = None
        self._workspace: Optional[str] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        self._experiments: Dict[str, Dict] = {}  # job_id -> experiment info
        self._metric_batches: Dict[str, deque] = {}  # job_id -> metric queue
        self._batch_size = 100  # Batch metrics for efficiency
        self._batch_interval = 5.0  # Seconds between batch uploads
        self._batch_tasks: Dict[str, asyncio.Task] = {}  # Background batch tasks
    
    async def connect(self, credentials: Dict[str, str]) -> bool:
        """
        Verify connection and store credentials.
        
        Args:
            credentials: Dictionary with 'api_key' and optionally 'workspace'
            
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
        self._workspace = credentials.get("workspace")
        
        # Create session with headers
        self._session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            }
        )
        
        # Verify connection by fetching workspaces
        try:
            async with self._session.get(
                f"{self.BASE_URL}/workspaces"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "workspaces" in data:
                        workspaces = data["workspaces"]
                        if workspaces:
                            # Use provided workspace or default to first one
                            if not self._workspace:
                                self._workspace = workspaces[0]["workspaceName"]
                            self._connected = True
                            return True
                        else:
                            raise ConnectionError("No workspaces found")
                    else:
                        raise ConnectionError("Invalid API response")
                elif response.status == 401:
                    raise ValueError("Invalid API key")
                else:
                    raise ConnectionError(f"Connection failed with status {response.status}")
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Failed to connect to Comet ML: {str(e)}")
    
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
        self._workspace = None
        self._experiments.clear()
        self._metric_batches.clear()
        self._batch_tasks.clear()
        return True
    
    async def verify_connection(self) -> bool:
        """Verify that the connection is still valid."""
        if not self._connected or not self._session:
            return False
        
        try:
            async with self._session.get(
                f"{self.BASE_URL}/workspaces"
            ) as response:
                return response.status == 200
        except:
            return False
    
    async def submit_job(self, config: TrainingConfig) -> str:
        """
        Create a new Comet ML experiment for tracking a training job.
        
        Args:
            config: Training configuration
            
        Returns:
            Experiment key for tracking
            
        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If experiment creation fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to Comet ML")
        
        # Generate job ID
        job_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Prepare experiment configuration
        experiment_config = {
            "workspaceName": self._workspace,
            "projectName": config.project_name,
            "experimentName": f"{config.base_model}_{config.algorithm}",
        }
        
        # Create experiment via API
        try:
            async with self._session.post(
                f"{self.BASE_URL}/write/experiment/create",
                json=experiment_config
            ) as response:
                if response.status not in [200, 201]:
                    raise RuntimeError(f"Failed to create experiment: {response.status}")
                
                data = await response.json()
                
                # Extract experiment key from response
                if "experimentKey" in data:
                    experiment_key = data["experimentKey"]
                else:
                    raise RuntimeError("No experiment key in response")
                
                # Store experiment info
                self._experiments[job_id] = {
                    "experiment_key": experiment_key,
                    "config": config,
                    "status": JobStatus.RUNNING,
                    "project": config.project_name,
                    "workspace": self._workspace,
                    "created_at": datetime.now().isoformat(),
                }
                
                # Log parameters
                await self._log_parameters(experiment_key, {
                    "base_model": config.base_model,
                    "model_source": config.model_source,
                    "algorithm": config.algorithm,
                    "rank": config.rank,
                    "alpha": config.alpha,
                    "dropout": config.dropout,
                    "target_modules": ",".join(config.target_modules),
                    "quantization": config.quantization or "none",
                    "learning_rate": config.learning_rate,
                    "batch_size": config.batch_size,
                    "gradient_accumulation_steps": config.gradient_accumulation_steps,
                    "num_epochs": config.num_epochs,
                    "warmup_steps": config.warmup_steps,
                    "provider": config.provider,
                    "dataset_path": config.dataset_path,
                    "validation_split": config.validation_split,
                })
                
                # Add tags
                await self._add_tags(experiment_key, [
                    config.algorithm,
                    config.provider,
                    config.model_source,
                ])
                
                # Initialize metric batch queue
                self._metric_batches[job_id] = deque()
                
                # Start background batch task
                self._batch_tasks[job_id] = asyncio.create_task(
                    self._batch_upload_loop(job_id)
                )
                
                return job_id
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to create experiment: {str(e)}")
    
    async def _log_parameters(self, experiment_key: str, parameters: Dict[str, Any]):
        """Log parameters to an experiment."""
        try:
            async with self._session.post(
                f"{self.BASE_URL}/write/experiment/parameters",
                json={
                    "experimentKey": experiment_key,
                    "parameters": [
                        {"name": k, "value": str(v)}
                        for k, v in parameters.items()
                    ]
                }
            ) as response:
                if response.status not in [200, 201]:
                    # Log error but don't fail
                    pass
        except aiohttp.ClientError:
            pass
    
    async def _add_tags(self, experiment_key: str, tags: List[str]):
        """Add tags to an experiment."""
        try:
            async with self._session.post(
                f"{self.BASE_URL}/write/experiment/tags",
                json={
                    "experimentKey": experiment_key,
                    "tags": tags
                }
            ) as response:
                if response.status not in [200, 201]:
                    # Log error but don't fail
                    pass
        except aiohttp.ClientError:
            pass
    
    async def _batch_upload_loop(self, job_id: str):
        """Background task to periodically upload batched metrics."""
        try:
            while job_id in self._experiments:
                await asyncio.sleep(self._batch_interval)
                await self._flush_metrics(job_id)
        except asyncio.CancelledError:
            # Final flush on cancellation
            await self._flush_metrics(job_id)
            raise
    
    async def _flush_metrics(self, job_id: str):
        """Flush batched metrics to Comet ML."""
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
        
        # Send batch to Comet ML
        exp_info = self._experiments.get(job_id)
        if not exp_info:
            return
        
        try:
            async with self._session.post(
                f"{self.BASE_URL}/write/experiment/metrics",
                json={
                    "experimentKey": exp_info['experiment_key'],
                    "metrics": metrics_to_send
                }
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
        for name, value in metrics.items():
            metric_entry = {
                "metricName": name,
                "metricValue": value,
                "step": step if step is not None else 0,
                "timestamp": int(datetime.now().timestamp() * 1000),  # milliseconds
            }
            self._metric_batches[job_id].append(metric_entry)
        
        # Flush if batch is full
        if len(self._metric_batches[job_id]) >= self._batch_size:
            await self._flush_metrics(job_id)
    
    async def get_job_status(self, job_id: str) -> JobStatus:
        """
        Get the current status of a Comet ML experiment.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Current job status
        """
        if not self._connected:
            raise RuntimeError("Not connected to Comet ML")
        
        if job_id not in self._experiments:
            return JobStatus.FAILED
        
        exp_info = self._experiments[job_id]
        
        try:
            async with self._session.get(
                f"{self.BASE_URL}/experiment",
                params={
                    "experimentKey": exp_info['experiment_key']
                }
            ) as response:
                if response.status != 200:
                    return JobStatus.FAILED
                
                data = await response.json()
                
                if "experiment" in data:
                    experiment = data["experiment"]
                    status = experiment.get("status", "running")
                    
                    # Map Comet ML status to JobStatus
                    status_map = {
                        "running": JobStatus.RUNNING,
                        "completed": JobStatus.COMPLETED,
                        "failed": JobStatus.FAILED,
                        "killed": JobStatus.CANCELLED,
                    }
                    
                    return status_map.get(status, JobStatus.RUNNING)
                
                return JobStatus.RUNNING
                
        except aiohttp.ClientError:
            return JobStatus.FAILED
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        Mark a Comet ML experiment as stopped.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if cancellation successful
        """
        if not self._connected:
            raise RuntimeError("Not connected to Comet ML")
        
        if job_id not in self._experiments:
            return False
        
        exp_info = self._experiments[job_id]
        
        try:
            # End the experiment
            async with self._session.post(
                f"{self.BASE_URL}/write/experiment/end",
                json={
                    "experimentKey": exp_info['experiment_key']
                }
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
                    exp_info["status"] = JobStatus.CANCELLED
                
                return success
                
        except aiohttp.ClientError:
            return False
    
    async def stream_logs(self, job_id: str) -> AsyncIterator[str]:
        """
        Stream metrics as log entries (Comet ML doesn't provide traditional logs).
        
        Args:
            job_id: Job identifier
            
        Yields:
            Metric updates as log lines
        """
        if not self._connected:
            raise RuntimeError("Not connected to Comet ML")
        
        if job_id not in self._experiments:
            yield f"Experiment {job_id} not found"
            return
        
        exp_info = self._experiments[job_id]
        last_step = 0
        
        # Poll for new metrics
        while True:
            status = await self.get_job_status(job_id)
            if status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                yield f"Experiment completed with status: {status.value}"
                break
            
            try:
                # Fetch recent metrics
                async with self._session.get(
                    f"{self.BASE_URL}/experiment/metrics",
                    params={
                        "experimentKey": exp_info['experiment_key']
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if "metrics" in data:
                            for metric in data["metrics"]:
                                step = metric.get("step", 0)
                                if step > last_step:
                                    last_step = step
                                    name = metric.get("metricName", "unknown")
                                    value = metric.get("metricValue", 0)
                                    yield f"Step {step}: {name}={value:.4f}" if isinstance(value, float) else f"Step {step}: {name}={value}"
            except:
                pass
            
            await asyncio.sleep(2)
    
    async def fetch_artifact(self, job_id: str) -> bytes:
        """
        Download artifacts from a Comet ML experiment.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Artifact data as bytes
            
        Raises:
            FileNotFoundError: If artifact doesn't exist
            RuntimeError: If download fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to Comet ML")
        
        if job_id not in self._experiments:
            raise FileNotFoundError(f"Experiment {job_id} not found")
        
        exp_info = self._experiments[job_id]
        
        try:
            # List assets for the experiment
            async with self._session.get(
                f"{self.BASE_URL}/experiment/assets",
                params={
                    "experimentKey": exp_info['experiment_key']
                }
            ) as response:
                if response.status != 200:
                    raise RuntimeError(f"Failed to list assets: {response.status}")
                
                data = await response.json()
                
                if "assets" in data:
                    assets = data["assets"]
                    if not assets:
                        raise FileNotFoundError("No assets found for this experiment")
                    
                    # Download first asset
                    asset = assets[0]
                    asset_id = asset.get("assetId")
                    
                    if not asset_id:
                        raise RuntimeError("Asset ID not found")
                    
                    # Download asset
                    async with self._session.get(
                        f"{self.BASE_URL}/experiment/asset/download",
                        params={
                            "experimentKey": exp_info['experiment_key'],
                            "assetId": asset_id
                        }
                    ) as asset_response:
                        if asset_response.status != 200:
                            raise RuntimeError(f"Failed to download asset: {asset_response.status}")
                        
                        return await asset_response.read()
                else:
                    raise FileNotFoundError("No assets found for this experiment")
                    
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to fetch artifact: {str(e)}")
    
    async def upload_artifact(self, path: str, metadata: Dict) -> str:
        """
        Upload an artifact to Comet ML.
        
        Args:
            path: Local path to artifact
            metadata: Artifact metadata (must include 'job_id')
            
        Returns:
            Asset ID
            
        Raises:
            FileNotFoundError: If local file doesn't exist
            RuntimeError: If upload fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to Comet ML")
        
        # Check file exists
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        job_id = metadata.get("job_id")
        if not job_id or job_id not in self._experiments:
            raise ValueError("Valid job_id required in metadata")
        
        exp_info = self._experiments[job_id]
        
        try:
            # Upload file
            with open(file_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename=file_path.name)
                data.add_field('experimentKey', exp_info['experiment_key'])
                data.add_field('fileName', file_path.name)
                data.add_field('type', metadata.get("type", "asset"))
                
                async with self._session.post(
                    f"{self.BASE_URL}/write/experiment/upload-asset",
                    data=data
                ) as response:
                    if response.status not in [200, 201]:
                        raise RuntimeError(f"Upload failed: {response.status}")
                    
                    result = await response.json()
                    
                    if "assetId" in result:
                        return result["assetId"]
                    else:
                        return file_path.name
                    
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to upload artifact: {str(e)}")
    
    async def list_resources(self) -> List[Resource]:
        """
        Comet ML doesn't provide compute resources.
        
        Returns:
            Empty list
        """
        return []
    
    async def get_pricing(self, resource_id: str) -> PricingInfo:
        """
        Comet ML pricing is subscription-based, not per-resource.
        
        Args:
            resource_id: Not used
            
        Returns:
            Default pricing info indicating free tier
            
        Raises:
            ValueError: Always, as Comet ML doesn't have per-resource pricing
        """
        raise ValueError("Comet ML uses subscription-based pricing, not per-resource pricing")
    
    def get_required_credentials(self) -> List[str]:
        """Get list of required credential keys."""
        return ["api_key"]
    
    async def compare_experiments(self, job_ids: List[str]) -> Dict[str, Any]:
        """
        Compare multiple experiments and return comparison data.
        
        Args:
            job_ids: List of job identifiers to compare
            
        Returns:
            Dictionary with comparison data including metrics, parameters, and summary
        """
        if not self._connected:
            raise RuntimeError("Not connected to Comet ML")
        
        comparison_data = {
            "experiments": [],
            "metrics": {},
            "parameters": {},
        }
        
        for job_id in job_ids:
            if job_id not in self._experiments:
                continue
            
            exp_info = self._experiments[job_id]
            
            try:
                # Fetch experiment details
                async with self._session.get(
                    f"{self.BASE_URL}/experiment",
                    params={
                        "experimentKey": exp_info['experiment_key']
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if "experiment" in data:
                            experiment = data["experiment"]
                            
                            comparison_data["experiments"].append({
                                "job_id": job_id,
                                "experiment_key": exp_info['experiment_key'],
                                "name": experiment.get("experimentName"),
                                "status": experiment.get("status"),
                                "created_at": exp_info["created_at"],
                            })
                            
                            # Store parameters
                            comparison_data["parameters"][job_id] = experiment.get("parameters", {})
                            
                            # Fetch metrics summary
                            async with self._session.get(
                                f"{self.BASE_URL}/experiment/metrics/summary",
                                params={
                                    "experimentKey": exp_info['experiment_key']
                                }
                            ) as metrics_response:
                                if metrics_response.status == 200:
                                    metrics_data = await metrics_response.json()
                                    comparison_data["metrics"][job_id] = metrics_data.get("metrics", {})
                            
            except aiohttp.ClientError:
                continue
        
        return comparison_data
    
    def get_experiment_url(self, job_id: str) -> Optional[str]:
        """
        Get the Comet ML dashboard URL for an experiment.
        
        Args:
            job_id: Job identifier
            
        Returns:
            URL string or None if not available
        """
        if job_id not in self._experiments:
            return None
        
        exp_info = self._experiments[job_id]
        workspace = exp_info["workspace"]
        project = exp_info["project"]
        experiment_key = exp_info["experiment_key"]
        
        return f"https://www.comet.com/{workspace}/{project}/{experiment_key}"
    
    async def register_model(self, job_id: str, model_name: str, version: Optional[str] = None) -> str:
        """
        Register a model in Comet ML's model registry.
        
        Args:
            job_id: Job identifier
            model_name: Name for the model in registry
            version: Optional version string
            
        Returns:
            Model registry ID
            
        Raises:
            RuntimeError: If registration fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to Comet ML")
        
        if job_id not in self._experiments:
            raise ValueError(f"Experiment {job_id} not found")
        
        exp_info = self._experiments[job_id]
        
        try:
            # Register model
            async with self._session.post(
                f"{self.BASE_URL}/write/registry-model/create",
                json={
                    "workspaceName": self._workspace,
                    "modelName": model_name,
                    "experimentKey": exp_info['experiment_key'],
                    "version": version or "1.0.0",
                }
            ) as response:
                if response.status not in [200, 201]:
                    raise RuntimeError(f"Failed to register model: {response.status}")
                
                data = await response.json()
                
                if "registryModelId" in data:
                    return data["registryModelId"]
                else:
                    return model_name
                    
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to register model: {str(e)}")
