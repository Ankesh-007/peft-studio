# Enhanced Training Configuration Wizard

## Overview

The Enhanced Training Configuration Wizard provides a comprehensive interface for configuring LLM fine-tuning with support for multiple compute providers, PEFT algorithms, quantization options, and experiment tracking.

**Validates Requirements:** 4.1, 4.2, 4.3, 4.4, 4.5

## Features

### 1. Provider Selection (Requirement 4.1)
- **Local GPU**: Free, uses your local hardware
- **RunPod**: Cloud GPU provider
- **Lambda Labs**: H100/A100 instances
- **Vast.ai**: Marketplace GPU rental

The wizard automatically detects connected cloud providers and displays only available options.

### 2. Algorithm Selection (Requirement 4.2)
Supported PEFT algorithms:
- **LoRA**: Standard Low-Rank Adaptation
- **QLoRA**: Quantized LoRA with 4-bit quantization
- **DoRA**: Weight-Decomposed Low-Rank Adaptation
- **PiSSA**: Principal Singular Values and Singular Vectors Adaptation
- **rsLoRA**: Rank-Stabilized LoRA

### 3. Quantization Configuration (Requirement 4.3)
- **None**: Full precision training
- **int8**: 8-bit integer quantization
- **int4**: 4-bit integer quantization
- **NF4**: 4-bit NormalFloat quantization

**Note:** DoRA is incompatible with quantization. The wizard validates this automatically.

### 4. Experiment Tracking (Requirement 4.4)
- **None**: No experiment tracking
- **Weights & Biases (W&B)**: Industry-standard experiment tracking
- **Comet ML**: ML experiment management
- **Arize Phoenix**: LLM-focused tracking

When an experiment tracker is selected, a project name is required.

### 5. Configuration Validation (Requirement 4.5)
The wizard validates:
- All required fields are populated
- Hyperparameters are within valid ranges
- Algorithm and quantization compatibility
- Experiment tracker configuration completeness
- Memory requirements vs. available resources

## Components

### Frontend Component
**Location:** `src/components/wizard/EnhancedConfigurationStep.tsx`

Features:
- Real-time validation feedback
- Dynamic provider detection
- Smart defaults based on hardware
- Training estimates (time, cost, carbon footprint)
- Accessibility support

### Backend Service
**Location:** `backend/services/training_config_service.py`

Provides:
- `TrainingConfiguration` dataclass
- `validate_configuration()` method
- `is_configuration_complete()` method
- Algorithm and quantization descriptions
- Memory requirement estimation

### API Endpoint
**Endpoint:** `POST /api/config/validate-training`

Request body:
```json
{
  "provider": "local",
  "algorithm": "lora",
  "quantization": "none",
  "experiment_tracker": "wandb",
  "project_name": "my-project",
  "model_name": "meta-llama/Llama-2-7b",
  "model_path": "/models/llama-2-7b",
  "dataset_id": "my-dataset",
  "dataset_path": "/data/my-dataset",
  "lora_r": 8,
  "lora_alpha": 16,
  "lora_dropout": 0.1,
  "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj"],
  "learning_rate": 0.0002,
  "batch_size": 4,
  "gradient_accumulation_steps": 4,
  "num_epochs": 3
}
```

Response:
```json
{
  "is_valid": true,
  "errors": [],
  "warnings": ["Learning rate is quite high, may cause training instability"],
  "suggestions": ["Enable experiment tracking to monitor training progress"]
}
```

## Property-Based Testing

**Test File:** `backend/tests/test_training_configuration_completeness.py`

**Property 4: Training configuration completeness**
> For any training configuration, all required fields should be populated before submission is allowed.

The test suite includes:
- 10 property-based tests covering all requirements
- 100+ test cases per property
- Validation of complete and incomplete configurations
- Algorithm and quantization compatibility testing
- Experiment tracker validation
- Hyperparameter validation

All tests pass successfully.

## Usage Example

```typescript
// In your React component
const handleConfigUpdate = async (config: EnhancedConfig) => {
  const response = await fetch('http://127.0.0.1:8000/api/config/validate-training', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });
  
  const validation = await response.json();
  
  if (!validation.is_valid) {
    // Show errors to user
    setValidationErrors(validation.errors);
  } else {
    // Proceed to next step
    onNext();
  }
};
```

## Validation Rules

### Required Fields
- Provider must be selected
- Algorithm must be selected
- Model name and path must be provided
- Dataset ID and path must be provided
- All hyperparameters must be positive
- LoRA rank (r) must be positive
- LoRA alpha must be positive
- LoRA dropout must be between 0 and 1
- At least one target module must be specified

### Compatibility Rules
- DoRA cannot be used with quantization
- Experiment tracker requires project name
- QLoRA typically uses 4-bit quantization (warning if not)

### Warnings
- Very small effective batch size (batch_size * gradient_accumulation = 1)
- High learning rate (> 1e-3)
- QLoRA without quantization

### Suggestions
- Consider cloud providers for faster training (when using local)
- Enable experiment tracking (when tracker is none)

## Integration with Training Wizard

The Enhanced Configuration Step integrates seamlessly with the existing Training Wizard:

1. User selects use case (Step 1)
2. User uploads dataset (Step 2)
3. User selects model (Step 3)
4. **Enhanced Configuration (Step 4)** ← New
5. User reviews and launches (Step 5)

The wizard automatically:
- Fetches available compute providers
- Calculates smart defaults based on hardware
- Validates configuration in real-time
- Updates training estimates dynamically
- Prevents submission of invalid configurations

## Testing

Run all tests:
```bash
# Property-based tests
python -m pytest backend/tests/test_training_configuration_completeness.py -v

# API integration tests
python -m pytest backend/tests/test_training_config_api.py -v
```

## Future Enhancements

Potential improvements:
- Save configuration presets
- Compare configurations side-by-side
- Import/export configurations
- Configuration recommendations based on use case
- Advanced hyperparameter tuning suggestions
- Cost optimization recommendations
