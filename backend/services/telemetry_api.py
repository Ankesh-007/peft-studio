"""
Telemetry API

FastAPI endpoints for telemetry management and analytics.

Requirements: 15.5
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

from .telemetry_service import get_telemetry


router = APIRouter(prefix="/api/telemetry", tags=["telemetry"])


class TelemetryConsentRequest(BaseModel):
    """Request to update telemetry consent."""
    enabled: bool


class EventTrackingRequest(BaseModel):
    """Request to track an event."""
    event_type: str
    properties: Optional[Dict[str, Any]] = None


class PerformanceMetricRequest(BaseModel):
    """Request to track a performance metric."""
    metric_name: str
    value: float
    unit: str = "ms"


class AnalyticsRequest(BaseModel):
    """Request for analytics data."""
    start_date: Optional[str] = None
    end_date: Optional[str] = None


@router.get("/consent")
async def get_consent_status():
    """
    Get current telemetry consent status.
    
    Returns information about what data is collected and user's consent status.
    """
    telemetry = get_telemetry()
    return telemetry.get_consent_status()


@router.post("/consent")
async def update_consent(request: TelemetryConsentRequest):
    """
    Update telemetry consent.
    
    Args:
        request: Consent update request
        
    Returns:
        Updated consent status
    """
    telemetry = get_telemetry()
    
    if request.enabled:
        telemetry.enable()
    else:
        telemetry.disable()
    
    return {
        "success": True,
        "enabled": telemetry.is_enabled(),
        "message": f"Telemetry {'enabled' if request.enabled else 'disabled'}"
    }


@router.post("/events")
async def track_event(request: EventTrackingRequest):
    """
    Track a telemetry event.
    
    Args:
        request: Event tracking request
        
    Returns:
        Success status
    """
    telemetry = get_telemetry()
    
    if not telemetry.is_enabled():
        raise HTTPException(
            status_code=403,
            detail="Telemetry is not enabled"
        )
    
    await telemetry.track_event(request.event_type, request.properties)
    
    return {
        "success": True,
        "message": "Event tracked"
    }


@router.post("/performance")
async def track_performance_metric(request: PerformanceMetricRequest):
    """
    Track a performance metric.
    
    Args:
        request: Performance metric request
        
    Returns:
        Success status
    """
    telemetry = get_telemetry()
    
    if not telemetry.is_enabled():
        raise HTTPException(
            status_code=403,
            detail="Telemetry is not enabled"
        )
    
    await telemetry.track_performance(
        request.metric_name,
        request.value,
        request.unit
    )
    
    return {
        "success": True,
        "message": "Performance metric tracked"
    }


@router.post("/analytics")
async def get_analytics(request: AnalyticsRequest):
    """
    Get usage analytics.
    
    Args:
        request: Analytics request with optional date range
        
    Returns:
        Analytics data
    """
    telemetry = get_telemetry()
    
    if not telemetry.is_enabled():
        raise HTTPException(
            status_code=403,
            detail="Telemetry is not enabled"
        )
    
    start_date = None
    end_date = None
    
    if request.start_date:
        try:
            start_date = datetime.fromisoformat(request.start_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid start_date format. Use ISO format."
            )
    
    if request.end_date:
        try:
            end_date = datetime.fromisoformat(request.end_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid end_date format. Use ISO format."
            )
    
    analytics = await telemetry.get_analytics(start_date, end_date)
    
    return analytics


@router.get("/export")
async def export_telemetry_data():
    """
    Export all telemetry data for the user.
    
    Returns:
        All collected telemetry data
    """
    telemetry = get_telemetry()
    
    if not telemetry.is_enabled():
        raise HTTPException(
            status_code=403,
            detail="Telemetry is not enabled"
        )
    
    data = await telemetry.export_data()
    
    return data


@router.delete("/data")
async def delete_telemetry_data():
    """
    Delete all telemetry data.
    
    Returns:
        Success status
    """
    telemetry = get_telemetry()
    
    await telemetry.delete_data()
    
    return {
        "success": True,
        "message": "All telemetry data deleted"
    }


@router.get("/health")
async def telemetry_health():
    """
    Check telemetry service health.
    
    Returns:
        Health status
    """
    telemetry = get_telemetry()
    
    return {
        "status": "healthy",
        "enabled": telemetry.is_enabled(),
        "session_id": telemetry.session_id
    }
