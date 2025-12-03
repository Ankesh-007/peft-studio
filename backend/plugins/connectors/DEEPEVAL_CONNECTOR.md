# DeepEval Connector

## Overview

The DeepEval connector integrates with the DeepEval platform for automated LLM evaluation and testing. It provides comprehensive evaluation capabilities including test case generation, metric calculation, and quality issue detection.

## Features

- **Test Case Generation**: Automatically generate test cases from validation datasets
- **Evaluation Execution**: Run evaluations with multiple metrics
- **Metric Calculation**: Calculate various quality metrics (relevancy, faithfulness, hallucination, etc.)
- **Quality Issue Detection**: Identify quality issues and get improvement suggestions
- **Evaluation Comparison**: Compare multiple evaluations with statistical significance

## Supported Metrics

The connector supports the following evaluation metrics:

- `answer_relevancy`: Measures how relevant the answer is to the question
- `faithfulness`: Measures factual consistency with the context
- `contextual_relevancy`: Measures relevance of retrieved context
- `hallucination`: Detects hallucinated information
- `toxicity`: Detects toxic or harmful content
- `bias`: Detects biased responses
- `g_eval`: General evaluation using GPT-based scoring
- `summarization`: Evaluates summary quality
- `ragas`: RAGAS framework metrics

## Configuration

### Required Credentials

- `api_key`: DeepEval API key (required)
- `project_id`: Project ID (optional, will use default if not provided)

### Example Connection

```python
from plugins.connectors.deepeval_connector import DeepEvalConnector

connector = DeepEvalConnector()

# Connect with credentials
await connector.connect({
    "api_key": "your-api-key-here",
    "project_id": "optional-project-id"
})
```

## Usage

### 1. Create Evaluation Job

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
    dataset_path="./validation_data.json",
    validation_split=0.1,
)

# Create evaluation job
job_id = await connector.submit_job(config)
```

### 2. Generate Test Cases

```python
# Generate test cases from validation data
test_cases = await connector.generate_test_cases(
    job_id=job_id,
    dataset_path="./validation_data.json",
    num_cases=100,
    task_type="text_generation"
)

print(f"Generated {len(test_cases)} test cases")
```

### 3. Run Evaluation

```python
# Get model predictions
model_outputs = [
    "This is the model's response to test case 1",
    "This is the model's response to test case 2",
    # ... more outputs
]

# Run evaluation
results = await connector.run_evaluation(
    job_id=job_id,
    model_outputs=model_outputs,
    metrics=["answer_relevancy", "faithfulness", "hallucination"]
)

print("Evaluation Results:")
for metric, score in results.get("metrics", {}).items():
    print(f"  {metric}: {score:.4f}")
```

### 4. Calculate Specific Metrics

```python
# Calculate metrics for specific predictions
predictions = ["Model prediction 1", "Model prediction 2"]
references = ["Ground truth 1", "Ground truth 2"]
contexts = ["Context for prediction 1", "Context for prediction 2"]

metrics = await connector.calculate_metrics(
    job_id=job_id,
    predictions=predictions,
    references=references,
    contexts=contexts,
    metric_names=["answer_relevancy", "faithfulness"]
)

print("Calculated Metrics:")
for metric, score in metrics.items():
    print(f"  {metric}: {score:.4f}")
```

### 5. Detect Quality Issues

```python
# Detect quality issues and get suggestions
analysis = await connector.detect_quality_issues(
    job_id=job_id,
    threshold=0.7  # Quality threshold (0-1)
)

print("Quality Issues:")
for issue in analysis["issues"]:
    print(f"  - {issue}")

print("\nSuggestions:")
for suggestion in analysis["suggestions"]:
    print(f"  - {suggestion}")
```

### 6. Monitor Evaluation Progress

```python
# Stream evaluation logs
async for log in connector.stream_logs(job_id):
    print(log)
```

### 7. Compare Evaluations

```python
# Compare multiple evaluations
comparison = await connector.compare_evaluations([job_id1, job_id2, job_id3])

print("Comparison Results:")
for eval_data in comparison["evaluations"]:
    print(f"  Job {eval_data['job_id']}: {eval_data['status']}")

print("\nMetrics Comparison:")
for job_id, metrics in comparison["metrics"].items():
    print(f"  {job_id}:")
    for metric, score in metrics.items():
        print(f"    {metric}: {score:.4f}")

