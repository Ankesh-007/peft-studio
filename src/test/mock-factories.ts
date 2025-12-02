/**
 * Mock data factories for complex components
 */

import type {
  OptimizationProfile,
  Dataset,
  ModelInfo,
  TrainingConfig,
  TrainingEstimates,
  ValidationResult,
  WizardState,
  ConfigurationPreset,
} from "../types/wizard";

// ============================================================================
// Optimization Profile Factory
// ============================================================================

export function createMockProfile(
  overrides?: Partial<OptimizationProfile>,
): OptimizationProfile {
  return {
    id: "test-profile",
    name: "Test Profile",
    description: "A test optimization profile",
    use_case: "general",
    icon: "🧪",
    example_use_cases: ["Testing", "Development"],
    config: {
      lora_r: 16,
      lora_alpha: 32,
      lora_dropout: 0.05,
      target_modules: ["q_proj", "v_proj"],
      learning_rate: 2e-4,
      num_epochs: 3,
      warmup_ratio: 0.1,
      max_seq_length: 2048,
      weight_decay: 0.01,
      max_grad_norm: 1.0,
      scheduler: "cosine",
    },
    requirements: {
      min_gpu_memory_gb: 8,
      recommended_gpu_memory_gb: 16,
      min_dataset_size: 100,
      recommended_dataset_size: 1000,
      estimated_time_per_epoch_minutes: 30,
    },
    tags: ["test", "mock"],
    ...overrides,
  };
}

// ============================================================================
// Dataset Factory
// ============================================================================

export function createMockDataset(overrides?: Partial<Dataset>): Dataset {
  return {
    id: "test-dataset",
    name: "test-data.json",
    path: "/path/to/test-data.json",
    format: "json",
    size: 1024000,
    num_samples: 500,
    preview: [
      {
        instruction: "What is machine learning?",
        input: "",
        output: "Machine learning is a subset of AI...",
      },
    ],
    ...overrides,
  };
}

// ============================================================================
// Model Info Factory
// ============================================================================

export function createMockModel(overrides?: Partial<ModelInfo>): ModelInfo {
  return {
    model_id: "test-org/test-model",
    author: "test-org",
    model_name: "test-model",
    downloads: 10000,
    likes: 500,
    tags: ["test", "transformer"],
    pipeline_tag: "text-generation",
    library_name: "transformers",
    size_mb: 5000,
    parameters: 7000,
    architecture: "TestForCausalLM",
    license: "apache-2.0",
    ...overrides,
  };
}

// ============================================================================
// Training Config Factory
// ============================================================================

export function createMockTrainingConfig(
  overrides?: Partial<TrainingConfig>,
): TrainingConfig {
  return {
    modelName: "test-model",
    modelPath: "/models/test-model",
    datasetId: "test-dataset",
    datasetPath: "/data/test-dataset",
    peftMethod: "lora",
    loraR: 16,
    loraAlpha: 32,
    loraDropout: 0.05,
    targetModules: ["q_proj", "v_proj"],
    learningRate: 2e-4,
    batchSize: 4,
    gradientAccumulation: 4,
    epochs: 3,
    maxSteps: 1000,
    warmupSteps: 100,
    optimizer: "adamw",
    scheduler: "cosine",
    weightDecay: 0.01,
    maxGradNorm: 1.0,
    precision: "fp16",
    quantization: null,
    saveSteps: 100,
    saveTotal: 3,
    evalSteps: 50,
    evalStrategy: "steps",
    ...overrides,
  };
}

// ============================================================================
// Training Estimates Factory
// ============================================================================

export function createMockEstimates(
  overrides?: Partial<TrainingEstimates>,
): TrainingEstimates {
  return {
    duration: {
      min: 60,
      expected: 90,
      max: 120,
    },
    cost: {
      electricityCost: 2.5,
      gpuHours: 1.5,
      carbonFootprint: 0.8,
    },
    resources: {
      peakMemory: 12000,
      avgGPUUtilization: 85,
      diskSpace: 5000,
    },
    confidence: 0.85,
    ...overrides,
  };
}

// ============================================================================
// Validation Result Factory
// ============================================================================

export function createMockValidation(
  overrides?: Partial<ValidationResult>,
): ValidationResult {
  return {
    field: "test_field",
    level: "warning",
    message: "Test validation message",
    suggestion: "Try adjusting the value",
    autoFixable: false,
    ...overrides,
  };
}

// ============================================================================
// Wizard State Factory
// ============================================================================

export function createMockWizardState(
  overrides?: Partial<WizardState>,
): WizardState {
  return {
    currentStep: 0,
    profile: null,
    dataset: null,
    model: null,
    config: {},
    estimates: null,
    validation: [],
    ...overrides,
  };
}

// ============================================================================
// Configuration Preset Factory
// ============================================================================

