# HuggingFace Hub Connector

## Overview

The HuggingFace Hub connector integrates PEFT Studio with HuggingFace Hub, the primary model registry for open-source LLMs. This connector enables model discovery, metadata caching, model downloads, and adapter uploads with automatic model card generation.

## Features

- ✅ Model search and browsing across HuggingFace Hub
- ✅ Model metadata fetching with 24-hour caching
- ✅ Offline-first architecture with persistent cache
- ✅ Model download with caching
- ✅ Adapter upload with automatic model card generation
- ✅ License checking
- ✅ Compatibility verification
- ✅ Repository management

## Requirements Validated

This connector implements the following requirements:

- **Requirement 2.1**: Browse and select base models from HuggingFace registry
- **Requirement 2.2**: Display model metadata (size, license, downloads, compatibility)
- **Requirement 2.4**: Cache model metadata for offline access (Property 6)
- **Requirement 8.1**: Upload adapters to HuggingFace Hub
- **Requirement 8.2**: Generate model cards with training details
- **Requirement 12.1**: Offline-first with cached metadata

## Installation

### Prerequisites

```bash
pip install aiohttp huggingface_hub
```

### Configuration

The connector requires a HuggingFace API token for authentication.

## Usage

### 1. Connection

```python
from plugins.connectors.huggingface_connector import HuggingFaceConnector

# Create connector instance
connector = HuggingFaceConnector()

# Connect with API token
await connector.connect({
    "token": "hf_your_token_here"
})

# Verify connection
is_connected = await connector.verify_connection()
```

### 2. Search Models

```python
# Search for models
results = await connector.search_models(
    query="llama",
    filter_tags=["text-generation", "pytorch"],
    sort="downloads",
    limit=20
)

for model in results:
    print(f"{model.model_id}: {model.downloads} downloads")
```

### 3. Get Model Metadata

```python
# Get metadata (uses cache if available)
metadata = await connector.get_model_metadata(
    "meta-llama/Llama-2-7b-hf",
    use_cache=True
)

if metadata:
    print(f"Model: {metadata.model_id}")
    print(f"License: {metadata.license}")
    print(f"Size: {metadata.model_size} bytes")
    print(f"Library: {metadata.library_name}")
```

### 4. Download Model

```python
# Download model with caching
model_path = await connector.download_model(
    "meta-llama/Llama-2-7b-hf",
    cache_dir=Path("~/.cache/huggingface")
)

print(f"Model downloaded to: {model_path}")
```

### 5. Upload Adapter

```python
# Upload adapter with metadata
repo_url = await connector.upload_artifact(
    path="./output/adapter",
    metadata={
        "repo_id": "username/my-adapter",
        "base_model": "meta-llama/Llama-2-7b-hf",
        "dataset": "alpaca",
        "description": "Fine-tuned on Alpaca dataset",
        "training_config": {
            "rank": 16,
            "alpha": 32,
            "learning_rate": 2e-4,
        },
        "metrics": {
            "loss": 0.5,
            "accuracy": 0.85,
        }
    }
)

print(f"Adapter uploaded to: {repo_url}")
```

### 6. Check License and Compatibility

```python
# Check model license
license_info = await connector.check_license("meta-llama/Llama-2-7b-hf")
print(f"License: {license_info}")

# Check compatibility
is_compatible = await connector.check_compatibility(
    "meta-llama/Llama-2-7b-hf",
    required_library="transformers"
)
print(f"Compatible: {is_compatible}")
```

## Model Metadata Caching

The connector implements **Property 6: Model metadata caching** to support offline-first operation.

### Cache Behavior

- **TTL**: 24 hours by default (configurable)
- **Storage**: Persistent disk cache at `~/.peft-studio/cache/models/`
- **Format**: JSON files with MD5-hashed filenames
- **Cross-session**: Cache survives application restarts

### Cache Operations

```python
# Get cached metadata (returns None if expired)
metadata = connector._cache.get("model-id", ttl_hours=24)

# Manually cache metadata
connector._cache.set(metadata)

# Remove from cache
connector._cache.remove("model-id")

# Clear all cache
connector._cache.clear()

# Get all cached models
all_cached = connector._cache.get_all_cached()
```

### Cache Expiration

```python
# Check if cache entry is expired
if metadata.is_expired(ttl_hours=24):
    print("Cache expired, fetching fresh data")
```

## Model Card Generation

When uploading adapters, the connector automatically generates a comprehensive model card in Markdown format.

