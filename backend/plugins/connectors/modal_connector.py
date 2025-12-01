"""
Modal connector for serverless function deployment and inference.

This connector integrates with Modal's serverless platform to:
- Deploy functions for inference
- Implement cold-start optimization
- Track usage and costs
- Manage serverless deployments

Modal API Documentation: https://modal.com/docs
"""

from typing import Dict, List, AsyncIterator, Optional, Any
import asyncio
import aiohttp
import json
from pathlib import Path
import sys
from datetime import datetime
import hashlib

sys.path.append(str(Path(__file__).parent.parent.parent))

from connectors.base import (
    PlatformConnector,
    Resource,
    ResourceType,
    PricingInfo,
    TrainingConfig,
    JobStatus,
)


class ModalConnector(PlatformConnector):
    """
    Connector for Modal serverless function deployment platform.
    
    Modal provides serverless function deployment with cold-start optimization.
    This connector handles:
    - Function deployment for inference
    - Cold-start optimization with container caching
    - Usage tracking and monitoring
    - Serverless inference execution
    """
    
    # Connector metadata
    name = "modal"
    display_name = "Modal"
    description = "Serverless function deployment with cold-start optimization"
    version = "1.0.0"
    
    # Supported features
    supports_training = False
    supports_inference = True
    supports_registry = False
    supports_tracking = False
    
    # API endpoints
    BASE_URL = "https://api.modal.com/v1"
    
    def __init__(self):
        self._token_id: Optional[str] = None
        self._token_secret: Optional[str] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        self._functions: Dict[str, Dict] = {}
        self._deployments: Dict[str, Dict] = {}
        # Cache for cold-start optimization
        self._container_cache: Dict[str, str] = {}
    
    async def connect(self, credentials: Dict[str, str]) -> bool:
        """
        Verify connection and store credentials.
        
        Args:
            credentials: Dictionary with 'token_id' and 'token_secret'
            
        Returns:
            True if connection successful
            
        Raises:
            ConnectionError: If connection fails
            ValueError: If credentials are invalid
        """
        token_id = credentials.get("token_id")
        token_secret = credentials.get("token_secret")
        
        if not token_id or not token_secret:
            raise ValueError("token_id and token_secret are required")
        
        self._token_id = token_id
        self._token_secret = token_secret
        
        # Create session with headers
        headers = {
            "Authorization": f"Bearer {self._token_id}:{self._token_secret}",
            "Content-Type": "application/json",
        }
        
        self._session = aiohttp.ClientSession(headers=headers)
        
        # Verify connection by fetching workspace info
        try:
            async with self._session.get(f"{self.BASE_URL}/workspaces/me") as response:
                if response.status == 200:
                    data = await response.json()
                    if "id" in data:
                        self._connected = True
                        return True
                    else:
                        raise ConnectionError("Invalid API response")
                elif response.status == 401:
                    raise ValueError("Invalid credentials")
                else:
                    raise ConnectionError(f"Connection failed with status {response.status}")
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Failed to connect to Modal: {str(e)}")
    
    async def disconnect(self) -> bool:
        """Disconnect and cleanup resources."""
        if self._session:
            await self._session.close()
            self._session = None
        
        self._connected = False
        self._token_id = None
        self._token_secret = None
        self._functions.clear()
        self._deployments.clear()
        self._container_cache.clear()
        return True
    
    async def verify_connection(self) -> bool:
        """Verify that the connection is still valid."""
        if not self._connected or not self._session:
            return False
        
        try:
            async with self._session.get(f"{self.BASE_URL}/workspaces/me") as response:
                return response.status == 200
        except:
            return False
    
    def _generate_container_id(self, base_model: str, dependencies: List[str]) -> str:
        """
        Generate a unique container ID for caching.
        
        This enables cold-start optimization by reusing containers
        with the same base model and dependencies.
        
        Args:
            base_model: Base model identifier
            dependencies: List of Python dependencies
            
        Returns:
            Container ID hash
        """
        # Create deterministic hash from model and dependencies
        content = f"{base_model}:{':'.join(sorted(dependencies))}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    async def deploy_function(
        self,
        function_name: str,
        base_model: str,
        adapter_path: Optional[str] = None,
        deployment_config: Optional[Dict] = None,
    ) -> str:
        """
        Deploy a serverless function for inference.
        
        This creates a Modal function with cold-start optimization:
        - Container image is cached based on base model and dependencies
        - Model weights are preloaded in the container
        - Subsequent invocations reuse warm containers
        
        Args:
            function_name: Name for the function
            base_model: Base model identifier
            adapter_path: Optional path to adapter files
            deployment_config: Optional deployment configuration
            
        Returns:
            Function ID
            
        Raises:
            RuntimeError: If deployment fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to Modal")
        
        config = deployment_config or {}
        
        # Define dependencies for the container
        dependencies = [
            "torch",
            "transformers",
            "accelerate",
            "safetensors",
        ]
        
        # Add quantization libraries if needed
        if config.get("quantization"):
            dependencies.extend(["bitsandbytes", "auto-gptq"])
        
        # Generate container ID for caching
        container_id = self._generate_container_id(base_model, dependencies)
        
        # Check if we have a cached container
        cached_image = self._container_cache.get(container_id)
        
        # Build function definition
        function_payload = {
            "name": function_name,
            "image": {
                "base": "python:3.10-slim",
                "python_packages": dependencies,
                "cached_image_id": cached_image,  # Reuse if available
            },
            "resources": {
                "gpu": config.get("gpu_type", "A10G"),
                "memory_mb": config.get("memory_mb", 16384),
                "cpu_count": config.get("cpu_count", 4),
            },
            "environment": {
                "BASE_MODEL": base_model,
                "ADAPTER_PATH": adapter_path or "",
                "QUANTIZATION": config.get("quantization", ""),
                "MAX_BATCH_SIZE": str(config.get("max_batch_size", 8)),
            },
            "cold_start_optimization": {
                "keep_warm": config.get("keep_warm", 1),  # Keep 1 container warm
                "max_containers": config.get("max_containers", 10),
                "preload_model": True,  # Preload model in container
            },
            "code": self._generate_inference_code(base_model, adapter_path),
        }
        
        try:
            async with self._session.post(
                f"{self.BASE_URL}/functions",
                json=function_payload
            ) as response:
                if response.status not in [200, 201]:
                    error_text = await response.text()
                    raise RuntimeError(f"Failed to deploy function: {error_text}")
                
                data = await response.json()
                function_id = data["id"]
                
                # Cache the container image ID for future deployments
                if "image_id" in data:
                    self._container_cache[container_id] = data["image_id"]
                
                # Store function info
                self._functions[function_id] = {
                    "id": function_id,
                    "name": function_name,
                    "base_model": base_model,
                    "adapter_path": adapter_path,
                    "status": "deploying",
                    "url": data.get("url"),
                    "container_id": container_id,
                    "created_at": datetime.now().isoformat(),
                }
                
                return function_id
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to deploy function: {str(e)}")
    
    def _generate_inference_code(
        self,
        base_model: str,
        adapter_path: Optional[str] = None,
    ) -> str:
        """
        Generate Python code for the inference function.
        
        This code will run inside the Modal container and handle:
        - Model loading with caching
        - Adapter loading if provided
        - Inference execution
        - Response formatting
        
        Args:
            base_model: Base model identifier
            adapter_path: Optional adapter path
            
        Returns:
            Python code as string
        """
        code = f'''
import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from modal import method, Image, gpu

# Global model cache (persists across invocations in same container)
_model = None
_tokenizer = None

def load_model():
    """Load model once and cache in container."""
    global _model, _tokenizer
    
    if _model is None:
        base_model = "{base_model}"
        adapter_path = "{adapter_path or ''}"
        quantization = os.environ.get("QUANTIZATION", "")
        
        # Load tokenizer
        _tokenizer = AutoTokenizer.from_pretrained(base_model)
        
        # Load model with optional quantization
        load_kwargs = {{"torch_dtype": torch.float16}}
        
        if quantization == "int8":
            load_kwargs["load_in_8bit"] = True
        elif quantization == "int4":
            load_kwargs["load_in_4bit"] = True
        
        _model = AutoModelForCausalLM.from_pretrained(
            base_model,
            **load_kwargs
        )
        
        # Load adapter if provided
        if adapter_path:
            from peft import PeftModel
            _model = PeftModel.from_pretrained(_model, adapter_path)
        
        _model.eval()
    
    return _model, _tokenizer

@method()
def generate(prompt: str, max_tokens: int = 256, temperature: float = 0.7) -> dict:
    """
    Generate text from prompt.
    
    This function is called for each inference request.
    The model is loaded once and cached in the container.
    """
    model, tokenizer = load_model()
    
    # Tokenize input
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    # Generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=temperature > 0,
        )
    
    # Decode output
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    return {{
        "text": generated_text,
        "prompt_tokens": len(inputs["input_ids"][0]),
        "completion_tokens": len(outputs[0]) - len(inputs["input_ids"][0]),
    }}
'''
        return code
    
    async def get_function_status(self, function_id: str) -> str:
        """
        Get the status of a function deployment.
        
        Args:
            function_id: Function identifier
            
        Returns:
            Status string: "deploying", "ready", "failed", "stopped"
        """
        if not self._connected:
            raise RuntimeError("Not connected to Modal")
        
        try:
            async with self._session.get(
                f"{self.BASE_URL}/functions/{function_id}"
            ) as response:
                if response.status != 200:
                    return "failed"
                
                data = await response.json()
                status = data.get("status", "unknown")
                
                # Update cached function info
                if function_id in self._functions:
                    self._functions[function_id]["status"] = status
                    self._functions[function_id]["url"] = data.get("url")
                
                return status
                
        except aiohttp.ClientError:
            return "failed"
    
    async def list_functions(self) -> List[Dict]:
        """
        List all deployed functions.
        
        Returns:
            List of function information dictionaries
        """
        if not self._connected:
            raise RuntimeError("Not connected to Modal")
        
        try:
            async with self._session.get(f"{self.BASE_URL}/functions") as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                functions = data.get("functions", [])
                
                # Update cache
                for function in functions:
                    function_id = function["id"]
                    self._functions[function_id] = function
                
                return functions
                
        except aiohttp.ClientError:
            return []
    
    async def delete_function(self, function_id: str) -> bool:
        """
        Delete a deployed function.
        
        Args:
            function_id: Function identifier
            
        Returns:
            True if deleted successfully
        """
        if not self._connected:
            raise RuntimeError("Not connected to Modal")
        
        try:
            async with self._session.delete(
                f"{self.BASE_URL}/functions/{function_id}"
            ) as response:
                if response.status in [200, 204]:
                    if function_id in self._functions:
                        del self._functions[function_id]
                    return True
                return False
                
        except aiohttp.ClientError:
            return False
    
    async def invoke_function(
        self,
        function_id: str,
        prompt: str,
        generation_config: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Invoke a deployed function for inference.
        
        Cold-start optimization ensures fast response times:
        - Warm containers respond immediately
        - Cold starts are minimized through container caching
        - Model is preloaded in container
        
        Args:
            function_id: Function identifier
            prompt: Input prompt
            generation_config: Optional generation parameters
            
        Returns:
            Dictionary with 'text', 'tokens', 'latency_ms', 'cold_start'
        """
        if not self._connected:
            raise RuntimeError("Not connected to Modal")
        
        # Get function info
        function = self._functions.get(function_id)
        if not function:
            # Fetch function info
            await self.get_function_status(function_id)
            function = self._functions.get(function_id)
        
        if not function or not function.get("url"):
            raise RuntimeError(f"Function {function_id} not found or not ready")
        
        url = function["url"]
        
        # Build invocation request
        config = generation_config or {}
        payload = {
            "prompt": prompt,
            "max_tokens": config.get("max_tokens", 256),
            "temperature": config.get("temperature", 0.7),
        }
        
        try:
            start_time = asyncio.get_event_loop().time()
            
            async with self._session.post(
                f"{url}/generate",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Function invocation failed: {error_text}")
                
                data = await response.json()
                
                end_time = asyncio.get_event_loop().time()
                latency_ms = (end_time - start_time) * 1000
                
                # Check if this was a cold start
                cold_start = response.headers.get("X-Modal-Cold-Start", "false") == "true"
                
                return {
                    "text": data.get("text", ""),
                    "tokens": {
                        "prompt": data.get("prompt_tokens", 0),
                        "completion": data.get("completion_tokens", 0),
                        "total": data.get("prompt_tokens", 0) + data.get("completion_tokens", 0),
                    },
                    "latency_ms": latency_ms,
                    "cold_start": cold_start,
                    "function_id": function_id,
                }
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Function invocation failed: {str(e)}")
    
    async def get_usage_stats(
        self,
        function_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get usage statistics and billing information.
        
        Args:
            function_id: Optional function to filter by
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)
            
        Returns:
            Dictionary with usage statistics including cold start metrics
        """
        if not self._connected:
            raise RuntimeError("Not connected to Modal")
        
        params = {}
        if function_id:
            params["function_id"] = function_id
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        try:
            async with self._session.get(
                f"{self.BASE_URL}/usage",
                params=params
            ) as response:
                if response.status != 200:
                    return {}
                
                data = await response.json()
                return {
                    "total_invocations": data.get("total_invocations", 0),
                    "total_compute_seconds": data.get("total_compute_seconds", 0),
                    "cold_starts": data.get("cold_starts", 0),
                    "warm_starts": data.get("warm_starts", 0),
                    "avg_cold_start_ms": data.get("avg_cold_start_ms", 0),
                    "avg_warm_start_ms": data.get("avg_warm_start_ms", 0),
                    "total_cost_usd": data.get("total_cost_usd", 0.0),
                    "functions": data.get("functions", []),
                    "period": {
                        "start": data.get("start_date"),
                        "end": data.get("end_date"),
                    }
                }
                
        except aiohttp.ClientError:
            return {}
    
    async def get_cold_start_metrics(self, function_id: str) -> Dict[str, Any]:
        """
        Get detailed cold-start optimization metrics.
        
        Args:
            function_id: Function identifier
            
        Returns:
            Dictionary with cold-start metrics
        """
        if not self._connected:
            raise RuntimeError("Not connected to Modal")
        
        try:
            async with self._session.get(
                f"{self.BASE_URL}/functions/{function_id}/metrics"
            ) as response:
                if response.status != 200:
                    return {}
                
                data = await response.json()
                return {
                    "container_cache_hit_rate": data.get("container_cache_hit_rate", 0.0),
                    "avg_cold_start_ms": data.get("avg_cold_start_ms", 0),
                    "avg_warm_start_ms": data.get("avg_warm_start_ms", 0),
                    "p50_cold_start_ms": data.get("p50_cold_start_ms", 0),
                    "p95_cold_start_ms": data.get("p95_cold_start_ms", 0),
                    "p99_cold_start_ms": data.get("p99_cold_start_ms", 0),
                    "warm_containers": data.get("warm_containers", 0),
                    "total_containers": data.get("total_containers", 0),
                }
                
        except aiohttp.ClientError:
            return {}
    
    # Required abstract methods (not applicable for inference platform)
    
    async def submit_job(self, config: TrainingConfig) -> str:
        """Not supported for inference platform."""
        raise NotImplementedError("Modal connector does not support training jobs")
    
    async def get_job_status(self, job_id: str) -> JobStatus:
        """Not supported for inference platform."""
        raise NotImplementedError("Modal connector does not support training jobs")
    
    async def cancel_job(self, job_id: str) -> bool:
        """Not supported for inference platform."""
        raise NotImplementedError("Modal connector does not support training jobs")
    
    async def stream_logs(self, job_id: str) -> AsyncIterator[str]:
        """Not supported for inference platform."""
        raise NotImplementedError("Modal connector does not support training jobs")
        yield  # Make it a generator
    
    async def fetch_artifact(self, job_id: str) -> bytes:
        """Not supported for inference platform."""
        raise NotImplementedError("Modal connector does not support training jobs")
    
    async def upload_artifact(self, path: str, metadata: Dict) -> str:
        """Not supported for inference platform."""
        raise NotImplementedError("Modal connector does not support artifact uploads")
    
    async def list_resources(self) -> List[Resource]:
        """
        List available serverless resources.
        
        Returns:
            List of available GPU resources for serverless functions
        """
        if not self._connected:
            return []
        
        # Modal offers various GPU types for serverless functions
        return [
            Resource(
                id="modal-a10g",
                name="NVIDIA A10G (Serverless)",
                type=ResourceType.GPU,
                gpu_type="A10G",
                gpu_count=1,
                vram_gb=24,
                available=True,
                region="us-east-1",
            ),
            Resource(
                id="modal-a100",
                name="NVIDIA A100 (Serverless)",
                type=ResourceType.GPU,
                gpu_type="A100",
                gpu_count=1,
                vram_gb=40,
                available=True,
                region="us-east-1",
            ),
            Resource(
                id="modal-t4",
                name="NVIDIA T4 (Serverless)",
                type=ResourceType.GPU,
                gpu_type="T4",
                gpu_count=1,
                vram_gb=16,
                available=True,
                region="us-east-1",
            ),
        ]
    
    async def get_pricing(self, resource_id: str) -> PricingInfo:
        """
        Get pricing information for serverless resources.
        
        Modal charges per second of compute time.
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            Pricing information
        """
        # Modal pricing (per second of compute)
        pricing_map = {
            "modal-a10g": PricingInfo(
                resource_id=resource_id,
                price_per_hour=1.10,  # ~$0.000305/second
                currency="USD",
                billing_increment_seconds=1,
                minimum_charge_seconds=0,
            ),
            "modal-a100": PricingInfo(
                resource_id=resource_id,
                price_per_hour=4.00,  # ~$0.00111/second
                currency="USD",
                billing_increment_seconds=1,
                minimum_charge_seconds=0,
            ),
            "modal-t4": PricingInfo(
                resource_id=resource_id,
                price_per_hour=0.60,  # ~$0.000167/second
                currency="USD",
                billing_increment_seconds=1,
                minimum_charge_seconds=0,
            ),
        }
        
        if resource_id not in pricing_map:
            raise ValueError(f"Invalid resource ID: {resource_id}")
        
        return pricing_map[resource_id]
    
    def get_required_credentials(self) -> List[str]:
        """Get list of required credential keys."""
        return ["token_id", "token_secret"]
