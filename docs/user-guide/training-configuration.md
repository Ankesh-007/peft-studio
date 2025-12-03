# Training Configuration Guide

Complete guide to configuring PEFT training in PEFT Studio.

## Overview

PEFT Studio provides a wizard-based interface for configuring training with smart defaults and explanations for every parameter.

## Training Configuration Wizard

### Step 1: Select Base Model

**What to consider:**
- Model size (7B, 13B, 70B parameters)
- Task compatibility (chat, completion, instruction)
- License restrictions
- Hardware requirements

**Popular choices:**
- **Llama 2 7B**: General purpose, good balance
- **Mistral 7B**: Strong performance, efficient
- **CodeLlama 7B**: Code-specific tasks
- **Falcon 7B**: Open license, versatile

**Tips:**
- Start with 7B models for experimentation
- Check VRAM requirements before selecting
- Consider quantized versions for limited hardware

### Step 2: Choose PEFT Algorithm

#### LoRA (Low-Rank Adaptation)
**Best for:** General fine-tuning, balanced performance

**Parameters:**
- **Rank (r)**: 4-64 (default: 8)
  - Lower = less parameters, faster training
  - Higher = more capacity, better quality
- **Alpha (α)**: Usually 2×rank (default: 16)
  - Controls adaptation strength
- **Dropout**: 0.0-0.1 (default: 0.05)
  - Prevents overfitting
- **Target Modules**: Which layers to adapt
  - Common: `["q_proj", "v_proj"]`
  - More: `["q_proj", "k_proj", "v_proj", "o_proj"]`

**Example config:**
```json
{
  "algorithm": "lora",
  "rank": 8,
  "alpha": 16,
  "dropout": 0.05,
  "target_modules": ["q_proj", "v_proj"]
}
```

#### QLoRA (Quantized LoRA)
**Best for:** Limited VRAM, cost optimization

**Additional parameters:**
- **Quantization**: int4, int8, or nf4
- **Double quantization**: Further memory savings

**Benefits:**
- 4× memory reduction with int4
- Minimal quality loss
- Enables larger models on smaller GPUs

**Example config:**
```json
{
  "algorithm": "qlora",
  "rank": 8,
  "alpha": 16,
  "quantization": "nf4",
  "double_quantization": true
}
```

#### DoRA (Weight-Decomposed LoRA)
**Best for:** Maximum quality, research

**Characteristics:**
- Better than LoRA for same rank
- Slightly slower training
- More stable convergence

**Example config:**
```json
{
  "algorithm": "dora",
  "rank": 8,
  "alpha": 16,
  "dropout": 0.05
}
```

#### PiSSA (Principal Singular Values and Singular Vectors Adaptation)
**Best for:** Fast convergence, efficiency

**Characteristics:**
- Faster convergence than LoRA
- Better initialization
- Requires SVD computation

#### rsLoRA (Rank-Stabilized LoRA)
**Best for:** High-rank training, stability

**Characteristics:**
- Stable at higher ranks
- Better scaling properties
- Recommended for rank >16

### Step 3: Configure Hyperparameters

#### Learning Rate
**Range:** 1e-6 to 1e-2
**Default:** 2e-4

**Guidelines:**
- Smaller models: 2e-4 to 5e-4
- Larger models: 1e-4 to 2e-4
- More data: Lower learning rate
- Less data: Higher learning rate

**Scheduler options:**
- Linear: Gradual decrease
- Cosine: Smooth curve
- Constant: No change

#### Batch Size
**Range:** 1-32 per GPU
**Default:** 4

**Considerations:**
- Larger = faster training, more memory
- Smaller = less memory, more stable
- Use gradient accumulation for effective larger batches

**Formula:**
```
Effective Batch Size = batch_size × gradient_accumulation_steps × num_gpus
```

#### Gradient Accumulation
**Range:** 1-32
**Default:** 4

**Purpose:**
- Simulate larger batch sizes
- Reduce memory usage
- Maintain training stability

**Example:**
```
batch_size = 2
gradient_accumulation_steps = 8
# Effective batch size = 16
```

#### Number of Epochs
**Range:** 1-10
**Default:** 3

**Guidelines:**
- Small datasets: 3-5 epochs
- Large datasets: 1-2 epochs
- Monitor validation loss to avoid overfitting

#### Warmup Steps
**Range:** 0-1000
**Default:** 100

**Purpose:**
- Gradual learning rate increase
- Prevents early instability
- Recommended: 5-10% of total steps

### Step 4: Select Compute Provider

#### Local GPU
**Pros:**
- Zero cost
- Full control
- No network latency

**Cons:**
- Limited to your hardware
- Ties up your machine
- No scalability

**Best for:**
- Experimentation
- Small models
- Development

#### RunPod
**Pros:**
- Wide GPU selection
- Competitive pricing
- Fast provisioning

**Cons:**
- Spot instances can be interrupted
- Variable availability

**Pricing:** $0.39-$2.89/hour

#### Lambda Labs
**Pros:**
- H100 and A100 GPUs
- Reliable infrastructure
- Good for production

