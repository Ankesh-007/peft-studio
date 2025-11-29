# Design Document

## Overview

The Simplified LLM Optimization feature transforms PEFT Studio into an accessible, wizard-driven application that makes fine-tuning Large Language Models intuitive for users of all skill levels. The design centers around a multi-step Training Wizard that guides users through the entire process with intelligent defaults, real-time feedback, and automatic error recovery.

The system architecture follows a layered approach:
- **Presentation Layer**: React-based Training Wizard with step-by-step UI
- **Intelligence Layer**: Smart configuration engine that calculates optimal settings
- **Training Layer**: Enhanced training orchestration with monitoring and recovery
- **Storage Layer**: Model versioning and checkpoint management

Key design principles:
1. **Progressive Disclosure**: Show simple options first, advanced settings on demand
2. **Intelligent Defaults**: Calculate optimal values based on hardware and data
3. **Continuous Feedback**: Real-time guidance and validation at every step
4. **Graceful Degradation**: Automatic fallbacks when resources are constrained
5. **Reversibility**: Allow users to go back and change decisions without losing progress

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Electron Main Process                    │
│  ┌────────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │ IPC Bridge     │  │ Notification │  │ File System     │ │
│  │                │  │ Manager      │  │ Manager         │ │
│  └────────────────┘  └──────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ IPC
                              │
┌─────────────────────────────┴───────────────────────────────┐
│                    React Frontend (Renderer)                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Training Wizard Component                │  │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐  │  │
│  │  │Step 1│→│Step 2│→│Step 3│→│Step 4│→│Review &  │  │  │
│  │  │      │ │      │ │      │ │      │ │Launch    │  │  │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Smart Configuration Engine (Frontend)         │  │
│  │  • Hardware Detection  • Profile Selection            │  │
│  │  • Validation Logic    • Estimate Calculations        │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            Real-Time Monitoring Dashboard             │  │
│  │  • Live Metrics  • Progress Tracking  • Alerts       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              │ HTTP/WebSocket
                              │
┌─────────────────────────────┴───────────────────────────────┐
│                   Python FastAPI Backend                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Training Orchestration Service              │  │
│  │  • Job Queue  • Checkpoint Manager  • Error Handler  │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          Hardware Profiling Service                   │  │
│  │  • GPU Detection  • Memory Analysis  • Benchmarking  │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          Dataset Processing Service                   │  │
│  │  • Format Detection  • Validation  • Preprocessing   │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          Model Management Service                     │  │
│  │  • Version Control  • Export  • Inference Testing    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              │
┌─────────────────────────────┴───────────────────────────────┐
│                    Training Engine Layer                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  PyTorch + Transformers + PEFT + bitsandbytes        │  │
│  │  • Adaptive Training Loop  • Auto-Recovery           │  │
│  │  • Dynamic Resource Management                        │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

1. **Wizard Initialization**: User opens Training Wizard → Frontend requests hardware profile → Backend detects GPU/CPU/RAM
2. **Configuration**: User selects profile/dataset → Smart engine calculates defaults → Backend validates feasibility
3. **Training Launch**: User confirms → Backend creates training job → Training engine starts with monitoring
4. **Real-Time Updates**: Training engine emits metrics → WebSocket pushes to frontend → Dashboard updates
5. **Completion**: Training finishes → Model versioned → Inference playground auto-loads model

## Components and Interfaces

### 1. Training Wizard Component (Frontend)

**Purpose**: Multi-step guided interface for configuring training runs

**Sub-Components**:

#### Step 1: Use Case Selection
- Display 6+ optimization profiles with descriptions
- Show hardware requirements and estimated time for each
- Allow custom profile creation

#### Step 2: Dataset Upload & Validation
- Drag-and-drop file upload
- Automatic format detection (CSV, JSON, JSONL, TXT)
- Real-time validation with error highlighting
- Data preview with sample rows

#### Step 3: Model Selection
- Browse HuggingFace models with search/filter
- Show model size, parameters, and memory requirements
- Display compatibility warnings

#### Step 4: Smart Configuration
- Auto-calculated hyperparameters with explanations
- Collapsible advanced settings section
- Real-time estimate updates (time, cost, carbon)

