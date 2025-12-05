import type { TooltipConfig } from "../types/wizard";

/**
 * Tooltip configuration for all wizard settings
 * Provides plain-language explanations for technical terms
 */
export const tooltipConfig: TooltipConfig = {
  // Profile Settings
  "profile.use_case": {
    title: "Use Case",
    description:
      "The type of task you want your model to perform. Each use case has optimized settings for that specific purpose.",
    example: 'Choose "Chatbot" for conversational AI or "Code Generation" for programming tasks.',
  },

  // LoRA Settings
  lora_r: {
    title: "LoRA Rank (r)",
    description:
      "LoRA rank controls how many parameters are trained. Higher values mean more learning capacity but require more memory.",
    example: "Typical values: 8 for simple tasks, 16-32 for complex tasks.",
  },
  lora_alpha: {
    title: "LoRA Alpha",
    description:
      "LoRA alpha is a scaling factor that controls how much the fine-tuning affects the model. Usually set to 2x the rank.",
    example: "If rank is 16, alpha is typically 32.",
  },
  lora_dropout: {
    title: "LoRA Dropout",
    description:
      "LoRA dropout randomly turns off some training to prevent overfitting. Higher values (0.1-0.2) help with small datasets.",
    example: "0.05 for large datasets, 0.1-0.2 for small datasets.",
  },
  target_modules: {
    title: "Target Modules",
    description:
      "LoRA target modules specify which parts of the model to train. More modules = better results but slower training.",
    example: "Common: q_proj, v_proj for basic training; add more for complex tasks.",
  },

  // Training Hyperparameters
  learning_rate: {
    title: "Learning Rate",
    description:
      "How quickly the model learns. Too high causes instability, too low makes training slow.",
    example: "Typical range: 1e-4 to 3e-4 for fine-tuning.",
  },
  num_epochs: {
    title: "Number of Epochs",
    description:
      "How many times the model sees your entire dataset. More epochs = more learning, but risk of overfitting.",
    example: "3-5 epochs is typical for most tasks.",
  },
  warmup_ratio: {
    title: "Warmup Ratio",
    description:
      "Percentage of training where learning rate gradually increases. Helps stabilize early training.",
    example: "0.1 means 10% of training is warmup.",
  },
  max_seq_length: {
    title: "Maximum Sequence Length",
    description:
      "Maximum number of tokens (words/pieces) the model can process at once. Longer = more context but more memory.",
    example: "2048 for chat, 4096 for code or long documents.",
  },
  weight_decay: {
    title: "Weight Decay",
    description:
      "Regularization that prevents overfitting by penalizing large weights. Small values (0.01) are typical.",
    example: "0.01 is a good default for most tasks.",
  },
  max_grad_norm: {
    title: "Gradient Clipping",
    description:
      "Prevents training instability by limiting how much the model can change in one step.",
    example: "1.0 is standard; lower (0.5) for unstable training.",
  },
  scheduler: {
    title: "Learning Rate Scheduler",
    description:
      "How the learning rate changes during training. Cosine gradually decreases, linear drops steadily.",
    example: "Cosine is most common and works well for most tasks.",
  },

  // Batch and Memory Settings
  batch_size: {
    title: "Batch Size",
    description:
      "Number of examples processed together. Larger batches are faster but use more memory.",
    example: "Typical values: 4-8 for 8GB GPU, 16-32 for 24GB GPU.",
  },
  gradient_accumulation: {
    title: "Gradient Accumulation",
    description:
      "Simulates larger batches by accumulating gradients over multiple steps. Useful when memory is limited.",
    example: "If batch size is 4 and accumulation is 8, effective batch is 32.",
  },

  // Precision Settings
  precision: {
    title: "Training Precision",
    description:
      "Number format used during training. Lower precision (fp16, bf16) uses less memory and is faster.",
    example: "fp16 for most GPUs, bf16 for newer GPUs (A100, H100).",
  },
  quantization: {
    title: "Quantization",
    description:
      "Compresses the model to use less memory. 8-bit is good quality, 4-bit saves more memory.",
    example: "Automatically enabled if your GPU doesn't have enough memory.",
  },

  // Hardware Requirements
  min_gpu_memory: {
    title: "Minimum GPU Memory",
    description: "The absolute minimum GPU memory needed to run this configuration.",
    example: "Typical requirements: 8GB for 7B models, 16GB for 13B models, 24GB+ for 30B+ models.",
  },
  recommended_gpu_memory: {
    title: "Recommended GPU Memory",
    description: "GPU memory for optimal performance and stability.",
    example: "Recommended: 16GB for 7B models, 24GB for 13B models, 40GB+ for 30B+ models.",
  },
  min_dataset_size: {
    title: "Minimum Dataset Size",
    description: "Minimum number of training examples needed for this use case.",
    example: "Typical minimums: 100-500 examples for simple tasks, 1000+ for complex tasks.",
  },
  recommended_dataset_size: {
    title: "Recommended Dataset Size",
    description: "Ideal number of training examples for best results.",
    example: "Recommended: 1000-5000 examples for most tasks, 10000+ for production quality.",
  },
  estimated_time: {
    title: "Estimated Training Time",
    description: "Approximate time per epoch based on typical hardware and model size.",
    example: "Typical times: 10-30 minutes per epoch on RTX 3090, 5-15 minutes on A100.",
  },

  // Dataset Settings
  dataset_format: {
    title: "Dataset Format",
    description:
      "The file format of your training data. We support common formats like CSV, JSON, and plain text.",
    example: "Typical formats: CSV (80% of users), JSON/JSONL (15%), TXT (5%).",
  },
  dataset_validation: {
    title: "Dataset Validation",
    description:
      "Automatic checks to ensure your data is properly formatted and ready for training.",
    example: "Common checks: 100+ examples minimum, consistent field names, no empty entries.",
  },

  // Model Selection
  model_selection: {
    title: "Model Selection",
    description:
      "Choose a pre-trained model to fine-tune. Consider model size, popularity, and compatibility with your hardware.",
    example:
      "Popular choices: Llama-2-7B (70k+ downloads), Mistral-7B (50k+ downloads), Phi-2 (3B parameters).",
  },
  model_size: {
    title: "Model Size",
    description:
      "Number of parameters in the model. Larger models are more capable but require more resources.",
    example: "Common sizes: 3B (fast), 7B (balanced), 13B (capable), 70B+ (best quality).",
  },
  model_architecture: {
    title: "Model Architecture",
    description: "The underlying structure of the model (e.g., Llama, Mistral, GPT).",
    example:
      "Common architectures: Llama-2 (60% of users), Mistral (25%), GPT-style (10%), others (5%).",
  },

  // Training Estimates
  training_estimates: {
    title: "Training Estimates",
    description:
      "Predicted time, cost, and resource usage for your training run. These are estimates and may vary by ±20%.",
    example: "Typical range: 30 minutes to 4 hours depending on model size and dataset.",
  },
  training_duration: {
    title: "Training Duration",
    description: "Estimated time to complete training based on your configuration and hardware.",
    example: "Typical durations: 1-3 hours for 7B models, 3-8 hours for 13B models (3 epochs).",
  },
  gpu_hours: {
    title: "GPU Hours",
    description: "Total GPU time required for training. Useful for estimating cloud costs.",
    example: "Multiply by your cloud provider's hourly rate.",
  },
  electricity_cost: {
    title: "Electricity Cost",
    description: "Estimated electricity cost based on your GPU power consumption and local rates.",
    example: "Typical cost: $0.50-$2.00 per training run at $0.12/kWh electricity rate.",
  },
  carbon_footprint: {
    title: "Carbon Footprint",
    description: "Estimated CO2 emissions from the electricity used during training.",
    example: "Typical range: 0.5-5 kg CO2 depending on training duration and local energy mix.",
  },
  memory_usage: {
    title: "Memory Usage",
    description: "Estimated GPU memory required for training with this configuration.",
    example: "Typical usage: 6-8GB for 7B models, 12-16GB for 13B models with LoRA.",
  },
  epochs: {
    title: "Training Epochs",
    description:
      "Number of complete passes through your dataset. More epochs = more learning but risk of overfitting.",
    example: "3-5 epochs is typical for most fine-tuning tasks.",
  },

  // Advanced Settings
  optimizer: {
    title: "Optimizer",
    description:
      "Algorithm used to update model weights. AdamW is the standard for LLM fine-tuning.",
    example: "Use AdamW (default) for 99% of cases, SGD only for specific research needs.",
  },
  save_steps: {
    title: "Save Checkpoint Every N Steps",
    description:
      "How often to save your progress. More frequent saves use more disk space but provide more recovery points.",
    example: "Every 500 steps is typical.",
  },
  eval_steps: {
    title: "Evaluate Every N Steps",
    description: "How often to check model performance on validation data.",
    example: "Same as save_steps is common.",
  },
};

/**
 * Get tooltip for a specific configuration key
 */
export function getTooltip(key: string) {
  return tooltipConfig[key] || null;
}

/**
 * Check if a tooltip exists for a key
 */
export function hasTooltip(key: string): boolean {
  return key in tooltipConfig;
}

/**
 * Get all tooltip keys
 */
export function getAllTooltipKeys(): string[] {
  return Object.keys(tooltipConfig);
}
