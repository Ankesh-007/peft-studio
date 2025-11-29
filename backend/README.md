# PEFT Studio Backend

## Overview

The PEFT Studio backend provides a FastAPI-based service for Parameter-Efficient Fine-Tuning of Large Language Models using Unsloth for optimized performance (2x speed, 60-70% less VRAM).

## Features Implemented

### 1. PEFT Service (`services/peft_service.py`)
- Support for multiple PEFT algorithms: LoRA, QLoRA, DoRA, PiSSA, rsLoRA
- Unsloth integration for optimized model loading and training
- Automatic configuration of algorithm-specific parameters
- Memory-efficient model management

### 2. Hardware Profiling Service (`services/hardware_service.py`)
- GPU detection with detailed specifications (memory, compute capability, CUDA version)
- CPU and RAM detection
- CUDA environment validation
- Hardware profile caching (5-minute refresh)
- Real-time resource monitoring

### 3. Model Registry Service (`services/model_registry_service.py`)
- HuggingFace Hub integration
- Model search and filtering
- Model metadata caching
- Popular models discovery
- Model compatibility checking

## API Endpoints

### Hardware
- `GET /api/hardware/profile` - Get complete hardware profile
- `GET /api/hardware/cuda/validate` - Validate CUDA environment

### Models
- `POST /api/models/search` - Search HuggingFace models
- `GET /api/models/{model_id}` - Get model details
- `GET /api/models/popular/{task}` - Get popular models for a task

### PEFT
- `POST /api/peft/load-model` - Load model with Unsloth
- `GET /api/peft/loaded-models` - List loaded models
- `GET /api/peft/algorithms` - List supported PEFT algorithms

## Testing

Property-based tests are implemented using Hypothesis to ensure correctness across all input combinations.

### Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

### Test Coverage

- **Property 1**: Use case selection configures all parameters (Requirements 1.2, 3.2)
  - Validates that all PEFT algorithms correctly configure required parameters
  - Tests algorithm-specific flags (rsLoRA, DoRA, PiSSA)
  - Verifies parameter preservation with custom configurations

## Installation

```bash
cd backend
pip install -r requirements.txt
```

Note: Unsloth requires CUDA and may need specific system configurations.

## Running the Server

```bash
cd backend
python main.py
```

The server will start on `http://127.0.0.1:8000`

## Dependencies

Key dependencies:
- FastAPI - Web framework
- Unsloth - Optimized PEFT training
- PyTorch - Deep learning framework
- Transformers - HuggingFace models
- PEFT - Parameter-efficient fine-tuning
- Hypothesis - Property-based testing