#### Step 5: Review & Launch
- Summary of all selections
- Final estimates with confidence intervals
- One-click launch button

**State Management**:
```typescript
interface WizardState {
  currentStep: number;
  profile: OptimizationProfile | null;
  dataset: Dataset | null;
  model: ModelInfo | null;
  config: TrainingConfig;
  estimates: TrainingEstimates;
  validation: ValidationResult[];
}
```

**Key Methods**:
- `nextStep()`: Validate current step and advance
- `previousStep()`: Return to previous step without losing data
- `calculateEstimates()`: Update time/cost predictions
- `validateStep()`: Check if current step is complete
- `launchTraining()`: Submit configuration to backend

### 2. Smart Configuration Engine (Frontend/Backend)

**Purpose**: Calculate optimal training parameters based on hardware and data

**Frontend Component**:
```typescript
class SmartConfigEngine {
  calculateBatchSize(gpuMemory: number, modelSize: number, seqLength: number): number
  calculateGradientAccumulation(targetBatchSize: number, maxBatchSize: number): number
  recommendPrecision(gpuCapability: string): 'fp16' | 'bf16' | 'int8'
  estimateTrainingTime(config: TrainingConfig, hardware: HardwareProfile): TimeEstimate
  estimateCost(trainingTime: number, electricityRate: number): CostEstimate
}
```

**Backend Service**:
```python
class HardwareProfiler:
    def detect_gpus() -> List[GPUInfo]
    def measure_available_memory() -> MemoryInfo
    def benchmark_throughput(model_name: str) -> ThroughputMetrics
    def calculate_optimal_config(
        model_size: int,
        dataset_size: int,
        hardware: HardwareInfo
    ) -> OptimalConfig
```

**Configuration Algorithm**:
1. Detect GPU memory and compute capability
2. Calculate maximum batch size that fits in memory
3. Determine if quantization is needed (8-bit, 4-bit)
4. Set gradient accumulation to reach effective batch size
5. Calculate optimal learning rate based on batch size
6. Estimate training time using throughput benchmarks

### 3. Optimization Profile System

**Purpose**: Pre-configured settings for common use cases

**Profile Structure**:
```typescript
interface OptimizationProfile {
  id: string;
  name: string;
  description: string;
  useCase: string;
  icon: string;
  config: {
    loraR: number;
    loraAlpha: number;
    loraDropout: number;
    targetModules: string[];
    learningRate: number;
    epochs: number;
    warmupRatio: number;
    maxSeqLength: number;
  };
  requirements: {
    minGPUMemory: number;
    recommendedDatasetSize: number;
  };
}
```

**Built-in Profiles**:
1. **Chatbot Assistant**: Optimized for conversational AI
2. **Code Generation**: Syntax-aware settings for programming
3. **Text Summarization**: Efficient for document processing
4. **Question Answering**: Focused on factual accuracy
5. **Creative Writing**: Higher temperature, diverse outputs
6. **Domain Adaptation**: General-purpose fine-tuning

### 4. Dataset Processing Service (Backend)

**Purpose**: Validate, analyze, and prepare training data

**API Endpoints**:
```python
POST /api/datasets/upload
POST /api/datasets/validate
GET /api/datasets/{id}/preview
GET /api/datasets/{id}/statistics
POST /api/datasets/{id}/preprocess
```

**Processing Pipeline**:
```python
class DatasetProcessor:
    def detect_format(file_path: str) -> DatasetFormat
    def validate_structure(dataset: Dataset) -> ValidationResult
    def analyze_statistics(dataset: Dataset) -> DatasetStats
    def check_quality(dataset: Dataset) -> QualityReport
    def preprocess(dataset: Dataset, config: PreprocessConfig) -> ProcessedDataset
```

**Validation Checks**:
- Format consistency (all rows have required fields)
- Text length distribution
- Character encoding issues
- Duplicate detection
- Empty or malformed entries
- Token count estimation

### 5. Training Orchestration Service (Backend)

**Purpose**: Manage training lifecycle with monitoring and recovery

