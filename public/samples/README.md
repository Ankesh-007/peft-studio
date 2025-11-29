# Sample Dataset and Model

This directory contains sample data for testing PEFT Studio features.

## Sample Dataset

**File**: `sample-dataset.jsonl`

A small conversational dataset with 10 instruction-response pairs covering various topics:
- General knowledge questions
- Programming tasks
- Science explanations
- Practical instructions

**Format**: JSONL (JSON Lines)
Each line contains:
- `instruction`: The user's question or request
- `input`: Additional context (optional)
- `output`: The expected response

## Usage

This sample dataset is automatically available when you complete the onboarding setup wizard. You can use it to:

1. Test the Training Wizard workflow
2. Experiment with different optimization profiles
3. Learn how to format your own datasets
4. Verify your system is working correctly

## Model Information

For testing purposes, we recommend using small models like:
- **Llama-3-8B** (8 billion parameters)
- **Mistral-7B** (7 billion parameters)
- **GPT-Neo-2.7B** (2.7 billion parameters)

These models are small enough to train quickly on consumer hardware while still demonstrating the full capabilities of PEFT Studio.

## Creating Your Own Dataset

To create your own dataset, follow this format:

```jsonl
{"instruction": "Your question or task", "input": "", "output": "The expected response"}
{"instruction": "Another question", "input": "", "output": "Another response"}
```

### Tips:
- Keep instructions clear and specific
- Provide diverse examples
- Aim for at least 50-100 examples for meaningful fine-tuning
- Use consistent formatting across all entries
