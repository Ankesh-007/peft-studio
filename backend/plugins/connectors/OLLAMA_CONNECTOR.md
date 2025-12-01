# Ollama Connector

The Ollama connector integrates with local Ollama instances to provide model registry and local inference capabilities.

## Overview

Ollama is a tool for running large language models locally. This connector enables:
- Browsing the local model library
- Generating Modelfiles for custom models
- Packaging adapters as Ollama models
- Pushing models to Ollama library
- Local inference with models

## Features

- ✅ Model library browsing
- ✅ Modelfile generation
- ✅ Local model packaging
- ✅ Model push to Ollama library
- ✅ Local inference
- ✅ Model metadata caching
- ❌ Training jobs (not applicable)
- ❌ Remote compute (local only)

## Prerequisites

1. **Install Ollama**: Download and install from [ollama.ai](https://ollama.ai)
2. **Start Ollama service**: Run `ollama serve` or start the Ollama app
3. **Verify installation**: Run `ollama list` to see available models

## Connection

### Basic Connection

```python
from plugins.connectors.ollama_connector import OllamaConnector

connector = OllamaConnector()

# Connect to local Ollama instance (default: http://localhost:11434)
await connector.connect({})
```

### Custom Base URL

```python
# Connect to Ollama on a different host/port
await connector.connect({
    "base_url": "http://192.168.1.100:11434"
})
```

### No Authentication Required

Ollama typically runs locally without authentication. The connector only needs to verify that the Ollama service is accessible.

## Usage Examples

### 1. List Available Models

```python
# List all models in local Ollama instance
models = await connector.list_models()

for model in models:
    print(f"Name: {model.name}")
    print(f"Size: {model.size / (1024**3):.2f} GB")
    print(f"Modified: {model.modified_at}")
    print(f"Format: {model.details.get('format', 'unknown')}")
    print()
```

### 2. Get Model Metadata

```python
# Get metadata for a specific model
metadata = await connector.get_model_metadata("llama2:7b")

if metadata:
    print(f"Model: {metadata.name}")
    print(f"Size: {metadata.size}")
    print(f"Digest: {metadata.digest}")
    print(f"Details: {metadata.details}")
```

### 3. Generate Modelfile

```python
# Basic Modelfile
modelfile = connector.generate_modelfile(
    base_model="llama2:7b"
)

# Modelfile with adapter
modelfile = connector.generate_modelfile(
    base_model="llama2:7b",
    adapter_path="/path/to/adapter.safetensors"
)

# Complete Modelfile with all options
modelfile = connector.generate_modelfile(
    base_model="llama2:7b",
    adapter_path="/path/to/adapter.safetensors",
    system_prompt="You are a helpful coding assistant.",
    template="{{ .System }}\n\nUser: {{ .Prompt }}\nAssistant:",
    parameters={
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 40,
        "num_ctx": 4096,
    }
)

print(modelfile)
```

Example Modelfile output:
```
FROM llama2:7b

ADAPTER /path/to/adapter.safetensors

SYSTEM """You are a helpful coding assistant."""

TEMPLATE """{{ .System }}

User: {{ .Prompt }}
Assistant:"""

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_ctx 4096
```

### 4. Create Custom Model

```python
# Generate Modelfile
modelfile = connector.generate_modelfile(
    base_model="llama2:7b",
    system_prompt="You are a helpful assistant."
)

# Create model from Modelfile
await connector.create_model(
    name="my-custom-model",
    modelfile=modelfile,
    stream=True  # Show progress
)

# Verify model was created
models = await connector.list_models()
assert any(m.name == "my-custom-model" for m in models)
```

### 5. Package and Upload Adapter

```python
# Package adapter as Ollama model
metadata = {
    "name": "my-finetuned-llama",
    "base_model": "llama2:7b",
    "system_prompt": "You are a helpful assistant specialized in Python.",
    "parameters": {
        "temperature": 0.7,
        "top_p": 0.9,
    },
    "push": False,  # Set to True to push to Ollama library
}

model_name = await connector.upload_artifact(
    path="/path/to/adapter.safetensors",
    metadata=metadata
)

print(f"Model created: {model_name}")
```

### 6. Pull Model from Library

```python
# Pull a model from Ollama library
await connector.pull_model(
    name="llama2:7b",
    stream=True  # Show download progress
)
```

### 7. Push Model to Library

```python
# Push your custom model to Ollama library
# Note: Requires proper authentication and permissions
await connector.push_model(
    name="username/my-custom-model",
    stream=True
)
```

### 8. Generate Text

```python
# Generate text with a model
response = await connector.generate(
    model="llama2:7b",
    prompt="Explain quantum computing in simple terms.",
    stream=False,
    options={
        "temperature": 0.7,
        "top_p": 0.9,
    }
)

print(response)
```

### 9. Delete Model

```python
# Delete a model from local instance
await connector.delete_model("my-custom-model")
```

## Modelfile Reference

A Modelfile defines how to build a custom model. It supports the following instructions:

### FROM (Required)
Specifies the base model to use.
```
FROM llama2:7b
```

### ADAPTER (Optional)
Adds adapter weights to the model.
```
ADAPTER /path/to/adapter.safetensors
```

### SYSTEM (Optional)
Sets the system prompt.
```
SYSTEM """You are a helpful assistant."""
```

### TEMPLATE (Optional)
Defines the prompt template.
```
TEMPLATE """{{ .System }}

User: {{ .Prompt }}
Assistant:"""
```

### PARAMETER (Optional)
Sets model parameters.
```
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_ctx 4096
PARAMETER repeat_penalty 1.1
```

Common parameters:
- `temperature`: Controls randomness (0.0-2.0)
- `top_p`: Nucleus sampling threshold (0.0-1.0)
- `top_k`: Top-k sampling (1-100)
- `num_ctx`: Context window size
- `repeat_penalty`: Penalty for repetition (1.0-2.0)

## Integration with PEFT Studio

### Workflow: Fine-tune → Package → Deploy

```python
# 1. After fine-tuning, you have an adapter
adapter_path = "/path/to/trained/adapter.safetensors"

# 2. Package as Ollama model
metadata = {
    "name": "my-finetuned-model",
    "base_model": "llama2:7b",
    "system_prompt": "You are a specialized assistant.",
}

model_name = await connector.upload_artifact(adapter_path, metadata)

# 3. Use for local inference
response = await connector.generate(
    model=model_name,
    prompt="Your prompt here"
)
```

## Caching

The connector implements model metadata caching:

- **Cache Location**: `~/.peft-studio/cache/ollama/`
- **TTL**: 24 hours (configurable)
- **Persistence**: Cache survives application restarts
- **Offline Access**: Cached metadata available offline

```python
# Get metadata with caching (default)
metadata = await connector.get_model_metadata("llama2:7b", use_cache=True)

# Force refresh from API
metadata = await connector.get_model_metadata("llama2:7b", use_cache=False)

# Clear cache
connector._cache.clear()
```

## Error Handling

```python
try:
    await connector.connect({})
except ConnectionError as e:
    print(f"Ollama not running: {e}")
    print("Start Ollama with: ollama serve")

try:
    await connector.create_model("my-model", modelfile)
except RuntimeError as e:
    print(f"Model creation failed: {e}")

try:
    await connector.upload_artifact(path, metadata)
except FileNotFoundError:
    print("Adapter file not found")
except ValueError as e:
    print(f"Invalid metadata: {e}")
```

## Limitations

1. **Local Only**: Ollama runs locally, no cloud compute
2. **No Training**: Cannot submit training jobs (use compute providers)
3. **Model Format**: Works best with GGUF format models
4. **Authentication**: Limited support for authenticated operations (push)

## Troubleshooting

### Connection Failed

**Problem**: `ConnectionError: Failed to connect to Ollama`

**Solutions**:
1. Check if Ollama is running: `ollama list`
2. Start Ollama: `ollama serve` or launch Ollama app
3. Verify port: Default is 11434
4. Check firewall settings

### Model Not Found

**Problem**: Model doesn't appear in list

**Solutions**:
1. Pull the model: `ollama pull llama2:7b`
2. Verify model name: `ollama list`
3. Check model was created successfully

### Adapter Loading Failed

**Problem**: Model creation fails with adapter

**Solutions**:
1. Verify adapter file exists and is readable
2. Check adapter format (should be .safetensors or .gguf)
3. Ensure base model is compatible
4. Check Ollama logs for details

### Out of Memory

**Problem**: Model fails to load due to insufficient memory

**Solutions**:
1. Use a smaller model variant (e.g., 7B instead of 13B)
2. Use quantized models (Q4, Q5)
3. Close other applications
4. Increase system swap space

## API Reference

### Connection Methods

- `connect(credentials)`: Connect to Ollama instance
- `disconnect()`: Disconnect and cleanup
- `verify_connection()`: Check if connection is valid

### Model Management

- `list_models()`: List all local models
- `get_model_metadata(name)`: Get metadata for specific model
- `pull_model(name)`: Pull model from library
- `push_model(name)`: Push model to library
- `delete_model(name)`: Delete local model

### Modelfile Operations

- `generate_modelfile(...)`: Generate Modelfile content
- `create_model(name, modelfile)`: Create model from Modelfile

### Inference

- `generate(model, prompt, options)`: Generate text

### Artifact Management

- `upload_artifact(path, metadata)`: Package adapter as Ollama model

## Requirements Validation

This connector satisfies the following requirements:

- ✅ **Requirement 2.1**: Model browsing from Ollama library
- ✅ **Requirement 8.1**: Adapter upload to Ollama
- ✅ **Requirement 8.3**: Modelfile generation and local packaging

## See Also

- [Ollama Documentation](https://github.com/ollama/ollama/tree/main/docs)
- [Ollama API Reference](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Modelfile Reference](https://github.com/ollama/ollama/blob/main/docs/modelfile.md)
- [HuggingFace Connector](./HUGGINGFACE_CONNECTOR.md)
- [Civitai Connector](./civitai_connector.py)