**Core Class**:
```python
class TrainingOrchestrator:
    def create_job(config: TrainingConfig) -> TrainingJob
    def start_training(job_id: str) -> None
    def pause_training(job_id: str) -> None
    def resume_training(job_id: str) -> None
    def stop_training(job_id: str) -> None
    def get_status(job_id: str) -> TrainingStatus
    def get_metrics(job_id: str) -> TrainingMetrics
```

**Training Job State Machine**:
```
CREATED → INITIALIZING → RUNNING ⇄ PAUSED
                ↓           ↓
            FAILED      COMPLETED
```

**Monitoring System**:
- Emit metrics every 2 seconds via WebSocket
- Track: loss, learning rate, throughput, GPU utilization, memory
- Detect anomalies: loss divergence, NaN values, memory leaks
- Auto-checkpoint every N steps and on anomaly detection

### 6. Error Detection and Recovery System (Backend)

**Purpose**: Automatically detect and recover from training issues

**Anomaly Detectors**:
```python
class AnomalyDetector:
    def detect_loss_divergence(loss_history: List[float]) -> bool
    def detect_gradient_explosion(gradients: Tensor) -> bool
    def detect_overfitting(train_loss: float, val_loss: float) -> bool
    def detect_memory_leak(memory_history: List[int]) -> bool
```

**Recovery Strategies**:
```python
class RecoveryStrategy:
    def handle_loss_divergence() -> Action:
        # Reduce learning rate by 50%, reload last checkpoint
        
    def handle_gradient_explosion() -> Action:
        # Enable gradient clipping, reduce learning rate
        
    def handle_oom_error() -> Action:
        # Reduce batch size, enable gradient checkpointing
        
    def handle_overfitting() -> Action:
        # Suggest early stopping, increase dropout
```

### 7. Real-Time Monitoring Dashboard (Frontend)

**Purpose**: Display training progress with visual feedback

**Key Visualizations**:
- **Loss Curves**: Line chart with color-coded zones (green: good, yellow: acceptable, red: problematic)
- **Progress Ring**: Circular progress with epoch counter
- **Resource Meters**: GPU/CPU/RAM utilization bars
- **Throughput Graph**: Steps per second over time
- **Anomaly Alerts**: Toast notifications with suggested actions

**WebSocket Integration**:
```typescript
class TrainingMonitor {
  private ws: WebSocket;
  
  connect(jobId: string): void
  onMetricsUpdate(callback: (metrics: TrainingMetrics) => void): void
  onAnomaly(callback: (anomaly: Anomaly) => void): void
  onComplete(callback: (result: TrainingResult) => void): void
}
```

### 8. Model Versioning System (Backend)

**Purpose**: Track model iterations with automatic versioning

**Version Structure**:
```python
@dataclass
class ModelVersion:
    id: str
    model_name: str
    version: str  # semantic versioning: v1.0.0
    timestamp: datetime
    config: TrainingConfig
    metrics: FinalMetrics
    checkpoint_path: Path
    size_bytes: int
    parent_version: Optional[str]
```

**Version Management**:
```python
class ModelVersionManager:
    def create_version(model_name: str, checkpoint: Path) -> ModelVersion
    def list_versions(model_name: str) -> List[ModelVersion]
    def compare_versions(v1: str, v2: str) -> VersionComparison
    def rollback_to_version(version: str) -> None
    def archive_old_versions(keep_latest: int) -> None
```

### 9. Inference Playground Integration (Frontend)

**Purpose**: Immediate model testing after training

**Auto-Load Feature**:
```typescript
class InferencePlayground {
  autoLoadModel(modelVersion: ModelVersion): Promise<void>
  generateExamplePrompts(useCase: string): string[]
  compareWithBaseModel(prompt: string): Promise<ComparisonResult>
  saveConversation(messages: Message[]): void
}
```

**Comparison View**:
- Side-by-side output display
- Highlight differences
- Quality scoring (coherence, relevance, fluency)
- Export conversation history

### 10. Export System (Backend)

**Purpose**: Convert models to various deployment formats

**Export Formats**:
```python
class ModelExporter:
    def export_to_huggingface(model: Model, metadata: dict) -> HFPackage
    def export_to_ollama(model: Model) -> OllamaModelfile
    def export_to_gguf(model: Model, quantization: str) -> GGUFFile
    def export_to_lmstudio(model: Model) -> LMStudioPackage
```

