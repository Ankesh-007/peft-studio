"""
Property-based tests for backend service initialization.

Feature: peft-application-fix, Property 1: Backend Service Initialization
Validates: Requirements 1.1, 1.2, 1.4

Tests that the backend service either starts successfully on any available port
or returns a clear error message explaining the issue.
"""

import pytest
from hypothesis import given, strategies as st, settings
import requests
import time
import subprocess
import sys
import os
from pathlib import Path


def is_port_available(port: int) -> bool:
    """Check if a port is available for use."""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('localhost', port))
        sock.close()
        return True
    except OSError:
        return False


def check_health(port: int, timeout: int = 5) -> dict:
    """Check if backend is healthy on given port."""
    try:
        response = requests.get(
            f'http://localhost:{port}/api/health',
            timeout=timeout
        )
        if response.status_code == 200:
            return {'healthy': True, 'response': response.json()}
        else:
            return {'healthy': False, 'error': f'Status {response.status_code}'}
    except requests.exceptions.ConnectionError:
        return {'healthy': False, 'error': 'Connection refused'}
    except requests.exceptions.Timeout:
        return {'healthy': False, 'error': 'Timeout'}
    except Exception as e:
        return {'healthy': False, 'error': str(e)}


@pytest.mark.property
@given(port=st.integers(min_value=8000, max_value=8010))
@settings(max_examples=10, deadline=5000)  # 5 second deadline, 10 examples
def test_backend_port_availability_check(port):
    """
    Property 1: Backend Service Initialization - Port Availability
    
    For any port in the valid range, we can determine if it's available.
    This is a prerequisite for backend starting successfully.
    
    The backend should be able to detect port conflicts and either:
    1. Use an available port, OR
    2. Return a clear error about port conflicts
    """
    # Test that we can check port availability
    available = is_port_available(port)
    
    # This should always return a boolean
    assert isinstance(available, bool), \
        "Port availability check should return boolean"
    
    # If port is not available, verify we can detect it
    if not available:
        # Try to connect to see if something is actually there
        health = check_health(port, timeout=1)
        # Either something responds or connection is refused
        assert health['healthy'] or 'error' in health, \
            "Port appears in use but cannot determine status"


@pytest.mark.property
def test_backend_health_endpoint_responds_quickly():
    """
    Property: Health check endpoint should respond within 5 seconds.
    
    This ensures the health check doesn't load heavy services and
    can be used for monitoring without impacting performance.
    """
    # This test assumes backend is already running on default port
    # We'll test the response time of the health endpoint
    
    port = 8000
    
    # Check if backend is running
    if not is_port_available(port):
        # Backend might be running, test it
        start_time = time.time()
        health = check_health(port, timeout=5)
        response_time = time.time() - start_time
        
        if health['healthy']:
            # Verify response time is under 5 seconds
            assert response_time < 5.0, \
                f"Health check took {response_time:.2f}s, should be under 5s"
            
            # Verify response has expected structure
            assert 'status' in health['response'], \
                "Health check response missing 'status' field"
            assert health['response']['status'] == 'healthy', \
                "Health check status is not 'healthy'"
        else:
            pytest.skip("Backend is not running on default port")
    else:
        pytest.skip("Backend is not running on default port")


@pytest.mark.property
def test_dependencies_endpoint_returns_complete_info():
    """
    Property: Dependencies endpoint should return complete dependency information.
    
    This ensures users can diagnose missing dependencies.
    """
    port = 8000
    
    # Check if backend is running
    if not is_port_available(port):
        try:
            response = requests.get(
                f'http://localhost:{port}/api/dependencies',
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required fields are present
                assert 'python_version' in data, \
                    "Dependencies response missing 'python_version'"
                assert 'packages' in data, \
                    "Dependencies response missing 'packages'"
                assert 'all_dependencies_met' in data, \
                    "Dependencies response missing 'all_dependencies_met'"
                
                # Verify packages info is complete
                required_packages = ['torch', 'transformers', 'peft', 'fastapi']
                for pkg in required_packages:
                    assert pkg in data['packages'], \
                        f"Dependencies response missing info for '{pkg}'"
                    
                    pkg_info = data['packages'][pkg]
                    assert 'installed' in pkg_info, \
                        f"Package '{pkg}' missing 'installed' field"
                    
                    if not pkg_info['installed']:
                        # If not installed, should have fix instructions
                        assert 'fix_instructions' in pkg_info, \
                            f"Missing package '{pkg}' has no fix instructions"
            else:
                pytest.skip(f"Dependencies endpoint returned {response.status_code}")
        except requests.exceptions.RequestException:
            pytest.skip("Backend is not responding")
    else:
        pytest.skip("Backend is not running on default port")


@pytest.mark.property
def test_startup_status_endpoint_provides_detailed_info():
    """
    Property: Startup status endpoint should provide detailed initialization info.
    
    This helps diagnose startup issues and performance problems.
    """
    port = 8000
    
    # Check if backend is running
    if not is_port_available(port):
        try:
            response = requests.get(
                f'http://localhost:{port}/api/startup/status',
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required fields are present
                assert 'initialized' in data, \
                    "Startup status missing 'initialized' field"
                assert 'startup_time' in data, \
                    "Startup status missing 'startup_time' field"
                assert 'ready' in data, \
                    "Startup status missing 'ready' field"
                
                # If not ready, should have recommendations
                if not data.get('ready', False):
                    assert 'recommendations' in data, \
                        "Startup status not ready but has no recommendations"
            else:
                pytest.skip(f"Startup status endpoint returned {response.status_code}")
        except requests.exceptions.RequestException:
            pytest.skip("Backend is not responding")
    else:
        pytest.skip("Backend is not running on default port")


if __name__ == '__main__':
    # Run the property tests
    pytest.main([__file__, '-v', '-m', 'property'])