### Generated Model Card Includes

- Base model information
- Training dataset
- Adapter type (LoRA, QLoRA, etc.)
- Training configuration (JSON)
- Evaluation metrics
- Usage examples with code
- License information

### Example Model Card

```markdown
---
base_model: meta-llama/Llama-2-7b-hf
tags:
- peft
- lora
- adapter
license: apache-2.0
---

# username/my-adapter

Fine-tuned on Alpaca dataset

## Model Details

- **Base Model:** meta-llama/Llama-2-7b-hf
- **Training Dataset:** alpaca
- **Adapter Type:** LoRA
- **Created with:** PEFT Studio

## Training Configuration

```json
{
  "rank": 16,
  "alpha": 32,
  "learning_rate": 0.0002
}
```

## Evaluation Metrics

- **loss:** 0.5
- **accuracy:** 0.85

## Usage

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Load base model
base_model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-2-7b-hf")
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-hf")

# Load adapter
model = PeftModel.from_pretrained(base_model, "username/my-adapter")

# Generate
inputs = tokenizer("Your prompt here", return_tensors="pt")
outputs = model.generate(**inputs)
print(tokenizer.decode(outputs[0]))
```

## License

This adapter is released under the Apache 2.0 license.
```

## API Reference

### HuggingFaceConnector

#### Methods

##### `connect(credentials: Dict[str, str]) -> bool`

Connect to HuggingFace Hub with API token.

**Parameters:**
- `credentials`: Dictionary with `token` key (HF API token starting with "hf_")

**Returns:** `True` if connection successful

**Raises:**
- `ValueError`: If token is missing or invalid format
- `ConnectionError`: If connection fails

##### `search_models(query, filter_tags, sort, limit) -> List[ModelMetadata]`

Search for models on HuggingFace Hub.

**Parameters:**
- `query` (Optional[str]): Search query string
- `filter_tags` (Optional[List[str]]): Filter by tags
- `sort` (str): Sort by "downloads", "likes", "trending", or "updated"
- `limit` (int): Maximum number of results (default: 20)

**Returns:** List of `ModelMetadata` objects

##### `get_model_metadata(model_id, use_cache) -> Optional[ModelMetadata]`

Get metadata for a specific model with caching support.

**Parameters:**
- `model_id` (str): Model identifier (e.g., "meta-llama/Llama-2-7b-hf")
- `use_cache` (bool): Whether to use cached data (default: True)

**Returns:** `ModelMetadata` or `None` if not found

##### `download_model(model_id, cache_dir) -> Path`

Download a model with caching.

**Parameters:**
- `model_id` (str): Model identifier
- `cache_dir` (Optional[Path]): Cache directory (default: ~/.cache/huggingface)

**Returns:** Path to downloaded model directory

**Raises:**
- `RuntimeError`: If not connected or download fails
- `FileNotFoundError`: If model doesn't exist

##### `upload_artifact(path, metadata) -> str`

Upload an adapter with automatic model card generation.

**Parameters:**
- `path` (str): Local path to adapter directory
- `metadata` (Dict): Adapter metadata (see usage example)

**Returns:** Repository URL

**Raises:**
- `RuntimeError`: If not connected or upload fails
- `FileNotFoundError`: If local path doesn't exist
- `ValueError`: If `repo_id` is missing from metadata

##### `check_license(model_id) -> Optional[str]`

Check the license of a model.

**Parameters:**
- `model_id` (str): Model identifier

**Returns:** License identifier (e.g., "apache-2.0", "mit") or `None`

##### `check_compatibility(model_id, required_library) -> bool`

Check if a model is compatible with requirements.

**Parameters:**
- `model_id` (str): Model identifier
- `required_library` (Optional[str]): Required library (e.g., "transformers")

**Returns:** `True` if compatible, `False` otherwise

### ModelMetadata

Data class representing model metadata.

**Attributes:**
- `model_id` (str): Model identifier
- `author` (str): Model author
- `downloads` (int): Download count
- `likes` (int): Like count
- `tags` (List[str]): Model tags
- `pipeline_tag` (Optional[str]): Pipeline type
- `library_name` (Optional[str]): Library name
- `license` (Optional[str]): License identifier
- `model_size` (Optional[int]): Model size in bytes
- `created_at` (str): Creation timestamp
- `last_modified` (str): Last modification timestamp
- `siblings` (List[Dict]): Model files
- `card_data` (Optional[Dict]): Model card data
- `cached_at` (datetime): Cache timestamp

**Methods:**
- `to_dict() -> Dict`: Convert to dictionary for serialization
- `from_dict(data: Dict) -> ModelMetadata`: Create from dictionary
- `is_expired(ttl_hours: int) -> bool`: Check if cache entry is expired

### ModelCache

Cache manager for model metadata.

**Methods:**
- `get(model_id, ttl_hours) -> Optional[ModelMetadata]`: Get cached metadata
- `set(metadata)`: Cache metadata
- `remove(model_id)`: Remove from cache
- `clear()`: Clear all cache
- `get_all_cached() -> List[ModelMetadata]`: Get all cached models

## Testing

### Unit Tests

Run the connector tests:

```bash
pytest backend/tests/test_huggingface_connector.py -v
```

### Property-Based Tests

Run the caching property tests:

```bash
pytest backend/tests/test_model_metadata_caching.py -v
```

The property-based tests verify:
- Metadata persistence across sessions
- 24-hour cache availability
- Expired cache removal
- Multiple model independence
- Serialization round-trip
- Cache operations

## Error Handling

### Common Errors

**Invalid Token Format**
```python
# Error: Token doesn't start with "hf_"
ValueError: Invalid HuggingFace token format (should start with 'hf_')
```

**Not Connected**
```python
# Error: Attempting operations without connection
RuntimeError: Not connected to HuggingFace
```

**Model Not Found**
```python
# Returns None instead of raising error
metadata = await connector.get_model_metadata("nonexistent/model")
# metadata is None
```

**Upload Without repo_id**
```python
# Error: Missing required metadata
ValueError: repo_id is required in metadata
```

## Offline Operation

The connector is designed for offline-first operation:

1. **Online**: Fetches metadata from API and caches it
2. **Offline**: Returns cached metadata if available and not expired
3. **Cache Miss**: Returns `None` when offline and not cached

```python
# This works offline if model was previously cached
metadata = await connector.get_model_metadata(
    "meta-llama/Llama-2-7b-hf",
    use_cache=True
)