**Export Pipeline**:
1. Merge LoRA weights with base model (optional)
2. Convert to target format
3. Generate metadata/model card
4. Package with tokenizer and config
5. Validate exported model
6. Provide installation instructions

## Data Models

### TrainingConfig
```typescript
interface TrainingConfig {
  // Model
  modelName: string;
  modelPath: string;
  
  // Dataset
  datasetId: string;
  datasetPath: string;
  
  // PEFT Settings
  peftMethod: 'lora' | 'qlora' | 'prefix-tuning';
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
  optimizer: 'adamw' | 'sgd';
  scheduler: 'linear' | 'cosine' | 'constant';
  weightDecay: number;
  maxGradNorm: number;
  
  // Precision
  precision: 'fp32' | 'fp16' | 'bf16';
  quantization: '8bit' | '4bit' | null;
  
  // Checkpointing
  saveSteps: number;
  saveTotal: number;
  
  // Validation
  evalSteps: number;
  evalStrategy: 'steps' | 'epoch';
}
```

### HardwareProfile
```typescript
interface HardwareProfile {
  gpus: GPUInfo[];
  cpu: CPUInfo;
  ram: RAMInfo;
  timestamp: Date;
}

interface GPUInfo {
  id: number;
  name: string;
  memoryTotal: number;  // bytes
  memoryAvailable: number;
  computeCapability: string;
  cudaVersion: string;
}
```

### TrainingMetrics
```typescript
interface TrainingMetrics {
  step: number;
  epoch: number;
  loss: number;
  learningRate: number;
  gradNorm: number;
  
  // Performance
  throughput: number;  // steps/sec
  samplesPerSecond: number;
  
  // Resources
  gpuUtilization: number[];  // per GPU
  gpuMemoryUsed: number[];
  gpuTemperature: number[];
  cpuUtilization: number;
  ramUsed: number;
  
  // Validation (optional)
  valLoss?: number;
  valPerplexity?: number;
  
  // Timing
  timestamp: Date;
  elapsedTime: number;
  estimatedTimeRemaining: number;
}
```

### TrainingEstimates
```typescript
interface TrainingEstimates {
  duration: {
    min: number;  // seconds
    expected: number;
    max: number;
  };
  
  cost: {
    electricityCost: number;  // USD
    gpuHours: number;
    carbonFootprint: number;  // kg CO2
  };
  
  resources: {
    peakMemory: number;
    avgGPUUtilization: number;
    diskSpace: number;
  };
  
  confidence: number;  // 0-1
}
```

### ValidationResult
```typescript
interface ValidationResult {
  field: string;
  level: 'error' | 'warning' | 'info';
  message: string;
  suggestion?: string;
  autoFixable: boolean;
}
```

### Anomaly
```typescript
interface Anomaly {
  type: 'loss_divergence' | 'gradient_explosion' | 'overfitting' | 'oom' | 'memory_leak';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  detectedAt: {
    step: number;
    timestamp: Date;
  };
  suggestedActions: Action[];
  autoRecoverable: boolean;
}

interface Action {
  description: string;
  automatic: boolean;
  execute: () => Promise<void>;
}
```

## C
orrectness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

After analyzing the acceptance criteria, several properties are redundant or can be combined. For example, properties about storing "all fields" during saves/checkpoints can be unified into comprehensive round-trip properties. Properties about UI displaying "all required fields" can be combined into single validation properties per component.

### Property 1: Use case selection configures all parameters
*For any* optimization profile selection, the system should automatically populate all required technical parameters (LoRA settings, learning rate, batch size, epochs, target modules)
**Validates: Requirements 1.2, 3.2**

### Property 2: Configuration tooltips completeness
*For any* configuration setting displayed in the wizard, there should exist a corresponding tooltip with plain-language explanation
**Validates: Requirements 1.3**

### Property 3: Smart defaults calculation
*For any* combination of hardware specifications and dataset characteristics, when advanced settings are not specified, the system should calculate valid default values for all hyperparameters
**Validates: Requirements 1.5, 2.2, 2.5**

