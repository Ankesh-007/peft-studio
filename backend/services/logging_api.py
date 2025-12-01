"""
Logging API

REST API endpoints for logging and diagnostics functionality.
Validates: Requirements 19.1, 19.2, 19.3, 19.4, 19.5
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

from services.logging_service import (
    get_logging_service,
    ErrorSeverity,
    ErrorLog,
    DiagnosticReport
)


router = APIRouter(prefix="/api/logging", tags=["logging"])


class LogLevel(str, Enum):
    """Log level filter"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogEntry(BaseModel):
    """Log entry model"""
    timestamp: str
    level: str
    message: str
    error_type: Optional[str] = None
    severity: Optional[str] = None
    context: Optional[dict] = None


class LogFilter(BaseModel):
    """Log filter parameters"""
    level: Optional[LogLevel] = None
    severity: Optional[ErrorSeverity] = None
    error_type: Optional[str] = None
    search_query: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: Optional[int] = 100


class DiagnosticReportResponse(BaseModel):
    """Diagnostic report response"""
    report_id: str
    generated_at: str
    error_count: int
    download_url: str


class DebugModeStatus(BaseModel):
    """Debug mode status"""
    enabled: bool
    verbose_logging: bool


# Global debug mode state
_debug_mode_enabled = False


@router.get("/logs")
async def get_logs(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    error_type: Optional[str] = Query(None, description="Filter by error type"),
    search: Optional[str] = Query(None, description="Search query"),
    limit: Optional[int] = Query(100, description="Maximum number of logs")
):
    """
    Get error logs with optional filtering.
    
    Query Parameters:
    - severity: Filter by severity level (low, medium, high, critical)
    - error_type: Filter by error type
    - search: Search in error messages
    - limit: Maximum number of logs to return
    
    Returns:
    - List of error logs matching filters
    """
    try:
        service = get_logging_service()
        
        # Convert severity string to enum if provided
        severity_enum = None
        if severity:
            try:
                severity_enum = ErrorSeverity(severity.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid severity: {severity}. Must be one of: low, medium, high, critical"
                )
        
        # Get filtered logs
        logs = service.get_error_logs(
            severity=severity_enum,
            error_type=error_type,
            limit=limit
        )
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            logs = [
                log for log in logs
                if search_lower in log.error_message.lower()
                or search_lower in log.stack_trace.lower()
            ]
        
        # Convert to response format
        return {
            "logs": [log.to_dict() for log in logs],
            "total": len(logs),
            "filtered": bool(severity or error_type or search)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/search")
async def search_logs(
    query: str = Query(..., description="Search query"),
    limit: Optional[int] = Query(100, description="Maximum number of results")
):
    """
    Search logs by query string.
    
    Searches in error messages, stack traces, and context.
    
    Query Parameters:
    - query: Search query string
    - limit: Maximum number of results
    
    Returns:
    - List of matching error logs
    """
    try:
        service = get_logging_service()
        
        # Get all logs
        all_logs = service.get_error_logs(limit=None)
        
        # Search in error messages, stack traces, and context
        query_lower = query.lower()
        matching_logs = []
        
        for log in all_logs:
            # Search in error message
            if query_lower in log.error_message.lower():
                matching_logs.append(log)
                continue
            
            # Search in stack trace
            if query_lower in log.stack_trace.lower():
                matching_logs.append(log)
                continue
            
            # Search in context
            if log.context:
                context_str = str(log.context).lower()
                if query_lower in context_str:
                    matching_logs.append(log)
                    continue
        
        # Apply limit
        if limit:
            matching_logs = matching_logs[-limit:]
        
        return {
            "logs": [log.to_dict() for log in matching_logs],
            "total": len(matching_logs),
            "query": query
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/diagnostic-report")
async def generate_diagnostic_report(
    configuration: Optional[dict] = None,
    environment_info: Optional[dict] = None
):
    """
    Generate a comprehensive diagnostic report.
    
    Request Body:
    - configuration: Optional configuration information
    - environment_info: Optional environment information
    
    Returns:
    - Diagnostic report with all error logs and system information
    """
    try:
        service = get_logging_service()
        
        # Generate report
        report = service.generate_diagnostic_report(
            configuration=configuration,
            environment_info=environment_info
        )
        
        # Save report to file
        import os
        import json
        from pathlib import Path
        
        # Create reports directory
        reports_dir = Path.home() / ".peft-studio" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Save report
        report_file = reports_dir / f"diagnostic_report_{report.report_id}.json"
        with open(report_file, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
        
        return {
            "report_id": report.report_id,
            "generated_at": report.generated_at.isoformat(),
            "error_count": len(report.error_logs),
            "download_url": f"/api/logging/diagnostic-report/{report.report_id}/download",
            "file_path": str(report_file)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/diagnostic-report/{report_id}/download")
async def download_diagnostic_report(report_id: str):
    """
    Download a diagnostic report.
    
    Path Parameters:
    - report_id: Report ID
    
    Returns:
    - Diagnostic report file
    """
    try:
        from pathlib import Path
        from fastapi.responses import FileResponse
        
        # Find report file
        reports_dir = Path.home() / ".peft-studio" / "reports"
        report_file = reports_dir / f"diagnostic_report_{report_id}.json"
        
        if not report_file.exists():
            raise HTTPException(status_code=404, detail="Report not found")
        
        return FileResponse(
            path=str(report_file),
            filename=f"diagnostic_report_{report_id}.json",
            media_type="application/json"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export")
async def export_logs(
    filepath: Optional[str] = None
):
    """
    Export error logs to a file.
    
    Request Body:
    - filepath: Optional custom file path (defaults to ~/.peft-studio/logs/export_<timestamp>.json)
    
    Returns:
    - Export file path
    """
    try:
        service = get_logging_service()
        
        # Generate default filepath if not provided
        if not filepath:
            from pathlib import Path
            logs_dir = Path.home() / ".peft-studio" / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = str(logs_dir / f"export_{timestamp}.json")
        
        # Export logs
        service.export_logs(filepath)
        
        return {
            "success": True,
            "filepath": filepath,
            "log_count": len(service.error_logs)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/logs")
async def clear_logs():
    """
    Clear all error logs.
    
    Returns:
    - Success status
    """
    try:
        service = get_logging_service()
        service.clear_logs()
        
        return {
            "success": True,
            "message": "All error logs cleared"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug-mode")
async def get_debug_mode():
    """
    Get debug mode status.
    
    Returns:
    - Debug mode status
    """
    return {
        "enabled": _debug_mode_enabled,
        "verbose_logging": _debug_mode_enabled
    }


@router.post("/debug-mode")
async def set_debug_mode(enabled: bool):
    """
    Enable or disable debug mode.
    
    Request Body:
    - enabled: Whether to enable debug mode
    
    Returns:
    - Updated debug mode status
    """
    global _debug_mode_enabled
    
    try:
        _debug_mode_enabled = enabled
        
        # Configure logging level based on debug mode
        import logging
        if enabled:
            logging.getLogger().setLevel(logging.DEBUG)
        else:
            logging.getLogger().setLevel(logging.INFO)
        
        return {
            "enabled": _debug_mode_enabled,
            "verbose_logging": _debug_mode_enabled,
            "message": f"Debug mode {'enabled' if enabled else 'disabled'}"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_log_stats():
    """
    Get logging statistics.
    
    Returns:
    - Statistics about error logs
    """
    try:
        service = get_logging_service()
        
        # Count logs by severity
        severity_counts = {
            "low": 0,
            "medium": 0,
            "high": 0,
            "critical": 0
        }
        
        # Count logs by error type
        error_type_counts = {}
        
        for log in service.error_logs:
            # Count by severity
            severity_counts[log.severity.value] += 1
            
            # Count by error type
            if log.error_type not in error_type_counts:
                error_type_counts[log.error_type] = 0
            error_type_counts[log.error_type] += 1
        
        return {
            "total_logs": len(service.error_logs),
            "by_severity": severity_counts,
            "by_error_type": error_type_counts,
            "recent_actions_count": len(service.recent_actions)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
