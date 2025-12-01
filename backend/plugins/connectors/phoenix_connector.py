"""
Arize Phoenix connector for LLM observability and experiment tracking.

This connector integrates with Arize Phoenix's API for LLM trace logging,
evaluation tracking, and hallucination detection.

Arize Phoenix Documentation: https://docs.arize.com/phoenix/
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


class PhoenixConnector(PlatformConnector):
    """
    Connector for Arize Phoenix LLM observability platform.
    
    Arize Phoenix provides LLM trace logging, evaluation tracking,
    and hallucination detection. This connector handles:
    - LLM trace logging with spans
    - Evaluation tracking and metrics
    - Hallucination detection integration
    - Experiment comparison
    """
    
    # Connector metadata
    name = "phoenix"
    display_name = "Arize Phoenix"
    description = "LLM observability and evaluation tracking with Arize Phoenix"
    version = "1.0.0"
    
    # Supported features
    supports_training = False  # Phoenix doesn't provide compute
    supports_inference = False
    supports_registry = False
    supports_tracking = True  # Primary feature
    
    # API endpoints
    BASE_URL = "https://app.phoenix.arize.com/v1"
    
    def __init__(self):
        self._api_key: Optional[str] = None
        self._project_id: Optional[str] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        self._traces: Dict[str, Dict] = {}  # job_id -> trace info
        self._span_batches: Dict[str, deque] = {}  # job_id -> span queue
        self._batch_size = 50  # Batch spans for efficiency
        self._batch_interval = 3.0  # Seconds between batch uploads
        self._batch_tasks: Dict[str, asyncio.Task] = {}  # Background batch tasks
    
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
            raise ConnectionError(f"Failed to connect to Arize Phoenix: {str(e)}")
    
    async def _create_project(self, name: str) -> str:
        """Create a new project in Phoenix."""
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
        # Cancel all batch tasks
        for task in self._batch_tasks.values():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Flush remaining spans
        for job_id in list(self._span_batches.keys()):
            await self._flush_spans(job_id)
        
        if self._session:
            await self._session.close()
            self._session = None
        
        self._connected = False
        self._api_key = None
        self._project_id = None
        self._traces.clear()
        self._span_batches.clear()
        self._batch_tasks.clear()
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
        Create a new Phoenix trace for tracking a training job.
        
        Args:
            config: Training configuration
            
        Returns:
            Trace ID for tracking
            
        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If trace creation fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to Arize Phoenix")
        
        # Generate trace ID
        trace_id = str(uuid.uuid4())
        job_id = f"trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Prepare trace configuration
        trace_config = {
            "trace_id": trace_id,
            "project_id": self._project_id,
            "name": f"{config.base_model}_{config.algorithm}",
            "metadata": {
                "base_model": config.base_model,
                "model_source": config.model_source,
                "algorithm": config.algorithm,
                "rank": config.rank,
                "alpha": config.alpha,
                "dropout": config.dropout,
                "target_modules": config.target_modules,
                "quantization": config.quantization or "none",
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
            "start_time": datetime.now().isoformat(),
        }
        
        # Create trace via API
        try:
            async with self._session.post(
                f"{self.BASE_URL}/traces",
                json=trace_config
            ) as response:
                if response.status not in [200, 201]:
                    raise RuntimeError(f"Failed to create trace: {response.status}")
                
                # Store trace info
                self._traces[job_id] = {
                    "trace_id": trace_id,
                    "config": config,
                    "status": JobStatus.RUNNING,
                    "project_id": self._project_id,
                    "created_at": datetime.now().isoformat(),
                    "spans": [],
                }
                
                # Initialize span batch queue
                self._span_batches[job_id] = deque()
                
                # Start background batch task
                self._batch_tasks[job_id] = asyncio.create_task(
                    self._batch_upload_loop(job_id)
                )
                
                return job_id
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to create trace: {str(e)}")
    
    async def _batch_upload_loop(self, job_id: str):
        """Background task to periodically upload batched spans."""
        try:
            while job_id in self._traces:
                await asyncio.sleep(self._batch_interval)
                await self._flush_spans(job_id)
        except asyncio.CancelledError:
            # Final flush on cancellation
            await self._flush_spans(job_id)
            raise
    
    async def _flush_spans(self, job_id: str):
        """Flush batched spans to Phoenix."""
        if job_id not in self._span_batches:
            return
        
        batch = self._span_batches[job_id]
        if not batch:
            return
        
        # Collect all spans from batch
        spans_to_send = []
        while batch:
            spans_to_send.append(batch.popleft())
        
        if not spans_to_send:
            return
        
        # Send batch to Phoenix
        trace_info = self._traces.get(job_id)
        if not trace_info:
            return
        
        try:
            async with self._session.post(
                f"{self.BASE_URL}/spans",
                json={
                    "trace_id": trace_info['trace_id'],
                    "spans": spans_to_send
                }
            ) as response:
                if response.status not in [200, 201]:
                    # Re-queue spans on failure
                    for span in spans_to_send:
                        batch.append(span)
        except aiohttp.ClientError:
            # Re-queue spans on error
            for span in spans_to_send:
                batch.append(span)
    
    async def log_span(
        self,
        job_id: str,
        name: str,
        span_type: str,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        parent_span_id: Optional[str] = None
    ):
        """
        Log a span for LLM trace tracking.
        
        Args:
            job_id: Job identifier
            name: Span name
            span_type: Type of span (e.g., 'llm', 'chain', 'tool', 'retriever')
            input_data: Input data for the span
            output_data: Output data from the span
            metadata: Additional metadata
            parent_span_id: Parent span ID for nested spans
        """
        if job_id not in self._span_batches:
            return
        
        # Create span entry
        span_id = str(uuid.uuid4())
        span_entry = {
            "span_id": span_id,
            "name": name,
            "span_type": span_type,
            "start_time": datetime.now().isoformat(),
            "end_time": datetime.now().isoformat(),
            "input": input_data or {},
            "output": output_data or {},
            "metadata": metadata or {},
            "parent_span_id": parent_span_id,
        }
        
        # Add to batch queue
        self._span_batches[job_id].append(span_entry)
        
        # Store span ID in trace
        if job_id in self._traces:
            self._traces[job_id]["spans"].append(span_id)
        
        # Flush if batch is full
        if len(self._span_batches[job_id]) >= self._batch_size:
            await self._flush_spans(job_id)
        
        return span_id
    
    async def log_metrics(self, job_id: str, metrics: Dict[str, Any], step: Optional[int] = None):
        """
        Log metrics as a span in the trace.
        
        Args:
            job_id: Job identifier
            metrics: Dictionary of metric name -> value
            step: Training step number
        """
        await self.log_span(
            job_id=job_id,
            name=f"metrics_step_{step}" if step is not None else "metrics",
            span_type="metrics",
            output_data=metrics,
            metadata={"step": step} if step is not None else {}
        )
    
    async def log_evaluation(
        self,
        job_id: str,
        eval_name: str,
        predictions: List[str],
        references: List[str],
        scores: Dict[str, float]
    ):
        """
        Log evaluation results.
        
        Args:
            job_id: Job identifier
            eval_name: Name of the evaluation
            predictions: Model predictions
            references: Reference/ground truth values
            scores: Evaluation scores
        """
        await self.log_span(
            job_id=job_id,
            name=f"evaluation_{eval_name}",
            span_type="evaluation",
            input_data={
                "predictions": predictions,
                "references": references,
            },
            output_data=scores,
            metadata={"eval_name": eval_name}
        )
    
    async def detect_hallucination(
        self,
        job_id: str,
        context: str,
        response: str,
        threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        Detect hallucinations in LLM responses.
        
        Args:
            job_id: Job identifier
            context: Context/source text
            response: LLM response to check
            threshold: Hallucination detection threshold
            
        Returns:
            Dictionary with hallucination detection results
        """
        if not self._connected:
            raise RuntimeError("Not connected to Arize Phoenix")
        
        try:
            async with self._session.post(
                f"{self.BASE_URL}/hallucination/detect",
                json={
                    "context": context,
                    "response": response,
                    "threshold": threshold,
                }
            ) as response_obj:
                if response_obj.status == 200:
                    result = await response_obj.json()
                    
                    # Log hallucination detection as a span
                    await self.log_span(
                        job_id=job_id,
                        name="hallucination_detection",
                        span_type="hallucination",
                        input_data={
                            "context": context,
                            "response": response,
                            "threshold": threshold,
                        },
                        output_data=result,
                    )
                    
                    return result
                else:
                    return {
                        "is_hallucination": False,
                        "confidence": 0.0,
                        "error": f"Detection failed with status {response_obj.status}"
                    }
        except aiohttp.ClientError as e:
            return {
                "is_hallucination": False,
                "confidence": 0.0,
                "error": str(e)
            }
    
    async def get_job_status(self, job_id: str) -> JobStatus:
        """
        Get the current status of a Phoenix trace.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Current job status
        """
        if not self._connected:
            raise RuntimeError("Not connected to Arize Phoenix")
        
        if job_id not in self._traces:
            return JobStatus.FAILED
        
        trace_info = self._traces[job_id]
        
        try:
            async with self._session.get(
                f"{self.BASE_URL}/traces/{trace_info['trace_id']}"
            ) as response:
                if response.status != 200:
                    return JobStatus.FAILED
                
                data = await response.json()
                
                if "trace" in data:
                    trace = data["trace"]
                    status = trace.get("status", "running")
                    
                    # Map Phoenix status to JobStatus
                    status_map = {
                        "running": JobStatus.RUNNING,
                        "completed": JobStatus.COMPLETED,
                        "failed": JobStatus.FAILED,
                        "error": JobStatus.FAILED,
                    }
                    
                    return status_map.get(status, JobStatus.RUNNING)
                
                return JobStatus.RUNNING
                
        except aiohttp.ClientError:
            return JobStatus.FAILED
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        Mark a Phoenix trace as completed.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if cancellation successful
        """
        if not self._connected:
            raise RuntimeError("Not connected to Arize Phoenix")
        
        if job_id not in self._traces:
            return False
        
        trace_info = self._traces[job_id]
        
        try:
            # End the trace
            async with self._session.patch(
                f"{self.BASE_URL}/traces/{trace_info['trace_id']}",
                json={
                    "status": "completed",
                    "end_time": datetime.now().isoformat()
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
                    await self._flush_spans(job_id)
                    
                    # Update status
                    trace_info["status"] = JobStatus.CANCELLED
                
                return success
                
        except aiohttp.ClientError:
            return False
    
    async def stream_logs(self, job_id: str) -> AsyncIterator[str]:
        """
        Stream spans as log entries.
        
        Args:
            job_id: Job identifier
            
        Yields:
            Span updates as log lines
        """
        if not self._connected:
            raise RuntimeError("Not connected to Arize Phoenix")
        
        if job_id not in self._traces:
            yield f"Trace {job_id} not found"
            return
        
        trace_info = self._traces[job_id]
        last_span_count = 0
        
        # Poll for new spans
        while True:
            status = await self.get_job_status(job_id)
            if status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                yield f"Trace completed with status: {status.value}"
                break
            
            try:
                # Fetch trace with spans
                async with self._session.get(
                    f"{self.BASE_URL}/traces/{trace_info['trace_id']}/spans"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if "spans" in data:
                            spans = data["spans"]
                            if len(spans) > last_span_count:
                                # Yield new spans
                                for span in spans[last_span_count:]:
                                    span_name = span.get("name", "unknown")
                                    span_type = span.get("span_type", "unknown")
                                    yield f"[{span_type}] {span_name}"
                                last_span_count = len(spans)
            except:
                pass
            
            await asyncio.sleep(2)
    
    async def fetch_artifact(self, job_id: str) -> bytes:
        """
        Download trace data from Phoenix.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Trace data as JSON bytes
            
        Raises:
            FileNotFoundError: If trace doesn't exist
            RuntimeError: If download fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to Arize Phoenix")
        
        if job_id not in self._traces:
            raise FileNotFoundError(f"Trace {job_id} not found")
        
        trace_info = self._traces[job_id]
        
        try:
            # Fetch complete trace with spans
            async with self._session.get(
                f"{self.BASE_URL}/traces/{trace_info['trace_id']}/export"
            ) as response:
                if response.status != 200:
                    raise RuntimeError(f"Failed to export trace: {response.status}")
                
                return await response.read()
                    
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to fetch artifact: {str(e)}")
    
    async def upload_artifact(self, path: str, metadata: Dict) -> str:
        """
        Upload trace data to Phoenix.
        
        Args:
            path: Local path to trace data
            metadata: Artifact metadata (must include 'job_id')
            
        Returns:
            Trace ID
            
        Raises:
            FileNotFoundError: If local file doesn't exist
            RuntimeError: If upload fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to Arize Phoenix")
        
        # Check file exists
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        job_id = metadata.get("job_id")
        if not job_id or job_id not in self._traces:
            raise ValueError("Valid job_id required in metadata")
        
        trace_info = self._traces[job_id]
        
        try:
            # Upload trace data
            with open(file_path, 'rb') as f:
                data = await f.read()
                
                async with self._session.post(
                    f"{self.BASE_URL}/traces/{trace_info['trace_id']}/import",
                    data=data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status not in [200, 201]:
                        raise RuntimeError(f"Upload failed: {response.status}")
                    
                    return trace_info['trace_id']
                    
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to upload artifact: {str(e)}")
    
    async def list_resources(self) -> List[Resource]:
        """
        Phoenix doesn't provide compute resources.
        
        Returns:
            Empty list
        """
        return []
    
    async def get_pricing(self, resource_id: str) -> PricingInfo:
        """
        Phoenix pricing is subscription-based, not per-resource.
        
        Args:
            resource_id: Not used
            
        Raises:
            ValueError: Always, as Phoenix doesn't have per-resource pricing
        """
        raise ValueError("Phoenix uses subscription-based pricing, not per-resource pricing")
    
    def get_required_credentials(self) -> List[str]:
        """Get list of required credential keys."""
        return ["api_key"]
    
    async def compare_traces(self, job_ids: List[str]) -> Dict[str, Any]:
        """
        Compare multiple traces and return comparison data.
        
        Args:
            job_ids: List of job identifiers to compare
            
        Returns:
            Dictionary with comparison data including spans, metrics, and evaluations
        """
        if not self._connected:
            raise RuntimeError("Not connected to Arize Phoenix")
        
        comparison_data = {
            "traces": [],
            "spans": {},
            "evaluations": {},
        }
        
        for job_id in job_ids:
            if job_id not in self._traces:
                continue
            
            trace_info = self._traces[job_id]
            
            try:
                # Fetch trace details
                async with self._session.get(
                    f"{self.BASE_URL}/traces/{trace_info['trace_id']}"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if "trace" in data:
                            trace = data["trace"]
                            
                            comparison_data["traces"].append({
                                "job_id": job_id,
                                "trace_id": trace_info["trace_id"],
                                "name": trace.get("name"),
                                "status": trace.get("status"),
                                "created_at": trace_info["created_at"],
                            })
                            
                            # Fetch spans
                            async with self._session.get(
                                f"{self.BASE_URL}/traces/{trace_info['trace_id']}/spans"
                            ) as spans_response:
                                if spans_response.status == 200:
                                    spans_data = await spans_response.json()
                                    comparison_data["spans"][job_id] = spans_data.get("spans", [])
                            
                            # Extract evaluation spans
                            eval_spans = [
                                span for span in comparison_data["spans"].get(job_id, [])
                                if span.get("span_type") == "evaluation"
                            ]
                            comparison_data["evaluations"][job_id] = eval_spans
                            
            except aiohttp.ClientError:
                continue
        
        return comparison_data
    
    def get_trace_url(self, job_id: str) -> Optional[str]:
        """
        Get the Phoenix dashboard URL for a trace.
        
        Args:
            job_id: Job identifier
            
        Returns:
            URL string or None if not available
        """
        if job_id not in self._traces:
            return None
        
        trace_info = self._traces[job_id]
        project_id = trace_info["project_id"]
        trace_id = trace_info["trace_id"]
        
        return f"https://app.phoenix.arize.com/projects/{project_id}/traces/{trace_id}"
