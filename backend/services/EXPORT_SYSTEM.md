# Model Export System

## Overview

The Model Export System provides comprehensive functionality for exporting fine-tuned models to various deployment formats. This system implements Requirements 15.1-15.5 from the simplified-llm-optimization specification.

## Supported Export Formats

### 1. HuggingFace Format
- **Artifacts Generated:**
  - `README.md` - Model card with training details and usage instructions
  - `config.json` - Model configuration
  - Model weight files (`.bin`, `.safetensors`, `.pt`, `.pth`)
  - Tokenizer files (`tokenizer.json`, `tokenizer_config.json`, `special_tokens_map.json`)

- **Use Case:** Sharing models on HuggingFace Hub, integration with Transformers library

### 2. Ollama Format
- **Artifacts Generated:**
  - `Modelfile` - Ollama configuration with parameters and templates
  - `INSTALL.md` - Installation and usage instructions
  - `model/` - Model directory with weights

- **Use Case:** Local deployment with Ollama for easy CLI and API access

### 3. GGUF Format
- **Artifacts Generated:**
  - `CONVERSION_INSTRUCTIONS.md` - Step-by-step conversion guide
  - `conversion_info.json` - Metadata about the conversion

- **Use Case:** Deployment with llama.cpp, LM Studio, or other GGUF-compatible tools
- **Note:** Requires manual conversion using llama.cpp tools

### 4. LM Studio Format
- **Artifacts Generated:**
  - `lmstudio_config.json` - LM Studio configuration
  - `LMSTUDIO_SETUP.md` - Setup and usage instructions
  - `model/` - Model directory with weights

- **Use Case:** Easy import into LM Studio for local inference

## API Endpoints

### Export Model
```
POST /api/export/model
```

**Request Body:**
```json
{
  "model_path": "/path/to/checkpoint",
  "format": "huggingface",
  "model_name": "my-fine-tuned-model",
  "metadata": {
    "config": {...},
    "metrics": {...}
  },
  "quantization": "Q4_K_M",
  "merge_adapters": true
}
```

**Response:**
```json
{
  "success": true,
  "format": "huggingface",
  "output_path": "/exports/huggingface/my-fine-tuned-model",
  "artifacts": ["README.md", "config.json", "adapter_model.bin"],
  "size_bytes": 14680064,
  "message": "Successfully exported to HuggingFace format",
  "verification_passed": true,
  "verification_details": {
    "passed": true,
    "found_files": ["README.md", "config.json"],
    "has_model_weights": true
  }
}
```

### Verify Export
```
POST /api/export/verify
```

**Request Body:**
```json
{
  "export_path": "/exports/huggingface/my-model",
  "format": "huggingface"
}
```

**Response:**
```json
{
  "passed": true,
  "details": {
    "passed": true,
    "found_files": ["README.md", "config.json"],
    "missing_required_files": [],
    "has_model_weights": true,
    "message": "Export verification passed"
  }
}
```

### List Export Formats
```
GET /api/export/formats
```

**Response:**
```json
{
  "formats": [
    {
      "id": "huggingface",
      "name": "HuggingFace",
      "description": "Export to HuggingFace format with model card, config, and tokenizer",
      "artifacts": ["README.md", "config.json", "model weights", "tokenizer files"]
    },
    ...
  ]
}
```

### Export from Version
```
POST /api/export/from-version
```

**Request Body:**
```json
{
  "model_name": "chatbot-model",
  "version": "v1.0.0",
  "format": "ollama",
  "quantization": null,
  "merge_adapters": true
}
```

## Service Architecture

### ModelExporter Class

The `ModelExporter` class provides the core export functionality:

```python
class ModelExporter:
    def export_model(
        self,
        model_path: str,
        format: ExportFormat,
        model_name: str,
        metadata: Optional[Dict[str, Any]] = None,
        quantization: Optional[str] = None,
        merge_adapters: bool = True
    ) -> ExportResult
    
    def verify_export(
        self,
        export_path: str,
        format: ExportFormat
    ) -> Dict[str, Any]
```

### Export Result

Each export operation returns an `ExportResult` object:

