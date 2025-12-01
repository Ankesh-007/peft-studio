"""
Deployment Management Service

Manages model deployment across multiple platforms (Predibase, Together AI, Modal, Replicate).
Handles deployment configuration, endpoint management, testing, and usage monitoring.

Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
import logging
import asyncio
from pathlib import Path

from connectors.connector_manager import get_connector_manager
from connectors.base import PlatformConnector


logger = logging.getLogger(__name__)


class DeploymentStatus(str, Enum):
    """Deployment status states"""
    PENDING = "pending"
    DEPLOYING = "deploying"
    ACTIVE = "active"
    FAILED = "failed"
    STOPPED = "stopped"
    UPDATING = "updating"


class DeploymentPlatform(str, Enum):
    """Supported deployment platforms"""
    PREDIBASE = "predibase"
    TOGETHER_AI = "together_ai"
    MODAL = "modal"
    REPLICATE = "replicate"


@dataclass
class DeploymentConfig:
    """Configuration for model deployment"""
    deployment_id: str
    name: str
    platform: str  # predibase, together_ai, modal, replicate
    
    # Model information
    model_path: str  # Path to adapter or model
    base_model: Optional[str] = None  # Base model for adapters
    
    # Deployment settings
    instance_type: Optional[str] = None
    min_instances: int = 1
    max_instances: int = 10
    auto_scaling: bool = True
    
    # Inference settings
    max_batch_size: int = 1
    timeout_seconds: int = 60
    
    # Environment
    environment_vars: Dict[str, str] = field(default_factory=dict)
    
    # Metadata
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class EndpointInfo:
    """Information about a deployment endpoint"""
    endpoint_id: str
    deployment_id: str
    url: str
    api_key: Optional[str] = None
    
    # Status
    status: str = "active"
    health_check_url: Optional[str] = None
    last_health_check: Optional[datetime] = None
    
    # Performance
    avg_latency_ms: float = 0.0
    requests_per_minute: float = 0.0
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        if self.last_health_check:
            data['last_health_check'] = self.last_health_check.isoformat()
        return data


@dataclass
class UsageMetrics:
    """Usage metrics for a deployment"""
    deployment_id: str
    
    # Request metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    
    # Performance metrics
    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    
    # Token metrics (for LLM deployments)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    
    # Cost metrics
    estimated_cost: float = 0.0
    cost_per_request: float = 0.0
    
    # Time period
    period_start: datetime = field(default_factory=datetime.now)
    period_end: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['period_start'] = self.period_start.isoformat()
        data['period_end'] = self.period_end.isoformat()
        return data


@dataclass
class Deployment:
    """Deployment with status and metadata"""
    deployment_id: str
    config: DeploymentConfig
    status: DeploymentStatus = DeploymentStatus.PENDING
    
    # Endpoint information
    endpoint: Optional[EndpointInfo] = None
    
    # Platform-specific ID
    platform_deployment_id: Optional[str] = None
    
    # Status tracking
    created_at: datetime = field(default_factory=datetime.now)
    deployed_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    
    # Error tracking
    error_message: Optional[str] = None
    
    # Usage tracking
    usage_metrics: Optional[UsageMetrics] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            'deployment_id': self.deployment_id,
            'config': self.config.to_dict(),
            'status': self.status.value,
            'endpoint': self.endpoint.to_dict() if self.endpoint else None,
            'platform_deployment_id': self.platform_deployment_id,
            'created_at': self.created_at.isoformat(),
            'deployed_at': self.deployed_at.isoformat() if self.deployed_at else None,
            'stopped_at': self.stopped_at.isoformat() if self.stopped_at else None,
            'error_message': self.error_message,
            'usage_metrics': self.usage_metrics.to_dict() if self.usage_metrics else None
        }


class DeploymentService:
    """
    Service for managing model deployments across multiple platforms.
    
    Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
    """
    
    def __init__(self):
        """Initialize deployment service"""
        self.deployments: Dict[str, Deployment] = {}
        self.connector_manager = get_connector_manager()
        logger.info("DeploymentService initialized")
    
    async def create_deployment(self, config: DeploymentConfig) -> Deployment:
        """
        Create a new deployment.
        
        Args:
            config: Deployment configuration
            
        Returns:
            Created Deployment
            
        Requirements: 9.1
        """
        deployment = Deployment(
            deployment_id=config.deployment_id,
            config=config,
            status=DeploymentStatus.PENDING
        )
        
        self.deployments[config.deployment_id] = deployment
        logger.info(f"Created deployment: {config.deployment_id} on {config.platform}")
        
        return deployment
    
    async def deploy_to_platform(self, deployment_id: str) -> Deployment:
        """
        Deploy a model to the configured platform.
        
        Args:
            deployment_id: Deployment identifier
            
        Returns:
            Updated Deployment
            
        Raises:
            ValueError: If deployment not found or platform not supported
            RuntimeError: If deployment fails
            
        Requirements: 9.1, 9.2
        """
        if deployment_id not in self.deployments:
            raise ValueError(f"Deployment not found: {deployment_id}")
        
        deployment = self.deployments[deployment_id]
        config = deployment.config
        
        # Get connector for platform
        connector = self.connector_manager.get(config.platform)
        if not connector:
            raise ValueError(f"Platform not found: {config.platform}")
        
        if not connector.supports_inference:
            raise ValueError(f"Platform {config.platform} does not support inference")
        
        try:
            deployment.status = DeploymentStatus.DEPLOYING
            logger.info(f"Deploying {deployment_id} to {config.platform}")
            
            # Deploy using connector
            platform_deployment_id = await connector.deploy_model(
                model_path=config.model_path,
                base_model=config.base_model,
                instance_type=config.instance_type,
                min_instances=config.min_instances,
                max_instances=config.max_instances,
                environment_vars=config.environment_vars
            )
            
            deployment.platform_deployment_id = platform_deployment_id
            deployment.status = DeploymentStatus.ACTIVE
            deployment.deployed_at = datetime.now()
            
            # Get endpoint information
            endpoint_url = await connector.get_endpoint_url(platform_deployment_id)
            
            deployment.endpoint = EndpointInfo(
                endpoint_id=f"{deployment_id}_endpoint",
                deployment_id=deployment_id,
                url=endpoint_url,
                status="active",
                created_at=datetime.now()
            )
            
            logger.info(
                f"Deployed {deployment_id} to {config.platform} "
                f"as {platform_deployment_id}, endpoint: {endpoint_url}"
            )
            
            return deployment
            
        except Exception as e:
            logger.error(f"Failed to deploy {deployment_id} to {config.platform}: {e}")
            deployment.status = DeploymentStatus.FAILED
            deployment.error_message = str(e)
            raise RuntimeError(f"Deployment failed: {str(e)}")
    
    async def stop_deployment(self, deployment_id: str) -> bool:
        """
        Stop a running deployment.
        
        Args:
            deployment_id: Deployment identifier
            
        Returns:
            True if stopped successfully
            
        Requirements: 9.3
        """
        if deployment_id not in self.deployments:
            raise ValueError(f"Deployment not found: {deployment_id}")
        
        deployment = self.deployments[deployment_id]
        
        if deployment.status != DeploymentStatus.ACTIVE:
            raise ValueError(f"Cannot stop deployment in status: {deployment.status}")
        
        if not deployment.platform_deployment_id:
            raise ValueError(f"Deployment {deployment_id} has no platform deployment ID")
        
        # Get connector
        connector = self.connector_manager.get(deployment.config.platform)
        if not connector:
            raise ValueError(f"Platform not found: {deployment.config.platform}")
        
        try:
            success = await connector.stop_deployment(deployment.platform_deployment_id)
            
            if success:
                deployment.status = DeploymentStatus.STOPPED
                deployment.stopped_at = datetime.now()
                
                if deployment.endpoint:
                    deployment.endpoint.status = "stopped"
                
                logger.info(f"Stopped deployment {deployment_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to stop deployment {deployment_id}: {e}")
            raise
    
    async def test_endpoint(self, deployment_id: str, test_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test a deployment endpoint with sample input.
        
        Args:
            deployment_id: Deployment identifier
            test_input: Test input data
            
        Returns:
            Response from endpoint
            
        Requirements: 9.4
        """
        if deployment_id not in self.deployments:
            raise ValueError(f"Deployment not found: {deployment_id}")
        
        deployment = self.deployments[deployment_id]
        
        if deployment.status != DeploymentStatus.ACTIVE:
            raise ValueError(f"Cannot test deployment in status: {deployment.status}")
        
        if not deployment.endpoint:
            raise ValueError(f"Deployment {deployment_id} has no endpoint")
        
        # Get connector
        connector = self.connector_manager.get(deployment.config.platform)
        if not connector:
            raise ValueError(f"Platform not found: {deployment.config.platform}")
        
        try:
            start_time = datetime.now()
            
            response = await connector.invoke_endpoint(
                deployment.platform_deployment_id,
                test_input
            )
            
            end_time = datetime.now()
            latency_ms = (end_time - start_time).total_seconds() * 1000
            
            # Update endpoint metrics
            if deployment.endpoint:
                deployment.endpoint.last_health_check = datetime.now()
                deployment.endpoint.avg_latency_ms = latency_ms
            
            logger.info(f"Tested endpoint for {deployment_id}, latency: {latency_ms:.2f}ms")
            
            return {
                'success': True,
                'response': response,
                'latency_ms': latency_ms,
                'timestamp': end_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to test endpoint for {deployment_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_usage_metrics(self, deployment_id: str) -> UsageMetrics:
        """
        Get usage metrics for a deployment.
        
        Args:
            deployment_id: Deployment identifier
            
        Returns:
            UsageMetrics
            
        Requirements: 9.5
        """
        if deployment_id not in self.deployments:
            raise ValueError(f"Deployment not found: {deployment_id}")
        
        deployment = self.deployments[deployment_id]
        
        if not deployment.platform_deployment_id:
            raise ValueError(f"Deployment {deployment_id} has no platform deployment ID")
        
        # Get connector
        connector = self.connector_manager.get(deployment.config.platform)
        if not connector:
            raise ValueError(f"Platform not found: {deployment.config.platform}")
        
        try:
            # Fetch metrics from platform
            platform_metrics = await connector.get_deployment_metrics(
                deployment.platform_deployment_id
            )
            
            # Convert to our format
            metrics = UsageMetrics(
                deployment_id=deployment_id,
                total_requests=platform_metrics.get('total_requests', 0),
                successful_requests=platform_metrics.get('successful_requests', 0),
                failed_requests=platform_metrics.get('failed_requests', 0),
                avg_latency_ms=platform_metrics.get('avg_latency_ms', 0.0),
                p50_latency_ms=platform_metrics.get('p50_latency_ms', 0.0),
                p95_latency_ms=platform_metrics.get('p95_latency_ms', 0.0),
                p99_latency_ms=platform_metrics.get('p99_latency_ms', 0.0),
                total_input_tokens=platform_metrics.get('total_input_tokens', 0),
                total_output_tokens=platform_metrics.get('total_output_tokens', 0),
                estimated_cost=platform_metrics.get('estimated_cost', 0.0),
                period_start=datetime.fromisoformat(platform_metrics.get('period_start', datetime.now().isoformat())),
                period_end=datetime.fromisoformat(platform_metrics.get('period_end', datetime.now().isoformat()))
            )
            
            # Calculate cost per request
            if metrics.total_requests > 0:
                metrics.cost_per_request = metrics.estimated_cost / metrics.total_requests
            
            deployment.usage_metrics = metrics
            
            logger.info(f"Retrieved usage metrics for {deployment_id}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get usage metrics for {deployment_id}: {e}")
            raise
    
    def get_deployment(self, deployment_id: str) -> Optional[Deployment]:
        """
        Get deployment by ID.
        
        Args:
            deployment_id: Deployment identifier
            
        Returns:
            Deployment or None if not found
        """
        return self.deployments.get(deployment_id)
    
    def list_deployments(
        self,
        platform: Optional[str] = None,
        status: Optional[DeploymentStatus] = None
    ) -> List[Deployment]:
        """
        List deployments with optional filtering.
        
        Args:
            platform: Filter by platform
            status: Filter by status
            
        Returns:
            List of deployments
        """
        deployments = list(self.deployments.values())
        
        if platform:
            deployments = [d for d in deployments if d.config.platform == platform]
        
        if status:
            deployments = [d for d in deployments if d.status == status]
        
        return deployments
    
    async def update_deployment(
        self,
        deployment_id: str,
        updates: Dict[str, Any]
    ) -> Deployment:
        """
        Update deployment configuration.
        
        Args:
            deployment_id: Deployment identifier
            updates: Configuration updates
            
        Returns:
            Updated Deployment
            
        Requirements: 9.3
        """
        if deployment_id not in self.deployments:
            raise ValueError(f"Deployment not found: {deployment_id}")
        
        deployment = self.deployments[deployment_id]
        
        if deployment.status != DeploymentStatus.ACTIVE:
            raise ValueError(f"Cannot update deployment in status: {deployment.status}")
        
        # Get connector
        connector = self.connector_manager.get(deployment.config.platform)
        if not connector:
            raise ValueError(f"Platform not found: {deployment.config.platform}")
        
        try:
            deployment.status = DeploymentStatus.UPDATING
            
            # Update on platform
            await connector.update_deployment(
                deployment.platform_deployment_id,
                updates
            )
            
            # Update local config
            for key, value in updates.items():
                if hasattr(deployment.config, key):
                    setattr(deployment.config, key, value)
            
            deployment.status = DeploymentStatus.ACTIVE
            
            logger.info(f"Updated deployment {deployment_id}")
            
            return deployment
            
        except Exception as e:
            logger.error(f"Failed to update deployment {deployment_id}: {e}")
            deployment.status = DeploymentStatus.ACTIVE  # Revert to active
            raise


# Singleton instance
_deployment_service = None


def get_deployment_service() -> DeploymentService:
    """Get singleton instance of deployment service"""
    global _deployment_service
    if _deployment_service is None:
        _deployment_service = DeploymentService()
    return _deployment_service
