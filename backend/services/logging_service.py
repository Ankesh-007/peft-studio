"""
Logging Service

Handles comprehensive logging and diagnostic report generation for training errors.
Validates: Requirements 19.1, 19.2, 19.3, 19.4, 19.5
"""

import logging
import traceback
import sys
import platform
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SystemState:
    """Captures system state at the time of error"""
    timestamp: datetime
    platform: str
    python_version: str
    cpu_usage_percent: float
    memory_usage_percent: float
    gpu_info: Optional[Dict[str, Any]] = None
    disk_usage_percent: Optional[float] = None
    network_status: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "platform": self.platform,
            "python_version": self.python_version,
            "cpu_usage_percent": self.cpu_usage_percent,
            "memory_usage_percent": self.memory_usage_percent,
            "gpu_info": self.gpu_info,
            "disk_usage_percent": self.disk_usage_percent,
            "network_status": self.network_status
        }


@dataclass
class ErrorLog:
    """Complete error log entry with all required information"""
    timestamp: datetime
    error_message: str
    stack_trace: str
    system_state: SystemState
    error_type: str = "unknown"
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    context: Optional[Dict[str, Any]] = None
    recent_actions: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "system_state": self.system_state.to_dict(),
            "error_type": self.error_type,
            "severity": self.severity.value,
            "context": self.context or {},
            "recent_actions": self.recent_actions or []
        }
    
    def is_complete(self) -> bool:
        """Check if error log contains all required fields"""
        # Check required fields are present and non-empty
        if not self.timestamp:
            return False
        if not self.error_message or len(self.error_message.strip()) == 0:
            return False
        if not self.stack_trace or len(self.stack_trace.strip()) == 0:
            return False
        if not self.system_state:
            return False
        
        # Check system state completeness
        if not self.system_state.timestamp:
            return False
        if not self.system_state.platform or len(self.system_state.platform.strip()) == 0:
            return False
        if not self.system_state.python_version or len(self.system_state.python_version.strip()) == 0:
            return False
        
        return True


@dataclass
class DiagnosticReport:
    """Complete diagnostic report for troubleshooting"""
    report_id: str
    generated_at: datetime
    error_logs: List[ErrorLog]
    configuration: Dict[str, Any]
    environment_info: Dict[str, Any]
    recent_operations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at.isoformat(),
            "error_logs": [log.to_dict() for log in self.error_logs],
            "configuration": self.configuration,
            "environment_info": self.environment_info,
            "recent_operations": self.recent_operations
        }


