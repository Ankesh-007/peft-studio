"""
Replicate connector for model deployment and inference.

This connector integrates with Replicate's platform to:
- Deploy models for inference
- Implement inference API
- Manage model versions
- Track usage and costs

Replicate API Documentation: https://replicate.com/docs
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


class ReplicateConnector(PlatformConnector):
    """
    Connector for Replicate model deployment and inference platform.
    
    Replicate provides model deployment with version management.
    This connector handles:
    - Model deployment
    - Inference API
    - Version management
    - Usage tracking
    """
    
    # Connector metadata
    name = "replicate"
    display_name = "Replicate"
    description = "Model deployment with version management"
    version = "1.0.0"
    
    # Supported features
    supports_training = False
    supports_inference = True
    supports_registry = True
    supports_tracking = False
    
    # API endpoints
    BASE_URL = "https://api.replicate.com/v1"
    
    def __init__(self):
        self._api_token: Optional[str] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        self._models: Dict[str, Dict] = {}
        self._versions: Dict[str, List[Dict]] = {}
        self._predictions: Dict[str, Dict] = {}
    
    async def connect(self, credentials: Dict[str, str]) -> bool:
        """
        Verify connection and store credentials.
        
        Args:
            credentials: Dictionary with 'api_token'
            
        Returns:
            True if connection successful
            
        Raises:
            ConnectionError: If connection fails
            ValueError: If credentials are invalid
        """
        api_token = credentials.get("api_token")
        if not api_token:
            raise ValueError("api_token is required")
        
        self._api_token = api_token
        
        # Create session with headers
        headers = {
            "Authorization": f"Token {self._api_token}",
            "Content-Type": "application/json",
        }
        
        self._session = aiohttp.ClientSession(headers=headers)
        
        # Verify connection by fetching account info
        try:
            async with self._session.get(f"{self.BASE_URL}/account") as response:
                if response.status == 200:
                    data = await response.json()
                    if "username" in data or "type" in data:
                        self._connected = True
                        return True
                    else:
                        raise ConnectionError("Invalid API response")
                elif response.status == 401:
                    raise ValueError("Invalid API token")
                else:
                    raise ConnectionError(f"Connection failed with status {response.status}")
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Failed to connect to Replicate: {str(e)}")
    
    async def disconnect(self) -> bool:
        """Disconnect and cleanup resources."""
        if self._session:
            await self._session.close()
            self._session = None
        
        self._connected = False
        self._api_token = None
        self._models.clear()
        self._versions.clear()
        self._predictions.clear()
        return True
    
    async def verify_connection(self) -> bool:
        """Verify that the connection is still valid."""
        if not self._connected or not self._session:
            return False
        
        try:
            async with self._session.get(f"{self.BASE_URL}/account") as response:
                return response.status == 200
        except:
            return False
    
    async def create_model(
        self,
        owner: str,
        name: str,
        visibility: str = "public",
        hardware: str = "gpu-t4",
        description: Optional[str] = None,
    ) -> str:
        """
        Create a new model on Replicate.
        
        Args:
            owner: Username or organization name
            name: Model name
            visibility: "public" or "private"
            hardware: Hardware to run on (e.g., "gpu-t4", "gpu-a40-large")
            description: Optional model description
            
        Returns:
            Model ID (owner/name format)
            
        Raises:
            RuntimeError: If model creation fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to Replicate")
        
        model_payload = {
            "owner": owner,
            "name": name,
            "visibility": visibility,
            "hardware": hardware,
        }
        
        if description:
            model_payload["description"] = description
        
        try:
            async with self._session.post(
                f"{self.BASE_URL}/models",
                json=model_payload
            ) as response:
                if response.status not in [200, 201]:
                    error_text = await response.text()
                    raise RuntimeError(f"Failed to create model: {error_text}")
                
                data = await response.json()
                model_id = f"{owner}/{name}"
                
                # Store model info
                self._models[model_id] = {
                    "id": model_id,
                    "owner": owner,
                    "name": name,
                    "visibility": visibility,
                    "hardware": hardware,
                    "description": description,
                    "url": data.get("url"),
                    "created_at": datetime.now().isoformat(),
                }
                
                return model_id
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to create model: {str(e)}")
    
    async def create_model_version(
        self,
        model_id: str,
        version: str,
        weights_url: Optional[str] = None,
        config: Optional[Dict] = None,
    ) -> str:
        """
        Create a new version of a model.
        
        Args:
            model_id: Model identifier (owner/name format)
            version: Version identifier (e.g., "v1", "1.0.0")
            weights_url: Optional URL to model weights
            config: Optional version configuration
            
        Returns:
            Version ID
            
        Raises:
            RuntimeError: If version creation fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to Replicate")
        
        version_payload = {
            "version": version,
        }
        
        if weights_url:
            version_payload["weights_url"] = weights_url
        
        if config:
            version_payload["config"] = config
        
        try:
            async with self._session.post(
                f"{self.BASE_URL}/models/{model_id}/versions",
                json=version_payload
            ) as response:
                if response.status not in [200, 201]:
                    error_text = await response.text()
                    raise RuntimeError(f"Failed to create version: {error_text}")
                
                data = await response.json()
                version_id = data["id"]
                
                # Store version info
                if model_id not in self._versions:
                    self._versions[model_id] = []
                
                self._versions[model_id].append({
                    "id": version_id,
                    "version": version,
                    "model_id": model_id,
                    "weights_url": weights_url,
                    "config": config,
                    "created_at": datetime.now().isoformat(),
                })
                
                return version_id
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to create version: {str(e)}")
    
    async def deploy_model(
        self,
        model_name: str,
        base_model: str,
        adapter_path: Optional[str] = None,
        deployment_config: Optional[Dict] = None,
    ) -> str:
        """
        Deploy a model to Replicate.
        
        This creates a model and uploads the first version.
        
        Args:
            model_name: Name for the model
            base_model: Base model identifier
            adapter_path: Optional path to adapter files
            deployment_config: Optional deployment configuration
            
        Returns:
            Model ID
            
        Raises:
            RuntimeError: If deployment fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to Replicate")
        
        config = deployment_config or {}
        
        # Extract owner from config or use default
        owner = config.get("owner", "default")
        
        # Create model
        model_id = await self.create_model(
            owner=owner,
            name=model_name,
            visibility=config.get("visibility", "public"),
            hardware=config.get("hardware", "gpu-t4"),
            description=config.get("description"),
        )
        
        # If adapter provided, upload it
        if adapter_path:
            # Upload adapter and get URL
            artifact_id = await self.upload_artifact(adapter_path, {
                "name": model_name,
                "base_model": base_model,
            })
            
            # Create first version with adapter
            await self.create_model_version(
                model_id=model_id,
                version="v1",
                weights_url=artifact_id,  # artifact_id is the URL
                config={"base_model": base_model},
            )
        
        return model_id
    
    async def get_model(self, model_id: str) -> Dict[str, Any]:
        """
        Get model information.
        
        Args:
            model_id: Model identifier (owner/name format)
            
        Returns:
            Model information dictionary
        """
        if not self._connected:
            raise RuntimeError("Not connected to Replicate")
        
        try:
            async with self._session.get(
                f"{self.BASE_URL}/models/{model_id}"
            ) as response:
                if response.status != 200:
                    return {}
                
                data = await response.json()
                
                # Update cache
                self._models[model_id] = data
                
                return data
                
        except aiohttp.ClientError:
            return {}
    
    async def list_model_versions(self, model_id: str) -> List[Dict]:
        """
        List all versions of a model.
        
        Args:
            model_id: Model identifier (owner/name format)
            
        Returns:
            List of version information dictionaries
        """
        if not self._connected:
            raise RuntimeError("Not connected to Replicate")
        
        try:
            async with self._session.get(
                f"{self.BASE_URL}/models/{model_id}/versions"
            ) as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                versions = data.get("results", [])
                
                # Update cache
                self._versions[model_id] = versions
                
                return versions
                
        except aiohttp.ClientError:
            return []
    
    async def get_model_version(self, model_id: str, version_id: str) -> Dict[str, Any]:
        """
        Get specific version information.
        
        Args:
            model_id: Model identifier (owner/name format)
            version_id: Version identifier
            
        Returns:
            Version information dictionary
        """
        if not self._connected:
            raise RuntimeError("Not connected to Replicate")
        
        try:
            async with self._session.get(
                f"{self.BASE_URL}/models/{model_id}/versions/{version_id}"
            ) as response:
                if response.status != 200:
                    return {}
                
                data = await response.json()
                return data
                
        except aiohttp.ClientError:
            return {}
    
    async def delete_model(self, model_id: str) -> bool:
        """
        Delete a model.
        
        Args:
            model_id: Model identifier (owner/name format)
            
        Returns:
            True if deleted successfully
        """
        if not self._connected:
            raise RuntimeError("Not connected to Replicate")
        
        try:
            async with self._session.delete(
                f"{self.BASE_URL}/models/{model_id}"
            ) as response:
                if response.status in [200, 204]:
                    if model_id in self._models:
                        del self._models[model_id]
                    if model_id in self._versions:
                        del self._versions[model_id]
                    return True
                return False
                
        except aiohttp.ClientError:
            return False
    
    async def create_prediction(
        self,
        model_id: str,
        version_id: Optional[str] = None,
        input_data: Optional[Dict] = None,
    ) -> str:
        """
        Create a prediction (inference request).
        
        Args:
            model_id: Model identifier (owner/name format)
            version_id: Optional specific version ID
            input_data: Input data for the prediction
            
        Returns:
            Prediction ID
            
        Raises:
            RuntimeError: If prediction creation fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to Replicate")
        
        # Build prediction payload
        if version_id:
            # Use specific version
            prediction_payload = {
                "version": version_id,
                "input": input_data or {},
            }
        else:
            # Use latest version of model
            prediction_payload = {
                "model": model_id,
                "input": input_data or {},
            }
        
        try:
            async with self._session.post(
                f"{self.BASE_URL}/predictions",
                json=prediction_payload
            ) as response:
                if response.status not in [200, 201]:
                    error_text = await response.text()
                    raise RuntimeError(f"Failed to create prediction: {error_text}")
                
                data = await response.json()
                prediction_id = data["id"]
                
                # Store prediction info
                self._predictions[prediction_id] = {
                    "id": prediction_id,
                    "model_id": model_id,
                    "version_id": version_id,
                    "status": data.get("status", "starting"),
                    "created_at": datetime.now().isoformat(),
                }
                
                return prediction_id
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to create prediction: {str(e)}")
    
    async def get_prediction(self, prediction_id: str) -> Dict[str, Any]:
        """
        Get prediction status and results.
        
        Args:
            prediction_id: Prediction identifier
            
        Returns:
            Prediction information dictionary
        """
        if not self._connected:
            raise RuntimeError("Not connected to Replicate")
        
        try:
            async with self._session.get(
                f"{self.BASE_URL}/predictions/{prediction_id}"
            ) as response:
                if response.status != 200:
                    return {}
                
                data = await response.json()
                
                # Update cache
                self._predictions[prediction_id] = data
                
                return data
                
        except aiohttp.ClientError:
            return {}
    
    async def wait_for_prediction(
        self,
        prediction_id: str,
        timeout: int = 300,
        poll_interval: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Wait for a prediction to complete.
        
        Args:
            prediction_id: Prediction identifier
            timeout: Maximum time to wait in seconds
            poll_interval: Time between status checks in seconds
            
        Returns:
            Final prediction result
            
        Raises:
            TimeoutError: If prediction doesn't complete within timeout
        """
        start_time = asyncio.get_event_loop().time()
        
        while True:
            prediction = await self.get_prediction(prediction_id)
            status = prediction.get("status")
            
            if status in ["succeeded", "failed", "canceled"]:
                return prediction
            
            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"Prediction {prediction_id} timed out after {timeout}s")
            
            # Wait before next poll
            await asyncio.sleep(poll_interval)
    
    async def cancel_prediction(self, prediction_id: str) -> bool:
        """
        Cancel a running prediction.
        
        Args:
            prediction_id: Prediction identifier
            
        Returns:
            True if canceled successfully
        """
        if not self._connected:
            raise RuntimeError("Not connected to Replicate")
        
        try:
            async with self._session.post(
                f"{self.BASE_URL}/predictions/{prediction_id}/cancel"
            ) as response:
                return response.status in [200, 204]
                
        except aiohttp.ClientError:
            return False
    
    async def inference(
        self,
        model_id: str,
        prompt: str,
        version_id: Optional[str] = None,
        generation_config: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Perform inference on a model.
        
        Args:
            model_id: Model identifier (owner/name format)
            prompt: Input prompt
            version_id: Optional specific version ID
            generation_config: Optional generation parameters
            
        Returns:
            Dictionary with 'text', 'latency_ms', 'prediction_id'
        """
        if not self._connected:
            raise RuntimeError("Not connected to Replicate")
        
        # Build input data
        config = generation_config or {}
        input_data = {
            "prompt": prompt,
            "max_length": config.get("max_tokens", 256),
            "temperature": config.get("temperature", 0.7),
            "top_p": config.get("top_p", 0.9),
            "repetition_penalty": config.get("repetition_penalty", 1.0),
        }
        
        # Create prediction
        start_time = asyncio.get_event_loop().time()
        prediction_id = await self.create_prediction(
            model_id=model_id,
            version_id=version_id,
            input_data=input_data,
        )
        
        # Wait for completion
        prediction = await self.wait_for_prediction(prediction_id)
        end_time = asyncio.get_event_loop().time()
        
        latency_ms = (end_time - start_time) * 1000
        
        # Extract output
        output = prediction.get("output", "")
        if isinstance(output, list):
            output = "".join(output)
        
        return {
            "text": output,
            "latency_ms": latency_ms,
            "prediction_id": prediction_id,
            "status": prediction.get("status"),
            "metrics": prediction.get("metrics", {}),
        }
    
    async def upload_artifact(self, path: str, metadata: Dict) -> str:
        """
        Upload an adapter to Replicate.
        
        Note: Replicate requires models to be pushed via Cog or Docker.
        This method returns a placeholder URL.
        
        Args:
            path: Local path to adapter directory
            metadata: Adapter metadata
            
        Returns:
            Artifact URL (placeholder)
            
        Raises:
            FileNotFoundError: If local path doesn't exist
        """
        if not self._connected:
            raise RuntimeError("Not connected to Replicate")
        
        adapter_path = Path(path)
        if not adapter_path.exists():
            raise FileNotFoundError(f"Adapter path not found: {path}")
        
        # Replicate uses Cog for model packaging
        # This is a simplified implementation
        # In production, you would use Cog to build and push the model
        
        adapter_name = metadata.get("name", "adapter")
        
        # Return a placeholder URL
        # In a real implementation, this would be the URL after pushing with Cog
        return f"https://replicate.delivery/models/{adapter_name}"
    
    # Required abstract methods (not applicable for inference platform)
    
    async def submit_job(self, config: TrainingConfig) -> str:
        """Not supported for inference platform."""
        raise NotImplementedError("Replicate connector does not support training jobs")
    
    async def get_job_status(self, job_id: str) -> JobStatus:
        """Not supported for inference platform."""
        raise NotImplementedError("Replicate connector does not support training jobs")
    
    async def cancel_job(self, job_id: str) -> bool:
        """Not supported for inference platform."""
        raise NotImplementedError("Replicate connector does not support training jobs")
    
    async def stream_logs(self, job_id: str) -> AsyncIterator[str]:
        """Not supported for inference platform."""
        raise NotImplementedError("Replicate connector does not support training jobs")
        yield  # Make it a generator
    
    async def fetch_artifact(self, job_id: str) -> bytes:
        """Not supported for inference platform."""
        raise NotImplementedError("Replicate connector does not support training jobs")
    
    async def list_resources(self) -> List[Resource]:
        """
        List available inference resources.
        
        Returns:
            List of available GPU resources
        """
        if not self._connected:
            return []
        
        # Replicate offers various GPU types
        return [
            Resource(
                id="replicate-t4",
                name="NVIDIA T4",
                type=ResourceType.GPU,
                gpu_type="T4",
                gpu_count=1,
                vram_gb=16,
                available=True,
                region="us-east-1",
            ),
            Resource(
                id="replicate-a40-small",
                name="NVIDIA A40 (Small)",
                type=ResourceType.GPU,
                gpu_type="A40",
                gpu_count=1,
                vram_gb=48,
                available=True,
                region="us-east-1",
            ),
            Resource(
                id="replicate-a40-large",
                name="NVIDIA A40 (Large)",
                type=ResourceType.GPU,
                gpu_type="A40",
                gpu_count=1,
                vram_gb=48,
                available=True,
                region="us-east-1",
            ),
        ]
    
    async def get_pricing(self, resource_id: str) -> PricingInfo:
        """
        Get pricing information for resources.
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            Pricing information
        """
        # Replicate pricing (per second of compute)
        pricing_map = {
            "replicate-t4": PricingInfo(
                resource_id=resource_id,
                price_per_hour=0.23,  # ~$0.000064/second
                currency="USD",
                billing_increment_seconds=1,
                minimum_charge_seconds=1,
            ),
            "replicate-a40-small": PricingInfo(
                resource_id=resource_id,
                price_per_hour=1.40,  # ~$0.000389/second
                currency="USD",
                billing_increment_seconds=1,
                minimum_charge_seconds=1,
            ),
            "replicate-a40-large": PricingInfo(
                resource_id=resource_id,
                price_per_hour=2.80,  # ~$0.000778/second
                currency="USD",
                billing_increment_seconds=1,
                minimum_charge_seconds=1,
            ),
        }
        
        if resource_id not in pricing_map:
            raise ValueError(f"Invalid resource ID: {resource_id}")
        
        return pricing_map[resource_id]
    
    def get_required_credentials(self) -> List[str]:
        """Get list of required credential keys."""
        return ["api_token"]
