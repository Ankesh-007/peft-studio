"""
Shared pytest fixtures for backend tests.

This module provides common fixtures for:
- Database connection mocking
- FastAPI test client
- Common test data
- External API mocking (Hugging Face, WandB, etc.)

Validates: Requirements 6.2, 6.3, 6.4, 6.5
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from typing import Dict, Any, List

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Import FastAPI test client
from fastapi.testclient import TestClient


# ============================================================================
# Database Fixtures (Requirement 6.4)
# ============================================================================

@pytest.fixture
def mock_db_session():
    """
    Mock database session for testing without actual database connections.
    
    Validates: Requirement 6.4 - Database connections shall be mocked appropriately
    """
    session = MagicMock()
    session.query = MagicMock()
    session.add = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.close = MagicMock()
    session.flush = MagicMock()
    session.refresh = MagicMock()
    return session


@pytest.fixture
def mock_db_engine():
    """Mock database engine for testing."""
    engine = MagicMock()
    engine.connect = MagicMock()
    engine.dispose = MagicMock()
    return engine


@pytest.fixture
def mock_get_db(mock_db_session):
    """
    Mock the get_db dependency for FastAPI endpoints.
    
    Validates: Requirement 6.4 - Database connections shall be mocked appropriately
    """
    def _get_db():
        try:
            yield mock_db_session
        finally:
            pass
    return _get_db


# ============================================================================
# FastAPI Test Client Fixtures (Requirement 6.3)
# ============================================================================

@pytest.fixture
def test_client():
    """
    FastAPI test client for integration testing.
    
    Validates: Requirement 6.3 - Test fixtures shall be properly configured
    """
    from main import app
    return TestClient(app)


@pytest.fixture
def authenticated_client(test_client):
    """Test client with authentication headers (if needed in future)."""
    # For now, return regular client
    # Can be extended with auth tokens when authentication is implemented
    return test_client


# ============================================================================
# Common Test Data Fixtures (Requirement 6.3)
# ============================================================================

@pytest.fixture
def sample_hardware_profile():
    """
    Sample hardware profile data for testing.
    
    Validates: Requirement 6.3 - Test fixtures shall be properly configured
    """
    return {
        "gpus": [
            {
                "id": 0,
                "name": "NVIDIA RTX 4090",
                "memory_total": 24 * 1024**3,  # 24 GB
                "memory_available": 20 * 1024**3,  # 20 GB
                "memory_used": 4 * 1024**3,  # 4 GB
                "compute_capability": "8.9",
                "cuda_version": "12.1",
                "temperature": 65.0,
                "utilization": 45.0
            }
        ],
        "cpu": {
            "cores_physical": 16,
            "cores_logical": 32,
            "frequency_mhz": 3800.0,
            "architecture": "x86_64",
            "utilization": 25.0
        },
        "ram": {
            "total": 64 * 1024**3,  # 64 GB
            "available": 48 * 1024**3,  # 48 GB
            "used": 16 * 1024**3,  # 16 GB
            "percent_used": 25.0
        },
        "platform": "Linux",
        "python_version": "3.10.12",
        "torch_version": "2.1.0",
        "cuda_available": True,
        "timestamp": datetime.now().isoformat()
    }


@pytest.fixture
def sample_model_info():
    """Sample model information for testing."""
    return {
        "model_id": "meta-llama/Llama-2-7b-hf",
        "author": "meta-llama",
        "model_name": "Llama-2-7b-hf",
        "downloads": 1000000,
        "likes": 5000,
        "tags": ["text-generation", "llama", "pytorch"],
        "pipeline_tag": "text-generation",
        "library_name": "transformers",
        "size_mb": 13000,
        "parameters": 7000000000,
        "architecture": "LlamaForCausalLM",
        "license": "llama2"
    }


@pytest.fixture
def sample_training_config():
    """Sample training configuration for testing."""
    return {
        "model_name": "meta-llama/Llama-2-7b-hf",
        "dataset_name": "alpaca",
        "batch_size": 4,
        "gradient_accumulation_steps": 4,
        "learning_rate": 2e-4,
        "num_epochs": 3,
        "max_steps": 1000,
        "lora_r": 16,
        "lora_alpha": 32,
        "lora_dropout": 0.05,
        "target_modules": ["q_proj", "v_proj"],
        "precision": "fp16",
        "quantization": "4bit"
    }


@pytest.fixture
def sample_training_metrics():
    """Sample training metrics for testing."""
    return {
        "step": 100,
        "epoch": 1,
        "loss": 1.234,
        "learning_rate": 2e-4,
        "throughput": 150.5,
        "samples_per_second": 12.5,
        "grad_norm": 0.85,
        "val_loss": 1.156,
        "val_perplexity": 3.18
    }


@pytest.fixture
def sample_dataset_info():
    """Sample dataset information for testing."""
    return {
        "name": "alpaca",
        "path": "/data/alpaca",
        "format": "json",
        "num_examples": 52000,
        "size_mb": 250,
        "validation_status": "valid",
        "metadata": {
            "avg_sequence_length": 256,
            "max_sequence_length": 512,
            "columns": ["instruction", "input", "output"]
        }
    }


@pytest.fixture
def sample_job_id():
    """Sample job ID for testing."""
    return "test_job_12345"


# ============================================================================
# External API Mocking - Hugging Face (Requirement 6.5)
# ============================================================================

@pytest.fixture
def mock_huggingface_api():
    """
    Mock Hugging Face Hub API for testing.
    
    Validates: Requirement 6.5 - External API calls shall be mocked or stubbed
    """
    with patch('services.model_registry_service.HfApi') as mock_api:
        # Create mock instance
        mock_instance = MagicMock()
        mock_api.return_value = mock_instance
        
        # Mock model_info method
        mock_instance.model_info.return_value = MagicMock(
            modelId="meta-llama/Llama-2-7b-hf",
            author="meta-llama",
            downloads=1000000,
            likes=5000,
            tags=["text-generation", "llama"],
            pipeline_tag="text-generation",
            library_name="transformers",
            created_at=datetime(2023, 7, 18),
            last_modified=datetime(2023, 7, 18)
        )
        
        # Mock list_models method
        mock_instance.list_models.return_value = [
            MagicMock(
                modelId="meta-llama/Llama-2-7b-hf",
                author="meta-llama",
                downloads=1000000,
                likes=5000
            )
        ]
        
        yield mock_instance


@pytest.fixture
def mock_huggingface_list_models():
    """
    Mock huggingface_hub.list_models function.
    
    Validates: Requirement 6.5 - External API calls shall be mocked or stubbed
    """
    with patch('services.model_registry_service.list_models') as mock_list:
        mock_list.return_value = [
            MagicMock(
                modelId="meta-llama/Llama-2-7b-hf",
                author="meta-llama",
                downloads=1000000,
                likes=5000,
                tags=["text-generation"],
                pipeline_tag="text-generation",
                library_name="transformers"
            ),
            MagicMock(
                modelId="mistralai/Mistral-7B-v0.1",
                author="mistralai",
                downloads=500000,
                likes=3000,
                tags=["text-generation"],
                pipeline_tag="text-generation",
                library_name="transformers"
            )
        ]
        yield mock_list


# ============================================================================
# External API Mocking - WandB (Requirement 6.5)
# ============================================================================

@pytest.fixture
def mock_wandb():
    """
    Mock Weights & Biases (WandB) API for testing.
    
    Validates: Requirement 6.5 - External API calls shall be mocked or stubbed
    """
    with patch('services.wandb_integration_service.WANDB_AVAILABLE', True):
        with patch('services.wandb_integration_service.wandb', create=True) as mock_wandb_module:
            # Create mock run
            mock_run = MagicMock()
            mock_run.id = "test_run_123"
            mock_run.name = "test_run"
            mock_run.url = "https://wandb.ai/test/test-project/runs/test_run_123"
            mock_run.summary = MagicMock()
            mock_run.config = {}
            mock_run.log = MagicMock()
            mock_run.finish = MagicMock()
            
            # Mock wandb.init to return the mock run
            mock_wandb_module.init.return_value = mock_run
            mock_wandb_module.run = mock_run
            
            yield mock_wandb_module


@pytest.fixture
def mock_wandb_disabled():
    """Mock WandB as unavailable for testing disabled state."""
    with patch('services.wandb_integration_service.WANDB_AVAILABLE', False):
        yield


# ============================================================================
# External API Mocking - PyTorch/CUDA (Requirement 6.5)
# ============================================================================

@pytest.fixture
def mock_torch_cuda():
    """
    Mock PyTorch CUDA functionality for testing without GPU.
    
    Validates: Requirement 6.5 - External API calls shall be mocked or stubbed
    """
    with patch('torch.cuda.is_available') as mock_is_available:
        with patch('torch.cuda.device_count') as mock_device_count:
            with patch('torch.cuda.get_device_properties') as mock_get_props:
                with patch('torch.cuda.mem_get_info') as mock_mem_info:
                    # Configure mocks
                    mock_is_available.return_value = True
                    mock_device_count.return_value = 1
                    
                    # Mock device properties
                    mock_props = MagicMock()
                    mock_props.name = "NVIDIA RTX 4090"
                    mock_props.total_memory = 24 * 1024**3  # 24 GB
                    mock_props.major = 8
                    mock_props.minor = 9
                    mock_get_props.return_value = mock_props
                    
                    # Mock memory info (free, total)
                    mock_mem_info.return_value = (20 * 1024**3, 24 * 1024**3)
                    
                    yield {
                        'is_available': mock_is_available,
                        'device_count': mock_device_count,
                        'get_device_properties': mock_get_props,
                        'mem_get_info': mock_mem_info
                    }


@pytest.fixture
def mock_torch_no_cuda():
    """Mock PyTorch with CUDA unavailable."""
    with patch('torch.cuda.is_available', return_value=False):
        with patch('torch.cuda.device_count', return_value=0):
            yield


# ============================================================================
# Service Instance Fixtures
# ============================================================================

@pytest.fixture
def mock_hardware_service():
    """Mock hardware service for testing."""
    with patch('services.hardware_service.HardwareService') as mock_service:
        instance = MagicMock()
        mock_service.return_value = instance
        
        # Configure mock methods
        instance.get_hardware_profile.return_value = MagicMock(
            gpus=[],
            cpu=MagicMock(cores_physical=16, cores_logical=32),
            ram=MagicMock(total=64*1024**3, available=48*1024**3),
            cuda_available=False
        )
        
        yield instance


@pytest.fixture
def mock_model_registry_service():
    """Mock model registry service for testing."""
    with patch('services.model_registry_service.ModelRegistryService') as mock_service:
        instance = MagicMock()
        mock_service.return_value = instance
        
        # Configure mock methods
        instance.search_models.return_value = []
        instance.get_model_info.return_value = None
        instance.get_popular_models.return_value = []
        
        yield instance


@pytest.fixture
def mock_peft_service():
    """Mock PEFT service for testing."""
    with patch('services.peft_service.PEFTService') as mock_service:
        instance = MagicMock()
        mock_service.return_value = instance
        
        # Configure mock methods
        instance.load_model_with_unsloth.return_value = MagicMock(
            model_name="test-model",
            max_seq_length=2048,
            supports_gradient_checkpointing=True,
            memory_footprint_mb=5000
        )
        instance.list_loaded_models.return_value = []
        
        yield instance


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "pbt: mark test as property-based test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_gpu: mark test as requiring GPU"
    )
    config.addinivalue_line(
        "markers", "requires_internet: mark test as requiring internet connection"
    )


@pytest.fixture(autouse=True)
def reset_singletons():
    """
    Reset singleton instances between tests to ensure test isolation.
    
    Validates: Requirement 6.2 - pytest shall execute without import errors
    """
    # This fixture runs automatically before each test
    # Add any singleton reset logic here if needed
    yield
    # Cleanup after test
    pass


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory for test data."""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def temp_model_dir(tmp_path):
    """Create a temporary directory for test models."""
    model_dir = tmp_path / "test_models"
    model_dir.mkdir()
    return model_dir


