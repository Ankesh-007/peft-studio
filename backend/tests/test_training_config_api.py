"""
Integration tests for Training Configuration API
Tests the /api/config/validate-training endpoint
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture(scope="module", autouse=True)
def disable_rate_limiting():
    """Disable rate limiting for integration tests"""
    from services.security_service import get_security_service
    security_service = get_security_service()
    security_service.rate_limiter.enabled = False
    yield
    security_service.rate_limiter.enabled = True


client = TestClient(app)


def test_validate_complete_configuration():
    """Test validation of a complete training configuration"""
    request_data = {
        "provider": "local",
        "algorithm": "lora",
        "quantization": "none",
        "experiment_tracker": "none",
        "model_name": "test-model",
        "model_path": "/path/to/model",
        "dataset_id": "test-dataset",
        "dataset_path": "/path/to/dataset",
        "lora_r": 8,
        "lora_alpha": 16,
        "lora_dropout": 0.1,
        "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj"],
        "learning_rate": 2e-4,
        "batch_size": 4,
        "gradient_accumulation_steps": 4,
        "num_epochs": 3,
    }
    
    response = client.post("/api/config/validate-training", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert len(data["errors"]) == 0


def test_validate_missing_model():
    """Test validation with missing model information"""
    request_data = {
        "provider": "local",
        "algorithm": "lora",
        "model_name": "",  # Missing
        "model_path": "",  # Missing
        "dataset_id": "test-dataset",
        "dataset_path": "/path/to/dataset",
    }
    
    response = client.post("/api/config/validate-training", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is False
    assert any("model" in error.lower() for error in data["errors"])


def test_validate_dora_with_quantization():
    """Test validation of incompatible DoRA + quantization"""
    request_data = {
        "provider": "local",
        "algorithm": "dora",
        "quantization": "int4",  # Incompatible with DoRA
        "model_name": "test-model",
        "model_path": "/path/to/model",
        "dataset_id": "test-dataset",
        "dataset_path": "/path/to/dataset",
    }
    
    response = client.post("/api/config/validate-training", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is False
    assert any("dora" in error.lower() and "quantization" in error.lower() for error in data["errors"])


def test_validate_tracker_without_project_name():
    """Test validation of experiment tracker without project name"""
    request_data = {
        "provider": "local",
        "algorithm": "lora",
        "experiment_tracker": "wandb",
        "project_name": None,  # Missing
        "model_name": "test-model",
        "model_path": "/path/to/model",
        "dataset_id": "test-dataset",
        "dataset_path": "/path/to/dataset",
    }
    
    response = client.post("/api/config/validate-training", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is False
    assert any("project" in error.lower() for error in data["errors"])


def test_validate_invalid_hyperparameters():
    """Test validation with invalid hyperparameters"""
    request_data = {
        "provider": "local",
        "algorithm": "lora",
        "model_name": "test-model",
        "model_path": "/path/to/model",
        "dataset_id": "test-dataset",
        "dataset_path": "/path/to/dataset",
        "learning_rate": -0.001,  # Invalid (negative)
        "batch_size": 0,  # Invalid (zero)
    }
    
    response = client.post("/api/config/validate-training", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is False
    assert len(data["errors"]) > 0


def test_validate_invalid_enum_value():
    """Test validation with invalid enum value"""
    request_data = {
        "provider": "invalid_provider",  # Invalid
        "algorithm": "lora",
        "model_name": "test-model",
        "model_path": "/path/to/model",
        "dataset_id": "test-dataset",
        "dataset_path": "/path/to/dataset",
    }
    
    response = client.post("/api/config/validate-training", json=request_data)
    
    assert response.status_code == 400  # Bad request for invalid enum


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
