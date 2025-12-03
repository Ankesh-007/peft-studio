# Backend Test Organization

This directory contains all backend tests for PEFT Studio, organized by feature and service.

## Test Categories

### Service Tests
Tests for individual backend services:
- `test_*_service.py` - Service implementation tests
- `test_*_api.py` - API endpoint tests

### Connector Tests
Tests for platform connectors (11 connectors):
- `test_civitai_connector.py`
- `test_cometml_connector.py`
- `test_deepeval_connector.py`
- `test_honeyhive_connector.py`
- `test_huggingface_connector.py`
- `test_lambda_labs_connector.py`
- `test_modal_connector.py`
- `test_ollama_connector.py`
- `test_phoenix_connector.py`
- `test_predibase_connector.py`
- `test_replicate_connector.py`
- `test_runpod_connector.py`
- `test_together_ai_connector.py`
- `test_vastai_connector.py`
- `test_wandb_connector.py`

### Feature Tests
Tests grouped by feature area:

**Cost Calculation:**
- `test_cost_calculator.py`
- `test_cost_calculator_standalone.py`
- `test_cost_api.py`
- `test_cost_estimation_accuracy.py`

**Configuration Management:**
- `test_configuration_alternatives.py`
- `test_configuration_diff.py`
- `test_configuration_export_roundtrip.py`

**Error Handling:**
- `test_error_actions.py`
- `test_error_formatting.py`
- `test_error_help_links.py`
- `test_error_log_completeness.py`
- `test_error_notifications.py`

**Export System:**
- `test_export_verification.py`
- `test_huggingface_export.py`
- `test_ollama_export.py`

**Dataset Management:**
- `test_dataset_format_acceptance.py`
- `test_dataset_format_detection.py`
- `test_dataset_validation_suggestions.py`

**Pause/Resume:**
- `test_pause_checkpoint.py`
- `test_pause_resume_roundtrip.py`
- `test_paused_run_display.py`

### Integration Tests
End-to-end tests that verify complete workflows:
- `test_e2e_complete_workflow.py`
- `test_e2e_performance_validation.py`
- `test_e2e_platform_integration.py`
- `test_e2e_security_audit.py`

### Property-Based Tests
Tests that verify properties across many inputs:
- `test_credential_encryption_roundtrip.py`
- `test_preset_roundtrip.py`
- `test_resource_usage_limits.py`

## Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=backend --cov-report=html

# Run specific test file
pytest backend/tests/test_cost_calculator.py

# Run tests matching a pattern
pytest -k "cost"
pytest -k "connector"
pytest -k "e2e"

# Run tests with verbose output
pytest -v

# Run tests in parallel
pytest -n auto
```

## Test Configuration

Test configuration is managed in:
- `pytest.ini` - Pytest configuration
- `conftest.py` - Shared fixtures and test setup

## Test Structure

### Standard Test Structure

```python
import pytest
from backend.services.example_service import ExampleService

class TestExampleService:
    """Tests for ExampleService"""
    
    def test_basic_functionality(self):
        """Test basic service functionality"""
        service = ExampleService()
        result = service.do_something()
        assert result is not None
    
    def test_error_handling(self):
        """Test service error handling"""
        service = ExampleService()
        with pytest.raises(ValueError):
            service.do_invalid_operation()
```

### Property-Based Test Structure

```python
from hypothesis import given, strategies as st

class TestExampleProperties:
    """Property-based tests for Example"""
    
    @given(st.text())
    def test_property_holds_for_all_strings(self, input_string):
        """Test that property holds for any string input"""
        result = process_string(input_string)
        assert len(result) >= len(input_string)
```

## Fixtures

Common fixtures are defined in `conftest.py`:
- `db_session` - Database session for tests
- `test_client` - FastAPI test client
- `mock_connector` - Mock connector for testing

## Best Practices

1. **Test Isolation**: Each test should be independent and not rely on other tests
2. **Clear Naming**: Use descriptive test names that explain what is being tested
3. **Arrange-Act-Assert**: Structure tests with clear setup, execution, and verification
4. **Mock External Services**: Use mocks for external APIs and services
5. **Test Edge Cases**: Include tests for boundary conditions and error cases
6. **Property-Based Testing**: Use Hypothesis for testing properties across many inputs
7. **Performance Testing**: Include performance benchmarks for critical paths

## Test Coverage Goals

- **Service Layer**: 90%+ coverage
- **API Endpoints**: 95%+ coverage
- **Connectors**: 85%+ coverage
- **Critical Paths**: 100% coverage

## Continuous Integration

Tests are automatically run on:
- Every pull request
- Every commit to main branch
- Nightly builds

See `.github/workflows/test.yml` for CI configuration.

## Related Documentation

- [Testing Guide](../../docs/developer-guide/testing.md) - Comprehensive testing documentation
- [Contributing Guide](../../docs/CONTRIBUTING.md) - Guidelines for contributing tests
- [Resource Usage Limits Fix](../../docs/developer-guide/resource-usage-limits-fix.md) - Property test fix documentation