if metadata:
    print("Using cached metadata")
else:
    print("Not available offline")
```

## Performance Considerations

### Cache Benefits

- **Reduced API calls**: Cached metadata avoids repeated API requests
- **Faster response**: Local cache is instant vs. network latency
- **Offline access**: Continue working without internet
- **Cost savings**: Fewer API calls reduce rate limiting issues

### Cache Storage

- Each cached model: ~1-5 KB
- 1000 models: ~1-5 MB
- Cache directory: `~/.peft-studio/cache/models/`

## Security

### Token Storage

- Tokens are stored in OS keystore via `CredentialService`
- Never logged or exposed in error messages
- Transmitted only over HTTPS

### API Communication

- All API calls use HTTPS
- Bearer token authentication
- No credentials in URLs or query parameters

## Limitations

### Not Supported

The HuggingFace connector is a registry connector and does not support:
- Training job submission
- Compute resource provisioning
- Inference endpoints
- Experiment tracking

These operations raise `NotImplementedError`.

### Rate Limiting

HuggingFace Hub has rate limits:
- Unauthenticated: 60 requests/hour
- Authenticated: 5000 requests/hour

The connector's caching helps stay within limits.

## Troubleshooting

### Connection Issues

**Problem**: Connection fails with 401 error
**Solution**: Verify token is valid and starts with "hf_"

**Problem**: Connection timeout
**Solution**: Check internet connection and firewall settings

### Cache Issues

**Problem**: Cache not persisting
**Solution**: Check write permissions for `~/.peft-studio/cache/models/`

**Problem**: Stale cache data
**Solution**: Clear cache with `connector._cache.clear()`

### Upload Issues

**Problem**: Upload fails with 403 error
**Solution**: Verify token has write permissions

**Problem**: Model card not generated
**Solution**: Ensure adapter directory contains required files

## Contributing

When extending the HuggingFace connector:

1. Maintain offline-first design
2. Cache all metadata fetches
3. Follow the `PlatformConnector` interface
4. Add tests for new functionality
5. Update this documentation

## References

- [HuggingFace Hub API Documentation](https://huggingface.co/docs/huggingface_hub)
- [HuggingFace Hub Python Library](https://github.com/huggingface/huggingface_hub)
- [Model Card Guidelines](https://huggingface.co/docs/hub/model-cards)
- [PEFT Studio Connector Architecture](../../connectors/README.md)