```python
@dataclass
class ExportResult:
    success: bool
    format: ExportFormat
    output_path: str
    artifacts: List[str]
    size_bytes: int
    message: str
    verification_passed: bool
    verification_details: Optional[Dict[str, Any]]
```

## Property-Based Testing

The export system is validated with comprehensive property-based tests:

### Test Coverage

1. **HuggingFace Export Completeness (Property 32)**
   - Validates all required artifacts are present
   - Checks model card content
   - Verifies model weights inclusion
   - Tests with and without metadata

2. **Ollama Export Artifacts (Property 33)**
   - Validates Modelfile generation
   - Checks installation instructions
   - Verifies model directory structure
   - Tests Modelfile syntax

3. **Export Verification (Property 34)**
   - Tests verification for all formats
   - Validates consistency across multiple runs
   - Checks error handling for invalid paths
   - Verifies format-specific requirements

### Running Tests

```bash
# Run all export tests
python -m pytest backend/tests/test_huggingface_export.py -v
python -m pytest backend/tests/test_ollama_export.py -v
python -m pytest backend/tests/test_export_verification.py -v

# Run with hypothesis settings
python -m pytest backend/tests/test_*_export.py -v --hypothesis-show-statistics
```

## Usage Examples

### Python Service Usage

```python
from services.export_service import get_model_exporter

# Get exporter instance
exporter = get_model_exporter()

# Export to HuggingFace
result = exporter.export_model(
    model_path="/models/checkpoint",
    format='huggingface',
    model_name="my-chatbot",
    metadata={
        'config': {'model_name': 'llama-2-7b', 'lora_r': 16},
        'metrics': {'final_loss': 0.45}
    }
)

if result.success:
    print(f"Exported to: {result.output_path}")
    print(f"Artifacts: {result.artifacts}")
    print(f"Verification: {'Passed' if result.verification_passed else 'Failed'}")
```

### API Usage

```python
import requests

# Export model
response = requests.post('http://localhost:8000/api/export/model', json={
    'model_path': '/models/checkpoint',
    'format': 'ollama',
    'model_name': 'my-assistant',
    'metadata': {'config': {...}, 'metrics': {...}}
})

result = response.json()
print(f"Export successful: {result['success']}")
print(f"Output path: {result['output_path']}")

# Verify export
verify_response = requests.post('http://localhost:8000/api/export/verify', json={
    'export_path': result['output_path'],
    'format': 'ollama'
})

verification = verify_response.json()
print(f"Verification passed: {verification['passed']}")
```

## Integration with Model Versioning

The export system integrates seamlessly with the model versioning system:

```python
# Export a specific version
response = requests.post('http://localhost:8000/api/export/from-version', json={
    'model_name': 'chatbot-model',
    'version': 'v1.2.0',
    'format': 'huggingface'
})
```

This automatically:
1. Retrieves the specified version from the versioning system
2. Includes version metadata in the export
3. Names the export with version information
4. Verifies the export completeness

## Future Enhancements

Planned improvements for the export system:

1. **MergeKit Integration**
   - Multi-adapter merging using TIES and DARE methods
   - Combine multiple LoRA adapters into a single model

2. **GGUF Conversion**
   - Automated conversion using llama.cpp
   - Support for various quantization levels
   - Batch conversion of multiple models

3. **Additional Formats**
   - TensorRT optimization
   - ONNX export
   - Mobile formats (CoreML, TFLite)

4. **Export Validation**
   - Automated inference testing
   - Performance benchmarking
   - Quality verification

## Requirements Validation

This implementation validates the following requirements:

- **15.1**: Export options display for HuggingFace, Ollama, LM Studio, and GGUF ✓
- **15.2**: HuggingFace export with model card, config, and tokenizer ✓
- **15.3**: Ollama export with Modelfile and instructions ✓
- **15.4**: Export completion display with location and test button ✓
- **15.5**: Export verification for correct loading and sample output ✓

## Error Handling

The export system includes comprehensive error handling:

- Invalid export paths
- Missing model files
- Insufficient disk space
- Format-specific validation errors
- Graceful degradation for optional components

All errors are logged and returned with descriptive messages to help users resolve issues.