class LoggingService:
    """Service for comprehensive logging and diagnostic report generation"""
    
    def __init__(self):
        self.error_logs: List[ErrorLog] = []
        self.recent_actions: List[str] = []
        self.max_recent_actions = 50
    
    def capture_system_state(self) -> SystemState:
        """Capture current system state"""
        try:
            import psutil
            
            # Get CPU and memory usage
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Get disk usage
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            
            # Try to get GPU info
            gpu_info = None
            try:
                import torch
                if torch.cuda.is_available():
                    gpu_info = {
                        "device_count": torch.cuda.device_count(),
                        "current_device": torch.cuda.current_device(),
                        "device_name": torch.cuda.get_device_name(0),
                        "memory_allocated": torch.cuda.memory_allocated(0),
                        "memory_reserved": torch.cuda.memory_reserved(0)
                    }
            except Exception as e:
                logger.debug(f"Could not get GPU info: {e}")
            
            return SystemState(
                timestamp=datetime.now(),
                platform=platform.platform(),
                python_version=sys.version,
                cpu_usage_percent=cpu_usage,
                memory_usage_percent=memory_usage,
                gpu_info=gpu_info,
                disk_usage_percent=disk_usage,
                network_status="online"  # Simplified for now
            )
        except Exception as e:
            logger.error(f"Error capturing system state: {e}")
            # Return minimal system state
            return SystemState(
                timestamp=datetime.now(),
                platform=platform.platform(),
                python_version=sys.version,
                cpu_usage_percent=0.0,
                memory_usage_percent=0.0
            )
    
    def log_error(
        self,
        error: Exception,
        error_type: str = "unknown",
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorLog:
        """
        Log an error with complete information.
        
        Args:
            error: The exception that occurred
            error_type: Type of error (training_error, oom_error, etc.)
            severity: Error severity level
            context: Additional context information
            
        Returns:
            ErrorLog with complete information
        """
        # Capture error message
        error_message = str(error)
        
        # Capture stack trace
        stack_trace = ''.join(traceback.format_exception(
            type(error),
            error,
            error.__traceback__
        ))
        
        # Capture system state
        system_state = self.capture_system_state()
        
        # Create error log
        error_log = ErrorLog(
            timestamp=datetime.now(),
            error_message=error_message,
            stack_trace=stack_trace,
            system_state=system_state,
            error_type=error_type,
            severity=severity,
            context=context,
            recent_actions=self.recent_actions.copy()
        )
        
        # Store error log
        self.error_logs.append(error_log)
        
        # Log to standard logger
        logger.error(
            f"Error logged: {error_type} - {error_message}",
            extra={
                "error_type": error_type,
                "severity": severity.value,
                "timestamp": error_log.timestamp.isoformat()
            }
        )
        
        return error_log
    
    def track_action(self, action: str):
        """Track a user action for recent actions log"""
        self.recent_actions.append(f"{datetime.now().isoformat()}: {action}")
        
        # Keep only recent actions
        if len(self.recent_actions) > self.max_recent_actions:
            self.recent_actions = self.recent_actions[-self.max_recent_actions:]
    
    def generate_diagnostic_report(
        self,
        configuration: Optional[Dict[str, Any]] = None,
        environment_info: Optional[Dict[str, Any]] = None
    ) -> DiagnosticReport:
        """
        Generate a comprehensive diagnostic report.
        
        Args:
            configuration: Current configuration
            environment_info: Environment information
            
        Returns:
            DiagnosticReport with all error logs and system information
        """
        import uuid
        
        report = DiagnosticReport(
            report_id=str(uuid.uuid4()),
            generated_at=datetime.now(),
            error_logs=self.error_logs.copy(),
            configuration=configuration or {},
            environment_info=environment_info or self._get_environment_info(),
            recent_operations=self.recent_actions.copy()
        )
        
        return report
    
    def _get_environment_info(self) -> Dict[str, Any]:
        """Get environment information"""
        env_info = {
            "platform": platform.platform(),
            "python_version": sys.version,
            "python_implementation": platform.python_implementation(),
        }
        
        # Try to get package versions
        try:
            import torch
            env_info["torch_version"] = torch.__version__
            env_info["cuda_available"] = torch.cuda.is_available()
            if torch.cuda.is_available():
                env_info["cuda_version"] = torch.version.cuda
        except ImportError:
            pass
        
        try:
            import transformers
            env_info["transformers_version"] = transformers.__version__
        except ImportError:
            pass
        
        return env_info
    
    def get_error_logs(
        self,
        severity: Optional[ErrorSeverity] = None,
        error_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[ErrorLog]:
        """
        Get error logs with optional filtering.
        
        Args:
            severity: Filter by severity level
            error_type: Filter by error type
            limit: Maximum number of logs to return
            
        Returns:
            List of error logs matching filters
        """
        logs = self.error_logs
        
        # Apply filters
        if severity:
            logs = [log for log in logs if log.severity == severity]
        
        if error_type:
            logs = [log for log in logs if log.error_type == error_type]
        
        # Apply limit
        if limit:
            logs = logs[-limit:]
        
        return logs
    
    def clear_logs(self):
        """Clear all error logs"""
        self.error_logs.clear()
        logger.info("Error logs cleared")
    
    def export_logs(self, filepath: str):
        """Export error logs to a file"""
        import json
        
        with open(filepath, 'w') as f:
            json.dump(
                [log.to_dict() for log in self.error_logs],
                f,
                indent=2
            )
        
        logger.info(f"Error logs exported to {filepath}")


# Singleton instance
_logging_service = None


def get_logging_service() -> LoggingService:
    """Get the singleton logging service instance"""
    global _logging_service
    if _logging_service is None:
        _logging_service = LoggingService()
    return _logging_service
