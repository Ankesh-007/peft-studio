"""
Predibase connector for LoRAX adapter deployment and serving.

This connector integrates with Predibase's LoRAX platform to:
- Deploy adapters for hot-swappable serving
- Manage inference endpoints
- Track usage and billing
- Perform inference with adapter hot-swapping

Predibase API Documentation: https://docs.predibase.com/
LoRAX Documentation: https://github.com/predibase/lorax
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


class PredibaseConnector(PlatformConnector):
    """
    Connector for Predibase LoRAX adapter deployment platform.
    
    Predibase provides LoRAX-based adapter serving with hot-swapping capabilities.
    This connector handles:
    - LoRAX adapter deployment
    - Hot-swap adapter serving on shared base models
    - Inference endpoint management
    - Usage tracking and billing
    - Multi-adapter inference
    """
    
    # Connector metadata
    name = "predibase"
    display_name = "Predibase"
    description = "LoRAX adapter deployment with hot-swappable serving"
    version = "1.0.0"
    
    # Supported features
    supports_training = False
    supports_inference = True
    supports_registry = True
    supports_tracking = False
    
    # API endpoints
    BASE_URL = "https://api.predibase.com/v1"
    
    def __init__(self):
        self._api_key: Optional[str] = None
        self._tenant_id: Optional[str] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        self._deployments: Dict[str, Dict] = {}
        self._adapters: Dict[str, Dict] = {}
    
    async def connect(self, credentials: Dict[str, str]) -> bool:
        """
        Verify connection and store credentials.
        
        Args:
            credentials: Dictionary with 'api_key' and optionally 'tenant_id'
            
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
        self._tenant_id = credentials.get("tenant_id")
        
        # Create session with headers
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        
        if self._tenant_id:
            headers["X-Tenant-Id"] = self._tenant_id
        
        self._session = aiohttp.ClientSession(headers=headers)
        
        # Verify connection by fetching tenant info
        try:
            async with self._session.get(f"{self.BASE_URL}/tenants/me") as response:
                if response.status == 200:
                    data = await response.json()
                    if "id" in data:
                        self._tenant_id = data["id"]
                        self._connected = True
                        return True
                    else:
                        raise ConnectionError("Invalid API response")
                elif response.status == 401:
                    raise ValueError("Invalid API key")
                else:
                    raise ConnectionError(f"Connection failed with status {response.status}")
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Failed to connect to Predibase: {str(e)}")
    
    async def disconnect(self) -> bool:
        """Disconnect and cleanup resources."""
        if self._session:
            await self._session.close()
            self._session = None
        
        self._connected = False
        self._api_key = None
        self._tenant_id = None
        self._deployments.clear()
        self._adapters.clear()
        return True
    
    async def verify_connection(self) -> bool:
        """Verify that the connection is still valid."""
        if not self._connected or not self._session:
            return False
        
        try:
            async with self._session.get(f"{self.BASE_URL}/tenants/me") as response:
                return response.status == 200
        except:
            return False
    
    async def deploy_adapter(
        self,
        adapter_path: str,
        base_model: str,
        adapter_name: str,
        deployment_config: Optional[Dict] = None,
    ) -> str:
        """
        Deploy an adapter to Predibase LoRAX.
        
        Args:
            adapter_path: Local path to adapter files
            base_model: Base model identifier (e.g., "meta-llama/Llama-2-7b-hf")
            adapter_name: Name for the deployed adapter
            deployment_config: Optional deployment configuration
            
        Returns:
            Deployment ID
            
        Raises:
            FileNotFoundError: If adapter path doesn't exist
            RuntimeError: If deployment fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to Predibase")
        
        # Check adapter path exists
        path = Path(adapter_path)
        if not path.exists():
            raise FileNotFoundError(f"Adapter path not found: {adapter_path}")
        
        # First, upload the adapter
        adapter_id = await self.upload_artifact(adapter_path, {
            "name": adapter_name,
            "base_model": base_model,
        })
        
        # Create deployment configuration
        config = deployment_config or {}
        deployment_payload = {
            "adapter_id": adapter_id,
            "base_model": base_model,
            "name": adapter_name,
            "config": {
                "max_batch_size": config.get("max_batch_size", 32),
                "max_concurrent_requests": config.get("max_concurrent_requests", 100),
                "enable_hot_swap": True,  # Always enable hot-swapping
                "gpu_type": config.get("gpu_type", "A100"),
            }
        }
        
        try:
            async with self._session.post(
                f"{self.BASE_URL}/deployments",
                json=deployment_payload
            ) as response:
                if response.status not in [200, 201]:
                    error_text = await response.text()
                    raise RuntimeError(f"Failed to create deployment: {error_text}")
                
                data = await response.json()
                deployment_id = data["id"]
                
                # Store deployment info
                self._deployments[deployment_id] = {
                    "id": deployment_id,
                    "adapter_id": adapter_id,
                    "adapter_name": adapter_name,
                    "base_model": base_model,
                    "status": "deploying",
                    "endpoint": data.get("endpoint"),
                    "created_at": datetime.now().isoformat(),
                }
                
                return deployment_id
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to deploy adapter: {str(e)}")
    
    async def get_deployment_status(self, deployment_id: str) -> str:
        """
        Get the status of a deployment.
        
        Args:
            deployment_id: Deployment identifier
            
        Returns:
            Status string: "deploying", "ready", "failed", "stopped"
        """
        if not self._connected:
            raise RuntimeError("Not connected to Predibase")
        
        try:
            async with self._session.get(
                f"{self.BASE_URL}/deployments/{deployment_id}"
            ) as response:
                if response.status != 200:
                    return "failed"
                
                data = await response.json()
                status = data.get("status", "unknown")
                
                # Update cached deployment info
                if deployment_id in self._deployments:
                    self._deployments[deployment_id]["status"] = status
                    self._deployments[deployment_id]["endpoint"] = data.get("endpoint")
                
                return status
                
        except aiohttp.ClientError:
            return "failed"
    
    async def list_deployments(self) -> List[Dict]:
        """
        List all deployments for the tenant.
        
        Returns:
            List of deployment information dictionaries
        """
        if not self._connected:
            raise RuntimeError("Not connected to Predibase")
        
        try:
            async with self._session.get(f"{self.BASE_URL}/deployments") as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                deployments = data.get("deployments", [])
                
                # Update cache
                for deployment in deployments:
                    deployment_id = deployment["id"]
                    self._deployments[deployment_id] = deployment
                
                return deployments
                
        except aiohttp.ClientError:
            return []
    
    async def stop_deployment(self, deployment_id: str) -> bool:
        """
        Stop a running deployment.
        
        Args:
            deployment_id: Deployment identifier
            
        Returns:
            True if stopped successfully
        """
        if not self._connected:
            raise RuntimeError("Not connected to Predibase")
        
        try:
            async with self._session.post(
                f"{self.BASE_URL}/deployments/{deployment_id}/stop"
            ) as response:
                if response.status in [200, 204]:
                    if deployment_id in self._deployments:
                        self._deployments[deployment_id]["status"] = "stopped"
                    return True
                return False
                
        except aiohttp.ClientError:
            return False
    
    async def inference(
        self,
        deployment_id: str,
        prompt: str,
        adapter_name: Optional[str] = None,
        generation_config: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Perform inference with optional adapter hot-swapping.
        
        This is the key feature of Predibase/LoRAX - you can specify which
        adapter to use for each request without reloading the base model.
        
        Args:
            deployment_id: Deployment identifier
            prompt: Input prompt
            adapter_name: Optional adapter to use (enables hot-swapping)
            generation_config: Optional generation parameters
            
        Returns:
            Dictionary with 'text', 'tokens', 'latency_ms'
        """
        if not self._connected:
            raise RuntimeError("Not connected to Predibase")
        
        # Get deployment endpoint
        deployment = self._deployments.get(deployment_id)
        if not deployment:
            # Fetch deployment info
            await self.get_deployment_status(deployment_id)
            deployment = self._deployments.get(deployment_id)
        
        if not deployment or not deployment.get("endpoint"):
            raise RuntimeError(f"Deployment {deployment_id} not found or not ready")
        
        endpoint = deployment["endpoint"]
        
        # Build inference request
        config = generation_config or {}
        payload = {
            "prompt": prompt,
            "max_new_tokens": config.get("max_new_tokens", 256),
            "temperature": config.get("temperature", 0.7),
            "top_p": config.get("top_p", 0.9),
            "top_k": config.get("top_k", 50),
            "repetition_penalty": config.get("repetition_penalty", 1.0),
        }
        
        # Add adapter if specified (enables hot-swapping)
        if adapter_name:
            payload["adapter"] = adapter_name
        
        try:
            start_time = asyncio.get_event_loop().time()
            
            async with self._session.post(
                f"{endpoint}/generate",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Inference failed: {error_text}")
                
                data = await response.json()
                
                end_time = asyncio.get_event_loop().time()
                latency_ms = (end_time - start_time) * 1000
                
                return {
                    "text": data.get("generated_text", ""),
                    "tokens": data.get("tokens", []),
                    "latency_ms": latency_ms,
                    "adapter_used": adapter_name or "base",
                }
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Inference request failed: {str(e)}")
    
    async def get_usage_stats(
        self,
        deployment_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get usage statistics and billing information.
        
        Args:
            deployment_id: Optional deployment to filter by
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)
            
        Returns:
            Dictionary with usage statistics
        """
        if not self._connected:
            raise RuntimeError("Not connected to Predibase")
        
        params = {}
        if deployment_id:
            params["deployment_id"] = deployment_id
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
                    "total_cost_usd": data.get("total_cost_usd", 0.0),
                    "deployments": data.get("deployments", []),
                    "period": {
                        "start": data.get("start_date"),
                        "end": data.get("end_date"),
                    }
                }
                
        except aiohttp.ClientError:
            return {}
    
    async def upload_artifact(self, path: str, metadata: Dict) -> str:
        """
        Upload an adapter to Predibase registry.
        
        Args:
            path: Local path to adapter directory
            metadata: Adapter metadata including 'name' and 'base_model'
            
        Returns:
            Adapter ID
            
        Raises:
            FileNotFoundError: If local path doesn't exist
            RuntimeError: If upload fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to Predibase")
        
        adapter_path = Path(path)
        if not adapter_path.exists():
            raise FileNotFoundError(f"Adapter path not found: {path}")
        
        adapter_name = metadata.get("name")
        base_model = metadata.get("base_model")
        
        if not adapter_name or not base_model:
            raise ValueError("'name' and 'base_model' are required in metadata")
        
        # Create adapter registry entry
        adapter_payload = {
            "name": adapter_name,
            "base_model": base_model,
            "description": metadata.get("description", ""),
            "tags": metadata.get("tags", []),
        }
        
        try:
            # Create adapter entry
            async with self._session.post(
                f"{self.BASE_URL}/adapters",
                json=adapter_payload
            ) as response:
                if response.status not in [200, 201]:
                    error_text = await response.text()
                    raise RuntimeError(f"Failed to create adapter entry: {error_text}")
                
                data = await response.json()
                adapter_id = data["id"]
                upload_url = data.get("upload_url")
            
            # Upload adapter files
            # Find adapter files (adapter_model.safetensors, adapter_config.json)
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
                f"{self.BASE_URL}/adapters/{adapter_id}/complete"
            ) as response:
                if response.status not in [200, 204]:
                    raise RuntimeError("Failed to finalize adapter upload")
            
            # Cache adapter info
            self._adapters[adapter_id] = {
                "id": adapter_id,
                "name": adapter_name,
                "base_model": base_model,
                "uploaded_at": datetime.now().isoformat(),
            }
            
            return adapter_id
            
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to upload adapter: {str(e)}")
    
    async def list_adapters(self) -> List[Dict]:
        """
        List all adapters in the registry.
        
        Returns:
            List of adapter information dictionaries
        """
        if not self._connected:
            raise RuntimeError("Not connected to Predibase")
        
        try:
            async with self._session.get(f"{self.BASE_URL}/adapters") as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                adapters = data.get("adapters", [])
                
                # Update cache
                for adapter in adapters:
                    adapter_id = adapter["id"]
                    self._adapters[adapter_id] = adapter
                
                return adapters
                
        except aiohttp.ClientError:
            return []
    
    # Required abstract methods (not applicable for inference platform)
    
    async def submit_job(self, config: TrainingConfig) -> str:
        """Not supported for inference platform."""
        raise NotImplementedError("Predibase connector does not support training jobs")
    
    async def get_job_status(self, job_id: str) -> JobStatus:
        """Not supported for inference platform."""
        raise NotImplementedError("Predibase connector does not support training jobs")
    
    async def cancel_job(self, job_id: str) -> bool:
        """Not supported for inference platform."""
        raise NotImplementedError("Predibase connector does not support training jobs")
    
    async def stream_logs(self, job_id: str) -> AsyncIterator[str]:
        """Not supported for inference platform."""
        raise NotImplementedError("Predibase connector does not support training jobs")
        yield  # Make it a generator
    
    async def fetch_artifact(self, job_id: str) -> bytes:
        """Not supported for inference platform."""
        raise NotImplementedError("Predibase connector does not support training jobs")
    
    async def list_resources(self) -> List[Resource]:
        """
        List available inference resources.
        
        Returns:
            List of available GPU resources for inference
        """
        if not self._connected:
            return []
        
        # Predibase offers managed inference resources
        return [
            Resource(
                id="predibase-a100",
                name="NVIDIA A100 (Managed)",
                type=ResourceType.GPU,
                gpu_type="A100",
                gpu_count=1,
                vram_gb=40,
                available=True,
                region="us-east-1",
            ),
            Resource(
                id="predibase-a10",
                name="NVIDIA A10 (Managed)",
                type=ResourceType.GPU,
                gpu_type="A10",
                gpu_count=1,
                vram_gb=24,
                available=True,
                region="us-east-1",
            ),
        ]
    
    async def get_pricing(self, resource_id: str) -> PricingInfo:
        """
        Get pricing information for inference resources.
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            Pricing information
        """
        # Predibase uses pay-per-token pricing
        pricing_map = {
            "predibase-a100": PricingInfo(
                resource_id=resource_id,
                price_per_hour=3.00,  # Base rate
                currency="USD",
                billing_increment_seconds=1,
                minimum_charge_seconds=0,
            ),
            "predibase-a10": PricingInfo(
                resource_id=resource_id,
                price_per_hour=1.50,  # Base rate
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
        return ["api_key"]
