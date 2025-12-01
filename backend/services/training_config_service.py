"""
Training Configuration Service
Handles validation and management of training configurations
Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5
"""

from typing import Dict, List, Optional, Literal
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PEFTAlgorithm(str, Enum):
    """Supported PEFT algorithms"""
    LORA = "lora"
    QLORA = "qlora"
    DORA = "dora"
    PISSA = "pissa"
    RSLORA = "rslora"


class QuantizationType(str, Enum):
    """Supported quantization types"""
    NONE = "none"
    INT8 = "int8"
    INT4 = "int4"
    NF4 = "nf4"


class ComputeProvider(str, Enum):
    """Supported compute providers"""
    LOCAL = "local"
    RUNPOD = "runpod"
    LAMBDA = "lambda"
    VASTAI = "vastai"


class ExperimentTracker(str, Enum):
    """Supported experiment trackers"""
    NONE = "none"
    WANDB = "wandb"
    COMETML = "cometml"
    PHOENIX = "phoenix"


@dataclass
class TrainingConfiguration:
    """Complete training configuration"""
    # Provider
    provider: ComputeProvider
    resource_id: Optional[str] = None
    
    # Algorithm
    algorithm: PEFTAlgorithm = PEFTAlgorithm.LORA
    
    # Quantization
    quantization: QuantizationType = QuantizationType.NONE
    
    # Experiment Tracking
    experiment_tracker: ExperimentTracker = ExperimentTracker.NONE
    project_name: Optional[str] = None
    
    # Model
    model_name: str = ""
    model_path: str = ""
    
    # Dataset
    dataset_id: str = ""
    dataset_path: str = ""
    
    # PEFT Settings
    lora_r: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.1
    target_modules: List[str] = field(default_factory=lambda: ["q_proj", "k_proj", "v_proj", "o_proj"])
    
    # Training Hyperparameters
    learning_rate: float = 2e-4
    batch_size: int = 4
    gradient_accumulation_steps: int = 4
    num_epochs: int = 3
    max_steps: int = -1
    warmup_steps: int = 100
    
    # Optimization
    optimizer: str = "adamw"
    scheduler: str = "linear"
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0
    
    # Precision
    precision: str = "fp16"
    
    # Checkpointing
    save_steps: int = 500
    save_total_limit: int = 3
    
    # Validation
    eval_steps: int = 500
    eval_strategy: str = "steps"


