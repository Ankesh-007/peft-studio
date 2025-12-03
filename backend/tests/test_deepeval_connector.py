"""
Tests for DeepEval connector.

Tests the DeepEval connector's ability to:
- Connect to the platform
- Generate test cases
- Execute evaluations
- Calculate metrics
- Detect quality issues
- Compare evaluations
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from plugins.connectors.deepeval_connector import DeepEvalConnector
from connectors.base import TrainingConfig, JobStatus


@pytest.fixture
def connector():
    """Create a DeepEval connector instance."""
    return DeepEvalConnector()


@pytest.fixture
def mock_session():
    """Create a mock aiohttp session."""
    session = AsyncMock()
    return session


@pytest.fixture
def training_config():
    """Create a sample training configuration."""
    return TrainingConfig(
        base_model="meta-llama/Llama-2-7b-hf",
        model_source="huggingface",
        algorithm="lora",
        rank=16,
        alpha=32,
        dropout=0.1,
        target_modules=["q_proj", "v_proj"],
        dataset_path="./test_data.json",
        validation_split=0.1,
    )


@pytest.mark.asyncio
async def test_connector_metadata(connector):
    """Test connector metadata is correctly set."""
    assert connector.name == "deepeval"
    assert connector.display_name == "DeepEval"
    assert connector.supports_tracking is True
    assert connector.supports_training is False
    assert connector.supports_inference is False
    assert connector.supports_registry is False


@pytest.mark.asyncio
async def test_connect_success(connector, mock_session):
    """Test successful connection to DeepEval."""
    # Mock successful API response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "projects": [{"id": "test-project-123", "name": "Test Project"}]
    })
    
    mock_session.get = AsyncMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        result = await connector.connect({
            "api_key": "test-api-key",
            "project_id": "test-project-123"
        })
    
    assert result is True
    assert connector._connected is True
    assert connector._api_key == "test-api-key"
    assert connector._project_id == "test-project-123"


@pytest.mark.asyncio
async def test_connect_invalid_credentials(connector, mock_session):
    """Test connection with invalid credentials."""
    # Mock 401 response
    mock_response = AsyncMock()
    mock_response.status = 401
    
    mock_session.get = AsyncMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        with pytest.raises(ValueError, match="Invalid API key"):
            await connector.connect({"api_key": "invalid-key"})


@pytest.mark.asyncio
async def test_connect_missing_api_key(connector):
    """Test connection without API key."""
    with pytest.raises(ValueError, match="api_key is required"):
        await connector.connect({})


@pytest.mark.asyncio
async def test_submit_job(connector, mock_session, training_config):
    """Test creating an evaluation job."""
    # Setup connection
    connector._connected = True
    connector._api_key = "test-key"
    connector._project_id = "test-project"
    connector._session = mock_session
    
    # Mock successful job creation
    mock_response = AsyncMock()
    mock_response.status = 201
    mock_response.json = AsyncMock(return_value={
        "evaluation_id": "eval-123"
    })
    
    mock_session.post = AsyncMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    job_id = await connector.submit_job(training_config)
    
    assert job_id is not None
    assert job_id.startswith("eval_")
    assert job_id in connector._evaluations
    assert connector._evaluations[job_id]["status"] == JobStatus.PENDING


@pytest.mark.asyncio
async def test_submit_job_not_connected(connector, training_config):
    """Test submitting job when not connected."""
    with pytest.raises(RuntimeError, match="Not connected"):
        await connector.submit_job(training_config)


@pytest.mark.asyncio
async def test_generate_test_cases(connector, mock_session):
    """Test generating test cases from validation data."""
    # Setup
    connector._connected = True
    connector._session = mock_session
    connector._project_id = "test-project"
    
    job_id = "eval_test"
    connector._evaluations[job_id] = {
        "eval_id": "eval-123",
        "status": JobStatus.PENDING,
    }
    
    # Mock test case generation response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "test_cases": [
            {"input": "Test input 1", "expected_output": "Expected 1"},
            {"input": "Test input 2", "expected_output": "Expected 2"},
        ]
    })
    
    mock_session.post = AsyncMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    test_cases = await connector.generate_test_cases(
        job_id=job_id,
        dataset_path="./test_data.json",
        num_cases=2
    )
    
    assert len(test_cases) == 2
    assert test_cases[0]["input"] == "Test input 1"
    assert job_id in connector._test_cases
    assert len(connector._test_cases[job_id]) == 2


@pytest.mark.asyncio
async def test_run_evaluation(connector, mock_session):
    """Test running evaluation on model outputs."""
    # Setup
    connector._connected = True
    connector._session = mock_session
    
    job_id = "eval_test"
    connector._evaluations[job_id] = {
        "eval_id": "eval-123",
        "status": JobStatus.PENDING,
    }
    connector._test_cases[job_id] = [
        {"input": "Test 1", "expected": "Expected 1"},
        {"input": "Test 2", "expected": "Expected 2"},
    ]
    
    # Mock evaluation response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "results": {
            "metrics": {
                "answer_relevancy": 0.85,
                "faithfulness": 0.92,
                "hallucination": 0.05,
            }
        }
    })
    
    mock_session.post = AsyncMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    model_outputs = ["Output 1", "Output 2"]
    results = await connector.run_evaluation(
        job_id=job_id,
        model_outputs=model_outputs
    )
    
    assert "metrics" in results
    assert results["metrics"]["answer_relevancy"] == 0.85
    assert results["metrics"]["faithfulness"] == 0.92
    assert connector._evaluations[job_id]["status"] == JobStatus.COMPLETED


@pytest.mark.asyncio
async def test_run_evaluation_no_test_cases(connector):
    """Test running evaluation without test cases."""
    connector._connected = True
    
    job_id = "eval_test"
    connector._evaluations[job_id] = {
        "eval_id": "eval-123",
        "status": JobStatus.PENDING,
    }
    
    with pytest.raises(ValueError, match="No test cases available"):
        await connector.run_evaluation(
            job_id=job_id,
            model_outputs=["Output 1"]
        )


@pytest.mark.asyncio
async def test_calculate_metrics(connector, mock_session):
    """Test calculating specific metrics."""
    # Setup
    connector._connected = True
    connector._session = mock_session
    
    job_id = "eval_test"
    connector._evaluations[job_id] = {
        "eval_id": "eval-123",
        "results": {},
    }
    
    # Mock metrics calculation response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "metrics": {
            "answer_relevancy": 0.88,
            "faithfulness": 0.95,
        }
    })
    
    mock_session.post = AsyncMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    predictions = ["Prediction 1", "Prediction 2"]
    references = ["Reference 1", "Reference 2"]
    
    metrics = await connector.calculate_metrics(
        job_id=job_id,
        predictions=predictions,
        references=references,
        metric_names=["answer_relevancy", "faithfulness"]
    )
    
    assert metrics["answer_relevancy"] == 0.88
    assert metrics["faithfulness"] == 0.95
    assert "metrics" in connector._evaluations[job_id]["results"]


@pytest.mark.asyncio
async def test_detect_quality_issues(connector, mock_session):
    """Test detecting quality issues and getting suggestions."""
    # Setup
    connector._connected = True
    connector._session = mock_session
    
    job_id = "eval_test"
    connector._evaluations[job_id] = {
        "eval_id": "eval-123",
        "results": {
            "metrics": {
                "faithfulness": 0.65,
                "hallucination": 0.25,
            }
        },
    }
    
    # Mock quality analysis response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "issues": [
            "Low faithfulness score (0.65)",
            "High hallucination rate (0.25)",
        ],
        "suggestions": [
            "Increase training data size",
            "Add more context to prompts",
            "Fine-tune with higher quality examples",
        ]
    })
    
    mock_session.post = AsyncMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    analysis = await connector.detect_quality_issues(
        job_id=job_id,
        threshold=0.7
    )
    
    assert len(analysis["issues"]) == 2
    assert len(analysis["suggestions"]) == 3
    assert "Low faithfulness score" in analysis["issues"][0]
    assert "quality_analysis" in connector._evaluations[job_id]


@pytest.mark.asyncio
async def test_detect_quality_issues_no_results(connector):
    """Test detecting quality issues without evaluation results."""
    connector._connected = True
    
    job_id = "eval_test"
    connector._evaluations[job_id] = {
        "eval_id": "eval-123",
    }
    
    with pytest.raises(ValueError, match="No evaluation results available"):
        await connector.detect_quality_issues(job_id)


@pytest.mark.asyncio
async def test_get_job_status(connector, mock_session):
    """Test getting evaluation job status."""
    # Setup
    connector._connected = True
    connector._session = mock_session
    
    job_id = "eval_test"
    connector._evaluations[job_id] = {
        "eval_id": "eval-123",
    }
    
    # Mock status response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "status": "completed"
    })
    
    mock_session.get = AsyncMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    status = await connector.get_job_status(job_id)
    
    assert status == JobStatus.COMPLETED


@pytest.mark.asyncio
async def test_cancel_job(connector, mock_session):
    """Test cancelling an evaluation job."""
    # Setup
    connector._connected = True
    connector._session = mock_session
    
    job_id = "eval_test"
    connector._evaluations[job_id] = {
        "eval_id": "eval-123",
        "status": JobStatus.RUNNING,
    }
    
    # Mock cancel response
    mock_response = AsyncMock()
    mock_response.status = 200
    
    mock_session.post = AsyncMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    result = await connector.cancel_job(job_id)
    
    assert result is True
    assert connector._evaluations[job_id]["status"] == JobStatus.CANCELLED


@pytest.mark.asyncio
async def test_stream_logs(connector, mock_session):
    """Test streaming evaluation logs."""
    # Setup
    connector._connected = True
    connector._session = mock_session
    
    job_id = "eval_test"
    connector._evaluations[job_id] = {
        "eval_id": "eval-123",
        "status": JobStatus.RUNNING,
        "results": {
            "metrics": {
                "answer_relevancy": 0.85,
            }
        },
    }
    
    # Mock progress response
    mock_progress_response = AsyncMock()
    mock_progress_response.status = 200
    mock_progress_response.json = AsyncMock(return_value={
        "progress": 50,
        "current_metric": "answer_relevancy"
    })
    
    # Mock status response (completed)
    mock_status_response = AsyncMock()
    mock_status_response.status = 200
    mock_status_response.json = AsyncMock(return_value={
        "status": "completed"
    })
    
    call_count = [0]
    
    async def mock_get(url):
        call_count[0] += 1
        if "progress" in url:
            return mock_progress_response
        else:
            # Return completed status after first call
            if call_count[0] > 2:
                connector._evaluations[job_id]["status"] = JobStatus.COMPLETED
            return mock_status_response
    
    mock_session.get = mock_get
    mock_progress_response.__aenter__ = AsyncMock(return_value=mock_progress_response)
    mock_progress_response.__aexit__ = AsyncMock(return_value=None)
    mock_status_response.__aenter__ = AsyncMock(return_value=mock_status_response)
    mock_status_response.__aexit__ = AsyncMock(return_value=None)
    
    logs = []
    async for log in connector.stream_logs(job_id):
        logs.append(log)
        if len(logs) >= 3:  # Limit iterations
            break
    
    assert len(logs) > 0
    assert any("Progress" in log or "completed" in log for log in logs)


@pytest.mark.asyncio
async def test_compare_evaluations(connector, mock_session):
    """Test comparing multiple evaluations."""
    # Setup
    connector._connected = True
    connector._session = mock_session
    
    job_id1 = "eval_test1"
    job_id2 = "eval_test2"
    
    connector._evaluations[job_id1] = {
        "eval_id": "eval-123",
        "created_at": "2024-01-01T00:00:00",
        "status": JobStatus.COMPLETED,
        "results": {
            "metrics": {
                "answer_relevancy": 0.85,
                "faithfulness": 0.90,
            }
        },
    }
    
    connector._evaluations[job_id2] = {
        "eval_id": "eval-456",
        "created_at": "2024-01-02T00:00:00",
        "status": JobStatus.COMPLETED,
        "results": {
            "metrics": {
                "answer_relevancy": 0.88,
                "faithfulness": 0.92,
            }
        },
    }
    
    # Mock comparison response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "significance": {
            "answer_relevancy": {"p_value": 0.03, "significant": True},
            "faithfulness": {"p_value": 0.15, "significant": False},
        }
    })
    
    mock_session.post = AsyncMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    comparison = await connector.compare_evaluations([job_id1, job_id2])
    
    assert len(comparison["evaluations"]) == 2
    assert len(comparison["metrics"]) == 2
    assert job_id1 in comparison["metrics"]
    assert job_id2 in comparison["metrics"]
    assert "statistical_significance" in comparison


@pytest.mark.asyncio
async def test_fetch_artifact(connector, mock_session):
    """Test downloading evaluation results."""
    # Setup
    connector._connected = True
    connector._session = mock_session
    
    job_id = "eval_test"
    connector._evaluations[job_id] = {
        "eval_id": "eval-123",
    }
    
    # Mock export response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.read = AsyncMock(return_value=b'{"results": "test"}')
    
    mock_session.get = AsyncMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    artifact = await connector.fetch_artifact(job_id)
    
    assert artifact == b'{"results": "test"}'


@pytest.mark.asyncio
async def test_get_required_credentials(connector):
    """Test getting required credentials list."""
    credentials = connector.get_required_credentials()
    
    assert "api_key" in credentials
    assert len(credentials) == 1


@pytest.mark.asyncio
async def test_list_resources(connector):
    """Test listing resources (should be empty)."""
    resources = await connector.list_resources()
    
    assert resources == []


@pytest.mark.asyncio
async def test_get_pricing(connector):
    """Test getting pricing (should raise error)."""
    with pytest.raises(ValueError, match="subscription-based pricing"):
        await connector.get_pricing("resource-123")


@pytest.mark.asyncio
async def test_get_evaluation_url(connector):
    """Test getting evaluation dashboard URL."""
    job_id = "eval_test"
    connector._evaluations[job_id] = {
        "eval_id": "eval-123",
        "project_id": "project-456",
    }
    
    url = connector.get_evaluation_url(job_id)
    
    assert url is not None
    assert "confident-ai.com" in url
    assert "project-456" in url
    assert "eval-123" in url


@pytest.mark.asyncio
async def test_disconnect(connector, mock_session):
    """Test disconnecting from DeepEval."""
    connector._connected = True
    connector._session = mock_session
    connector._api_key = "test-key"
    connector._project_id = "test-project"
    
    mock_session.close = AsyncMock()
    
    result = await connector.disconnect()
    
    assert result is True
    assert connector._connected is False
    assert connector._session is None
    assert connector._api_key is None


@pytest.mark.asyncio
async def test_verify_connection(connector, mock_session):
    """Test verifying connection status."""
    connector._connected = True
    connector._session = mock_session
    
    # Mock successful verification
    mock_response = AsyncMock()
    mock_response.status = 200
    
    mock_session.get = AsyncMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    result = await connector.verify_connection()
    
    assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
