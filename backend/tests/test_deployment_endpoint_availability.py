"""
Property-Based Test: Deployment Endpoint Availability

Property 14: Deployment endpoint availability
For any deployed adapter, the inference endpoint should respond to test requests within 10 seconds

Validates: Requirements 9.4, 9.5

Feature: unified-llm-platform, Property 14: Deployment endpoint availability
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime, timedelta
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import time

from services.deployment_service import (
    DeploymentService,
    DeploymentConfig,
    DeploymentStatus,
    EndpointInfo,
    Deployment
)


# Strategies for generating test data

@st.composite
def deployment_config_strategy(draw):
    """Generate valid deployment configurations"""
    deployment_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), blacklist_characters='-_')))
    deployment_id = f"deploy_{deployment_id}"
    
    name = draw(st.text(min_size=1, max_size=100))
    platform = draw(st.sampled_from(['predibase', 'together_ai', 'modal', 'replicate']))
    model_path = draw(st.text(min_size=1, max_size=200))
    
    return DeploymentConfig(
        deployment_id=deployment_id,
        name=name,
        platform=platform,
        model_path=model_path,
        base_model=draw(st.one_of(st.none(), st.text(min_size=1, max_size=100))),
        min_instances=draw(st.integers(min_value=1, max_value=5)),
        max_instances=draw(st.integers(min_value=5, max_value=20)),
        auto_scaling=draw(st.booleans()),
        max_batch_size=draw(st.integers(min_value=1, max_value=32)),
        timeout_seconds=draw(st.integers(min_value=10, max_value=300))
    )


@st.composite
def endpoint_test_input_strategy(draw):
    """Generate test input data for endpoints"""
    return {
        'prompt': draw(st.text(min_size=1, max_size=500)),
        'max_tokens': draw(st.integers(min_value=1, max_value=2048)),
        'temperature': draw(st.floats(min_value=0.0, max_value=2.0)),
        'top_p': draw(st.floats(min_value=0.0, max_value=1.0))
    }


class TestDeploymentEndpointAvailability:
    """
    Property-Based Tests for Deployment Endpoint Availability
    
    Property 14: For any deployed adapter, the inference endpoint should respond 
    to test requests within 10 seconds
    
    Validates: Requirements 9.4, 9.5
    """
    
    @pytest.fixture
    def service(self, mock_connector):
        """Create deployment service instance with mocked connector"""
        with patch('services.deployment_service.get_connector_manager') as mock_manager:
            mock_manager_instance = MagicMock()
            mock_manager_instance.get.return_value = mock_connector
            mock_manager.return_value = mock_manager_instance
            
            # Patch at module level
            with patch('services.deployment_service.get_connector_manager', return_value=mock_manager_instance):
                service = DeploymentService()
                yield service
    
    @pytest.fixture
    def mock_connector(self):
        """Create mock connector for testing"""
        connector = AsyncMock()
        connector.name = "test_platform"
        connector.supports_inference = True
        
        # Mock deployment methods
        connector.deploy_model = AsyncMock(return_value="platform_deploy_123")
        connector.get_endpoint_url = AsyncMock(return_value="https://api.test.com/v1/inference")
        connector.invoke_endpoint = AsyncMock(return_value={
            'output': 'test response',
            'tokens': 10
        })
        connector.stop_deployment = AsyncMock(return_value=True)
        connector.get_deployment_metrics = AsyncMock(return_value={
            'total_requests': 100,
            'successful_requests': 95,
            'failed_requests': 5,
            'avg_latency_ms': 150.0,
            'p50_latency_ms': 120.0,
            'p95_latency_ms': 300.0,
            'p99_latency_ms': 500.0,
            'total_input_tokens': 5000,
            'total_output_tokens': 3000,
            'estimated_cost': 2.50,
            'period_start': datetime.now().isoformat(),
            'period_end': datetime.now().isoformat()
        })
        
        return connector
    
    @given(
        config=deployment_config_strategy(),
        test_input=endpoint_test_input_strategy()
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_endpoint_responds_within_timeout(self, service, config, test_input):
        """
        Property: For any deployed adapter, the endpoint should respond within 10 seconds
        
        This tests that:
        1. Deployed endpoints are accessible
        2. Test requests complete within the timeout
        3. Response time is tracked
        
        Validates: Requirements 9.4, 9.5
        """
        async def run_test():
            # Create deployment
            deployment = await service.create_deployment(config)
            assert deployment.deployment_id == config.deployment_id
            assert deployment.status == DeploymentStatus.PENDING
            
            # Deploy to platform
            deployment = await service.deploy_to_platform(config.deployment_id)
            assert deployment.status == DeploymentStatus.ACTIVE
            assert deployment.endpoint is not None
            assert deployment.endpoint.url is not None
            
            # Test endpoint with timeout
            start_time = time.time()
            result = await service.test_endpoint(config.deployment_id, test_input)
            end_time = time.time()
            
            elapsed_seconds = end_time - start_time
            
            # Property: Response time should be within 10 seconds
            assert elapsed_seconds < 10.0, \
                f"Endpoint response took {elapsed_seconds:.2f}s, exceeds 10s limit"
            
            # Property: Test should succeed
            assert result['success'] is True, \
                f"Endpoint test failed: {result.get('error')}"
            
            # Property: Response should contain expected data
            assert 'response' in result
            assert 'latency_ms' in result
            assert 'timestamp' in result
            
            # Property: Latency should be reasonable (< 10000ms)
            assert result['latency_ms'] < 10000, \
                f"Latency {result['latency_ms']}ms exceeds 10s limit"
            
            # Property: Endpoint info should be updated
            assert deployment.endpoint.last_health_check is not None
            assert deployment.endpoint.avg_latency_ms > 0
        
        # Run async test
        asyncio.run(run_test())
    
    @given(config=deployment_config_strategy())
    @settings(
        max_examples=30,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_endpoint_availability_after_deployment(self, service, config):
        """
        Property: Deployed endpoints should be immediately available after deployment
        
        This tests that:
        1. Endpoint URL is provided after deployment
        2. Endpoint is accessible
        3. Health check can be performed
        
        Validates: Requirements 9.4
        """
        async def run_test():
            # Create and deploy
            deployment = await service.create_deployment(config)
            deployment = await service.deploy_to_platform(config.deployment_id)
            
            # Property: Endpoint should exist
            assert deployment.endpoint is not None, \
                "Deployed model should have an endpoint"
            
            # Property: Endpoint should have a URL
            assert deployment.endpoint.url is not None, \
                "Endpoint should have a URL"
            assert len(deployment.endpoint.url) > 0, \
                "Endpoint URL should not be empty"
            
            # Property: Endpoint should be marked as active
            assert deployment.endpoint.status == "active", \
                f"Endpoint status should be 'active', got '{deployment.endpoint.status}'"
            
            # Property: Endpoint should be testable immediately
            test_input = {'prompt': 'test', 'max_tokens': 10}
            result = await service.test_endpoint(config.deployment_id, test_input)
            
            assert result['success'] is True, \
                "Endpoint should be testable immediately after deployment"
        
        asyncio.run(run_test())
    
    @given(
        config=deployment_config_strategy(),
        num_requests=st.integers(min_value=1, max_value=10)
    )
    @settings(
        max_examples=20,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_endpoint_handles_multiple_requests(self, service, mock_connector, config, num_requests):
        """
        Property: Endpoints should handle multiple sequential requests reliably
        
        This tests that:
        1. Multiple requests can be made to the same endpoint
        2. Each request completes within timeout
        3. Metrics are tracked across requests
        
        Validates: Requirements 9.4, 9.5
        """
        async def run_test():
            with patch('services.deployment_service.get_connector_manager') as mock_manager:
                mock_manager_instance = MagicMock()
                mock_manager_instance.get.return_value = mock_connector
                mock_manager.return_value = mock_manager_instance
                
                # Create and deploy
                deployment = await service.create_deployment(config)
                deployment = await service.deploy_to_platform(config.deployment_id)
                
                # Make multiple requests
                latencies = []
                for i in range(num_requests):
                    test_input = {
                        'prompt': f'test request {i}',
                        'max_tokens': 10
                    }
                    
                    start_time = time.time()
                    result = await service.test_endpoint(config.deployment_id, test_input)
                    elapsed = time.time() - start_time
                    
                    # Property: Each request should succeed
                    assert result['success'] is True, \
                        f"Request {i+1}/{num_requests} failed"
                    
                    # Property: Each request should complete within timeout
                    assert elapsed < 10.0, \
                        f"Request {i+1}/{num_requests} took {elapsed:.2f}s, exceeds 10s"
                    
                    latencies.append(result['latency_ms'])
                
                # Property: All latencies should be reasonable
                assert all(lat < 10000 for lat in latencies), \
                    f"Some latencies exceed 10s limit: {latencies}"
                
                # Property: Endpoint metrics should reflect requests
                deployment = service.get_deployment(config.deployment_id)
                assert deployment.endpoint.last_health_check is not None
        
        asyncio.run(run_test())
    
    @given(config=deployment_config_strategy())
    @settings(
        max_examples=20,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_stopped_endpoint_not_available(self, service, mock_connector, config):
        """
        Property: Stopped deployments should not have available endpoints
        
        This tests that:
        1. Endpoints can be stopped
        2. Stopped endpoints are marked as unavailable
        3. Test requests to stopped endpoints fail appropriately
        
        Validates: Requirements 9.4
        """
        async def run_test():
            with patch('services.deployment_service.get_connector_manager') as mock_manager:
                mock_manager_instance = MagicMock()
                mock_manager_instance.get.return_value = mock_connector
                mock_manager.return_value = mock_manager_instance
                
                # Create, deploy, and stop
                deployment = await service.create_deployment(config)
                deployment = await service.deploy_to_platform(config.deployment_id)
                
                # Verify endpoint is active
                assert deployment.endpoint.status == "active"
                
                # Stop deployment
                success = await service.stop_deployment(config.deployment_id)
                assert success is True
                
                # Property: Deployment should be stopped
                deployment = service.get_deployment(config.deployment_id)
                assert deployment.status == DeploymentStatus.STOPPED
                
                # Property: Endpoint should be marked as stopped
                assert deployment.endpoint.status == "stopped"
                
                # Property: Test requests should fail
                with pytest.raises(ValueError, match="Cannot test deployment in status"):
                    await service.test_endpoint(config.deployment_id, {'prompt': 'test'})
        
        asyncio.run(run_test())
    
    @given(config=deployment_config_strategy())
    @settings(
        max_examples=20,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_usage_metrics_available(self, service, mock_connector, config):
        """
        Property: Usage metrics should be available for active deployments
        
        This tests that:
        1. Metrics can be retrieved for active deployments
        2. Metrics contain expected fields
        3. Metrics are updated after requests
        
        Validates: Requirements 9.5
        """
        async def run_test():
            with patch('services.deployment_service.get_connector_manager') as mock_manager:
                mock_manager_instance = MagicMock()
                mock_manager_instance.get.return_value = mock_connector
                mock_manager.return_value = mock_manager_instance
                
                # Create and deploy
                deployment = await service.create_deployment(config)
                deployment = await service.deploy_to_platform(config.deployment_id)
                
                # Get usage metrics
                metrics = await service.get_usage_metrics(config.deployment_id)
                
                # Property: Metrics should exist
                assert metrics is not None
                
                # Property: Metrics should have required fields
                assert hasattr(metrics, 'deployment_id')
                assert hasattr(metrics, 'total_requests')
                assert hasattr(metrics, 'successful_requests')
                assert hasattr(metrics, 'failed_requests')
                assert hasattr(metrics, 'avg_latency_ms')
                assert hasattr(metrics, 'estimated_cost')
                
                # Property: Metrics should be non-negative
                assert metrics.total_requests >= 0
                assert metrics.successful_requests >= 0
                assert metrics.failed_requests >= 0
                assert metrics.avg_latency_ms >= 0
                assert metrics.estimated_cost >= 0
                
                # Property: Successful + failed should equal total
                assert metrics.successful_requests + metrics.failed_requests == metrics.total_requests
        
        asyncio.run(run_test())


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
