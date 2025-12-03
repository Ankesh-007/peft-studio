"""
Base connector interface and data models.

All platform connectors must implement the PlatformConnector abstract class
to ensure consistent behavior across different platforms.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, AsyncIterator
from enum import Enum


class ResourceType(Enum):
    """Types of compute resources."""
    GPU = "gpu"
    CPU = "cpu"
    TPU = "tpu"


class JobStatus(Enum):
    """Training job status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Resource:
    """Compute resource information."""
    id: str
    name: str
    type: ResourceType
    gpu_type: Optional[str] = None
    gpu_count: int = 0
    vram_gb: int = 0
    cpu_cores: int = 0
    ram_gb: int = 0
    available: bool = True
    region: Optional[str] = None


@dataclass
class PricingInfo:
    """Pricing information for a resource."""
    resource_id: str
    price_per_hour: float
    currency: str = "USD"
    billing_increment_seconds: int = 60
    minimum_charge_seconds: int = 60
    spot_available: bool = False
    spot_price_per_hour: Optional[float] = None


@dataclass
class TrainingConfig:
    """Training configuration."""
    # Model
    base_model: str
    model_source: str  # huggingface, civitai, ollama
    
    # PEFT
    algorithm: str  # lora, qlora, dora, pissa, rslora
    rank: int
    alpha: int
    dropout: float
    target_modules: List[str]
    
    # Quantization
    quantization: Optional[str] = None  # int8, int4, nf4
    
    # Training
    learning_rate: float = 2e-4
    batch_size: int = 4
    gradient_accumulation_steps: int = 4
    num_epochs: int = 3
    warmup_steps: int = 100
    
    # Compute
    provider: str = "local"
    resource_id: Optional[str] = None
    
    # Dataset
    dataset_path: str = ""
    validation_split: float = 0.1
    
    # Tracking
    experiment_tracker: Optional[str] = None  # wandb, cometml, phoenix
    project_name: str = "peft-training"
    
    # Output
    output_dir: str = "./output"
    checkpoint_steps: int = 500