### Property 4: Hardware detection completeness
*For any* system initialization, the hardware detection should return valid values for GPU memory, CPU cores, and RAM capacity
**Validates: Requirements 2.1**

### Property 5: Quantization auto-enable on insufficient memory
*For any* model and GPU memory combination where model size exceeds available memory, the system should automatically enable quantization
**Validates: Requirements 2.3**

### Property 6: Dataset format acceptance
*For any* file in CSV, JSON, JSONL, or plain text format, the upload system should successfully accept and process the file
**Validates: Requirements 4.1**

### Property 7: Dataset format detection
*For any* valid dataset file, the system should correctly identify its format (CSV, JSON, JSONL, or TXT)
**Validates: Requirements 4.2**

### Property 8: Dataset validation provides suggestions
*For any* dataset containing formatting errors, the validation system should return specific, actionable suggestions for each error
**Validates: Requirements 4.4**

### Property 9: Loss curve color coding
*For any* loss value, the visualization system should assign the correct color zone (green for good, yellow for acceptable, red for problematic) based on defined thresholds
**Validates: Requirements 5.2**

### Property 10: Training estimates include confidence intervals
*For any* training configuration, the time estimation function should return minimum, expected, and maximum duration values
**Validates: Requirements 5.3, 9.1**

### Property 11: Anomaly detection provides explanations and actions
*For any* detected training anomaly, the system should return both a plain-language explanation and a list of suggested actions
**Validates: Requirements 5.4, 6.1, 6.2, 6.4**

### Property 12: Memory threshold triggers batch size reduction
*For any* training state where GPU memory usage exceeds 90%, the system should automatically reduce batch size and generate a notification
**Validates: Requirements 6.3**

### Property 13: Training completion triggers quality analysis
*For any* completed training run, the system should generate a quality score and specific improvement suggestions
**Validates: Requirements 6.5**

### Property 14: Use case generates relevant prompts
*For any* training use case, the inference playground should generate at least 3 example prompts relevant to that use case
**Validates: Requirements 7.2**

### Property 15: Inference comparison includes both outputs
*For any* inference request, the comparison function should return both the fine-tuned model output and the base model output
**Validates: Requirements 7.4**

### Property 16: Configuration save/load round-trip
*For any* training configuration, saving it as a preset and then loading that preset should restore all hyperparameters, dataset references, and model selections identically
**Validates: Requirements 8.2, 8.4, 8.5**

### Property 17: Cost estimates completeness
*For any* training configuration, the estimate calculation should return GPU hours, electricity cost, and carbon footprint values
**Validates: Requirements 9.2**

### Property 18: Configuration alternatives suggestion
*For any* training configuration, the system should suggest at least one alternative configuration that is either faster or more resource-efficient
**Validates: Requirements 9.5**

### Property 19: Error messages are plain language
*For any* error that occurs, the displayed message should not contain technical stack traces or code references
**Validates: Requirements 10.1**

### Property 20: Error handling provides actions
*For any* error, the system should return between 2 and 3 specific actions the user can take to resolve it
**Validates: Requirements 10.2**

### Property 21: Unresolvable errors include help links
*For any* error that cannot be automatically resolved, the error response should include a help documentation link
**Validates: Requirements 10.4**

### Property 22: Training run comparison generates charts
*For any* selection of 2-5 completed training runs, the comparison function should generate side-by-side charts for all key metrics
**Validates: Requirements 11.2**

### Property 23: Comparison highlights best performers
*For any* set of training runs being compared, the system should identify and highlight the best-performing run for each metric
**Validates: Requirements 11.3**

### Property 24: Configuration diff calculation
*For any* pair of training configurations, the diff function should identify and return all parameter differences
**Validates: Requirements 11.4**

### Property 25: Progress milestone notifications
*For any* training run, when progress reaches 25%, 50%, 75%, or 100%, the system should generate a desktop notification
**Validates: Requirements 12.1**

### Property 26: Training error triggers notification
*For any* error during training, the system should send an urgent desktop notification with error summary
**Validates: Requirements 12.2**