**Cons:**
- Limited availability
- Higher prices
- Approval required

**Pricing:** $1.10-$2.49/hour

#### Vast.ai
**Pros:**
- Lowest prices
- Many options
- Flexible

**Cons:**
- Variable quality
- Less reliable
- More complex setup

**Pricing:** $0.20-$1.50/hour

### Step 5: Upload Dataset

#### Supported Formats

**JSON Lines (.jsonl):**
```json
{"text": "Example 1"}
{"text": "Example 2"}
```

**JSON Array:**
```json
[
  {"text": "Example 1"},
  {"text": "Example 2"}
]
```

**CSV:**
```csv
text
"Example 1"
"Example 2"
```

**Instruction Format:**
```json
{
  "instruction": "Translate to French",
  "input": "Hello world",
  "output": "Bonjour le monde"
}
```

#### Dataset Best Practices

1. **Quality over Quantity**
   - 100 high-quality examples > 1000 poor ones
   - Clean and consistent formatting
   - Remove duplicates

2. **Validation Split**
   - Use 10-20% for validation
   - Monitor for overfitting
   - Early stopping if needed

3. **Data Diversity**
   - Cover different scenarios
   - Include edge cases
   - Balance categories

4. **Length Considerations**
   - Trim very long examples
   - Pad short examples
   - Consider context window

### Step 6: Configure Experiment Tracking

#### Weights & Biases
**Features:**
- Real-time metrics
- Hyperparameter tracking
- Model comparison
- Team collaboration

**Setup:**
```json
{
  "experiment_tracker": "wandb",
  "project_name": "my-finetuning",
  "run_name": "llama2-lora-v1",
  "tags": ["lora", "llama2", "production"]
}
```

#### Comet ML
**Features:**
- Experiment management
- Model registry
- Code tracking
- Reproducibility

#### Arize Phoenix
**Features:**
- LLM-specific metrics
- Trace logging
- Hallucination detection
- Evaluation tracking

### Step 7: Review and Launch

**Final checklist:**
- [ ] Model selected and compatible
- [ ] PEFT algorithm configured
- [ ] Hyperparameters set
- [ ] Compute provider selected
- [ ] Dataset uploaded and validated
- [ ] Experiment tracking enabled
- [ ] Output directory specified

**Cost estimate:**
- Training time: ~45 minutes
- Compute cost: $2.50
- Total cost: $2.50

**Click "Launch Training" to start!**

## Advanced Configuration

### Gradient Checkpointing
**Enable for:**
- Large models
- Limited VRAM
- Batch size >4

**Trade-off:**
- 20-30% slower training
- 30-40% memory savings

### Mixed Precision Training
**Options:**
- fp16: Faster, less memory
- bf16: More stable, better for large models
- fp32: Highest precision, most memory

**Recommendation:**
- Use bf16 for Ampere GPUs (A100, RTX 30xx)
- Use fp16 for older GPUs

### Custom Learning Rate Schedule
```json
{
  "lr_scheduler_type": "cosine",
  "warmup_ratio": 0.1,
  "num_cycles": 0.5
}
```

### Early Stopping
```json
{
  "early_stopping": true,
  "early_stopping_patience": 3,
  "early_stopping_threshold": 0.01
}
```

## Configuration Templates

### Quick Start (7B Model)
```json
{
  "base_model": "meta-llama/Llama-2-7b-hf",
  "algorithm": "lora",
  "rank": 8,
  "alpha": 16,
  "learning_rate": 2e-4,
  "batch_size": 4,
  "num_epochs": 3,
  "quantization": null
}
```

### Memory Optimized (13B Model)
```json
{
  "base_model": "meta-llama/Llama-2-13b-hf",
  "algorithm": "qlora",
  "rank": 8,
  "alpha": 16,
  "learning_rate": 1e-4,
  "batch_size": 1,
  "gradient_accumulation_steps": 16,
  "num_epochs": 2,
  "quantization": "nf4",
  "gradient_checkpointing": true
}
```

### High Quality (7B Model)
```json
{
  "base_model": "mistralai/Mistral-7B-v0.1",
  "algorithm": "dora",
  "rank": 16,
  "alpha": 32,
  "learning_rate": 1e-4,
  "batch_size": 8,
  "gradient_accumulation_steps": 2,
  "num_epochs": 5,
  "warmup_steps": 200
}
```

## Troubleshooting

### Training is too slow
- Reduce batch size
- Enable gradient checkpointing
- Use quantization
- Try smaller model

### Out of memory
- Reduce batch size to 1
- Increase gradient accumulation
- Enable quantization (QLoRA)
- Use gradient checkpointing
- Reduce rank

### Loss not decreasing
- Increase learning rate
- Reduce warmup steps
- Check dataset quality
- Try different algorithm

### Loss is NaN
- Reduce learning rate
- Add gradient clipping
- Increase warmup steps
- Check for data issues

## Next Steps

- [Deploy your adapter](deployment.md)
- [Share your configuration](configuration-management.md)
- [Explore the model browser](model-browser.md)
