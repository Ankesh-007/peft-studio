export interface OptimizationProfile {
  id: string;
  name: string;
  description: string;
  use_case: string;
  icon: string;
  example_use_cases: string[];
  config: ProfileConfig;
  requirements: HardwareRequirements;
  tags: string[];
}

export interface ProfileConfig {
  lora_r: number;
  lora_alpha: number;
  lora_dropout: number;
  target_modules: string[];
  learning_rate: number;
  num_epochs: number;
  warmup_ratio: number;
  max_seq_length: number;
  weight_decay: number;
  max_grad_norm: number;
  scheduler: string;
}

export interface HardwareRequirements {
  min_gpu_memory_gb: number;
  recommended_gpu_memory_gb: number;
  min_dataset_size: number;
  recommended_dataset_size: number;
  estimated_time_per_epoch_minutes: number;
}

export interface Dataset {
  id: string;
  name: string;
  path: string;
  format: string;
  size: number;
  num_samples?: number;
  preview?: any[];
}

export interface ModelInfo {
  model_id: string;
  author: string;
  model_name: string;
  downloads: number;
  likes: number;
  tags: string[];
  pipeline_tag: string;
  library_name: string;
  size_mb: number;
  parameters: number;
  architecture: string;
  license: string;
}

export interface TrainingConfig {
  // Model
  modelName: string;
  modelPath: string;

  // Dataset
  datasetId: string;
  datasetPath: string;

  // PEFT Settings
  peftMethod: "lora" | "qlora" | "prefix-tuning";
  loraR: number;
  loraAlpha: number;
  loraDropout: number;
  targetModules: string[];

  // Training Hyperparameters
  learningRate: number;
  batchSize: number;
  gradientAccumulation: number;
  epochs: number;
  maxSteps: number;
  warmupSteps: number;

  // Optimization
  optimizer: "adamw" | "sgd";
  scheduler: "linear" | "cosine" | "constant";
  weightDecay: number;
  maxGradNorm: number;

  // Precision
  precision: "fp32" | "fp16" | "bf16";
  quantization: "8bit" | "4bit" | null;

  // Checkpointing
  saveSteps: number;
  saveTotal: number;

  // Validation
  evalSteps: number;
  evalStrategy: "steps" | "epoch";
}

export interface TrainingEstimates {
  duration: {
    min: number;
    expected: number;
    max: number;
  };
  cost: {
    electricityCost: number;
    gpuHours: number;
    carbonFootprint: number;
  };
  resources: {
    peakMemory: number;
    avgGPUUtilization: number;
    diskSpace: number;
  };
  confidence: number;
}

export interface ValidationResult {
  field: string;
  level: "error" | "warning" | "info";
  message: string;
  suggestion?: string;
  autoFixable: boolean;
}

export interface WizardState {
  currentStep: number;
  profile: OptimizationProfile | null;
  dataset: Dataset | null;
  model: ModelInfo | null;
  config: Partial<TrainingConfig>;
  estimates: TrainingEstimates | null;
  validation: ValidationResult[];
}

export interface TooltipConfig {
  [key: string]: {
    title: string;
    description: string;
    example?: string;
  };
}

export interface ConfigurationPreset {
  id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
  tags: string[];

  // Model configuration
  model_name: string;
  model_path: string;

  // Dataset configuration
  dataset_id: string;
  dataset_path: string;

  // PEFT Settings
  peft_method: "lora" | "qlora" | "prefix-tuning";
  lora_r: number;
  lora_alpha: number;
  lora_dropout: number;
  target_modules: string[];

  // Training Hyperparameters
  learning_rate: number;
  batch_size: number;
  gradient_accumulation: number;
  epochs: number;
  max_steps: number;
  warmup_steps: number;

  // Optimization
  optimizer: "adamw" | "sgd";
  scheduler: "linear" | "cosine" | "constant";
  weight_decay: number;
  max_grad_norm: number;

  // Precision
  precision: "fp32" | "fp16" | "bf16";
  quantization: "8bit" | "4bit" | null;

  // Checkpointing
  save_steps: number;
  save_total: number;

  // Validation
  eval_steps: number;
  eval_strategy: "steps" | "epoch";
}