### Property 27: Pause saves checkpoint
*For any* training pause action, the system should save a checkpoint containing model weights, optimizer state, and current metrics
**Validates: Requirements 13.1, 13.4**

### Property 28: Pause/resume round-trip preserves state
*For any* training state, pausing and then immediately resuming should restore the exact training state (step, epoch, loss, learning rate)
**Validates: Requirements 13.3**

### Property 29: Paused run displays complete information
*For any* paused training run, the display should include elapsed time, remaining time estimate, and resource usage at pause time
**Validates: Requirements 13.5**

### Property 30: Model versioning on completion
*For any* completed training run, the system should automatically create a model version with version number, timestamp, configuration, and metrics
**Validates: Requirements 14.1, 14.2**

### Property 31: Low disk space triggers cleanup prompt
*For any* system state where available disk space falls below a threshold, the system should prompt the user with version sizes and cleanup options
**Validates: Requirements 14.5**

### Property 32: HuggingFace export completeness
*For any* model exported to HuggingFace format, the export package should contain model weights, model card, configuration file, and tokenizer files
**Validates: Requirements 15.2**

### Property 33: Ollama export generates required artifacts
*For any* model exported to Ollama format, the export should generate a valid Modelfile and installation instructions
**Validates: Requirements 15.3**

### Property 34: Export verification succeeds
*For any* exported model, the verification function should successfully load the model and generate sample output
**Validates: Requirements 15.5**

## Error Handling

### Error Categories

1. **User Input Errors**
   - Invalid dataset format
   - Incompatible model selection
   - Out-of-range hyperparameters
   - **Handling**: Immediate validation with inline error messages and suggestions

2. **Resource Errors**
   - Insufficient GPU memory
   - Disk space exhausted
   - Network connectivity issues
   - **Handling**: Automatic fallbacks (quantization, cleanup) with user notification

3. **Training Errors**
   - Loss divergence
   - Gradient explosion
   - NaN values in loss
   - **Handling**: Automatic recovery strategies with checkpoint rollback

4. **System Errors**
   - CUDA errors
   - File system errors
   - Process crashes
   - **Handling**: Graceful degradation, state preservation, detailed error reports

### Error Recovery Strategies

```python
class ErrorRecoverySystem:
    def handle_error(error: Exception, context: TrainingContext) -> RecoveryAction:
        if isinstance(error, OutOfMemoryError):
            return reduce_batch_size_and_retry(context)
        elif isinstance(error, LossDivergenceError):
            return reduce_learning_rate_and_rollback(context)
        elif isinstance(error, GradientExplosionError):
            return enable_gradient_clipping_and_retry(context)
        elif isinstance(error, DatasetError):
            return show_validation_errors_and_halt(context)
        else:
            return save_state_and_report(context, error)
```

### User-Facing Error Messages

All errors follow this template:
```
[Plain Language Title]

What happened: [Simple explanation without jargon]

Why it happened: [Likely cause]

What you can do:
1. [Automatic action if available]
2. [Manual action option 1]
3. [Manual action option 2]

[Get Help button → relevant documentation]
```

## Testing Strategy

### Unit Testing

**Framework**: Jest for TypeScript/React, pytest for Python

**Coverage Areas**:
- Smart configuration calculations
- Hardware detection logic
- Dataset validation rules
- Error message formatting
- Version management operations
- Export format conversions

**Example Unit Tests**:
```typescript
describe('SmartConfigEngine', () => {
  test('calculates batch size within GPU memory limits', () => {
    const engine = new SmartConfigEngine();
    const batchSize = engine.calculateBatchSize(24000, 7000, 2048);
    expect(batchSize).toBeGreaterThan(0);
    expect(batchSize).toBeLessThanOrEqual(32);
  });
  
  test('enables quantization when memory insufficient', () => {
    const engine = new SmartConfigEngine();
    const config = engine.calculateOptimalConfig({
      gpuMemory: 8000,
      modelSize: 13000,
      datasetSize: 10000
    });
    expect(config.quantization).toBe('8bit');
  });
});
```

### Property-Based Testing

**Framework**: fast-check for TypeScript, Hypothesis for Python

**Configuration**: Each property test should run a minimum of 100 iterations to ensure comprehensive coverage of the input space.

