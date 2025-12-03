"""
Tests for Arize Phoenix connector.

Tests the Phoenix connector's ability to:
- Connect to Phoenix API
- Create and manage traces
- Log spans and metrics
- Track evaluations
- Detect hallucinations
- Compare traces
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from collections import deque
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from plugins.connectors.phoenix_connector import PhoenixConnector
from connectors.base import TrainingConfig, JobStatus


@pytest.fixture
def connector():
    """Create a Phoenix connector instance."""
    return PhoenixConnector()


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
        learning_rate=2e-4,
        batch_size=4,
        gradient_accumulation_steps=4,
        num_epochs=3,
        warmup_steps=100,
        provider="runpod",
        dataset_path="data/train.jsonl",
        validation_split=0.1,
        project_name="test-project",
    )


@pytest.mark.asyncio
async def test_connect_success(connector, mock_session):
    """Test successful connection to Phoenix."""
    # Mock successful connection
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "projects": [{"id": "project-123", "name": "test-project"}]
    })
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session.get = Mock(return_value=mock_response)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        result = await connector.connect({"api_key": "test-key"})
    
    assert result is True
    assert connector._connected is True
    assert connector._api_key == "test-key"
    assert connector._project_id == "project-123"


@pytest.mark.asyncio
async def test_connect_invalid_credentials(connector, mock_session):
    """Test connection with invalid credentials."""
    # Mock 401 response
    mock_response = AsyncMock()
    mock_response.status = 401
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session.get = Mock(return_value=mock_response)
    
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
    """Test creating a trace for a training job."""
    # Setup connection
    connector._connected = True
    connector._api_key = "test-key"
    connector._project_id = "project-123"
    connector._session = mock_session
    
    # Mock trace creation
    mock_response = AsyncMock()
    mock_response.status = 201
    mock_response.json = AsyncMock(return_value={
        "trace_id": "trace-456"
    })
    
    mock_session.post = AsyncMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    # Mock background task
    with patch('asyncio.create_task') as mock_create_task:
        job_id = await connector.submit_job(training_config)
    
    assert job_id.startswith("trace_")
    assert job_id in connector._traces
    assert connector._traces[job_id]["status"] == JobStatus.RUNNING
    assert job_id in connector._span_batches
    mock_create_task.assert_called_once()


@pytest.mark.asyncio
async def test_log_span(connector, mock_session):
    """Test logging a span."""
    # Setup
    connector._connected = True
    connector._session = mock_session
    job_id = "test-job"
    connector._span_batches[job_id] = deque()  # Use deque instead of Queue
    connector._traces[job_id] = {
        "trace_id": "trace-123",
        "spans": []
    }
    
    # Log span
    span_id = await connector.log_span(
        job_id=job_id,
        name="test_span",
        span_type="llm",
        input_data={"prompt": "test"},
        output_data={"response": "test response"},
        metadata={"model": "gpt-4"}
    )
    
    assert span_id is not None
    assert len(connector._traces[job_id]["spans"]) == 1


@pytest.mark.asyncio
async def test_log_metrics(connector, mock_session):
    """Test logging metrics as a span."""
    # Setup
    connector._connected = True
    connector._session = mock_session
    job_id = "test-job"
    connector._span_batches[job_id] = asyncio.Queue()
    connector._traces[job_id] = {
        "trace_id": "trace-123",
        "spans": []
    }
    
    # Log metrics
    await connector.log_metrics(
        job_id=job_id,
        metrics={"loss": 0.5, "accuracy": 0.9},
        step=100
    )
    
    # Verify span was created
    assert len(connector._traces[job_id]["spans"]) == 1


@pytest.mark.asyncio
async def test_log_evaluation(connector, mock_session):
    """Test logging evaluation results."""
    # Setup
    connector._connected = True
    connector._session = mock_session
    job_id = "test-job"
    connector._span_batches[job_id] = asyncio.Queue()
    connector._traces[job_id] = {
        "trace_id": "trace-123",
        "spans": []
    }
    
    # Log evaluation
    await connector.log_evaluation(
        job_id=job_id,
        eval_name="validation",
        predictions=["A", "B", "C"],
        references=["A", "B", "C"],
        scores={"accuracy": 1.0, "f1": 1.0}
    )
    
    # Verify span was created
    assert len(connector._traces[job_id]["spans"]) == 1


@pytest.mark.asyncio
async def test_detect_hallucination(connector, mock_session):
    """Test hallucination detection."""
    # Setup
    connector._connected = True
    connector._session = mock_session
    job_id = "test-job"
    connector._span_batches[job_id] = asyncio.Queue()
    connector._traces[job_id] = {
        "trace_id": "trace-123",
        "spans": []
    }
    
    # Mock hallucination detection response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "is_hallucination": True,
        "confidence": 0.85,
        "explanation": "Response contradicts context"
    })
    
    mock_session.post = AsyncMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    # Detect hallucination
    result = await connector.detect_hallucination(
        job_id=job_id,
        context="The sky is blue.",
        response="The sky is green.",
        threshold=0.5
    )
    
    assert result["is_hallucination"] is True
    assert result["confidence"] == 0.85
    assert len(connector._traces[job_id]["spans"]) == 1


@pytest.mark.asyncio
async def test_get_job_status(connector, mock_session):
    """Test getting trace status."""
    # Setup
    connector._connected = True
    connector._session = mock_session
    job_id = "test-job"
    connector._traces[job_id] = {
        "trace_id": "trace-123",
        "status": JobStatus.RUNNING
    }
    
    # Mock status response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "trace": {"status": "completed"}
    })
    
    mock_session.get = AsyncMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    status = await connector.get_job_status(job_id)
    
    assert status == JobStatus.COMPLETED


@pytest.mark.asyncio
async def test_cancel_job(connector, mock_session):
    """Test cancelling a trace."""
    # Setup
    connector._connected = True
    connector._session = mock_session
    job_id = "test-job"
    connector._traces[job_id] = {
        "trace_id": "trace-123",
        "status": JobStatus.RUNNING
    }
    connector._span_batches[job_id] = asyncio.Queue()
    
    # Mock cancel response
    mock_response = AsyncMock()
    mock_response.status = 200
    
    mock_session.patch = AsyncMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    # Mock batch task
    mock_task = AsyncMock()
    mock_task.done = Mock(return_value=False)
    mock_task.cancel = Mock()
    connector._batch_tasks[job_id] = mock_task
    
    result = await connector.cancel_job(job_id)
    
    assert result is True
    assert connector._traces[job_id]["status"] == JobStatus.CANCELLED
    mock_task.cancel.assert_called_once()


@pytest.mark.asyncio
async def test_compare_traces(connector, mock_session):
    """Test comparing multiple traces."""
    # Setup
    connector._connected = True
    connector._session = mock_session
    
    job_id1 = "job-1"
    job_id2 = "job-2"
    
    connector._traces[job_id1] = {
        "trace_id": "trace-1",
        "project_id": "project-123",
        "created_at": "2024-01-01T00:00:00"
    }
    connector._traces[job_id2] = {
        "trace_id": "trace-2",
        "project_id": "project-123",
        "created_at": "2024-01-02T00:00:00"
    }
    
    # Mock trace details
    mock_trace_response = AsyncMock()
    mock_trace_response.status = 200
    mock_trace_response.json = AsyncMock(return_value={
        "trace": {
            "name": "test-trace",
            "status": "completed"
        }
    })
    
    # Mock spans response
    mock_spans_response = AsyncMock()
    mock_spans_response.status = 200
    mock_spans_response.json = AsyncMock(return_value={
        "spans": [
            {"span_id": "span-1", "span_type": "llm"},
            {"span_id": "span-2", "span_type": "evaluation"}
        ]
    })
    
    mock_session.get = AsyncMock(side_effect=[
        mock_trace_response, mock_spans_response,
        mock_trace_response, mock_spans_response
    ])
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    comparison = await connector.compare_traces([job_id1, job_id2])
    
    assert len(comparison["traces"]) == 2
    assert job_id1 in comparison["spans"]
    assert job_id2 in comparison["spans"]
    assert job_id1 in comparison["evaluations"]
    assert job_id2 in comparison["evaluations"]


@pytest.mark.asyncio
async def test_get_trace_url(connector):
    """Test getting trace dashboard URL."""
    job_id = "test-job"
    connector._traces[job_id] = {
        "trace_id": "trace-123",
        "project_id": "project-456"
    }
    
    url = connector.get_trace_url(job_id)
    
    assert url == "https://app.phoenix.arize.com/projects/project-456/traces/trace-123"


@pytest.mark.asyncio
async def test_disconnect(connector, mock_session):
    """Test disconnecting from Phoenix."""
    # Setup
    connector._connected = True
    connector._session = mock_session
    connector._api_key = "test-key"
    
    job_id = "test-job"
    connector._traces[job_id] = {"trace_id": "trace-123"}
    connector._span_batches[job_id] = asyncio.Queue()
    
    # Mock batch task
    mock_task = AsyncMock()
    mock_task.done = Mock(return_value=False)
    mock_task.cancel = Mock()
    connector._batch_tasks[job_id] = mock_task
    
    # Mock session close
    mock_session.close = AsyncMock()
    
    result = await connector.disconnect()
    
    assert result is True
    assert connector._connected is False
    assert connector._api_key is None
    assert len(connector._traces) == 0
    mock_task.cancel.assert_called_once()
    mock_session.close.assert_called_once()


@pytest.mark.asyncio
async def test_verify_connection(connector, mock_session):
    """Test verifying connection status."""
    # Setup
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


@pytest.mark.asyncio
async def test_list_resources(connector):
    """Test listing resources (should return empty list)."""
    resources = await connector.list_resources()
    assert resources == []


@pytest.mark.asyncio
async def test_get_pricing(connector):
    """Test getting pricing (should raise ValueError)."""
    with pytest.raises(ValueError, match="subscription-based pricing"):
        await connector.get_pricing("resource-123")


def test_get_required_credentials(connector):
    """Test getting required credentials."""
    credentials = connector.get_required_credentials()
    assert credentials == ["api_key"]


def test_connector_metadata(connector):
    """Test connector metadata."""
    assert connector.name == "phoenix"
    assert connector.display_name == "Arize Phoenix"
    assert connector.supports_tracking is True
    assert connector.supports_training is False
    assert connector.supports_inference is False
    assert connector.supports_registry is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