class PlatformConnector(ABC):
    """
    Abstract base class for platform connectors.
    
    All connectors must implement this interface to ensure consistent
    behavior across different platforms. This enables the system to
    work with any platform that implements these methods.
    """
    
    # Connector metadata
    name: str = ""
    display_name: str = ""
    description: str = ""
    version: str = "1.0.0"
    
    # Supported features
    supports_training: bool = False
    supports_inference: bool = False
    supports_registry: bool = False
    supports_tracking: bool = False
    
    @abstractmethod
    async def connect(self, credentials: Dict[str, str]) -> bool:
        """
        Verify connection and store credentials.
        
        Args:
            credentials: Dictionary of credential key-value pairs
            
        Returns:
            True if connection successful, False otherwise
            
        Raises:
            ConnectionError: If connection fails
            ValueError: If credentials are invalid
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Disconnect from the platform and cleanup resources.
        
        Returns:
            True if disconnection successful
        """
        pass
    
    @abstractmethod
    async def verify_connection(self) -> bool:
        """
        Verify that the connection is still valid.
        
        Returns:
            True if connection is valid, False otherwise
        """
        pass
    
    @abstractmethod
    async def submit_job(self, config: TrainingConfig) -> str:
        """
        Submit a training job to the platform.
        
        Args:
            config: Training configuration
            
        Returns:
            Job ID for tracking
            
        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If job submission fails
        """
        pass
    
    @abstractmethod
    async def get_job_status(self, job_id: str) -> JobStatus:
        """
        Get the current status of a training job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Current job status
        """
        pass
    
    @abstractmethod
    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running training job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if cancellation successful
        """
        pass
    
    @abstractmethod
    async def stream_logs(self, job_id: str) -> AsyncIterator[str]:
        """
        Stream logs from a training job in real-time.
        
        Args:
            job_id: Job identifier
            
        Yields:
            Log lines as they become available
        """
        pass
    
    @abstractmethod
    async def fetch_artifact(self, job_id: str) -> bytes:
        """
        Download the trained adapter artifact.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Artifact data as bytes
            
        Raises:
            FileNotFoundError: If artifact doesn't exist
            RuntimeError: If download fails
        """
        pass
    
    @abstractmethod
    async def upload_artifact(self, path: str, metadata: Dict) -> str:
        """
        Upload an adapter to the platform's registry.
        
        Args:
            path: Local path to artifact
            metadata: Artifact metadata (name, description, etc.)
            
        Returns:
            Artifact ID or URL
            
        Raises:
            FileNotFoundError: If local file doesn't exist
            RuntimeError: If upload fails
        """
        pass
    
    @abstractmethod
    async def list_resources(self) -> List[Resource]:
        """
        List available compute resources.
        
        Returns:
            List of available resources
        """
        pass
    
    @abstractmethod
    async def get_pricing(self, resource_id: str) -> PricingInfo:
        """
        Get pricing information for a specific resource.
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            Pricing information
            
        Raises:
            ValueError: If resource_id is invalid
        """
        pass
    
    def get_required_credentials(self) -> List[str]:
        """
        Get list of required credential keys.
        
        Returns:
            List of credential key names
        """
        return []
    
    def validate_config(self, config: TrainingConfig) -> bool:
        """
        Validate a training configuration for this platform.
        
        Args:
            config: Training configuration to validate
            
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid with details
        """
        if not config.base_model:
            raise ValueError("base_model is required")
        if not config.dataset_path:
            raise ValueError("dataset_path is required")
        if config.rank <= 0:
            raise ValueError("rank must be positive")
        if config.alpha <= 0:
            raise ValueError("alpha must be positive")
        if not 0 <= config.dropout <= 1:
            raise ValueError("dropout must be between 0 and 1")
        return True
    
    # Deployment methods (optional, only for inference platforms)
    
    async def deploy_model(
        self,
        model_path: str,
        base_model: Optional[str] = None,
        instance_type: Optional[str] = None,
        min_instances: int = 1,
        max_instances: int = 10,
        environment_vars: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Deploy a model for inference.
        
        Args:
            model_path: Path to model or adapter
            base_model: Base model for adapters
            instance_type: Instance type to use
            min_instances: Minimum number of instances
            max_instances: Maximum number of instances
            environment_vars: Environment variables
            
        Returns:
            Platform deployment ID
            
        Raises:
            NotImplementedError: If platform doesn't support deployment
        """
        raise NotImplementedError(f"{self.name} does not support model deployment")
    
    async def stop_deployment(self, deployment_id: str) -> bool:
        """
        Stop a running deployment.
        
        Args:
            deployment_id: Platform deployment ID
            
        Returns:
            True if stopped successfully
            
        Raises:
            NotImplementedError: If platform doesn't support deployment
        """
        raise NotImplementedError(f"{self.name} does not support deployment management")
    
    async def get_endpoint_url(self, deployment_id: str) -> str:
        """
        Get the endpoint URL for a deployment.
        
        Args:
            deployment_id: Platform deployment ID
            
        Returns:
            Endpoint URL
            
        Raises:
            NotImplementedError: If platform doesn't support deployment
        """
        raise NotImplementedError(f"{self.name} does not support deployment")
    
    async def invoke_endpoint(
        self,
        deployment_id: str,
        input_data: Dict[str, any]
    ) -> Dict[str, any]:
        """
        Invoke a deployment endpoint with input data.
        
        Args:
            deployment_id: Platform deployment ID
            input_data: Input data for inference
            
        Returns:
            Response from endpoint
            
        Raises:
            NotImplementedError: If platform doesn't support deployment
        """
        raise NotImplementedError(f"{self.name} does not support endpoint invocation")
    
    async def get_deployment_metrics(self, deployment_id: str) -> Dict[str, any]:
        """
        Get usage metrics for a deployment.
        
        Args:
            deployment_id: Platform deployment ID
            
        Returns:
            Dictionary of metrics
            
        Raises:
            NotImplementedError: If platform doesn't support deployment
        """
        raise NotImplementedError(f"{self.name} does not support deployment metrics")
    
    async def update_deployment(
        self,
        deployment_id: str,
        updates: Dict[str, any]
    ) -> bool:
        """
        Update deployment configuration.
        
        Args:
            deployment_id: Platform deployment ID
            updates: Configuration updates
            
        Returns:
            True if updated successfully
            
        Raises:
            NotImplementedError: If platform doesn't support deployment updates
        """
        raise NotImplementedError(f"{self.name} does not support deployment updates")
