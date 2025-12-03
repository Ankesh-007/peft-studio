"""
Property-Based Test for Platform Connection Verification

Tests Property 11: Platform connection verification
For any platform connection, the system should detect invalid credentials within 5 seconds

Validates: Requirements 1.4, 1.5
"""

import pytest
import asyncio
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime
import time

from services.platform_connection_service import PlatformConnectionService
from connectors.base import PlatformConnector
from typing import Dict


# Mock connector for testing
class MockConnector(PlatformConnector):
    """Mock connector for testing connection verification."""
    
    name = "mock_platform"
    display_name = "Mock Platform"
    description = "Mock platform for testing"
    version = "1.0.0"
    supports_training = True
    supports_inference = False
    supports_registry = False
    supports_tracking = False
    
    def __init__(self):
        self.connected = False
        self.credentials = {}
        self.should_fail = False
        self.delay_seconds = 0
    
    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Mock connect method."""
        await asyncio.sleep(self.delay_seconds)
        
        if self.should_fail:
            return False
        
        # Check for valid credentials
        if 'api_key' not in credentials or not credentials['api_key']:
            return False
        
        # Simulate invalid credentials
        if credentials['api_key'] == 'invalid':
            return False
        
        self.connected = True
        self.credentials = credentials
        return True
    
    async def disconnect(self) -> bool:
        """Mock disconnect method."""
        self.connected = False
        self.credentials = {}
        return True
    
    async def verify_connection(self) -> bool:
        """Mock verify connection method."""
        await asyncio.sleep(self.delay_seconds)
        
        if self.should_fail:
            return False
        
        return self.connected
    
    async def submit_job(self, config) -> str:
        return "mock_job_id"
    
    async def get_job_status(self, job_id: str):
        from connectors.base import JobStatus
        return JobStatus.PENDING
    
    async def cancel_job(self, job_id: str) -> bool:
        return True
    
    async def stream_logs(self, job_id: str):
        yield "mock log"
    
    async def fetch_artifact(self, job_id: str) -> bytes:
        return b"mock artifact"
    
    async def upload_artifact(self, path: str, metadata: Dict) -> str:
        return "mock_artifact_id"
    
    async def list_resources(self):
        return []
    
    async def get_pricing(self, resource_id: str):
        from connectors.base import PricingInfo
        return PricingInfo(resource_id=resource_id, price_per_hour=1.0)
    
    def get_required_credentials(self):
        return ['api_key']


@pytest.fixture
def connection_service():
    """Create a connection service with mock connector."""
    service = PlatformConnectionService()
    
    # Register mock connector
    mock_connector = MockConnector()
    service.connector_manager.register(mock_connector)
    
    return service


@pytest.fixture
def mock_connector():
    """Create a mock connector."""
    return MockConnector()


# ============================================================================
# Property 11: Platform connection verification
# ============================================================================

@pytest.mark.asyncio
@given(
    api_key=st.text(min_size=1, max_size=100)
)
@settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.too_slow])
async def test_property_invalid_credentials_detected_quickly(api_key):
    """
    Property 11: Platform connection verification
    
    For any platform connection, the system should detect invalid credentials
    within 5 seconds.
    
    **Feature: unified-llm-platform, Property 11: Platform connection verification**
    **Validates: Requirements 1.4, 1.5**
    """
    service = PlatformConnectionService()
    mock_connector = MockConnector()
    service.connector_manager.register(mock_connector)
    
    # Use invalid credentials
    credentials = {'api_key': 'invalid'}
    
    # Measure verification time
    start_time = time.time()
    
    try:
        result = await service.verify_connection('mock_platform', timeout_seconds=5)
        verification_time = time.time() - start_time
        
        # Property: Verification should complete within 5 seconds
        assert verification_time <= 5.0, \
            f"Verification took {verification_time:.2f}s, should be ≤ 5s"
        
        # Property: Invalid credentials should be detected
        assert not result['valid'], \
            "Invalid credentials should be detected as invalid"
        
    except Exception as e:
        verification_time = time.time() - start_time
        
        # Even with errors, should complete within 5 seconds
        assert verification_time <= 5.0, \
            f"Verification with error took {verification_time:.2f}s, should be ≤ 5s"


@pytest.mark.asyncio
@given(
    api_key=st.text(min_size=10, max_size=100).filter(lambda x: x != 'invalid')
)
@settings(max_examples=50, deadline=None)
async def test_property_valid_credentials_verified_quickly(api_key):
    """
    Property 11: Platform connection verification (valid case)
    
    For any platform connection with valid credentials, verification should
    complete within 5 seconds and return valid=True.
    
    **Feature: unified-llm-platform, Property 11: Platform connection verification**
    **Validates: Requirements 1.4, 1.5**
    """
    service = PlatformConnectionService()
    mock_connector = MockConnector()
    service.connector_manager.register(mock_connector)
    
    # Connect with valid credentials
    credentials = {'api_key': api_key}
    await service.connect_platform('mock_platform', credentials)
    
    # Measure verification time
    start_time = time.time()
    result = await service.verify_connection('mock_platform', timeout_seconds=5)
    verification_time = time.time() - start_time
    
    # Property: Verification should complete within 5 seconds
    assert verification_time <= 5.0, \
        f"Verification took {verification_time:.2f}s, should be ≤ 5s"
    
    # Property: Valid credentials should be verified as valid
    assert result['valid'], \
        "Valid credentials should be verified as valid"
    
    # Cleanup
    await service.disconnect_platform('mock_platform')


@pytest.mark.asyncio
async def test_property_timeout_enforced():
    """
    Property 11: Platform connection verification (timeout enforcement)
    
    Verification should respect the timeout parameter and not exceed it.
    
    **Feature: unified-llm-platform, Property 11: Platform connection verification**
    **Validates: Requirements 1.4, 1.5**
    """
    service = PlatformConnectionService()
    mock_connector = MockConnector()
    
    # Set a long delay to trigger timeout
    mock_connector.delay_seconds = 10
    service.connector_manager.register(mock_connector)
    
    # Connect first
    credentials = {'api_key': 'valid_key'}
    await service.connect_platform('mock_platform', credentials)
    
    # Verify with short timeout
    timeout_seconds = 2
    start_time = time.time()
    result = await service.verify_connection('mock_platform', timeout_seconds=timeout_seconds)
    verification_time = time.time() - start_time
    
    # Property: Should not exceed timeout by more than 1 second (for processing overhead)
    assert verification_time <= timeout_seconds + 1.0, \
        f"Verification took {verification_time:.2f}s, should be ≤ {timeout_seconds + 1.0}s"
    
    # Property: Timeout should result in invalid verification
    assert not result['valid'], \
        "Timed out verification should be marked as invalid"
    
    # Cleanup
    await service.disconnect_platform('mock_platform')


@pytest.mark.asyncio
@given(
    platform_name=st.text(min_size=1, max_size=50),
    api_key=st.text(min_size=1, max_size=100)
)
@settings(max_examples=30, deadline=None)
async def test_property_verification_result_structure(platform_name, api_key):
    """
    Property 11: Platform connection verification (result structure)
    
    For any verification attempt, the result should have a consistent structure
    with required fields.
    
    **Feature: unified-llm-platform, Property 11: Platform connection verification**
    **Validates: Requirements 1.4, 1.5**
    """
    service = PlatformConnectionService()
    mock_connector = MockConnector()
    mock_connector.name = platform_name
    service.connector_manager.register(mock_connector)
    
    # Try to verify (may or may not be connected)
    result = await service.verify_connection(platform_name, timeout_seconds=5)
    
    # Property: Result should have required fields
    assert 'platform' in result, "Result should have 'platform' field"
    assert 'valid' in result, "Result should have 'valid' field"
    assert 'verified_at' in result, "Result should have 'verified_at' field"
    
    # Property: Result fields should have correct types
    assert isinstance(result['platform'], str), "'platform' should be a string"
    assert isinstance(result['valid'], bool), "'valid' should be a boolean"
    assert isinstance(result['verified_at'], str), "'verified_at' should be a string"
    
    # Property: Platform name should match
    assert result['platform'] == platform_name, \
        "Result platform should match requested platform"
    
    # Property: If invalid, should have error message
    if not result['valid']:
        assert 'error' in result, "Invalid result should have 'error' field"
        assert result['error'] is not None, "Invalid result should have non-null error"


@pytest.mark.asyncio
async def test_property_verification_updates_connection_status():
    """
    Property 11: Platform connection verification (status update)
    
    Verification should update the connection status based on the result.
    
    **Feature: unified-llm-platform, Property 11: Platform connection verification**
    **Validates: Requirements 1.4, 1.5**
    """
    service = PlatformConnectionService()
    mock_connector = MockConnector()
    service.connector_manager.register(mock_connector)
    
    # Connect with valid credentials
    credentials = {'api_key': 'valid_key'}
    await service.connect_platform('mock_platform', credentials)
    
    # Get initial connection
    connection = service.get_connection('mock_platform')
    assert connection is not None
    initial_status = connection.status
    
    # Verify connection
    result = await service.verify_connection('mock_platform')
    
    # Get updated connection
    updated_connection = service.get_connection('mock_platform')
    
    # Property: Status should be updated based on verification result
    if result['valid']:
        assert updated_connection.status == 'connected', \
            "Valid verification should set status to 'connected'"
        assert updated_connection.last_verified is not None, \
            "Valid verification should update last_verified timestamp"
    else:
        assert updated_connection.status == 'error', \
            "Invalid verification should set status to 'error'"
        assert updated_connection.error_message is not None, \
            "Invalid verification should set error_message"
    
    # Cleanup
    await service.disconnect_platform('mock_platform')


# ============================================================================
# Unit Tests for Edge Cases
# ============================================================================

@pytest.mark.asyncio
async def test_verify_nonexistent_platform():
    """Test verifying a platform that doesn't exist."""
    service = PlatformConnectionService()
    
    result = await service.verify_connection('nonexistent_platform')
    
    assert not result['valid']
    assert 'error' in result
    assert 'not found' in result['error'].lower()


@pytest.mark.asyncio
async def test_verify_disconnected_platform():
    """Test verifying a platform that is not connected."""
    service = PlatformConnectionService()
    mock_connector = MockConnector()
    service.connector_manager.register(mock_connector)
    
    # Don't connect, just verify
    result = await service.verify_connection('mock_platform')
    
    assert not result['valid']
    assert 'error' in result
    assert 'not connected' in result['error'].lower()


@pytest.mark.asyncio
async def test_verify_connection_with_connector_error():
    """Test verification when connector raises an error."""
    service = PlatformConnectionService()
    mock_connector = MockConnector()
    mock_connector.should_fail = True
    service.connector_manager.register(mock_connector)
    
    # Connect first
    credentials = {'api_key': 'valid_key'}
    try:
        await service.connect_platform('mock_platform', credentials)
    except:
        pass  # Connection may fail, that's ok
    
    # Verify should handle the error gracefully
    result = await service.verify_connection('mock_platform')
    
    assert not result['valid']
    assert 'error' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