export function createMockPreset(
  overrides?: Partial<ConfigurationPreset>,
): ConfigurationPreset {
  return {
    id: "test-preset",
    name: "Test Preset",
    description: "A test configuration preset",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    tags: ["test"],
    model_name: "test-model",
    model_path: "/models/test-model",
    dataset_id: "test-dataset",
    dataset_path: "/data/test-dataset",
    peft_method: "lora",
    lora_r: 16,
    lora_alpha: 32,
    lora_dropout: 0.05,
    target_modules: ["q_proj", "v_proj"],
    learning_rate: 2e-4,
    batch_size: 4,
    gradient_accumulation: 4,
    epochs: 3,
    max_steps: 1000,
    warmup_steps: 100,
    optimizer: "adamw",
    scheduler: "cosine",
    weight_decay: 0.01,
    max_grad_norm: 1.0,
    precision: "fp16",
    quantization: null,
    save_steps: 100,
    save_total: 3,
    eval_steps: 50,
    eval_strategy: "steps",
    ...overrides,
  };
}

// ============================================================================
// Training Run Factory
// ============================================================================

export interface TrainingRun {
  id: number;
  name: string;
  model: string;
  dataset: string;
  status: "running" | "completed" | "failed" | "paused";
  progress: number;
  started_at?: string;
  completed_at?: string;
  current_step?: number;
  total_steps?: number;
  current_loss?: number;
}

export function createMockTrainingRun(
  overrides?: Partial<TrainingRun>,
): TrainingRun {
  return {
    id: 1,
    name: "test-training-run",
    model: "test-model",
    dataset: "test-dataset",
    status: "running",
    progress: 50,
    started_at: new Date().toISOString(),
    current_step: 500,
    total_steps: 1000,
    current_loss: 0.5,
    ...overrides,
  };
}

// ============================================================================
// Paused Run Factory
// ============================================================================

export interface PausedRun {
  job_id: string;
  state: string;
  paused_at: string;
  started_at: string;
  elapsed_time: number;
  remaining_time_estimate: number;
  current_step: number;
  current_epoch: number;
  current_loss: number;
  resource_usage: {
    gpu_utilization: number[];
    gpu_memory_used: number[];
    cpu_utilization: number;
    ram_used: number;
  };
  model_name: string;
  dataset_name: string;
}

export function createMockPausedRun(
  overrides?: Partial<PausedRun>,
): PausedRun {
  return {
    job_id: "test_job_123",
    state: "paused",
    paused_at: new Date().toISOString(),
    started_at: new Date(Date.now() - 3600000).toISOString(),
    elapsed_time: 3600,
    remaining_time_estimate: 1800,
    current_step: 500,
    current_epoch: 2,
    current_loss: 0.5,
    resource_usage: {
      gpu_utilization: [85.5, 42.3],
      gpu_memory_used: [12000000000, 8000000000],
      cpu_utilization: 60.0,
      ram_used: 32000000000,
    },
    model_name: "test-model",
    dataset_name: "test-dataset",
    ...overrides,
  };
}

// ============================================================================
// Hardware Info Factory
// ============================================================================

export interface HardwareInfo {
  gpus: Array<{
    name: string;
    memory_total: number;
    memory_free: number;
    utilization: number;
  }>;
  cpu: {
    cores: number;
    utilization: number;
  };
  ram: {
    total: number;
    available: number;
  };
}

export function createMockHardwareInfo(
  overrides?: Partial<HardwareInfo>,
): HardwareInfo {
  return {
    gpus: [
      {
        name: "NVIDIA RTX 3090",
        memory_total: 24000000000,
        memory_free: 12000000000,
        utilization: 50,
      },
    ],
    cpu: {
      cores: 16,
      utilization: 30,
    },
    ram: {
      total: 64000000000,
      available: 32000000000,
    },
    ...overrides,
  };
}

// ============================================================================
// Batch Factory Helpers
// ============================================================================

/**
 * Create multiple mock items using a factory
 */
export function createMockBatch<T>(
  factory: (index: number) => T,
  count: number,
): T[] {
  return Array.from({ length: count }, (_, i) => factory(i));
}

/**
 * Create mock profiles with different use cases
 */
export function createMockProfiles(): OptimizationProfile[] {
  return [
    createMockProfile({
      id: "chatbot",
      name: "Chatbot Assistant",
      use_case: "chatbot",
      icon: "💬",
    }),
    createMockProfile({
      id: "code-gen",
      name: "Code Generation",
      use_case: "code",
      icon: "💻",
    }),
    createMockProfile({
      id: "summarization",
      name: "Text Summarization",
      use_case: "summarization",
      icon: "📝",
    }),
  ];
}

/**
 * Create mock training runs with different statuses
 */
export function createMockTrainingRuns(): TrainingRun[] {
  return [
    createMockTrainingRun({ id: 1, status: "running", progress: 65 }),
    createMockTrainingRun({ id: 2, status: "completed", progress: 100 }),
    createMockTrainingRun({ id: 3, status: "failed", progress: 23 }),
    createMockTrainingRun({ id: 4, status: "paused", progress: 50 }),
  ];
}
