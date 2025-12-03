"""
Tests for Telemetry System

Tests opt-in telemetry, event tracking with anonymization, error reporting,
and performance metrics collection.

Requirements: 15.5
"""

import pytest
import asyncio
import json
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import shutil

from services.telemetry_service import TelemetryService, get_telemetry


@pytest.fixture
def temp_config_dir():
    """Create a temporary config directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def telemetry_service(temp_config_dir):
    """Create a telemetry service instance for testing."""
    return TelemetryService(config_dir=temp_config_dir)


class TestTelemetryOptIn:
    """Test opt-in telemetry functionality."""
    
    def test_telemetry_disabled_by_default(self, telemetry_service):
        """Telemetry should be disabled by default."""
        assert not telemetry_service.is_enabled()
    
    def test_enable_telemetry(self, telemetry_service):
        """Should be able to enable telemetry."""
        telemetry_service.enable()
        assert telemetry_service.is_enabled()
    
    def test_disable_telemetry(self, telemetry_service):
        """Should be able to disable telemetry."""
        telemetry_service.enable()
        telemetry_service.disable()
        assert not telemetry_service.is_enabled()
    
    def test_consent_status(self, telemetry_service):
        """Should provide consent status information."""
        status = telemetry_service.get_consent_status()
        
        assert "enabled" in status
        assert "user_id" in status
        assert "data_collected" in status
        assert "data_not_collected" in status
        assert isinstance(status["data_collected"], list)
        assert isinstance(status["data_not_collected"], list)
    
    def test_persistence_across_instances(self, temp_config_dir):
        """Telemetry settings should persist across instances."""
        service1 = TelemetryService(config_dir=temp_config_dir)
        service1.enable()
        
        # Create new instance
        service2 = TelemetryService(config_dir=temp_config_dir)
        assert service2.is_enabled()


class TestEventTracking:
    """Test event tracking functionality."""
    
    @pytest.mark.asyncio
    async def test_track_event_when_disabled(self, telemetry_service):
        """Should not track events when telemetry is disabled."""
        await telemetry_service.track_event("test_event", {"key": "value"})
        
        # Buffer should be empty
        assert len(telemetry_service.event_buffer) == 0
    
    @pytest.mark.asyncio
    async def test_track_event_when_enabled(self, telemetry_service):
        """Should track events when telemetry is enabled."""
        telemetry_service.enable()
        
        await telemetry_service.track_event("test_event", {"key": "value"})
        
        # Buffer should have one event
        assert len(telemetry_service.event_buffer) == 1
        
        event = telemetry_service.event_buffer[0]
        assert event["event_type"] == "test_event"
        assert "timestamp" in event
        assert "session_id" in event
        assert "user_id" in event
        assert "properties" in event
    
    @pytest.mark.asyncio
    async def test_event_anonymization(self, telemetry_service):
        """Should anonymize sensitive data in events."""
        telemetry_service.enable()
        
        sensitive_data = {
            "email": "user@example.com",
            "username": "testuser",
            "api_key": "secret123",
            "file_path": "/home/user/secret/file.txt",
            "safe_data": "this is fine"
        }
        
        await telemetry_service.track_event("test_event", sensitive_data)
        
        event = telemetry_service.event_buffer[0]
        properties = event["properties"]
        
        # Sensitive fields should be removed
        assert "email" not in properties
        assert "username" not in properties
        assert "api_key" not in properties
        
        # File path should be anonymized (only filename)
        assert properties["file_path"] == "file.txt"
        
        # Safe data should remain
        assert properties["safe_data"] == "this is fine"
    
    @pytest.mark.asyncio
    async def test_buffer_flush(self, telemetry_service):
        """Should flush events to storage when buffer is full."""
        telemetry_service.enable()
        
        # Add 100 events to trigger flush
        for i in range(100):
            await telemetry_service.track_event(f"event_{i}")
        
        # Buffer should be empty after flush
        assert len(telemetry_service.event_buffer) == 0
        
        # Events should be saved to file
        assert telemetry_service.events_file.exists()


class TestErrorReporting:
    """Test error reporting functionality."""
    
    @pytest.mark.asyncio
    async def test_track_error(self, telemetry_service):
        """Should track errors with context."""
        telemetry_service.enable()
        
        try:
            raise ValueError("Test error")
        except ValueError as e:
            await telemetry_service.track_error(e, {"context": "test"})
        
        assert len(telemetry_service.event_buffer) == 1
        
        event = telemetry_service.event_buffer[0]
        assert event["event_type"] == "error_occurred"
        assert event["properties"]["error_type"] == "ValueError"
        assert "error_message" in event["properties"]
        assert "system_info" in event["properties"]
    
    @pytest.mark.asyncio
    async def test_error_anonymization(self, telemetry_service):
        """Should anonymize error messages."""
        telemetry_service.enable()
        
        try:
            raise ValueError("Error with /home/user/secret/file.txt")
        except ValueError as e:
            await telemetry_service.track_error(e, {
                "email": "user@example.com"
            })
        
        event = telemetry_service.event_buffer[0]
        properties = event["properties"]
        
        # Context should be anonymized
        assert "email" not in properties["context"]


class TestPerformanceMetrics:
    """Test performance metrics collection."""
    
    @pytest.mark.asyncio
    async def test_track_performance_metric(self, telemetry_service):
        """Should track performance metrics."""
        telemetry_service.enable()
        
        await telemetry_service.track_performance("api_response_time", 150.5, "ms")
        
        # Should be in performance metrics
        assert "api_response_time" in telemetry_service.performance_metrics
        assert telemetry_service.performance_metrics["api_response_time"] == [150.5]
        
        # Should also create an event
        assert len(telemetry_service.event_buffer) == 1
        event = telemetry_service.event_buffer[0]
        assert event["event_type"] == "performance_metric"
        assert event["properties"]["metric_name"] == "api_response_time"
        assert event["properties"]["value"] == 150.5
        assert event["properties"]["unit"] == "ms"
    
    @pytest.mark.asyncio
    async def test_multiple_performance_metrics(self, telemetry_service):
        """Should track multiple performance metrics."""
        telemetry_service.enable()
        
        await telemetry_service.track_performance("metric1", 100.0)
        await telemetry_service.track_performance("metric1", 200.0)
        await telemetry_service.track_performance("metric2", 50.0)
        
        assert len(telemetry_service.performance_metrics["metric1"]) == 2
        assert len(telemetry_service.performance_metrics["metric2"]) == 1


class TestAnalytics:
    """Test analytics functionality."""
    
    @pytest.mark.asyncio
    async def test_get_analytics(self, telemetry_service):
        """Should provide analytics summary."""
        telemetry_service.enable()
        
        # Track some events
        await telemetry_service.track_event("event1")
        await telemetry_service.track_event("event1")
        await telemetry_service.track_event("event2")
        await telemetry_service.track_performance("metric1", 100.0)
        
        analytics = await telemetry_service.get_analytics()
        
        assert analytics["total_events"] == 4
        assert "event1" in analytics["event_counts"]
        assert analytics["event_counts"]["event1"] == 2
        assert "metric1" in analytics["performance_metrics"]
        assert analytics["performance_metrics"]["metric1"]["count"] == 1
        assert analytics["performance_metrics"]["metric1"]["avg"] == 100.0
    
    @pytest.mark.asyncio
    async def test_analytics_date_filtering(self, telemetry_service):
        """Should filter analytics by date range."""
        telemetry_service.enable()
        
        # Track events
        await telemetry_service.track_event("event1")
        await telemetry_service._flush_events()
        
        # Get analytics for future date range (should be empty)
        future_start = datetime.now() + timedelta(days=1)
        future_end = datetime.now() + timedelta(days=2)
        
        analytics = await telemetry_service.get_analytics(
            start_date=future_start,
            end_date=future_end
        )
        
        assert analytics["total_events"] == 0


class TestDataExportAndDeletion:
    """Test data export and deletion functionality."""
    
    @pytest.mark.asyncio
    async def test_export_data(self, telemetry_service):
        """Should export all telemetry data."""
        telemetry_service.enable()
        
        await telemetry_service.track_event("test_event")
        
        data = await telemetry_service.export_data()
        
        assert "config" in data
        assert "events" in data
        assert "analytics" in data
        assert len(data["events"]) == 1
    
    @pytest.mark.asyncio
    async def test_delete_data(self, telemetry_service):
        """Should delete all telemetry data."""
        telemetry_service.enable()
        
        await telemetry_service.track_event("test_event")
        await telemetry_service._flush_events()
        
        # Events file should exist
        assert telemetry_service.events_file.exists()
        
        await telemetry_service.delete_data()
        
        # Events file should be deleted
        assert not telemetry_service.events_file.exists()
        
        # Telemetry should be disabled
        assert not telemetry_service.is_enabled()
        
        # Buffer should be empty
        assert len(telemetry_service.event_buffer) == 0


class TestSystemInfo:
    """Test system information collection."""
    
    def test_system_info_anonymization(self, telemetry_service):
        """System info should not contain PII."""
        system_info = telemetry_service._get_system_info()
        
        assert "os" in system_info
        assert "python_version" in system_info
        assert "cpu_count" in system_info
        assert "total_memory_gb" in system_info
        
        # Should not contain identifying information
        assert "hostname" not in system_info
        assert "username" not in system_info
        assert "ip_address" not in system_info


class TestSessionTracking:
    """Test session tracking functionality."""
    
    def test_session_id_generation(self, telemetry_service):
        """Should generate unique session ID."""
        assert telemetry_service.session_id is not None
        assert len(telemetry_service.session_id) > 0
    
    def test_session_start_time(self, telemetry_service):
        """Should track session start time."""
        assert telemetry_service.session_start is not None
        assert isinstance(telemetry_service.session_start, datetime)
    
    @pytest.mark.asyncio
    async def test_session_ended_event(self, telemetry_service):
        """Should track session end event."""
        telemetry_service.enable()
        
        await telemetry_service.shutdown()
        
        # Events should be flushed to file
        assert telemetry_service.events_file.exists()
        
        # Read events from file
        with open(telemetry_service.events_file, 'r') as f:
            events = json.load(f)
        
        # Should have session_ended event
        events_found = [e for e in events 
                       if e["event_type"] == "session_ended"]
        assert len(events_found) == 1
        
        event = events_found[0]
        assert "duration_minutes" in event["properties"]


class TestAnonymousID:
    """Test anonymous ID generation."""
    
    def test_anonymous_id_consistency(self, temp_config_dir):
        """Anonymous ID should be consistent across instances."""
        service1 = TelemetryService(config_dir=temp_config_dir)
        user_id1 = service1.config.get("user_id")
        
        service2 = TelemetryService(config_dir=temp_config_dir)
        user_id2 = service2.config.get("user_id")
        
        assert user_id1 == user_id2
    
    def test_anonymous_id_format(self, telemetry_service):
        """Anonymous ID should be properly formatted."""
        user_id = telemetry_service.config.get("user_id")
        
        assert user_id is not None
        assert len(user_id) == 16  # SHA256 hash truncated to 16 chars
        assert user_id.isalnum()


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    @pytest.mark.asyncio
    async def test_global_track_event(self):
        """Should be able to track events using global function."""
        from services.telemetry_service import track_event
        
        telemetry = get_telemetry()
        telemetry.enable()
        
        await track_event("test_event", {"key": "value"})
        
        assert len(telemetry.event_buffer) > 0
    
    @pytest.mark.asyncio
    async def test_global_track_error(self):
        """Should be able to track errors using global function."""
        from services.telemetry_service import track_error
        
        telemetry = get_telemetry()
        telemetry.enable()
        
        try:
            raise ValueError("Test error")
        except ValueError as e:
            await track_error(e)
        
        assert len(telemetry.event_buffer) > 0
    
    @pytest.mark.asyncio
    async def test_global_track_performance(self):
        """Should be able to track performance using global function."""
        from services.telemetry_service import track_performance
        
        telemetry = get_telemetry()
        telemetry.enable()
        
        await track_performance("test_metric", 100.0)
        
        assert "test_metric" in telemetry.performance_metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
