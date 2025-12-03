"""
Deployment Management API

FastAPI endpoints for deployment management.

Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
"""

from fastapi import APIRouter, HTTPException, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging

from services.deployment_service import (
    get_deployment_service,
    DeploymentConfig,
    DeploymentStatus,
    DeploymentPlatform
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/deployments", tags=["deployments"])


# Request/Response models

class CreateDeploymentRequest(BaseModel):
    """Request to create a deployment"""
    deployment_id: str = Field(..., description="Unique deployment identifier")
    name: str = Field(..., description="Deployment name")
    platform: str = Field(..., description="Deployment platform (predibase, together_ai, modal, replicate)")
    model_path: str = Field(..., description="Path to model or adapter")
    base_model: Optional[str] = Field(None, description="Base model for adapters")
    instance_type: Optional[str] = Field(None, description="Instance type")
    min_instances: int = Field(1, ge=1, description="Minimum instances")
    max_instances: int = Field(10, ge=1, description="Maximum instances")
    auto_scaling: bool = Field(True, description="Enable auto-scaling")
    max_batch_size: int = Field(1, ge=1, description="Maximum batch size")
    timeout_seconds: int = Field(60, ge=1, description="Request timeout")
    environment_vars: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    description: Optional[str] = Field(None, description="Deployment description")
    tags: List[str] = Field(default_factory=list, description="Tags")


class DeploymentResponse(BaseModel):
    """Deployment response"""
    deployment_id: str
    config: Dict[str, Any]
    status: str
    endpoint: Optional[Dict[str, Any]]
    platform_deployment_id: Optional[str]
    created_at: str
    deployed_at: Optional[str]
    stopped_at: Optional[str]
    error_message: Optional[str]
    usage_metrics: Optional[Dict[str, Any]]


class TestEndpointRequest(BaseModel):
    """Request to test an endpoint"""
    input_data: Dict[str, Any] = Field(..., description="Test input data")


class TestEndpointResponse(BaseModel):
    """Response from endpoint test"""
    success: bool
    response: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    latency_ms: Optional[float] = None
    timestamp: str


class UpdateDeploymentRequest(BaseModel):
    """Request to update deployment"""
    min_instances: Optional[int] = Field(None, ge=1)
    max_instances: Optional[int] = Field(None, ge=1)
    auto_scaling: Optional[bool] = None
    environment_vars: Optional[Dict[str, str]] = None


# Endpoints

@router.post("/", response_model=DeploymentResponse, status_code=status.HTTP_201_CREATED)
async def create_deployment(request: CreateDeploymentRequest):
    """
    Create a new deployment.
    
    Requirements: 9.1
    """
    try:
        service = get_deployment_service()
        
        config = DeploymentConfig(
            deployment_id=request.deployment_id,
            name=request.name,
            platform=request.platform,
            model_path=request.model_path,
            base_model=request.base_model,
            instance_type=request.instance_type,
            min_instances=request.min_instances,
            max_instances=request.max_instances,
            auto_scaling=request.auto_scaling,
            max_batch_size=request.max_batch_size,
            timeout_seconds=request.timeout_seconds,
            environment_vars=request.environment_vars,
            description=request.description,
            tags=request.tags
        )
        
        deployment = await service.create_deployment(config)
        
        return DeploymentResponse(**deployment.to_dict())
        
    except Exception as e:
        logger.error(f"Error creating deployment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{deployment_id}/deploy", response_model=DeploymentResponse)
async def deploy_to_platform(deployment_id: str):
    """
    Deploy a model to the configured platform.
    
    Requirements: 9.1, 9.2
    """
    try:
        service = get_deployment_service()
        deployment = await service.deploy_to_platform(deployment_id)
        
        return DeploymentResponse(**deployment.to_dict())
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deploying: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{deployment_id}/stop")
async def stop_deployment(deployment_id: str):
    """
    Stop a running deployment.
    
    Requirements: 9.3
    """
    try:
        service = get_deployment_service()
        success = await service.stop_deployment(deployment_id)
        
        return {"success": success, "deployment_id": deployment_id}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error stopping deployment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{deployment_id}/test", response_model=TestEndpointResponse)
async def test_endpoint(deployment_id: str, request: TestEndpointRequest):
    """
    Test a deployment endpoint with sample input.
    
    Requirements: 9.4
    """
    try:
        service = get_deployment_service()
        result = await service.test_endpoint(deployment_id, request.input_data)
        
        return TestEndpointResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error testing endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{deployment_id}/metrics")
async def get_usage_metrics(deployment_id: str):
    """
    Get usage metrics for a deployment.
    
    Requirements: 9.5
    """
    try:
        service = get_deployment_service()
        metrics = await service.get_usage_metrics(deployment_id)
        
        return metrics.to_dict()
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(deployment_id: str):
    """Get deployment by ID"""
    try:
        service = get_deployment_service()
        deployment = service.get_deployment(deployment_id)
        
        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deployment not found: {deployment_id}"
            )
        
        return DeploymentResponse(**deployment.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting deployment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/", response_model=List[DeploymentResponse])
async def list_deployments(
    platform: Optional[str] = None,
    status: Optional[str] = None
):
    """List deployments with optional filtering"""
    try:
        service = get_deployment_service()
        
        status_enum = None
        if status:
            try:
                status_enum = DeploymentStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status}"
                )
        
        deployments = service.list_deployments(platform=platform, status=status_enum)
        
        return [DeploymentResponse(**d.to_dict()) for d in deployments]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing deployments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.patch("/{deployment_id}", response_model=DeploymentResponse)
async def update_deployment(deployment_id: str, request: UpdateDeploymentRequest):
    """
    Update deployment configuration.
    
    Requirements: 9.3
    """
    try:
        service = get_deployment_service()
        
        updates = {}
        if request.min_instances is not None:
            updates['min_instances'] = request.min_instances
        if request.max_instances is not None:
            updates['max_instances'] = request.max_instances
        if request.auto_scaling is not None:
            updates['auto_scaling'] = request.auto_scaling
        if request.environment_vars is not None:
            updates['environment_vars'] = request.environment_vars
        
        deployment = await service.update_deployment(deployment_id, updates)
        
        return DeploymentResponse(**deployment.to_dict())
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating deployment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