@pytest.fixture
def temp_checkpoint_dir(tmp_path):
    """Create a temporary directory for test checkpoints."""
    checkpoint_dir = tmp_path / "test_checkpoints"
    checkpoint_dir.mkdir()
    return checkpoint_dir


# ============================================================================
# Async Test Support
# ============================================================================

@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Mock Environment Variables
# ============================================================================

@pytest.fixture
def mock_env_vars(monkeypatch):
    """
    Mock environment variables for testing.
    
    Validates: Requirement 6.5 - External API calls shall be mocked or stubbed
    """
    # Set test environment variables
    monkeypatch.setenv("WANDB_API_KEY", "test_wandb_key")
    monkeypatch.setenv("HF_TOKEN", "test_hf_token")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("ENVIRONMENT", "test")
    
    yield
    
    # Cleanup is automatic with monkeypatch


# ============================================================================
# Cost Calculator Fixtures
# ============================================================================

@pytest.fixture
def sample_cost_estimate_request():
    """Sample cost estimate request for testing."""
    return {
        "training_time_hours": 2.0,
        "gpu_name": "RTX 4090",
        "num_gpus": 1,
        "electricity_rate_per_kwh": 0.15,
        "region": "US",
        "utilization": 0.85
    }


@pytest.fixture
def sample_gpu_power_profile():
    """Sample GPU power profile for testing."""
    return {
        "model_name": "RTX 4090",
        "tdp_watts": 450,
        "avg_power_watts": 400,
        "idle_power_watts": 50
    }


