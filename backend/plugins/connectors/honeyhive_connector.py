"""
HoneyHive connector for LLM evaluation and model comparison.

This connector integrates with HoneyHive's API for evaluation dataset management,
model battle comparisons, and result visualization.

HoneyHive Documentation: https://docs.honeyhive.ai/
"""

from typing import Dict, List, AsyncIterator, Optional, Any
import asyncio
import aiohttp
import json
from pathlib import Path
import sys
import os
from datetime import datetime
import uuid

sys.path.append(str(Path(__file__).parent.parent.parent))

from connectors.base import (
    PlatformConnector,
    Resource,
    ResourceType,
    PricingInfo,
    TrainingConfig,
    JobStatus,
)


class HoneyHiveConnector(PlatformConnector):
    """
    Connector for HoneyHive LLM evaluation platform.
    
    HoneyHive provides evaluation dataset management, model battle comparisons,
    and result visualization. This connector handles:
    - Evaluation dataset creation and management
    - Model battle comparisons (A/B testing)
    - Result visualization and reporting
    - Quality metrics tracking
    """
    
    # Connector metadata
    name = "honeyhive"
    display_name = "HoneyHive"
    description = "LLM evaluation with dataset management and model battles"
    version = "1.0.0"
    
    # Supported features
    supports_training = False  # HoneyHive doesn't provide compute
    supports_inference = False
    supports_registry = False
    supports_tracking = True  # Evaluation tracking
    
    # API endpoints
    BASE_URL = "https://api.honeyhive.ai/v1"
    
    # Supported evaluation metrics
    SUPPORTED_METRICS = [
        "accuracy",
        "precision",
        "recall",
        "f1_score",
        "bleu",
        "rouge",
        "meteor",
        "bertscore",
        "perplexity",
        "latency",
        "cost",
        "human_preference",
    ]
    
    def __init__(self):
        self._api_key: Optional[str] = None
        self._project_id: Optional[str] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        self._evaluations: Dict[str, Dict] = {}  # job_id -> evaluation info
        self._datasets: Dict[str, Dict] = {}  # dataset_id -> dataset info
        self._battles: Dict[str, Dict] = {}  # battle_id -> battle info
    
    async def connect(self, credentials: Dict[str, str]) -> bool:
        """
        Verify connection and store credentials.
        
        Args:
            credentials: Dictionary with 'api_key' and optionally 'project_id'
            
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
        self._project_id = credentials.get("project_id")
        
        # Create session with headers
        self._session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            }
        )
        
        # Verify connection by fetching projects
        try:
            async with self._session.get(
                f"{self.BASE_URL}/projects"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "projects" in data:
                        projects = data["projects"]
                        if projects:
                            # Use provided project or default to first one
                            if not self._project_id:
                                self._project_id = projects[0]["id"]
                            self._connected = True
                            return True
                        else:
                            # Create default project if none exist
                            self._project_id = await self._create_project("default")
                            self._connected = True
                            return True
                    else:
                        raise ConnectionError("Invalid API response")
                elif response.status == 401:
                    raise ValueError("Invalid API key")
                else:
                    raise ConnectionError(f"Connection failed with status {response.status}")
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Failed to connect to HoneyHive: {str(e)}")
    
    async def _create_project(self, name: str) -> str:
        """Create a new project in HoneyHive."""
        try:
            async with self._session.post(
                f"{self.BASE_URL}/projects",
                json={"name": name}
            ) as response:
                if response.status in [200, 201]:
                    data = await response.json()
                    return data.get("id", "default")
                else:
                    return "default"
        except:
            return "default"
    
    async def disconnect(self) -> bool:
        """Disconnect and cleanup resources."""
        if self._session:
            await self._session.close()
            self._session = None
        
        self._connected = False
        self._api_key = None
        self._project_id = None
        self._evaluations.clear()
        self._datasets.clear()
        self._battles.clear()
        return True
    
    async def verify_connection(self) -> bool:
        """Verify that the connection is still valid."""
        if not self._connected or not self._session:
            return False
        
        try:
            async with self._session.get(
                f"{self.BASE_URL}/projects"
            ) as response:
                return response.status == 200
        except:
            return False
    
    async def submit_job(self, config: TrainingConfig) -> str:
        """
        Create a new evaluation job for a trained model.
        
        Args:
            config: Training configuration (used to identify the model)
            
        Returns:
            Evaluation job ID for tracking
            
        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If evaluation creation fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to HoneyHive")
        
        # Generate evaluation ID
        eval_id = str(uuid.uuid4())
        job_id = f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Prepare evaluation configuration
        eval_config = {
            "evaluation_id": eval_id,
            "project_id": self._project_id,
            "name": f"eval_{config.base_model}_{config.algorithm}",
            "model_info": {
                "base_model": config.base_model,
                "algorithm": config.algorithm,
                "rank": config.rank,
                "alpha": config.alpha,
            },
            "dataset_path": config.dataset_path,
            "validation_split": config.validation_split,
            "metrics": self.SUPPORTED_METRICS,
            "created_at": datetime.now().isoformat(),
        }
        
        # Create evaluation via API
        try:
            async with self._session.post(
                f"{self.BASE_URL}/evaluations",
                json=eval_config
            ) as response:
                if response.status not in [200, 201]:
                    raise RuntimeError(f"Failed to create evaluation: {response.status}")
                
                # Store evaluation info
                self._evaluations[job_id] = {
                    "eval_id": eval_id,
                    "config": config,
                    "status": JobStatus.PENDING,
                    "project_id": self._project_id,
                    "created_at": datetime.now().isoformat(),
                    "dataset_id": None,
                    "results": {},
                }
                
                return job_id
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to create evaluation: {str(e)}")
    
    async def create_dataset(
        self,
        name: str,
        data: List[Dict[str, Any]],
        description: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Create an evaluation dataset in HoneyHive.
        
        Args:
            name: Dataset name
            data: List of evaluation examples
            description: Optional dataset description
            metadata: Optional metadata
            
        Returns:
            Dataset ID
            
        Raises:
            RuntimeError: If dataset creation fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to HoneyHive")
        
        dataset_id = str(uuid.uuid4())
        
        try:
            async with self._session.post(
                f"{self.BASE_URL}/datasets",
                json={
                    "dataset_id": dataset_id,
                    "project_id": self._project_id,
                    "name": name,
                    "description": description or "",
                    "data": data,
                    "metadata": metadata or {},
                    "created_at": datetime.now().isoformat(),
                }
            ) as response:
                if response.status not in [200, 201]:
                    raise RuntimeError(f"Failed to create dataset: {response.status}")
                
                # Store dataset info
                self._datasets[dataset_id] = {
                    "name": name,
                    "description": description,
                    "data": data,
                    "metadata": metadata,
                    "created_at": datetime.now().isoformat(),
                    "size": len(data),
                }
                
                return dataset_id
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to create dataset: {str(e)}")
    
    async def get_dataset(self, dataset_id: str) -> Dict[str, Any]:
        """
        Retrieve an evaluation dataset.
        
        Args:
            dataset_id: Dataset identifier
            
        Returns:
            Dataset information and data
            
        Raises:
            RuntimeError: If dataset retrieval fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to HoneyHive")
        
        # Check local cache first
        if dataset_id in self._datasets:
            return self._datasets[dataset_id]
        
        try:
            async with self._session.get(
                f"{self.BASE_URL}/datasets/{dataset_id}"
            ) as response:
                if response.status != 200:
                    raise RuntimeError(f"Failed to get dataset: {response.status}")
                
                data = await response.json()
                
                # Cache dataset
                self._datasets[dataset_id] = data
                
                return data
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to get dataset: {str(e)}")
    
    async def update_dataset(
        self,
        dataset_id: str,
        data: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Update an existing evaluation dataset.
        
        Args:
            dataset_id: Dataset identifier
            data: Optional new data to replace existing
            metadata: Optional metadata to update
            
        Returns:
            True if update successful
            
        Raises:
            RuntimeError: If dataset update fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to HoneyHive")
        
        update_payload = {}
        if data is not None:
            update_payload["data"] = data
        if metadata is not None:
            update_payload["metadata"] = metadata
        
        try:
            async with self._session.patch(
                f"{self.BASE_URL}/datasets/{dataset_id}",
                json=update_payload
            ) as response:
                if response.status not in [200, 204]:
                    raise RuntimeError(f"Failed to update dataset: {response.status}")
                
                # Update local cache
                if dataset_id in self._datasets:
                    if data is not None:
                        self._datasets[dataset_id]["data"] = data
                        self._datasets[dataset_id]["size"] = len(data)
                    if metadata is not None:
                        self._datasets[dataset_id]["metadata"] = metadata
                
                return True
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to update dataset: {str(e)}")
    
    async def delete_dataset(self, dataset_id: str) -> bool:
        """
        Delete an evaluation dataset.
        
        Args:
            dataset_id: Dataset identifier
            
        Returns:
            True if deletion successful
            
        Raises:
            RuntimeError: If dataset deletion fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to HoneyHive")
        
        try:
            async with self._session.delete(
                f"{self.BASE_URL}/datasets/{dataset_id}"
            ) as response:
                if response.status not in [200, 204]:
                    raise RuntimeError(f"Failed to delete dataset: {response.status}")
                
                # Remove from local cache
                self._datasets.pop(dataset_id, None)
                
                return True
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to delete dataset: {str(e)}")
    
    async def list_datasets(self) -> List[Dict[str, Any]]:
        """
        List all evaluation datasets in the project.
        
        Returns:
            List of dataset information
            
        Raises:
            RuntimeError: If listing fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to HoneyHive")
        
        try:
            async with self._session.get(
                f"{self.BASE_URL}/projects/{self._project_id}/datasets"
            ) as response:
                if response.status != 200:
                    raise RuntimeError(f"Failed to list datasets: {response.status}")
                
                data = await response.json()
                datasets = data.get("datasets", [])
                
                # Update local cache
                for dataset in datasets:
                    dataset_id = dataset.get("dataset_id")
                    if dataset_id:
                        self._datasets[dataset_id] = dataset
                
                return datasets
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to list datasets: {str(e)}")
    
    async def create_model_battle(
        self,
        name: str,
        model_a_id: str,
        model_b_id: str,
        dataset_id: str,
        metrics: Optional[List[str]] = None
    ) -> str:
        """
        Create a model battle comparison (A/B test).
        
        Args:
            name: Battle name
            model_a_id: First model identifier
            model_b_id: Second model identifier
            dataset_id: Dataset to use for comparison
            metrics: Optional list of metrics to compute
            
        Returns:
            Battle ID
            
        Raises:
            RuntimeError: If battle creation fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to HoneyHive")
        
        battle_id = str(uuid.uuid4())
        
        if metrics is None:
            metrics = self.SUPPORTED_METRICS
        
        try:
            async with self._session.post(
                f"{self.BASE_URL}/battles",
                json={
                    "battle_id": battle_id,
                    "project_id": self._project_id,
                    "name": name,
                    "model_a_id": model_a_id,
                    "model_b_id": model_b_id,
                    "dataset_id": dataset_id,
                    "metrics": metrics,
                    "created_at": datetime.now().isoformat(),
                    "status": "pending",
                }
            ) as response:
                if response.status not in [200, 201]:
                    raise RuntimeError(f"Failed to create battle: {response.status}")
                
                # Store battle info
                self._battles[battle_id] = {
                    "name": name,
                    "model_a_id": model_a_id,
                    "model_b_id": model_b_id,
                    "dataset_id": dataset_id,
                    "metrics": metrics,
                    "created_at": datetime.now().isoformat(),
                    "status": "pending",
                    "results": None,
                }
                
                return battle_id
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to create battle: {str(e)}")
    
    async def run_model_battle(
        self,
        battle_id: str,
        model_a_outputs: List[str],
        model_b_outputs: List[str]
    ) -> Dict[str, Any]:
        """
        Execute a model battle comparison.
        
        Args:
            battle_id: Battle identifier
            model_a_outputs: Outputs from model A
            model_b_outputs: Outputs from model B
            
        Returns:
            Battle results with metrics and winner
            
        Raises:
            RuntimeError: If battle execution fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to HoneyHive")
        
        if battle_id not in self._battles:
            raise ValueError(f"Battle {battle_id} not found")
        
        battle_info = self._battles[battle_id]
        battle_info["status"] = "running"
        
        try:
            async with self._session.post(
                f"{self.BASE_URL}/battles/{battle_id}/run",
                json={
                    "model_a_outputs": model_a_outputs,
                    "model_b_outputs": model_b_outputs,
                }
            ) as response:
                if response.status not in [200, 201]:
                    battle_info["status"] = "failed"
                    raise RuntimeError(f"Failed to run battle: {response.status}")
                
                data = await response.json()
                results = data.get("results", {})
                
                # Store results
                battle_info["results"] = results
                battle_info["status"] = "completed"
                
                return results
                
        except aiohttp.ClientError as e:
            battle_info["status"] = "failed"
            raise RuntimeError(f"Failed to run battle: {str(e)}")
    
    async def get_battle_results(self, battle_id: str) -> Dict[str, Any]:
        """
        Get results from a model battle.
        
        Args:
            battle_id: Battle identifier
            
        Returns:
            Battle results including metrics, winner, and visualizations
            
        Raises:
            RuntimeError: If results retrieval fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to HoneyHive")
        
        if battle_id not in self._battles:
            raise ValueError(f"Battle {battle_id} not found")
        
        # Check if we have cached results
        battle_info = self._battles[battle_id]
        if battle_info.get("results"):
            return battle_info["results"]
        
        try:
            async with self._session.get(
                f"{self.BASE_URL}/battles/{battle_id}/results"
            ) as response:
                if response.status != 200:
                    raise RuntimeError(f"Failed to get battle results: {response.status}")
                
                data = await response.json()
                results = data.get("results", {})
                
                # Cache results
                battle_info["results"] = results
                
                return results
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to get battle results: {str(e)}")
    
    async def get_battle_visualization(
        self,
        battle_id: str,
        viz_type: str = "comparison"
    ) -> Dict[str, Any]:
        """
        Get visualization data for a model battle.
        
        Args:
            battle_id: Battle identifier
            viz_type: Type of visualization (comparison, metrics, distribution)
            
        Returns:
            Visualization data in format suitable for charting
            
        Raises:
            RuntimeError: If visualization retrieval fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to HoneyHive")
        
        if battle_id not in self._battles:
            raise ValueError(f"Battle {battle_id} not found")
        
        try:
            async with self._session.get(
                f"{self.BASE_URL}/battles/{battle_id}/visualizations/{viz_type}"
            ) as response:
                if response.status != 200:
                    raise RuntimeError(f"Failed to get visualization: {response.status}")
                
                data = await response.json()
                return data.get("visualization", {})
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to get visualization: {str(e)}")
    
    async def get_job_status(self, job_id: str) -> JobStatus:
        """
        Get the current status of an evaluation job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Current job status
        """
        if not self._connected:
            raise RuntimeError("Not connected to HoneyHive")
        
        if job_id not in self._evaluations:
            return JobStatus.FAILED
        
        eval_info = self._evaluations[job_id]
        
        # Check if we have a stored status
        if "status" in eval_info:
            return eval_info["status"]
        
        try:
            # Fetch status from API
            async with self._session.get(
                f"{self.BASE_URL}/evaluations/{eval_info['eval_id']}/status"
            ) as response:
                if response.status != 200:
                    return JobStatus.FAILED
                
                data = await response.json()
                status_str = data.get("status", "pending")
                
                # Map HoneyHive status to JobStatus
                status_map = {
                    "pending": JobStatus.PENDING,
                    "running": JobStatus.RUNNING,
                    "completed": JobStatus.COMPLETED,
                    "failed": JobStatus.FAILED,
                    "error": JobStatus.FAILED,
                }
                
                status = status_map.get(status_str, JobStatus.PENDING)
                eval_info["status"] = status
                
                return status
                
        except aiohttp.ClientError:
            return JobStatus.FAILED
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel an evaluation job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if cancellation successful
        """
        if not self._connected:
            raise RuntimeError("Not connected to HoneyHive")
        
        if job_id not in self._evaluations:
            return False
        
        eval_info = self._evaluations[job_id]
        
        try:
            # Cancel the evaluation
            async with self._session.post(
                f"{self.BASE_URL}/evaluations/{eval_info['eval_id']}/cancel"
            ) as response:
                success = response.status in [200, 204]
                
                if success:
                    eval_info["status"] = JobStatus.CANCELLED
                
                return success
                
        except aiohttp.ClientError:
            return False
    
    async def stream_logs(self, job_id: str) -> AsyncIterator[str]:
        """
        Stream evaluation progress as log entries.
        
        Args:
            job_id: Job identifier
            
        Yields:
            Progress updates as log lines
        """
        if not self._connected:
            raise RuntimeError("Not connected to HoneyHive")
        
        if job_id not in self._evaluations:
            yield f"Evaluation {job_id} not found"
            return
        
        eval_info = self._evaluations[job_id]
        last_progress = 0
        
        # Poll for progress updates
        while True:
            status = await self.get_job_status(job_id)
            
            if status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                yield f"Evaluation completed with status: {status.value}"
                
                # Show final results
                if status == JobStatus.COMPLETED and eval_info.get("results"):
                    results = eval_info["results"]
                    if "metrics" in results:
                        yield "\nEvaluation Metrics:"
                        for metric_name, score in results["metrics"].items():
                            yield f"  {metric_name}: {score:.4f}"
                
                break
            
            try:
                # Fetch progress
                async with self._session.get(
                    f"{self.BASE_URL}/evaluations/{eval_info['eval_id']}/progress"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        progress = data.get("progress", 0)
                        
                        if progress > last_progress:
                            yield f"Progress: {progress}%"
                            last_progress = progress
                        
                        # Show current metric if available
                        current_metric = data.get("current_metric")
                        if current_metric:
                            yield f"Computing: {current_metric}"
            except:
                pass
            
            await asyncio.sleep(2)
    
    async def fetch_artifact(self, job_id: str) -> bytes:
        """
        Download evaluation results as JSON.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Evaluation results as JSON bytes
            
        Raises:
            FileNotFoundError: If evaluation doesn't exist
            RuntimeError: If download fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to HoneyHive")
        
        if job_id not in self._evaluations:
            raise FileNotFoundError(f"Evaluation {job_id} not found")
        
        eval_info = self._evaluations[job_id]
        
        try:
            # Fetch complete evaluation results
            async with self._session.get(
                f"{self.BASE_URL}/evaluations/{eval_info['eval_id']}/export"
            ) as response:
                if response.status != 200:
                    raise RuntimeError(f"Failed to export evaluation: {response.status}")
                
                return await response.read()
                    
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to fetch artifact: {str(e)}")
    
    async def upload_artifact(self, path: str, metadata: Dict) -> str:
        """
        Upload evaluation results to HoneyHive.
        
        Args:
            path: Local path to evaluation results
            metadata: Artifact metadata (must include 'job_id')
            
        Returns:
            Evaluation ID
            
        Raises:
            FileNotFoundError: If local file doesn't exist
            RuntimeError: If upload fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to HoneyHive")
        
        # Check file exists
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        job_id = metadata.get("job_id")
        if not job_id or job_id not in self._evaluations:
            raise ValueError("Valid job_id required in metadata")
        
        eval_info = self._evaluations[job_id]
        
        try:
            # Upload evaluation data
            with open(file_path, 'rb') as f:
                data = f.read()
                
                async with self._session.post(
                    f"{self.BASE_URL}/evaluations/{eval_info['eval_id']}/import",
                    data=data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status not in [200, 201]:
                        raise RuntimeError(f"Upload failed: {response.status}")
                    
                    return eval_info['eval_id']
                    
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to upload artifact: {str(e)}")
    
    async def list_resources(self) -> List[Resource]:
        """
        HoneyHive doesn't provide compute resources.
        
        Returns:
            Empty list
        """
        return []
    
    async def get_pricing(self, resource_id: str) -> PricingInfo:
        """
        HoneyHive pricing is subscription-based, not per-resource.
        
        Args:
            resource_id: Not used
            
        Raises:
            ValueError: Always, as HoneyHive doesn't have per-resource pricing
        """
        raise ValueError("HoneyHive uses subscription-based pricing, not per-resource pricing")
    
    def get_required_credentials(self) -> List[str]:
        """Get list of required credential keys."""
        return ["api_key"]
    
    def get_dashboard_url(self, job_id: str) -> Optional[str]:
        """
        Get the HoneyHive dashboard URL for an evaluation.
        
        Args:
            job_id: Job identifier
            
        Returns:
            URL string or None if not available
        """
        if job_id not in self._evaluations:
            return None
        
        eval_info = self._evaluations[job_id]
        project_id = eval_info["project_id"]
        eval_id = eval_info["eval_id"]
        
        return f"https://app.honeyhive.ai/projects/{project_id}/evaluations/{eval_id}"
    
    def get_battle_url(self, battle_id: str) -> Optional[str]:
        """
        Get the HoneyHive dashboard URL for a model battle.
        
        Args:
            battle_id: Battle identifier
            
        Returns:
            URL string or None if not available
        """
        if battle_id not in self._battles:
            return None
        
        return f"https://app.honeyhive.ai/projects/{self._project_id}/battles/{battle_id}"
