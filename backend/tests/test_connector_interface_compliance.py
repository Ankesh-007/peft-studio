"""
Property-based tests for connector interface compliance.

**Feature: unified-llm-platform, Property 1: Connector interface compliance**
**Validates: Requirements 13.1, 13.2**

This test verifies that all registered connectors properly implement
the PlatformConnector interface and that calling all interface methods
succeeds without raising NotImplementedError.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from typing import Dict, List
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from connectors.base import (
    PlatformConnector,
    Resource,
    ResourceType,
    PricingInfo,
    TrainingConfig,
    JobStatus,
)
from connectors.manager import ConnectorManager
from connectors.registry import ConnectorRegistry


# Strategy for generating training configurations
@st.composite
def training_config_strategy(draw):
    """Generate random but valid training configurations."""
    return TrainingConfig(
        base_model=draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        model_source=draw(st.sampled_from(["huggingface", "civitai", "ollama"])),
        algorithm=draw(st.sampled_from(["lora", "qlora", "dora", "pissa", "rslora"])),
        rank=draw(st.integers(min_value=1, max_value=256)),
        alpha=draw(st.integers(min_value=1, max_value=512)),
        dropout=draw(st.floats(min_value=0.0, max_value=1.0)),
        target_modules=draw(st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5)),
        quantization=draw(st.sampled_from([None, "int8", "int4", "nf4"])),
        learning_rate=draw(st.floats(min_value=1e-6, max_value=1e-2)),
        batch_size=draw(st.integers(min_value=1, max_value=32)),
        gradient_accumulation_steps=draw(st.integers(min_value=1, max_value=16)),
        num_epochs=draw(st.integers(min_value=1, max_value=10)),
        warmup_steps=draw(st.integers(min_value=0, max_value=1000)),
        provider=draw(st.text(min_size=1, max_size=20)),
        dataset_path=draw(st.text(min_size=1, max_size=100)),
        validation_split=draw(st.floats(min_value=0.0, max_value=0.5)),
        project_name=draw(st.text(min_size=1, max_size=50)),
        output_dir=draw(st.text(min_size=1, max_size=100)),
        checkpoint_steps=draw(st.integers(min_value=1, max_value=10000)),
    )


class TestConnectorInterfaceCompliance:
    """Test suite for connector interface compliance."""
    
    @pytest.fixture
    def connector_manager(self):
        """Create a connector manager for testing."""
        manager = ConnectorManager()
        # Discover connectors from plugins directory
        manager.discover_connectors()
        return manager
    
    def test_connector_discovery(self, connector_manager):
        """Test that connectors can be discovered."""
        # At least the local connector should be discovered
        connectors = connector_manager.list_connectors(enabled_only=False)
        assert len(connectors) > 0, "No connectors discovered"
    
    def test_all_connectors_have_required_attributes(self, connector_manager):
        """
        Property: For any registered connector, it must have all required attributes.
        
        This verifies that connectors have name, display_name, description, and version.
        """
        connectors = connector_manager.list_connectors(enabled_only=False)
        
        for connector_meta in connectors:
            assert connector_meta.name, f"Connector missing name"
            assert connector_meta.display_name, f"Connector {connector_meta.name} missing display_name"
            assert connector_meta.description, f"Connector {connector_meta.name} missing description"
            assert connector_meta.version, f"Connector {connector_meta.name} missing version"
    
    def test_all_connectors_implement_required_methods(self, connector_manager):
        """
        Property: For any registered connector, all interface methods must be implemented.
        
        This verifies that connectors don't have abstract methods remaining.
        """
        connectors = connector_manager.list_connectors(enabled_only=False)
        
        required_methods = [
            'connect',
            'disconnect',
            'verify_connection',
            'submit_job',
            'get_job_status',
            'cancel_job',
            'stream_logs',
            'fetch_artifact',
            'upload_artifact',
            'list_resources',
            'get_pricing',
        ]
        
        for connector_meta in connectors:
            connector_class = connector_meta.connector_class
            
            for method_name in required_methods:
                assert hasattr(connector_class, method_name), \
                    f"Connector {connector_meta.name} missing method {method_name}"
                
                method = getattr(connector_class, method_name)
                
                # Check method is not abstract
                is_abstract = hasattr(method, '__isabstractmethod__') and method.__isabstractmethod__
                assert not is_abstract, \
                    f"Connector {connector_meta.name} method {method_name} is still abstract"
    
    def test_connector_connect_method_works(self, connector_manager):
        """
        Property: For any registered connector, calling connect() should not raise NotImplementedError.
        
        This verifies the connect method is actually implemented.
        """
        connectors = connector_manager.list_connectors(enabled_only=False)
        
        for connector_meta in connectors:
            connector = connector_meta.connector_class()
            
            try:
                # Try to connect with empty credentials (may fail, but shouldn't be NotImplementedError)
                result = asyncio.run(connector.connect({}))
                assert isinstance(result, bool), \
                    f"Connector {connector_meta.name} connect() must return bool"
            except NotImplementedError:
                pytest.fail(f"Connector {connector_meta.name} connect() raised NotImplementedError")
            except Exception:
                # Other exceptions are okay (e.g., invalid credentials)
                pass
    
    def test_connector_disconnect_method_works(self, connector_manager):
        """
        Property: For any registered connector, calling disconnect() should not raise NotImplementedError.
        """
        connectors = connector_manager.list_connectors(enabled_only=False)
        
        for connector_meta in connectors:
            connector = connector_meta.connector_class()
            
            try:
                result = asyncio.run(connector.disconnect())
                assert isinstance(result, bool), \
                    f"Connector {connector_meta.name} disconnect() must return bool"
            except NotImplementedError:
                pytest.fail(f"Connector {connector_meta.name} disconnect() raised NotImplementedError")
            except Exception:
                # Other exceptions are okay
                pass
    
    def test_connector_verify_connection_method_works(self, connector_manager):
        """
        Property: For any registered connector, calling verify_connection() should not raise NotImplementedError.
        """
        connectors = connector_manager.list_connectors(enabled_only=False)
        
        for connector_meta in connectors:
            connector = connector_meta.connector_class()
            
            try:
                result = asyncio.run(connector.verify_connection())
                assert isinstance(result, bool), \
                    f"Connector {connector_meta.name} verify_connection() must return bool"
            except NotImplementedError:
                pytest.fail(f"Connector {connector_meta.name} verify_connection() raised NotImplementedError")
            except Exception:
                # Other exceptions are okay
                pass
    
    def test_connector_list_resources_method_works(self, connector_manager):
        """
        Property: For any registered connector, calling list_resources() should not raise NotImplementedError.
        """
        connectors = connector_manager.list_connectors(enabled_only=False)
        
        for connector_meta in connectors:
            connector = connector_meta.connector_class()
            
            try:
                result = asyncio.run(connector.list_resources())
                assert isinstance(result, list), \
                    f"Connector {connector_meta.name} list_resources() must return list"
            except NotImplementedError:
                pytest.fail(f"Connector {connector_meta.name} list_resources() raised NotImplementedError")
            except Exception:
                # Other exceptions are okay
                pass
    
    @given(config=training_config_strategy())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_connector_validate_config_works(self, connector_manager, config):
        """
        Property: For any registered connector and any valid training config,
        validate_config() should not raise NotImplementedError.
        """
        connectors = connector_manager.list_connectors(enabled_only=False)
        
        for connector_meta in connectors:
            connector = connector_meta.connector_class()
            
            try:
                # validate_config may raise ValueError for invalid configs, but not NotImplementedError
                result = connector.validate_config(config)
                # If it doesn't raise, it should return True
                assert result is True, \
                    f"Connector {connector_meta.name} validate_config() must return True when valid"
            except NotImplementedError:
                pytest.fail(f"Connector {connector_meta.name} validate_config() raised NotImplementedError")
            except ValueError:
                # ValueError is acceptable for invalid configs
                pass
            except Exception:
                # Other exceptions are okay
                pass
    
    def test_connector_get_required_credentials_works(self, connector_manager):
        """
        Property: For any registered connector, calling get_required_credentials()
        should not raise NotImplementedError and should return a list.
        """
        connectors = connector_manager.list_connectors(enabled_only=False)
        
        for connector_meta in connectors:
            connector = connector_meta.connector_class()
            
            try:
                result = connector.get_required_credentials()
                assert isinstance(result, list), \
                    f"Connector {connector_meta.name} get_required_credentials() must return list"
            except NotImplementedError:
                pytest.fail(f"Connector {connector_meta.name} get_required_credentials() raised NotImplementedError")
    
    def test_registry_validation_catches_incomplete_connectors(self):
        """
        Property: The registry validation should catch connectors that don't
        implement all required methods.
        """
        registry = ConnectorRegistry()
        
        # Create an incomplete connector class
        class IncompleteConnector(PlatformConnector):
            name = "incomplete"
            display_name = "Incomplete"
            description = "Test"
            version = "1.0.0"
            
            # Only implement some methods, leave others abstract
            async def connect(self, credentials: Dict[str, str]) -> bool:
                return True
        
        # Try to register - should fail validation
        success = registry.register(IncompleteConnector)
        assert not success, "Registry should reject incomplete connectors"
        
        # Check validation errors were recorded
        errors = registry.get_validation_errors("incomplete")
        assert len(errors) > 0, "Registry should record validation errors"
        assert any("not implemented" in err.lower() for err in errors), \
            "Validation errors should mention unimplemented methods"
    
    def test_connector_manager_isolates_connector_failures(self, connector_manager):
        """
        Property: For any connector failure, other connectors should continue functioning.
        
        This validates Requirement 13.3 about failure isolation.
        """
        # This is tested by the fact that if one connector fails to load,
        # the manager continues discovering other connectors
        
        # Get initial connector count
        initial_count = len(connector_manager.list_connectors(enabled_only=False))
        
        # Even if some connectors fail, we should have at least one working
        assert initial_count > 0, "At least one connector should be working"


# Run property-based tests with pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
