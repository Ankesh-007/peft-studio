"""
Together AI connector for serverless inference and adapter deployment.

This connector integrates with Together AI's serverless platform to:
- Create serverless inference endpoints
- Upload and deploy adapters
- Perform inference with pay-per-token pricing
- Monitor usage and costs
- Manage model deployments

Together AI API Documentation: https://docs.together.ai/
"""

from typing import Dict, List, AsyncIterator, Optional, Any
import asyncio
import aiohttp
import json
from pathlib import Path
import sys
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent.parent))

from connectors.base import (
    PlatformConnector,
    Resource,
    ResourceType,
    PricingInfo,
    TrainingConfig,
    JobStatus,
)


class TogetherAIConnector(PlatformConnector):
    """
    Connector for Together AI serverless inference platform.
    
    Together AI provides serverless inference with pay-per-token pricing.
    This connector handles:
    - Serverless endpoint creation
    - Adapter upload and deployment
    - Inference with pay-per-token billing
    - Usage tracking and monitoring
    - Multi-model deployment
    """
    
    # Connector metadata
    name = "together_ai"
    display_name = "Together AI"
    description = "Serverless inference with pay-per-token pricing"
    version = "1.0.0"
    
    # Supported features
    supports_training = False
    supports_inference = True
    supports_registry = True
    supports_tracking = False
    
    # API endpoints
    BASE_URL = "https://api.together.xyz/v1"
    
    def __init__(self):
        self._api_key: Optional[str] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        self._endpoints: Dict[str, Dict] = {}
        self._models: Dict[str, Dict] = {}
    
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
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        
        self._session = aiohttp.ClientSession(headers=headers)
        
        # Verify connection by fetching account info
        try:
            async with self._session.get(f"{self.BASE_URL}/auth/me") as response:
                if response.status == 200:
                    data = await response.json()
                    if "id" in data or "email" in data:
                        self._connected = True
                        return True
                    else:
                        raise ConnectionError("Invalid API response")
                elif response.status == 401:
                    raise ValueError("Invalid API key")
                else:
                    raise ConnectionError(f"Connection failed with status {response.status}")
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Failed to connect to Together AI: {str(e)}")
    
    async def disconnect(self) -> bool:
        """Disconnect and cleanup resources."""
        if self._session:
            await self._session.close()
            self._session = None
        
        self._connected = False
        self._api_key = None
        self._endpoints.clear()
        self._models.clear()
        return True
    
    async def verify_connection(self) -> bool:
        """Verify that the connection is still valid."""
        if not self._connected or not self._session:
            return False
        
        try:
            async with self._session.get(f"{self.BASE_URL}/auth/me") as response:
                return response.status == 200
        except:
            return False
    
    async def create_endpoint(
        self,
        model_name: str,
        endpoint_name: str,
        endpoint_config: Optional[Dict] = None,
    ) -> str:
        """
        Create a serverless inference endpoint.
        
        Args:
            model_name: Model identifier (e.g., "meta-llama/Llama-2-7b-hf")
            endpoint_name: Name for the endpoint
            endpoint_config: Optional endpoint configuration
            
        Returns:
            Endpoint ID
            
        Raises:
            RuntimeError: If endpoint creation fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to Together AI")
        
        # Build endpoint configuration
        config = endpoint_config or {}
        endpoint_payload = {
            "model": model_name,
            "name": endpoint_name,
            "config": {
                "max_tokens": config.get("max_tokens", 2048),
                "temperature": config.get("temperature", 0.7),
                "top_p": config.get("top_p", 0.9),
                "top_k": config.get("top_k", 50),
                "repetition_penalty": config.get("repetition_penalty", 1.0),
                "stop": config.get("stop", []),
            }
        }
        
        try:
            async with self._session.post(
                f"{self.BASE_URL}/endpoints",
                json=endpoint_payload
            ) as response:
                if response.status not in [200, 201]:
                    error_text = await response.text()
                    raise RuntimeError(f"Failed to create endpoint: {error_text}")
                
                data = await response.json()
                endpoint_id = data["id"]
                
                # Store endpoint info
                self._endpoints[endpoint_id] = {
                    "id": endpoint_id,
                    "name": endpoint_name,
                    "model": model_name,
                    "status": "creating",
                    "url": data.get("url"),
                    "created_at": datetime.now().isoformat(),
                }
                
                return endpoint_id
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to create endpoint: {str(e)}")
    
    async def deploy_adapter(
        self,
        adapter_path: str,
        base_model: str,
        adapter_name: str,
        deployment_config: Optional[Dict] = None,
    ) -> str:
        """
        Deploy an adapter to Together AI.
        
        Args:
            adapter_path: Local path to adapter files
            base_model: Base model identifier
            adapter_name: Name for the deployed adapter
            deployment_config: Optional deployment configuration
            
        Returns:
            Deployment ID (endpoint ID)
            
        Raises:
            FileNotFoundError: If adapter path doesn't exist
            RuntimeError: If deployment fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to Together AI")
        
        # Check adapter path exists
        path = Path(adapter_path)
        if not path.exists():
            raise FileNotFoundError(f"Adapter path not found: {adapter_path}")
        
        # First, upload the adapter
        model_id = await self.upload_artifact(adapter_path, {
            "name": adapter_name,
            "base_model": base_model,
        })
        
        # Create endpoint for the adapter
        endpoint_id = await self.create_endpoint(
            model_name=model_id,
            endpoint_name=adapter_name,
            endpoint_config=deployment_config,
        )
        
        return endpoint_id
    
    async def get_endpoint_status(self, endpoint_id: str) -> str:
        """
        Get the status of an endpoint.
        
        Args:
            endpoint_id: Endpoint identifier
            
        Returns:
            Status string: "creating", "ready", "failed", "stopped"
        """
        if not self._connected:
            raise RuntimeError("Not connected to Together AI")
        
        try:
            async with self._session.get(
                f"{self.BASE_URL}/endpoints/{endpoint_id}"
            ) as response:
                if response.status != 200:
                    return "failed"
                
                data = await response.json()
                status = data.get("status", "unknown")
                
                # Update cached endpoint info
                if endpoint_id in self._endpoints:
                    self._endpoints[endpoint_id]["status"] = status
                    self._endpoints[endpoint_id]["url"] = data.get("url")
                
                return status
                
        except aiohttp.ClientError:
            return "failed"
    
    async def list_endpoints(self) -> List[Dict]:
        """
        List all endpoints.
        
        Returns:
            List of endpoint information dictionaries
        """
        if not self._connected:
            raise RuntimeError("Not connected to Together AI")
        
        try:
            async with self._session.get(f"{self.BASE_URL}/endpoints") as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                endpoints = data.get("endpoints", [])
                
                # Update cache
                for endpoint in endpoints:
                    endpoint_id = endpoint["id"]
                    self._endpoints[endpoint_id] = endpoint
                
                return endpoints
                
        except aiohttp.ClientError:
            return []
    
    async def delete_endpoint(self, endpoint_id: str) -> bool:
        """
        Delete an endpoint.
        
        Args:
            endpoint_id: Endpoint identifier
            
        Returns:
            True if deleted successfully
        """
        if not self._connected:
            raise RuntimeError("Not connected to Together AI")
        
        try:
            async with self._session.delete(
                f"{self.BASE_URL}/endpoints/{endpoint_id}"
            ) as response:
                if response.status in [200, 204]:
                    if endpoint_id in self._endpoints:
                        del self._endpoints[endpoint_id]
                    return True
                return False
                
        except aiohttp.ClientError:
            return False
    
    async def inference(
        self,
        model: str,
        prompt: str,
        generation_config: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Perform inference with pay-per-token pricing.
        
        Args:
            model: Model identifier or endpoint ID
            prompt: Input prompt
            generation_config: Optional generation parameters
            
        Returns:
            Dictionary with 'text', 'tokens', 'latency_ms', 'cost_usd'
        """
        if not self._connected:
            raise RuntimeError("Not connected to Together AI")
        
        # Build inference request
        config = generation_config or {}
        payload = {
            "model": model,
            "prompt": prompt,
            "max_tokens": config.get("max_tokens", 256),
            "temperature": config.get("temperature", 0.7),
            "top_p": config.get("top_p", 0.9),
            "top_k": config.get("top_k", 50),
            "repetition_penalty": config.get("repetition_penalty", 1.0),
            "stop": config.get("stop", []),
        }
        
        try:
            start_time = asyncio.get_event_loop().time()
            
            async with self._session.post(
                f"{self.BASE_URL}/completions",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Inference failed: {error_text}")
                
                data = await response.json()
                
                end_time = asyncio.get_event_loop().time()
                latency_ms = (end_time - start_time) * 1000
                
                # Extract usage information
                usage = data.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", 0)
                
                # Calculate cost (approximate - actual pricing varies by model)
                # Together AI pricing: ~$0.0002 per 1K tokens for Llama-2-7B
                cost_per_1k_tokens = 0.0002
                cost_usd = (total_tokens / 1000) * cost_per_1k_tokens
                
                return {
                    "text": data.get("choices", [{}])[0].get("text", ""),
                    "tokens": {
                        "prompt": prompt_tokens,
                        "completion": completion_tokens,
                        "total": total_tokens,
                    },
                    "latency_ms": latency_ms,
                    "cost_usd": cost_usd,
                    "model": model,
                }
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Inference request failed: {str(e)}")
    
    async def inference_streaming(
        self,
        model: str,
        prompt: str,
        generation_config: Optional[Dict] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Perform streaming inference.
        
        Args:
            model: Model identifier or endpoint ID
            prompt: Input prompt
            generation_config: Optional generation parameters
            
        Yields:
            Dictionaries with streaming response chunks
        """
        if not self._connected:
            raise RuntimeError("Not connected to Together AI")
        
        # Build inference request
        config = generation_config or {}
        payload = {
            "model": model,
            "prompt": prompt,
            "max_tokens": config.get("max_tokens", 256),
            "temperature": config.get("temperature", 0.7),
            "top_p": config.get("top_p", 0.9),
            "top_k": config.get("top_k", 50),
            "repetition_penalty": config.get("repetition_penalty", 1.0),
            "stop": config.get("stop", []),
            "stream": True,
        }
        
        try:
            async with self._session.post(
                f"{self.BASE_URL}/completions",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Streaming inference failed: {error_text}")
                
                # Stream response chunks
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        data_str = line[6:]  # Remove 'data: ' prefix
                        if data_str == '[DONE]':
                            break
                        
                        try:
                            data = json.loads(data_str)
                            chunk = {
                                "text": data.get("choices", [{}])[0].get("text", ""),
                                "finish_reason": data.get("choices", [{}])[0].get("finish_reason"),
                            }
                            yield chunk
                        except json.JSONDecodeError:
                            continue
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Streaming inference failed: {str(e)}")
    
    async def get_usage_stats(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get usage statistics and billing information.
        
        Args:
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)
            
        Returns:
            Dictionary with usage statistics
        """
        if not self._connected:
            raise RuntimeError("Not connected to Together AI")
        
        params = {}
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
                    "total_requests": data.get("total_requests", 0),
                    "total_tokens": data.get("total_tokens", 0),
                    "prompt_tokens": data.get("prompt_tokens", 0),
                    "completion_tokens": data.get("completion_tokens", 0),
                    "total_cost_usd": data.get("total_cost_usd", 0.0),
                    "models": data.get("models", []),
                    "period": {
                        "start": data.get("start_date"),
                        "end": data.get("end_date"),
                    }
                }
                
        except aiohttp.ClientError:
            return {}
    
    async def list_available_models(self) -> List[Dict]:
        """
        List all available models on Together AI.
        
        Returns:
            List of model information dictionaries
        """
        if not self._connected:
            raise RuntimeError("Not connected to Together AI")
        
        try:
            async with self._session.get(f"{self.BASE_URL}/models") as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                models = data.get("models", [])
                
                # Update cache
                for model in models:
                    model_id = model["id"]
                    self._models[model_id] = model
                
                return models
                
        except aiohttp.ClientError:
            return []
    
    async def upload_artifact(self, path: str, metadata: Dict) -> str:
        """
        Upload an adapter to Together AI.
        
        Args:
            path: Local path to adapter directory
            metadata: Adapter metadata including 'name' and 'base_model'
            
        Returns:
            Model ID
            
        Raises:
            FileNotFoundError: If local path doesn't exist
            RuntimeError: If upload fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to Together AI")
        
        adapter_path = Path(path)
        if not adapter_path.exists():
            raise FileNotFoundError(f"Adapter path not found: {path}")
        
        adapter_name = metadata.get("name")
        base_model = metadata.get("base_model")
        
        if not adapter_name or not base_model:
            raise ValueError("'name' and 'base_model' are required in metadata")
        
        # Create model entry
        model_payload = {
            "name": adapter_name,
            "base_model": base_model,
            "description": metadata.get("description", ""),
            "type": "adapter",
        }
        
        try:
            # Create model entry
            async with self._session.post(
                f"{self.BASE_URL}/models",
                json=model_payload
            ) as response:
                if response.status not in [200, 201]:
                    error_text = await response.text()
                    raise RuntimeError(f"Failed to create model entry: {error_text}")
                
                data = await response.json()
                model_id = data["id"]
                upload_url = data.get("upload_url")
            
            # Upload adapter files
            adapter_files = []
            for file_name in ["adapter_model.safetensors", "adapter_config.json"]:
                file_path = adapter_path / file_name
                if file_path.exists():
                    adapter_files.append(file_path)
            
            if not adapter_files:
                raise FileNotFoundError("No adapter files found in directory")
            
            # Upload files
            for file_path in adapter_files:
                with open(file_path, 'rb') as f:
                    file_data = aiohttp.FormData()
                    file_data.add_field(
                        'file',
                        f,
                        filename=file_path.name,
                        content_type='application/octet-stream'
                    )
                    
                    async with self._session.post(
                        f"{upload_url}/{file_path.name}",
                        data=file_data
                    ) as upload_response:
                        if upload_response.status not in [200, 201]:
                            raise RuntimeError(f"Failed to upload {file_path.name}")
            
            # Mark upload as complete
            async with self._session.post(
                f"{self.BASE_URL}/models/{model_id}/complete"
            ) as response:
                if response.status not in [200, 204]:
                    raise RuntimeError("Failed to finalize model upload")
            
            # Cache model info
            self._models[model_id] = {
                "id": model_id,
                "name": adapter_name,
                "base_model": base_model,
                "uploaded_at": datetime.now().isoformat(),
            }
            
            return model_id
            
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to upload adapter: {str(e)}")
    
    # Required abstract methods (not applicable for inference platform)
    
    async def submit_job(self, config: TrainingConfig) -> str:
        """Not supported for inference platform."""
        raise NotImplementedError("Together AI connector does not support training jobs")
    
    async def get_job_status(self, job_id: str) -> JobStatus:
        """Not supported for inference platform."""
        raise NotImplementedError("Together AI connector does not support training jobs")
    
    async def cancel_job(self, job_id: str) -> bool:
        """Not supported for inference platform."""
        raise NotImplementedError("Together AI connector does not support training jobs")
    
    async def stream_logs(self, job_id: str) -> AsyncIterator[str]:
        """Not supported for inference platform."""
        raise NotImplementedError("Together AI connector does not support training jobs")
        yield  # Make it a generator
    
    async def fetch_artifact(self, job_id: str) -> bytes:
        """Not supported for inference platform."""
        raise NotImplementedError("Together AI connector does not support training jobs")
    
    async def list_resources(self) -> List[Resource]:
        """
        List available inference resources.
        
        Returns:
            List of available serverless resources
        """
        if not self._connected:
            return []
        
        # Together AI offers serverless inference (no specific resources to list)
        return [
            Resource(
                id="together-serverless",
                name="Serverless Inference",
                type=ResourceType.GPU,
                gpu_type="Various",
                gpu_count=0,  # Serverless
                vram_gb=0,  # Managed
                available=True,
                region="global",
            ),
        ]
    
    async def get_pricing(self, resource_id: str) -> PricingInfo:
        """
        Get pricing information for inference.
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            Pricing information (pay-per-token)
        """
        # Together AI uses pay-per-token pricing
        # Pricing varies by model, this is an average
        return PricingInfo(
            resource_id=resource_id,
            price_per_hour=0.0,  # Pay-per-token, not per-hour
            currency="USD",
            billing_increment_seconds=0,  # Per-token billing
            minimum_charge_seconds=0,
        )
    
    def get_required_credentials(self) -> List[str]:
        """Get list of required credential keys."""
        return ["api_key"]