# ============================================================================
# Comparison Service Fixtures
# ============================================================================

@pytest.fixture
def sample_comparison_runs():
    """Sample training runs for comparison testing."""
    return [
        {
            "job_id": "run_1",
            "config": {"learning_rate": 1e-4, "batch_size": 4},
            "metrics": {"final_loss": 0.5, "training_time": 3600}
        },
        {
            "job_id": "run_2",
            "config": {"learning_rate": 2e-4, "batch_size": 8},
            "metrics": {"final_loss": 0.45, "training_time": 1800}
        },
        {
            "job_id": "run_3",
            "config": {"learning_rate": 5e-5, "batch_size": 2},
            "metrics": {"final_loss": 0.55, "training_time": 7200}
        }
    ]


# ============================================================================
# Export Service Fixtures
# ============================================================================

@pytest.fixture
def mock_ollama_client():
    """Mock Ollama client for testing export functionality."""
    with patch('services.export_service.OllamaClient') as mock_client:
        instance = MagicMock()
        mock_client.return_value = instance
        
        instance.create_model.return_value = {"status": "success"}
        instance.list_models.return_value = []
        instance.delete_model.return_value = {"status": "success"}
        
        yield instance


@pytest.fixture
def mock_huggingface_upload():
    """Mock Hugging Face upload functionality."""
    with patch('services.export_service.upload_folder') as mock_upload:
        mock_upload.return_value = "https://huggingface.co/test/test-model"
        yield mock_upload