**Test Tagging**: Each property-based test must include a comment tag in this exact format:
```typescript
// **Feature: simplified-llm-optimization, Property 1: Use case selection configures all parameters**
```

**Coverage Areas**:
- Configuration generation for all profiles
- Hardware specification calculations
- Dataset validation across formats
- Error handling and recovery
- Round-trip serialization
- Comparison and diff operations

**Example Property Tests**:

```typescript
import fc from 'fast-check';

// **Feature: simplified-llm-optimization, Property 1: Use case selection configures all parameters**
test('use case selection configures all required parameters', () => {
  fc.assert(
    fc.property(
      fc.constantFrom('chatbot', 'code-generation', 'summarization', 'qa', 'creative-writing', 'domain-adaptation'),
      (useCase) => {
        const config = selectOptimizationProfile(useCase);
        
        expect(config.loraR).toBeGreaterThan(0);
        expect(config.loraAlpha).toBeGreaterThan(0);
        expect(config.learningRate).toBeGreaterThan(0);
        expect(config.epochs).toBeGreaterThan(0);
        expect(config.targetModules).toHaveLength(greaterThan(0));
      }
    ),
    { numRuns: 100 }
  );
});

// **Feature: simplified-llm-optimization, Property 3: Smart defaults calculation**
test('smart defaults calculated for any hardware and dataset', () => {
  fc.assert(
    fc.property(
      fc.record({
        gpuMemory: fc.integer({ min: 4000, max: 80000 }),
        cpuCores: fc.integer({ min: 4, max: 128 }),
        ramGB: fc.integer({ min: 16, max: 512 }),
        datasetSize: fc.integer({ min: 100, max: 1000000 }),
        modelSize: fc.integer({ min: 1000, max: 70000 })
      }),
      (specs) => {
        const defaults = calculateSmartDefaults(specs);
        
        expect(defaults.batchSize).toBeGreaterThan(0);
        expect(defaults.learningRate).toBeGreaterThan(0);
        expect(defaults.gradientAccumulation).toBeGreaterThan(0);
        expect(['fp32', 'fp16', 'bf16']).toContain(defaults.precision);
      }
    ),
    { numRuns: 100 }
  );
});

// **Feature: simplified-llm-optimization, Property 16: Configuration save/load round-trip**
test('configuration save and load preserves all settings', () => {
  fc.assert(
    fc.property(
      fc.record({
        modelName: fc.string(),
        loraR: fc.integer({ min: 1, max: 256 }),
        loraAlpha: fc.integer({ min: 1, max: 512 }),
        learningRate: fc.double({ min: 1e-6, max: 1e-3 }),
        batchSize: fc.integer({ min: 1, max: 128 }),
        epochs: fc.integer({ min: 1, max: 100 })
      }),
      (config) => {
        const saved = saveConfiguration(config);
        const loaded = loadConfiguration(saved);
        
        expect(loaded).toEqual(config);
      }
    ),
    { numRuns: 100 }
  );
});
```

```python
from hypothesis import given, strategies as st

# **Feature: simplified-llm-optimization, Property 7: Dataset format detection**
@given(st.sampled_from(['csv', 'json', 'jsonl', 'txt']))
def test_dataset_format_detection(format_type):
    """For any valid dataset format, detection should correctly identify it"""
    dataset_file = create_sample_dataset(format_type)
    detected_format = detect_dataset_format(dataset_file)
    
    assert detected_format == format_type

# **Feature: simplified-llm-optimization, Property 11: Anomaly detection provides explanations and actions**
@given(
    st.one_of(
        st.just('loss_divergence'),
        st.just('gradient_explosion'),
        st.just('overfitting'),
        st.just('oom')
    )
)
def test_anomaly_detection_completeness(anomaly_type):
    """For any detected anomaly, response should include explanation and actions"""
    anomaly = create_anomaly(anomaly_type)
    response = handle_anomaly(anomaly)
    
    assert response.explanation is not None
    assert len(response.explanation) > 0
    assert len(response.suggested_actions) >= 2
    assert len(response.suggested_actions) <= 3

# **Feature: simplified-llm-optimization, Property 28: Pause/resume round-trip preserves state**
@given(
    st.integers(min_value=1, max_value=10000),  # step
    st.integers(min_value=1, max_value=100),    # epoch
    st.floats(min_value=0.01, max_value=10.0),  # loss
    st.floats(min_value=1e-6, max_value=1e-3)   # learning_rate
)
def test_pause_resume_preserves_state(step, epoch, loss, learning_rate):
    """For any training state, pause then resume should preserve exact state"""
    initial_state = TrainingState(
        step=step,
        epoch=epoch,
        loss=loss,
        learning_rate=learning_rate
    )
    
    checkpoint = pause_training(initial_state)
    restored_state = resume_training(checkpoint)
    
    assert restored_state.step == initial_state.step
    assert restored_state.epoch == initial_state.epoch
    assert abs(restored_state.loss - initial_state.loss) < 1e-6
    assert abs(restored_state.learning_rate - initial_state.learning_rate) < 1e-9
```