@dataclass
class ValidationResult:
    """Result of configuration validation"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


class TrainingConfigService:
    """Service for training configuration validation and management"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_configuration(self, config: TrainingConfiguration) -> ValidationResult:
        """
        Validate a training configuration for completeness and correctness.
        
        Property 4: Training configuration completeness
        For any training configuration, all required fields should be populated 
        before submission is allowed.
        
        Args:
            config: Training configuration to validate
            
        Returns:
            ValidationResult with errors, warnings, and suggestions
        """
        result = ValidationResult(is_valid=True)
        
        # Validate provider (Requirement 4.1)
        if not config.provider:
            result.errors.append("Compute provider must be selected")
            result.is_valid = False
        
        # Validate algorithm (Requirement 4.2)
        if not config.algorithm:
            result.errors.append("PEFT algorithm must be selected")
            result.is_valid = False
        
        # Validate model selection
        if not config.model_name or not config.model_path:
            result.errors.append("Model must be selected")
            result.is_valid = False
        
        # Validate dataset selection
        if not config.dataset_id or not config.dataset_path:
            result.errors.append("Dataset must be selected")
            result.is_valid = False
        
        # Validate quantization compatibility (Requirement 4.3)
        if config.quantization != QuantizationType.NONE and config.algorithm == PEFTAlgorithm.DORA:
            result.errors.append("DoRA is not compatible with quantization")
            result.is_valid = False
        
        # Validate experiment tracker configuration (Requirement 4.4)
        if config.experiment_tracker != ExperimentTracker.NONE:
            if not config.project_name or config.project_name.strip() == "":
                result.errors.append("Project name is required when experiment tracking is enabled")
                result.is_valid = False
        
        # Validate hyperparameters (Requirement 4.5)
        if config.learning_rate <= 0:
            result.errors.append("Learning rate must be positive")
            result.is_valid = False
        
        if config.batch_size <= 0:
            result.errors.append("Batch size must be positive")
            result.is_valid = False
        
        if config.gradient_accumulation_steps <= 0:
            result.errors.append("Gradient accumulation steps must be positive")
            result.is_valid = False
        
        if config.num_epochs <= 0 and config.max_steps <= 0:
            result.errors.append("Either num_epochs or max_steps must be positive")
            result.is_valid = False
        
        if config.lora_r <= 0:
            result.errors.append("LoRA rank (r) must be positive")
            result.is_valid = False
        
        if config.lora_alpha <= 0:
            result.errors.append("LoRA alpha must be positive")
            result.is_valid = False
        
        if not (0 <= config.lora_dropout < 1):
            result.errors.append("LoRA dropout must be between 0 and 1")
            result.is_valid = False
        
        if not config.target_modules or len(config.target_modules) == 0:
            result.errors.append("At least one target module must be specified")
            result.is_valid = False
        
        # Add warnings for suboptimal configurations
        if config.batch_size == 1 and config.gradient_accumulation_steps == 1:
            result.warnings.append("Very small effective batch size may lead to unstable training")
        
        if config.learning_rate > 1e-3:
            result.warnings.append("Learning rate is quite high, may cause training instability")
        
        if config.quantization == QuantizationType.NONE and config.algorithm == PEFTAlgorithm.QLORA:
            result.warnings.append("QLoRA typically uses 4-bit quantization")
        
        # Add suggestions
        if config.provider == ComputeProvider.LOCAL:
            result.suggestions.append("Consider using cloud providers for faster training")
        
        if config.experiment_tracker == ExperimentTracker.NONE:
            result.suggestions.append("Enable experiment tracking to monitor training progress")
        
        return result
    
    def is_configuration_complete(self, config: TrainingConfiguration) -> bool:
        """
        Check if configuration has all required fields populated.
        
        Property 4: Training configuration completeness
        
        Args:
            config: Training configuration to check
            
        Returns:
            True if all required fields are populated
        """
        validation = self.validate_configuration(config)
        return validation.is_valid
    
    def get_algorithm_description(self, algorithm: PEFTAlgorithm) -> str:
        """Get human-readable description of PEFT algorithm"""
        descriptions = {
            PEFTAlgorithm.LORA: "Standard Low-Rank Adaptation - efficient fine-tuning with low-rank matrices",
            PEFTAlgorithm.QLORA: "Quantized LoRA - 4-bit quantization for reduced memory usage",
            PEFTAlgorithm.DORA: "Weight-Decomposed Low-Rank Adaptation - improved performance over LoRA",
            PEFTAlgorithm.PISSA: "Principal Singular Values and Singular Vectors Adaptation",
            PEFTAlgorithm.RSLORA: "Rank-Stabilized LoRA - improved stability for higher ranks",
        }
        return descriptions.get(algorithm, "Unknown algorithm")
    
    def get_quantization_description(self, quantization: QuantizationType) -> str:
        """Get human-readable description of quantization type"""
        descriptions = {
            QuantizationType.NONE: "Full precision - no quantization",
            QuantizationType.INT8: "8-bit integer quantization - moderate memory savings",
            QuantizationType.INT4: "4-bit integer quantization - significant memory savings",
            QuantizationType.NF4: "4-bit NormalFloat quantization - optimized for normal distributions",
        }
        return descriptions.get(quantization, "Unknown quantization")
    
    def estimate_memory_requirements(self, config: TrainingConfiguration, model_size_mb: float) -> Dict[str, float]:
        """
        Estimate memory requirements for a training configuration.
        
        Args:
            config: Training configuration
            model_size_mb: Model size in megabytes
            
        Returns:
            Dictionary with memory estimates
        """
        # Base model memory
        base_memory = model_size_mb
        
        # Apply quantization reduction
        if config.quantization == QuantizationType.INT8:
            base_memory *= 0.5
        elif config.quantization in [QuantizationType.INT4, QuantizationType.NF4]:
            base_memory *= 0.25
        
        # LoRA adapter memory (typically small)
        adapter_memory = (config.lora_r * 2 * len(config.target_modules) * 4) / 1024  # Rough estimate in MB
        
        # Optimizer states (AdamW has 2x parameters)
        optimizer_memory = adapter_memory * 2
        
        # Gradients
        gradient_memory = adapter_memory
        
        # Activations (depends on batch size and sequence length)
        activation_memory = config.batch_size * 100  # Rough estimate
        
        total_memory = base_memory + adapter_memory + optimizer_memory + gradient_memory + activation_memory
        
        return {
            "base_model_mb": base_memory,
            "adapter_mb": adapter_memory,
            "optimizer_mb": optimizer_memory,
            "gradient_mb": gradient_memory,
            "activation_mb": activation_memory,
            "total_mb": total_memory,
            "total_gb": total_memory / 1024,
        }


# Singleton instance
_training_config_service_instance = None


def get_training_config_service() -> TrainingConfigService:
    """Get singleton instance of TrainingConfigService"""
    global _training_config_service_instance
    if _training_config_service_instance is None:
        _training_config_service_instance = TrainingConfigService()
    return _training_config_service_instance
