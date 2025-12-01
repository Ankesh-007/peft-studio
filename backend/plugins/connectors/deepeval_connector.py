"""
DeepEval connector for LLM evaluation and testing.

This connector integrates with DeepEval's API for automated model evaluation,
test case generation, and quality assessment.

DeepEval Documentation: https://docs.confident-ai.com/
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


class DeepEvalConnector(PlatformConnector):
    """
    Connector for DeepEval LLM evaluation platform.
    
    DeepEval provides automated LLM evaluation, test case generation,
    and quality assessment. This connector handles:
    - Test case generation from validation data
    - Evaluation execution with multiple metrics
    - Metric calculation and reporting
    - Quality issue detection and suggestions
    """
    
    # Connector metadata
    name = "deepeval"
    display_name = "DeepEval"
    description = "Automated LLM evaluation and testing with DeepEval"
    version = "1.0.0"
    
    # Supported features
    supports_training = False  # DeepEval doesn't provide compute
    supports_inference = False
    supports_registry = False
    supports_tracking = True  # Evaluation tracking
    
    # API endpoints
    BASE_URL = "https://api.confident-ai.com/v1"
    
    # Supported evaluation metrics
    SUPPORTED_METRICS = [
        "answer_relevancy",
        "faithfulness",
        "contextual_relevancy",
        "hallucination",
        "toxicity",
        "bias",
        "g_eval",
        "summarization",
        "ragas",
    ]
    
    def __init__(self):
        self._api_key: Optional[str] = None
        self._project_id: Optional[str] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        self._evaluations: Dict[str, Dict] = {}  # job_id -> evaluation info
        self._test_cases: Dict[str, List[Dict]] = {}  # job_id -> test cases
    
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
            raise ConnectionError(f"Failed to connect to DeepEval: {str(e)}")
    
    async def _create_project(self, name: str) -> str:
        """Create a new project in DeepEval."""
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
        self._test_cases.clear()
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
            raise RuntimeError("Not connected to DeepEval")
        
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
            "metrics": self.SUPPORTED_METRICS,  # Use all supported metrics
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
                    "test_cases": [],
                    "results": {},
                }
                
                return job_id
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to create evaluation: {str(e)}")
    
    async def generate_test_cases(
        self,
        job_id: str,
        dataset_path: str,
        num_cases: int = 100,
        task_type: str = "text_generation"
    ) -> List[Dict[str, Any]]:
        """
        Generate test cases from validation data.
        
        Args:
            job_id: Evaluation job identifier
            dataset_path: Path to validation dataset
            num_cases: Number of test cases to generate
            task_type: Type of task (text_generation, qa, summarization, etc.)
            
        Returns:
            List of generated test cases
            
        Raises:
            RuntimeError: If test case generation fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to DeepEval")
        
        if job_id not in self._evaluations:
            raise ValueError(f"Evaluation {job_id} not found")
        
        try:
            # Request test case generation
            async with self._session.post(
                f"{self.BASE_URL}/test-cases/generate",
                json={
                    "dataset_path": dataset_path,
                    "num_cases": num_cases,
                    "task_type": task_type,
                    "project_id": self._project_id,
                }
            ) as response:
                if response.status not in [200, 201]:
                    raise RuntimeError(f"Failed to generate test cases: {response.status}")
                
                data = await response.json()
                test_cases = data.get("test_cases", [])
                
                # Store test cases
                self._test_cases[job_id] = test_cases
                self._evaluations[job_id]["test_cases"] = test_cases
                
                return test_cases
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to generate test cases: {str(e)}")
    
    async def run_evaluation(
        self,
        job_id: str,
        model_outputs: List[str],
        test_cases: Optional[List[Dict]] = None,
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Execute evaluation on model outputs.
        
        Args:
            job_id: Evaluation job identifier
            model_outputs: List of model predictions
            test_cases: Optional test cases (uses generated ones if not provided)
            metrics: Optional list of metrics to compute (uses all if not provided)
            
        Returns:
            Dictionary with evaluation results
            
        Raises:
            RuntimeError: If evaluation execution fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to DeepEval")
        
        if job_id not in self._evaluations:
            raise ValueError(f"Evaluation {job_id} not found")
        
        eval_info = self._evaluations[job_id]
        
        # Use provided test cases or stored ones
        if test_cases is None:
            test_cases = self._test_cases.get(job_id, [])
        
        if not test_cases:
            raise ValueError("No test cases available. Generate test cases first.")
        
        # Use provided metrics or all supported metrics
        if metrics is None:
            metrics = self.SUPPORTED_METRICS
        
        # Update status
        eval_info["status"] = JobStatus.RUNNING
        
        try:
            # Submit evaluation job
            async with self._session.post(
                f"{self.BASE_URL}/evaluations/{eval_info['eval_id']}/run",
                json={
                    "model_outputs": model_outputs,
                    "test_cases": test_cases,
                    "metrics": metrics,
                }
            ) as response:
                if response.status not in [200, 201]:
                    eval_info["status"] = JobStatus.FAILED
                    raise RuntimeError(f"Failed to run evaluation: {response.status}")
                
                data = await response.json()
                results = data.get("results", {})
                
                # Store results
                eval_info["results"] = results
                eval_info["status"] = JobStatus.COMPLETED
                
                return results
                
        except aiohttp.ClientError as e:
            eval_info["status"] = JobStatus.FAILED
            raise RuntimeError(f"Failed to run evaluation: {str(e)}")
    
    async def calculate_metrics(
        self,
        job_id: str,
        predictions: List[str],
        references: List[str],
        contexts: Optional[List[str]] = None,
        metric_names: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Calculate evaluation metrics for predictions.
        
        Args:
            job_id: Evaluation job identifier
            predictions: Model predictions
            references: Ground truth references
            contexts: Optional context for each prediction
            metric_names: Optional list of specific metrics to calculate
            
        Returns:
            Dictionary of metric name -> score
            
        Raises:
            RuntimeError: If metric calculation fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to DeepEval")
        
        if job_id not in self._evaluations:
            raise ValueError(f"Evaluation {job_id} not found")
        
        # Use provided metrics or all supported metrics
        if metric_names is None:
            metric_names = self.SUPPORTED_METRICS
        
        try:
            # Calculate metrics
            async with self._session.post(
                f"{self.BASE_URL}/metrics/calculate",
                json={
                    "predictions": predictions,
                    "references": references,
                    "contexts": contexts,
                    "metrics": metric_names,
                }
            ) as response:
                if response.status not in [200, 201]:
                    raise RuntimeError(f"Failed to calculate metrics: {response.status}")
                
                data = await response.json()
                metrics = data.get("metrics", {})
                
                # Store metrics in evaluation results
                eval_info = self._evaluations[job_id]
                if "metrics" not in eval_info["results"]:
                    eval_info["results"]["metrics"] = {}
                eval_info["results"]["metrics"].update(metrics)
                
                return metrics
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to calculate metrics: {str(e)}")
    
    async def detect_quality_issues(
        self,
        job_id: str,
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Detect quality issues in evaluation results and suggest improvements.
        
        Args:
            job_id: Evaluation job identifier
            threshold: Quality threshold (0-1)
            
        Returns:
            Dictionary with detected issues and suggestions
            
        Raises:
            RuntimeError: If quality detection fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to DeepEval")
        
        if job_id not in self._evaluations:
            raise ValueError(f"Evaluation {job_id} not found")
        
        eval_info = self._evaluations[job_id]
        
        if not eval_info.get("results"):
            raise ValueError("No evaluation results available. Run evaluation first.")
        
        try:
            # Analyze quality issues
            async with self._session.post(
                f"{self.BASE_URL}/evaluations/{eval_info['eval_id']}/analyze",
                json={
                    "results": eval_info["results"],
                    "threshold": threshold,
                }
            ) as response:
                if response.status not in [200, 201]:
                    raise RuntimeError(f"Failed to analyze quality: {response.status}")
                
                data = await response.json()
                
                issues = data.get("issues", [])
                suggestions = data.get("suggestions", [])
                
                # Store analysis
                eval_info["quality_analysis"] = {
                    "issues": issues,
                    "suggestions": suggestions,
                    "threshold": threshold,
                    "analyzed_at": datetime.now().isoformat(),
                }
                
                return {
                    "issues": issues,
                    "suggestions": suggestions,
                }
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to detect quality issues: {str(e)}")
    
    async def get_job_status(self, job_id: str) -> JobStatus:
        """
        Get the current status of an evaluation job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Current job status
        """
        if not self._connected:
            raise RuntimeError("Not connected to DeepEval")
        
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
                
                # Map DeepEval status to JobStatus
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
            raise RuntimeError("Not connected to DeepEval")
        
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
            raise RuntimeError("Not connected to DeepEval")
        
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
            raise RuntimeError("Not connected to DeepEval")
        
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
        Upload evaluation results to DeepEval.
        
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
            raise RuntimeError("Not connected to DeepEval")
        
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
        DeepEval doesn't provide compute resources.
        
        Returns:
            Empty list
        """
        return []
    
    async def get_pricing(self, resource_id: str) -> PricingInfo:
        """
        DeepEval pricing is subscription-based, not per-resource.
        
        Args:
            resource_id: Not used
            
        Raises:
            ValueError: Always, as DeepEval doesn't have per-resource pricing
        """
        raise ValueError("DeepEval uses subscription-based pricing, not per-resource pricing")
    
    def get_required_credentials(self) -> List[str]:
        """Get list of required credential keys."""
        return ["api_key"]
    
    async def compare_evaluations(self, job_ids: List[str]) -> Dict[str, Any]:
        """
        Compare multiple evaluations and return comparison data.
        
        Args:
            job_ids: List of job identifiers to compare
            
        Returns:
            Dictionary with comparison data including metrics and statistical significance
        """
        if not self._connected:
            raise RuntimeError("Not connected to DeepEval")
        
        comparison_data = {
            "evaluations": [],
            "metrics": {},
            "statistical_significance": {},
        }
        
        for job_id in job_ids:
            if job_id not in self._evaluations:
                continue
            
            eval_info = self._evaluations[job_id]
            
            comparison_data["evaluations"].append({
                "job_id": job_id,
                "eval_id": eval_info["eval_id"],
                "created_at": eval_info["created_at"],
                "status": eval_info.get("status", JobStatus.PENDING).value,
            })
            
            # Store metrics
            if "results" in eval_info and "metrics" in eval_info["results"]:
                comparison_data["metrics"][job_id] = eval_info["results"]["metrics"]
        
        # Calculate statistical significance if we have multiple evaluations
        if len(comparison_data["metrics"]) >= 2:
            try:
                async with self._session.post(
                    f"{self.BASE_URL}/evaluations/compare",
                    json={
                        "evaluation_ids": [
                            self._evaluations[jid]["eval_id"]
                            for jid in job_ids
                            if jid in self._evaluations
                        ]
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        comparison_data["statistical_significance"] = data.get("significance", {})
            except:
                pass
        
        return comparison_data
    
    def get_evaluation_url(self, job_id: str) -> Optional[str]:
        """
        Get the DeepEval dashboard URL for an evaluation.
        
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
        
        return f"https://app.confident-ai.com/projects/{project_id}/evaluations/{eval_id}"