### Integration Testing

**Scope**: End-to-end workflows through the Training Wizard

**Key Scenarios**:
1. Complete training workflow from profile selection to model export
2. Error recovery during training with checkpoint restoration
3. Multi-model comparison and configuration reuse
4. Dataset upload, validation, and preprocessing pipeline
5. Model versioning and rollback operations

### Performance Testing

**Benchmarks**:
- Hardware detection: < 2 seconds
- Dataset validation: < 5 seconds for 10K examples
- Configuration calculation: < 500ms
- UI responsiveness: < 100ms for all interactions
- WebSocket latency: < 50ms for metric updates

## Security Considerations

1. **File Upload Validation**
   - Scan uploaded files for malicious content
   - Limit file sizes (max 1GB for datasets)
   - Validate file extensions and MIME types

2. **Resource Limits**
   - Prevent excessive memory allocation
   - Limit concurrent training jobs
   - Implement disk space quotas

3. **Data Privacy**
   - Store datasets locally only
   - No telemetry without explicit consent
   - Secure deletion of temporary files

4. **Model Export**
   - Validate export paths to prevent directory traversal
   - Sanitize model metadata
   - Verify exported model integrity

## Performance Optimizations

1. **Lazy Loading**
   - Load model lists on demand
   - Stream large datasets in chunks
   - Defer heavy computations until needed

2. **Caching**
   - Cache hardware profiles (refresh every 5 minutes)
   - Cache model metadata from HuggingFace
   - Memoize configuration calculations

3. **Background Processing**
   - Run dataset validation in worker threads
   - Perform export operations asynchronously
   - Generate thumbnails and previews in background

4. **Memory Management**
   - Release GPU memory immediately after training
   - Clear checkpoint cache when disk space low
   - Implement LRU cache for model versions

## Deployment Considerations

1. **Electron Packaging**
   - Bundle Python runtime with application
   - Include CUDA libraries for GPU support
   - Minimize bundle size with tree-shaking

2. **Auto-Updates**
   - Check for updates on startup
   - Download updates in background
   - Prompt user to restart for installation

3. **Platform Support**
   - Windows 10/11 (primary)
   - macOS 12+ (secondary)
   - Linux (Ubuntu 20.04+, community support)

4. **Hardware Requirements**
   - Minimum: 8GB RAM, 4-core CPU, 20GB disk
   - Recommended: 16GB RAM, 8-core CPU, NVIDIA GPU with 8GB+ VRAM, 100GB disk
   - Optimal: 32GB+ RAM, 16+ core CPU, NVIDIA GPU with 24GB+ VRAM, 500GB SSD

## Future Enhancements

1. **Collaborative Features**
   - Share training configurations with team
   - Cloud-based model registry
   - Collaborative experiment tracking

2. **Advanced Optimization**
   - Hyperparameter search (grid, random, Bayesian)
   - Multi-GPU training support
   - Distributed training across machines

3. **Enhanced Monitoring**
   - Predictive anomaly detection with ML
   - Automatic performance tuning
   - Cost optimization recommendations

4. **Extended Export Options**
   - TensorRT optimization
   - ONNX export
   - Mobile deployment (CoreML, TFLite)
