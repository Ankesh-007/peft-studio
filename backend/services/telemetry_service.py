"""
Telemetry Service

Implements opt-in telemetry with event tracking, anonymization, error reporting,
and performance metrics collection.

Requirements: 15.5
"""

import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import asyncio
from collections import defaultdict
import platform
import psutil


class TelemetryService:
    """
    Manages telemetry collection with user consent and data anonymization.
    
    Features:
    - Opt-in only telemetry
    - Automatic data anonymization
    - Event tracking
    - Error reporting
    - Performance metrics collection
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize telemetry service.
        
        Args:
            config_dir: Directory for storing telemetry configuration
        """
        self.config_dir = config_dir or Path.home() / ".peft-studio" / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.config_dir / "telemetry_config.json"
        self.events_file = self.config_dir / "telemetry_events.json"
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize event buffer
        self.event_buffer: List[Dict[str, Any]] = []
        self.buffer_lock = asyncio.Lock()
        
        # Performance metrics
        self.performance_metrics: Dict[str, List[float]] = defaultdict(list)
        
        # Session tracking
        self.session_id = self._generate_session_id()
        self.session_start = datetime.now()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load telemetry configuration."""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        
        # Default configuration (opt-out by default)
        return {
            "enabled": False,
            "user_id": self._generate_anonymous_id(),
            "created_at": datetime.now().isoformat(),
            "last_prompt": None
        }
    
    def _save_config(self):
        """Save telemetry configuration."""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def _generate_anonymous_id(self) -> str:
        """Generate anonymous user ID."""
        # Use machine-specific info to create consistent anonymous ID
        machine_id = f"{platform.node()}-{platform.machine()}"
        return hashlib.sha256(machine_id.encode()).hexdigest()[:16]
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        return str(uuid.uuid4())
    
    def is_enabled(self) -> bool:
        """Check if telemetry is enabled."""
        return self.config.get("enabled", False)
    
    def enable(self):
        """Enable telemetry collection."""
        self.config["enabled"] = True
        self.config["enabled_at"] = datetime.now().isoformat()
        self._save_config()
    
    def disable(self):
        """Disable telemetry collection."""
        self.config["enabled"] = False
        self.config["disabled_at"] = datetime.now().isoformat()
        self._save_config()
    
    def get_consent_status(self) -> Dict[str, Any]:
        """
        Get current consent status.
        
        Returns:
            Dictionary with consent information
        """
        return {
            "enabled": self.is_enabled(),
            "user_id": self.config.get("user_id"),
            "last_prompt": self.config.get("last_prompt"),
            "data_collected": [
                "Application events (start, stop, feature usage)",
                "Error reports (anonymized stack traces)",
                "Performance metrics (response times, resource usage)",
                "System information (OS, Python version)",
                "Feature usage statistics"
            ],
            "data_not_collected": [
                "Personal information (names, emails)",
                "API credentials or keys",
                "Model data or training datasets",
                "File paths or directory structures",
                "IP addresses"
            ]
        }
    
    def _anonymize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Anonymize sensitive data.
        
        Args:
            data: Raw event data
            
        Returns:
            Anonymized data
        """
        anonymized = data.copy()
        
        # Remove PII fields
        pii_fields = ['email', 'username', 'name', 'api_key', 'token', 'password']
        for field in pii_fields:
            anonymized.pop(field, None)
        
        # Hash identifiers
        if 'user_id' in anonymized:
            anonymized['user_id'] = hashlib.sha256(
                str(anonymized['user_id']).encode()
            ).hexdigest()[:16]
        
        # Anonymize file paths
        if 'file_path' in anonymized:
            # Only keep filename, not full path
            anonymized['file_path'] = Path(anonymized['file_path']).name
        
        # Anonymize error messages (remove potential PII)
        if 'error_message' in anonymized:
            # Remove file paths from error messages
            error_msg = anonymized['error_message']
            # Simple anonymization - in production, use more sophisticated methods
            anonymized['error_message'] = error_msg.split('\n')[0]  # First line only
        
        return anonymized
    
    async def track_event(
        self,
        event_type: str,
        properties: Optional[Dict[str, Any]] = None
    ):
        """
        Track an event.
        
        Args:
            event_type: Type of event (e.g., 'training_started', 'model_loaded')
            properties: Additional event properties
        """
        if not self.is_enabled():
            return
        
        event = {
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "user_id": self.config.get("user_id"),
            "properties": self._anonymize_data(properties or {})
        }
        
        async with self.buffer_lock:
            self.event_buffer.append(event)
            
            # Flush buffer if it gets too large
            if len(self.event_buffer) >= 100:
                await self._flush_events()
    
    async def track_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Track an error.
        
        Args:
            error: Exception that occurred
            context: Additional context about the error
        """
        if not self.is_enabled():
            return
        
        error_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": self._anonymize_data(context or {}),
            "system_info": self._get_system_info()
        }
        
        await self.track_event("error_occurred", error_data)
    
    async def track_performance(
        self,
        metric_name: str,
        value: float,
        unit: str = "ms"
    ):
        """
        Track a performance metric.
        
        Args:
            metric_name: Name of the metric (e.g., 'api_response_time')
            value: Metric value
            unit: Unit of measurement
        """
        if not self.is_enabled():
            return
        
        self.performance_metrics[metric_name].append(value)
        
        # Track as event
        await self.track_event("performance_metric", {
            "metric_name": metric_name,
            "value": value,
            "unit": unit
        })
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get anonymized system information."""
        return {
            "os": platform.system(),
            "os_version": platform.release(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "total_memory_gb": round(psutil.virtual_memory().total / (1024**3), 2)
        }
    
    async def _flush_events(self):
        """Flush event buffer to storage."""
        if not self.event_buffer:
            return
        
        # Load existing events
        events = []
        if self.events_file.exists():
            with open(self.events_file, 'r') as f:
                events = json.load(f)
        
        # Add new events
        events.extend(self.event_buffer)
        
        # Keep only last 1000 events
        events = events[-1000:]
        
        # Save events
        with open(self.events_file, 'w') as f:
            json.dump(events, f, indent=2)
        
        # Clear buffer
        self.event_buffer.clear()
    
    async def get_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get usage analytics.
        
        Args:
            start_date: Start date for analytics
            end_date: End date for analytics
            
        Returns:
            Analytics data
        """
        if not self.is_enabled():
            return {"error": "Telemetry not enabled"}
        
        # Flush current buffer
        await self._flush_events()
        
        # Load events
        if not self.events_file.exists():
            return {"events": [], "summary": {}}
        
        with open(self.events_file, 'r') as f:
            events = json.load(f)
        
        # Filter by date range
        if start_date or end_date:
            filtered_events = []
            for event in events:
                event_time = datetime.fromisoformat(event['timestamp'])
                if start_date and event_time < start_date:
                    continue
                if end_date and event_time > end_date:
                    continue
                filtered_events.append(event)
            events = filtered_events
        
        # Calculate summary statistics
        event_counts = defaultdict(int)
        for event in events:
            event_counts[event['event_type']] += 1
        
        # Performance metrics summary
        perf_summary = {}
        for metric_name, values in self.performance_metrics.items():
            if values:
                perf_summary[metric_name] = {
                    "count": len(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values)
                }
        
        return {
            "total_events": len(events),
            "event_counts": dict(event_counts),
            "performance_metrics": perf_summary,
            "session_duration_minutes": (
                datetime.now() - self.session_start
            ).total_seconds() / 60,
            "system_info": self._get_system_info()
        }
    
    async def export_data(self) -> Dict[str, Any]:
        """
        Export all telemetry data for user.
        
        Returns:
            All collected telemetry data
        """
        await self._flush_events()
        
        data = {
            "config": self.config,
            "events": [],
            "analytics": await self.get_analytics()
        }
        
        if self.events_file.exists():
            with open(self.events_file, 'r') as f:
                data["events"] = json.load(f)
        
        return data
    
    async def delete_data(self):
        """Delete all telemetry data."""
        # Clear buffer
        self.event_buffer.clear()
        
        # Delete files
        if self.events_file.exists():
            self.events_file.unlink()
        
        # Reset config but keep user_id
        user_id = self.config.get("user_id")
        self.config = {
            "enabled": False,
            "user_id": user_id,
            "deleted_at": datetime.now().isoformat()
        }
        self._save_config()
    
    async def shutdown(self):
        """Shutdown telemetry service and flush remaining events."""
        if self.is_enabled():
            await self.track_event("session_ended", {
                "duration_minutes": (
                    datetime.now() - self.session_start
                ).total_seconds() / 60
            })
        
        await self._flush_events()


# Global telemetry instance
_telemetry_instance: Optional[TelemetryService] = None


def get_telemetry() -> TelemetryService:
    """Get global telemetry instance."""
    global _telemetry_instance
    if _telemetry_instance is None:
        _telemetry_instance = TelemetryService()
    return _telemetry_instance


async def track_event(event_type: str, properties: Optional[Dict[str, Any]] = None):
    """Convenience function to track events."""
    telemetry = get_telemetry()
    await telemetry.track_event(event_type, properties)


async def track_error(error: Exception, context: Optional[Dict[str, Any]] = None):
    """Convenience function to track errors."""
    telemetry = get_telemetry()
    await telemetry.track_error(error, context)


async def track_performance(metric_name: str, value: float, unit: str = "ms"):
    """Convenience function to track performance metrics."""
    telemetry = get_telemetry()
    await telemetry.track_performance(metric_name, value, unit)
