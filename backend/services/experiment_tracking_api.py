"""
Experiment Tracking API

FastAPI endpoints for experiment tracking integration.

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import logging

from services.experiment_tracking_service import (
    get_experiment_tracking_service,
    ExperimentConfig,
    ExperimentMetadata,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/experiments", tags=["experiments"])


# Request/Response Models

class StartExperimentRequest(BaseModel):
    """Request to start experiment tracking"""
    job_id: str
    tracker_name: str  # wandb, cometml, phoenix
    project_name: str
    experiment_name: Optional[str] = None
    tags: List[str] = []
    notes: Optional[str] = None
    metadata: Dict[str, str]  # model_name, dataset_name, use_case, provider, algorithm
    hyperparameters: Dict[str, Any]


class LogMetricsRequest(BaseModel):
    """Request to log metrics"""
    job_id: str
    metrics: Dict[str, Any]
    step: Optional[int] = None
    commit: bool = True


class LogHyperparametersRequest(BaseModel):
    """Request to log hyperparameters"""
    job_id: str
    hyperparameters: Dict[str, Any]


class LinkArtifactRequest(BaseModel):
    """Request to link an artifact"""
    job_id: str
    artifact_path: str
    artifact_type: str = "model"
    artifact_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class FinishExperimentRequest(BaseModel):
    """Request to finish experiment"""
    job_id: str
    status: str = "completed"
    summary: Optional[Dict[str, Any]] = None


class CompareExperimentsRequest(BaseModel):
    """Request to compare experiments"""
    job_ids: List[str]
    metrics: Optional[List[str]] = None


class SearchExperimentsRequest(BaseModel):
    """Request to search experiments"""
    filters: Optional[Dict[str, Any]] = None
    sort_by: Optional[str] = None
    limit: int = 100


# API Endpoints

@router.post("/start")
async def start_experiment(request: StartExperimentRequest):
    """
    Start experiment tracking for a training job.
    
    This endpoint initializes experiment tracking on the specified platform
    (W&B, Comet ML, or Phoenix) and begins logging.
    """
    try:
        service = get_experiment_tracking_service()
        
        # Create config
        config = ExperimentConfig(
            tracker_name=request.tracker_name,
            project_name=request.project_name,
            experiment_name=request.experiment_name,
            tags=request.tags,
            notes=request.notes,
        )
        
        # Create metadata
        metadata = ExperimentMetadata(
            job_id=request.job_id,
            model_name=request.metadata.get("model_name", "unknown"),
            dataset_name=request.metadata.get("dataset_name", "unknown"),
            use_case=request.metadata.get("use_case", "training"),
            provider=request.metadata.get("provider", "local"),
            algorithm=request.metadata.get("algorithm", "lora"),
        )
        
        # Start experiment
        success = await service.start_experiment(
            job_id=request.job_id,
            config=config,
            metadata=metadata,
            hyperparameters=request.hyperparameters,
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to start experiment tracking")
        
        # Get experiment info
        exp_info = service.get_experiment_info(request.job_id)
        
        return {
            "success": True,
            "message": f"Experiment tracking started on {request.tracker_name}",
            "experiment": exp_info,
        }
        
    except Exception as e:
        logger.error(f"Error starting experiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/metrics")
async def log_metrics(request: LogMetricsRequest):
    """
    Log metrics for an experiment.
    
    Metrics are automatically batched for efficiency. Set commit=False
    to buffer metrics and reduce API calls.
    """
    try:
        service = get_experiment_tracking_service()
        
        success = await service.log_metrics(
            job_id=request.job_id,
            metrics=request.metrics,
            step=request.step,
            commit=request.commit,
        )
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Experiment {request.job_id} not found")
        
        return {
            "success": True,
            "message": "Metrics logged successfully",
        }
        
    except Exception as e:
        logger.error(f"Error logging metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hyperparameters")
async def log_hyperparameters(request: LogHyperparametersRequest):
    """
    Log or update hyperparameters for an experiment.
    
    Hyperparameters can be updated during training to track
    dynamic changes like learning rate schedules.
    """
    try:
        service = get_experiment_tracking_service()
        
        success = await service.log_hyperparameters(
            job_id=request.job_id,
            hyperparameters=request.hyperparameters,
        )
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Experiment {request.job_id} not found")
        
        return {
            "success": True,
            "message": "Hyperparameters logged successfully",
        }
        
    except Exception as e:
        logger.error(f"Error logging hyperparameters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/artifacts")
async def link_artifact(request: LinkArtifactRequest):
    """
    Link an artifact (model checkpoint, dataset, etc.) to an experiment.
    
    Artifacts are uploaded to the experiment tracker and linked
    to the experiment for easy access and versioning.
    """
    try:
        service = get_experiment_tracking_service()
        
        success = await service.link_artifact(
            job_id=request.job_id,
            artifact_path=request.artifact_path,
            artifact_type=request.artifact_type,
            artifact_name=request.artifact_name,
            metadata=request.metadata,
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to link artifact")
        
        return {
            "success": True,
            "message": "Artifact linked successfully",
        }
        
    except Exception as e:
        logger.error(f"Error linking artifact: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/finish")
async def finish_experiment(request: FinishExperimentRequest):
    """
    Finish experiment tracking for a job.
    
    This endpoint flushes any remaining metrics and marks
    the experiment as complete on the tracker.
    """
    try:
        service = get_experiment_tracking_service()
        
        success = await service.finish_experiment(
            job_id=request.job_id,
            status=request.status,
            summary=request.summary,
        )
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Experiment {request.job_id} not found")
        
        return {
            "success": True,
            "message": f"Experiment finished with status {request.status}",
        }
        
    except Exception as e:
        logger.error(f"Error finishing experiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare")
async def compare_experiments(request: CompareExperimentsRequest):
    """
    Compare multiple experiments across different trackers.
    
    Returns unified comparison data including metrics, hyperparameters,
    artifacts, and statistics.
    """
    try:
        service = get_experiment_tracking_service()
        
        comparison_data = await service.compare_experiments(
            job_ids=request.job_ids,
            metrics=request.metrics,
        )
        
        return {
            "success": True,
            "comparison": comparison_data,
        }
        
    except Exception as e:
        logger.error(f"Error comparing experiments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_experiments(request: SearchExperimentsRequest):
    """
    Search and filter experiments.
    
    Supports filtering by tracker, status, project, tags, date range,
    and metadata. Results can be sorted and limited.
    """
    try:
        service = get_experiment_tracking_service()
        
        results = await service.search_experiments(
            filters=request.filters,
            sort_by=request.sort_by,
            limit=request.limit,
        )
        
        return {
            "success": True,
            "count": len(results),
            "experiments": results,
        }
        
    except Exception as e:
        logger.error(f"Error searching experiments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}")
async def get_experiment(job_id: str):
    """
    Get detailed information about an experiment.
    
    Returns experiment metadata, hyperparameters, artifacts,
    summary metrics, and tracker URL.
    """
    try:
        service = get_experiment_tracking_service()
        
        exp_info = service.get_experiment_info(job_id)
        
        if not exp_info:
            raise HTTPException(status_code=404, detail=f"Experiment {job_id} not found")
        
        return {
            "success": True,
            "experiment": exp_info,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting experiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/url")
async def get_experiment_url(job_id: str):
    """
    Get the tracker dashboard URL for an experiment.
    
    Returns a direct link to view the experiment on the
    tracker platform (W&B, Comet ML, or Phoenix).
    """
    try:
        service = get_experiment_tracking_service()
        
        url = service.get_experiment_url(job_id)
        
        if not url:
            raise HTTPException(status_code=404, detail=f"Experiment {job_id} not found or URL not available")
        
        return {
            "success": True,
            "url": url,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting experiment URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_experiments(
    status: Optional[str] = Query(None, description="Filter by status"),
    tracker: Optional[str] = Query(None, description="Filter by tracker"),
    project: Optional[str] = Query(None, description="Filter by project"),
    limit: int = Query(100, description="Maximum number of results"),
):
    """
    List experiments with optional filtering.
    
    Returns a list of experiments matching the specified filters.
    """
    try:
        service = get_experiment_tracking_service()
        
        # Build filters
        filters = {}
        if status:
            filters["status"] = status
        if tracker:
            filters["tracker"] = tracker
        if project:
            filters["project"] = project
        
        results = await service.search_experiments(
            filters=filters if filters else None,
            limit=limit,
        )
        
        return {
            "success": True,
            "count": len(results),
            "experiments": results,
        }
        
    except Exception as e:
        logger.error(f"Error listing experiments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active/list")
async def list_active_experiments():
    """
    Get list of currently active experiments.
    
    Returns job IDs of all experiments with status "running".
    """
    try:
        service = get_experiment_tracking_service()
        
        active_job_ids = service.get_active_experiments()
        
        return {
            "success": True,
            "count": len(active_job_ids),
            "job_ids": active_job_ids,
        }
        
    except Exception as e:
        logger.error(f"Error listing active experiments: {e}")
        raise HTTPException(status_code=500, detail=str(e))
