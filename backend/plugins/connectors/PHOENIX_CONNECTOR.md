# Arize Phoenix Connector

## Overview

The Arize Phoenix connector integrates with Arize Phoenix's LLM observability platform for trace logging, evaluation tracking, and hallucination detection.

## Features

- **LLM Trace Logging**: Track LLM interactions with detailed span logging
- **Evaluation Tracking**: Log evaluation results and metrics
- **Hallucination Detection**: Detect hallucinations in LLM responses
- **Experiment Comparison**: Compare multiple traces and evaluations

## Configuration

### Required Credentials

- `api_key`: Arize Phoenix API key

### Optional Credentials

- `project_id`: Project ID (defaults to first available project)

## Usage

### Connecting

```python
from plugins.connectors.phoenix_connector import PhoenixConnector

connector = PhoenixConnector()
await connector.connect({
    "api_key": "your-api-key",
    "project_id": "optional-project-id"
})
```

### Creating a Trace

```python
from connectors.base import TrainingConfig

config = TrainingConfig(
    base_model="meta-llama/Llama-2-7b-hf",
    model_source="huggingface",
    algorithm="lora",
    rank=16,
    alpha=32,
    dropout=0.1,
    target_modules=["q_proj", "v_proj"],
    project_name="my-llm-project"
)

job_id = await connector.submit_job(config)
```

### Logging Spans

```python
# Log a basic span
span_id = await connector.log_span(
    job_id=job_id,
    name="llm_generation",
    span_type="llm",
    input_data={"prompt": "What is the capital of France?"},
    output_data={"response": "The capital of France is Paris."},
    metadata={"model": "gpt-4", "temperature": 0.7}
)

# Log nested spans
parent_span_id = await connector.log_span(
    job_id=job_id,
    name="chain_execution",
    span_type="chain",
    input_data={"query": "Research question"}
)

child_span_id = await connector.log_span(
    job_id=job_id,
    name="retrieval",
    span_type="retriever",
    input_data={"query": "Research question"},
    output_data={"documents": ["doc1", "doc2"]},
    parent_span_id=parent_span_id
)
```

### Logging Metrics

```python
# Log training metrics
await connector.log_metrics(
    job_id=job_id,
    metrics={
        "loss": 0.234,
        "accuracy": 0.89,
        "learning_rate": 2e-4
    },
    step=100
)
```

### Logging Evaluations

```python
# Log evaluation results
await connector.log_evaluation(
    job_id=job_id,
    eval_name="validation_set",
    predictions=["Paris", "London", "Berlin"],
    references=["Paris", "London", "Berlin"],
    scores={
        "accuracy": 1.0,
        "f1_score": 1.0,
        "precision": 1.0,
        "recall": 1.0
    }
)
```

### Hallucination Detection

```python
# Detect hallucinations
result = await connector.detect_hallucination(
    job_id=job_id,
    context="The Eiffel Tower is located in Paris, France.",
    response="The Eiffel Tower is located in London, England.",
    threshold=0.5
)

print(f"Is hallucination: {result['is_hallucination']}")
print(f"Confidence: {result['confidence']}")
```

### Comparing Traces

```python
# Compare multiple traces
comparison = await connector.compare_traces([job_id1, job_id2, job_id3])

print(f"Traces: {comparison['traces']}")
print(f"Spans: {comparison['spans']}")
print(f"Evaluations: {comparison['evaluations']}")
```

### Getting Trace URL

```python
# Get dashboard URL
url = connector.get_trace_url(job_id)
print(f"View trace at: {url}")
```

## Span Types

Phoenix supports various span types for different LLM operations:

- `llm`: LLM generation calls
- `chain`: Chain of operations
- `tool`: Tool/function calls
- `retriever`: Document retrieval
- `embedding`: Embedding generation
- `metrics`: Metric logging
- `evaluation`: Evaluation results
- `hallucination`: Hallucination detection

## API Endpoints

- `GET /v1/projects` - List projects
- `POST /v1/projects` - Create project
- `POST /v1/traces` - Create trace
- `GET /v1/traces/{trace_id}` - Get trace details
- `PATCH /v1/traces/{trace_id}` - Update trace
- `POST /v1/spans` - Log spans (batch)
- `GET /v1/traces/{trace_id}/spans` - Get trace spans
- `GET /v1/traces/{trace_id}/export` - Export trace data
- `POST /v1/traces/{trace_id}/import` - Import trace data
- `POST /v1/hallucination/detect` - Detect hallucinations

## Batching

The connector automatically batches spans for efficiency:

- **Batch Size**: 50 spans per batch
- **Batch Interval**: 3 seconds
- **Auto-flush**: When batch is full or on disconnect

## Error Handling

The connector handles various error scenarios:

- **Connection Errors**: Retries with exponential backoff
- **Batch Failures**: Re-queues spans for retry
- **API Errors**: Graceful degradation with error logging

## Best Practices

1. **Use Descriptive Names**: Give spans meaningful names for easier debugging
2. **Add Metadata**: Include relevant metadata for filtering and analysis
3. **Nest Spans**: Use parent-child relationships for complex operations
4. **Log Evaluations**: Track evaluation metrics for model quality
5. **Detect Hallucinations**: Use hallucination detection for critical responses
6. **Compare Traces**: Compare multiple runs to identify improvements

## Limitations

- Phoenix doesn't provide compute resources (training/inference)
- Pricing is subscription-based, not per-resource
- Trace data is retained based on subscription plan
- API rate limits apply based on subscription tier

## References

- [Arize Phoenix Documentation](https://docs.arize.com/phoenix/)
- [Phoenix API Reference](https://docs.arize.com/phoenix/api/)
- [LLM Observability Guide](https://docs.arize.com/phoenix/llm-observability/)