if comparison["statistical_significance"]:
    print("\nStatistical Significance:")
    print(comparison["statistical_significance"])
```

### 8. Export Results

```python
# Download evaluation results
results_data = await connector.fetch_artifact(job_id)

# Save to file
with open("evaluation_results.json", "wb") as f:
    f.write(results_data)
```

## API Reference

### Main Methods

#### `connect(credentials: Dict[str, str]) -> bool`
Connect to DeepEval platform and verify credentials.

#### `submit_job(config: TrainingConfig) -> str`
Create a new evaluation job. Returns job ID.

#### `generate_test_cases(job_id: str, dataset_path: str, num_cases: int, task_type: str) -> List[Dict]`
Generate test cases from validation data.

#### `run_evaluation(job_id: str, model_outputs: List[str], test_cases: Optional[List[Dict]], metrics: Optional[List[str]]) -> Dict`
Execute evaluation on model outputs.

#### `calculate_metrics(job_id: str, predictions: List[str], references: List[str], contexts: Optional[List[str]], metric_names: Optional[List[str]]) -> Dict[str, float]`
Calculate specific evaluation metrics.

#### `detect_quality_issues(job_id: str, threshold: float) -> Dict`
Detect quality issues and get improvement suggestions.

#### `get_job_status(job_id: str) -> JobStatus`
Get current evaluation status.

#### `stream_logs(job_id: str) -> AsyncIterator[str]`
Stream evaluation progress logs.

#### `compare_evaluations(job_ids: List[str]) -> Dict`
Compare multiple evaluations with statistical significance.

#### `fetch_artifact(job_id: str) -> bytes`
Download evaluation results as JSON.

## Integration with Training Pipeline

The DeepEval connector integrates seamlessly with the training pipeline:

```python
# After training completes
training_job_id = await training_connector.submit_job(training_config)

# Wait for training to complete
while await training_connector.get_job_status(training_job_id) == JobStatus.RUNNING:
    await asyncio.sleep(10)

# Create evaluation job
eval_job_id = await deepeval_connector.submit_job(training_config)

# Generate test cases
test_cases = await deepeval_connector.generate_test_cases(
    job_id=eval_job_id,
    dataset_path=training_config.dataset_path,
    num_cases=100
)

# Get model predictions (from inference)
predictions = await get_model_predictions(test_cases)

# Run evaluation
results = await deepeval_connector.run_evaluation(
    job_id=eval_job_id,
    model_outputs=predictions
)

# Check for quality issues
if results.get("metrics", {}).get("faithfulness", 1.0) < 0.7:
    analysis = await deepeval_connector.detect_quality_issues(eval_job_id)
    print("Quality issues detected:")
    for suggestion in analysis["suggestions"]:
        print(f"  - {suggestion}")
```

## Error Handling

The connector provides detailed error messages for common issues:

```python
try:
    await connector.connect(credentials)
except ValueError as e:
    print(f"Invalid credentials: {e}")
except ConnectionError as e:
    print(f"Connection failed: {e}")

try:
    results = await connector.run_evaluation(job_id, outputs)
except RuntimeError as e:
    print(f"Evaluation failed: {e}")
```

## Best Practices

1. **Test Case Generation**: Generate sufficient test cases (100+) for reliable evaluation
2. **Metric Selection**: Choose metrics relevant to your task (e.g., faithfulness for RAG)
3. **Quality Threshold**: Set appropriate thresholds based on your quality requirements
4. **Comparison**: Compare multiple model versions to track improvements
5. **Issue Detection**: Always check for quality issues after evaluation

## Limitations

- Requires active DeepEval API subscription
- Evaluation time depends on number of test cases and metrics
- Some metrics require specific input formats (e.g., contexts for faithfulness)
- Statistical significance requires at least 2 evaluations

## Troubleshooting

### Connection Issues
- Verify API key is valid
- Check network connectivity
- Ensure project exists or let connector create default

### Evaluation Failures
- Verify test cases are properly formatted
- Ensure model outputs match test case count
- Check that selected metrics are supported

### Quality Detection Issues
- Run evaluation before detecting quality issues
- Ensure threshold is between 0 and 1
- Check that evaluation results contain metrics

## References

- [DeepEval Documentation](https://docs.confident-ai.com/)
- [DeepEval Metrics Guide](https://docs.confident-ai.com/docs/metrics-introduction)
- [DeepEval API Reference](https://docs.confident-ai.com/docs/api-reference)
